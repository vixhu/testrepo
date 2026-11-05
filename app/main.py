from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi

from starlette.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException
import logging
from app.api import auth, blog_categories, blog_content_section, careers, catalogues, certificates, dashboard, department_contacts, forms, form_submissions, menus, pages, products, product_categories, product_content_sections, profile, roles, seo, blog_posts, users, industry_tags, annual_returns, newsletter_subscribers
from app.services.scheduled_blog_publisher import scheduled_blog_publisher_task
from app.services.scheduled_career_closer import scheduled_career_closer_task
import asyncio
import cloudinary
from app.config import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    cloudinary.config(
        cloud_name=settings.cloudinary_cloud_name,
        api_key=settings.cloudinary_api_key,
        api_secret=settings.cloudinary_api_secret,
        secure=True
    )
    publisher_task = asyncio.create_task(scheduled_blog_publisher_task())
    career_closer_task = asyncio.create_task(scheduled_career_closer_task())
    yield
    publisher_task.cancel()
    career_closer_task.cancel()


app = FastAPI(
    title="Indication Admin APIs",
    description="Backend Service API for Indication Instruments Admin Application",
    version="1.0.0",
    docs_url="/" if settings.docs_enabled else None,
    redoc_url=None,
    openapi_url="/openapi.json" if settings.docs_enabled else None,
    lifespan=lifespan,
    redirect_slashes=False,
)

origins = [
    "http://localhost:5173",
    "http://localhost:3000",
    "http://localhost:8000",
]

if settings.cors_origins:
    for o in settings.cors_origins.split(","):
        cleaned = o.strip()
        if cleaned and cleaned not in origins:
            origins.append(cleaned)

origin_regex = (
    r"^https?://(localhost|127\.0\.0\.1)(:\d+)?$|"
    r"^https://([a-zA-Z0-9-]+\.)*indicationinstruments\.com$"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_origin_regex=origin_regex,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def _cors_headers_for_request(request):
    origin = request.headers.get("origin")
    if not origin:
        return {}
    if (
        origin in origins
        or origin.endswith(".indicationinstruments.com")
        or origin == "https://indicationinstruments.com"
    ):
        return {
            "Access-Control-Allow-Origin": origin,
            "Access-Control-Allow-Credentials": "true",
        }
    return {}


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request, exc):
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
        headers=_cors_headers_for_request(request),
    )

@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    logging.exception("Unhandled server error")
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"},
        headers=_cors_headers_for_request(request),
    )

def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema

    openapi_schema = get_openapi(
        title="Indication Admin APIs",
        version="1.0.0",
        description="Backend Service API for Indication Instruments Admin Application",
        routes=app.routes,
    )

    openapi_schema["components"]["securitySchemes"] = {
        "BearerAuth": {
            "type": "http",
            "scheme": "bearer",
        }
    }

    public_paths = {"/", "/health", "/auth/login"}
    for path, operations in openapi_schema["paths"].items():
        for method, operation in operations.items():
            if not isinstance(operation, dict):
                continue
            if path in public_paths:
                operation["security"] = []
            else:
                operation["security"] = [{"BearerAuth": []}]

    app.openapi_schema = openapi_schema
    return app.openapi_schema


app.openapi = custom_openapi


@app.get("/health")
def health():
    return {"status": "ok"}


if not settings.docs_enabled:
    @app.get("/")
    def root():
        return {"status": "ok"}


app.include_router(dashboard.router)
app.include_router(auth.router)
app.include_router(profile.router)
app.include_router(blog_categories.router)
app.include_router(blog_content_section.router)
app.include_router(menus.router)
app.include_router(roles.router)
app.include_router(product_categories.router)
app.include_router(industry_tags.router)
app.include_router(products.router)
app.include_router(product_content_sections.router)
app.include_router(seo.router)
app.include_router(pages.router)
app.include_router(blog_posts.router)
app.include_router(forms.router)
app.include_router(form_submissions.router)
app.include_router(careers.router)
app.include_router(certificates.router)
app.include_router(catalogues.router)
app.include_router(users.router)
app.include_router(annual_returns.router)
app.include_router(newsletter_subscribers.router)
app.include_router(department_contacts.router)

