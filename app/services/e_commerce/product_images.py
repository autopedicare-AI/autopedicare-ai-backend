import uuid
import boto3
from botocore.exceptions import ClientError
from fastapi import HTTPException, status, UploadFile
from fastapi.concurrency import run_in_threadpool
from sqlalchemy import select, update, func
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger
from uuid import UUID

from app.core.config import settings
from app.models.e_commerce.product_images import ProductImage
from app.models.e_commerce.vendors import Vendor
from app.models.user import User
from app.models.e_commerce.products import Product
from app.schemas.e_commerce.product_images import (
    ProductImageResponse,
)


class ProductImageService:

    def __init__(self, db: AsyncSession, current_user: User | None = None):
        self.db = db
        self.current_user = current_user
        self.vendor_id = None
        if current_user:
            self.vendor_id = None  # will be set lazily
        self.s3_client = boto3.client(
            "s3",
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            region_name=settings.AWS_REGION,
        )
        self.bucket_name = settings.AWS_BUCKET_NAME
        # max upload size in bytes; default to 5MB if not configured
        self.max_file_size = getattr(settings, "MAX_IMAGE_UPLOAD_SIZE_BYTES", 5 * 1024 * 1024)

    async def _get_user_vendor_id(self):
        result = await self.db.execute(
            select(Vendor).where(Vendor.owner_id == self.current_user.id)
        )
        vendor = result.scalars().first()
        if not vendor:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Vendor profile not found",
            )
        return vendor.id

    async def verify_product_ownership(self, product_id: UUID):
        if self.vendor_id is None:
            self.vendor_id = await self._get_user_vendor_id()
        result = await self.db.execute(
            select(Product)
            .options(
                selectinload(Product.vendor),
                selectinload(Product.images),
            )
            .where(
                Product.id == product_id,
                Product.vendor_id == self.vendor_id,
            )
        )
        product = result.scalars().first()
        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Product not found",
            )
        return product

    async def _upload_to_cloud(self, file: UploadFile) -> str:
        """Uploads the file to AWS S3 and returns the public URL."""

        # Validate content type
        if not file.content_type.startswith("image/"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid file type. Only image files are allowed.",
            )

        # Validate file size when possible
        try:
            # move to end to get size
            current = file.file.tell()
            file.file.seek(0, 2)
            size = file.file.tell()
            file.file.seek(0)
        except Exception:
            size = None

        if size is not None and size > self.max_file_size:
            max_mb = round(self.max_file_size / (1024 * 1024), 2)
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"File too large. Maximum allowed size is {max_mb} MB.",
            )

        if not self.bucket_name:
            logger.error("AWS_BUCKET_NAME environment variable is not set.")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Server configuration error regarding image uploads.",
            )

        file_extension = file.filename.split(".")[-1] if "." in file.filename else "jpg"
        unique_filename = f"product-images/{uuid.uuid4()}.{file_extension}"

        try:
            await run_in_threadpool(
                self.s3_client.upload_fileobj,
                file.file,
                self.bucket_name,
                unique_filename,
                ExtraArgs={
                    "Content-Type": file.content_type,
                },
            )
        except ClientError as e:
            logger.error("S3 Upload failed: {error}", error=e)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to upload image to cloud storage.",
            )

        region = settings.AWS_REGION
        return f"https://{self.bucket_name}.s3.{region}.amazonaws.com/{unique_filename}"

    async def add_image(
        self,
        product_id: UUID,
        file: UploadFile,
        angle_type: str,
        is_primary: bool = False,
    ):

        await self.verify_product_ownership(product_id)

        try:
            image_url = await self._upload_to_cloud(file)
        except HTTPException:
            raise
        except Exception as e:
            logger.error("Failed to upload image to cloud storage: {error}", error=e)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to upload image. Please try again later.",
            )

        if is_primary:
            await self.db.execute(
                update(ProductImage)
                .where(
                    ProductImage.product_id == product_id,
                    ProductImage.is_primary == True,
                )
                .values({ProductImage.is_primary: False})
            )

        result = await self.db.execute(
            select(func.count()).select_from(ProductImage).where(
                ProductImage.product_id == product_id
            )
        )
        existing_image_count = result.scalar_one()
        display_order = existing_image_count + 1

        new_image = ProductImage(
            product_id=product_id,
            image_url=image_url,
            angle_type=angle_type,
            is_primary=is_primary,
            display_order=display_order,
        )

        self.db.add(new_image)
        try:
            await self.db.commit()
            await self.db.refresh(new_image)
            return ProductImageResponse.model_validate(new_image)
        except Exception as e:
            await self.db.rollback()
            logger.error("Failed to save product image to database: {error}", error=e)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to save product image. Please try again later.",
            )

    async def delete_image(self, image_id: UUID):
        if self.vendor_id is None:
            self.vendor_id = await self._get_user_vendor_id()
        result = await self.db.execute(
            select(ProductImage)
            .join(Product)
            .where(
                ProductImage.id == image_id,
                Product.vendor_id == self.vendor_id,
            )
        )
        image = result.scalars().first()

        if not image:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Product image not found.",
            )

        try:
            object_key = image.image_url.split(".com/")[-1]
            await run_in_threadpool(
                self.s3_client.delete_object,
                Bucket=self.bucket_name,
                Key=object_key,
            )
        except ClientError as e:
            logger.warning(
                "Failed to delete image from S3, but proceeding with DB deletion. Error: {error}",
                error=e,
            )

        await self.db.delete(image)
        try:
            await self.db.commit()
        except Exception as e:
            logger.error(
                "Failed to delete product image from database: {error}", error=e
            )
            await self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to delete product image. Please try again later.",
            )

    async def get_product_images(self, product_id: UUID) -> list[ProductImageResponse]:
        result = await self.db.execute(
            select(ProductImage)
            .where(ProductImage.product_id == product_id)
            .order_by(ProductImage.display_order)
        )
        images = result.scalars().all()
        return [ProductImageResponse.model_validate(image) for image in images]
