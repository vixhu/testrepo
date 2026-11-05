from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, File, Form, UploadFile
from app.schemas.blogs import BlogCreate, BlogUpdate
from app.services.blog_post_service import BlogPostService, get_blog_post_service
from app.services.menu_permission_service import require_menu_access

router = APIRouter(prefix="/blogs", tags=["Blog Posts API"])


@router.get("/")
def get_all_blogs(
    token: str = Depends(require_menu_access("blogs", "Read")),
    blog_post_service: BlogPostService = Depends(get_blog_post_service)):

    return blog_post_service.get_all_blogs(token)


@router.get("/{blog_id}")
def get_blog_by_id(
    blog_id: int,
    token: str = Depends(require_menu_access("blogs", "Read")),
    blog_post_service: BlogPostService = Depends(get_blog_post_service)):

    return blog_post_service.get_blog_by_id(blog_id, token)


@router.get("/slug/{slug}")
def get_blog_by_slug(
    slug: str,
    token: str = Depends(require_menu_access("blogs", "Read")),
    blog_post_service: BlogPostService = Depends(get_blog_post_service)):

    return blog_post_service.get_blog_by_slug(slug, token)


@router.post("/")
def create_blog(
    category_id: int = Form(...),
    title: str = Form(...),
    slug: str = Form(...),
    status: str = Form("draft"),
    published_at: Optional[datetime] = Form(None),
    scheduled_publish_at: Optional[datetime] = Form(None),
    is_featured: bool = Form(False),
    author_name: Optional[str] = Form(None),
    author_image_url: Optional[str] = Form(None),
    featured_image: Optional[UploadFile] = File(None),
    token: str = Depends(require_menu_access("blogs", "Write")),
    blog_post_service: BlogPostService = Depends(get_blog_post_service)):

    blog_data = BlogCreate(
        category_id=category_id,
        title=title,
        slug=slug,
        status=status,
        published_at=published_at,
        scheduled_publish_at=scheduled_publish_at,
        is_featured=is_featured,
        author_name=author_name,
        author_image_url=author_image_url,
    )

    return blog_post_service.create_blog(blog_data, token, featured_image=featured_image)


@router.put("/{blog_id}")
def update_blog(
    blog_id: int,
    category_id: int = Form(...),
    title: str = Form(...),
    slug: str = Form(...),
    status: str = Form(...),
    published_at: Optional[datetime] = Form(None),
    scheduled_publish_at: Optional[datetime] = Form(None),
    is_featured: bool = Form(False),
    author_name: Optional[str] = Form(None),
    author_image_url: Optional[str] = Form(None),
    featured_image: Optional[UploadFile] = File(None),
    token: str = Depends(require_menu_access("blogs", "Write")),
    blog_post_service: BlogPostService = Depends(get_blog_post_service)):

    blog_data = BlogUpdate(
        blog_id=blog_id,
        category_id=category_id,
        title=title,
        slug=slug,
        status=status,
        published_at=published_at,
        scheduled_publish_at=scheduled_publish_at,
        is_featured=is_featured,
        author_name=author_name,
        author_image_url=author_image_url,
    )

    return blog_post_service.update_blog(blog_data, token, featured_image=featured_image)



@router.post("/{blog_id}/activate")
def set_blog_active(
    blog_id: int,
    token: str = Depends(require_menu_access("blogs", "Write")),
    blog_post_service: BlogPostService = Depends(get_blog_post_service)):

    return blog_post_service.set_blog_active(blog_id, token, True)


@router.delete("/{blog_id}")
def set_blog_inactive(
    blog_id: int,
    token: str = Depends(require_menu_access("blogs", "Write")),
    blog_post_service: BlogPostService = Depends(get_blog_post_service)):

    return blog_post_service.set_blog_active(blog_id, token, False)


@router.post("/upload")
def upload_media(
    file: UploadFile = File(...),
    folder: str = Form("blog-content"),
    token: str = Depends(require_menu_access("blogs", "Write")),
    blog_post_service: BlogPostService = Depends(get_blog_post_service)):

    return blog_post_service.upload_media(file, token, folder_key=folder)
