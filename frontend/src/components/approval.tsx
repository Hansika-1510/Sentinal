"use client";

import { useId, useState } from "react";
import {
  ArrowRightIcon,
  CheckCircleIcon,
  ClockIcon,
  LockKeyIcon,
  ShieldCheckIcon,
  XCircleIcon,
} from "@phosphor-icons/react";
import { DemoLabel, Dialog, SectionHeading } from "./ui";

export type ApprovalDecision = { decision: "approved" | "rejected"; reason: string; time: string };

export function ApprovalCard({
  onDecision,
  compact = false,
  initialDecision = null,
}: {
  onDecision?: (decision: ApprovalDecision) => void;
  compact?: boolean;
  initialDecision?: ApprovalDecision | null;
}) {
  const [decision, setDecision] = useState<ApprovalDecision | null>(initialDecision);
  const [open, setOpen] = useState(false);
  const [reason, setReason] = useState("");
  const reasonId = useId();
  const record = (result: "approved" | "rejected", note: string) => {
    const entry: ApprovalDecision = {
      decision: result,
      reason: note,
      time: new Date().toLocaleTimeString("en-GB", { timeZone: "UTC" }),
    };
    setDecision(entry);
    setOpen(false);
    onDecision?.(entry);
  };
  return (
    <>
      <div className={`approval-card ${compact ? "approval-compact" : ""}`}>
        <div className="approval-header">
          <span className="mono">
            <LockKeyIcon size={15} />
            {decision ? "DECISION RECORDED" : "HUMAN APPROVAL REQUIRED"}
          </span>
          <DemoLabel>DEMO</DemoLabel>
        </div>
        {decision ? (
          <div className={`approval-outcome ${decision.decision}`} aria-live="polite">
            {decision.decision === "approved" ? (
              <CheckCircleIcon size={40} />
            ) : (
              <XCircleIcon size={40} />
            )}
            <h3>
              {decision.decision === "approved"
                ? "Approved. With a record."
                : "Rejected. You’re in control."}
            </h3>
            <p>
              {decision.decision === "approved"
                ? "The scoped rollback is approved in this demo. Sentinel will verify the outcome against runtime signals."
                : "The proposed action was rejected. Production remains unchanged in this example."}
            </p>
            <div className="approval-audit">
              <span className="mono">AUDIT / {decision.time} UTC</span>
              <p>{decision.reason}</p>
              <span>Decision by you. Scope: payment-service.</span>
            </div>
            {!compact && (
              <button
                type="button"
                className="button button-outline"
                onClick={() => {
                  setDecision(null);
                  setReason("");
                }}
              >
                Reset example
                <ArrowRightIcon size={17} />
              </button>
            )}
          </div>
        ) : (
          <>
            <div className="approval-action">
              <span className="mono">RECOMMENDED ACTION</span>
              <h3>
                Rollback
                <br />
                <span>payment-service</span>
              </h3>
              <div className="rollback-versions mono">
                <span>v1.8.3</span>
                <ArrowRightIcon size={18} />
                <span>v1.8.2</span>
              </div>
            </div>
            <dl className="approval-details">
              <div>
                <dt>Risk</dt>
                <dd className="text-warning">HIGH</dd>
              </div>
              <div>
                <dt>Expected impact</dt>
                <dd>Temporary service interruption</dd>
              </div>
              <div>
                <dt>Rollback path</dt>
                <dd>Available</dd>
              </div>
              <div>
                <dt>Scope</dt>
                <dd>payment-service / production</dd>
              </div>
            </dl>
            <div className="approval-buttons">
              <button
                type="button"
                className="button button-outline"
                onClick={() => record("rejected", "Operator declined the proposed rollback.")}
              >
                Reject
              </button>
              <button type="button" className="button button-light" onClick={() => setOpen(true)}>
                Approve
                <ArrowRightIcon size={17} />
              </button>
            </div>
            <div className="approval-footnote">
              <ClockIcon size={13} />
              Waiting for a human decision.
            </div>
          </>
        )}
      </div>
      <Dialog title="Approve this action" open={open} onClose={() => setOpen(false)}>
        <div className="approval-confirm-summary">
          <span className="mono text-warning">HIGH RISK / INTERACTIVE DEMO</span>
          <p>
            Rollback <strong>payment-service</strong> from <strong>v1.8.3</strong> to{" "}
            <strong>v1.8.2</strong>.
          </p>
          <span>
            Expected impact: temporary service interruption. This demo records your decision without
            changing a real service.
          </span>
        </div>
        <form
          onSubmit={(event) => {
            event.preventDefault();
            if (reason.trim().length >= 8) record("approved", reason.trim());
          }}
        >
          <label className="approval-reason" htmlFor={reasonId}>
            Reason for approval
            <textarea
              id={reasonId}
              value={reason}
              onChange={(event) => setReason(event.target.value)}
              required
              minLength={8}
              maxLength={500}
              placeholder="Record why this action is appropriate…"
              aria-describedby={`${reasonId}-help`}
            />
          </label>
          <p id={`${reasonId}-help`} className="form-help">
            At least 8 characters. Your reason is retained in the audit trail.
          </p>
          <div className="dialog-actions">
            <button type="button" className="button button-outline" onClick={() => setOpen(false)}>
              Cancel
            </button>
            <button
              type="submit"
              className="button button-primary"
              disabled={reason.trim().length < 8}
            >
              Confirm approval
              <ArrowRightIcon size={17} />
            </button>
          </div>
        </form>
      </Dialog>
    </>
  );
}

export function HumanControl() {
  return (
    <section id="human-control" className="human-section section page-padding">
      <div className="human-message">
        <span className="eyebrow mono">AUTONOMOUS INTELLIGENCE. HUMAN AUTHORITY.</span>
        <SectionHeading>
          AI CAN
          <br />
          RECOMMEND.
          <br />
          <span className="muted">
            HUMANS
            <br />
            DECIDE.
          </span>
        </SectionHeading>
        <p className="section-copy" data-reveal>
          Sensitive production actions stop at your approval. You see the risk, the impact, and the
          way back.
        </p>
        <div className="human-promises" data-reveal>
          <p>
            <ShieldCheckIcon size={17} />
            No silent code changes.
          </p>
          <p>
            <ShieldCheckIcon size={17} />
            No hidden production actions.
          </p>
          <p>
            <ShieldCheckIcon size={17} />
            Every decision is auditable.
          </p>
        </div>
      </div>
      <div className="human-control-example" data-reveal>
        <ApprovalCard />
      </div>
    </section>
  );
}
