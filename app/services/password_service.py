import hashlib
import base64
import bcrypt


class PasswordService:
    def _pre_hash(self, plain_password: str) -> str:
        digest = hashlib.sha256(plain_password.encode()).digest()
        return base64.b64encode(digest).decode()

    def hash_password(self, plain_password: str) -> str:
        password_bytes = self._pre_hash(plain_password).encode()
        hashed_password = bcrypt.hashpw(password_bytes, bcrypt.gensalt(rounds=12))
        return hashed_password.decode()

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        password_bytes = self._pre_hash(plain_password).encode()
        hashed_bytes = hashed_password.encode()
        return bcrypt.checkpw(password_bytes, hashed_bytes)


def get_password_service() -> PasswordService:
    return PasswordService()
