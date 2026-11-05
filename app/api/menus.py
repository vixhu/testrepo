from fastapi import APIRouter, Depends

from app.schemas.menus import MenuCreate, MenuUpdate
from app.services.menu_permission_service import require_menu_access
from app.services.menu_service import MenuService, get_menu_service


router = APIRouter(prefix="/menus", tags=["Menus API"])


@router.get("/")
def get_all_menus(
    token: str = Depends(require_menu_access("menus", "Read")),
    menu_service: MenuService = Depends(get_menu_service),
):
    return menu_service.get_all_menus(token)


@router.get("/{menu_id}")
def get_menu_by_id(
    menu_id: int,
    token: str = Depends(require_menu_access("menus", "Read")),
    menu_service: MenuService = Depends(get_menu_service),
):
    return menu_service.get_menu_by_id(menu_id, token)


@router.get("/{menu_id}/items")
def get_menu_items(
    menu_id: int,
    token: str = Depends(require_menu_access("menus", "Read")),
    menu_service: MenuService = Depends(get_menu_service),
):
    return menu_service.get_menu_items(menu_id, token)


@router.get("/items/{item_id}")
def get_menu_item_by_id(
    item_id: int,
    token: str = Depends(require_menu_access("menus", "Read")),
    menu_service: MenuService = Depends(get_menu_service),
):
    return menu_service.get_menu_item_by_id(item_id, token)


@router.post("/")
def create_menu(
    menu_data: MenuCreate,
    token: str = Depends(require_menu_access("menus", "Write")),
    menu_service: MenuService = Depends(get_menu_service),
):
    return menu_service.create_menu(menu_data, token)


@router.put("/{menu_id}")
def update_menu(
    menu_id: int,
    menu_data: MenuUpdate,
    token: str = Depends(require_menu_access("menus", "Write")),
    menu_service: MenuService = Depends(get_menu_service),
):
    return menu_service.update_menu(menu_id, menu_data, token)


@router.delete("/{menu_id}")
def delete_menu(
    menu_id: int,
    token: str = Depends(require_menu_access("menus", "Write")),
    menu_service: MenuService = Depends(get_menu_service),
):
    return menu_service.delete_menu(menu_id, token)
