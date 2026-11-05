from collections import Counter, defaultdict
from datetime import date, datetime, timedelta, timezone
from typing import Iterable

from fastapi import Depends, HTTPException
from sqlalchemy import and_, case, extract, func, literal_column, or_, select, text
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.analytics_events import AnalyticsEvent
from app.models.blog_categories import BlogCategory
from app.models.blog_media import BlogMedia
from app.models.blog_posts import BlogPost
from app.models.catalogues import Catalogue
from app.models.careers import Career
from app.models.certificates import Certificate
from app.models.form_submissions import FormSubmission
from app.models.forms import Form
from app.models.media import Media
from app.models.menus import Menu
from app.models.newsletter_subscribers import NewsletterSubscriber
from app.models.product_categories import ProductCategory
from app.models.product_content_sections import ProductContentSection
from app.models.product_industry_tags import IndustryTag
from app.models.products import Product
from app.models.roles import Role
from app.models.seo import SEO
from app.models.users import User
from app.services.activity_log_service import ActivityLogService, get_activity_log_service
from app.services.user_service import UserService, get_user_service
from app.utils.date_utils import IST, format_datetime_ist, format_datetime_ist_full, get_utc_now


class DashboardService:
    DATE_TIME_FORMAT = "%d/%b/%Y %I:%M %p"
    ANALYTICS_PERIODS = {
        "today": "today",
        "yesterday": "today",
        "last_7_days": "last_7_days",
        "last7days": "last_7_days",
        "7d": "last_7_days",
        "last_30_days": "last_30_days",
        "last30days": "last_30_days",
        "30d": "last_30_days",
    }

    def _analytics_bounds(self, period: str | None = "today"):
        key = (period or "today").strip().lower().replace(" ", "_").replace("-", "_")
        resolved = self.ANALYTICS_PERIODS.get(key)
        if not resolved:
            raise HTTPException(
                status_code=400,
                detail="period must be today, last_7_days, or last_30_days",
            )

        now_ist = datetime.now(IST)
        today_start_ist = now_ist.replace(hour=0, minute=0, second=0, microsecond=0)

        if resolved == "today":
            start_ist = today_start_ist
            end_ist = today_start_ist + timedelta(days=1)
        elif resolved == "last_7_days":
            start_ist = today_start_ist - timedelta(days=6)
            end_ist = today_start_ist + timedelta(days=1)
        else:
            start_ist = today_start_ist - timedelta(days=29)
            end_ist = today_start_ist + timedelta(days=1)

        start = start_ist.astimezone(timezone.utc).replace(tzinfo=None)
        end = end_ist.astimezone(timezone.utc).replace(tzinfo=None)

        labels = []
        cursor = start_ist.date()
        last = (end_ist - timedelta(microseconds=1)).date()
        while cursor <= last:
            labels.append(cursor.isoformat())
            cursor += timedelta(days=1)
        return start, end, labels

    def _in_period(self, column, start, end):
        return and_(column >= start, column < end)

    TREND_KEYS = {
        "contact_button_click": "contact_button_clicks",
        "email_click": "email_clicks",
        "whatsapp_click": "whatsapp_clicks",
        "catalogue_download": "catalogue_downloads",
        "datasheet_download": "datasheet_downloads",
        "annual_return_download": "annual_return_downloads",
        "product_click": "product_clicks",
        "product_category_click": "product_category_clicks",
    }
    TABLE_TREND_TYPES = {"form_submission", "newsletter_signup"}

    def _utc_to_ist_date(self, column):
        return func.date(func.timestampadd(literal_column("MINUTE"), 330, column))

    def _as_iso_date(self, value):
        if value is None:
            return None
        if isinstance(value, datetime):
            return value.strftime("%Y-%m-%d")
        if isinstance(value, date):
            return value.isoformat()
        text_value = str(value).strip()
        return text_value[:10] if len(text_value) >= 10 else None

    def _page_slug_tail(self):
        return func.substring_index(AnalyticsEvent.page_slug, "/", -1)

    def _matches_product(self):
        slug_tail = self._page_slug_tail()
        return or_(
            and_(AnalyticsEvent.reference_id.isnot(None), AnalyticsEvent.reference_id == Product.id),
            and_(
                AnalyticsEvent.page_slug.isnot(None),
                or_(
                    AnalyticsEvent.page_slug == Product.slug,
                    slug_tail == Product.slug,
                ),
            ),
        )

    def _matches_product_category(self):
        slug_tail = self._page_slug_tail()
        return or_(
            and_(AnalyticsEvent.reference_id.isnot(None), AnalyticsEvent.reference_id == ProductCategory.id),
            and_(
                AnalyticsEvent.page_slug.isnot(None),
                or_(
                    AnalyticsEvent.page_slug == ProductCategory.slug,
                    slug_tail == ProductCategory.slug,
                ),
            ),
        )

    def _sort_ts(self, value):
        if not value:
            return datetime.min
        if getattr(value, "tzinfo", None):
            return value.astimezone(timezone.utc).replace(tzinfo=None)
        return value

    def _product_name_maps(self):
        rows = self.db.query(Product.id, Product.slug, Product.title).all()
        by_id = {}
        by_slug = {}
        for row in rows:
            title = row.title or row.slug
            if row.id is not None:
                by_id[int(row.id)] = title
            if row.slug:
                by_slug[row.slug] = title
                tail = str(row.slug).strip("/").split("/")[-1]
                if tail:
                    by_slug[tail] = title
        return by_id, by_slug

    def _resolve_product_name(self, event_type, reference_id, page_slug, by_id, by_slug):
        if event_type not in {"product_click", "datasheet_download", "form_submission"}:
            return None
        if reference_id is not None:
            try:
                name = by_id.get(int(reference_id))
            except (TypeError, ValueError):
                name = None
            if name:
                return name
        if not page_slug:
            return None
        slug = str(page_slug).strip()
        if slug in by_slug:
            return by_slug[slug]
        tail = slug.strip("/").split("/")[-1]
        if tail in by_slug:
            return by_slug[tail]
        return None

    def __init__(self, db: Session, user_service: UserService, activity_log_service: ActivityLogService):
        self.db = db
        self.user_service = user_service
        self.activity_log_service = activity_log_service

    def _authorize(self, token: str):
        return self.user_service.get_user_from_token(token)

    def _count(self, model, *criteria) -> int:
        query = self.db.query(func.count(model.id))
        if criteria:
            query = query.filter(*criteria)
        return int(query.scalar() or 0)

    def _count_subquery(self, model, *criteria):
        stmt = select(func.count(model.id))
        if criteria:
            stmt = stmt.where(*criteria)
        return stmt.scalar_subquery()

    def _fmt_dt(self, value) -> str | None:
        return format_datetime_ist_full(value)

    def _record_payload(self, record_id, name, action_url=None):
        return {"id": record_id, "name": name, "action_url": action_url}

    def _user_names(self, user_ids: Iterable[int | None]) -> dict[int, str]:
        ids = {int(user_id) for user_id in user_ids if user_id is not None}
        if not ids:
            return {}
        users = self.db.query(User.id, User.full_name, User.email).filter(User.id.in_(ids)).all()
        return {int(user.id): user.full_name or user.email for user in users}

    def get_overview_metrics(self, token: str):
        self._authorize(token)
        row = self.db.query(
            self._count_subquery(Product).label("total_products"),
            self._count_subquery(Product, Product.is_active == True).label("active_products"),
            self._count_subquery(ProductCategory).label("total_categories"),
            self._count_subquery(IndustryTag).label("total_industry_tags"),
            self._count_subquery(Certificate).label("total_certificates"),
            self._count_subquery(Role).label("total_roles"),
            self._count_subquery(User).label("total_users"),
            self._count_subquery(Catalogue).label("total_catalogues"),
            self._count_subquery(
                BlogPost, and_(BlogPost.is_active == True, BlogPost.status == "published")
            ).label("total_blog_posts"),
        ).one()
        total_products = int(row.total_products or 0)
        active_products = int(row.active_products or 0)

        return [
            {"key": "total_products", "label": "Total Products", "value": total_products},
            {"key": "active_products", "label": "Active Products", "value": active_products},
            {"key": "inactive_products", "label": "Inactive Products", "value": total_products - active_products},
            {"key": "total_categories", "label": "Total Categories", "value": int(row.total_categories or 0)},
            {"key": "total_industry_tags", "label": "Total Industry Tags", "value": int(row.total_industry_tags or 0)},
            {"key": "total_certificates", "label": "Total Certificates", "value": int(row.total_certificates or 0)},
            {"key": "total_roles", "label": "Total Roles", "value": int(row.total_roles or 0)},
            {"key": "total_users", "label": "Total Users", "value": int(row.total_users or 0)},
            {"key": "total_catalogues", "label": "Total Catalogues", "value": int(row.total_catalogues or 0)},
            {"key": "total_blog_posts", "label": "Total Blog Posts", "value": int(row.total_blog_posts or 0)},
        ]

    def get_content_health(self, token: str):
        self._authorize(token)

        products_without_images = self.db.query(Product).filter(
            Product.featured_image_id.is_(None),
        )
        products_without_category = (
            self.db.query(Product)
            .outerjoin(ProductCategory, Product.category_id == ProductCategory.id)
            .filter(or_(Product.category_id.is_(None), ProductCategory.id.is_(None)))
        )
        products_without_seo = (
            self.db.query(Product)
            .outerjoin(SEO, and_(SEO.reference_type == "product", SEO.reference_id == Product.id))
            .filter(or_(SEO.id.is_(None), SEO.meta_title.is_(None), SEO.meta_description.is_(None)))
        )
        blogs_without_featured_image = (
            self.db.query(BlogPost)
            .outerjoin(BlogMedia, and_(BlogMedia.blog_id == BlogPost.id, BlogMedia.is_featured == True))
            .filter(BlogMedia.id.is_(None))
        )
        blogs_without_seo = (
            self.db.query(BlogPost)
            .outerjoin(SEO, and_(SEO.reference_type == "post", SEO.reference_id == BlogPost.id))
            .filter(or_(SEO.id.is_(None), SEO.meta_title.is_(None), SEO.meta_description.is_(None)))
        )
        inactive_records_count = self._inactive_records_count()
        draft_content_count = self._draft_content_count()

        return [
            self._health_issue("products_without_images", "Products without images", products_without_images, Product.title, "/products"),
            self._health_issue("products_without_category", "Products without category", products_without_category, Product.title, "/products"),
            self._health_issue("products_without_seo_metadata", "Products without SEO metadata", products_without_seo, Product.title, "/admin/seo"),
            self._health_issue("blog_posts_without_featured_image", "Blog posts without featured image", blogs_without_featured_image, BlogPost.title, "/admin/blogs"),
            self._health_issue("blog_posts_without_seo_metadata", "Blog posts without SEO metadata", blogs_without_seo, BlogPost.title, "/admin/seo"),
            {"key": "inactive_records_count", "label": "Inactive records count", "count": inactive_records_count, "records": []},
            {"key": "draft_content_count", "label": "Draft content count", "count": draft_content_count, "records": []},
        ]

    def _health_issue(self, key: str, label: str, query, name_column, action_url: str):
        count = int(query.count() or 0)
        records = [
            self._record_payload(item.id, getattr(item, name_column.key), action_url)
            for item in query.order_by(getattr(name_column.class_, "updated_at", name_column.class_.id).desc()).limit(10).all()
        ]
        return {"key": key, "label": label, "count": count, "records": records}

    def get_analytics(self, token: str):
        self._authorize(token)
        return {
            "products_by_category": self._products_by_category(),
            "products_by_industry": self._products_by_industry(),
            "active_vs_inactive_products": [
                {"label": "Active", "value": self._count(Product, Product.is_active == True)},
                {"label": "Inactive", "value": self._count(Product, Product.is_active == False)},
            ],
            "blogs_by_category": self._blogs_by_category(),
            "faqs_by_category": self._faqs_by_category(),
            "monthly_content_growth": self._monthly_content_growth(),
        }

    def _products_by_category(self):
        rows = (
            self.db.query(func.coalesce(ProductCategory.name, "Uncategorized").label("label"), func.count(Product.id).label("value"))
            .select_from(Product)
            .outerjoin(ProductCategory, Product.category_id == ProductCategory.id)
            .group_by(func.coalesce(ProductCategory.name, "Uncategorized"))
            .order_by(func.count(Product.id).desc())
            .all()
        )
        return [{"label": row.label, "value": int(row.value)} for row in rows]

    def _products_by_industry(self):
        tag_names = {int(row.id): row.name for row in self.db.query(IndustryTag.id, IndustryTag.name).all()}
        counts = Counter()
        for industry_tag_ids in self.db.query(Product.industry_tag_id).all():
            ids = industry_tag_ids[0] or []
            if not isinstance(ids, list):
                counts["Unassigned"] += 1
                continue
            if not ids:
                counts["Unassigned"] += 1
            for tag_id in ids:
                try:
                    counts[tag_names.get(int(tag_id), f"Tag #{tag_id}")] += 1
                except (TypeError, ValueError):
                    continue
        return [{"label": label, "value": value} for label, value in counts.most_common()]

    def _blogs_by_category(self):
        rows = (
            self.db.query(func.coalesce(BlogCategory.name, "Uncategorized").label("label"), func.count(BlogPost.id).label("value"))
            .select_from(BlogPost)
            .outerjoin(BlogCategory, BlogPost.category_id == BlogCategory.id)
            .group_by(func.coalesce(BlogCategory.name, "Uncategorized"))
            .order_by(func.count(BlogPost.id).desc())
            .all()
        )
        return [{"label": row.label, "value": int(row.value)} for row in rows]

    def _faqs_by_category(self):
        rows = (
            self.db.query(func.coalesce(ProductCategory.name, "Uncategorized").label("label"), func.count(ProductContentSection.id).label("value"))
            .join(Product, Product.id == ProductContentSection.product_id)
            .outerjoin(ProductCategory, Product.category_id == ProductCategory.id)
            .filter(ProductContentSection.section_type == "faq")
            .group_by(func.coalesce(ProductCategory.name, "Uncategorized"))
            .order_by(func.count(ProductContentSection.id).desc())
            .all()
        )
        return [{"label": row.label, "value": int(row.value)} for row in rows]

    def _monthly_content_growth(self):
        modules = [
            ("products", Product),
            ("blogs", BlogPost),
            ("certificates", Certificate),
            ("catalogues", Catalogue),
        ]
        growth = defaultdict(lambda: {"products": 0, "blogs": 0, "certificates": 0, "catalogues": 0, "total": 0})

        for key, model in modules:
            rows = (
                self.db.query(
                    extract("year", model.created_at).label("year"),
                    extract("month", model.created_at).label("month"),
                    func.count(model.id).label("value"),
                )
                .group_by(extract("year", model.created_at), extract("month", model.created_at))
                .order_by(extract("year", model.created_at), extract("month", model.created_at))
                .all()
            )
            for row in rows:
                if row.year is None or row.month is None:
                    continue
                month_key = f"{int(row.year):04d}-{int(row.month):02d}"
                growth[month_key][key] = int(row.value)
                growth[month_key]["total"] += int(row.value)

        return [{"month": month, **values} for month, values in sorted(growth.items())[-12:]]

    def get_user_activity(self, token: str):
        self._authorize(token)
        rows = (
            self.db.query(User.id, User.full_name, User.email, User.last_login, User.is_active)
            .filter(User.last_login.isnot(None))
            .order_by(User.last_login.desc())
            .limit(10)
            .all()
        )
        return {
            "total_users": self._count(User),
            "active_users": self._count(User, User.is_active == True),
            "last_login_activity": [
                {
                    "id": row.id,
                    "name": row.full_name,
                    "email": row.email,
                    "is_active": bool(row.is_active),
                    "last_login": self._fmt_dt(row.last_login),
                }
                for row in rows
            ],
        }

    def get_enquiry_lead_summary(self, token: str):
        self._authorize(token)
        today_start, today_end, _ = self._analytics_bounds("today")
        now_ist = datetime.now(IST).replace(hour=0, minute=0, second=0, microsecond=0)
        week_start_ist = now_ist - timedelta(days=now_ist.weekday())
        week_start = week_start_ist.astimezone(timezone.utc).replace(tzinfo=None)

        return {
            "new_enquiries_today": self._count(
                FormSubmission, self._in_period(FormSubmission.created_at, today_start, today_end)
            ),
            "new_enquiries_this_week": self._count(FormSubmission, FormSubmission.created_at >= week_start),
            "pending_follow_ups": 0,
        }

    def get_recent_activity(self, token: str, limit: int = 30):
        self._authorize(token)
        logged_activity = self._get_logged_activity(limit)
        if logged_activity:
            return logged_activity

        return self._get_inferred_recent_activity(limit)

    def get_activity_logs(
        self,
        token: str,
        page: int,
        limit: int,
        module: str | None = None,
        action: str | None = None,
        user_id: int | None = None,
        search: str | None = None,
    ):
        self._authorize(token)
        return self.activity_log_service.search(page, limit, module, action, user_id, search)

    def _get_logged_activity(self, limit: int):
        logs = self.activity_log_service.list_recent(limit)
        return [
            {
                "module": log.module,
                "record_name": log.record_name or f"{log.module} #{log.record_id}",
                "action": log.action,
                "user": log.user_name or log.user_email,
                "timestamp": self._fmt_dt(log.created_at),
                "previous_values": self.activity_log_service.format_stored_values(log.previous_values),
                "changed_values": self.activity_log_service.format_stored_values(log.changed_values),
            }
            for log in logs
        ]

    def _get_inferred_recent_activity(self, limit: int):
        modules = [
            ("Products", Product, Product.title),
            ("Blogs", BlogPost, BlogPost.title),
            ("Certificates", Certificate, Certificate.title),
            ("Catalogues", Catalogue, Catalogue.title),
            ("SEO", SEO, SEO.meta_title),
            ("Careers", Career, Career.title),
            ("Roles", Role, Role.role_name),
            ("Users", User, User.full_name),
            ("Forms", Form, Form.title),
            ("Menus", Menu, Menu.name),
        ]

        items = []
        user_ids = []
        per_module_limit = max(5, min(limit, 10))

        for module_name, model, name_column in modules:
            rows = self.db.query(model).order_by(model.updated_at.desc()).limit(per_module_limit).all()
            for row in rows:
                action = "Added"
                actor_id = getattr(row, "created_by", None)
                timestamp = getattr(row, "created_at", None)
                updated_at = getattr(row, "updated_at", None)
                if updated_at and timestamp and updated_at != timestamp:
                    action = "Updated"
                    actor_id = getattr(row, "updated_by", None) or actor_id
                    timestamp = updated_at

                user_ids.append(actor_id)
                record_name = getattr(row, name_column.key) or f"{module_name} #{row.id}"
                items.append(
                    {
                        "module": module_name,
                        "record_name": record_name,
                        "action": action,
                        "user_id": actor_id,
                        "timestamp_value": timestamp,
                    }
                )

        user_names = self._user_names(user_ids)
        items.sort(key=lambda item: item["timestamp_value"] or datetime.min, reverse=True)

        return [
            {
                "module": item["module"],
                "record_name": item["record_name"],
                "action": item["action"],
                "user": user_names.get(int(item["user_id"])) if item["user_id"] else None,
                "timestamp": self._fmt_dt(item["timestamp_value"]),
            }
            for item in items[:limit]
        ]

    def get_system_health(self, token: str):
        self._authorize(token)
        database_status = "ok"
        try:
            self.db.execute(text("SELECT 1"))
        except Exception:
            database_status = "error"

        uploaded_files_count = int(self.db.query(func.count(Media.id)).scalar() or 0)
        inactive_records_count = self._inactive_records_count()
        draft_content_count = self._draft_content_count()

        return {
            "status": "ok" if database_status == "ok" else "degraded",
            "database": database_status,
            "uploaded_files_count": uploaded_files_count,
            "inactive_records_count": inactive_records_count,
            "draft_content_count": draft_content_count,
        }

    def _inactive_records_count(self) -> int:
        inactive_models = [
            (Product, Product.is_active == False),
            (ProductCategory, ProductCategory.is_active == False),
            (IndustryTag, IndustryTag.is_active == False),
            (BlogPost, BlogPost.is_active == False),
            (BlogCategory, BlogCategory.is_active == False),
            (Certificate, Certificate.is_active == False),
            (Catalogue, Catalogue.is_active == False),
            (Career, Career.is_active == False),
            (Form, Form.is_active == False),
            (User, User.is_active == False),
            (SEO, SEO.is_active == False),
            (Role, Role.is_enabled == 0),
        ]
        return sum(self._count(model, criterion) for model, criterion in inactive_models)

    def _draft_content_count(self) -> int:
        return self._count(BlogPost, BlogPost.status == "draft")

    def get_summary(self, token: str):
        return {
            "overview_metrics": self.get_overview_metrics(token),
            "content_health": self.get_content_health(token),
            "analytics": self.get_analytics(token),
            "user_activity": self.get_user_activity(token),
            "enquiry_lead_summary": self.get_enquiry_lead_summary(token),
            "recent_activity": self.get_recent_activity(token),
            "system_health": self.get_system_health(token),
            "quick_actions": [
                {"label": "Add Product", "module": "products", "url": "/products/new"},
                {"label": "Add Blog Post", "module": "blogs", "url": "/blogs/new"},
                {"label": "Upload Catalogue", "module": "catalogues", "url": "/catalogues/new"},
                {"label": "Review SEO", "module": "seo", "url": "/seo"},
                {"label": "Manage Users", "module": "users", "url": "/users"},
            ],
        }

    def get_event_summary(self, token: str, period: str | None = "today"):
        self._authorize(token)
        start, end, _ = self._analytics_bounds(period)
        rows = (
            self.db.query(AnalyticsEvent.event_type, func.count(AnalyticsEvent.id))
            .filter(self._in_period(AnalyticsEvent.created_at, start, end))
            .group_by(AnalyticsEvent.event_type)
            .all()
        )
        counts = {row[0]: row[1] for row in rows}
        return {
            "form_submissions": self._count(
                FormSubmission, self._in_period(FormSubmission.created_at, start, end)
            ),
            "newsletter_signups": self._count(
                NewsletterSubscriber, self._in_period(NewsletterSubscriber.created_at, start, end)
            ),
            "contact_button_clicks": counts.get("contact_button_click", 0),
            "email_clicks": counts.get("email_click", 0),
            "whatsapp_clicks": counts.get("whatsapp_click", 0),
            "catalogue_downloads": counts.get("catalogue_download", 0),
            "datasheet_downloads": counts.get("datasheet_download", 0),
            "annual_return_downloads": counts.get("annual_return_download", 0),
            "product_clicks": counts.get("product_click", 0),
            "product_category_clicks": counts.get("product_category_click", 0),
        }

    def get_event_trends(self, token: str, period: str | None = "today", range_days: int | None = None):
        self._authorize(token)
        if period:
            start, end, labels = self._analytics_bounds(period)
        else:
            days = range_days or 30
            now = get_utc_now()
            now_naive = now.replace(tzinfo=None) if now.tzinfo else now
            start = (now_naive - timedelta(days=days)).replace(hour=0, minute=0, second=0, microsecond=0)
            end = now_naive.replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=1)
            labels = []
            cursor = start.date()
            last = (end - timedelta(microseconds=1)).date()
            while cursor <= last:
                labels.append(cursor.isoformat())
                cursor += timedelta(days=1)

        ist_event_date = self._utc_to_ist_date(AnalyticsEvent.created_at)
        rows = (
            self.db.query(
                ist_event_date.label("date"),
                AnalyticsEvent.event_type,
                func.count(AnalyticsEvent.id).label("count")
            )
            .filter(self._in_period(AnalyticsEvent.created_at, start, end))
            .group_by(ist_event_date, AnalyticsEvent.event_type)
            .order_by(ist_event_date)
            .all()
        )

        datasets = defaultdict(lambda: defaultdict(int))
        for row in rows:
            if row.event_type in self.TABLE_TREND_TYPES:
                continue
            key = self.TREND_KEYS.get(row.event_type)
            date_str = self._as_iso_date(row.date)
            if not key or not date_str:
                continue
            datasets[key][date_str] = int(row.count or 0)

        newsletter_date = self._utc_to_ist_date(NewsletterSubscriber.created_at)
        newsletter_rows = (
            self.db.query(
                newsletter_date.label("date"),
                func.count(NewsletterSubscriber.id).label("count"),
            )
            .filter(self._in_period(NewsletterSubscriber.created_at, start, end))
            .group_by(newsletter_date)
            .all()
        )
        for row in newsletter_rows:
            date_str = self._as_iso_date(row.date)
            if date_str:
                datasets["newsletter_signups"][date_str] = int(row.count or 0)

        form_date = self._utc_to_ist_date(FormSubmission.created_at)
        form_rows = (
            self.db.query(
                form_date.label("date"),
                func.count(FormSubmission.id).label("count"),
            )
            .filter(self._in_period(FormSubmission.created_at, start, end))
            .group_by(form_date)
            .all()
        )
        for row in form_rows:
            date_str = self._as_iso_date(row.date)
            if date_str:
                datasets["form_submissions"][date_str] = int(row.count or 0)

        preferred = [
            "form_submissions",
            "newsletter_signups",
            "product_clicks",
            "whatsapp_clicks",
            "email_clicks",
            "contact_button_clicks",
            "catalogue_downloads",
            "datasheet_downloads",
            "annual_return_downloads",
            "product_category_clicks",
        ]
        final_datasets = {}
        for key in preferred:
            date_counts = datasets.get(key)
            if not date_counts:
                continue
            final_datasets[key] = [int(date_counts.get(label, 0) or 0) for label in labels]
        for key, date_counts in datasets.items():
            if key in final_datasets:
                continue
            final_datasets[key] = [int(date_counts.get(label, 0) or 0) for label in labels]

        return {
            "labels": labels,
            "datasets": final_datasets
        }

    def get_top_products(self, token: str, limit: int = 10, period: str | None = "today"):
        self._authorize(token)
        start, end, _ = self._analytics_bounds(period)
        rows = (
            self.db.query(Product.id, Product.title, func.count(AnalyticsEvent.id).label("clicks"))
            .join(
                AnalyticsEvent,
                and_(
                    AnalyticsEvent.event_type == "product_click",
                    self._matches_product(),
                ),
            )
            .filter(self._in_period(AnalyticsEvent.created_at, start, end))
            .group_by(Product.id, Product.title)
            .order_by(func.count(AnalyticsEvent.id).desc())
            .limit(limit)
            .all()
        )
        return [{"product_id": row.id, "product_name": row.title, "clicks": row.clicks} for row in rows]

    def get_top_product_categories(self, token: str, limit: int = 10, period: str | None = "today"):
        self._authorize(token)
        start, end, _ = self._analytics_bounds(period)
        rows = (
            self.db.query(ProductCategory.id, ProductCategory.name, func.count(AnalyticsEvent.id).label("clicks"))
            .join(
                AnalyticsEvent,
                and_(
                    AnalyticsEvent.event_type == "product_category_click",
                    self._matches_product_category(),
                ),
            )
            .filter(self._in_period(AnalyticsEvent.created_at, start, end))
            .group_by(ProductCategory.id, ProductCategory.name)
            .order_by(func.count(AnalyticsEvent.id).desc())
            .limit(limit)
            .all()
        )
        return [{"category_id": row.id, "category_name": row.name, "clicks": row.clicks} for row in rows]

    def _event_timestamp(self, value):
        if not value:
            return ""
        if getattr(value, "tzinfo", None):
            value = value.astimezone(timezone.utc).replace(tzinfo=None)
        return value.isoformat() + "Z"

    def get_recent_events(self, token: str, limit: int = 25, period: str | None = "today"):
        self._authorize(token)
        start, end, _ = self._analytics_bounds(period)
        events = (
            self.db.query(AnalyticsEvent)
            .filter(
                self._in_period(AnalyticsEvent.created_at, start, end),
                AnalyticsEvent.event_type != "form_submission",
            )
            .order_by(AnalyticsEvent.created_at.desc())
            .limit(limit)
            .all()
        )
        subscribers = (
            self.db.query(NewsletterSubscriber)
            .filter(self._in_period(NewsletterSubscriber.created_at, start, end))
            .order_by(NewsletterSubscriber.created_at.desc())
            .limit(limit)
            .all()
        )
        submissions = (
            self.db.query(FormSubmission)
            .filter(self._in_period(FormSubmission.created_at, start, end))
            .order_by(FormSubmission.created_at.desc())
            .limit(limit)
            .all()
        )
        by_id, by_slug = self._product_name_maps()
        combined = [
            {
                "id": ev.id,
                "event_type": ev.event_type,
                "page_slug": ev.page_slug,
                "product_name": self._resolve_product_name(
                    ev.event_type, ev.reference_id, ev.page_slug, by_id, by_slug
                ),
                "created_at": self._event_timestamp(ev.created_at),
                "_sort": ev.created_at,
            }
            for ev in events
        ]
        combined.extend(
            {
                "id": sub.id,
                "event_type": "form_submission",
                "page_slug": sub.form_type,
                "product_id": sub.product_id,
                "product_name": self._resolve_product_name(
                    "form_submission", sub.product_id, None, by_id, by_slug
                ),
                "created_at": self._event_timestamp(sub.created_at),
                "_sort": sub.created_at,
            }
            for sub in submissions
        )
        combined.extend(
            {
                "id": sub.id,
                "event_type": "newsletter_signup",
                "page_slug": None,
                "product_name": None,
                "created_at": self._event_timestamp(sub.created_at),
                "_sort": sub.created_at,
            }
            for sub in subscribers
        )
        combined.sort(key=lambda item: self._sort_ts(item["_sort"]), reverse=True)
        return [{k: v for k, v in item.items() if k != "_sort"} for item in combined[:limit]]

    def get_events(self, token: str, event_type: str | None = None, start_date: str | None = None, end_date: str | None = None, page: int = 1, limit: int = 50, period: str | None = None):
        self._authorize(token)
        period_start = period_end = None
        if period:
            period_start, period_end, _ = self._analytics_bounds(period)
        if event_type in {"form_submission", "form_submissions"}:
            query = self.db.query(FormSubmission)
            if period_start is not None:
                query = query.filter(self._in_period(FormSubmission.created_at, period_start, period_end))
            else:
                if start_date:
                    query = query.filter(FormSubmission.created_at >= start_date)
                if end_date:
                    query = query.filter(FormSubmission.created_at <= end_date)
            total = query.count()
            submissions = query.order_by(FormSubmission.created_at.desc()).offset((page - 1) * limit).limit(limit).all()
            by_id, by_slug = self._product_name_maps()
            return {
                "data": [
                    {
                        "id": sub.id,
                        "event_type": "form_submission",
                        "reference_id": sub.id,
                        "reference_type": "form",
                        "page_slug": sub.form_type,
                        "product_id": sub.product_id,
                        "product_name": self._resolve_product_name(
                            "form_submission", sub.product_id, None, by_id, by_slug
                        ),
                        "ip_address": sub.ip_address,
                        "user_agent": sub.user_agent,
                        "created_at": self._event_timestamp(sub.created_at),
                    }
                    for sub in submissions
                ],
                "total": total,
                "page": page,
                "limit": limit,
                "total_pages": (total + limit - 1) // limit,
            }

        if event_type in {"newsletter_signup", "newsletter_signups"}:
            query = self.db.query(NewsletterSubscriber)
            if period_start is not None:
                query = query.filter(self._in_period(NewsletterSubscriber.created_at, period_start, period_end))
            else:
                if start_date:
                    query = query.filter(NewsletterSubscriber.created_at >= start_date)
                if end_date:
                    query = query.filter(NewsletterSubscriber.created_at <= end_date)
            total = query.count()
            subscribers = query.order_by(NewsletterSubscriber.created_at.desc()).offset((page - 1) * limit).limit(limit).all()
            return {
                "data": [
                    {
                        "id": sub.id,
                        "event_type": "newsletter_signup",
                        "reference_id": sub.id,
                        "reference_type": None,
                        "page_slug": None,
                        "ip_address": None,
                        "user_agent": None,
                        "created_at": sub.created_at.isoformat() + ("Z" if not sub.created_at.tzinfo else "") if sub.created_at else None,
                    }
                    for sub in subscribers
                ],
                "total": total,
                "page": page,
                "limit": limit,
                "total_pages": (total + limit - 1) // limit,
            }

        query = self.db.query(AnalyticsEvent)
        if event_type:
            query = query.filter(AnalyticsEvent.event_type == event_type)
        if period_start is not None:
            query = query.filter(self._in_period(AnalyticsEvent.created_at, period_start, period_end))
        else:
            if start_date:
                query = query.filter(AnalyticsEvent.created_at >= start_date)
            if end_date:
                query = query.filter(AnalyticsEvent.created_at <= end_date)
            
        total = query.count()
        events = query.order_by(AnalyticsEvent.created_at.desc()).offset((page - 1) * limit).limit(limit).all()
        by_id, by_slug = self._product_name_maps()

        return {
            "data": [
                {
                    "id": ev.id,
                    "event_type": ev.event_type,
                    "reference_id": ev.reference_id,
                    "reference_type": ev.reference_type,
                    "page_slug": ev.page_slug,
                    "product_name": self._resolve_product_name(
                        ev.event_type, ev.reference_id, ev.page_slug, by_id, by_slug
                    ),
                    "ip_address": ev.ip_address,
                    "user_agent": ev.user_agent,
                    "created_at": ev.created_at.isoformat() + ("Z" if not ev.created_at.tzinfo else "") if ev.created_at else None
                }
                for ev in events
            ],
            "total": total,
            "page": page,
            "limit": limit,
            "total_pages": (total + limit - 1) // limit
        }

    def get_downloads_analytics(self, token: str, period: str | None = "today"):
        summary = self.get_event_summary(token, period)
        return {
            "catalogue_downloads": summary["catalogue_downloads"],
            "datasheet_downloads": summary["datasheet_downloads"],
            "annual_return_downloads": summary["annual_return_downloads"],
        }

    def get_clicks_analytics(self, token: str, period: str | None = "today"):
        summary = self.get_event_summary(token, period)
        return {
            "contact_button_clicks": summary["contact_button_clicks"],
            "email_clicks": summary["email_clicks"],
            "whatsapp_clicks": summary["whatsapp_clicks"],
            "product_clicks": summary["product_clicks"],
            "product_category_clicks": summary["product_category_clicks"],
        }

    def get_forms_analytics(self, token: str, period: str | None = "today"):
        summary = self.get_event_summary(token, period)
        return {
            "form_submissions": summary["form_submissions"],
            "newsletter_signups": summary["newsletter_signups"],
        }


def get_dashboard_service(
    db: Session = Depends(get_db),
    user_service: UserService = Depends(get_user_service),
        activity_log_service: ActivityLogService = Depends(get_activity_log_service),
) -> DashboardService:
    return DashboardService(db, user_service, activity_log_service)
