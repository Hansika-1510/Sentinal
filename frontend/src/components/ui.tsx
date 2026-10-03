"use client";

import { useEffect, useId, useRef, useState, type ReactNode, type PointerEvent } from "react";
import { createPortal } from "react-dom";
import { motion, useMotionValue, useSpring } from "motion/react";
import { useReducedMotion } from "@/lib/use-reduced-motion";
import {
  ArrowRightIcon,
  ArrowUpRightIcon,
  CheckIcon,
  CopyIcon,
  XIcon,
} from "@phosphor-icons/react";

export function BrandMark({ className = "" }: { className?: string }) {
  return (
    <span className={`brand-mark ${className}`} aria-hidden="true">
      <i />
      <i />
      <i />
    </span>
  );
}

export function Brand({ href = "/" }: { href?: string }) {
  return (
    <a className="brand" href={href} aria-label="Sentinel home">
      <BrandMark />
      <span>SENTINEL</span>
    </a>
  );
}

export function MagneticLink({
  children,
  href,
  className = "",
  arrow = false,
  external = false,
  underline = false,
  onClick,
}: {
  children: ReactNode;
  href: string;
  className?: string;
  arrow?: boolean;
  external?: boolean;
  /** Give the label the sweeping underline. See `.link-line` in globals.css. */
  underline?: boolean;
  onClick?: () => void;
}) {
  const reduced = useReducedMotion();
  const rect = useRef<DOMRect | null>(null);
  const x = useMotionValue(0);
  const y = useMotionValue(0);
  const springX = useSpring(x, { stiffness: 240, damping: 24 });
  const springY = useSpring(y, { stiffness: 240, damping: 24 });
  const move = (event: PointerEvent<HTMLAnchorElement>) => {
    if (reduced || event.pointerType !== "mouse" || !rect.current) return;
    x.set((event.clientX - rect.current.left - rect.current.width / 2) * 0.075);
    y.set((event.clientY - rect.current.top - rect.current.height / 2) * 0.13);
  };
  return (
    <motion.a
      href={href}
      className={className}
      style={{ x: springX, y: springY }}
      onPointerEnter={(event) => {
        rect.current = event.currentTarget.getBoundingClientRect();
      }}
      onPointerMove={move}
      onPointerLeave={() => {
        x.set(0);
        y.set(0);
      }}
      onClick={onClick}
      {...(external ? { target: "_blank", rel: "noopener noreferrer" } : {})}
    >
      {underline ? (
        // Two stacked hairlines, not one. The visible line leaves to the right
        // while an identical one arrives from the left; each keeps a fixed
        // transform-origin, which a single element swapping its origin cannot
        // do without the origin itself interpolating mid-transition.
        <span className="link-label">
          <span className="link-text">{children}</span>
          <span className="link-line link-line--current" aria-hidden="true" />
          <span className="link-line link-line--next" aria-hidden="true" />
        </span>
      ) : (
        children
      )}
      {arrow && <ArrowRightIcon className="button-arrow" aria-hidden="true" />}
    </motion.a>
  );
}

export function TextLink({
  href,
  children,
  className = "",
}: {
  href: string;
  children: ReactNode;
  className?: string;
}) {
  return (
    <MagneticLink href={href} className={`text-link ${className}`} arrow underline>
      {children}
    </MagneticLink>
  );
}

export function TiltSurface({
  children,
  className = "",
}: {
  children: ReactNode;
  className?: string;
}) {
  const reduce = useReducedMotion();
  const rect = useRef<DOMRect | null>(null);
  const x = useMotionValue(0);
  const y = useMotionValue(0);
  const z = useMotionValue(0);
  const rx = useSpring(x, { stiffness: 180, damping: 24 });
  const ry = useSpring(y, { stiffness: 180, damping: 24 });
  const tz = useSpring(z, { stiffness: 210, damping: 26 });
  return (
    <motion.div
      className={className}
      style={{ rotateX: rx, rotateY: ry, z: tz, transformPerspective: 1450 }}
      onPointerEnter={(event) => {
        rect.current = event.currentTarget.getBoundingClientRect();
        if (reduce || event.pointerType !== "mouse") return;
        z.set(34);
      }}
      onPointerMove={(event) => {
        if (reduce || event.pointerType !== "mouse" || !rect.current) return;
        x.set(
          (-(event.clientY - rect.current.top - rect.current.height / 2) / rect.current.height) * 6.5,
        );
        y.set(
          ((event.clientX - rect.current.left - rect.current.width / 2) / rect.current.width) * 6.5,
        );
      }}
      onPointerLeave={() => {
        x.set(0);
        y.set(0);
        z.set(0);
      }}
    >
      {children}
    </motion.div>
  );
}

export function Dialog({
  open,
  onClose,
  title,
  children,
  className = "",
}: {
  open: boolean;
  onClose: () => void;
  title: string;
  children: ReactNode;
  className?: string;
}) {
  const ref = useRef<HTMLDialogElement>(null);
  const titleId = useId();
  const [mounted, setMounted] = useState(false);
  useEffect(() => {
    setMounted(true);
  }, []);
  useEffect(() => {
    const dialog = ref.current;
    if (!dialog || !mounted || !open) return;
    const previous = document.activeElement as HTMLElement | null;
    const overflow = document.documentElement.style.overflow;
    dialog.showModal();
    document.documentElement.style.overflow = "hidden";
    document.dispatchEvent(new CustomEvent("sentinel:dialog", { detail: true }));
    return () => {
      dialog.close();
      document.documentElement.style.overflow = overflow;
      document.dispatchEvent(new CustomEvent("sentinel:dialog", { detail: false }));
      previous?.focus({ preventScroll: true });
    };
  }, [open, mounted]);
  if (!mounted) return null;
  return createPortal(
    <dialog
      ref={ref}
      className={`dialog ${className}`}
      aria-labelledby={titleId}
      onCancel={onClose}
      onClick={(event) => {
        if (event.target === event.currentTarget) onClose();
      }}
      data-lenis-prevent
    >
      <div className="dialog-content">
        <div className="dialog-heading">
          <h2 id={titleId}>{title}</h2>
          <button type="button" className="icon-button" aria-label="Close dialog" onClick={onClose}>
            <XIcon />
          </button>
        </div>
        {children}
      </div>
    </dialog>,
    document.body,
  );
}

export function CopyButton({ value, label = "Copy guidance" }: { value: string; label?: string }) {
  const [state, setState] = useState<"idle" | "copied" | "error">("idle");
  const timer = useRef<ReturnType<typeof setTimeout> | null>(null);
  useEffect(
    () => () => {
      if (timer.current) clearTimeout(timer.current);
    },
    [],
  );
  return (
    <button
      type="button"
      className="copy-button"
      onClick={async () => {
        try {
          await navigator.clipboard.writeText(value);
          setState("copied");
        } catch {
          setState("error");
        }
        if (timer.current) clearTimeout(timer.current);
        timer.current = setTimeout(() => setState("idle"), 2400);
      }}
      aria-live="polite"
    >
      {state === "copied" ? <CheckIcon size={16} /> : <CopyIcon size={16} />}
      {state === "copied" ? "Copied" : state === "error" ? "Copy unavailable" : label}
    </button>
  );
}

export function SectionHeading({
  children,
  className = "",
  id,
}: {
  children: ReactNode;
  className?: string;
  id?: string;
}) {
  return (
    <h2 id={id} className={`section-title ${className}`} data-wipe>
      {children}
    </h2>
  );
}

export function DemoLabel({ children = "ILLUSTRATIVE INCIDENT" }: { children?: ReactNode }) {
  return <span className="demo-label">{children}</span>;
}

export function ArrowBadge() {
  return (
    <span className="arrow-badge" aria-hidden="true">
      <ArrowUpRightIcon />
    </span>
  );
}
