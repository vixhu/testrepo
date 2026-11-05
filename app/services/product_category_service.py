from fastapi import Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.product_categories import ProductCategory
from app.models.products import Product
from app.services.activity_log_service import ActivityLogService, get_activity_log_service
from app.services.user_service import UserService, get_user_service


class ProductCategoryService:
    def __init__(self, db,
        user_service: UserService,
        activity_log_service: ActivityLogService):
        
        self.db = db
        self.user_service = user_service
        self.activity_log_service = activity_log_service

    
    # Replaced _require_admin with self.user_service._require_permission

    def _serialize_category_for_tree(self, category):
        return {
            "id": category.id,
            "name": category.name,
            "slug": category.slug,
            "parent_id": category.parent_id,
            "display_order": category.display_order,
            "is_active": bool(category.is_active),
            "children": []
        }

    def _serialize_category(self, category):
        return {
            "id": category.id,
            "category_id": category.id,
            "name": category.name,
            "slug": category.slug,
            "is_active": bool(category.is_active),
            "created_at": category.created_at,
            "created_by": category.created_by,
            "updated_at": category.updated_at,
            "updated_by": category.updated_by,
        }

    def _ensure_slug_available(self, slug: str, exclude_category_id=None):
        from app.utils.query import ensure_slug_available
        ensure_slug_available(
            self.db,
            ProductCategory,
            slug,
            exclude_id=exclude_category_id,
            detail="Product category with this slug already exists",
        )

    def _ensure_name_unique_in_parent(self, name: str, parent_id: int | None, exclude_category_id=None):
        query = self.db.query(ProductCategory).filter(
            ProductCategory.name == name,
            ProductCategory.parent_id == parent_id
        )
        if exclude_category_id:
            query = query.filter(ProductCategory.id != exclude_category_id)
        if query.first():
            raise HTTPException(status_code=400, detail="Category name must be unique within the same parent")

    def _ensure_parent_exists(self, parent_id: int | None):
        if parent_id is not None:
            parent = self.db.query(ProductCategory).filter(ProductCategory.id == parent_id).first()
            if not parent:
                raise HTTPException(status_code=400, detail="Parent category does not exist")

    def _prevent_circular_hierarchy(self, category_id: int, new_parent_id: int | None):
        if new_parent_id is None:
            return
        if category_id == new_parent_id:
            raise HTTPException(status_code=400, detail="Category cannot be its own parent")
        
        current_parent_id = new_parent_id
        while current_parent_id is not None:
            if current_parent_id == category_id:
                raise HTTPException(status_code=400, detail="Circular hierarchy detected")
            parent = self.db.query(ProductCategory).filter(ProductCategory.id == current_parent_id).first()
            if not parent:
                break
            current_parent_id = parent.parent_id

    def get_all_product_category(self, token):
        self.user_service.get_user_from_token(token)

        categories = self.db.query(ProductCategory).order_by(
            ProductCategory.display_order.asc(),
            ProductCategory.name.asc()
        ).all()
        
        category_map = {c.id: self._serialize_category_for_tree(c) for c in categories}
        tree = []
        for c in categories:
            node = category_map[c.id]
            if c.parent_id and c.parent_id in category_map:
                category_map[c.parent_id]["children"].append(node)
            elif not c.parent_id:
                tree.append(node)
        
        return tree

    
    def get_product_category(self, category_slug, token):
        self.user_service.get_user_from_token(token)

        category = self.db.query(ProductCategory).filter(ProductCategory.slug == category_slug).first()
        if not category:
            raise HTTPException(status_code=404, detail="Product category not found")

        return self._serialize_category(category)


    def add_product_category(self, category_data, token):
        user = self.user_service.get_user_from_token(token)

        if not getattr(category_data, 'name', None) or not getattr(category_data, 'slug', None):
            raise HTTPException(status_code=400, detail="Category name and slug are required")

        self._ensure_slug_available(category_data.slug)
        parent_id = getattr(category_data, 'parent_id', None)
        self._ensure_parent_exists(parent_id)
        self._ensure_name_unique_in_parent(category_data.name, parent_id)

        new_category = ProductCategory(
            name=category_data.name,
            slug=category_data.slug,
            parent_id=parent_id,
            display_order=getattr(category_data, 'display_order', 0),
            is_active=getattr(category_data, 'is_active', True),
            created_by=user.id,
            updated_by=user.id,
        )

        self.db.add(new_category)
        self.db.commit()
        self.db.refresh(new_category)
        self.activity_log_service.record(module="Product Categories", action="Added", record_id=new_category.id, record_name=new_category.name, user=user, description="Product category created", commit=True)

        return {
            "message": "Product category added successfully",
            "category": self._serialize_category(new_category)
        }


    def update_product_category(self, category_id: int, category_data, token):
        user = self.user_service.get_user_from_token(token)
        category = self.db.query(ProductCategory).filter(ProductCategory.id == category_id).first()
        if not category:
            raise HTTPException(status_code=404, detail="Product category not found")

        previous_values = self.activity_log_service.snapshot(category)
        
        if getattr(category_data, 'slug', None) is not None:
            self._ensure_slug_available(category_data.slug, exclude_category_id=category.id)
            
        new_parent_id = getattr(category_data, 'parent_id', category.parent_id)
        new_name = getattr(category_data, 'name', category.name)
        
        if new_parent_id != category.parent_id or new_name != category.name:
            if new_parent_id != category.parent_id:
                self._ensure_parent_exists(new_parent_id)
                self._prevent_circular_hierarchy(category_id, new_parent_id)
            self._ensure_name_unique_in_parent(new_name, new_parent_id, exclude_category_id=category.id)

        if getattr(category_data, 'name', None) is not None:
            category.name = category_data.name
        if getattr(category_data, 'slug', None) is not None:
            category.slug = category_data.slug
        
        has_parent_id = hasattr(category_data, 'parent_id')
        if has_parent_id:
             category.parent_id = category_data.parent_id

        if getattr(category_data, 'display_order', None) is not None:
            category.display_order = category_data.display_order
        if getattr(category_data, 'is_active', None) is not None:
            category.is_active = category_data.is_active

        category.updated_by = user.id

        self.db.commit()
        self.db.refresh(category)
        self.activity_log_service.record(module="Product Categories", action="Updated", record_id=category.id, record_name=category.name, user=user, description="Product category updated", previous_values=previous_values, changed_values=self.activity_log_service.changes(previous_values, category), commit=True)

        return {
            "message": "Product category updated successfully",
            "category": self._serialize_category(category)
        }


    def delete_product_category(self, category_id: int, token):
        user = self.user_service.get_user_from_token(token)

        if not category_id:
            raise HTTPException(status_code=400, detail="Category ID is required")

        category = self.db.query(ProductCategory).filter(ProductCategory.id == category_id).first()
        if not category:
            raise HTTPException(status_code=404, detail="Product category not found")

        if self.db.query(ProductCategory).filter(ProductCategory.parent_id == category.id).first():
            raise HTTPException(status_code=400, detail="Category has child categories and cannot be deleted")

        if self.db.query(Product).filter(Product.category_id == category.id).first():
            raise HTTPException(status_code=400, detail="Category has products and cannot be deleted")

        previous_values = self.activity_log_service.snapshot(category, ["is_active"])
        category.is_active = False
        self.db.commit()
        self.db.refresh(category)
        self.activity_log_service.record(module="Product Categories", action="Deleted", record_id=category.id, record_name=category.name, user=user, description="Product category deactivated", previous_values=previous_values, changed_values=self.activity_log_service.changes(previous_values, category), commit=True)

        return {
            "message": "Product category deleted successfully",
            "category": self._serialize_category(category)
        }


def get_product_category_service(
        db: Session = Depends(get_db),
        user_service: UserService = Depends(get_user_service),
        activity_log_service: ActivityLogService = Depends(get_activity_log_service))-> ProductCategoryService:
    return ProductCategoryService(db, user_service, activity_log_service)
