from fastapi import APIRouter, Depends, Query
from app.schemas.careers import CareerCreate, CareerStatusUpdate, CareerUpdate
from app.services.career_service import CareerService, get_career_service
from app.services.menu_permission_service import require_menu_access

router = APIRouter(prefix="/careers", tags=["Careers API"])


@router.get("/")
def get_all_careers(
    page: int | None = Query(default=None, ge=1),
    limit: int | None = Query(default=None, ge=1, le=100),
    token: str = Depends(require_menu_access("careers", "Read")),
    career_service: CareerService = Depends(get_career_service),
):
    return career_service.get_all_careers(token, page=page, limit=limit)


@router.get("/{career_id}")
def get_career_by_id(career_id: int, token: str = Depends(require_menu_access("careers", "Read")), career_service: CareerService = Depends(get_career_service)):
    return career_service.get_career_by_id(career_id, token)


@router.post("/")
def create_career(career_data: CareerCreate, token: str = Depends(require_menu_access("careers", "Write")), career_service: CareerService = Depends(get_career_service)):
    return career_service.create_career(career_data, token)


@router.put("/{career_id}")
def update_career(career_id: int, career_data: CareerUpdate, token: str = Depends(require_menu_access("careers", "Write")), career_service: CareerService = Depends(get_career_service)):
    return career_service.update_career(career_id, career_data, token)


@router.put("/{career_id}/status")
def set_career_status(career_id: int, status_data: CareerStatusUpdate, token: str = Depends(require_menu_access("careers", "Write")), career_service: CareerService = Depends(get_career_service)):
    return career_service.set_career_status(career_id, status_data, token)


@router.delete("/{career_id}")
def delete_career(career_id: int, token: str = Depends(require_menu_access("careers", "Write")), career_service: CareerService = Depends(get_career_service)):
    return career_service.delete_career(career_id, token)
