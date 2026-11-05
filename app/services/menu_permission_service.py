from fastapi import Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.admin_menus import AdminMenu
from app.models.role_menus import RoleMenu
from app.models.roles import Role
from app.models.user_roles import UserRole
from app.models.users import User
from app.services.activity_log_service import ActivityLogService
from app.services.token_service import TokenService, get_bearer_token


ACCESS_LEVELS = {
    "None": 0,
    "Read": 1,
    "Write": 2,
}


class MenuPermissionService:
    def __init__(self, db: Session):
        self.db = db

    def get_user_role(self, user_id: int):
        return (
            self.db.query(Role)
            .join(UserRole, UserRole.role_id == Role.id)
            .filter(UserRole.user_id == user_id)
            .filter(Role.is_enabled == 1)
            .first()
        )

    def get_user_menu_permissions(self, user_id: int):
        rows = (
            self.db.query(AdminMenu, RoleMenu.access_level)
            .join(RoleMenu, RoleMenu.admin_menu_id == AdminMenu.id)
            .join(UserRole, UserRole.role_id == RoleMenu.role_id)
            .join(Role, Role.id == UserRole.role_id)
            .filter(UserRole.user_id == user_id)
            .filter(Role.is_enabled == 1)
            .order_by(AdminMenu.sort_order)
            .all()
        )

        return [
            {
                "id": menu.id,
                "name": menu.name,
                "slug": menu.slug,
                "icon": menu.icon,
                "access_level": access_level,
            }
            for menu, access_level in rows
        ]

    def check_menu_access(self, user_id: int, menu_slug: str, required_access: str):
        access_rank = ACCESS_LEVELS.get(required_access)
        if access_rank is None:
            raise HTTPException(status_code=500, detail="Invalid required access level")

        role = self.get_user_role(user_id)
        if role and role.role_name == "admin":
            return True

        row = (
            self.db.query(RoleMenu.access_level)
            .join(AdminMenu, AdminMenu.id == RoleMenu.admin_menu_id)
            .join(UserRole, UserRole.role_id == RoleMenu.role_id)
            .join(Role, Role.id == UserRole.role_id)
            .filter(UserRole.user_id == user_id)
            .filter(AdminMenu.slug == menu_slug)
            .filter(Role.is_enabled == 1)
            .first()
        )

        if not row or ACCESS_LEVELS.get(row.access_level, 0) < access_rank:
            raise HTTPException(status_code=403, detail="Permission denied")

        return True

    def update_user_menu_access(self, admin_user_id: int, user_id: int, menu_slug: str, access_level: str):
        if access_level not in ACCESS_LEVELS:
            raise HTTPException(status_code=400, detail="Invalid access level")

        admin_role = self.get_user_role(admin_user_id)
        if not admin_role or admin_role.role_name != "admin":
            raise HTTPException(status_code=403, detail="Permission denied")

        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        user_role = (
            self.db.query(UserRole)
            .join(Role, Role.id == UserRole.role_id)
            .filter(UserRole.user_id == user_id)
            .filter(Role.is_enabled == 1)
            .first()
        )
        if not user_role:
            raise HTTPException(status_code=404, detail="User role not found")

        menu = self.db.query(AdminMenu).filter(AdminMenu.slug == menu_slug).first()
        if not menu:
            raise HTTPException(status_code=404, detail="Menu not found")

        role_menu = (
            self.db.query(RoleMenu)
            .filter(RoleMenu.role_id == user_role.role_id)
            .filter(RoleMenu.admin_menu_id == menu.id)
            .first()
        )
        previous_values = ActivityLogService(self.db).snapshot(role_menu) if role_menu else None

        if role_menu:
            role_menu.access_level = access_level
            role_menu.updated_by = admin_user_id
        else:
            role_menu = RoleMenu(
                role_id=user_role.role_id,
                admin_menu_id=menu.id,
                access_level=access_level,
                created_by=admin_user_id,
            )
            self.db.add(role_menu)

        self.db.commit()
        self.db.refresh(role_menu)
        admin_user = self.db.query(User).filter(User.id == admin_user_id).first()
        ActivityLogService(self.db).record(
            module="User Permissions",
            action="Updated",
            record_id=role_menu.id,
            record_name=f"{user.full_name}: {menu.name}",
            user=admin_user,
            description="User menu access updated",
            metadata={"user_id": user.id, "menu_slug": menu.slug, "access_level": role_menu.access_level},
            previous_values=previous_values,
            changed_values=ActivityLogService(self.db).changes(previous_values, role_menu) if previous_values else None,
            commit=True,
        )

        return {
            "user_id": user_id,
            "role_id": user_role.role_id,
            "menu": {
                "id": menu.id,
                "name": menu.name,
                "slug": menu.slug,
                "icon": menu.icon,
            },
            "access_level": role_menu.access_level,
        }


def require_menu_access(menu_slug: str, required_access: str):
    def dependency(token: str = Depends(get_bearer_token), db: Session = Depends(get_db)):
        user_id = int(TokenService.verify_access_token(token))
        MenuPermissionService(db).check_menu_access(user_id, menu_slug, required_access)
        return token

    return dependency
