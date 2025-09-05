import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .routers import auth, images, edits, subscriptions, admin, websocket_info, websocket
from .settings import settings
from .utils.errors import register_exception_handlers
from .utils.lifespan import lifespan

# Initialize logging
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO),
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
logger = logging.getLogger("backendservice")


# Create app with lifespan context
app = FastAPI(
    title="Real Estate Image Enhancer - BackendService",
    version="1.0.0",
    description=(
        "Backend service providing authentication, image upload, edit requests, "
        "background processing via Google Nano Banana API, Stripe subscriptions, "
        "and admin/usage APIs. All routes include strong validation and audit logging."
    ),
    lifespan=lifespan,
    openapi_tags=[
        {"name": "Health", "description": "Service health and operational info."},
        {"name": "Auth", "description": "User registration, login, session & profile."},
        {"name": "Images", "description": "Secure image upload, retrieval and metadata."},
        {"name": "Edits", "description": "Edit requests and before/after delivery."},
        {"name": "Subscriptions", "description": "Stripe-based payments and plans."},
        {"name": "Admin", "description": "Administrative analytics and monitoring."},
        {"name": "WebSockets", "description": "Real-time notifications for edit status updates, subscription changes, and usage alerts via WebSocket connections."},
    ],
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[origin.strip() for origin in settings.CORS_ALLOW_ORIGINS.split(",") if origin.strip()] or ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register exception handlers
register_exception_handlers(app)


@app.get("/", tags=["Health"], summary="Health check", description="Service availability probe.")
def health_check():
    # PUBLIC_INTERFACE
    """Health check endpoint.

    Returns:
        dict: Message and environment label indicating service availability.
    """
    return {"message": "Healthy", "env": settings.ENVIRONMENT}


# Include routers (modular REST structure)
app.include_router(auth.router, prefix="/auth", tags=["Auth"])
app.include_router(images.router, prefix="/images", tags=["Images"])
app.include_router(edits.router, prefix="/edits", tags=["Edits"])
app.include_router(subscriptions.router, prefix="/subscriptions", tags=["Subscriptions"])
app.include_router(admin.router, prefix="/admin", tags=["Admin"])
app.include_router(websocket_info.router, prefix="/docs", tags=["WebSockets"])
app.include_router(websocket.router, tags=["WebSockets"])
