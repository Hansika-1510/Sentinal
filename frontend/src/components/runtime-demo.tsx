"use client";

import { useEffect, useRef, useState } from "react";
import { useInView } from "motion/react";
import { useReducedMotion } from "@/lib/use-reduced-motion";
import {
  ArrowUpRightIcon,
  ArrowClockwiseIcon,
  CaretDownIcon,
  PauseIcon,
  PlayIcon,
  PulseIcon,
  WarningCircleIcon,
} from "@phosphor-icons/react";
import { BrandMark, DemoLabel, SectionHeading } from "./ui";
import { TelemetryChart } from "./telemetry-chart";

const samples = [
  { error: "0.2", latency: "120", failures: "2", state: "Healthy baseline" },
  { error: "0.3", latency: "145", failures: "8", state: "Deployment detected" },
  { error: "0.4", latency: "210", failures: "24", state: "Baseline shifting" },
  { error: "1.8", latency: "420", failures: "86", state: "Anomaly detected" },
  { error: "7.4", latency: "830", failures: "342", state: "Incident created" },
];
const logs = [
  ["10:42:38.104", "INFO", "GET /api/payment", "200", "118ms"],
  ["10:42:39.281", "INFO", "GET /api/payment", "200", "124ms"],
  ["10:42:41.092", "WARN", "HikariPool: pool at capacity", "30/30", ""],
  ["10:42:42.781", "ERROR", "POST /api/payment", "500", "829ms"],
  ["10:42:43.016", "ERROR", "Connection is not available", "TIMEOUT", ""],
  ["10:43:02.143", "ERROR", "POST /api/payment", "500", "842ms"],
];

export function RuntimeDemo() {
  const ref = useRef<HTMLElement>(null);
  const visible = useInView(ref, { amount: 0.3 });
  const reduced = useReducedMotion();
  const [stage, setStage] = useState(0);
  const [running, setRunning] = useState(true);
  const [manual, setManual] = useState(false);
  const [service, setService] = useState("payment");
  const [environment, setEnvironment] = useState("production");
  useEffect(() => {
    if (reduced && !manual) {
      setStage(4);
      setRunning(false);
    }
  }, [reduced, manual]);
  useEffect(() => {
    if (!visible || !running || environment === "staging" || stage >= 4 || (reduced && !manual))
      return;
    const timer = setInterval(() => {
      if (!document.hidden) setStage((value) => Math.min(4, value + 1));
    }, 1800);
    return () => clearInterval(timer);
  }, [visible, running, stage, environment, reduced, manual]);
  const data = samples[environment === "staging" ? 0 : stage];
  const incident = stage === 4 && environment === "production";
  const error = service === "checkout" ? (Number(data.error) * 0.58).toFixed(1) : data.error;
  const latency =
    service === "database" ? String(Math.round(Number(data.latency) * 1.2)) : data.latency;
  return (
    <section ref={ref} id="runtime" className="runtime-section section page-padding">
      <SectionHeading>
        IT STARTS
        <br />
        WITH A <span className="accent">SIGNAL.</span>
      </SectionHeading>
      <p className="section-copy" data-reveal>
        A release lands. Latency climbs. Somewhere in the noise, a story begins.
      </p>
      <div
        className={`runtime-panel product-surface ${incident ? "has-incident" : ""}`}
        data-reveal
      >
        <div className="product-toolbar">
          <div className="product-breadcrumb">
            <BrandMark />
            <span>Sentinel</span>
            <span className="breadcrumb-divider">/</span>
            <span>Runtime</span>
          </div>
          <div className="runtime-controls">
            <DemoLabel>SIMULATED TELEMETRY</DemoLabel>
            <label className="environment-select">
              <span className="sr-only">Environment</span>
              <select
                value={environment}
                onChange={(event) => {
                  setEnvironment(event.target.value);
                  if (event.target.value === "staging") setRunning(false);
                }}
              >
                <option value="production">production</option>
                <option value="staging">staging</option>
              </select>
              <CaretDownIcon size={12} />
            </label>
          </div>
        </div>
        <div className="runtime-service-bar">
          <div className="service-tabs" role="group" aria-label="Service">
            {["payment", "checkout", "database"].map((item) => (
              <button
                type="button"
                key={item}
                onClick={() => setService(item)}
                className={service === item ? "active" : ""}
                aria-pressed={service === item}
              >
                {item === "database" ? "Database" : `${item[0].toUpperCase()}${item.slice(1)} API`}
              </button>
            ))}
          </div>
          <span className={`runtime-state mono ${incident ? "text-incident" : ""}`}>
            <span className="status-dot" />
            {data.state}
          </span>
        </div>
        <div className="runtime-metrics">
          <div>
            <span className="mono">ERROR RATE</span>
            <strong className={stage > 2 && environment === "production" ? "text-incident" : ""}>
              {error}
              <small>%</small>
            </strong>
            <span>of all requests</span>
          </div>
          <div>
            <span className="mono">P95 LATENCY</span>
            <strong>
              {latency}
              <small>ms</small>
            </strong>
            <span>request duration</span>
          </div>
          <div>
            <span className="mono">HTTP 500s</span>
            <strong>
              {data.failures}
              <small>/min</small>
            </strong>
            <span>failed requests</span>
          </div>
          <div className="health-metric">
            <span className="mono">SERVICE HEALTH</span>
            <strong>
              <PulseIcon size={30} />
              {stage > 2 && environment === "production" ? "Degraded" : "Operational"}
            </strong>
            <span>{service}-service</span>
          </div>
        </div>
        <div className="runtime-chart-header">
          <span className="mono">REQUEST ERRORS</span>
          <div className="playback-controls">
            <button
              type="button"
              className="icon-button"
              onClick={() => {
                setManual(true);
                if (stage >= 4) setStage(0);
                setRunning(!running || stage >= 4);
                setEnvironment("production");
              }}
              aria-label={running && stage < 4 ? "Pause simulation" : "Play simulation"}
            >
              {running && stage < 4 ? <PauseIcon size={15} /> : <PlayIcon size={15} />}
            </button>
            <button
              type="button"
              className="icon-button"
              aria-label="Replay incident"
              onClick={() => {
                setManual(true);
                setStage(0);
                setEnvironment("production");
                setRunning(true);
              }}
            >
              <ArrowClockwiseIcon size={15} />
            </button>
            <span className="mono">LAST 5 MINUTES</span>
          </div>
        </div>
        <TelemetryChart
          level={environment === "staging" ? 0 : stage}
          label={`${service} error rate`}
        />
        <div className="runtime-logs">
          <div className="log-header mono">
            <span>LIVE LOGS</span>
            <span>{service}-service</span>
          </div>
          <div className="log-lines" aria-label="Example log entries">
            {logs
              .slice(Math.max(0, Math.min(stage, 3) - 1), Math.min(6, stage + 3))
              .map(([time, level, route, status, duration]) => (
                <div
                  className={`log-row mono ${environment === "staging" ? "info" : level.toLowerCase()}`}
                  key={time}
                >
                  <time>{time}</time>
                  <span>{environment === "staging" ? "INFO" : level}</span>
                  <code>
                    {environment === "staging" && level !== "INFO"
                      ? "Health check passed"
                      : route.replace("payment", service)}
                  </code>
                  <b>{environment === "staging" ? "200" : status}</b>
                  <span>{duration}</span>
                </div>
              ))}
          </div>
        </div>
        <div
          className={`runtime-incident-banner ${incident ? "is-active" : ""}`}
          aria-live="polite"
        >
          <WarningCircleIcon size={23} />
          <div>
            <strong>
              {incident ? "Incident #1042 created" : "Sentinel is observing every signal"}
            </strong>
            <span className="mono">
              {incident
                ? "HIGH / payment-service / production"
                : "Logs, metrics, deployments. One shared context."}
            </span>
          </div>
          <a href="/console" aria-label="Investigate incident in console">
            <ArrowUpRightIcon size={24} />
          </a>
        </div>
      </div>
    </section>
  );
}
