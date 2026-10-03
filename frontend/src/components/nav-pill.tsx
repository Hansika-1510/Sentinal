"use client";

import { useEffect, useState } from "react";
import { usePathname } from "next/navigation";

export type NavLink = { label: string; href: string };

/** `"/#platform"` → `"platform"`; `"/docs"` → `null`. */
function anchorOf(href: string): string | null {
  const hash = href.indexOf("#");
  return hash === -1 ? null : href.slice(hash + 1);
}

/**
 * Which nav item the reader is currently inside.
 *
 * Only the in-page anchors are observable, and the routes differ in which of
 * them they actually contain: `/` has all four, `/docs` has `#agents` and
 * `#security` of its own. So the label has two sources and they have to be
 * ranked, not chosen between at setup time.
 *
 * The page's own label — the link whose href is the current pathname, `/docs`
 * for the Docs link — is the floor. It is what the pill shows before any
 * tracked section has reached the band, and what it returns to if the reader
 * scrolls back above the first one. A section that is actually in the band
 * outranks it. The first link is the last resort on `/`, where no href is a
 * pathname.
 *
 * Ranking matters on `/docs` specifically: it has two real anchor targets, so a
 * fallback that only ran when *no* target existed would never run there, and the
 * pill would sit on the first link until the reader happened to scroll into
 * `#agents`.
 *
 * `links` must be a stable reference — the caller keeps it at module scope, so
 * the observer is built once. An inline array literal would tear it down and
 * rebuild it on every render.
 */
export function useActiveSection(links: NavLink[]): string {
  const pathname = usePathname();
  const own = links.find((link) => link.href === pathname)?.href;
  const fallback = own ?? links[0].href;
  const [active, setActive] = useState(fallback);

  useEffect(() => {
    const anchors = links
      .map((link) => ({ link, id: anchorOf(link.href) }))
      .filter((entry): entry is { link: NavLink; id: string } => entry.id !== null);

    const targets = anchors
      .map(({ id }) => document.getElementById(id))
      .filter((element): element is HTMLElement => element !== null);

    if (targets.length === 0) {
      setActive(fallback);
      return;
    }

    // The band sits just under the header. Of every section crossing it, the
    // topmost wins — measured by position rather than by `intersectionRatio`,
    // because a ratio is relative to each section's own height and would let a
    // short section outrank the tall one the reader is actually inside.
    const seen = new Map<string, { top: number; hit: boolean }>();
    const observer = new IntersectionObserver(
      (entries) => {
        for (const entry of entries) {
          seen.set(entry.target.id, {
            top: entry.boundingClientRect.top,
            hit: entry.isIntersecting,
          });
        }
        let best: { id: string; top: number } | null = null;
        for (const [id, state] of seen) {
          if (!state.hit) continue;
          if (!best || state.top < best.top) best = { id, top: state.top };
        }
        if (!best) {
          // Nothing is in the band, and that has two very different meanings.
          // If the topmost tracked section is still below it, the reader has not
          // reached any of them yet and the page's own label is the honest one.
          // If they have scrolled past the lot, the last one still describes
          // where they are, so it stands.
          const topmost = Math.min(...targets.map((t) => t.getBoundingClientRect().top));
          if (topmost > window.innerHeight * 0.35) setActive(fallback);
          return;
        }
        const match = anchors.find((entry) => entry.id === best?.id);
        if (match) setActive(match.link.href);
      },
      { rootMargin: "-15% 0px -65% 0px", threshold: 0 },
    );

    for (const target of targets) observer.observe(target);
    return () => observer.disconnect();
  }, [links, fallback]);

  return active;
}

/**
 * The 3D navigation pill.
 *
 * Everything inside `.nav-pill-gloss` is a stacked highlight meant to read as
 * one machined bar — an edge ridge, a hemisphere catch, a directional wash, a
 * specular blob, a bottom curvature and a contact shadow. All of it is
 * `pointer-events: none` and carries no accessible content; the links are the
 * only interactive things and they paint above every layer.
 *
 * The collapse is done in CSS, not React — `.nav-pill` opens on `:hover` and
 * `:focus-within`, and that second selector is load-bearing. Collapsed, only
 * the active label is drawn; without `:focus-within` the other four would be
 * drawn at zero width, still focusable but invisible, and a keyboard user would
 * be tabbing into a pill they cannot see open. React's only job here is
 * `data-active`.
 */
export function NavPill({ links }: { links: NavLink[] }) {
  const active = useActiveSection(links);

  return (
    <nav className="nav-pill" aria-label="Main navigation">
      <span className="nav-pill-gloss" aria-hidden="true">
        <i className="gloss-ridge" />
        <i className="gloss-hemi" />
        <i className="gloss-dir" />
        <i className="gloss-blob" />
        <i className="gloss-curve" />
        <i className="gloss-contact" />
      </span>
      {links.map((link) => {
        const isActive = link.href === active;
        return (
          <a
            key={link.label}
            href={link.href}
            data-active={isActive ? "true" : undefined}
            aria-current={isActive ? "location" : undefined}
          >
            {link.label}
          </a>
        );
      })}
    </nav>
  );
}
