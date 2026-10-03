"use client";

import { useEffect, useRef, useState } from "react";
import { useReducedMotion } from "@/lib/use-reduced-motion";
import { gsap } from "gsap";
import { ScrollTrigger } from "gsap/ScrollTrigger";
import {
  ArrowRightIcon,
  ArrowUpRightIcon,
  CheckIcon,
  ShieldCheckIcon,
} from "@phosphor-icons/react";
import { MagneticLink, TextLink } from "./ui";

const loop = [
  { word: "DETECT.", href: "#runtime", detail: "Hear the signal through the noise." },
  { word: "TRACE.", href: "#investigation", detail: "Follow the evidence to its origin." },
  { word: "FIX.", href: "#fix-advisor", detail: "Put the precise guidance in human hands." },
  { word: "VERIFY.", href: "#recovery", detail: "Measure the outcome. Confirm recovery." },
  { word: "LEARN.", href: "#memory", detail: "Turn every incident into the next advantage." },
];

export function FullLoop() {
  const ref = useRef<HTMLElement>(null);
  const [active, setActive] = useState(0);
  const current = useRef(0);
  const reduced = useReducedMotion();
  useEffect(() => {
    if (reduced) return;
    gsap.registerPlugin(ScrollTrigger);
    const trigger = ScrollTrigger.create({
      trigger: ref.current,
      start: "top 40%",
      end: "bottom 75%",
      onUpdate: (self) => {
        const next = Math.min(4, Math.floor(self.progress * 5));
        if (next !== current.current) {
          current.current = next;
          setActive(next);
        }
      },
    });
    return () => trigger.kill();
  }, [reduced]);
  return (
    <section
      ref={ref}
      className="loop-section section page-padding"
      aria-label="The continuous incident intelligence loop"
    >
      <div className="loop-words">
        {loop.map((item, index) => (
          <a
            href={item.href}
            key={item.word}
            className={`loop-word ${index <= active ? "is-past" : ""} ${index === active ? "active" : ""}`}
            onMouseEnter={() => setActive(index)}
          >
            <span>{item.word}</span>
            {index === active && <ArrowUpRightIcon weight="light" aria-hidden="true" />}
          </a>
        ))}
      </div>
      <div className="loop-aside">
        <div className="loop-orbit" aria-hidden="true">
          <div className="orbit-ring" />
          <span className="loop-orbit-label mono">
            CONTINUOUS
            <br />
            INTELLIGENCE
          </span>
          {loop.map((item, index) => (
            <span
              key={item.word}
              className={`loop-orbit-node ${index === active ? "active" : ""}`}
              style={{
                transform: `rotate(${index * 72 - 90}deg) translateX(135px) rotate(${90 - index * 72}deg)`,
              }}
            >
              {index < active ? <CheckIcon size={12} /> : index + 1}
            </span>
          ))}
          <span className="loop-return">↻</span>
        </div>
        <p className="loop-description">{loop[active].detail}</p>
        <span className="mono">EVERY INCIDENT MAKES THE SYSTEM SMARTER.</span>
      </div>
    </section>
  );
}

const controls = [
  {
    title: "Human authority",
    items: [
      "Explicit approval for sensitive actions",
      "No autonomous source-code modification",
      "Every decision is auditable",
    ],
  },
  {
    title: "Defense in depth",
    items: [
      "Least-privilege access",
      "Secret redaction",
      "Evidence-backed recommendations",
      "Deterministic security checks",
    ],
  },
];

export function Security() {
  return (
    <section id="security" className="security-section section page-padding">
      <div className="security-title">
        <ShieldCheckIcon size={32} weight="light" />
        <h2 className="section-title" data-reveal>
          BUILT FOR SYSTEMS
          <br />
          YOU CAN’T AFFORD
          <br />
          <span className="muted">TO GUESS ABOUT.</span>
        </h2>
      </div>
      <div className="security-controls" data-reveal>
        {controls.map((group) => (
          <div className="security-group" key={group.title}>
            <h3 className="mono">{group.title.toUpperCase()}</h3>
            <ul>
              {group.items.map((item) => (
                <li key={item}>
                  <CheckIcon size={15} />
                  <span>{item}</span>
                </li>
              ))}
            </ul>
          </div>
        ))}
      </div>
      <TextLink href="/docs#security">Explore the security model</TextLink>
    </section>
  );
}

export function FinalCTA() {
  const ref = useRef<HTMLElement>(null);
  const reduced = useReducedMotion();
  useEffect(() => {
    if (reduced) return;
    gsap.registerPlugin(ScrollTrigger);
    const context = gsap.context(() => {
      gsap.to(".closing-ring", {
        scale: 0.03,
        opacity: 0,
        stagger: 0.12,
        ease: "power2.inOut",
        scrollTrigger: { trigger: ref.current, start: "top 75%", end: "bottom 92%", scrub: 1 },
      });
    }, ref);
    return () => context.revert();
  }, [reduced]);
  return (
    <section ref={ref} className="final-cta section page-padding">
      <div className="closing-signal" aria-hidden="true">
        {[0, 1, 2, 3].map((index) => (
          <span className="closing-ring" key={index} style={{ inset: `${index * 25}px` }} />
        ))}
        <span className="closing-core" />
      </div>
      <h2 data-reveal>
        WHEN PRODUCTION
        <br />
        BREAKS, <span>KNOW WHY.</span>
      </h2>
      <div className="final-actions">
        <MagneticLink href="/console" className="button button-primary" arrow>
          Explore Sentinel
        </MagneticLink>
        <MagneticLink href="/architecture" className="text-link">
          View architecture
          <ArrowRightIcon className="button-arrow" size={18} />
        </MagneticLink>
      </div>
      <p>
        From incident to root cause.
        <br />
        And all the way back to healthy.
      </p>
    </section>
  );
}
