from loguru import logger
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status
from typing import List
from uuid import UUID
from app.models.fleet.assignments import Assignment
from app.schemas.fleet.assignments import (
    AssignmentCreate,
    AssignmentUpdate,
    AssignmentResponse,
)


class AssignmentService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_assignment(
        self, assignment_data: AssignmentCreate
    ) -> AssignmentResponse:
        # Check if driver or vehicle already has active assignment
        result = await self.db.execute(
            select(Assignment).where(
                Assignment.driver_id == assignment_data.driver_id,
                Assignment.status == "active",
            )
        )
        active_driver = result.scalars().first()
        if active_driver:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Driver already assigned to a vehicle",
            )

        result = await self.db.execute(
            select(Assignment).where(
                Assignment.vehicle_id == assignment_data.vehicle_id,
                Assignment.status == "active",
            )
        )
        active_vehicle = result.scalars().first()
        if active_vehicle:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Vehicle already assigned to a driver",
            )

        assignment = Assignment(**assignment_data.model_dump())
        self.db.add(assignment)
        try:
            await self.db.commit()
            await self.db.refresh(assignment)
            return AssignmentResponse.model_validate(assignment)
        except Exception:
            await self.db.rollback()
            logger.exception(
                "Assignment create error",
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal server error",
            )

    async def get_assignments(
        self, skip: int = 0, limit: int = 10
    ) -> List[AssignmentResponse]:
        result = await self.db.execute(
            select(Assignment).offset(skip).limit(limit)
        )
        assignments = result.scalars().all()
        return [AssignmentResponse.model_validate(a) for a in assignments]

    async def update_assignment(
        self, assignment_id: str, assignment_data: AssignmentUpdate
    ) -> AssignmentResponse:
        try:
            assignment_uuid = UUID(assignment_id)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid assignment ID"
            )
        result = await self.db.execute(
            select(Assignment).where(Assignment.id == assignment_uuid)
        )
        assignment = result.scalars().first()
        if not assignment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Assignment not found"
            )
        for key, value in assignment_data.model_dump(exclude_unset=True).items():
            setattr(assignment, key, value)
        try:
            await self.db.commit()
            await self.db.refresh(assignment)
            return AssignmentResponse.model_validate(assignment)
        except Exception as e:
            await self.db.rollback()
            logger.exception(
                "Assignment update error | assignment_id={assignment_id}",
                assignment_id=assignment_id,
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal server error",
            )

    async def delete_assignment(self, assignment_id: str):
        try:
            assignment_uuid = UUID(assignment_id)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid assignment ID"
            )
        result = await self.db.execute(
            select(Assignment).where(Assignment.id == assignment_uuid)
        )
        assignment = result.scalars().first()
        if not assignment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Assignment not found"
            )
        await self.db.delete(assignment)
        await self.db.commit()
