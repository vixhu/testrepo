from datetime import datetime, timezone

from fastapi import Depends, HTTPException
from fastapi import UploadFile
from sqlalchemy import case, text
from sqlalchemy.exc import DataError, IntegrityError
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.blog_categories import BlogCategory
from app.models.blog_media import BlogMedia
from app.models.media import Media
from app.models.seo import SEO
from app.models.blog_posts import BlogPost
from app.models.users import User
from app.schemas.blogs import BlogCreate, BlogUpdate
from app.services.activity_log_service import ActivityLogService, get_activity_log_service
from app.services.user_service import UserService, get_user_service
from app.utils.date_utils import format_datetime_ist, format_datetime_ist_full, get_utc_now
from app.utils.files import CLOUDINARY_FOLDERS, alt_text_for_upload, cloudinary_folder, upload_to_cloudinary
from app.utils.query import ensure_slug_available


class BlogPostService:
    ALLOWED_MIME_TYPE = "image/webp"
    ALLOWED_STATUSES = {"draft", "published", "scheduled"}
    _status_enum_ready = False
    _author_columns_ready = False

    def __init__(self, db,
        user_service: UserService,
        activity_log_service: ActivityLogService):
        
        self.db = db
        self.user_service = user_service
        self.activity_log_service = activity_log_service

    def _naive_utc(self, value: datetime | None):
        if value is None:
            return None
        if value.tzinfo is not None:
            return value.astimezone(timezone.utc).replace(tzinfo=None)
        return value

    def _published_at_for_status(self, status: str, published_at: datetime | None, existing: datetime | None = None):
        if status == "published":
            return self._naive_utc(published_at) or self._naive_utc(get_utc_now())
        if published_at is not None:
            return self._naive_utc(published_at)
        return existing

    def _has_upload(self, upload_file: UploadFile | None):
        return bool(upload_file is not None and (upload_file.filename or "").strip())

    def _validate_status(self, status: str):
        if status not in self.ALLOWED_STATUSES:
            raise HTTPException(
                status_code=400,
                detail="Status must be draft, published, or scheduled",
            )

    def _ensure_slug_available(self, slug: str, exclude_id: int | None = None):
        ensure_slug_available(
            self.db,
            BlogPost,
            slug,
            exclude_id=exclude_id,
            detail="A blog post with this slug already exists",
        )

    def _ensure_scheduled_status_supported(self):
        if BlogPostService._status_enum_ready:
            return
        try:
            row = self.db.execute(text("SHOW COLUMNS FROM blog_posts LIKE 'status'")).fetchone()
            column_type = str(row[1] if row is not None else "").lower()
            if "scheduled" not in column_type:
                self.db.execute(
                    text(
                        "ALTER TABLE blog_posts MODIFY COLUMN status "
                        "ENUM('draft','published','scheduled') NOT NULL DEFAULT 'draft'"
                    )
                )
                self.db.commit()
        except Exception:
            self.db.rollback()
        finally:
            BlogPostService._status_enum_ready = True

    def _ensure_author_columns(self):
        if BlogPostService._author_columns_ready:
            return
        try:
            rows = self.db.execute(text("SHOW COLUMNS FROM blog_posts")).fetchall()
            if not isinstance(rows, (list, tuple)):
                return
            names = {str(row[0]) for row in rows if row}
            if "author_name" not in names:
                self.db.execute(text("ALTER TABLE blog_posts ADD COLUMN author_name VARCHAR(255) NULL"))
            if "author_image_url" not in names:
                self.db.execute(text("ALTER TABLE blog_posts ADD COLUMN author_image_url VARCHAR(500) NULL"))
            self.db.commit()
        except Exception:
            self.db.rollback()
        finally:
            BlogPostService._author_columns_ready = True

    def _author_from_user(self, user: User, name: str | None = None, image_url: str | None = None):
        stored_name = (name or "").strip() or (user.full_name if user else None)
        stored_image = (image_url or "").strip() or (user.profile_image_url if user else None)
        return stored_name, stored_image

    def _save_featured_image(self, blog: BlogPost, upload_file: UploadFile, user_id: int):
        result = upload_to_cloudinary(
            upload_file,
            cloudinary_folder("blogs", blog.slug, "featured"),
            allowed_types={self.ALLOWED_MIME_TYPE},
        )

        media_record = Media(
            file_name=result["file_name"],
            url=result["url"],
            mime_type=result["mime_type"],
            alt_text=alt_text_for_upload(upload_file.filename or result["file_name"], blog.title),
            created_by=user_id,
            updated_by=user_id,
        )
        self.db.add(media_record)
        self.db.flush()

        featured_link = self.db.query(BlogMedia).filter(
            BlogMedia.blog_id == blog.id,
            BlogMedia.is_featured == True
        ).first()

        if featured_link:
            featured_link.media_id = media_record.id
            featured_link.display_order = 1
            featured_link.updated_by = user_id
        else:
            featured_link = BlogMedia(
                blog_id=blog.id,
                media_id=media_record.id,
                is_featured=True,
                display_order=1,
                created_by=user_id,
                updated_by=user_id,
            )
            self.db.add(featured_link)

        return media_record

    def _serialize_featured_image(self, blog_id: int):
        featured_link = self.db.query(BlogMedia).filter(
            BlogMedia.blog_id == blog_id,
            BlogMedia.is_featured == True
        ).first()

        if not featured_link:
            return None

        media = self.db.query(Media).filter(Media.id == featured_link.media_id).first()
        if not media:
            return None

        media_payload = {
            "id": media.id,
            "file_name": media.file_name,
            "url": media.url,
            "mime_type": media.mime_type,
            "alt_text": media.alt_text,
        }

        return {
            "blog_media": {
                "id": featured_link.id,
                "blog_id": featured_link.blog_id,
                "media_id": featured_link.media_id,
                "is_featured": bool(featured_link.is_featured),
                "display_order": featured_link.display_order,
            },
            "media": media_payload,
            "featured_image": media_payload,
        }

    def _author_payload(self, post: BlogPost, user: User | None):
        return {
            "author_name": getattr(post, "author_name", None) or (user.full_name if user else None),
            "author_image_url": getattr(post, "author_image_url", None) or (user.profile_image_url if user else None),
        }

    def _users_by_ids(self, user_ids):
        ids = {user_id for user_id in user_ids if user_id}
        if not ids:
            return {}
        return {user.id: user for user in self.db.query(User).filter(User.id.in_(ids)).all()}

    def _serialize(self, post: BlogPost, category_name: str | None = None, author: User | None = None):
        payload = {
            "id": post.id,
            "category_id": post.category_id,
            "category_name": category_name,
            "title": post.title,
            "slug": post.slug,
            "featured_image": self._serialize_featured_image(post.id),
            "status": post.status,
            "published_at": format_datetime_ist(post.published_at) if post.published_at else None,
            "scheduled_publish_at": format_datetime_ist_full(post.scheduled_publish_at) if post.scheduled_publish_at else None,
            "is_featured": bool(post.is_featured),
            "is_active": bool(post.is_active),
            "view_count": post.view_count,
            "created_at": format_datetime_ist(post.created_at) if post.created_at else None,
            "created_by": post.created_by,
            "updated_at": format_datetime_ist(post.updated_at) if post.updated_at else None,
            "updated_by": post.updated_by,
        }
        payload.update(self._author_payload(post, author))
        return payload

    def get_all_blogs(self, token: str):
        self.user_service.get_user_from_token(token)
        self._ensure_author_columns()

        posts = (
            self.db.query(BlogPost, BlogCategory.name.label("category_name"))
            .outerjoin(BlogCategory, BlogPost.category_id == BlogCategory.id)
            .order_by(
                case(
                    (
                        (BlogPost.is_active == True) & (BlogPost.status == "published"),
                        0,
                    ),
                    ((BlogPost.is_active == True), 1),
                    ((BlogPost.status == "published"), 2),
                    else_=3,
                ),
                BlogPost.created_at.desc(),
            )
            .all()
        )

        authors = self._users_by_ids(post.created_by for post, _ in posts)
        grouped_posts = {}

        for post, category_name in posts:
            category_id = post.category_id
            category_name = category_name or "Uncategorized"

            if category_id not in grouped_posts:
                grouped_posts[category_id] = {
                    "category_id": category_id,
                    "category_name": category_name,
                    "blogs": [],
                }

            grouped_posts[category_id]["blogs"].append(
                self._serialize(post, category_name, authors.get(post.created_by))
            )

        return list(grouped_posts.values())

    def get_blog_by_id(self, blog_id: int, token: str):
        self.user_service.get_user_from_token(token)
        self._ensure_author_columns()

        post = self.db.query(BlogPost).filter(BlogPost.id == blog_id).first()
        if not post:
            return None

        author = self.db.query(User).filter(User.id == post.created_by).first() if post.created_by else None
        return self._serialize(post, author=author)

    def get_blog_by_slug(self, slug: str, token: str):
        self.user_service.get_user_from_token(token)

        post = self.db.query(BlogPost).filter(BlogPost.slug == slug, BlogPost.is_active == True).first()
        if not post:
            return None

        author = self.db.query(User).filter(User.id == post.created_by).first() if post.created_by else None
        return self._serialize(post, author=author)

    def create_blog(self, payload: BlogCreate, token: str, featured_image: UploadFile | None = None):
        user = self.user_service.get_user_from_token(token)
        self._validate_status(payload.status)
        self._ensure_slug_available(payload.slug)
        self._ensure_scheduled_status_supported()
        self._ensure_author_columns()

        author_name, author_image_url = self._author_from_user(
            user, payload.author_name, payload.author_image_url
        )
        post = BlogPost(
            category_id=payload.category_id,
            title=payload.title,
            slug=payload.slug,
            author_name=author_name,
            author_image_url=author_image_url,
            status=payload.status,
            published_at=self._published_at_for_status(payload.status, payload.published_at),
            scheduled_publish_at=self._naive_utc(payload.scheduled_publish_at),
            is_featured=payload.is_featured,
            created_by=user.id,
            updated_by=user.id,
        )

        try:
            self.db.add(post)
            self.db.flush()

            if self._has_upload(featured_image):
                self._save_featured_image(post, featured_image, user.id)

            seo_record = SEO(
                reference_type="post",
                reference_id=post.id,
                meta_title=post.title,
                created_by=user.id,
            )
            self.db.add(seo_record)
            self.db.commit()
            self.db.refresh(post)
        except HTTPException:
            self.db.rollback()
            raise
        except IntegrityError:
            self.db.rollback()
            raise HTTPException(status_code=400, detail="A blog post with this slug already exists")
        except DataError:
            self.db.rollback()
            raise HTTPException(status_code=400, detail="Invalid blog post data")

        self.activity_log_service.record(
            module="Blogs",
            action="Added",
            record_id=post.id,
            record_name=post.title,
            user=user,
            description="Blog post created",
            metadata={"status": post.status},
            commit=True,
        )

        return {"message": "Blog created successfully", "id": post.id}

    def update_blog(self, payload: BlogUpdate, token: str, featured_image: UploadFile | None = None):
        user = self.user_service.get_user_from_token(token)

        post = self.db.query(BlogPost).filter(BlogPost.id == payload.blog_id, BlogPost.is_active == True).first()
        if not post:
            raise HTTPException(status_code=404, detail="Blog post not found")

        self._validate_status(payload.status)
        self._ensure_slug_available(payload.slug, exclude_id=post.id)
        self._ensure_scheduled_status_supported()
        self._ensure_author_columns()

        previous_values = self.activity_log_service.snapshot(post)
        post.category_id = payload.category_id
        post.title = payload.title
        post.slug = payload.slug
        post.status = payload.status
        post.published_at = self._published_at_for_status(payload.status, payload.published_at, post.published_at)
        post.scheduled_publish_at = self._naive_utc(payload.scheduled_publish_at)
        post.is_featured = payload.is_featured
        post.updated_by = user.id
        author_name, author_image_url = self._author_from_user(
            user, payload.author_name, payload.author_image_url
        )
        if (payload.author_name or "").strip() or not post.author_name:
            post.author_name = author_name
        if (payload.author_image_url or "").strip() or not post.author_image_url:
            post.author_image_url = author_image_url

        try:
            self.db.add(post)

            if self._has_upload(featured_image):
                self._save_featured_image(post, featured_image, user.id)

            self.db.commit()
            self.db.refresh(post)
        except HTTPException:
            self.db.rollback()
            raise
        except IntegrityError:
            self.db.rollback()
            raise HTTPException(status_code=400, detail="A blog post with this slug already exists")
        except DataError:
            self.db.rollback()
            raise HTTPException(status_code=400, detail="Invalid blog post data")
        self.activity_log_service.record(
            module="Blogs",
            action="Updated",
            record_id=post.id,
            record_name=post.title,
            user=user,
            description="Blog post updated",
            metadata={"status": post.status},
            previous_values=previous_values,
            changed_values=self.activity_log_service.changes(previous_values, post),
            commit=True,
        )

        return {"message": "Blog updated successfully", "id": post.id}

    def set_blog_active(self, blog_id: int, token: str, is_active: bool):
        user = self.user_service.get_user_from_token(token)

        post = self.db.query(BlogPost).filter(BlogPost.id == blog_id).first()
        if not post or (not is_active and not post.is_active):
            raise HTTPException(status_code=404, detail="Blog post not found")

        previous_values = self.activity_log_service.snapshot(post, ["is_active"])
        post.is_active = is_active
        post.updated_by = user.id
        self.db.commit()
        self.activity_log_service.record(
            module="Blogs",
            action="Activated" if is_active else "Deleted",
            record_id=post.id,
            record_name=post.title,
            user=user,
            description="Blog post status changed",
            metadata={"is_active": post.is_active},
            previous_values=previous_values,
            changed_values=self.activity_log_service.changes(previous_values, post),
            commit=True,
        )

        action = "activated" if is_active else "deleted"
        return {"message": f"Blog post {action} successfully"}

    def upload_media(self, upload_file: UploadFile, token: str, folder_key: str = "blog-content"):
        user = self.user_service.get_user_from_token(token)
        folder = CLOUDINARY_FOLDERS.get(folder_key, CLOUDINARY_FOLDERS["blog-content"])
        result = upload_to_cloudinary(
            upload_file,
            folder,
            allowed_types={self.ALLOWED_MIME_TYPE},
        )

        media_record = Media(
            file_name=result["file_name"],
            url=result["url"],
            mime_type=result["mime_type"],
            alt_text=alt_text_for_upload(upload_file.filename or result["file_name"]),
            created_by=user.id,
            updated_by=user.id,
        )
        self.db.add(media_record)
        self.db.commit()
        self.db.refresh(media_record)
        self.activity_log_service.record(
            module="Media",
            action="Uploaded",
            record_id=media_record.id,
            record_name=result["file_name"],
            user=user,
            description="Blog image uploaded",
            metadata={"mime_type": result["mime_type"]},
            commit=True,
        )

        return {
            "id": media_record.id,
            "url": result["url"],
            "file_name": result["file_name"],
            "mime_type": result["mime_type"],
            "alt_text": media_record.alt_text,
        }


def get_blog_post_service(
        db: Session = Depends(get_db),
        user_service: UserService = Depends(get_user_service),
        activity_log_service: ActivityLogService = Depends(get_activity_log_service))-> BlogPostService:
    return BlogPostService(db, user_service, activity_log_service)
