from fastapi import APIRouter, Depends, File, UploadFile
from app.schemas.users import ProfileUpdate
from app.services.profile_service import ProfileService, get_profile_service
from app.services.token_service import get_bearer_token

router = APIRouter(prefix="/profile", tags=["Profile API"])


@router.get("/")
def get_profile(
    token: str = Depends(get_bearer_token),
    profile_service: ProfileService = Depends(get_profile_service)):

    return profile_service.get_profile(token)


@router.put("/")
def update_profile(
    profile_data: ProfileUpdate,
    token: str = Depends(get_bearer_token),
    profile_service: ProfileService = Depends(get_profile_service)):

    return profile_service.update_profile(token, profile_data)


@router.post("/image")
def upload_profile_image(
    file: UploadFile = File(...),
    token: str = Depends(get_bearer_token),
    profile_service: ProfileService = Depends(get_profile_service)):

    return profile_service.upload_image(token, file)


@router.delete("/image")
def delete_profile_image(
    token: str = Depends(get_bearer_token),
    profile_service: ProfileService = Depends(get_profile_service)):

    return profile_service.delete_image(token)


