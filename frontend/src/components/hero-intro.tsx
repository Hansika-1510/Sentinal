"use client";

import { useEffect, useState } from "react";
import { BrandMark } from "./ui";

/** Matches the `intro-wipe` animation in globals.css. */
const INTRO_MS = 1000;
const GATE = "(min-width: 768px) and (prefers-reduced-motion: no-preference)";

/**
 * The opening frame: an opaque cover that draws a rule and then wipes upward off
 * the hero.
 *
 * Engineered to be disposable rather than impressive:
 *
 * - It renders on the server, so it paints with the first frame instead of
 *   appearing after hydration — a loader that shows up late is worse than none.
 * - All motion is CSS, so it completes even if this component never hydrates.
 *   The animation ends fully clipped, and the cover is `pointer-events: none`
 *   throughout, so a page whose script failed is still completely usable.
 * - The effect only decides when to unmount. Under reduced motion, or on a
 *   narrow screen, it unmounts on the first tick and the CSS keeps it hidden
 *   either way.
 * - No timers chain, no network, no font wait: the whole thing is a fixed
 *   1s, and the cover is gone from the DOM at the end of it.
 */
export default function HeroIntro() {
  const [done, setDone] = useState(false);

  useEffect(() => {
    if (!window.matchMedia(GATE).matches) {
      setDone(true);
      return;
    }
    const timer = window.setTimeout(() => setDone(true), INTRO_MS);
    return () => window.clearTimeout(timer);
  }, []);

  if (done) return null;

  return (
    <div className="intro" aria-hidden="true">
      <div className="intro-mark">
        <BrandMark />
        <span className="intro-word">SENTINEL</span>
      </div>
      <div className="intro-rule">
        <i />
      </div>
      <span className="intro-status mono">INITIALISING RUNTIME TRACE</span>
    </div>
  );
}
