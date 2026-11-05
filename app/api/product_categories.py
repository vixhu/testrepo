from typing import List
from fastapi import APIRouter, Depends
from app.schemas.product_categories import ProductCategoryCreate, ProductCategoryStatusUpdate, ProductCategoryUpdate, CategoryTreeResponse
from app.services.product_category_service import ProductCategoryService, get_product_category_service
from app.services.menu_permission_service import require_menu_access

router = APIRouter(prefix="/product-categories", tags=["Product Categories API"])


@router.get("/", response_model=List[CategoryTreeResponse])
def get_all_product_categories(
    token: str = Depends(require_menu_access("products", "Read")),
    product_category_service: ProductCategoryService = Depends(get_product_category_service)):
    return product_category_service.get_all_product_category(token)


@router.get("/{category_slug}", response_model=CategoryTreeResponse)
def get_product_category(
    category_slug: str,
    token: str = Depends(require_menu_access("products", "Read")),
    product_category_service: ProductCategoryService = Depends(get_product_category_service)):
    return product_category_service.get_product_category(category_slug, token)

@router.post("/")
def add_product_category(
    category_data: ProductCategoryCreate,
    token: str = Depends(require_menu_access("products", "Write")),
    product_category_service: ProductCategoryService = Depends(get_product_category_service)):
    return product_category_service.add_product_category(category_data, token)


@router.put("/{category_id}")
def update_product_category(
    category_id: int,
    category_data: ProductCategoryUpdate,
    token: str = Depends(require_menu_access("products", "Write")),
    product_category_service: ProductCategoryService = Depends(get_product_category_service)):
    return product_category_service.update_product_category(category_id, category_data, token)


@router.delete("/{category_id}")
def delete_product_category(
    category_id: int,
    token: str = Depends(require_menu_access("products", "Write")),
    product_category_service: ProductCategoryService = Depends(get_product_category_service)):
    return product_category_service.delete_product_category(category_id, token)


@router.patch("/{category_id}/status")
def set_product_category_status(
    category_id: int,
    status_data: ProductCategoryStatusUpdate,
    token: str = Depends(require_menu_access("products", "Write")),
    product_category_service: ProductCategoryService = Depends(get_product_category_service)):
    return product_category_service.update_product_category(
        category_id,
        ProductCategoryUpdate(is_active=status_data.is_active),
        token,
    )
