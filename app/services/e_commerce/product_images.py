import uuid
import boto3
from botocore.exceptions import ClientError
from fastapi import HTTPException, status, UploadFile
from sqlalchemy.orm import Session
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

    def __init__(self, db: Session, current_user: User | None = None):
        self.db = db
        self.current_user = current_user
        self.vendor_id = self._get_user_vendor_id() if current_user else None
        self.s3_client = boto3.client(
            "s3",
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            region_name=settings.AWS_REGION,
        )
        self.bucket_name = settings.AWS_BUCKET_NAME

    def _get_user_vendor_id(self):
        vendor = (
            self.db.query(Vendor)
            .filter(Vendor.owner_id == self.current_user.id)
            .first()
        )
        if not vendor:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Vendor profile not found",
            )
        return vendor.id

    def verify_product_ownership(self, product_id: UUID):
        product = (
            self.db.query(Product)
            .filter(Product.id == product_id, Product.vendor_id == self.vendor_id)
            .first()
        )
        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Product not found",
            )
        return product

    async def _upload_to_cloud(self, file: UploadFile) -> str:
        """Uploads the file to AWS S3 and returns the public URL."""

        if not file.content_type.startswith("image/"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid file type. Only image files are allowed.",
            )

        if not self.bucket_name:
            logger.error("AWS_BUCKET_NAME environment variable is not set.")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Server configuration error regarding image uploads.",
            )

        # Generate a safe, unique filename using UUID
        file_extension = file.filename.split(".")[-1] if "." in file.filename else "jpg"
        unique_filename = f"product-images/{uuid.uuid4()}.{file_extension}"

        try:
            # uploading to s3
            self.s3_client.upload_fileobj(
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

        self.verify_product_ownership(product_id)

        # Uploading to cloud storage
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

        # Primary Image logic
        if is_primary:
            self.db.query(ProductImage).filter(
                ProductImage.product_id == product_id, ProductImage.is_primary == True
            ).update({ProductImage.is_primary: False})

        # Get the display order
        existing_image_count = (
            self.db.query(ProductImage)
            .filter(ProductImage.product_id == product_id)
            .count()
        )
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
            self.db.commit()
            self.db.refresh(new_image)
            return ProductImageResponse.model_validate(new_image)
        except Exception as e:
            self.db.rollback()
            logger.error("Failed to save product image to database: {error}", error=e)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to save product image. Please try again later.",
            )

    def delete_image(self, image_id: UUID):
        image = (
            self.db.query(ProductImage)
            .join(Product)
            .filter(ProductImage.id == image_id, Product.vendor_id == self.vendor_id)
            .first()
        )

        if not image:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Product image not found.",
            )

        # Delete the actual file from S3
        try:
            # Extract the S3 object key from the URL
            # Example URL: https://my-bucket.s3.us-east-1.amazonaws.com/product-images/123.jpg
            # Object Key: product-images/123.jpg
            object_key = image.image_url.split(".com/")[-1]
            self.s3_client.delete_object(Bucket=self.bucket_name, Key=object_key)
        except ClientError as e:
            logger.warning(
                "Failed to delete image from S3, but proceeding with DB deletion. Error: {error}",
                error=e,
            )

        self.db.delete(image)
        try:
            self.db.commit()
        except Exception as e:
            logger.error(
                "Failed to delete product image from database: {error}", error=e
            )
            self.db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to delete product image. Please try again later.",
            )

    def get_product_images(self, product_id: UUID) -> list[ProductImageResponse]:
        """Public endpoint to retrieve all images for a product."""
        images = (
            self.db.query(ProductImage)
            .filter(ProductImage.product_id == product_id)
            .order_by(ProductImage.display_order)
            .all()
        )
        return [ProductImageResponse.model_validate(image) for image in images]
