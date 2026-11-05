from fastapi import Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.admin_menus import AdminMenu
from app.models.menu_items import MenuItem
from app.models.role_menus import RoleMenu
from app.services.activity_log_service import ActivityLogService, get_activity_log_service
from app.services.user_service import UserService, get_user_service


class MenuService:
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

    def _serialize_menu(self, menu):
        return {
            "id": menu.id,
            "name": menu.name,
            "slug": menu.slug,
            "icon": menu.icon,
            "sort_order": menu.sort_order,
            "created_at": menu.created_at,
            "created_by": menu.created_by,
            "updated_at": menu.updated_at,
            "updated_by": menu.updated_by,
        }

    def _serialize_menu_item(self, menu_item):
        return {
            "id": menu_item.id,
            "menu_id": menu_item.menu_id,
            "parent_id": menu_item.parent_id,
            "title": menu_item.title,
            "url": menu_item.url,
            "sort_order": menu_item.sort_order,
            "created_at": menu_item.created_at,
            "created_by": menu_item.created_by,
            "updated_at": menu_item.updated_at,
            "updated_by": menu_item.updated_by,
        }

    def _ensure_slug_available(self, slug: str, exclude_menu_id: int = None):
        from app.utils.query import ensure_slug_available
        ensure_slug_available(
            self.db, AdminMenu, slug, exclude_id=exclude_menu_id, detail="Menu with this slug already exists"
        )

    def get_all_menus(self, token: str):
        self.user_service.get_user_from_token(token)
        menus = self.db.query(AdminMenu).order_by(AdminMenu.sort_order.asc(), AdminMenu.id.asc()).all()
        return [self._serialize_menu(menu) for menu in menus]

    def get_menu_by_id(self, menu_id: int, token: str):
        self.user_service.get_user_from_token(token)
        menu = self.db.query(AdminMenu).filter(AdminMenu.id == menu_id).first()
        if not menu:
            raise HTTPException(status_code=404, detail="Menu not found")
        return self._serialize_menu(menu)

    def get_menu_items(self, menu_id: int, token: str):
        self.user_service.get_user_from_token(token)
        menu = self.db.query(AdminMenu).filter(AdminMenu.id == menu_id).first()
        if not menu:
            raise HTTPException(status_code=404, detail="Menu not found")

        items = (
            self.db.query(MenuItem)
            .filter(MenuItem.menu_id == menu_id)
            .order_by(MenuItem.sort_order.asc(), MenuItem.id.asc())
            .all()
        )
        return {
            "menu": self._serialize_menu(menu),
            "items": [self._serialize_menu_item(item) for item in items],
        }

    def get_menu_item_by_id(self, item_id: int, token: str):
        self.user_service.get_user_from_token(token)
        item = self.db.query(MenuItem).filter(MenuItem.id == item_id).first()
        if not item:
            raise HTTPException(status_code=404, detail="Menu item not found")

        menu = self.db.query(AdminMenu).filter(AdminMenu.id == item.menu_id).first()
        return {
            "menu": self._serialize_menu(menu) if menu else None,
            "item": self._serialize_menu_item(item),
        }

    def create_menu(self, menu_data, token: str):
        admin = self.user_service.get_user_from_token(token)
        self._ensure_slug_available(menu_data.slug)

        menu = AdminMenu(
            name=menu_data.name,
            slug=menu_data.slug,
            icon=menu_data.icon,
            sort_order=menu_data.sort_order,
            created_by=admin.id,
            updated_by=admin.id,
        )
        self.db.add(menu)
        self.db.commit()
        self.db.refresh(menu)
        self.activity_log_service.record(module="Menus", action="Added", record_id=menu.id, record_name=menu.name, user=admin, description="Admin menu created", commit=True)

        return {
            "message": "Menu created successfully",
            "menu": self._serialize_menu(menu),
        }

    def update_menu(self, menu_id: int, menu_data, token: str):
        admin = self.user_service.get_user_from_token(token)
        menu = self.db.query(AdminMenu).filter(AdminMenu.id == menu_id).first()
        if not menu:
            raise HTTPException(status_code=404, detail="Menu not found")

        previous_values = self.activity_log_service.snapshot(menu)
        update_data = menu_data.model_dump(exclude_unset=True)
        if "slug" in update_data:
            self._ensure_slug_available(update_data["slug"], exclude_menu_id=menu.id)

        for field_name, value in update_data.items():
            setattr(menu, field_name, value)

        menu.updated_by = admin.id
        self.db.commit()
        self.db.refresh(menu)
        self.activity_log_service.record(module="Menus", action="Updated", record_id=menu.id, record_name=menu.name, user=admin, description="Admin menu updated", metadata={"fields": list(update_data.keys())}, previous_values=previous_values, changed_values=self.activity_log_service.changes(previous_values, menu), commit=True)

        return {
            "message": "Menu updated successfully",
            "menu": self._serialize_menu(menu),
        }

    def delete_menu(self, menu_id: int, token: str):
        admin = self.user_service.get_user_from_token(token)
        menu = self.db.query(AdminMenu).filter(AdminMenu.id == menu_id).first()
        if not menu:
            raise HTTPException(status_code=404, detail="Menu not found")

        role_menu_exists = self.db.query(RoleMenu).filter(RoleMenu.admin_menu_id == menu.id).first()
        if role_menu_exists:
            raise HTTPException(status_code=400, detail="Menu is assigned to roles and cannot be deleted")

        self.db.delete(menu)
        self.db.commit()
        self.activity_log_service.record(module="Menus", action="Deleted", record_id=menu_id, record_name=menu.name, user=admin, description="Admin menu deleted", commit=True)

        return {"message": "Menu deleted successfully"}


def get_menu_service(
    db: Session = Depends(get_db),
    user_service: UserService = Depends(get_user_service),
        activity_log_service: ActivityLogService = Depends(get_activity_log_service),
) -> MenuService:
    return MenuService(db, user_service, activity_log_service)
