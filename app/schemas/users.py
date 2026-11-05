from pydantic import BaseModel
from typing import Optional

class UserCreate(BaseModel):
    full_name: str
    email: str
    password: str
    role: str = "staff"

class UserUpdate(BaseModel):
    id: int
    full_name: str
    email: str
    password: str
    role: str = "staff"

class UserLogin(BaseModel):
    email: str
    password: str


class AdminUserCreate(BaseModel):
    full_name: str
    email: str
    password: str
    role: str = "staff"
    is_active: bool = True


class AdminUserUpdate(BaseModel):
    full_name: Optional[str] = None
    email: Optional[str] = None
    password: Optional[str] = None
    role: Optional[str] = None
    is_active: Optional[bool] = None


class UserStatusUpdate(BaseModel):
    is_active: bool


class ProfileUpdate(BaseModel):
    full_name: Optional[str] = None
    email: Optional[str] = None
    current_password: Optional[str] = None
    new_password: Optional[str] = None


