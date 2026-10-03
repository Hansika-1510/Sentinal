import time
import uuid
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.core.logging import logger
from app.core.exceptions import (
    IncidentResponseException,
    domain_exception_handler,
    global_exception_handler
)
from app.db.session import init_db
from app.api.routes import api_router
from app.api.routes.health import router as health_root_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: initialize database tables
    logger.info("Initializing database tables and schema...")
    init_db()
    logger.info(f"{settings.APP_NAME} started successfully in '{settings.APP_ENV}' mode.")
    yield
    logger.info(f"{settings.APP_NAME} shutting down.")


app = FastAPI(
    title=settings.APP_NAME,
    description="Backend engine for the AI Software Incident Response Agent platform.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Request ID & Latency Middleware
@app.middleware("http")
async def request_context_middleware(request: Request, call_next):
    request_id = request.headers.get("X-Request-ID") or f"req-{uuid.uuid4().hex[:12]}"
    request.state.request_id = request_id

    start_time = time.time()
    response: Response = await call_next(request)
    duration_ms = round((time.time() - start_time) * 1000, 2)

    response.headers["X-Request-ID"] = request_id
    response.headers["X-Response-Time-Ms"] = str(duration_ms)

    logger.info(
        f"{request.method} {request.url.path} -> {response.status_code} ({duration_ms}ms)",
        extra={"extra_data": {"request_id": request_id, "path": request.url.path, "status_code": response.status_code}}
    )
    return response


# Register Exception Handlers
app.add_exception_handler(IncidentResponseException, domain_exception_handler)
app.add_exception_handler(Exception, global_exception_handler)

# Register Routers
app.include_router(health_root_router)  # /health, /ready directly at root
app.include_router(api_router, prefix=settings.API_V1_STR)


@app.get("/", tags=["Root"])
def root():
    return {
        "app": settings.APP_NAME,
        "version": "1.0.0",
        "docs": "/docs",
        "status": "online"
    }
