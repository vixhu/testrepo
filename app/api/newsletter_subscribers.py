from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.services.newsletter_subscriber_service import NewsletterSubscriberService, get_newsletter_subscriber_service
from app.services.menu_permission_service import require_menu_access
from app.schemas.newsletter_subscribers import PaginatedNewsletterSubscriberResponse
from typing import Optional
from datetime import datetime
from fastapi.responses import StreamingResponse

router = APIRouter(prefix="/newsletter-subscribers", tags=["Newsletter Subscribers"])

@router.get("/", response_model=PaginatedNewsletterSubscriberResponse)
def get_subscribers(
    is_active: Optional[bool] = None, 
    page: int = 1, 
    limit: int = 20, 
    token: str = Depends(require_menu_access("newsletter-subscribers", "Read")),
    service: NewsletterSubscriberService = Depends(get_newsletter_subscriber_service)
):
    skip = (page - 1) * limit
    subscribers, total = service.get_subscribers(token, is_active=is_active, skip=skip, limit=limit)
    return {"data": subscribers, "total": total, "page": page, "limit": limit}

@router.get("/export")
def export_subscribers(
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    start_date: Optional[datetime] = Query(None, description="Start date for filtering"),
    end_date: Optional[datetime] = Query(None, description="End date for filtering"),
    token: str = Depends(require_menu_access("newsletter-subscribers", "Read")),
    service: NewsletterSubscriberService = Depends(get_newsletter_subscriber_service)
):
    stream = service.export_subscribers(token, is_active=is_active, start_date=start_date, end_date=end_date)
    filename = "newsletter_subscribers.xlsx"
    headers = {
        "Content-Disposition": f"attachment; filename={filename}"
    }
    return StreamingResponse(
        stream,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers=headers
    )
