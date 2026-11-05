from fastapi import APIRouter, Depends, UploadFile, File, Query
from app.schemas.annual_returns import AnnualReturnCreate, AnnualReturnStatusUpdate, AnnualReturnUpdate
from app.services.annual_return_service import AnnualReturnService, get_annual_return_service
from app.services.menu_permission_service import require_menu_access

router = APIRouter(prefix="/annual-returns", tags=["Annual Returns API"])


@router.post("/upload")
def upload_annual_return_file(file: UploadFile = File(...), token: str = Depends(require_menu_access("annual-returns", "Write")), annual_return_service: AnnualReturnService = Depends(get_annual_return_service)):
    return annual_return_service.upload_annual_return_file(file, token)


@router.get("/")
def get_all_annual_returns(
    page: int | None = Query(default=None, ge=1),
    limit: int | None = Query(default=None, ge=1, le=100),
    token: str = Depends(require_menu_access("annual-returns", "Read")),
    annual_return_service: AnnualReturnService = Depends(get_annual_return_service),
):
    return annual_return_service.get_all_annual_returns(token, page=page, limit=limit)


@router.post("/")
def create_annual_return(annual_return_data: AnnualReturnCreate, token: str = Depends(require_menu_access("annual-returns", "Write")), annual_return_service: AnnualReturnService = Depends(get_annual_return_service)):
    return annual_return_service.create_annual_return(annual_return_data, token)


@router.put("/{annual_return_id}")
def update_annual_return(annual_return_id: int, annual_return_data: AnnualReturnUpdate, token: str = Depends(require_menu_access("annual-returns", "Write")), annual_return_service: AnnualReturnService = Depends(get_annual_return_service)):
    return annual_return_service.update_annual_return(annual_return_id, annual_return_data, token)


@router.put("/{annual_return_id}/status")
def set_annual_return_status(annual_return_id: int, status_data: AnnualReturnStatusUpdate, token: str = Depends(require_menu_access("annual-returns", "Write")), annual_return_service: AnnualReturnService = Depends(get_annual_return_service)):
    return annual_return_service.set_annual_return_status(annual_return_id, status_data, token)