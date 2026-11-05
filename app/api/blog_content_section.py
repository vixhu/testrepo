from fastapi import APIRouter, Depends
from app.schemas.blog_content_section import BlogContentSectionCreate, BlogContentSectionUpdate
from app.services.blog_content_section_service import BlogContentSectionService, get_blog_content_section_service
from app.services.menu_permission_service import require_menu_access


router = APIRouter(prefix="/blogs", tags=["Blog Content Sections API"])


@router.get("/{blog_id}/sections")
def get_sections_by_blog_id(
    blog_id: int,
    token: str = Depends(require_menu_access("blogs", "Read")),
    blog_content_section_service: BlogContentSectionService = Depends(get_blog_content_section_service)):

    return blog_content_section_service.get_blog_content_sections_by_blog_id(blog_id, token)


@router.get("/sections/{section_id}")
def get_section_by_id(
    section_id: int,
    token: str = Depends(require_menu_access("blogs", "Read")),
    blog_content_section_service: BlogContentSectionService = Depends(get_blog_content_section_service)):

    return blog_content_section_service.get_blog_content_section_by_id(section_id, token)


@router.post("/sections")
def create_section(
    section_data: BlogContentSectionCreate,
    token: str = Depends(require_menu_access("blogs", "Write")),
    blog_content_section_service: BlogContentSectionService = Depends(get_blog_content_section_service)):

    return blog_content_section_service.create_blog_content_section(section_data, token)


@router.put("/sections/{section_id}")
def update_section(
    section_id: int,
    section_data: BlogContentSectionUpdate,
    token: str = Depends(require_menu_access("blogs", "Write")),
    blog_content_section_service: BlogContentSectionService = Depends(get_blog_content_section_service)):

    return blog_content_section_service.update_blog_content_section(section_id, section_data, token)


@router.delete("/sections/{section_id}")
def delete_section(
    section_id: int,
    token: str = Depends(require_menu_access("blogs", "Write")),
    blog_content_section_service: BlogContentSectionService = Depends(get_blog_content_section_service)):

    return blog_content_section_service.delete_blog_content_section(section_id, token)
