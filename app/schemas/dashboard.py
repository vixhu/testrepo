from typing import Any, Optional

from pydantic import BaseModel


class DashboardMetric(BaseModel):
    key: str
    label: str
    value: int


class ContentHealthIssue(BaseModel):
    key: str
    label: str
    count: int
    records: list[dict[str, Any]] = []


class RecentActivityItem(BaseModel):
    module: str
    record_name: str
    action: str
    user: Optional[str] = None
    timestamp: Optional[str] = None
    previous_values: Optional[dict[str, Any]] = None
    changed_values: Optional[dict[str, Any]] = None


class ChartDataPoint(BaseModel):
    label: str
    value: int


class MonthlyContentGrowthPoint(BaseModel):
    month: str
    products: int = 0
    blogs: int = 0
    pages: int = 0
    certificates: int = 0
    catalogues: int = 0
    total: int = 0


class UserActivitySummary(BaseModel):
    total_users: int
    active_users: int
    last_login_activity: list[dict[str, Any]]


class EnquiryLeadSummary(BaseModel):
    new_enquiries_today: int
    new_enquiries_this_week: int
    pending_follow_ups: int


class DashboardAnalytics(BaseModel):
    products_by_category: list[ChartDataPoint]
    products_by_industry: list[ChartDataPoint]
    active_vs_inactive_products: list[ChartDataPoint]
    blogs_by_category: list[ChartDataPoint]
    faqs_by_category: list[ChartDataPoint]
    monthly_content_growth: list[MonthlyContentGrowthPoint]


class SystemHealth(BaseModel):
    status: str
    database: str
    uploaded_files_count: int
    inactive_records_count: int
    draft_content_count: int


class DashboardSummary(BaseModel):
    overview_metrics: list[DashboardMetric]
    content_health: list[ContentHealthIssue]
    analytics: DashboardAnalytics

    user_activity: UserActivitySummary
    enquiry_lead_summary: EnquiryLeadSummary
    recent_activity: list[RecentActivityItem]
    system_health: SystemHealth
    quick_actions: list[dict[str, str]]


class EventSummaryResponse(BaseModel):
    form_submissions: int = 0
    newsletter_signups: int = 0
    contact_button_clicks: int = 0
    email_clicks: int = 0
    whatsapp_clicks: int = 0
    catalogue_downloads: int = 0
    datasheet_downloads: int = 0
    annual_return_downloads: int = 0
    product_clicks: int = 0
    product_category_clicks: int = 0


class EventTrendsResponse(BaseModel):
    labels: list[str]
    datasets: dict[str, list[int]]


class TopProductResponse(BaseModel):
    product_id: int
    product_name: str
    clicks: int


class TopCategoryResponse(BaseModel):
    category_id: int
    category_name: str
    clicks: int


class RecentEventResponse(BaseModel):
    id: int
    event_type: str
    page_slug: Optional[str] = None
    product_name: Optional[str] = None
    created_at: str


class DownloadsAnalyticsResponse(BaseModel):
    catalogue_downloads: int = 0
    datasheet_downloads: int = 0
    annual_return_downloads: int = 0


class ClickAnalyticsResponse(BaseModel):
    contact_button_clicks: int = 0
    email_clicks: int = 0
    whatsapp_clicks: int = 0
    product_clicks: int = 0
    product_category_clicks: int = 0


class FormAnalyticsResponse(BaseModel):
    form_submissions: int = 0
    newsletter_signups: int = 0
