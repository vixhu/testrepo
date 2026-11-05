from fastapi import APIRouter, Depends, UploadFile, File, Query
from app.schemas.catalogues import CatalogueCreate, CatalogueStatusUpdate, CatalogueUpdate
from app.services.catalogue_service import CatalogueService, get_catalogue_service
from app.services.menu_permission_service import require_menu_access

router = APIRouter(prefix="/catalogues", tags=["Catalogues API"])


@router.post("/upload")
def upload_catalogue_file(file: UploadFile = File(...), token: str = Depends(require_menu_access("catalogues", "Write")), catalogue_service: CatalogueService = Depends(get_catalogue_service)):
    return catalogue_service.upload_catalogue_file(file, token)


@router.post("/")
def create_catalogue(catalogue_data: CatalogueCreate, token: str = Depends(require_menu_access("catalogues", "Write")), catalogue_service: CatalogueService = Depends(get_catalogue_service)):
    return catalogue_service.create_catalogue(catalogue_data, token)


@router.get("/")
def get_all_catalogues(
    page: int | None = Query(default=None, ge=1),
    limit: int | None = Query(default=None, ge=1, le=100),
    token: str = Depends(require_menu_access("catalogues", "Read")),
    catalogue_service: CatalogueService = Depends(get_catalogue_service),
):
    return catalogue_service.get_all_catalogues(token, page=page, limit=limit)


@router.get("/{catalogue_id}")
def get_catalogue(catalogue_id: int, token: str = Depends(require_menu_access("catalogues", "Read")), catalogue_service: CatalogueService = Depends(get_catalogue_service)):
    return catalogue_service.get_catalogue(catalogue_id, token)


@router.put("/{catalogue_id}")
def update_catalogue(catalogue_id: int, catalogue_data: CatalogueUpdate, token: str = Depends(require_menu_access("catalogues", "Write")), catalogue_service: CatalogueService = Depends(get_catalogue_service)):
    return catalogue_service.update_catalogue(catalogue_id, catalogue_data, token)


@router.put("/{catalogue_id}/status")
def set_catalogue_status(catalogue_id: int, status_data: CatalogueStatusUpdate, token: str = Depends(require_menu_access("catalogues", "Write")), catalogue_service: CatalogueService = Depends(get_catalogue_service)):
    return catalogue_service.set_catalogue_status(catalogue_id, status_data, token)
