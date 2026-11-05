from fastapi import APIRouter, Depends, UploadFile, File, Query
from app.schemas.certificates import CertificateCreate, CertificateStatusUpdate, CertificateUpdate
from app.services.certificate_service import CertificateService, get_certificate_service
from app.services.menu_permission_service import require_menu_access

router = APIRouter(prefix="/certificates", tags=["Certificates API"])


@router.post("/upload")
def upload_certificate_file(file: UploadFile = File(...), token: str = Depends(require_menu_access("certificates", "Write")), certificate_service: CertificateService = Depends(get_certificate_service)):
    return certificate_service.upload_certificate_file(file, token)


@router.get("/")
def get_all_certificates(
    page: int | None = Query(default=None, ge=1),
    limit: int | None = Query(default=None, ge=1, le=100),
    token: str = Depends(require_menu_access("certificates", "Read")),
    certificate_service: CertificateService = Depends(get_certificate_service),
):
    return certificate_service.get_all_certificates(token, page=page, limit=limit)


@router.get("/{certificate_id}")
def get_certificate(certificate_id: int, token: str = Depends(require_menu_access("certificates", "Read")), certificate_service: CertificateService = Depends(get_certificate_service)):
    return certificate_service.get_certificate(certificate_id, token)


@router.post("/")
def create_certificate(certificate_data: CertificateCreate, token: str = Depends(require_menu_access("certificates", "Write")), certificate_service: CertificateService = Depends(get_certificate_service)):
    return certificate_service.create_certificate(certificate_data, token)


@router.put("/{certificate_id}")
def update_certificate(certificate_id: int, certificate_data: CertificateUpdate, token: str = Depends(require_menu_access("certificates", "Write")), certificate_service: CertificateService = Depends(get_certificate_service)):
    return certificate_service.update_certificate(certificate_id, certificate_data, token)


@router.put("/{certificate_id}/status")
def set_certificate_status(certificate_id: int, status_data: CertificateStatusUpdate, token: str = Depends(require_menu_access("certificates", "Write")), certificate_service: CertificateService = Depends(get_certificate_service)):
    return certificate_service.set_certificate_status(certificate_id, status_data, token)
