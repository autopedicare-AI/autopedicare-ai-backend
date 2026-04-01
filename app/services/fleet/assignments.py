from loguru import logger
from sqlalchemy.orm import Session
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
    def __init__(self, db: Session):
        self.db = db

    def create_assignment(
        self, assignment_data: AssignmentCreate
    ) -> AssignmentResponse:
        # Check if driver or vehicle already has active assignment
        active_driver = (
            self.db.query(Assignment)
            .filter(
                Assignment.driver_id == assignment_data.driver_id,
                Assignment.status == "active",
            )
            .first()
        )
        if active_driver:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Driver already assigned to a vehicle",
            )

        active_vehicle = (
            self.db.query(Assignment)
            .filter(
                Assignment.vehicle_id == assignment_data.vehicle_id,
                Assignment.status == "active",
            )
            .first()
        )
        if active_vehicle:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Vehicle already assigned to a driver",
            )

        assignment = Assignment(**assignment_data.model_dump())
        self.db.add(assignment)
        try:
            self.db.commit()
            self.db.refresh(assignment)
            return AssignmentResponse.model_validate(assignment)
        except Exception:
            self.db.rollback()
            logger.exception(
                "Assignment create error",
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal server error",
            )

    def get_assignments(
        self, skip: int = 0, limit: int = 10
    ) -> List[AssignmentResponse]:
        assignments = self.db.query(Assignment).offset(skip).limit(limit).all()
        return [AssignmentResponse.model_validate(a) for a in assignments]

    def update_assignment(
        self, assignment_id: str, assignment_data: AssignmentUpdate
    ) -> AssignmentResponse:
        try:
            assignment_uuid = UUID(assignment_id)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid assignment ID"
            )
        assignment = (
            self.db.query(Assignment).filter(Assignment.id == assignment_uuid).first()
        )
        if not assignment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Assignment not found"
            )
        for key, value in assignment_data.model_dump(exclude_unset=True).items():
            setattr(assignment, key, value)
        try:
            self.db.commit()
            self.db.refresh(assignment)
            return AssignmentResponse.model_validate(assignment)
        except Exception as e:
            self.db.rollback()
            logger.exception(
                "Assignment update error | assignment_id={assignment_id}",
                assignment_id=assignment_id,
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal server error",
            )

    def delete_assignment(self, assignment_id: str):
        try:
            assignment_uuid = UUID(assignment_id)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid assignment ID"
            )
        assignment = (
            self.db.query(Assignment).filter(Assignment.id == assignment_uuid).first()
        )
        if not assignment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Assignment not found"
            )
        self.db.delete(assignment)
        self.db.commit()
