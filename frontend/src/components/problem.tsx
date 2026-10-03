"use client";

import { useEffect, useRef } from "react";
import { useReducedMotion } from "@/lib/use-reduced-motion";
import { gsap } from "gsap";
import { ScrollTrigger } from "gsap/ScrollTrigger";
import { CodeIcon, GitCommitIcon, StackIcon, WarningCircleIcon } from "@phosphor-icons/react";
import { SplitHeading } from "./split-heading";

const fragments = [
  {
    icon: WarningCircleIcon,
    label: "THE ALERT",
    title: "500s. Everywhere.",
    meta: "payment-service / HIGH",
  },
  {
    icon: StackIcon,
    label: "THE DEPLOYMENT",
    title: "Something just shipped.",
    meta: "v1.8.3 / production",
  },
  {
    icon: GitCommitIcon,
    label: "THE COMMIT",
    title: "One small refactor.",
    meta: "8f03c2a / 3 files changed",
  },
  {
    icon: CodeIcon,
    label: "THE LINE",
    title: "A connection left open.",
    meta: "PaymentService.java:42",
  },
];

export function ProblemStory() {
  const ref = useRef<HTMLElement>(null);
  const reduced = useReducedMotion();
  useEffect(() => {
    if (reduced) return;
    gsap.registerPlugin(ScrollTrigger);
    const context = gsap.context(() => {
      gsap.from(".problem-phrases span", {
        opacity: 0,
        x: 20,
        stagger: 0.22,
        scrollTrigger: {
          trigger: ".problem-phrases",
          start: "top 78%",
          end: "bottom 48%",
          scrub: 1,
        },
      });
      const media = gsap.matchMedia();
      media.add("(min-width: 768px)", () => {
        gsap.from(".problem-piece", {
          y: (index) => [-45, 55, -40, 35][index],
          x: (index) => [25, -15, 20, -25][index],
          rotation: (index) => [-7, 5, -5, 6][index],
          stagger: 0.07,
          ease: "power2.out",
          scrollTrigger: {
            trigger: ".problem-pieces",
            start: "top 85%",
            end: "bottom 62%",
            scrub: 1,
          },
        });
        gsap.from(".pieces-line", {
          scaleX: 0,
          transformOrigin: "left",
          scrollTrigger: {
            trigger: ".problem-pieces",
            start: "top 65%",
            end: "bottom 40%",
            scrub: 1,
          },
        });
      });
    }, ref);
    return () => context.revert();
  }, [reduced]);
  return (
    <section ref={ref} id="how-it-works" className="problem section page-padding">
      <div className="problem-intro">
        <SplitHeading
          className="statement"
          lines={["An incident is never", { text: "just an incident.", className: "is-dim" }]}
        />
        <div className="problem-phrases">
          <span>A spike in errors.</span>
          <span>A deployment.</span>
          <span>A changed file.</span>
          <span>A dependency.</span>
          <span>A hidden regression.</span>
          <span>A developer connecting the dots.</span>
        </div>
      </div>
      <div className="problem-pieces">
        <div className="pieces-line" aria-hidden="true" />
        {fragments.map(({ icon: Icon, label, title, meta }) => (
          <div className="problem-piece" key={label}>
            <div className="piece-label mono">
              <Icon size={18} />
              {label}
            </div>
            <strong>{title}</strong>
            <span className="mono">{meta}</span>
            <i className="piece-port" aria-hidden="true" />
          </div>
        ))}
      </div>
      <p className="problem-outro" data-reveal>
        The dots already exist.
        <br />
        <span>They’re just scattered.</span>
      </p>
    </section>
  );
}
