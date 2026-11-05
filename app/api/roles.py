from fastapi import APIRouter, Depends

from app.schemas.roles import RoleCreate, RoleMenuCreate, RoleMenuUpdate, RoleUpdate
from app.services.menu_permission_service import require_menu_access
from app.services.role_service import RoleService, get_role_service


router = APIRouter(prefix="/roles", tags=["Roles API"])


@router.get("/")
def get_all_roles(
    token: str = Depends(require_menu_access("roles", "Read")),
    role_service: RoleService = Depends(get_role_service),
):
    return role_service.get_all_roles(token)


@router.get("/{role_id}")
def get_role_by_id(
    role_id: int,
    token: str = Depends(require_menu_access("roles", "Read")),
    role_service: RoleService = Depends(get_role_service),
):
    return role_service.get_role_by_id(role_id, token)


@router.post("/")
def create_role(
    role_data: RoleCreate,
    token: str = Depends(require_menu_access("roles", "Write")),
    role_service: RoleService = Depends(get_role_service),
):
    return role_service.create_role(role_data, token)


@router.put("/{role_id}")
def update_role(
    role_id: int,
    role_data: RoleUpdate,
    token: str = Depends(require_menu_access("roles", "Write")),
    role_service: RoleService = Depends(get_role_service),
):
    return role_service.update_role(role_id, role_data, token)


@router.delete("/{role_id}")
def delete_role(
    role_id: int,
    token: str = Depends(require_menu_access("roles", "Write")),
    role_service: RoleService = Depends(get_role_service),
):
    return role_service.delete_role(role_id, token)


@router.get("/{role_id}/menus")
def get_role_menus(
    role_id: int,
    token: str = Depends(require_menu_access("roles", "Read")),
    role_service: RoleService = Depends(get_role_service),
):
    return role_service.get_role_menus(role_id, token)


@router.get("/role-menus/{role_menu_id}")
def get_role_menu_by_id(
    role_menu_id: int,
    token: str = Depends(require_menu_access("roles", "Read")),
    role_service: RoleService = Depends(get_role_service),
):
    return role_service.get_role_menu_by_id(role_menu_id, token)


@router.post("/{role_id}/menus")
def create_role_menu(
    role_id: int,
    payload: RoleMenuCreate,
    token: str = Depends(require_menu_access("roles", "Write")),
    role_service: RoleService = Depends(get_role_service),
):
    return role_service.create_role_menu(role_id, payload, token)


@router.put("/role-menus/{role_menu_id}")
def update_role_menu(
    role_menu_id: int,
    payload: RoleMenuUpdate,
    token: str = Depends(require_menu_access("roles", "Write")),
    role_service: RoleService = Depends(get_role_service),
):
    return role_service.update_role_menu(role_menu_id, payload, token)


@router.delete("/role-menus/{role_menu_id}")
def delete_role_menu(
    role_menu_id: int,
    token: str = Depends(require_menu_access("roles", "Write")),
    role_service: RoleService = Depends(get_role_service),
):
    return role_service.delete_role_menu(role_menu_id, token)
