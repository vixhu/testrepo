from fastapi import APIRouter, Depends
from app.services.industry_tag_service import IndustryTagService, get_industry_tag_service
from app.services.menu_permission_service import require_menu_access

router = APIRouter(prefix="/industry-tags", tags=["Industry Tags Management"])


@router.get("/")
def get_all_tags(
    token: str = Depends(require_menu_access("products", "Read")),
    service: IndustryTagService = Depends(get_industry_tag_service)):
    return service.get_all_tags(token)


@router.get("/{tag_id}")
def get_tag(
    tag_id: int,
    token: str = Depends(require_menu_access("products", "Read")),
    service: IndustryTagService = Depends(get_industry_tag_service)):
    return service.get_tag_by_id(tag_id, token)


