from fastapi import APIRouter, Depends, File, UploadFile
from app.schemas.seo import SeoUpdate
from app.services.seo_service import SeoService, get_seo_service
from app.services.menu_permission_service import require_menu_access

router = APIRouter(prefix="/seo", tags=["SEO API"])


@router.get("")
@router.get("/")
def get_all_seo(
    token: str = Depends(require_menu_access("seo", "Read")),
    seo_service: SeoService = Depends(get_seo_service)):

    return seo_service.get_all_seo(token)


@router.post("/upload")
def upload_og_image(
    file: UploadFile = File(...),
    token: str = Depends(require_menu_access("seo", "Write")),
    seo_service: SeoService = Depends(get_seo_service)):

    return seo_service.upload_og_image(file, token)


@router.get("/{seo_id}")
def get_seo_by_id(
    seo_id: int,
    token: str = Depends(require_menu_access("seo", "Read")),
    seo_service: SeoService = Depends(get_seo_service)):

    return seo_service.get_seo_by_id(seo_id, token)


@router.put("/{seo_id}")
def update_seo(
    seo_id: int,
    seo_data: SeoUpdate,
    token: str = Depends(require_menu_access("seo", "Write")),
    seo_service: SeoService = Depends(get_seo_service)):

    return seo_service.update_seo(seo_id, seo_data, token)


@router.delete("/{seo_id}")
def delete_seo(
    seo_id: int,
    token: str = Depends(require_menu_access("seo", "Write")),
    seo_service: SeoService = Depends(get_seo_service)):
    
    return seo_service.delete_seo(seo_id, token)


@router.patch("/{seo_id}/activate")
def activate_seo(
    seo_id: int,
    token: str = Depends(require_menu_access("seo", "Write")),
    seo_service: SeoService = Depends(get_seo_service)):

    return seo_service.activate_seo(seo_id, token)

