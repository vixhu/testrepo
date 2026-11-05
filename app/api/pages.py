from fastapi import APIRouter, Depends

from app.services.menu_permission_service import require_menu_access
from app.services.page_service import PageService, get_page_service


router = APIRouter(prefix="/pages", tags=["Pages API"])


@router.get("/")
def get_pages(
    token: str = Depends(require_menu_access("pages", "Read")),
    page_service: PageService = Depends(get_page_service),
):
    return page_service.get_pages(token)


@router.get("/{slug}/content")
def get_page_content(
    slug: str,
    token: str = Depends(require_menu_access("pages", "Read")),
    page_service: PageService = Depends(get_page_service),
):
    return page_service.get_page_content(slug, token)


@router.get("/{slug}")
def get_page_by_slug(
    slug: str,
    token: str = Depends(require_menu_access("pages", "Read")),
    page_service: PageService = Depends(get_page_service),
):
    return page_service.get_page_by_slug(slug, token)
