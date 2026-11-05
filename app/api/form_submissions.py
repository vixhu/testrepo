from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from datetime import datetime

from app.schemas.form_submissions import FormSubmissionCreate, FormSubmissionFilter, FormSubmissionUpdate
from app.services.form_submission_service import FormSubmissionService, get_form_submission_service
from app.services.menu_permission_service import require_menu_access


router = APIRouter(prefix="/form-submissions", tags=["Form Submissions API"])


@router.get("/")
def get_all_form_submissions(
    page: int = 1,
    limit: int = 20,
    search: str | None = None,
    form_type: str | None = None,
    start_date: datetime | None = None,
    end_date: datetime | None = None,
    token: str = Depends(require_menu_access("forms", "Read")),
    form_submission_service: FormSubmissionService = Depends(get_form_submission_service),
):
    filter_data = FormSubmissionFilter(page=page, limit=limit, search=search, form_type=form_type, start_date=start_date, end_date=end_date)
    return form_submission_service.get_all_form_submissions(filter_data, token)


@router.get("/export")
def export_form_submissions(
    form_type: str | None = Query(None, description="Filter by form type category"),
    start_date: datetime | None = Query(None, description="Start date for filtering"),
    end_date: datetime | None = Query(None, description="End date for filtering"),
    token: str = Depends(require_menu_access("forms", "Read")),
    form_submission_service: FormSubmissionService = Depends(get_form_submission_service),
):
    stream = form_submission_service.export_form_submissions(token, form_type=form_type, start_date=start_date, end_date=end_date)
    filename = "form_submissions.xlsx"
    headers = {
        "Content-Disposition": f"attachment; filename={filename}"
    }
    return StreamingResponse(
        stream,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers=headers
    )


@router.get("/{submission_id}")
def get_form_submission(
    submission_id: int,
    token: str = Depends(require_menu_access("forms", "Read")),
    form_submission_service: FormSubmissionService = Depends(get_form_submission_service),
):
    return form_submission_service.get_form_submission(submission_id, token)


@router.post("/")
def create_form_submission(
    payload: FormSubmissionCreate,
    token: str = Depends(require_menu_access("forms", "Write")),
    form_submission_service: FormSubmissionService = Depends(get_form_submission_service),
):
    return form_submission_service.create_form_submission(payload, token)


@router.put("/{submission_id}")
def update_form_submission(
    submission_id: int,
    payload: FormSubmissionUpdate,
    token: str = Depends(require_menu_access("forms", "Write")),
    form_submission_service: FormSubmissionService = Depends(get_form_submission_service),
):
    return form_submission_service.update_form_submission(submission_id, payload, token)


@router.delete("/{submission_id}")
def delete_form_submission(
    submission_id: int,
    token: str = Depends(require_menu_access("forms", "Write")),
    form_submission_service: FormSubmissionService = Depends(get_form_submission_service),
):
    return form_submission_service.delete_form_submission(submission_id, token)


