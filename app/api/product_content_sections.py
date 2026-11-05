from fastapi import APIRouter, Depends

from app.schemas.product_content_section import ProductContentSectionCreate, ProductContentSectionUpdate
from app.services.product_content_section_service import ProductContentSectionService, get_product_content_section_service
from app.services.menu_permission_service import require_menu_access

router = APIRouter(prefix="/products", tags=["Product Content Sections API"])


@router.get("/{product_id}/sections")
def get_sections_by_product_id(
    product_id: int,
    token: str = Depends(require_menu_access("products", "Read")),
    product_content_section_service: ProductContentSectionService = Depends(get_product_content_section_service)):

    return product_content_section_service.get_product_content_sections_by_product_id(product_id, token)


@router.get("/sections/{section_id}")
def get_section_by_id(
    section_id: int,
    token: str = Depends(require_menu_access("products", "Read")),
    product_content_section_service: ProductContentSectionService = Depends(get_product_content_section_service)):

    return product_content_section_service.get_product_content_section_by_id(section_id, token)


@router.post("/sections")
def create_section(
    section_data: ProductContentSectionCreate,
    token: str = Depends(require_menu_access("products", "Write")),
    product_content_section_service: ProductContentSectionService = Depends(get_product_content_section_service)):

    return product_content_section_service.create_product_content_section(section_data, token)


@router.put("/sections/{section_id}")
def update_section(
    section_id: int,
    section_data: ProductContentSectionUpdate,
    token: str = Depends(require_menu_access("products", "Write")),
    product_content_section_service: ProductContentSectionService = Depends(get_product_content_section_service)):

    return product_content_section_service.update_product_content_section(section_id, section_data, token)


@router.delete("/sections/{section_id}")
def delete_section(
    section_id: int,
    token: str = Depends(require_menu_access("products", "Write")),
    product_content_section_service: ProductContentSectionService = Depends(get_product_content_section_service)):

    return product_content_section_service.delete_product_content_section(section_id, token)
