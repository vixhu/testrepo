from typing import Optional
from fastapi import APIRouter, Body, Depends, File, UploadFile, Form
from app.schemas.products import ProductCreate, ProductUpdate
from app.services.menu_permission_service import require_menu_access
from app.services.product_service import ProductService, get_product_service
from app.services.product_media_service import ProductMediaService, get_product_media_service


router = APIRouter(prefix="/products", tags=["Product Management API"])


@router.get("/")
def get_all_products(
    token: str = Depends(require_menu_access("products", "Read")),
    product_service: ProductService = Depends(get_product_service),
):
    return product_service.get_all_products(token)


@router.get("/{product_id}")
def get_product(
    product_id: int,
    token: str = Depends(require_menu_access("products", "Read")),
    product_service: ProductService = Depends(get_product_service),
):
    return product_service.get_product(product_id, token)


@router.post("/")
def create_product(
    product_data: ProductCreate,
    token: str = Depends(require_menu_access("products", "Write")),
    product_service: ProductService = Depends(get_product_service),
):
    return product_service.create_product(product_data, token)


@router.put("/{product_id}")
def update_product(
    product_id: int,
    product_data: ProductUpdate,
    token: str = Depends(require_menu_access("products", "Write")),
    product_service: ProductService = Depends(get_product_service),
):
    return product_service.update_product(product_id, product_data, token)


@router.put("/{product_id}/status")
def set_product_status(
    product_id: int,
    is_active: bool = Body(...),
    token: str = Depends(require_menu_access("products", "Write")),
    product_service: ProductService = Depends(get_product_service),
):
    return product_service.set_product_status(product_id, is_active, token)


@router.post("/upload")
def upload_product_media(
    file: UploadFile = File(...),
    product_name: Optional[str] = Form(None),
    media_type: Optional[str] = Form(None),
    is_datasheet: bool = Form(False),
    token: str = Depends(require_menu_access("products", "Write")),
    product_media_service: ProductMediaService = Depends(get_product_media_service),
):
    kind = media_type or ("datasheet" if is_datasheet else "image")
    return product_media_service.upload_media(file, product_name, kind, token)
