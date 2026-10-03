from fastapi import APIRouter
from app.api.routes.health import router as health_router
from app.api.routes.services import router as services_router
from app.api.routes.events import router as events_router
from app.api.routes.deployments import router as deployments_router
from app.api.routes.code_reviews import router as code_reviews_router
from app.api.routes.incidents import router as incidents_router
from app.api.routes.actions import router as actions_router
from app.api.routes.audit import router as audit_router
from app.api.routes.webhooks import router as webhooks_router

api_router = APIRouter()

api_router.include_router(health_router)
api_router.include_router(services_router)
api_router.include_router(events_router)
api_router.include_router(deployments_router)
api_router.include_router(code_reviews_router)
api_router.include_router(incidents_router)
api_router.include_router(actions_router)
api_router.include_router(audit_router)
api_router.include_router(webhooks_router)
