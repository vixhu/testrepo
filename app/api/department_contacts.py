from fastapi import APIRouter, Depends
from app.schemas.department_contact import DepartmentContactCreate, DepartmentContactUpdate, DepartmentContactStatusUpdate
from app.services.department_contact_service import DepartmentContactService, get_department_contact_service
from app.services.menu_permission_service import require_menu_access

router = APIRouter(prefix="/department-contacts", tags=["Department Contacts API"])


@router.get("/")
def get_all_department_contacts(token: str = Depends(require_menu_access("department_contact", "Read")), department_contact_service: DepartmentContactService = Depends(get_department_contact_service)):
    return department_contact_service.get_department_contacts(token)


@router.get("/{department_contact_id}")
def get_department_contact(department_contact_id: int, token: str = Depends(require_menu_access("department_contact", "Read")), department_contact_service: DepartmentContactService = Depends(get_department_contact_service)):
    return department_contact_service.get_department_contact(department_contact_id, token)


@router.post("/")
def create_department_contact(department_contact_data: DepartmentContactCreate, token: str = Depends(require_menu_access("department_contact", "Write")), department_contact_service: DepartmentContactService = Depends(get_department_contact_service)):
    return department_contact_service.create_department_contact(department_contact_data, token)


@router.put("/{department_contact_id}")
def update_department_contact(department_contact_id: int, department_contact_data: DepartmentContactUpdate, token: str = Depends(require_menu_access("department_contact", "Write")), department_contact_service: DepartmentContactService = Depends(get_department_contact_service)):
    return department_contact_service.update_department_contact(department_contact_id, department_contact_data, token)


@router.put("/{department_contact_id}/status")
def set_department_contact_status(department_contact_id: int, status_data: DepartmentContactStatusUpdate, token: str = Depends(require_menu_access("department_contact", "Write")), department_contact_service: DepartmentContactService = Depends(get_department_contact_service)):
    return department_contact_service.set_department_contact_status(department_contact_id, status_data, token)