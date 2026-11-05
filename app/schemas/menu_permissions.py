from typing import Literal

from pydantic import BaseModel


class MenuPermissionUpdate(BaseModel):
    menu_slug: str
    access_level: Literal["None", "Read", "Write"]
