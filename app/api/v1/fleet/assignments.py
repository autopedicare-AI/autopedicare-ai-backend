from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import List
from app.db.session import get_db
from app.services.fleet.assignments import AssignmentService
from app.schemas.fleet.assignments import AssignmentCreate, AssignmentUpdate, AssignmentResponse

router = APIRouter(prefix="/assignments", tags=["Assignments"])


@router.post("", response_model=AssignmentResponse, status_code=201)
def create_assignment(assignment: AssignmentCreate, db: Session = Depends(get_db)):
    service = AssignmentService(db)
    return service.create_assignment(assignment)


@router.get("", response_model=List[AssignmentResponse])
def get_assignments(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db)
):
    service = AssignmentService(db)
    return service.get_assignments(skip, limit)


@router.put("/{assignment_id}", response_model=AssignmentResponse)
def update_assignment(assignment_id: str, assignment: AssignmentUpdate, db: Session = Depends(get_db)):
    service = AssignmentService(db)
    return service.update_assignment(assignment_id, assignment)


@router.delete("/{assignment_id}", status_code=204)
def delete_assignment(assignment_id: str, db: Session = Depends(get_db)):
    service = AssignmentService(db)
    service.delete_assignment(assignment_id)