"use client";

import { useState } from "react";
import { ArrowUpRightIcon, ListIcon } from "@phosphor-icons/react";
import { Brand, Dialog } from "./ui";
import { NavPill, type NavLink } from "./nav-pill";

// Module scope, so `useActiveSection` sees a stable reference and builds its
// IntersectionObserver once rather than on every render.
const links: NavLink[] = [
  { label: "Platform", href: "/#platform" },
  { label: "How it works", href: "/#how-it-works" },
  { label: "Agents", href: "/#agents" },
  { label: "Security", href: "/#security" },
  { label: "Docs", href: "/docs" },
];

export function Navigation() {
  const [open, setOpen] = useState(false);
  return (
    <>
      <a href="#main" className="skip-link">
        Skip to content
      </a>
      {/* Two plates on the slate: the brand at the left, the pill centred. The
          header itself still paints nothing, so it stays legible over the slate
          ground and over the beige panels it scrolls across without depending on
          a translucent backdrop-filter. */}
      <header className="site-nav">
        <Brand />
        <NavPill links={links} />
        <button
          type="button"
          className="icon-button menu-toggle"
          aria-label="Open navigation"
          aria-expanded={open}
          onClick={() => setOpen(true)}
        >
          <ListIcon size={24} />
        </button>
      </header>
      <Dialog
        title="Explore Sentinel"
        open={open}
        onClose={() => setOpen(false)}
        className="mobile-menu"
      >
        <nav aria-label="Mobile navigation">
          {links.map((link) => (
            <a key={link.label} href={link.href} onClick={() => setOpen(false)}>
              {link.label}
              <ArrowUpRightIcon />
            </a>
          ))}
          <a href="/console" onClick={() => setOpen(false)}>
            Open Console
            <ArrowUpRightIcon />
          </a>
        </nav>
      </Dialog>
    </>
  );
}
