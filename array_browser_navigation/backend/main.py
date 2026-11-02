"""
FastAPI application entry point.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import os

from backend.database.connection import engine, Base
from backend.database import models  # noqa: F401 — registers ORM models
from backend.api.navigation_routes import router
from backend.api.proxy_route import router as proxy_router

# Create all database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Array-Based Browser Navigation",
    description=(
        "A browser-like application that demonstrates how an Array/List "
        "data structure can power browser Back/Forward navigation.\n\n"
        "**Navigation decisions are always made by the Array Algorithm Engine.** "
        "MySQL is used only for persistence."
    ),
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Allow the frontend (served on the same origin or a different port) to call the API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register navigation routes under /api
app.include_router(router, prefix="/api", tags=["Navigation"])
app.include_router(proxy_router, prefix="/api", tags=["Proxy"])

# ---------------------------------------------------------------------------
# Serve frontend static files
# ---------------------------------------------------------------------------
_frontend_dir = os.path.join(os.path.dirname(__file__), "..", "frontend")
_frontend_dir = os.path.abspath(_frontend_dir)

if os.path.isdir(_frontend_dir):
    app.mount(
        "/static",
        StaticFiles(directory=_frontend_dir),
        name="static",
    )

    @app.get("/", include_in_schema=False)
    def serve_index():
        return FileResponse(os.path.join(_frontend_dir, "index.html"))

else:
    @app.get("/", include_in_schema=False)
    def root():
        return {
            "message": "Array-Based Browser Navigation API",
            "docs": "/docs",
            "api": "/api",
        }
