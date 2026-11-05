from typing import Optional
from fastapi import Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.admin_menus import AdminMenu
from app.models.role_menus import RoleMenu
from app.models.roles import Role
from app.models.user_roles import UserRole
from app.models.users import User
from app.schemas.users import UserCreate
from app.services.activity_log_service import ActivityLogService, get_activity_log_service
from app.services.menu_permission_service import MenuPermissionService
from app.services.token_service import TokenService, get_token_service
from app.utils.pagination import paginate_query

class UserService:
    def __init__(self,db,
                 token_service: TokenService,
                 activity_log_service: ActivityLogService):
        self.db = db
        self.token_service = token_service
        self.activity_log_service = activity_log_service

        
    def find_user_by_email(self, email: str):
        return self.db.query(User).filter(User.email == email).first()

    def get_user_by_email(self, email: str):
        user = self.find_user_by_email(email)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        return user
       
    def get_user_by_id(self, id: int):
        user = self.db.query(User).filter(User.id == id).first()
        return user
    
    def check_if_email_exists(self, email: str):
        email = self.db.query(User).filter(User.email == email).first()
        if email:
            raise HTTPException(status_code=400, detail="Email already exists")
        
    def create_user(self, user_create: UserCreate):
        new_user = User(
            full_name=user_create.full_name,
            email=user_create.email,
            password=user_create.password,
        )
        
        self.db.add(new_user)
        self.db.commit()
        self.db.refresh(new_user)

        role = self.db.query(Role).filter(Role.role_name == user_create.role).first()
        if role:
            self.db.add(UserRole(user_id=new_user.id, role_id=role.id, created_by=new_user.id))
            self.db.commit()

        self.activity_log_service.record(
            module="Users",
            action="Registered",
            record_id=new_user.id,
            record_name=new_user.full_name,
            user=new_user,
            description="User registered",
            metadata={"email": new_user.email, "role": user_create.role},
            commit=True,
        )

        return new_user


    def get_user_from_token(self, token) -> Optional[User]:
        # Verify the access token (not the temporary token) to get the user id
        user_id = self.token_service.verify_access_token(token)
        try:
            user_id = int(user_id)
        except Exception:
            pass
        user = self.get_user_by_id(user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        return user

    def get_user_role(self, user_id):
        role = (
            self.db.query(Role)
            .join(UserRole, UserRole.role_id == Role.id)
            .filter(UserRole.user_id == user_id)
            .filter(Role.is_enabled == 1)
            .first()
        )
        return role.role_name if role else None

    def _require_admin(self, token: str):
        user = self.get_user_from_token(token)
        role_name = self.get_user_role(user.id)
        if role_name != "admin":
            raise HTTPException(status_code=403, detail="Permission denied")
        return user

    def _require_permission(self, token: str, menu_slug: str, required_access: str = "Read"):
        user = self.get_user_from_token(token)
        role_name = self.get_user_role(user.id)
        if role_name == "admin":
            return user
                
        MenuPermissionService(self.db).check_menu_access(user.id, menu_slug, required_access)
        return user

    def _get_role_by_name(self, role_name: str):
        role = self.db.query(Role).filter(Role.role_name == role_name, Role.is_enabled == 1).first()
        if not role:
            raise HTTPException(status_code=404, detail="Role not found")
        return role

    def _set_user_role(self, user_id: int, role_name: str, admin_user_id: int):
        role = self._get_role_by_name(role_name)
        user_role = self.db.query(UserRole).filter(UserRole.user_id == user_id).first()

        if user_role:
            user_role.role_id = role.id
            user_role.updated_by = admin_user_id
        else:
            user_role = UserRole(user_id=user_id, role_id=role.id, created_by=admin_user_id)
            self.db.add(user_role)

        return role

    def _serialize_user(self, user: User):
        role = (
            self.db.query(Role)
            .join(UserRole, UserRole.role_id == Role.id)
            .filter(UserRole.user_id == user.id)
            .first()
        )

        return {
            "id": user.id,
            "full_name": user.full_name,
            "email": user.email,
            "profile_image_url": user.profile_image_url,
            "is_active": bool(user.is_active),
            "last_login": user.last_login,
            "last_login_ip": user.last_login_ip,
            "created_at": user.created_at,
            "updated_at": user.updated_at,
            "role": {
                "id": role.id,
                "role_name": role.role_name,
            } if role else None,
        }

    def get_all_users(self, token: str, page: int | None = None, limit: int | None = None):
        self.get_user_from_token(token)
        query = self.db.query(User).order_by(User.full_name.asc())
        users, meta = paginate_query(query, page, limit)
        data = [self._serialize_user(user) for user in users]
        if meta is None:
            return data
        return {"data": data, **meta}

    def get_admin_user_by_id(self, user_id: int, token: str):
        self.get_user_from_token(token)
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        return self._serialize_user(user)

    def create_admin_user(self, user_data, hashed_password: str, token: str):
        admin = self.get_user_from_token(token)
        self.check_if_email_exists(user_data.email)

        user = User(
            full_name=user_data.full_name,
            email=user_data.email,
            password=hashed_password,
            is_active=user_data.is_active,
            created_by=admin.id,
        )

        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)

        self._set_user_role(user.id, user_data.role, admin.id)
        self.db.commit()
        self.activity_log_service.record(module="Users", action="Added", record_id=user.id, record_name=user.full_name, user=admin, description="Admin user created", metadata={"email": user.email, "role": user_data.role}, commit=True)

        return {
            "message": "User created successfully",
            "user": self._serialize_user(user),
        }

    def update_admin_user(self, user_id: int, user_data, token: str, hashed_password: Optional[str] = None):
        admin = self.get_user_from_token(token)
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        previous_values = self.activity_log_service.snapshot(user)
        previous_role = self.get_user_role(user.id)
        if user_data.email is not None and user_data.email != user.email:
            self.check_if_email_exists(user_data.email)
            user.email = user_data.email

        if user_data.full_name is not None:
            user.full_name = user_data.full_name

        if hashed_password is not None:
            user.password = hashed_password

        if user_data.is_active is not None:
            user.is_active = user_data.is_active

        if user_data.role is not None:
            self._set_user_role(user.id, user_data.role, admin.id)

        user.updated_by = admin.id
        self.db.commit()
        self.db.refresh(user)
        changed_values = self.activity_log_service.changes(previous_values, user)
        current_role = self.get_user_role(user.id)
        if previous_role != current_role:
            previous_values["role"] = previous_role
            changed_values["role"] = {"from": previous_role, "to": current_role}
        self.activity_log_service.record(module="Users", action="Updated", record_id=user.id, record_name=user.full_name, user=admin, description="Admin user updated", metadata={"email": user.email}, previous_values=previous_values, changed_values=changed_values, commit=True)

        return {
            "message": "User updated successfully",
            "user": self._serialize_user(user),
        }

    def upload_user_image(self, user_id: int, upload_file, token: str):
        from app.utils.files import IMAGE_TYPES, cloudinary_folder, upload_to_cloudinary

        admin = self.get_user_from_token(token)
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        result = upload_to_cloudinary(
            upload_file,
            cloudinary_folder("users", str(user.id), "profile"),
            allowed_types=IMAGE_TYPES,
        )
        if not result.get("url"):
            raise HTTPException(status_code=500, detail="Cloudinary did not return an image URL")
        user.profile_image_url = result["url"]
        user.updated_by = admin.id
        self.db.commit()
        self.db.refresh(user)
        return {
            "message": "User image updated successfully",
            "user": self._serialize_user(user),
        }

    def set_user_status(self, user_id: int, status_data, token: str):
        admin = self.get_user_from_token(token)
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        previous_values = self.activity_log_service.snapshot(user, ["is_active"])
        user.is_active = bool(status_data.is_active)
        user.updated_by = admin.id
        self.db.commit()
        self.activity_log_service.record(module="Users", action="Activated" if user.is_active else "Deactivated", record_id=user.id, record_name=user.full_name, user=admin, description="User status changed", metadata={"is_active": user.is_active}, previous_values=previous_values, changed_values=self.activity_log_service.changes(previous_values, user), commit=True)

        return {
            "message": f"User {'activated' if user.is_active else 'deactivated'} successfully"
        }

    def delete_admin_user(self, user_id: int, token: str):
        admin = self.get_user_from_token(token)
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        previous_values = self.activity_log_service.snapshot(user, ["is_active"])
        user.is_active = False
        user.updated_by = admin.id
        self.db.commit()
        self.activity_log_service.record(module="Users", action="Deleted", record_id=user.id, record_name=user.full_name, user=admin, description="Admin user deactivated", previous_values=previous_values, changed_values=self.activity_log_service.changes(previous_values, user), commit=True)

        return {"message": "User deleted successfully"}

    def get_user_menu_access(self, user_id: int, token: str):
        self._require_admin(token)
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        user_role = self.db.query(UserRole).filter(UserRole.user_id == user_id).first()
        if not user_role:
            raise HTTPException(status_code=404, detail="User role not found")

        role_menus = (
            self.db.query(RoleMenu)
            .filter(RoleMenu.role_id == user_role.role_id)
            .all()
        )
        access_by_menu_id = {role_menu.admin_menu_id: role_menu.access_level for role_menu in role_menus}

        menus = self.db.query(AdminMenu).order_by(AdminMenu.id).all()
        return [
            {
                "id": menu.id,
                "name": menu.name,
                "slug": menu.slug,
                "icon": menu.icon,
                "access_level": access_by_menu_id.get(menu.id, "None"),
            }
            for menu in menus
        ]


def get_user_service(
        db: Session = Depends(get_db),
        token_service: TokenService = Depends(get_token_service),
        activity_log_service: ActivityLogService = Depends(get_activity_log_service)) -> UserService:
    return UserService(db, token_service, activity_log_service)
