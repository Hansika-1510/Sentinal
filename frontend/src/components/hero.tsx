"use client";

import dynamic from "next/dynamic";
import Image from "next/image";
import { useCallback, useEffect, useRef, useState } from "react";
import { useInView } from "motion/react";
import { useReducedMotion } from "@/lib/use-reduced-motion";
import {
  ArrowDownRightIcon,
  ArrowUpRightIcon,
  GitCommitIcon,
  PulseIcon,
} from "@phosphor-icons/react";
import { MagneticLink } from "./ui";
import HeroIntro from "./hero-intro";

const SignalLens = dynamic(() => import("./signal-lens"), { ssr: false });
const stages = [
  {
    label: "OBSERVING RUNTIME",
    title: "Every signal. Connected.",
    value: "120",
    unit: "ms",
    detail: "payment-service / production",
    trace: "Listening for the unexpected",
    status: "healthy",
  },
  {
    label: "ANOMALY DETECTED",
    title: "Payment API degradation",
    value: "7.4",
    unit: "%",
    detail: "500 errors / threshold exceeded",
    trace: "Tracing deployment v1.8.3",
    status: "incident",
  },
  {
    label: "TRACING THE EVIDENCE",
    title: "One change. A chain reaction.",
    value: "42",
    unit: "sec",
    detail: "from deployment to anomaly",
    trace: "Related commit: 8f03c2a",
    status: "tracing",
  },
  {
    label: "PROBABLE CAUSE FOUND",
    title: "Connection pool exhausted",
    value: "91",
    unit: "%",
    detail: "confidence / evidence-backed",
    trace: "PaymentService.java : 42-48",
    status: "root",
  },
];

const runtimeEvents = [
  ["10:42:38", "GET /api/payment", "200"],
  ["10:42:39", "GET /api/payment", "200"],
  ["10:42:41", "POST /api/payment", "500"],
  ["10:42:42", "POST /api/payment", "500"],
  ["10:42:43", "ERROR connection pool exhausted", "ERR"],
  ["10:42:44", "POST /api/payment", "500"],
];

export function Hero() {
  const ref = useRef<HTMLElement>(null);
  const visible = useInView(ref, { amount: 0.1 });
  const reduced = useReducedMotion();
  const [step, setStep] = useState(1);
  const [enabled, setEnabled] = useState(false);
  const [ready, setReady] = useState(false);
  const onReady = useCallback(() => setReady(true), []);
  useEffect(() => {
    if (reduced || !visible) return;
    const timer = setInterval(() => {
      if (!document.hidden) setStep((value) => (value + 1) % stages.length);
    }, 4500);
    return () => clearInterval(timer);
  }, [visible, reduced]);
  useEffect(() => {
    const desktop = window.matchMedia(
      "(min-width: 768px) and (prefers-reduced-motion: no-preference)",
    );
    if (!desktop.matches) return;
    // The WebP poster is already on screen, so the WebGL lens is an enhancement:
    // build it once the main thread is idle rather than while the page hydrates.
    let idle = 0;
    let timer = 0;
    const enable = () => setEnabled(true);
    if (typeof window.requestIdleCallback === "function") {
      idle = window.requestIdleCallback(enable, { timeout: 2500 });
    } else {
      timer = window.setTimeout(enable, 700);
    }
    return () => {
      if (idle) window.cancelIdleCallback(idle);
      if (timer) window.clearTimeout(timer);
    };
  }, []);
  const stage = stages[step];
  return (
    <>
      <HeroIntro />
      <section ref={ref} className="hero page-padding" aria-labelledby="hero-title">
        <div className="hero-eyebrow mono">
          <span className="signal-dot" /> AI INTELLIGENCE. HUMAN INSTINCT.
        </div>
        <h1 id="hero-title" className="hero-title">
          <span className="hero-line">
            <span>PRODUCTION</span>
          </span>
          <span className="hero-line">
            <span>BREAKS.</span>
          </span>
          <span className="hero-line hero-last-line">
            <span>
              WE TRACE <em>WHY.</em>
            </span>
          </span>
        </h1>
        <div className={`hero-signal ${stage.status}`}>
          <div className="lens-orbit-label mono">RUNTIME → ROOT CAUSE</div>
          <div className={`lens-art ${ready ? "is-ready" : ""}`}>
            <Image
              src="/visuals/signal-lens.webp"
              alt="A sculptural titanium signal lens with a vermilion core"
              width={850}
              height={850}
              priority
              className="lens-poster"
              unoptimized
            />
            {enabled && <SignalLens onReady={onReady} />}
          </div>
          {/* Decorative labels, so they drift against the lens as the hero
              scrolls. `[data-parallax]` is wired in site-provider and keys its
              range off the parent, which here is `.hero-signal`. */}
          <div className="lens-coordinate coordinate-a mono" data-parallax="-70">
            S / 01
          </div>
          <div className="lens-coordinate coordinate-b mono" data-parallax="-130">
            OBSERVABILITY, WITH CONTEXT.
          </div>
          <a className="hero-incident" href="/console">
            <span className="sr-only">Open the payment incident in the demo console: </span>
            <div className="incident-card-top">
              <span className="mono">
                <span className={`status-dot ${step === 0 ? "is-green" : ""}`} /> {stage.label}
              </span>
              <ArrowUpRightIcon size={15} />
            </div>
            <div className="hero-incident-body">
              <div>
                <strong>{stage.title}</strong>
                <span className="mono">{stage.detail}</span>
              </div>
              <div className="incident-number">
                {stage.value}
                <small>{stage.unit}</small>
              </div>
            </div>
            <div className="incident-sparkline" aria-hidden="true">
              {[
                10, 14, 9, 18, 13, 11, 19, 15, 12, 22, 30, 16, 39, 29, 47, 60, 38, 70, 58, 82, 63,
                88, 70, 91, 68, 83, 75, 94, 76, 88, 69, 91,
              ].map((height, index) => (
                <i
                  key={index}
                  style={{
                    transform: `scaleY(${(step === 0 ? 7 + (index % 5) * 3 : height) / 100})`,
                  }}
                />
              ))}
            </div>
          </a>
          <div className="hero-commit">
            <GitCommitIcon size={18} />
            <div>
              <span className="mono">CONTEXT IDENTIFIED</span>
              <strong>{stage.trace}</strong>
            </div>
            <span className="trace-corner" />
          </div>
        </div>
        <div className="hero-bottom">
          <div className="hero-description">
            <p>
              AI-powered incident response that connects runtime failures to deployments, code, and
              the evidence behind them.
            </p>
            <div className="hero-actions">
              <MagneticLink href="#platform" className="button button-primary" arrow>
                Explore the system
              </MagneticLink>
              <MagneticLink href="#runtime" className="button button-text">
                <span className="play-symbol" aria-hidden="true" />
                View live incident
              </MagneticLink>
            </div>
          </div>
          <div className="hero-side-note">
            <ArrowDownRightIcon size={27} aria-hidden="true" />
            <span>
              Your production incident has a story.
              <br />
              Follow every connection.
            </span>
          </div>
        </div>
      </section>
      <div className="runtime-ribbon" aria-label="Example production log stream">
        <span className="ribbon-label mono">
          <PulseIcon size={17} /> LIVE RUNTIME
        </span>
        <div className="ribbon-window">
          <div className="ribbon-track" style={{ animationDuration: step === 0 ? "42s" : "28s" }}>
            {[0, 1].map((copy) => (
              <div key={copy} className="ribbon-group" aria-hidden={copy === 1}>
                {runtimeEvents.map(([time, route, status], index) => (
                  <span key={index} className="runtime-event mono">
                    <time>{time}</time>
                    <span>{route}</span>
                    <b className={status === "200" ? "log-ok" : "log-error"}>{status}</b>
                  </span>
                ))}
              </div>
            ))}
          </div>
        </div>
        <span className="ribbon-demo mono">SIMULATION</span>
      </div>
    </>
  );
}
