from typing import Optional, Dict, Any
from pydantic import BaseModel


class CareerCreate(BaseModel):
    title: str
    slug: str
    department: str
    location: Optional[str] = None
    employment_type: str
    description: Dict[str, Any]

    experience_min_years: Optional[str] = None

    salary_min: Optional[int] = None
    salary_max: Optional[int] = None
    salary_currency: Optional[str] = None

    status: Optional[str] = "open"
    featured: Optional[bool] = False
    closing_date: Optional[str] = None


class CareerUpdate(BaseModel):
    title: Optional[str] = None
    slug: Optional[str] = None
    department: Optional[str] = None
    location: Optional[str] = None
    employment_type: Optional[str] = None
    description: Optional[Dict[str, Any]] = None

    experience_min_years: Optional[str] = None

    salary_min: Optional[int] = None
    salary_max: Optional[int] = None
    salary_currency: Optional[str] = None

    status: Optional[str] = None
    featured: Optional[bool] = None
    closing_date: Optional[str] = None


class CareerStatusUpdate(BaseModel):
    is_active: bool