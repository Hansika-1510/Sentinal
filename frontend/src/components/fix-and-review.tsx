"use client";

import { useEffect, useRef, useState } from "react";
import { useInView } from "motion/react";
import { useReducedMotion } from "@/lib/use-reduced-motion";
import {
  ArrowClockwiseIcon,
  ArrowDownRightIcon,
  ArrowRightIcon,
  CheckIcon,
  CircleNotchIcon,
  CodeIcon,
  GitCommitIcon,
  ShieldCheckIcon,
  UserCircleIcon,
} from "@phosphor-icons/react";
import { originalCode, recommendation } from "@/lib/data";
import { CopyButton, DemoLabel, TextLink } from "./ui";

export function FixAdvisor() {
  const [line, setLine] = useState(42);
  return (
    <section id="fix-advisor" className="fix-section section page-padding">
      <h2 className="section-title fix-heading" data-reveal>
        WE DON’T FIX YOUR CODE.
        <br />
        <span className="muted">WE TELL YOU WHERE TO LOOK.</span>
      </h2>
      <div className="fix-workspace" data-reveal>
        <div className="code-window">
          <div className="code-titlebar">
            <div>
              <CodeIcon size={17} />
              <span>PaymentService.java</span>
            </div>
            <span className="mono">8f03c2a</span>
          </div>
          <div className="code-body" aria-label="Original code with the resource lifecycle issue">
            {originalCode.map((row) => (
              <button
                type="button"
                key={row.n}
                className={`code-line ${row.n >= 42 ? "code-at-risk" : ""} ${line === row.n ? "selected" : ""}`}
                onClick={() => setLine(row.n)}
                onMouseEnter={() => setLine(row.n)}
                aria-label={`Line ${row.n}: ${row.text || "empty line"}. ${row.note}`}
                aria-pressed={line === row.n}
              >
                <span className="line-number">{row.n}</span>
                <code>{row.text || " "}</code>
              </button>
            ))}
          </div>
          <div className="code-insight">
            <span className="mono">L{line}</span>
            <p>{originalCode.find((row) => row.n === line)?.note}</p>
          </div>
        </div>
        <aside className="advisor-panel">
          <div className="advisor-label mono">
            <span className="advisor-symbol">↳</span> FIX ADVISOR
          </div>
          <dl>
            <div>
              <dt>Problem</dt>
              <dd>Resource lifecycle is not guaranteed.</dd>
            </div>
            <div>
              <dt>Recommended change</dt>
              <dd>Use automatic resource management.</dd>
            </div>
            <div>
              <dt>Why</dt>
              <dd>
                Unreleased connections exhaust the pool and cause request failures under sustained
                traffic.
              </dd>
            </div>
            <div>
              <dt>Developer action</dt>
              <dd className="advisor-action">
                Update the block <ArrowRightIcon size={13} /> test <ArrowRightIcon size={13} />{" "}
                commit.
              </dd>
            </div>
          </dl>
          <CopyButton value={recommendation} />
        </aside>
      </div>
      <div className="developer-ownership">
        <div className="ownership-flow">
          <UserCircleIcon />
          <span>YOU WRITE IT</span>
          <ArrowRightIcon size={15} />
          <GitCommitIcon />
          <span>YOU COMMIT IT</span>
        </div>
        <p>Guidance, never silent source-code changes.</p>
      </div>
    </section>
  );
}

const checks = [
  { name: "SECURITY", detail: "Resource cleanup verified" },
  { name: "QUALITY", detail: "Lifecycle boundaries checked" },
  { name: "REGRESSION", detail: "Sustained-load test passed" },
  { name: "REVIEW", detail: "Robin Review approved" },
];
const diff = [
  { type: "neutral", text: " public Payment process(Payment payment) {" },
  { type: "removed", text: "-  Connection connection = dataSource.getConnection();" },
  { type: "removed", text: "-  PreparedStatement stmt = connection.prepareStatement(sql);" },
  { type: "removed", text: "-  ResultSet result = stmt.executeQuery();" },
  { type: "removed", text: "-  return mapResult(result);" },
  { type: "added", text: "+  try (Connection connection = dataSource.getConnection();" },
  { type: "added", text: "+       PreparedStatement stmt = connection.prepareStatement(sql)) {" },
  { type: "added", text: "+    stmt.setString(1, payment.id());" },
  { type: "added", text: "+    try (ResultSet result = stmt.executeQuery()) {" },
  { type: "added", text: "+      return mapResult(result);" },
  { type: "added", text: "+    }" },
  { type: "added", text: "+  }" },
  { type: "neutral", text: " }" },
];

export function CodeReview() {
  const ref = useRef<HTMLElement>(null);
  const visible = useInView(ref, { amount: 0.35 });
  const reduced = useReducedMotion();
  const [progress, setProgress] = useState(0);
  const [replay, setReplay] = useState(0);
  useEffect(() => {
    if (reduced && replay === 0) {
      setProgress(4);
      return;
    }
    if (!visible || progress >= 4) return;
    const timer = setInterval(() => setProgress((value) => Math.min(value + 1, 4)), 900);
    return () => clearInterval(timer);
  }, [visible, reduced, replay, progress]);
  return (
    <section ref={ref} id="verification" className="review-section section page-padding">
      <h2 className="section-title review-heading" data-reveal>
        THE DEVELOPER FIXES IT.
        <br />
        <span className="muted">WE VERIFY IT.</span>
      </h2>
      <div className="review-surface product-surface" data-reveal>
        <div className="review-toolbar">
          <span className="mono">
            <GitCommitIcon size={17} /> DEVELOPER COMMIT <b>c91e6b4</b>
          </span>
          <DemoLabel>HUMAN-AUTHORED FIX</DemoLabel>
        </div>
        <div className="review-columns">
          <div className="diff-window">
            <div className="diff-file mono">
              <span>PaymentService.java</span>
              <span className="text-recovered">
                +7 <span className="text-incident">−4</span>
              </span>
            </div>
            <div
              className="diff-body"
              tabIndex={0}
              role="region"
              aria-label="Developer-authored code diff"
            >
              {diff.map((row, index) => (
                <div key={index} className={`diff-line ${row.type}`}>
                  <code>{row.text}</code>
                </div>
              ))}
            </div>
            <div className="diff-footer">
              <UserCircleIcon size={16} />
              <span>Written and committed by the developer</span>
              <CheckIcon size={16} />
            </div>
          </div>
          <div className="review-results">
            <div className="review-agents">
              <ShieldCheckIcon size={26} />
              <span>
                CodeGuard
                <br />
                <span className="muted">+ Robin Review</span>
              </span>
              <button
                type="button"
                aria-label="Replay code review"
                className="icon-button"
                onClick={() => {
                  setProgress(0);
                  setReplay((value) => value + 1);
                }}
              >
                <ArrowClockwiseIcon size={16} />
              </button>
            </div>
            <div className="review-checks">
              {checks.map((check, index) => (
                <div
                  key={check.name}
                  className={`review-check ${progress > index ? "passed" : ""}`}
                >
                  <span className="review-check-icon">
                    {progress > index ? (
                      <CheckIcon size={15} />
                    ) : (
                      <CircleNotchIcon
                        size={15}
                        className={progress === index ? "is-checking" : ""}
                      />
                    )}
                  </span>
                  <span>
                    <strong className="mono">{check.name}</strong>
                    <span>{check.detail}</span>
                  </span>
                  <b className="mono">
                    {progress > index ? (index === 3 ? "APPROVED" : "PASS") : "PENDING"}
                  </b>
                </div>
              ))}
            </div>
            <div
              className={`review-verdict ${progress === 4 ? "complete" : ""}`}
              aria-live="polite"
            >
              <ArrowDownRightIcon size={23} />
              <span>
                {progress === 4
                  ? "Verified. Ready for your pipeline."
                  : "Validating the developer’s change…"}
              </span>
            </div>
          </div>
        </div>
      </div>
      <div className="review-after">
        <p>Your code. Your pipeline. A second set of eyes.</p>
        <TextLink href="#human-control">The human stays in control</TextLink>
      </div>
    </section>
  );
}
