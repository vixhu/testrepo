from typing import List, Optional
from pydantic import BaseModel

class SeoUpdate(BaseModel):
    meta_title: Optional[str] = None
    meta_description: Optional[str] = None
    canonical_url: Optional[str] = None
    og_title: Optional[str] = None
    og_description: Optional[str] = None
    og_image_id: Optional[int] = None
    target_keywords: Optional[List[str]] = None