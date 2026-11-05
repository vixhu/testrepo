import mimetypes
import re
import uuid
from pathlib import Path

import cloudinary.uploader
from fastapi import HTTPException

PDF_TYPE = "application/pdf"
IMAGE_TYPES = {"image/jpeg", "image/png", "image/webp", "image/gif"}
VIDEO_TYPES = {"video/mp4", "video/webm", "video/quicktime"}
MAX_PDF_SIZE = 10 * 1024 * 1024
MAX_IMAGE_SIZE = 4 * 1024 * 1024
MAX_VIDEO_SIZE = 8 * 1024 * 1024
MAX_DEFAULT_SIZE = 10 * 1024 * 1024

CONTENT_TYPE_EXTENSIONS = {
    "application/pdf": ".pdf",
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
    "model/gltf-binary": ".glb",
    "model/gltf+json": ".gltf",
    "video/mp4": ".mp4",
    "video/webm": ".webm",
    "video/quicktime": ".mov",
}


CLOUDINARY_ROOT = "indication"

CLOUDINARY_FOLDERS = {
    "blog-content": f"{CLOUDINARY_ROOT}/blogs/content",
    "seo-og": f"{CLOUDINARY_ROOT}/seo/og-images",
}


def sanitize_filename(filename: str, max_length: int = 255) -> str:
    name = Path(filename).name
    name = re.sub(r"[^a-zA-Z0-9._-]+", "_", name)
    return name[:max_length] or uuid.uuid4().hex


def public_id_from_name(name: str | None, max_length: int = 240) -> str:
    stem = Path(name or "uploaded_file").name
    while Path(stem).suffix.lower() in CONTENT_TYPE_EXTENSIONS.values():
        stripped = Path(stem).stem
        if stripped == stem:
            break
        stem = stripped
    return sanitize_filename(stem, max_length=max_length)


def cloudinary_folder(*parts: str) -> str:
    segments = [CLOUDINARY_ROOT]
    for part in parts:
        cleaned = re.sub(r"[^a-zA-Z0-9._-]+", "_", str(part).strip()).strip("._")
        if cleaned:
            segments.append(cleaned[:80])
    return "/".join(segments)


def alt_text_for_upload(filename: str, context: str | None = None) -> str:
    context_text = (context or "").strip()
    if context_text and context_text.lower() not in {"unassigned", "uploaded_file", "file"}:
        return context_text[:500]
    stem = Path(filename or "").stem
    text = re.sub(r"[_\-]+", " ", stem)
    text = re.sub(r"\s+", " ", text).strip()
    return (text or "Uploaded file")[:500]


def extension_for(content_type: str | None, filename: str = "") -> str:
    ext = Path(filename or "").suffix
    if ext:
        return ext
    if content_type and content_type in CONTENT_TYPE_EXTENSIONS:
        return CONTENT_TYPE_EXTENSIONS[content_type]
    return mimetypes.guess_extension(content_type or "") or ""


def cloudinary_resource_type(content_type: str | None) -> str:
    if content_type == PDF_TYPE:
        return "raw"
    if content_type and content_type.startswith("video/"):
        return "video"
    if content_type and content_type.startswith("image/"):
        return "image"
    return "auto"


def _rename_if_public_id_has_extension(result: dict, ext: str) -> dict:
    public_id = result.get("public_id") or ""
    last = public_id.rsplit("/", 1)[-1]
    suffix = Path(last).suffix.lower()
    known = {value.lower() for value in CONTENT_TYPE_EXTENSIONS.values()}
    if ext:
        known.add(ext.lower())
    if suffix not in known:
        return result

    target = public_id[: -len(suffix)]
    if not target.rsplit("/", 1)[-1]:
        return result
    try:
        renamed = cloudinary.uploader.rename(
            public_id,
            target,
            overwrite=True,
            invalidate=True,
        )
    except Exception:
        return result
    if renamed.get("secure_url"):
        return {**result, **renamed}
    result["public_id"] = target
    return result


def _file_size_bytes(upload_file) -> int:
    handle = upload_file.file
    position = handle.tell() if hasattr(handle, "tell") else 0
    size = handle.seek(0, 2)
    handle.seek(position or 0)
    try:
        return int(size or 0)
    except (TypeError, ValueError):
        return 0


def upload_to_cloudinary(
    upload_file,
    folder: str,
    *,
    allowed_types: set[str] | None = None,
    max_size: int | None = None,
    public_id: str | None = None,
    unique_public_id: bool = True,
) -> dict:
    if allowed_types and upload_file.content_type not in allowed_types:
        if allowed_types == {PDF_TYPE}:
            raise HTTPException(status_code=400, detail="Only PDF files are allowed")
        if allowed_types == {"image/webp"}:
            raise HTTPException(status_code=400, detail="Only WebP images are allowed")
        if allowed_types == {"video/webm"}:
            raise HTTPException(status_code=400, detail="Only WebM videos are allowed")
        if allowed_types == IMAGE_TYPES:
            raise HTTPException(status_code=400, detail="Only JPEG, PNG, WebP, or GIF images are allowed")
        if allowed_types == VIDEO_TYPES:
            raise HTTPException(status_code=400, detail="Only MP4, WebM, or QuickTime videos are allowed")
        raise HTTPException(status_code=400, detail="Unsupported file type")

    file_size = _file_size_bytes(upload_file)
    upload_file.file.seek(0)

    if max_size is None:
        if upload_file.content_type == PDF_TYPE:
            max_size = MAX_PDF_SIZE
        elif upload_file.content_type and upload_file.content_type.startswith("image/"):
            max_size = MAX_IMAGE_SIZE
        elif upload_file.content_type and upload_file.content_type.startswith("video/"):
            max_size = MAX_VIDEO_SIZE
        else:
            max_size = MAX_DEFAULT_SIZE

    if file_size > max_size:
        limit_mb = max_size / (1024 * 1024)
        actual_mb = file_size / (1024 * 1024)
        raise HTTPException(
            status_code=400,
            detail=f"File is {actual_mb:.1f}MB; the limit is {limit_mb:.0f}MB",
        )

    original = upload_file.filename or "uploaded_file"
    stem = public_id_from_name(public_id or original)
    ext = extension_for(upload_file.content_type, original)
    resource_type = cloudinary_resource_type(upload_file.content_type)

    if unique_public_id:
        public_id_name = f"{stem}_{uuid.uuid4().hex[:8]}"
    else:
        public_id_name = stem

    file_bytes = upload_file.file.read()
    upload_options = {
        "resource_type": resource_type,
        "folder": folder,
        "public_id": public_id_name,
        "overwrite": True,
        "use_filename": False,
        "unique_filename": False,
        "type": "upload",
        "access_mode": "public",
    }
    if resource_type == "raw" and ext:
        upload_options["format"] = ext.lstrip(".")
    try:
        result = cloudinary.uploader.upload(file_bytes, **upload_options)
    except Exception as e:
        message = str(e)
        lowered = message.lower()
        if "too large" in lowered or "maximum is" in lowered:
            actual_mb = file_size / (1024 * 1024)
            raise HTTPException(
                status_code=400,
                detail=f"File is {actual_mb:.1f}MB and was rejected as too large. Use a PDF under 10MB.",
            ) from e
        raise HTTPException(status_code=500, detail=f"Cloudinary upload failed: {message}") from e
    finally:
        upload_file.file.close()

    result = _rename_if_public_id_has_extension(result, ext)

    file_name = f"{public_id_name}{ext}"
    return {
        "url": result.get("secure_url"),
        "file_name": file_name,
        "mime_type": upload_file.content_type,
        "format": result.get("format", upload_file.content_type),
        "alt_text": alt_text_for_upload(original),
    }
