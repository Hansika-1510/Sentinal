import asyncio
from typing import Dict, Any
from fastapi import APIRouter, Depends, Header, Request, status, HTTPException
from sqlalchemy.orm import Session
from app.api.deps import get_db
from app.integrations.github import GitHubIntegration
from app.schemas.deployment import DeploymentCreate
from app.schemas.event import EventCreate
from app.services.deployment_service import DeploymentService
from app.agents.sentinel import SentinelAgent
from app.services.autonomous_response_service import run_autonomous_response
from app.core.logging import logger

router = APIRouter(prefix="/webhooks", tags=["Webhooks"])


@router.post("/github", status_code=status.HTTP_200_OK)
async def github_webhook(
    request: Request,
    x_hub_signature_256: str = Header(None),
    x_github_event: str = Header("push"),
    db: Session = Depends(get_db)
):
    """Handles GitHub webhooks for push and deployment events."""
    body_bytes = await request.body()
    github_integration = GitHubIntegration()

    if not github_integration.verify_webhook_signature(body_bytes, x_hub_signature_256):
        raise HTTPException(status_code=403, detail="Invalid GitHub webhook signature")

    payload = await request.json()
    logger.info(f"Received GitHub webhook event: {x_github_event}")

    if x_github_event == "push":
        # Record deployment/commit info if push to main/production
        ref = payload.get("ref", "")
        commits = payload.get("commits", [])
        repo_name = payload.get("repository", {}).get("name", "app-service")
        
        if commits:
            latest_commit = commits[-1]
            dep_service = DeploymentService(db)
            dep_service.record_deployment(DeploymentCreate(
                service=repo_name,
                version=latest_commit.get("id", "sha")[:7],
                commit_hash=latest_commit.get("id", "sha"),
                environment="production",
                status="SUCCESS",
                metadata_json={"author": latest_commit.get("author", {}).get("name"), "message": latest_commit.get("message")}
            ))

    return {"status": "processed", "event": x_github_event}


@router.post("/deployments", status_code=status.HTTP_201_CREATED)
def generic_deployment_webhook(dep_in: DeploymentCreate, db: Session = Depends(get_db)):
    """Generic webhook endpoint for CI/CD deployment notifications."""
    service = DeploymentService(db)
    dep = service.record_deployment(dep_in)
    return {"status": "registered", "deployment_id": dep.id}


@router.post("/runtime-events", status_code=status.HTTP_200_OK)
async def generic_runtime_webhook(event_in: EventCreate, db: Session = Depends(get_db)):
    """Generic webhook endpoint for ingestion from APM/Observability tools."""
    # Same reasoning as events.py: Sentinel is synchronous and does real DB work, so it
    # must not run on the event loop, which would stall every other in-flight request.
    # The session crosses threads but never concurrently -- see the note in events.py.
    response = await asyncio.to_thread(SentinelAgent(db).process_event, event_in)
    if response.incident_created and response.incident_id:
        await run_autonomous_response(response.incident_id, db)
    return response
