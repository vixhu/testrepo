from pydantic import BaseModel
from datetime import date


class CertificateCreate(BaseModel):
    title: str
    issued_by: str
    issued_date: date
    expiry_date: date | None = None
    pdf_url: str
    is_active: bool = True


class CertificateUpdate(BaseModel):
    title: str | None = None
    issued_by: str | None = None
    issued_date: date | None = None
    expiry_date: date | None = None
    pdf_url: str | None = None
    is_active: bool | None = None


class CertificateStatusUpdate(BaseModel):
    is_active: bool
