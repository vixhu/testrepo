from app.services.token_service import get_token_service
from app.database import get_db
from fastapi import Depends
from sqlalchemy.orm import Session
from app.models.newsletter_subscribers import NewsletterSubscriber
from app.models.users import User
from app.services.token_service import TokenService
from app.services.activity_log_service import ActivityLogService
from datetime import datetime
from typing import Optional
from app.utils.excel import build_xlsx


class NewsletterSubscriberService:
    def __init__(self, db: Session, token_service: TokenService):
        self.db = db
        self.token_service = token_service

    def get_subscribers(self, token: str, is_active: Optional[bool] = None, skip: int = 0, limit: int = 20):
        self.token_service.verify_access_token(token)
        query = self.db.query(NewsletterSubscriber)
        if is_active is not None:
            query = query.filter(NewsletterSubscriber.is_active == is_active)
        total = query.count()
        subscribers = query.order_by(NewsletterSubscriber.created_at.desc()).offset(skip).limit(limit).all()
        return subscribers, total

    def export_subscribers(self, token: str, is_active: Optional[bool] = None, start_date: Optional[datetime] = None, end_date: Optional[datetime] = None):
        user_id = self.token_service.verify_access_token(token)
        admin_user = self.db.query(User).filter(User.id == user_id).first()

        query = self.db.query(NewsletterSubscriber)
        if is_active is not None:
            query = query.filter(NewsletterSubscriber.is_active == is_active)
        if start_date:
            query = query.filter(NewsletterSubscriber.created_at >= start_date)
        if end_date:
            query = query.filter(NewsletterSubscriber.created_at <= end_date)
        
        subscribers = query.order_by(NewsletterSubscriber.created_at.desc()).all()
        stream = build_xlsx(
            ["ID", "Email", "Status", "Subscribed At"],
            [
                [
                    sub.id,
                    sub.email,
                    "Active" if sub.is_active else "Inactive",
                    sub.created_at.strftime("%Y-%m-%d %H:%M:%S") if sub.created_at else "",
                ]
                for sub in subscribers
            ],
            sheet_title="Newsletter Subscribers",
        )
        
        # Log the activity
        ActivityLogService(self.db).record(
            module="Newsletter Subscribers",
            action="Exported",
            record_id=None,
            record_name="Newsletter Subscribers Export",
            user=admin_user,
            description="Exported newsletter subscribers to Excel",
            metadata={
                "filters": {
                    "is_active": is_active, 
                    "start_date": start_date.isoformat() if start_date else None, 
                    "end_date": end_date.isoformat() if end_date else None
                }, 
                "exported_count": len(subscribers)
            },
            commit=True,
        )
        
        return stream

def get_newsletter_subscriber_service(db: Session = Depends(get_db), token_service: TokenService = Depends(get_token_service)):
    return NewsletterSubscriberService(db, token_service)
