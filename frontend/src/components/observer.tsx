"use client";

import { useState, type CSSProperties } from "react";
import {
  BellRingingIcon,
  CodeBlockIcon,
  CubeIcon,
  GraphIcon,
  PulseIcon,
  StackIcon,
} from "@phosphor-icons/react";
import { BrandMark } from "./ui";

const inputs = [
  {
    label: "Logs",
    icon: CodeBlockIcon,
    x: 13,
    y: 25,
    detail: "Connection timeouts share the same stack frame.",
    reading: "1,842 events / sec",
  },
  {
    label: "Errors",
    icon: BellRingingIcon,
    x: 76,
    y: 18,
    detail: "Payment API failures depart from their normal baseline.",
    reading: "500 rate +640%",
  },
  {
    label: "Metrics",
    icon: PulseIcon,
    x: 87,
    y: 56,
    detail: "Latency and connection usage move together.",
    reading: "p95 latency 830ms",
  },
  {
    label: "Deployments",
    icon: CubeIcon,
    x: 21,
    y: 74,
    detail: "The anomaly appears 42 seconds after the latest release.",
    reading: "payment-service v1.8.3",
  },
  {
    label: "Alerts",
    icon: StackIcon,
    x: 55,
    y: 87,
    detail: "Related symptoms become one incident, with one investigation.",
    reading: "3 alerts → 1 incident",
  },
  {
    label: "Dependencies",
    icon: GraphIcon,
    x: 11,
    y: 51,
    detail: "The blast radius connects payment, checkout, and database.",
    reading: "3 affected services",
  },
];

export function Observer() {
  const [active, setActive] = useState(1);
  return (
    <section className="observer-section section page-padding" aria-labelledby="observer-heading">
      <div className="observer-heading">
        <h2 id="observer-heading" className="section-title" data-reveal>
          MEET SENTINEL.
        </h2>
        <p data-reveal>Your runtime is always telling you something.</p>
      </div>
      <div className="observer-stage" data-reveal>
        <svg
          viewBox="0 0 1200 560"
          preserveAspectRatio="none"
          className="observer-connections"
          fill="none"
          aria-hidden="true"
        >
          <ellipse cx="600" cy="285" rx="250" ry="210" />
          <ellipse cx="600" cy="285" rx="390" ry="255" />
          {inputs.map((input, i) => (
            <g key={input.label}>
              <path
                d={`M${input.x * 12} ${input.y * 5.6} Q600 ${input.y * 5.6} 600 280`}
                className="observer-wire"
              />
              <path
                d={`M${input.x * 12} ${input.y * 5.6} Q600 ${input.y * 5.6} 600 280`}
                className={`observer-flow ${i === active ? "is-active" : ""}`}
                style={{ animationDelay: `${i * -0.7}s` }}
              />
            </g>
          ))}
        </svg>
        <div className="observer-core">
          <div className="core-ring" />
          <BrandMark />
          <span className="mono">SENTINEL</span>
        </div>
        {inputs.map(({ label, icon: Icon, x, y }, index) => (
          <button
            type="button"
            key={label}
            className={`observer-input ${active === index ? "active" : ""}`}
            aria-pressed={active === index}
            onClick={() => setActive(index)}
            style={{ "--x": `${x}%`, "--y": `${y}%` } as CSSProperties}
          >
            <Icon size={19} />
            <span>{label}</span>
          </button>
        ))}
        <div className="observer-insight">
          <div className="mono text-incident">ANOMALY DETECTED</div>
          <strong>{inputs[active].reading}</strong>
          <p>{inputs[active].detail}</p>
          <div className="observer-confidence">
            <span className="mono">CONFIDENCE</span>
            <b>
              96<small>%</small>
            </b>
          </div>
        </div>
      </div>
    </section>
  );
}
