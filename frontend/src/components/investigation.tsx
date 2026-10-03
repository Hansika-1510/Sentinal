"use client";

import { useEffect, useRef, useState } from "react";
import dynamic from "next/dynamic";
import { useInView } from "motion/react";
import { useReducedMotion } from "@/lib/use-reduced-motion";
import { gsap } from "gsap";
import { ScrollTrigger } from "gsap/ScrollTrigger";
import { ArrowDownIcon, ArrowUpRightIcon, CaretDownIcon, CheckIcon } from "@phosphor-icons/react";
import { evidence, timeline } from "@/lib/data";
import { DemoLabel } from "./ui";

const EvidenceGraph3D = dynamic(() => import("./evidence-graph-3d"), { ssr: false });

export function Investigation() {
  const ref = useRef<HTMLElement>(null);
  const [expanded, setExpanded] = useState<number | null>(5);
  const reduced = useReducedMotion();
  useEffect(() => {
    if (reduced) return;
    gsap.registerPlugin(ScrollTrigger);
    const context = gsap.context(() => {
      gsap.from(".timeline-progress", {
        scaleY: 0,
        transformOrigin: "top",
        ease: "none",
        scrollTrigger: {
          trigger: ".investigation-timeline",
          start: "top 65%",
          end: "bottom 70%",
          scrub: 0.6,
        },
      });
      gsap.utils
        .toArray<HTMLElement>(".timeline-event")
        .forEach((event) =>
          gsap.from(event, {
            opacity: 0,
            x: 16,
            scrollTrigger: { trigger: event, start: "top 90%", end: "top 64%", scrub: 0.6 },
          }),
        );
    }, ref);
    return () => context.revert();
  }, [reduced]);
  return (
    <section id="investigation" ref={ref} className="investigation-section section page-padding">
      <div className="investigation-heading">
        <span className="eyebrow mono">THE INVESTIGATOR</span>
        <h2 className="section-title" data-reveal>
          THEN WE
          <br />
          TRACE
          <br />
          <span className="accent">IT BACK.</span>
        </h2>
        <p className="section-copy" data-reveal>
          Every failure leaves a trail.
          <br />
          We make it impossible to miss.
        </p>
        <div className="timeline-key mono">
          <ArrowDownIcon size={22} />
          <span>
            ONE INCIDENT
            <br />
            EVERY CONNECTION
          </span>
        </div>
      </div>
      <div className="investigation-timeline">
        <div className="timeline-rail" aria-hidden="true">
          <div className="timeline-progress" />
        </div>
        {timeline.map((event, index) => (
          <article
            key={event.time}
            className={`timeline-event ${event.kind === "error" ? "event-error" : ""} ${index === 5 ? "event-found" : ""}`}
          >
            <span className="timeline-dot" aria-hidden="true" />
            <time className="mono">{event.time}</time>
            <button
              type="button"
              aria-expanded={expanded === index}
              aria-controls={`timeline-evidence-${index}`}
              onClick={() => setExpanded(expanded === index ? null : index)}
            >
              <span>
                <strong>{event.title}</strong>
                <span className="mono">{event.detail}</span>
              </span>
              <CaretDownIcon size={17} className={expanded === index ? "is-open" : ""} />
            </button>
            <div
              id={`timeline-evidence-${index}`}
              hidden={expanded !== index}
              className="timeline-note"
            >
              {event.note}
            </div>
          </article>
        ))}
      </div>
    </section>
  );
}

export function EvidenceChain() {
  const ref = useRef<HTMLElement>(null);
  const chain = useRef<HTMLDivElement>(null);
  const [selected, setSelected] = useState(0);
  const [wide, setWide] = useState(false);
  const reduced = useReducedMotion();
  // Below 1024px the section reflows into a grid and the connector SVG is
  // hidden outright, so there is nothing for a 3D graph to sit behind.
  useEffect(() => {
    const media = window.matchMedia("(min-width: 1024px) and (prefers-reduced-motion: no-preference)");
    const update = () => setWide(media.matches);
    update();
    media.addEventListener("change", update);
    return () => media.removeEventListener("change", update);
  }, []);
  const near = useInView(chain, { margin: "300px 0px", amount: 0 });
  useEffect(() => {
    if (reduced) return;
    gsap.registerPlugin(ScrollTrigger);
    const context = gsap.context(() => {
      gsap.fromTo(
        ".evidence-path",
        { strokeDashoffset: 1 },
        {
          strokeDashoffset: 0,
          stagger: 0.08,
          ease: "none",
          scrollTrigger: {
            trigger: ".evidence-canvas",
            start: "top 70%",
            end: "bottom 70%",
            scrub: 1,
          },
        },
      );
    }, ref);
    return () => context.revert();
  }, [reduced]);
  const paths = [
    "M240 130H320Q355 130 385 180L465 260",
    "M230 370H320Q370 370 420 330L465 310",
    "M990 90H900Q850 90 810 165L735 250",
    "M1020 370H900Q850 370 805 340L735 310",
    "M600 560V470",
  ];
  return (
    <section id="root-cause" ref={ref} className="evidence-section section page-padding">
      <h2 className="section-title" data-reveal>
        NOT A GUESS.
        <br />
        <span className="muted">AN EVIDENCE CHAIN.</span>
      </h2>
      <div className="evidence-canvas" ref={chain}>
        {wide && !reduced && near && <EvidenceGraph3D selected={selected} />}
        <svg
          className="evidence-connections"
          viewBox="0 0 1200 610"
          preserveAspectRatio="none"
          fill="none"
          aria-hidden="true"
        >
          {paths.map((path, index) => (
            <g key={path}>
              <path d={path} className="evidence-base" />
              <path
                d={path}
                pathLength="1"
                className={`evidence-path ${selected === index ? "selected" : ""}`}
              />
            </g>
          ))}
        </svg>
        <div className="root-cause-card">
          <div className="root-card-top mono">
            <span>
              <span className="status-dot" />
              PROBABLE ROOT CAUSE
            </span>
            <ArrowUpRightIcon size={16} />
          </div>
          <h3>PaymentService.java</h3>
          <span className="root-line-reference mono">LINES 42-48</span>
          <p>
            Database resources are not
            <br />
            being reliably released.
          </p>
          <div className="root-card-bottom">
            <div>
              <span className="mono">WHY IT MATTERS</span>
              <p>
                Repeated requests exhaust
                <br />
                the connection pool.
              </p>
            </div>
            <div className="root-confidence">
              <span className="mono">CONFIDENCE</span>
              <strong>
                91<small>%</small>
              </strong>
            </div>
          </div>
        </div>
        {evidence.map((item, index) => (
          <button
            key={item.id}
            type="button"
            className={`evidence-node evidence-node-${index} ${selected === index ? "selected" : ""}`}
            aria-pressed={selected === index}
            onClick={() => setSelected(index)}
          >
            <span className="evidence-check">
              <CheckIcon size={14} />
            </span>
            <span>
              <strong>{item.title}</strong>
              <span className="mono">{item.meta}</span>
            </span>
          </button>
        ))}
      </div>
      <div className="evidence-detail" aria-live="polite">
        <div className="evidence-detail-label mono">
          <span className="accent">EVIDENCE /</span> {evidence[selected].title}
        </div>
        <p>{evidence[selected].detail}</p>
        <code>{evidence[selected].code}</code>
      </div>
      <div className="evidence-caption">
        <p>Confidence you can inspect. A conclusion you can validate.</p>
        <DemoLabel />
      </div>
    </section>
  );
}
