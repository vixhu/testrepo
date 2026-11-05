from fastapi import Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.users import User
from app.schemas.users import ProfileUpdate
from app.services.password_service import PasswordService, get_password_service
from app.services.user_service import UserService, get_user_service


class ProfileService:
    def __init__(self, db, user_service: UserService, password_service: PasswordService):
        self.db = db
        self.user_service = user_service
        self.password_service = password_service

    def _serialize(self, user: User):
        role_name = self.user_service.get_user_role(user.id)
        if not role_name:
            raise HTTPException(status_code=403, detail="Permission denied")
        return {
            "user_id": user.id,
            "full_name": user.full_name,
            "email": user.email,
            "profile_image_url": user.profile_image_url,
            "role": role_name,
        }

    def get_profile(self, token):
        user = self.user_service.get_user_from_token(token)
        user_details = self.db.query(User).filter(User.id == user.id).first()
        if not user_details:
            raise HTTPException(status_code=404, detail="User not found")
        return self._serialize(user_details)

    def update_profile(self, token, profile_data: ProfileUpdate):
        user = self.user_service.get_user_from_token(token)
        user_details = self.db.query(User).filter(User.id == user.id).first()
        if not user_details:
            raise HTTPException(status_code=404, detail="User not found")

        if profile_data.full_name is not None:
            name = profile_data.full_name.strip()
            if not name:
                raise HTTPException(status_code=400, detail="Full name cannot be empty")
            user_details.full_name = name

        if profile_data.email is not None:
            email = profile_data.email.strip().lower()
            if not email:
                raise HTTPException(status_code=400, detail="Email cannot be empty")
            existing = self.db.query(User).filter(User.email == email, User.id != user_details.id).first()
            if existing:
                raise HTTPException(status_code=400, detail="Email already exists")
            user_details.email = email

        if profile_data.new_password:
            if not profile_data.current_password:
                raise HTTPException(status_code=400, detail="Current password is required to set a new password")
            if not self.password_service.verify_password(profile_data.current_password, user_details.password):
                raise HTTPException(status_code=400, detail="Current password is incorrect")
            if profile_data.new_password == profile_data.current_password:
                raise HTTPException(status_code=400, detail="New password must be different from the current password")
            user_details.password = self.password_service.hash_password(profile_data.new_password)
        elif profile_data.current_password:
            raise HTTPException(status_code=400, detail="New password is required when current password is provided")

        user_details.updated_by = user_details.id
        self.db.commit()
        self.db.refresh(user_details)

        payload = self._serialize(user_details)
        payload["message"] = "Profile updated successfully"
        return payload

    def upload_image(self, token, upload_file):
        from app.utils.files import IMAGE_TYPES, alt_text_for_upload, cloudinary_folder, upload_to_cloudinary

        user = self.user_service.get_user_from_token(token)
        original_name = upload_file.filename or "profile"
        result = upload_to_cloudinary(
            upload_file,
            cloudinary_folder("users", str(user.id), "profile"),
            allowed_types=IMAGE_TYPES,
        )
        if not result.get("url"):
            raise HTTPException(status_code=500, detail="Cloudinary did not return an image URL")
        user.profile_image_url = result["url"]
        user.updated_by = user.id
        self.db.commit()
        self.db.refresh(user)
        payload = self._serialize(user)
        payload["alt_text"] = alt_text_for_upload(original_name, user.full_name)
        payload["message"] = "Profile image updated successfully"
        return payload

    def delete_image(self, token):
        user = self.user_service.get_user_from_token(token)
        user.profile_image_url = None
        user.updated_by = user.id
        self.db.commit()
        self.db.refresh(user)
        payload = self._serialize(user)
        payload["message"] = "Profile image removed successfully"
        return payload


def get_profile_service(
        db: Session = Depends(get_db),
        user_service: UserService = Depends(get_user_service),
        password_service: PasswordService = Depends(get_password_service)) -> ProfileService:
    return ProfileService(db, user_service, password_service)
