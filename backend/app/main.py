from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.core.logging import logger
from app.api.v1.router import api_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    FastAPI Lifespan event context manager.
    Handles startup logging & initialization and shutdown cleanup.
    """
    # Startup logic
    logger.info(f"Starting {settings.PROJECT_NAME} (v{settings.VERSION}) in [{settings.ENVIRONMENT}] mode")
    logger.info(f"Configured CORS origins: {settings.CORS_ORIGINS}")
    
    yield
    
    # Shutdown logic
    logger.info(f"Shutting down {settings.PROJECT_NAME} application")


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    openapi_url=f"{settings.API_V1_STR}/openapi.json" if settings.ENVIRONMENT != "production" else None,
    lifespan=lifespan,
)

# Configure CORS Middleware
if settings.CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[str(origin) for origin in settings.CORS_ORIGINS],
        # Next.js may move to another local port when 3000 is occupied.
        # Keep this development-only convenience separate from production origins.
        allow_origin_regex=(r"^https?://(localhost|127\.0\.0\.1)(:\d+)?$" if settings.ENVIRONMENT == "development"
                            else settings.CORS_ORIGIN_REGEX or None),
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

# The exercise library is the same for every user and changes only when media is imported, so browsers may reuse
# it for a minute and Vercel's edge for five; a filter clicked again then answers at once.
PUBLIC_CATALOG = tuple(f"{settings.API_V1_STR}/{p}" for p in ("exercises", "muscle-groups", "equipment"))


@app.middleware("http")
async def cache_public_catalog(request: Request, call_next):
    response = await call_next(request)
    if request.method == "GET" and response.status_code == 200 and request.url.path.startswith(PUBLIC_CATALOG):
        response.headers.setdefault("Cache-Control", "public, max-age=60, s-maxage=300, stale-while-revalidate=86400")
    return response


# Mount API v1 Routes
app.include_router(api_router, prefix=settings.API_V1_STR)


@app.get("/health", tags=["Health"])
def root_health_check():
    """
    Root level simple health check endpoint.
    """
    return {"status": "healthy"}


@app.get("/", tags=["Root"])
def root():
    """
    Root endpoint.
    """
    return {
        "message": f"Welcome to {settings.PROJECT_NAME}",
        "version": settings.VERSION,
        "docs": "/docs" if settings.ENVIRONMENT != "production" else "Disabled",
        "health": f"{settings.API_V1_STR}/health",
    }
