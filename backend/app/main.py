from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.api.v1.endpoints.process import router as process_router, health_check
from app.api.v1.endpoints.convert import router as convert_router

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    version="1.0.0",
)

# Set up CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API Routers
app.include_router(process_router, prefix=settings.API_V1_STR, tags=["Processing"])
app.include_router(convert_router, prefix=settings.API_V1_STR, tags=["Conversion"])

# Expose top-level /health endpoint
app.add_api_route("/health", health_check, methods=["GET"], tags=["Health"])


@app.get("/")
async def root():
    return {
        "message": "AI Content Engine API V1 is running",
        "docs": "/docs",
        "health": "/health",
    }
