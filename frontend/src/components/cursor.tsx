"use client";

import { useEffect, useRef } from "react";

const DOT_SIZE = 6;
const RING_SIZE = 38;
/** How much of the remaining distance the ring closes each frame. */
const RING_EASE = 0.16;
/** Grown state for the ring over anything interactive. */
const HOVER_SCALE = 1.7;

/** Anything that reads as a target gets the enlarged ring. */
const INTERACTIVE = "a, button, [data-cursor], input, select, textarea, summary, label";

/**
 * Trailing cursor, mounted once from SiteProvider.
 *
 * Deliberately conservative:
 *
 * - Only armed for a fine pointer with motion allowed, and re-armed if a mouse
 *   is plugged in — the media queries are listened to, not sampled once.
 * - The native cursor is hidden only while this component is actually live, by
 *   putting `has-cursor` on `<html>`. If the effect never runs, or the pointer
 *   turns out to be coarse, the real cursor is untouched.
 * - The overlay is `pointer-events: none` and `aria-hidden`, so it never takes a
 *   click, a focus stop, or an accessible name away from anything.
 * - It moves by writing `transform` straight onto two refs. No React state, so
 *   the pointer never triggers a render.
 */
export default function Cursor() {
  const root = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const node = root.current;
    if (!node) return;
    const dot = node.querySelector<HTMLElement>(".cursor-dot");
    const ring = node.querySelector<HTMLElement>(".cursor-ring");
    if (!dot || !ring) return;

    const fine = window.matchMedia("(pointer: fine)");
    const reduce = window.matchMedia("(prefers-reduced-motion: reduce)");

    let frame = 0;
    let live = false;
    let x = 0;
    let y = 0;
    let ringX = 0;
    let ringY = 0;
    let scale = 1;
    let targetScale = 1;
    let hovering = false;

    const render = () => {
      ringX += (x - ringX) * RING_EASE;
      ringY += (y - ringY) * RING_EASE;
      scale += (targetScale - scale) * 0.18;
      dot.style.transform = `translate3d(${x - DOT_SIZE / 2}px, ${y - DOT_SIZE / 2}px, 0) scale(${
        hovering ? 0 : 1
      })`;
      ring.style.transform = `translate3d(${ringX - RING_SIZE / 2}px, ${
        ringY - RING_SIZE / 2
      }px, 0) scale(${scale})`;

      // Park the loop once the ring has caught up, and let the next pointermove
      // wake it. This keeps an idle page from animating forever.
      const settled =
        Math.abs(x - ringX) < 0.1 &&
        Math.abs(y - ringY) < 0.1 &&
        Math.abs(targetScale - scale) < 0.002;
      frame = settled ? 0 : requestAnimationFrame(render);
    };

    const move = (event: PointerEvent) => {
      if (event.pointerType !== "mouse") return;
      x = event.clientX;
      y = event.clientY;
      if (!live) {
        live = true;
        ringX = x;
        ringY = y;
        node.classList.add("is-active");
        document.documentElement.classList.add("has-cursor");
      }
      const target = event.target as Element | null;
      const interactive = Boolean(target?.closest?.(INTERACTIVE));
      if (interactive !== hovering) {
        hovering = interactive;
        targetScale = interactive ? HOVER_SCALE : 1;
        node.classList.toggle("is-hovering", interactive);
      }
      if (!frame) frame = requestAnimationFrame(render);
    };

    const hide = () => {
      if (!live) return;
      live = false;
      hovering = false;
      node.classList.remove("is-active", "is-hovering");
      document.documentElement.classList.remove("has-cursor");
    };

    const teardown = () => {
      cancelAnimationFrame(frame);
      frame = 0;
      hide();
      window.removeEventListener("pointermove", move);
      document.documentElement.removeEventListener("pointerleave", hide);
      window.removeEventListener("blur", hide);
    };

    const arm = () => {
      teardown();
      if (!fine.matches || reduce.matches) return;
      window.addEventListener("pointermove", move, { passive: true });
      document.documentElement.addEventListener("pointerleave", hide);
      window.addEventListener("blur", hide);
    };

    arm();
    fine.addEventListener("change", arm);
    reduce.addEventListener("change", arm);
    return () => {
      fine.removeEventListener("change", arm);
      reduce.removeEventListener("change", arm);
      teardown();
    };
  }, []);

  return (
    <div className="cursor" aria-hidden="true" ref={root}>
      <i className="cursor-ring" />
      <i className="cursor-dot" />
    </div>
  );
}
