from typing import Literal, Optional

from fastapi import APIRouter, Depends, Query

from app.schemas.dashboard import (
    DashboardAnalytics, DashboardSummary, SystemHealth,
    EventSummaryResponse, EventTrendsResponse, TopProductResponse, 
    TopCategoryResponse, RecentEventResponse, DownloadsAnalyticsResponse, 
    ClickAnalyticsResponse, FormAnalyticsResponse
)
from app.services.dashboard_service import DashboardService, get_dashboard_service
from app.services.menu_permission_service import require_menu_access


router = APIRouter(prefix="/dashboard", tags=["Admin Dashboard API"])

AnalyticsPeriod = Literal["today", "last_7_days", "last_30_days"]


def analytics_period_query():
    return Query(
        default="today",
        description="Analytics window: today, last_7_days, or last_30_days",
    )


@router.get("/summary/", response_model=DashboardSummary)
def get_dashboard_summary(
    token: str = Depends(require_menu_access("dashboard", "Read")),
    dashboard_service: DashboardService = Depends(get_dashboard_service),
):
    return dashboard_service.get_summary(token)


@router.get("/analytics/", response_model=DashboardAnalytics)
def get_dashboard_analytics(
    token: str = Depends(require_menu_access("dashboard", "Read")),
    dashboard_service: DashboardService = Depends(get_dashboard_service),
):
    return dashboard_service.get_analytics(token)


@router.get("/recent-activity/")
def get_dashboard_recent_activity(
    limit: int = Query(default=30, ge=1, le=100),
    token: str = Depends(require_menu_access("dashboard", "Read")),
    dashboard_service: DashboardService = Depends(get_dashboard_service),
):
    return dashboard_service.get_recent_activity(token, limit)


@router.get("/activity-logs/")
def get_dashboard_activity_logs(
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=50, ge=1, le=200),
    module: str | None = Query(default=None),
    action: str | None = Query(default=None),
    user_id: int | None = Query(default=None),
    search: str | None = Query(default=None, max_length=255),
    token: str = Depends(require_menu_access("dashboard", "Read")),
    dashboard_service: DashboardService = Depends(get_dashboard_service),
):
    return dashboard_service.get_activity_logs(
        token=token,
        page=page,
        limit=limit,
        module=module,
        action=action,
        user_id=user_id,
        search=search,
    )


@router.get("/system-health/", response_model=SystemHealth)
def get_dashboard_system_health(
    token: str = Depends(require_menu_access("dashboard", "Read")),
    dashboard_service: DashboardService = Depends(get_dashboard_service),
):
    return dashboard_service.get_system_health(token)


@router.get("/event-summary/", response_model=EventSummaryResponse)
def get_event_summary(
    period: AnalyticsPeriod = analytics_period_query(),
    token: str = Depends(require_menu_access("dashboard", "Read")),
    dashboard_service: DashboardService = Depends(get_dashboard_service),
):
    return dashboard_service.get_event_summary(token, period)


@router.get("/event-trends/", response_model=EventTrendsResponse)
def get_event_trends(
    period: AnalyticsPeriod = analytics_period_query(),
    range: Optional[int] = Query(None, description="Legacy range in days; ignored when period is set"),
    token: str = Depends(require_menu_access("dashboard", "Read")),
    dashboard_service: DashboardService = Depends(get_dashboard_service),
):
    return dashboard_service.get_event_trends(token, period=period, range_days=range)


@router.get("/top-products/", response_model=list[TopProductResponse])
def get_top_products(
    limit: int = Query(10),
    period: AnalyticsPeriod = analytics_period_query(),
    token: str = Depends(require_menu_access("dashboard", "Read")),
    dashboard_service: DashboardService = Depends(get_dashboard_service),
):
    return dashboard_service.get_top_products(token, limit, period)


@router.get("/top-product-categories/", response_model=list[TopCategoryResponse])
def get_top_product_categories(
    limit: int = Query(10),
    period: AnalyticsPeriod = analytics_period_query(),
    token: str = Depends(require_menu_access("dashboard", "Read")),
    dashboard_service: DashboardService = Depends(get_dashboard_service),
):
    return dashboard_service.get_top_product_categories(token, limit, period)


@router.get("/recent-events/", response_model=list[RecentEventResponse])
def get_recent_events(
    limit: int = Query(25),
    period: AnalyticsPeriod = analytics_period_query(),
    token: str = Depends(require_menu_access("dashboard", "Read")),
    dashboard_service: DashboardService = Depends(get_dashboard_service),
):
    return dashboard_service.get_recent_events(token, limit, period)


@router.get("/events/")
def get_events(
    event_type: str | None = Query(None),
    start_date: str | None = Query(None),
    end_date: str | None = Query(None),
    period: Optional[AnalyticsPeriod] = Query(default=None, description="today, last_7_days, or last_30_days"),
    page: int = Query(1),
    limit: int = Query(50),
    token: str = Depends(require_menu_access("dashboard", "Read")),
    dashboard_service: DashboardService = Depends(get_dashboard_service),
):
    return dashboard_service.get_events(token, event_type, start_date, end_date, page, limit, period)


@router.get("/downloads/", response_model=DownloadsAnalyticsResponse)
def get_downloads_analytics(
    period: AnalyticsPeriod = analytics_period_query(),
    token: str = Depends(require_menu_access("dashboard", "Read")),
    dashboard_service: DashboardService = Depends(get_dashboard_service),
):
    return dashboard_service.get_downloads_analytics(token, period)


@router.get("/clicks/", response_model=ClickAnalyticsResponse)
def get_clicks_analytics(
    period: AnalyticsPeriod = analytics_period_query(),
    token: str = Depends(require_menu_access("dashboard", "Read")),
    dashboard_service: DashboardService = Depends(get_dashboard_service),
):
    return dashboard_service.get_clicks_analytics(token, period)


@router.get("/forms/", response_model=FormAnalyticsResponse)
def get_forms_analytics(
    period: AnalyticsPeriod = analytics_period_query(),
    token: str = Depends(require_menu_access("dashboard", "Read")),
    dashboard_service: DashboardService = Depends(get_dashboard_service),
):
    return dashboard_service.get_forms_analytics(token, period)
