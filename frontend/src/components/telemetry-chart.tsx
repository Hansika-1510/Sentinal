"use client";

import { useId, useMemo } from "react";
import { motion } from "motion/react";
import { useReducedMotion } from "@/lib/use-reduced-motion";

export function TelemetryChart({
  level = 4,
  recovered = false,
  compact = false,
  label = "Payment API error rate",
  deploymentLabel,
}: {
  level?: number;
  recovered?: boolean;
  compact?: boolean;
  label?: string;
  deploymentLabel?: string;
}) {
  const rawId = useId();
  const id = rawId.replace(/:/g, "");
  const reduced = useReducedMotion();
  const values = useMemo(
    () =>
      Array.from({ length: 61 }, (_, i) => {
        const noise = Math.sin(i * 2.7) * 0.3 + Math.sin(i * 0.9) * 0.25;
        if (recovered)
          return i < 26
            ? 4.8 + Math.sin(i * 1.5) * 0.9
            : Math.max(0.22, 5.8 * Math.exp(-(i - 25) / 3.6) + noise * 0.15);
        if (i < 28 || level === 0) return 0.24 + Math.abs(noise) * 0.35;
        const growth = Math.min(1, (i - 28) / 11);
        return 0.3 + growth * Math.max(0.3, level * 1.42) + Math.abs(noise) * level * 0.6;
      }),
    [level, recovered],
  );
  const width = 900;
  const height = compact ? 130 : 225;
  const points = values.map(
    (value, i) => `${(i * width) / 60},${Math.round((height - 12 - (value / 9) * (height - 32)) * 100) / 100}`,
  );
  const path = `M${points.join(" L")}`;
  const area = `${path} L${width},${height} L0,${height} Z`;
  // Tokens, not literals: this chart is the one graphic that lands on both
  // planes — `#runtime` on the slate ground, `#recovery` and the console on
  // beige panels — and no single literal is legible on both. Every mark here is
  // a state colour, so it reads `var(...)` and the plane the chart happens to
  // be in resolves it.
  const color = recovered ? "var(--green)" : level > 0 ? "var(--accent-text)" : "var(--muted)";
  return (
    <div className={`telemetry-chart ${compact ? "chart-compact" : ""}`}>
      <svg
        viewBox={`0 0 ${width} ${height + 30}`}
        preserveAspectRatio="none"
        role="img"
        aria-label={`${label}: ${recovered ? "errors return to 0.2 percent after the reviewed deployment" : level > 0 ? "errors rise after deployment v1.8.3" : "healthy baseline"}`}
      >
        <defs>
          <linearGradient id={`fill-${id}`} x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor={color} stopOpacity="0.18" />
            <stop offset="100%" stopColor={color} stopOpacity="0" />
          </linearGradient>
        </defs>
        {[0.2, 0.5, 0.8].map((line) => (
          <line
            key={line}
            x1="0"
            y1={height * line}
            x2={width}
            y2={height * line}
            stroke="currentColor"
            strokeOpacity="0.09"
            strokeDasharray="3 6"
          />
        ))}
        <line
          x1={width * (recovered ? 0.43 : 0.46)}
          y1="6"
          x2={width * (recovered ? 0.43 : 0.46)}
          y2={height}
          stroke={recovered ? "var(--green)" : "var(--muted)"}
          strokeOpacity="0.4"
          strokeDasharray="4 4"
        />
        <motion.path
          d={area}
          animate={{ d: area }}
          transition={{ duration: reduced ? 0 : 0.8 }}
          fill={`url(#fill-${id})`}
        />
        <motion.path
          d={path}
          animate={{ d: path }}
          transition={{ duration: reduced ? 0 : 0.8 }}
          stroke={color}
          strokeWidth="2.4"
          fill="none"
          vectorEffect="non-scaling-stroke"
          strokeLinejoin="round"
        />
        <text
          x={width * (recovered ? 0.43 : 0.46) + 12}
          y="20"
          fill="var(--mid)"
          fontSize="11"
          fontFamily="monospace"
        >
          {deploymentLabel || (recovered ? "v1.8.4 deployed" : "v1.8.3 deployed")}
        </text>
        {["10:40", "10:41", "10:42", "10:43", "10:44"].map((time, i) => (
          <text
            key={time}
            x={(i * (width - 38)) / 4}
            y={height + 22}
            fill="var(--muted)"
            fontSize="11"
            fontFamily="monospace"
          >
            {time}
          </text>
        ))}
      </svg>
    </div>
  );
}
