import asyncio
import logging

from sqlalchemy.orm import Session

from app.models.blog_posts import BlogPost
from app.services.activity_log_service import ActivityLogService
from app.utils.date_utils import get_utc_now

logger = logging.getLogger(__name__)


class ScheduledBlogPublisher:
    def __init__(self, db: Session):
        self.db = db

    def publish_scheduled_blogs(self):
        try:
            now = get_utc_now()
            scheduled_blogs = (
                self.db.query(BlogPost)
                .filter(
                    BlogPost.status == "scheduled",
                    BlogPost.scheduled_publish_at <= now,
                    BlogPost.is_active == True,
                )
                .with_for_update(skip_locked=True)
                .all()
            )

            previous_values_by_id = {}
            for blog in scheduled_blogs:
                previous_values_by_id[blog.id] = ActivityLogService(self.db).snapshot(
                    blog,
                    ["status", "published_at", "scheduled_publish_at"],
                )
                blog.status = "published"
                blog.published_at = now
                blog.updated_at = now

            if scheduled_blogs:
                self.db.commit()
                activity_log_service = ActivityLogService(self.db)
                for blog in scheduled_blogs:
                    activity_log_service.record(
                        module="Blogs",
                        action="Published",
                        record_id=blog.id,
                        record_name=blog.title,
                        description="Scheduled blog post published automatically",
                        metadata={"source": "scheduled_publisher"},
                        previous_values=previous_values_by_id[blog.id],
                        changed_values=activity_log_service.changes(previous_values_by_id[blog.id], blog),
                    )
                if activity_log_service.table_exists():
                    self.db.commit()
                return {
                    "message": f"Published {len(scheduled_blogs)} scheduled blog(s)",
                    "count": len(scheduled_blogs),
                }
            return {
                "message": "No scheduled blogs to publish",
                "count": 0,
            }
        except Exception as e:
            self.db.rollback()
            raise Exception(f"Error publishing scheduled blogs: {str(e)}")


def get_scheduled_blog_publisher(db: Session) -> ScheduledBlogPublisher:
    return ScheduledBlogPublisher(db)


async def scheduled_blog_publisher_task():
    from app.database import SessionLocal

    while True:
        db = SessionLocal()
        try:
            publisher = get_scheduled_blog_publisher(db)
            result = publisher.publish_scheduled_blogs()
            if result.get("count"):
                logger.info("[Scheduled Blog Publisher] %s", result)
        except asyncio.CancelledError:
            raise
        except Exception as e:
            logger.exception("[Scheduled Blog Publisher Error] %s", e)
        finally:
            db.close()

        try:
            await asyncio.sleep(300)
        except asyncio.CancelledError:
            break
