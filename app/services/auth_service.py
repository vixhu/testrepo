import datetime

from fastapi import Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.config import settings
from app.schemas.users import UserCreate
from app.services.password_service import PasswordService, get_password_service
from app.services.token_service import TokenService, get_token_service
from app.services.user_service import UserService, get_user_service
from app.services.validation_service import ValidationService, get_validation_service
from app.services.menu_permission_service import MenuPermissionService
from app.services.activity_log_service import ActivityLogService, get_activity_log_service
from app.utils.date_utils import format_datetime_ist, format_datetime_ist_full, get_utc_now


class AuthService:
    def __init__(self, db,
        user_service: UserService,
        password_service: PasswordService,
        token_service: TokenService,
        validation_service: ValidationService,
        activity_log_service: ActivityLogService):
        
        self.db = db
        self.user_service = user_service
        self.password_service = password_service
        self.token_service = token_service
        self.validation_service = validation_service
        self.activity_log_service = activity_log_service

    def register_user(self, user_create: UserCreate):
        
        self.validation_service.check_full_name_validity(user_create.full_name)
        self.validation_service.check_email_validity(user_create.email)
        self.user_service.check_if_email_exists(user_create.email)
        self.validation_service.check_password_validity(user_create.password)

        user_create.password = self.password_service.hash_password(user_create.password)
        new_user = self.user_service.create_user(user_create)


        # role_name = self.user_service.get_user_role(new_user)
        # role_name = 'admin'
        # temp_token = self.token_service.create_temp_token(new_user.id, role_name)

        return {
            "message": "User created successfully",
            "username": new_user.email,
            "full_name": new_user.full_name,
            "email": new_user.email,
        }
    
    def login(self, email: str, password: str, ip_address: str | None = None, user_agent: str | None = None):
        user = self.user_service.find_user_by_email(email)
        if (
            not user
            or not user.password
            or not user.is_active
            or not self.password_service.verify_password(password, user.password)
        ):
            raise HTTPException(status_code=401, detail="Invalid email or password")

        self.db.refresh(user)

        permission_service = MenuPermissionService(self.db)
        role = permission_service.get_user_role(user.id)
        if not role:
            raise HTTPException(status_code=403, detail="Permission denied")

        menus = permission_service.get_user_menu_permissions(user.id)
        role_name = role.role_name

        access_token = self.token_service.create_access_token(user.id, role_name)
        # refresh_token = self.token_service.create_refresh_token(user.id, role)

        user.last_login = get_utc_now()
        user.last_login_ip = ip_address
        self.db.commit()
        self.activity_log_service.record(
            module="Auth",
            action="Login",
            record_id=user.id,
            record_name=user.full_name,
            user=user,
            description="Admin user logged in",
            ip_address=ip_address,
            user_agent=user_agent,
            commit=True,
        )

        result = {
            "access_token": access_token,
            "token_type": "bearer",
            "expires_in": settings.access_token_expire_minutes * 60,
            "user": {
                "id": user.id,
                "user_id": user.id,
                "full_name": user.full_name,
                "email": user.email,
                "profile_image_url": user.profile_image_url,
                "is_active": bool(user.is_active),
            },
            "role": {
                "id": role.id,
                "role_name": role.role_name,
            },
            "menus": menus,
        }
        return result


def get_auth_service(
        db: Session = Depends(get_db),
        user_service: UserService = Depends(get_user_service),
        password_service: PasswordService = Depends(get_password_service),
        token_service: TokenService = Depends(get_token_service),
        validation_service: ValidationService = Depends(get_validation_service),
        activity_log_service: ActivityLogService = Depends(get_activity_log_service))-> AuthService:
    return AuthService(db, user_service,password_service,token_service,validation_service,activity_log_service)
