from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas.menu_permissions import MenuPermissionUpdate
from app.schemas.users import UserLogin
from app.services.menu_permission_service import MenuPermissionService, require_menu_access
from app.services.auth_service import AuthService, get_auth_service
from app.services.token_service import TokenService, get_bearer_token
from app.utils.request import get_client_ip, get_user_agent

router = APIRouter(prefix="/auth", tags=["Authentication API"])

@router.post("/login")
def login(
    credentials: UserLogin,
    request: Request,
    auth_service: AuthService = Depends(get_auth_service),
):
    return auth_service.login(
        credentials.email,
        credentials.password,
        ip_address=get_client_ip(request),
        user_agent=get_user_agent(request),
    )


@router.get("/my-menus")
def my_menus(
    token: str = Depends(get_bearer_token),
    db: Session = Depends(get_db)):

    user_id = int(TokenService.verify_access_token(token))
    menu_permission_service = MenuPermissionService(db)
    return menu_permission_service.get_user_menu_permissions(user_id)


@router.put("/users/{user_id}/menu-access")
def update_user_menu_access(
    user_id: int,
    permission_data: MenuPermissionUpdate,
    token: str = Depends(require_menu_access("users", "Write")),
    db: Session = Depends(get_db)):

    admin_user_id = int(TokenService.verify_access_token(token))
    menu_permission_service = MenuPermissionService(db)
    return menu_permission_service.update_user_menu_access(
        admin_user_id,
        user_id,
        permission_data.menu_slug,
        permission_data.access_level,
    )
