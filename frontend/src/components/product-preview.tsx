"use client";

import dynamic from "next/dynamic";
import { useRef } from "react";
import { useInView } from "motion/react";
import { ArrowUpRightIcon } from "@phosphor-icons/react";
import { MagneticLink, SectionHeading } from "./ui";

const Dashboard = dynamic(() => import("./dashboard"), {
  ssr: false,
  loading: () => (
    <div className="dashboard-loader">
      <span className="mono">LOADING CONSOLE PREVIEW…</span>
    </div>
  ),
});

export function ProductPreview() {
  const ref = useRef<HTMLDivElement>(null);
  const near = useInView(ref, { once: true, margin: "600px 0px" });
  return (
    <section id="console-preview" className="preview-section section page-padding">
      <SectionHeading>
        ONE PLACE.
        <br />
        <span className="muted">THE WHOLE PICTURE.</span>
      </SectionHeading>
      <p className="section-copy" data-reveal>
        Every signal, investigation, and decision. Finally in the same room.
      </p>
      <div className="product-preview-stage" ref={ref} data-reveal>
        {near ? (
          <Dashboard />
        ) : (
          <div className="dashboard-loader">
            <span className="mono">INTERACTIVE CONSOLE</span>
          </div>
        )}
      </div>
      <div className="preview-footer">
        <span>Go ahead. Follow the evidence.</span>
        <MagneticLink href="/console" className="text-link">
          Open the full console
          <ArrowUpRightIcon size={18} />
        </MagneticLink>
      </div>
    </section>
  );
}
