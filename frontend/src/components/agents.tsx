"use client";

import { useEffect, useRef, useState } from "react";
import { useReducedMotion } from "@/lib/use-reduced-motion";
import { gsap } from "gsap";
import { ScrollTrigger } from "gsap/ScrollTrigger";
import {
  ArrowRightIcon,
  ArrowUpRightIcon,
  CheckIcon,
  CodeIcon,
  FingerprintIcon,
  GitCommitIcon,
  LockKeyIcon,
  ShieldCheckIcon,
} from "@phosphor-icons/react";
import { agents } from "@/lib/data";
import { Dialog, TiltSurface } from "./ui";

function AgentVisual({ type }: { type: string }) {
  return (
    <div className={`agent-visual agent-visual-${type}`} aria-hidden="true">
      {type === "guard" && (
        <>
          <div className="guard-sheet sheet-back" />
          <div className="guard-sheet sheet-front">
            <span />
            <span />
            <span />
            <span />
            <span />
            <i className="scan-line" />
          </div>
          <div className="guard-seal">
            <ShieldCheckIcon weight="light" size={53} />
          </div>
        </>
      )}
      {type === "signal" && (
        <>
          <div className="signal-wave">
            {Array.from({ length: 31 }, (_, i) => (
              <i
                key={i}
                style={{
                  height: `${Math.round((14 + Math.abs(Math.sin(i * 0.47)) * (i > 14 && i < 23 ? 120 : 46)) * 100) / 100}px`,
                  animationDelay: `${(i * 6) / 100}s`,
                }}
              />
            ))}
          </div>
          <div className="wave-baseline" />
          <span className="visual-caption mono">ANOMALY / +640%</span>
        </>
      )}
      {type === "trace" && (
        <>
          <div className="trace-orbit orbit-one" />
          <div className="trace-orbit orbit-two" />
          <div className="trace-center">
            <FingerprintIcon size={53} weight="light" />
          </div>
          <div className="trace-node trace-one">
            <GitCommitIcon size={17} />
          </div>
          <div className="trace-node trace-two">
            <CodeIcon size={17} />
          </div>
          <div className="trace-node trace-three">
            <span>500</span>
          </div>
          <i className="trace-scan" />
        </>
      )}
      {type === "code" && (
        <>
          <div className="advisor-code-sheet">
            <span className="mono">PaymentService.java</span>
            <div>
              <i>42</i>
              <b />
              <i>43</i>
              <b />
              <i>44</i>
              <b />
              <i>45</i>
              <b />
              <i>46</i>
              <b />
            </div>
            <span className="code-pointer">↳</span>
          </div>
          <span className="visual-caption mono">PRECISE GUIDANCE.</span>
        </>
      )}
      {type === "response" && (
        <>
          <div className="response-gate">
            <div>
              <span className="mono">ACTION REQUEST</span>
              <ArrowRightIcon size={18} />
            </div>
            <div className="response-lock">
              <LockKeyIcon size={34} weight="light" />
            </div>
            <div>
              <span className="mono">HUMAN APPROVAL</span>
              <CheckIcon size={18} />
            </div>
          </div>
          <span className="visual-caption mono">A HUMAN IN THE LOOP.</span>
        </>
      )}
      {type === "memory" && (
        <>
          <div className="memory-sheet sheet-one">
            <span className="mono">#0544</span>
          </div>
          <div className="memory-sheet sheet-two">
            <span className="mono">#0762</span>
          </div>
          <div className="memory-sheet sheet-three">
            <span className="mono">#1042</span>
            <FingerprintIcon size={40} weight="light" />
            <div className="memory-sheet-lines">
              <i />
              <i />
              <i />
            </div>
          </div>
        </>
      )}
    </div>
  );
}

export function AgentSystem() {
  const wrap = useRef<HTMLElement>(null);
  const track = useRef<HTMLDivElement>(null);
  const reduced = useReducedMotion();
  const [selected, setSelected] = useState<number | null>(null);
  useEffect(() => {
    if (reduced) return;
    gsap.registerPlugin(ScrollTrigger);
    const media = gsap.matchMedia();
    media.add("(min-width: 1024px)", () => {
      const distance = () =>
        Math.max(0, track.current!.scrollWidth - track.current!.parentElement!.clientWidth);
      const animation = gsap.to(track.current, {
        x: () => -distance(),
        ease: "none",
        scrollTrigger: {
          id: "sentinel-agents",
          trigger: wrap.current,
          start: "top top",
          end: () => `+=${distance() + 180}`,
          pin: true,
          scrub: 1,
          invalidateOnRefresh: true,
        },
      });
      return () => {
        animation.scrollTrigger?.kill();
        animation.kill();
      };
    });
    return () => media.revert();
  }, [reduced]);
  return (
    <>
      <section ref={wrap} id="agents" className="agents-section page-padding">
        <div className="agents-heading">
          <h2 className="section-title" data-reveal>
            SIX AGENTS.
            <br />
            <span className="muted">ONE SHARED CONTEXT.</span>
          </h2>
          <span className="agents-direction" aria-hidden="true">
            <ArrowRightIcon size={38} weight="light" />
          </span>
        </div>
        <div className="agents-track-viewport">
          <div ref={track} className="agents-track">
            {agents.map((agent, index) => (
              <TiltSurface key={agent.id} className={`agent-card agent-card-${agent.visual}`}>
                <AgentVisual type={agent.visual} />
                <div className="agent-content">
                  <p className="agent-role">{agent.role}</p>
                  <h3>{agent.name}</h3>
                  <p className="agent-description">{agent.description}</p>
                  <button
                    type="button"
                    className="agent-explore"
                    onClick={() => setSelected(index)}
                    aria-label={`Meet the agent: ${agent.name}`}
                  >
                    <span>Meet the agent</span>
                    <ArrowUpRightIcon size={21} />
                  </button>
                </div>
              </TiltSurface>
            ))}
          </div>
        </div>
        <p className="agents-footnote mono">SPECIALIZED INTELLIGENCE. COORDINATED RESPONSE.</p>
      </section>
      <Dialog
        open={selected !== null}
        onClose={() => setSelected(null)}
        title={selected === null ? "Agent" : agents[selected].name}
      >
        <div className="agent-dialog">
          {selected !== null && (
            <>
              <p className="agent-dialog-description">{agents[selected].description}</p>
              <dl>
                <div>
                  <dt>Reads</dt>
                  <dd>{agents[selected].input}</dd>
                </div>
                <div>
                  <dt>Produces</dt>
                  <dd>{agents[selected].output}</dd>
                </div>
                <div>
                  <dt>Human boundary</dt>
                  <dd>{agents[selected].boundary}</dd>
                </div>
              </dl>
              <a href={`/docs#${agents[selected].id}`} className="button button-primary">
                Read the documentation
                <ArrowRightIcon size={17} />
              </a>
            </>
          )}
        </div>
      </Dialog>
    </>
  );
}
