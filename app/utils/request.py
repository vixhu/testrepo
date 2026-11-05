import ipaddress

from fastapi import Request

from app.config import settings


def is_valid_ip(value: str | None) -> bool:
    if not value:
        return False
    try:
        ipaddress.ip_address(value)
        return True
    except ValueError:
        return False


def get_client_ip(request: Request) -> str | None:
    if settings.trust_proxy:
        forwarded = request.headers.get("x-forwarded-for")
        if forwarded:
            candidate = forwarded.split(",")[0].strip()
            if is_valid_ip(candidate):
                return candidate
        real_ip = request.headers.get("x-real-ip")
        if is_valid_ip(real_ip):
            return real_ip

    host = request.client.host if request.client else None
    if is_valid_ip(host):
        return host
    return None


def get_user_agent(request: Request) -> str | None:
    return request.headers.get("user-agent")
