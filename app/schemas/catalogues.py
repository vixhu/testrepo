from pydantic import BaseModel

class CatalogueCreate(BaseModel):
    title: str
    pdf_url: str
    is_active: bool = True

class CatalogueUpdate(BaseModel):
    title: str | None = None
    pdf_url: str | None = None
    is_active: bool | None = None

class CatalogueStatusUpdate(BaseModel):
    is_active: bool
