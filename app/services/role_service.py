from fastapi import Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.admin_menus import AdminMenu
from app.models.role_menus import RoleMenu
from app.models.roles import Role
from app.models.user_roles import UserRole
from app.services.activity_log_service import ActivityLogService, get_activity_log_service
from app.services.user_service import UserService, get_user_service


ACCESS_LEVELS = {"None": "None", "Read": "Read", "Write": "Write"}


class RoleService:
    def __init__(
        self,
        db,
        user_service: UserService,
        activity_log_service: ActivityLogService,
    ):
        self.db = db
        self.user_service = user_service
        self.activity_log_service = activity_log_service

    # Replaced _require_admin with self.user_service._require_permission

    def _serialize_role(self, role):
        return {
            "id": role.id,
            "role_name": role.role_name,
            "description": role.description,
            "is_admin_access_enabled": role.is_admin_access_enabled,
            "is_enabled": role.is_enabled,
            "created_by": role.created_by,
            "created_at": role.created_at,
            "updated_by": role.updated_by,
            "updated_at": role.updated_at,
        }

    def _serialize_menu(self, menu):
        return {
            "id": menu.id,
            "name": menu.name,
            "slug": menu.slug,
            "icon": menu.icon,
        }

    def _ensure_role_name_available(self, role_name: str, exclude_role_id: int = None):
        query = self.db.query(Role).filter(Role.role_name == role_name)
        if exclude_role_id is not None:
            query = query.filter(Role.id != exclude_role_id)

        if query.first():
            raise HTTPException(status_code=400, detail="Role with this name already exists")

    def _ensure_menu_exists(self, admin_menu_id: int):
        menu = self.db.query(AdminMenu).filter(AdminMenu.id == admin_menu_id).first()
        if not menu:
            raise HTTPException(status_code=404, detail="Menu not found")
        return menu

    def get_all_roles(self, token: str):
        self.user_service.get_user_from_token(token)
        roles = self.db.query(Role).order_by(Role.id.asc()).all()
        return [self._serialize_role(role) for role in roles]

    def get_role_by_id(self, role_id: int, token: str):
        self.user_service.get_user_from_token(token)
        role = self.db.query(Role).filter(Role.id == role_id).first()
        if not role:
            raise HTTPException(status_code=404, detail="Role not found")
        return self._serialize_role(role)

    def create_role(self, role_data, token: str):
        admin = self.user_service.get_user_from_token(token)
        self._ensure_role_name_available(role_data.role_name)

        role = Role(
            role_name=role_data.role_name,
            description=role_data.description,
            is_admin_access_enabled=role_data.is_admin_access_enabled,
            is_enabled=role_data.is_enabled,
            created_by=admin.id,
        )
        self.db.add(role)
        self.db.commit()
        self.db.refresh(role)
        self.activity_log_service.record(module="Roles", action="Added", record_id=role.id, record_name=role.role_name, user=admin, description="Role created", commit=True)

        return {
            "message": "Role created successfully",
            "role": self._serialize_role(role),
        }

    def update_role(self, role_id: int, role_data, token: str):
        admin = self.user_service.get_user_from_token(token)
        role = self.db.query(Role).filter(Role.id == role_id).first()
        if not role:
            raise HTTPException(status_code=404, detail="Role not found")

        previous_values = self.activity_log_service.snapshot(role)
        update_data = role_data.model_dump(exclude_unset=True)
        if "role_name" in update_data:
            self._ensure_role_name_available(update_data["role_name"], exclude_role_id=role.id)

        for field_name, value in update_data.items():
            setattr(role, field_name, value)

        role.updated_by = admin.id
        self.db.commit()
        self.db.refresh(role)
        self.activity_log_service.record(module="Roles", action="Updated", record_id=role.id, record_name=role.role_name, user=admin, description="Role updated", metadata={"fields": list(update_data.keys())}, previous_values=previous_values, changed_values=self.activity_log_service.changes(previous_values, role), commit=True)

        return {
            "message": "Role updated successfully",
            "role": self._serialize_role(role),
        }

    def delete_role(self, role_id: int, token: str):
        admin = self.user_service.get_user_from_token(token)
        role = self.db.query(Role).filter(Role.id == role_id).first()
        if not role:
            raise HTTPException(status_code=404, detail="Role not found")

        if self.db.query(UserRole).filter(UserRole.role_id == role.id).first():
            raise HTTPException(status_code=400, detail="Role is assigned to users and cannot be deleted")

        if self.db.query(RoleMenu).filter(RoleMenu.role_id == role.id).first():
            raise HTTPException(status_code=400, detail="Role has menu permissions and cannot be deleted")

        self.db.delete(role)
        self.db.commit()
        self.activity_log_service.record(module="Roles", action="Deleted", record_id=role_id, record_name=role.role_name, user=admin, description="Role deleted", commit=True)

        return {"message": "Role deleted successfully"}

    def get_role_menus(self, role_id: int, token: str):
        self.user_service.get_user_from_token(token)
        role = self.db.query(Role).filter(Role.id == role_id).first()
        if not role:
            raise HTTPException(status_code=404, detail="Role not found")

        role_menus = (
            self.db.query(RoleMenu, AdminMenu)
            .join(AdminMenu, AdminMenu.id == RoleMenu.admin_menu_id)
            .filter(RoleMenu.role_id == role_id)
            .order_by(AdminMenu.id.asc())
            .all()
        )

        return {
            "role": self._serialize_role(role),
            "menus": [
                {
                    "id": role_menu.id,
                    "role_id": role_menu.role_id,
                    "admin_menu": self._serialize_menu(menu),
                    "admin_menu_id": role_menu.admin_menu_id,
                    "access_level": role_menu.access_level,
                    "created_at": role_menu.created_at,
                    "created_by": role_menu.created_by,
                    "updated_at": role_menu.updated_at,
                    "updated_by": role_menu.updated_by,
                }
                for role_menu, menu in role_menus
            ],
        }

    def get_role_menu_by_id(self, role_menu_id: int, token: str):
        self.user_service.get_user_from_token(token)
        role_menu = self.db.query(RoleMenu).filter(RoleMenu.id == role_menu_id).first()
        if not role_menu:
            raise HTTPException(status_code=404, detail="Role menu not found")

        role = self.db.query(Role).filter(Role.id == role_menu.role_id).first()
        menu = self.db.query(AdminMenu).filter(AdminMenu.id == role_menu.admin_menu_id).first()
        return {
            "id": role_menu.id,
            "role": self._serialize_role(role) if role else None,
            "admin_menu": self._serialize_menu(menu) if menu else None,
            "access_level": role_menu.access_level,
            "created_at": role_menu.created_at,
            "created_by": role_menu.created_by,
            "updated_at": role_menu.updated_at,
            "updated_by": role_menu.updated_by,
        }

    def create_role_menu(self, role_id: int, payload, token: str):
        admin = self.user_service.get_user_from_token(token)
        role = self.db.query(Role).filter(Role.id == role_id).first()
        if not role:
            raise HTTPException(status_code=404, detail="Role not found")

        if payload.access_level not in ACCESS_LEVELS:
            raise HTTPException(status_code=400, detail="Invalid access level")

        menu = self._ensure_menu_exists(payload.admin_menu_id)
        existing = (
            self.db.query(RoleMenu)
            .filter(RoleMenu.role_id == role_id, RoleMenu.admin_menu_id == payload.admin_menu_id)
            .first()
        )
        if existing:
            raise HTTPException(status_code=400, detail="Role menu already exists")

        role_menu = RoleMenu(
            role_id=role_id,
            admin_menu_id=menu.id,
            access_level=payload.access_level,
            created_by=admin.id,
        )
        self.db.add(role_menu)
        self.db.commit()
        self.db.refresh(role_menu)
        self.activity_log_service.record(module="Role Permissions", action="Added", record_id=role_menu.id, record_name=f"{role.role_name}: {menu.name}", user=admin, description="Role menu permission created", metadata={"role_id": role.id, "menu_id": menu.id, "access_level": role_menu.access_level}, commit=True)

        return {"message": "Role menu created successfully", "role_menu": self.get_role_menu_by_id(role_menu.id, token)}

    def update_role_menu(self, role_menu_id: int, payload, token: str):
        admin = self.user_service.get_user_from_token(token)
        role_menu = self.db.query(RoleMenu).filter(RoleMenu.id == role_menu_id).first()
        if not role_menu:
            raise HTTPException(status_code=404, detail="Role menu not found")

        previous_values = self.activity_log_service.snapshot(role_menu)
        if payload.admin_menu_id is not None:
            self._ensure_menu_exists(payload.admin_menu_id)
            duplicate = (
                self.db.query(RoleMenu)
                .filter(RoleMenu.role_id == role_menu.role_id, RoleMenu.admin_menu_id == payload.admin_menu_id)
                .filter(RoleMenu.id != role_menu.id)
                .first()
            )
            if duplicate:
                raise HTTPException(status_code=400, detail="Role menu already exists for this role")
            role_menu.admin_menu_id = payload.admin_menu_id

        if payload.access_level is not None:
            if payload.access_level not in ACCESS_LEVELS:
                raise HTTPException(status_code=400, detail="Invalid access level")
            role_menu.access_level = payload.access_level

        role_menu.updated_by = admin.id
        self.db.commit()
        self.db.refresh(role_menu)
        role = self.db.query(Role).filter(Role.id == role_menu.role_id).first()
        menu = self.db.query(AdminMenu).filter(AdminMenu.id == role_menu.admin_menu_id).first()
        self.activity_log_service.record(module="Role Permissions", action="Updated", record_id=role_menu.id, record_name=f"{role.role_name if role else 'Role'}: {menu.name if menu else 'Menu'}", user=admin, description="Role menu permission updated", metadata={"role_id": role_menu.role_id, "menu_id": role_menu.admin_menu_id, "access_level": role_menu.access_level}, previous_values=previous_values, changed_values=self.activity_log_service.changes(previous_values, role_menu), commit=True)

        return {"message": "Role menu updated successfully", "role_menu": self.get_role_menu_by_id(role_menu.id, token)}

    def delete_role_menu(self, role_menu_id: int, token: str):
        admin = self.user_service.get_user_from_token(token)
        role_menu = self.db.query(RoleMenu).filter(RoleMenu.id == role_menu_id).first()
        if not role_menu:
            raise HTTPException(status_code=404, detail="Role menu not found")

        role = self.db.query(Role).filter(Role.id == role_menu.role_id).first()
        menu = self.db.query(AdminMenu).filter(AdminMenu.id == role_menu.admin_menu_id).first()
        record_name = f"{role.role_name if role else 'Role'}: {menu.name if menu else 'Menu'}"
        self.db.delete(role_menu)
        self.db.commit()
        self.activity_log_service.record(module="Role Permissions", action="Deleted", record_id=role_menu_id, record_name=record_name, user=admin, description="Role menu permission deleted", commit=True)
        return {"message": "Role menu deleted successfully"}


def get_role_service(
    db: Session = Depends(get_db),
    user_service: UserService = Depends(get_user_service),
        activity_log_service: ActivityLogService = Depends(get_activity_log_service),
) -> RoleService:
    return RoleService(db, user_service, activity_log_service)
