import re
from email_validator import validate_email, EmailNotValidError
from fastapi import Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.password_policy_settings import PasswordPolicySetting
from app.services.user_service import UserService, get_user_service

FULL_NAME_LIMIT= 50

class ValidationService:
    DEFAULT_PASSWORD_POLICY = {
        "min_length": 8,
        "max_length": 128,
        "require_uppercase": True,
        "require_lowercase": True,
        "require_number": True,
        "require_special_char": True,
    }

    def __init__(self, db, 
                 user_service : UserService):
        self.db = db
        self.user_service = user_service
    

    @staticmethod
    def check_email_validity(email: str):
        try:
            valid = validate_email(email, check_deliverability=True)
            return valid.email  
            
        except EmailNotValidError as e:
            raise HTTPException(status_code=422, detail=str(e))    
        
    def _get_password_policy(self) -> PasswordPolicySetting:
        policy = self.db.query(PasswordPolicySetting).order_by(PasswordPolicySetting.id.asc()).first()
        return policy or PasswordPolicySetting()

    def check_password_policy(self, password: str) -> dict:
        errors = []
        policy = self._get_password_policy()
        min_length = policy.min_length or self.DEFAULT_PASSWORD_POLICY["min_length"]
        max_length = policy.max_length or self.DEFAULT_PASSWORD_POLICY["max_length"]
        require_uppercase = self.DEFAULT_PASSWORD_POLICY["require_uppercase"] if policy.require_uppercase is None else policy.require_uppercase
        require_lowercase = self.DEFAULT_PASSWORD_POLICY["require_lowercase"] if policy.require_lowercase is None else policy.require_lowercase
        require_number = self.DEFAULT_PASSWORD_POLICY["require_number"] if policy.require_number is None else policy.require_number
        require_special_char = self.DEFAULT_PASSWORD_POLICY["require_special_char"] if policy.require_special_char is None else policy.require_special_char

        #check for spaces
        if ' ' in password:
            return {'is_valid': False, 'errors': 'Password must not contain spaces.'}
        # Check length
        if len(password) < min_length:
            errors.append(f"Password must be at least {min_length} characters long.")
        if len(password) > max_length:
            errors.append(f"Password must be no more than {max_length} characters long.")

        # Check for uppercase
        if require_uppercase and not re.search(r'[A-Z]', password):
            errors.append("Password must contain at least one uppercase letter.")

        # Check for lowercase
        if require_lowercase and not re.search(r'[a-z]', password):
            errors.append("Password must contain at least one lowercase letter.")

        # Check for numbers
        if require_number and not re.search(r'[0-9]', password):
            errors.append("Password must contain at least one number.")

        # Check for special characters
        if require_special_char and not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            errors.append("Password must contain at least one special character from these 's!@#$%^&*(),.?”:{}|<>[]1E'")

        return {
            "is_valid": len(errors) == 0,
            "errors": errors
        }

    def check_password_validity(self, password: str) -> bool:
        result = self.check_password_policy(password)
        if not result["is_valid"]:
            raise HTTPException(status_code=422, detail=result["errors"])
        return True

    def check_full_name_validity(self, full_name: str) -> bool:
        if not self.check_full_name_validity(full_name):
            raise HTTPException(status_code=422, detail="Full name is invalid.")
        return True
    
    @staticmethod
    def check_full_name_validity(full_name: str):
        if not full_name or len(full_name) > FULL_NAME_LIMIT:
            return False
        
        pattern = r'^[A-Za-z][A-Za-z]*$'
        return bool(re.match(pattern, full_name))
        
        
def get_validation_service(
        db: Session = Depends(get_db),
        user_service = Depends(get_user_service)) -> ValidationService:
    return ValidationService(db, user_service)