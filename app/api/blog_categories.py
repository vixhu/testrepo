from fastapi import APIRouter, Depends
from app.schemas.blog_categories import BlogCategoryCreate, BlogCategoryStatusUpdate, BlogCategoryUpdate
from app.services.blog_category_service import BlogCategoryService, get_blog_category_service
from app.services.menu_permission_service import require_menu_access

router = APIRouter(prefix="/blog-categories", tags=["Blog Categories API"])

@router.get("/")
def get_all_categories(
    token: str = Depends(require_menu_access("blogs", "Read")),
    blog_category_service: BlogCategoryService = Depends(get_blog_category_service)):

    return blog_category_service.get_all_categories(token)


@router.get("/{category_id}")
def get_category_by_id(
    category_id: int,
    token: str = Depends(require_menu_access("blogs", "Read")),
    blog_category_service: BlogCategoryService = Depends(get_blog_category_service)):

    return blog_category_service.get_category_by_id(category_id, token)


@router.post("/")
def create_category(
    blog_category_create: BlogCategoryCreate,
    token: str = Depends(require_menu_access("blogs", "Write")),
    blog_category_service: BlogCategoryService = Depends(get_blog_category_service)):
    
    return blog_category_service.create_category(blog_category_create, token)


@router.put("/{category_id}")
def update_category(
    category_id: int,
    blog_category_update: BlogCategoryUpdate,
    token: str = Depends(require_menu_access("blogs", "Write")),
    blog_category_service: BlogCategoryService = Depends(get_blog_category_service)):
    return blog_category_service.update_category(category_id, blog_category_update, token)


@router.patch("/{category_id}/status")
def set_category_status(
    category_id: int,
    token: str = Depends(require_menu_access("blogs", "Write")),
    blog_category_service: BlogCategoryService = Depends(get_blog_category_service)):
    
    return blog_category_service.toggle_category_status(category_id, token)
