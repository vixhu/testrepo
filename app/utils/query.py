from fastapi import HTTPException


def get_or_404(db, model, record_id, detail: str = "Not found"):
    record = db.query(model).filter(model.id == record_id).first()
    if not record:
        raise HTTPException(status_code=404, detail=detail)
    return record


def ensure_slug_available(db, model, slug: str, exclude_id=None, detail: str | None = None):
    query = db.query(model).filter(model.slug == slug)
    if exclude_id is not None:
        query = query.filter(model.id != exclude_id)
    if query.first():
        raise HTTPException(
            status_code=400,
            detail=detail or f"{model.__name__} with this slug already exists",
        )
