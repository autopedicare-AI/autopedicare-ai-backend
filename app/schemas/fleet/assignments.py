from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime
from uuid import UUID
from enum import Enum


class AssignmentStatus(str, Enum):
    active = "active"
    inactive = "inactive"


class AssignmentBase(BaseModel):
    driver_id: UUID
    vehicle_id: UUID
    status: AssignmentStatus = AssignmentStatus.active


class AssignmentCreate(AssignmentBase):
    pass


class AssignmentUpdate(BaseModel):
    status: Optional[AssignmentStatus] = None


class AssignmentResponse(AssignmentBase):
    id: UUID
    assigned_at: datetime

    model_config = ConfigDict(from_attributes=True)