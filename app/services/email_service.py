import re

from app.config import settings

EMAIL_LOGO_URL = "https://res.cloudinary.com/yozqxgys/image/upload/b_white,f_png/v1789687770/logo.webp"
EMAIL_SITE_URL = "https://www.indicationinstruments.com"
_BODY_OPEN_RE = re.compile(r"(<body[^>]*>)", re.IGNORECASE)


def format_from_address(from_address: str, from_name: str | None = None) -> str:
    address = (from_address or "").strip()
    name = (from_name if from_name is not None else settings.email_from_name).strip()
    if not address:
        return address
    if "<" in address and ">" in address:
        return address
    if not name:
        return address
    if any(char in name for char in ',;:"'):
        escaped = name.replace("\\", "\\\\").replace('"', '\\"')
        return f'"{escaped}" <{address}>'
    return f"{name} <{address}>"


def html_with_logo(message: str) -> str:
    if not message:
        message = ""
    if EMAIL_LOGO_URL in message:
        return message

    logo = (
        '<table role="presentation" cellpadding="0" cellspacing="0" border="0" width="100%" '
        'style="margin:0 0 24px 0;">'
        "<tr><td>"
        f'<a href="{EMAIL_SITE_URL}" target="_blank" rel="noopener">'
        f'<img src="{EMAIL_LOGO_URL}" alt="Indication Instruments" width="160" height="75" '
        'style="display:block;border:0;outline:none;text-decoration:none;width:160px;max-width:160px;height:auto;background-color:#ffffff;" />'
        "</a>"
        "</td></tr></table>"
    )

    body_open = _BODY_OPEN_RE.search(message)
    if body_open:
        insert_at = body_open.end()
        return message[:insert_at] + logo + message[insert_at:]

    return (
        '<html><body style="font-family:Arial,Helvetica,sans-serif;font-size:15px;color:#333;line-height:1.6;">'
        f"{logo}{message}</body></html>"
    )
