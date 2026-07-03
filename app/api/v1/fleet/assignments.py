from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from app.db.session import get_db
from app.services.fleet.assignments import AssignmentService
from app.schemas.fleet.assignments import (
    AssignmentCreate,
    AssignmentUpdate,
    AssignmentResponse,
)

router = APIRouter(prefix="/assignments", tags=["Assignments"])


@router.post("", response_model=AssignmentResponse, status_code=201)
async def create_assignment(assignment: AssignmentCreate, db: AsyncSession = Depends(get_db)):
    service = AssignmentService(db)
    return await service.create_assignment(assignment)


@router.get("", response_model=List[AssignmentResponse])
async def get_assignments(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    service = AssignmentService(db)
    return await service.get_assignments(skip, limit)


@router.put("/{assignment_id}", response_model=AssignmentResponse)
async def update_assignment(
    assignment_id: str, assignment: AssignmentUpdate, db: AsyncSession = Depends(get_db)
):
    service = AssignmentService(db)
    return await service.update_assignment(assignment_id, assignment)

@router.delete("/{assignment_id}", status_code=204)
async def delete_assignment(assignment_id: str, db: AsyncSession = Depends(get_db)):
    service = AssignmentService(db)
    await service.delete_assignment(assignment_id)
    return None