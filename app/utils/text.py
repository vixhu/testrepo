import re

NBSP_RE = re.compile(r"(?:&nbsp;|&#160;|&#x0*a0;|\u00a0|\u202f)+", re.IGNORECASE)
EMPTY_P_RE = re.compile(r"<p>(?:\s|&nbsp;|<br\s*/?>)*</p>", re.IGNORECASE)
RESOLUTIONS = (
    (1920, 720),
    (1024, 600),
    (800, 480),
    (480, 272),
    (320, 240),
    (240, 320),
    (240, 240),
    (128, 128),
)


def clean_product_text(value):
    if value is None or not isinstance(value, str):
        return value

    text = value.replace("\u2013", "-").replace("\u2014", "-").replace("\u2212", "-")
    text = NBSP_RE.sub(" ", text)
    text = re.sub(r"[ \t]{2,}", " ", text)

    for width, height in RESOLUTIONS:
        text = re.sub(rf"\b{width}[ ]{{0,2}}{height}\b", f"{width} × {height}", text)
        text = re.sub(rf"\b{width}[xX]{height}\b", f"{width} × {height}", text)

    text = re.sub(r"\b832\s*V\b", "8-32 V", text)
    text = re.sub(r"cd/m2\b", "cd/m²", text)
    text = re.sub(r"cd/m(?![²2])", "cd/m²", text)
    text = re.sub(r"\b(\d{1,2})C\s+to\s+\+(\d{1,2})C\b", r"-\1°C to +\2°C", text)
    return text.strip()


def clean_html_content(value):
    text = clean_product_text(value)
    if not isinstance(text, str):
        return text
    text = EMPTY_P_RE.sub("", text)
    text = re.sub(r"<p>\s+", "<p>", text)
    text = re.sub(r"\s+</p>", "</p>", text)
    return text.strip()


def _clean_text_field(value):
    if not isinstance(value, str):
        return value
    if "<" in value:
        return clean_html_content(value)
    return clean_product_text(value)


def clean_section_content(content):
    if isinstance(content, str):
        return _clean_text_field(content)
    if isinstance(content, dict):
        cleaned = dict(content)
        for key in ("html", "text", "answer", "author", "alt", "caption"):
            if key in cleaned:
                cleaned[key] = _clean_text_field(cleaned.get(key))
        if "items" in cleaned and isinstance(cleaned["items"], list):
            items = []
            for item in cleaned["items"]:
                if isinstance(item, str):
                    items.append(_clean_text_field(item))
                elif isinstance(item, dict):
                    faq = dict(item)
                    for faq_key in ("q", "a", "question", "answer"):
                        if faq_key in faq:
                            faq[faq_key] = _clean_text_field(faq.get(faq_key))
                    items.append(faq)
                else:
                    items.append(item)
            cleaned["items"] = items
        if "headers" in cleaned and isinstance(cleaned["headers"], list):
            cleaned["headers"] = [_clean_text_field(header) for header in cleaned["headers"]]
        if "rows" in cleaned and isinstance(cleaned["rows"], list):
            cleaned["rows"] = [
                [_clean_text_field(cell) for cell in row] if isinstance(row, list) else row
                for row in cleaned["rows"]
            ]
        return cleaned
    return content
