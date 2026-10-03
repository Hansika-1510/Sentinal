"use client";

import { useEffect, useRef, useState } from "react";
import { useInView } from "motion/react";
import { useReducedMotion } from "@/lib/use-reduced-motion";
import {
  ArrowDownRightIcon,
  ArrowRightIcon,
  CheckIcon,
  CheckCircleIcon,
  DatabaseIcon,
  FingerprintIcon,
} from "@phosphor-icons/react";
import { memoryIncidents } from "@/lib/data";
import { DemoLabel, SectionHeading } from "./ui";
import { TelemetryChart } from "./telemetry-chart";

export function Recovery() {
  const ref = useRef<HTMLElement>(null);
  const visible = useInView(ref, { amount: 0.35 });
  const reduced = useReducedMotion();
  const [phase, setPhase] = useState(0);
  const [automatic, setAutomatic] = useState(true);
  useEffect(() => {
    if (!automatic) return;
    if (reduced) {
      setPhase(2);
      return;
    }
    if (!visible) return;
    const validating = setTimeout(() => setPhase(1), 650);
    const recovered = setTimeout(() => setPhase(2), 2300);
    return () => {
      clearTimeout(validating);
      clearTimeout(recovered);
    };
  }, [visible, reduced, automatic]);
  const healed = phase === 2;
  return (
    <section
      ref={ref}
      id="recovery"
      className={`recovery-section section page-padding ${healed ? "is-recovered" : ""}`}
    >
      <SectionHeading>
        AND THEN
        <br />
        WE WATCH IT <span className="recovery-word">HEAL.</span>
      </SectionHeading>
      <div className="recovery-stage" data-reveal>
        <div className="recovery-readout">
          <div className="mono">PAYMENT API / ERROR RATE</div>
          <div className="recovery-number">
            {healed ? "0.2" : phase === 1 ? "1.8" : "7.4"}
            <span>%</span>
          </div>
          <p>
            <ArrowDownRightIcon size={21} />
            {healed
              ? "Back to baseline. Verified against live signals."
              : phase === 1
                ? "The reviewed change is being validated."
                : "The incident before the developer’s fix."}
          </p>
          <div
            className="recovery-comparison"
            role="group"
            aria-label="Compare runtime before and after recovery"
          >
            <button
              type="button"
              className={!healed ? "active" : ""}
              aria-pressed={!healed}
              onClick={() => {
                setAutomatic(false);
                setPhase(0);
              }}
            >
              Before
            </button>
            <button
              type="button"
              className={healed ? "active" : ""}
              aria-pressed={healed}
              onClick={() => {
                setAutomatic(false);
                setPhase(2);
              }}
            >
              After the fix
            </button>
          </div>
        </div>
        <div className="recovery-visual">
          <div className="recovery-bar-label mono">
            <span>HTTP 500s</span>
            <span>{healed ? "2 / min" : "342 / min"}</span>
          </div>
          <div className="recovery-bars" aria-hidden="true">
            {Array.from({ length: 38 }, (_, index) => (
              <div
                key={index}
                style={{
                  transform: `scaleY(${Math.round((healed ? 0.04 + (index % 5) * 0.018 : 0.2 + Math.abs(Math.sin(index * 1.8)) * 0.7) * 1000) / 1000})`,
                  transitionDelay: `${index * 13}ms`,
                }}
              />
            ))}
          </div>
          <div className="recovery-secondary">
            <div>
              <span className="mono">P95 LATENCY</span>
              <strong>
                {healed ? "120" : "830"}
                <small>ms</small>
              </strong>
            </div>
            <div>
              <span className="mono">CONNECTION POOL</span>
              <strong>
                {healed ? "6" : "30"}
                <small>/ 30</small>
              </strong>
            </div>
            <div>
              <span className="mono">SERVICE HEALTH</span>
              <span className="health-value">
                <CheckCircleIcon size={19} />
                {healed ? "Operational" : "Degraded"}
              </span>
            </div>
          </div>
        </div>
      </div>
      <div className="recovery-chart">
        <TelemetryChart
          level={4}
          recovered={healed}
          label="Verified recovery after deployment v1.8.4"
        />
      </div>
      <div className="recovery-status" aria-live="polite">
        {["INVESTIGATING", "VALIDATING", "RECOVERED"].map((label, index) => (
          <div key={label} className={phase >= index ? "complete" : ""}>
            <span className="status-step">
              {phase > index || healed ? <CheckIcon size={12} /> : index + 1}
            </span>
            <span className="mono">{label}</span>
            {index < 2 && <ArrowRightIcon size={19} />}
          </div>
        ))}
        <DemoLabel>RECOVERY IS VERIFIED, NOT ASSUMED.</DemoLabel>
      </div>
    </section>
  );
}

export function IncidentMemory() {
  const [selected, setSelected] = useState(0);
  const previous = memoryIncidents[selected];
  return (
    <section id="memory" className="memory-section section page-padding">
      <SectionHeading>
        THE NEXT INCIDENT
        <br />
        STARTS WITH <span className="muted">THE LAST ONE.</span>
      </SectionHeading>
      <div className="memory-workspace" data-reveal>
        <div className="memory-archive">
          <div className="archive-shadow archive-shadow-2" />
          <div className="archive-shadow archive-shadow-1" />
          <article className="archive-record">
            <div className="archive-top mono">
              <span>
                <DatabaseIcon size={18} /> INCIDENT MEMORY
              </span>
              <CheckCircleIcon size={19} />
            </div>
            <div className="archive-id">#1042</div>
            <h3>
              DB connection
              <br />
              exhaustion.
            </h3>
            <div className="archive-record-meta">
              <span className="mono">PAYMENT SERVICE</span>
              <span>Resolved 14m ago</span>
            </div>
            <div className="archive-tags">
              <span>Resource lifecycle</span>
              <span>Verified resolution</span>
            </div>
            <div className="archive-bottom">
              <FingerprintIcon size={21} />
              <span className="mono">EVIDENCE PRESERVED. CONTEXT RETAINED.</span>
            </div>
          </article>
        </div>
        <div className="memory-matches">
          <div className="memory-intro">
            <span className="mono">A FAMILIAR PATTERN</span>
            <p>
              Every resolution becomes
              <br />a head start.
            </p>
          </div>
          <div className="memory-match-list" role="group" aria-label="Explore similar incidents">
            {memoryIncidents.map((incident, index) => (
              <button
                type="button"
                key={incident.id}
                className={`memory-match ${selected === index ? "active" : ""}`}
                aria-pressed={selected === index}
                onClick={() => setSelected(index)}
              >
                <span className="mono">#{incident.id}</span>
                <span>{incident.title}</span>
                <strong>{incident.similarity}</strong>
                <ArrowRightIcon size={16} />
              </button>
            ))}
          </div>
          <div className="memory-lesson" aria-live="polite">
            <span className="mono">{previous.service.toUpperCase()} / SHARED EVIDENCE</span>
            <p>{previous.cause}</p>
            <span>{previous.lesson}</span>
          </div>
        </div>
      </div>
    </section>
  );
}
