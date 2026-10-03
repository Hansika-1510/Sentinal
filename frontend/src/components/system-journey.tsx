"use client";

import { useEffect, useRef, useState, type CSSProperties } from "react";
import dynamic from "next/dynamic";
import { useInView } from "motion/react";
import { useReducedMotion } from "@/lib/use-reduced-motion";
import { gsap } from "gsap";
import { ScrollTrigger } from "gsap/ScrollTrigger";
import {
  ArrowRightIcon,
  CheckCircleIcon,
  CodeIcon,
  CubeIcon,
  FingerprintIcon,
  GitBranchIcon,
  GitCommitIcon,
  MagnifyingGlassIcon,
  PulseIcon,
  ShieldCheckIcon,
  TerminalWindowIcon,
  UserCircleIcon,
  WarningCircleIcon,
} from "@phosphor-icons/react";
import { journey } from "@/lib/data";
import { BrandMark, TextLink } from "./ui";

const icons = [
  CodeIcon,
  ShieldCheckIcon,
  GitBranchIcon,
  CubeIcon,
  PulseIcon,
  WarningCircleIcon,
  MagnifyingGlassIcon,
  FingerprintIcon,
  TerminalWindowIcon,
  UserCircleIcon,
  GitCommitIcon,
  CubeIcon,
  CheckCircleIcon,
];

const JourneyRoute3D = dynamic(() => import("./journey-route-3d"), { ssr: false });

export function SystemJourney({ standalone = false }: { standalone?: boolean }) {
  const ref = useRef<HTMLElement>(null);
  const map = useRef<HTMLDivElement>(null);
  const [active, setActive] = useState(4);
  const [wide, setWide] = useState(false);
  const activeRef = useRef(4);
  const reduced = useReducedMotion();
  // The pin itself is gated on this exact query, so the rail appears and
  // disappears with the scene it belongs to rather than outliving it.
  useEffect(() => {
    const media = window.matchMedia(
      "(min-width: 1024px) and (prefers-reduced-motion: no-preference)",
    );
    const update = () => setWide(media.matches);
    update();
    media.addEventListener("change", update);
    return () => media.removeEventListener("change", update);
  }, []);
  const near = useInView(map, { margin: "300px 0px", amount: 0 });
  useEffect(() => {
    if (reduced || standalone) return;
    gsap.registerPlugin(ScrollTrigger);
    const media = gsap.matchMedia();
    media.add("(min-width: 1024px)", () => {
      const trigger = ScrollTrigger.create({
        trigger: ref.current,
        start: "top top",
        end: "+=1250",
        pin: true,
        scrub: 1,
        invalidateOnRefresh: true,
        onUpdate: (self) => {
          const next = Math.min(12, Math.floor(self.progress * 13));
          if (next !== activeRef.current) {
            activeRef.current = next;
            setActive(next);
          }
        },
      });
      return () => trigger.kill();
    });
    return () => media.revert();
  }, [reduced, standalone]);
  const step = journey[active];
  return (
    <section
      ref={ref}
      id="platform"
      className={`system-section page-padding ${standalone ? "system-standalone" : ""}`}
      aria-labelledby="system-heading"
    >
      <div className="system-header">
        <span className="eyebrow mono">THE ENTIRE INCIDENT LIFECYCLE</span>
        <h2 id="system-heading" className="section-title">
          SENTINEL CONNECTS
          <br />
          <span className="muted">THE DOTS.</span>
          <BrandMark className="heading-mark" />
        </h2>
      </div>
      <div className="system-map" ref={map}>
        {wide && !standalone && !reduced && near && <JourneyRoute3D active={active} />}
        <svg
          className="system-wiring"
          viewBox="0 0 1200 215"
          preserveAspectRatio="none"
          fill="none"
          aria-hidden="true"
        >
          <path d="M86 50H1114Q1175 50 1175 106Q1175 164 1114 164H86" className="route-base" />
          <path
            d="M86 50H1114Q1175 50 1175 106Q1175 164 1114 164H86"
            className="route-active"
            pathLength="1"
            style={{ strokeDashoffset: 1 - (active + 1) / 13 }}
          />
        </svg>
        <ol className="system-nodes">
          {journey.map((node, index) => {
            const Icon = icons[index];
            return (
              <li
                key={node.id}
                style={
                  {
                    "--node-column": index < 7 ? index + 1 : 13 - index,
                    "--node-row": index < 7 ? 1 : 2,
                  } as CSSProperties
                }
              >
                <button
                  type="button"
                  className={`system-node ${index === active ? "is-active" : ""} ${index < active ? "is-past" : ""} ${index === 12 ? "node-recovery" : ""}`}
                  aria-pressed={index === active}
                  onClick={() => {
                    activeRef.current = index;
                    setActive(index);
                  }}
                >
                  <span className="node-icon">
                    <Icon size={22} />
                  </span>
                  <span>{node.name}</span>
                </button>
              </li>
            );
          })}
        </ol>
      </div>
      <div className="journey-focus" key={step.id}>
        <div className="journey-index mono">
          {String(active + 1).padStart(2, "0")}
          <span> / 13</span>
        </div>
        <div className="journey-main">
          <span className="mono journey-group">{step.group}</span>
          <h3>
            {step.name}
            <ArrowRightIcon size={28} />
          </h3>
          <p>{step.detail}</p>
        </div>
        <div className="journey-readout">
          <span className="mono">CONNECTED CONTEXT</span>
          <strong>{step.signal}</strong>
          <span className="mono owner">OWNER / {step.owner}</span>
        </div>
      </div>
      <div className="system-footer">
        <p>One continuous story. From the first commit to verified recovery.</p>
        <TextLink href="/architecture">View architecture</TextLink>
      </div>
    </section>
  );
}
