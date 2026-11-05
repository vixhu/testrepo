from fastapi import APIRouter, Depends, File, Query, UploadFile

from app.schemas.menu_permissions import MenuPermissionUpdate
from app.schemas.users import AdminUserCreate, AdminUserUpdate, UserStatusUpdate
from app.services.menu_permission_service import MenuPermissionService, require_menu_access
from app.services.password_service import PasswordService, get_password_service
from app.services.token_service import TokenService
from app.services.user_service import UserService, get_user_service


router = APIRouter(prefix="/users", tags=["Users API"])


@router.get("/")
def get_all_users(
    page: int | None = Query(default=None, ge=1),
    limit: int | None = Query(default=None, ge=1, le=100),
    token: str = Depends(require_menu_access("users", "Read")),
    user_service: UserService = Depends(get_user_service)):

    return user_service.get_all_users(token, page=page, limit=limit)


@router.get("/{user_id}")
def get_user(
    user_id: int,
    token: str = Depends(require_menu_access("users", "Read")),
    user_service: UserService = Depends(get_user_service)):

    return user_service.get_admin_user_by_id(user_id, token)


@router.post("/")
def create_user(
    user_data: AdminUserCreate,
    token: str = Depends(require_menu_access("users", "Write")),
    user_service: UserService = Depends(get_user_service),
    password_service: PasswordService = Depends(get_password_service)):

    hashed_password = password_service.hash_password(user_data.password)
    return user_service.create_admin_user(user_data, hashed_password, token)


@router.post("/{user_id}/image")
def upload_user_image(
    user_id: int,
    file: UploadFile = File(...),
    token: str = Depends(require_menu_access("users", "Write")),
    user_service: UserService = Depends(get_user_service)):

    return user_service.upload_user_image(user_id, file, token)


@router.put("/{user_id}")
def update_user(
    user_id: int,
    user_data: AdminUserUpdate,
    token: str = Depends(require_menu_access("users", "Write")),
    user_service: UserService = Depends(get_user_service),
    password_service: PasswordService = Depends(get_password_service)):

    hashed_password = None
    if user_data.password:
        hashed_password = password_service.hash_password(user_data.password)

    return user_service.update_admin_user(user_id, user_data, token, hashed_password)


@router.patch("/{user_id}/status")
def set_user_status(
    user_id: int,
    status_data: UserStatusUpdate,
    token: str = Depends(require_menu_access("users", "Write")),
    user_service: UserService = Depends(get_user_service)):

    return user_service.set_user_status(user_id, status_data, token)


@router.delete("/{user_id}")
def delete_user(
    user_id: int,
    token: str = Depends(require_menu_access("users", "Write")),
    user_service: UserService = Depends(get_user_service)):

    return user_service.delete_admin_user(user_id, token)


@router.get("/{user_id}/menu-access")
def get_user_menu_access(
    user_id: int,
    token: str = Depends(require_menu_access("users", "Read")),
    user_service: UserService = Depends(get_user_service)):

    return user_service.get_user_menu_access(user_id, token)


@router.put("/{user_id}/menu-access")
def update_user_menu_access(
    user_id: int,
    permission_data: MenuPermissionUpdate,
    token: str = Depends(require_menu_access("users", "Write")),
    user_service: UserService = Depends(get_user_service)):

    admin_user_id = int(TokenService.verify_access_token(token))
    menu_permission_service = MenuPermissionService(user_service.db)
    return menu_permission_service.update_user_menu_access(
        admin_user_id,
        user_id,
        permission_data.menu_slug,
        permission_data.access_level,
    )
