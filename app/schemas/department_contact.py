from typing import Optional
from pydantic import BaseModel, EmailStr

class DepartmentContactCreate(BaseModel):
    department_name: str
    inquiry_type: str
    email: EmailStr
    display_order: int = 0


class DepartmentContactUpdate(BaseModel):
    department_name: Optional[str] = None
    inquiry_type: Optional[str] = None
    email: Optional[EmailStr] = None
    display_order: Optional[int] = None


class DepartmentContactStatusUpdate(BaseModel):
    is_active: bool


class DepartmentContactResponse(BaseModel):
    id: int
    department_name: str
    inquiry_type: str
    email: EmailStr
    display_order: int
    is_active: bool

    class Config:
        from_attributes = True