import asyncio
import sys
import os
import time

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
from app.models.action import Action
from app.agents.sentinel import SentinelAgent
from app.agents.investigator import InvestigatorAgent
from app.agents.codeguard import CodeGuardAgent
from app.schemas.deployment import DeploymentCreate
from app.schemas.event import EventCreate
from app.schemas.code_review import StagedReviewRequest
from app.schemas.action import ActionCreate, ActionApproveRequest, ActionExecuteRequest
from app.schemas.incident import IncidentResolveRequest
from app.services.deployment_service import DeploymentService
from app.services.remediation_service import RemediationService
from app.services.autonomous_response_service import run_autonomous_response
from app.services.incident_service import IncidentService
from app.services.postmortem_service import PostmortemService
from app.services.incident_memory_service import IncidentMemoryService
from scripts.seed_demo import seed_data


async def run_demo():
    print("\n" + "=" * 75)
    print(">>> AI SOFTWARE INCIDENT RESPONSE AGENT - END-TO-END DEMO")
    print("=" * 75)

    # 0. Seed database baseline
    await seed_data()
    db = SessionLocal()

    deployment_service = DeploymentService(db)
    codeguard = CodeGuardAgent(db)
    sentinel = SentinelAgent(db)
    investigator = InvestigatorAgent(db)
    remediation_service = RemediationService(db)
    incident_service = IncidentService(db)
    postmortem_service = PostmortemService(db)
    memory_service = IncidentMemoryService(db)

    print("-" * 75)
    print("STAGE 1: DEVELOPER CODE CHANGE & PRE-COMMIT REVIEW (CodeGuard)")
    print("-" * 75)
    
    staged_diff = """diff --git a/src/main/java/com/company/payment/config/DatabasePool.java b/src/main/java/com/company/payment/config/DatabasePool.java
--- a/src/main/java/com/company/payment/config/DatabasePool.java
+++ b/src/main/java/com/company/payment/config/DatabasePool.java
@@ -42,6 +42,6 @@ public class DatabasePool {
-    config.setMaximumPoolSize(50);
-    config.setConnectionTimeout(30000);
+    config.setMaximumPoolSize(2);
+    config.setConnectionTimeout(1000);
"""
    print("Developer stages change in PaymentService (reducing connection pool to 2).")
    review_resp = await codeguard.review_staged_diff(StagedReviewRequest(
        diff=staged_diff,
        commit_hash="a1b2c3d4e5f6",
        author="dev@company.com"
    ))
    print(f"CodeGuard Review: Decision=[{review_resp.decision}], Can Commit=[{review_resp.can_commit}]")
    for f in review_resp.findings:
        print(f"  • [{f.decision}] {f.file}:{f.line} -> {f.finding}")

    print("\n" + "-" * 75)
    print("STAGE 2: DEPLOYMENT REGISTERED (v1.8.3)")
    print("-" * 75)
    dep = deployment_service.record_deployment(DeploymentCreate(
        service="payment-service",
        version="v1.8.3",
        commit_hash="a1b2c3d4e5f6",
        environment="production",
        status="SUCCESS",
        metadata_json={"author": "dev@company.com", "pr": "#402"}
    ))
    print(f"Deployment registered: ID={dep.id}, Version={dep.version}, Commit={dep.commit_hash[:7]}")

    print("\n" + "-" * 75)
    print("STAGE 3: RUNTIME MONITORING & ERROR SPIKE INGESTION (Sentinel)")
    print("-" * 75)
    print("Generating simulated traffic error spike (HTTP 500 ConnectionTimeoutException)...")

    created_incident_id = None
    for i in range(8):
        resp = sentinel.process_event(EventCreate(
            service="payment-service",
            environment="production",
            level="ERROR",
            event_type="http_500",
            message=f"HTTP 500: HikariCP - Connection is not available, request timed out after 1000ms (worker-{i})",
            metadata_json={"uri": "/api/v1/payments/charge", "status_code": 500}
        ))
        if resp.incident_id:
            created_incident_id = resp.incident_id
            if resp.incident_created:
                print(f"[*] SENTINEL TRIGGERED NEW INCIDENT: {created_incident_id}")
                print(f"    Reason: {resp.reason}")
            else:
                print(f"[*] Event linked to active incident: {created_incident_id}")

    assert created_incident_id is not None, "Sentinel failed to capture incident ID!"

    print("\n" + "-" * 75)
    print(f"STAGE 4: AUTONOMOUS INVESTIGATION & EVIDENCE-BACKED RCA (Incident: {created_incident_id})")
    print("-" * 75)
    print("Handing off to the autonomous pipeline - no manual /investigate call, no human in the loop.")
    inv_result = await run_autonomous_response(created_incident_id, db)
    assert inv_result is not None, "Autonomous pipeline returned no investigation result!"
    rca = inv_result.rca

    print(f"Executive Summary: {rca.summary}")
    print(f"\nPrimary Hypothesis:")
    print(f"  Cause:      {rca.primary_hypothesis.cause}")
    print(f"  Confidence: {rca.primary_hypothesis.confidence}")
    print(f"  Evidence Items:")
    for ev in rca.primary_hypothesis.evidence:
        print(f"    - [{ev.type}] {ev.reference}: {ev.explanation}")

    print(f"\nBlast Radius Analysis:")
    print(f"  Total Affected Services: {rca.blast_radius.total_affected_services}")
    print(f"  Direct Impact:           {[n.service_name for n in rca.blast_radius.direct_impact]}")
    print(f"  Downstream Impact:       {[n.service_name for n in rca.blast_radius.downstream_impact]}")
    print(f"  Critical User Journeys:  {rca.blast_radius.critical_user_journeys_impacted}")

    print("\n" + "-" * 75)
    print("STAGE 5: FIX ADVISOR GUIDANCE (Developer Responsibility Invariant)")
    print("-" * 75)
    fix = rca.fix_guidance
    if fix:
        print(f"Repository:         {fix.repository}")
        print(f"File & Lines:       {fix.file}:{fix.line_start}-{fix.line_end}")
        print(f"Problem:            {fix.problem}")
        print(f"Why it happened:    {fix.why}")
        print(f"Recommended Change: {fix.recommended_change}")
        print(f"Expected Behavior:  {fix.expected_behavior}")
        print(f"Validation Steps:")
        for step in fix.validation_steps:
            print(f"  {step}")
        print(f"Safety Disclaimer:  {fix.disclaimer}")

    print("\n" + "-" * 75)
    print("STAGE 6: AUTONOMOUS RESPONSE PLANNING & SAFETY ENFORCEMENT")
    print("-" * 75)
    planned_actions = list(db.scalars(
        select(Action).where(Action.incident_id == created_incident_id).order_by(Action.created_at)
    ).all())
    assert planned_actions, "Response Planner auto-proposed no actions!"
    print(f"Response Planner auto-proposed {len(planned_actions)} action(s) with no human input:")
    for pa in planned_actions:
        print(f"  • ID={pa.id}, Type={pa.type}, Risk={pa.risk_level}, Status={pa.approval_status}")

    # Walk the approval path with the MEDIUM-risk rollback.
    action = next((a for a in planned_actions if a.type == "rollback_deployment"), planned_actions[0])
    print(f"\nSelected for the approval walkthrough: ID={action.id}, Type={action.type}, Risk={action.risk_level}")

    # Safety Test: Attempt execution BEFORE approval (must fail)
    print("\n[SAFETY] Testing Safety Guard: Executing unapproved MEDIUM-risk action...")
    try:
        await remediation_service.execute_action(action.id, ActionExecuteRequest(actor="operator@company.com"))
        print("[FAIL] Security check did not block unapproved action!")
    except Exception as e:
        print(f"[PASSED] (Blocked as expected): {e.message if hasattr(e, 'message') else str(e)}")

    print("\n" + "-" * 75)
    print("STAGE 7: HUMAN APPROVAL & OPERATIONAL EXECUTION")
    print("-" * 75)
    approved_action = remediation_service.approve_action(
        action.id,
        ActionApproveRequest(actor="alice@company.com", reason="RCA confirmed DB pool regression in v1.8.3. Approved rollback to v1.8.2.")
    )
    print(f"Action Status after Human Approval: [{approved_action.approval_status}] by {approved_action.approved_by}")

    # Execute approved action
    executed_action = await remediation_service.execute_action(
        action.id,
        ActionExecuteRequest(actor="alice@company.com")
    )
    print(f"Remediation Execution: Status=[{executed_action.approval_status}]")
    print(f"Execution Result:      {executed_action.result_json.get('message')}")

    print("\n" + "-" * 75)
    print("STAGE 8: RECOVERY MONITORING & RESOLUTION")
    print("-" * 75)
    print("Emitting post-remediation healthy telemetry events...")
    for _ in range(5):
        sentinel.process_event(EventCreate(
            service="payment-service",
            environment="production",
            level="INFO",
            event_type="health_check",
            message="Health check 200 OK: Payment gateway response latency 4ms",
            metadata_json={"status": "healthy"}
        ))

    # Resolve incident
    resolved_inc = await incident_service.resolve_incident(
        created_incident_id,
        IncidentResolveRequest(actor="alice@company.com", reason="Recovery verified by Sentinel.")
    )
    print(f"Incident Status: [{resolved_inc.status}], Resolved At: {resolved_inc.resolved_at}")

    print("\n" + "-" * 75)
    print("STAGE 9: POSTMORTEM GENERATION & INCIDENT MEMORY")
    print("-" * 75)
    postmortem = await postmortem_service.generate_and_store_postmortem(resolved_inc)
    print(f"Postmortem Title: {postmortem.title}")
    print(f"Root Cause:       {postmortem.root_cause}")
    print(f"Lessons Learned:")
    for ll in postmortem.lessons_learned:
        print(f"  * {ll}")
    print(f"Preventive Recommendations:")
    for pr in postmortem.preventive_recommendations:
        print(f"  * {pr}")

    print("\n" + "-" * 75)
    print("STAGE 10: HISTORICAL MEMORY SEMANTIC RETRIEVAL TEST")
    print("-" * 75)
    retrieved = await memory_service.find_similar_incidents("HikariCP connection pool timeout error", top_k=2)
    print(f"Retrieved {len(retrieved)} matching incidents from semantic memory:")
    for m in retrieved:
        print(f"  * [{m.incident_id}] (similarity: {m.similarity_score}): {m.summary[:80]}...")

    db.close()
    print("\n" + "=" * 75)
    print("[SUCCESS] FULL INCIDENT RESPONSE LIFECYCLE COMPLETE & VERIFIED!")
    print("=" * 75 + "\n")


if __name__ == "__main__":
    asyncio.run(run_demo())
