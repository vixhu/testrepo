from fastapi import APIRouter, Depends
from app.schemas.forms import FormStatusUpdate, FormUpdate
from app.services.form_service import FormService, get_form_service
from app.services.menu_permission_service import require_menu_access
from app.utils.date_utils import format_datetime_ist

router = APIRouter(prefix="/forms", tags=["Forms API"])


def _serialize_form(form):
    return {
        "id": form.id,
        "title": form.title,
        "form_type": form.form_type,
        "recipient_email": form.recipient_email,
        "cc_email": form.cc_email,
        "auto_reply_enabled": form.auto_reply_enabled,
        "auto_reply_subject": form.auto_reply_subject,
        "auto_reply_message": form.auto_reply_message,
        "is_active": form.is_active,
        "created_at": format_datetime_ist(form.created_at, "%Y-%m-%dT%H:%M:%S+05:30") if form.created_at else None,
        "updated_at": format_datetime_ist(form.updated_at, "%Y-%m-%dT%H:%M:%S+05:30") if form.updated_at else None,
    }


@router.get("")
@router.get("/")
def get_all_forms(token: str = Depends(require_menu_access("forms", "Read")), form_service: FormService = Depends(get_form_service)):
    forms = form_service.get_all_forms(token)
    return [_serialize_form(form) for form in forms]


@router.get("/{form_id}")
def get_form(form_id: int, token: str = Depends(require_menu_access("forms", "Read")), form_service: FormService = Depends(get_form_service)):
    form = form_service.get_form(form_id, token)
    return _serialize_form(form)


@router.put("/{form_id}")
def update_form(form_id: int, form_data: FormUpdate, token: str = Depends(require_menu_access("forms", "Write")), form_service: FormService = Depends(get_form_service)):
    return form_service.update_form(form_id, form_data, token)


@router.put("/{form_id}/status")
def set_form_status(form_id: int, status_data: FormStatusUpdate, token: str = Depends(require_menu_access("forms", "Write")), form_service: FormService = Depends(get_form_service)):
    return form_service.set_form_status(form_id, status_data, token)
