import asyncio
import sys
import os

# Add project root to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

from datetime import datetime, timezone, timedelta
from sqlalchemy import select
from app.db.session import SessionLocal, init_db
from app.models.service import Service
from app.models.deployment import Deployment
from app.models.code_review import CodeReview
from app.models.incident import Incident
from app.services.incident_memory_service import IncidentMemoryService
from app.core.logging import logger


async def seed_data():
    init_db()
    db = SessionLocal()
    memory_service = IncidentMemoryService(db)

    print("\n" + "=" * 60)
    print("[*] SEEDING AI INCIDENT RESPONSE AGENT DEMO DATA")
    print("=" * 60)

    # 1. Services Catalog & Dependency Topology
    services_data = [
        {
            "name": "payment-service",
            "environment": "production",
            "description": "Core payment processing and subscription billing microservice.",
            "dependencies": ["postgres-db", "stripe-api"],
            "metadata_json": {
                "features": ["Checkout Payment API", "Subscription Renewal", "Refund Processing"],
                "user_journeys": ["User checkout flow", "Merchant billing"]
            }
        },
        {
            "name": "order-service",
            "environment": "production",
            "description": "E-commerce order placement, inventory reservation, and checkout flow orchestration.",
            "dependencies": ["payment-service", "auth-service"],
            "metadata_json": {
                "features": ["Order Placement", "Order Status Query"],
                "user_journeys": ["User checkout flow", "Order History"]
            }
        },
        {
            "name": "auth-service",
            "environment": "production",
            "description": "Identity, JWT token issuance, and authentication service.",
            "dependencies": ["redis-sessions", "auth-db"],
            "metadata_json": {
                "features": ["User Login", "Token Refresh"],
                "user_journeys": ["User Authentication"]
            }
        },
        {
            "name": "api-gateway",
            "environment": "production",
            "description": "Ingress reverse proxy and rate limiting gateway.",
            "dependencies": ["auth-service", "order-service", "payment-service"],
            "metadata_json": {
                "features": ["Ingress Routing", "Rate Limiting"],
                "user_journeys": ["All Ingress Traffic"]
            }
        }
    ]

    for s_info in services_data:
        existing = db.scalars(select(Service).where(Service.name == s_info["name"])).first()
        if not existing:
            s = Service(**s_info)
            db.add(s)
            print(f"  + Service created: {s_info['name']}")
    db.commit()

    # 2. Baseline Healthy Deployments (v1.8.2)
    past_time = datetime.now(timezone.utc) - timedelta(days=2)
    existing_dep = db.scalars(select(Deployment).where(Deployment.version == "v1.8.2")).first()
    if not existing_dep:
        dep = Deployment(
            service="payment-service",
            version="v1.8.2",
            commit_hash="f0e1d2c3b4a5",
            environment="production",
            status="SUCCESS",
            deployed_at=past_time,
            metadata_json={"author": "lead-dev@company.com", "notes": "Stable baseline release"}
        )
        db.add(dep)
        print("  + Baseline deployment created: payment-service v1.8.2")
    db.commit()

    # 3. Seed Historical Incident Memory (for semantic similarity retrieval)
    hist_inc_id = "INC-HIST-01"
    existing_mem = db.scalars(select(Incident).where(Incident.id == hist_inc_id)).first()
    if not existing_mem:
        # Create historical incident record
        payment_service = db.scalars(select(Service).where(Service.name == "payment-service")).first()
        hist_inc = Incident(
            id=hist_inc_id,
            title="PAYMENT SERVICE: Database Connection Pool Exhaustion Under Peak Load",
            severity="CRITICAL",
            status="RESOLVED",
            service_id=payment_service.id if payment_service else "payment-service",
            environment="production",
            summary="Payment service crashed due to HikariCP pool starvation when max connection limit was misconfigured.",
            root_cause="Database pool max limit set to 5 causing threads to wait indefinitely for database connections.",
            confidence="HIGH",
            started_at=datetime.now(timezone.utc) - timedelta(days=14),
            resolved_at=datetime.now(timezone.utc) - timedelta(days=14, hours=-1),
            metadata_json={"seed": True}
        )
        db.add(hist_inc)
        db.commit()

        await memory_service.store_incident_memory(
            incident_id=hist_inc_id,
            summary="Payment Service encountered severe connection timeout exceptions during high traffic.",
            symptoms="HTTP 500 spike, ConnectionTimeoutException in DatabasePool, thread starvation.",
            rca="HikariCP connection pool max size was misconfigured to a very low value, causing all threads to stall under concurrent traffic.",
            resolution="Rolled back deployment to previous stable version and increased max pool size to 50.",
            outcome="Restored DB connection acquisition latency to < 5ms and eliminated 500 errors."
        )
        print(f"  + Historical incident memory seeded: {hist_inc_id} (HikariCP DB pool exhaustion)")

    db.close()
    print("\n✅ Seed data initialization complete!\n")


if __name__ == "__main__":
    asyncio.run(seed_data())
