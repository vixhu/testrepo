import asyncio
import logging

from sqlalchemy.orm import Session

from app.models.careers import Career
from app.utils.date_utils import get_utc_now, today_ist

logger = logging.getLogger(__name__)


class ScheduledCareerCloser:
    def __init__(self, db: Session):
        self.db = db

    def close_expired_careers(self):
        today = today_ist()
        careers = (
            self.db.query(Career)
            .filter(
                Career.is_active == True,
                Career.closing_date.isnot(None),
                Career.closing_date <= today,
            )
            .all()
        )
        if not careers:
            return {"message": "No careers to close", "count": 0}

        now = get_utc_now()
        for career in careers:
            career.is_active = False
            career.status = "closed"
            career.updated_at = now
        self.db.commit()
        return {
            "message": f"Closed {len(careers)} expired career(s)",
            "count": len(careers),
        }


async def scheduled_career_closer_task():
    from app.database import SessionLocal

    while True:
        db = SessionLocal()
        try:
            result = ScheduledCareerCloser(db).close_expired_careers()
            if result.get("count"):
                logger.info("[Scheduled Career Closer] %s", result)
        except asyncio.CancelledError:
            raise
        except Exception as e:
            logger.exception("[Scheduled Career Closer Error] %s", e)
        finally:
            db.close()

        try:
            await asyncio.sleep(3 * 60 * 60)
        except asyncio.CancelledError:
            break
