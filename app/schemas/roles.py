from typing import Optional

from pydantic import BaseModel, Field


class RoleCreate(BaseModel):
    role_name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    is_admin_access_enabled: int = 0
    is_enabled: int = 1


class RoleUpdate(BaseModel):
    role_name: Optional[str] = Field(default=None, min_length=1, max_length=100)
    description: Optional[str] = None
    is_admin_access_enabled: Optional[int] = None
    is_enabled: Optional[int] = None


class RoleMenuCreate(BaseModel):
    admin_menu_id: int
    access_level: str = "None"


class RoleMenuUpdate(BaseModel):
    admin_menu_id: Optional[int] = None
    access_level: Optional[str] = None

