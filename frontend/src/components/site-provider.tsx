"use client";

import { useEffect, useState } from "react";
import { MotionConfig } from "motion/react";
import { IconContext } from "@phosphor-icons/react";
import { usePathname } from "next/navigation";
import Cursor from "./cursor";

function ScrollEngine() {
  const pathname = usePathname();
  const [reduced, setReduced] = useState(true);
  useEffect(() => {
    const media = window.matchMedia("(prefers-reduced-motion: reduce)");
    const update = () => setReduced(media.matches);
    update();
    media.addEventListener("change", update);
    return () => media.removeEventListener("change", update);
  }, []);
  useEffect(() => {
    if (reduced) return;
    let dispose = () => {};
    let cancelled = false;

    async function setup() {
      const [{ default: Lenis }, { gsap }, { ScrollTrigger }] = await Promise.all([
        import("lenis"),
        import("gsap"),
        import("gsap/ScrollTrigger"),
      ]);
      if (cancelled) return;
      gsap.registerPlugin(ScrollTrigger);
      const lenis = new Lenis({
        duration: 1.1,
        smoothWheel: true,
        syncTouch: false,
        anchors: { offset: -96 },
        prevent: (node) => node.hasAttribute("data-lenis-prevent"),
      });
      lenis.on("scroll", ScrollTrigger.update);
      const tick = (time: number) => lenis.raf(time * 1000);
      gsap.ticker.add(tick);
      const onDialog = (event: Event) =>
        (event as CustomEvent<boolean>).detail ? lenis.stop() : lenis.start();
      document.addEventListener("sentinel:dialog", onDialog);

      const context = gsap.context(() => {
        gsap.utils.toArray<HTMLElement>("[data-reveal]").forEach((element) => {
          gsap.from(element, {
            opacity: 0,
            y: 36,
            duration: 0.9,
            ease: "power3.out",
            scrollTrigger: { trigger: element, start: "top 92%", once: true },
          });
        });

        // Editorial curtain reveal: the block is wiped open bottom-up while it
        // lifts into place. Both ends are given explicitly — animating `from`
        // alone would interpolate against the computed `clip-path: none`.
        gsap.utils.toArray<HTMLElement>("[data-wipe]").forEach((element) => {
          gsap.fromTo(
            element,
            { clipPath: "inset(0% 0% 108% 0%)", y: 26 },
            {
              clipPath: "inset(0% 0% -14% 0%)",
              y: 0,
              duration: 1.05,
              ease: "power3.out",
              scrollTrigger: { trigger: element, start: "top 90%", once: true },
            },
          );
        });

        // Per-character reveal, opt-in via <SplitHeading>. Each `.char` sits in
        // its own overflow-hidden mask so the glyphs rise out of a clipped
        // edge; the stagger is what makes the line read as set rather than
        // faded in.
        gsap.utils.toArray<HTMLElement>("[data-split]").forEach((element) => {
          const chars = element.querySelectorAll<HTMLElement>(".char");
          if (!chars.length) return;
          gsap.from(chars, {
            yPercent: 118,
            duration: 0.9,
            ease: "power3.out",
            stagger: { each: 0.016, from: "start" },
            scrollTrigger: { trigger: element, start: "top 88%", once: true },
          });
        });
        gsap.utils.toArray<HTMLElement>("[data-parallax]").forEach((element) => {
          gsap.to(element, {
            y: Number(element.dataset.parallax) || -50,
            ease: "none",
            scrollTrigger: {
              trigger: element.parentElement,
              start: "top bottom",
              end: "bottom top",
              scrub: 1,
            },
          });
        });
      });
      const refresh = () => ScrollTrigger.refresh();
      document.fonts.ready.then(() => {
        if (!cancelled) refresh();
      });
      const timer = window.setTimeout(refresh, 500);
      dispose = () => {
        window.clearTimeout(timer);
        document.removeEventListener("sentinel:dialog", onDialog);
        gsap.ticker.remove(tick);
        context.revert();
        lenis.destroy();
      };
    }
    void setup();
    return () => {
      cancelled = true;
      dispose();
    };
  }, [pathname, reduced]);
  return null;
}

export function SiteProvider({ children }: { children: React.ReactNode }) {
  return (
    <MotionConfig reducedMotion="user">
      <IconContext.Provider value={{ size: 20, weight: "regular" }}>
        <ScrollEngine />
        <Cursor />
        {children}
      </IconContext.Provider>
    </MotionConfig>
  );
}
