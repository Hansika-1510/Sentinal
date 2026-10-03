#!/usr/bin/env python3
"""
Re-key the Sentinel stylesheets onto the slate ground.

Two jobs, both driven by names and literals rather than by character offsets
into a comment-stripped copy of the file:

  1. swap the ground-plane text literals the browser proved are sitting on slate
     for the ladder token that now belongs there;
  2. fix the handful of rules whose hover/plane arithmetic broke when the ground
     and the panels stopped sharing one ink set.

Comments are blanked rather than removed (`' ' * len`), so every offset stays
valid against the file actually on disk. An earlier pass removed them instead
and wrote its edits into the wrong bytes; that is the whole reason this file
exists rather than a shell one-liner.
"""
import re
from pathlib import Path

APP = Path("src/app")

# (file, selector, literal sitting on the slate ground, token it should be)
#
# This migration has been applied. Re-running it is expected to fail on every
# entry, because each literal it looks for has already been replaced by the
# token — it is kept as the record of what moved and why, not as a runnable
# plan. The header's `.desktop-nav a` entry was retired when the header was
# replaced by the navigation pill; `.desktop-nav` no longer exists.
FLIPS = [
    ("globals.css", ".hero-eyebrow", "#2a1e12", "var(--muted)"),
    ("globals.css", ".lens-orbit-label", "#18283a", "var(--mid)"),
    ("globals.css", ".lens-coordinate", "#1a2b3e", "var(--mid)"),
    ("globals.css", ".hero-description p", "#2c1f13", "var(--muted)"),
    ("globals.css", ".footer-top nav a", "#23180e", "var(--text)"),
    ("experience.css", ".human-promises p", "#271b10", "var(--text)"),
    ("experience.css", ".loop-orbit-label", "#291d12", "var(--muted)"),
    ("experience.css", ".loop-orbit-node", "#2a1e12", "var(--muted)"),
    ("experience.css", ".loop-return", "#382c0c", "var(--amber)"),
    ("experience.css", ".loop-aside > .mono", "#2e2114", "var(--muted)"),
    ("experience.css", ".security-group h3", "#291d12", "var(--muted)"),
    ("experience.css", ".memory-match > .mono", "#142232", "var(--muted)"),
    ("experience.css", ".memory-match > span:nth-child(2)", "#251a0f", "var(--text)"),
    ("experience.css", ".memory-lesson .mono", "#2c1f13", "var(--muted)"),
    ("experience.css", ".memory-lesson p", "#22180e", "var(--text)"),
    ("experience.css", ".memory-lesson > span:last-child", "#152334", "var(--muted)"),
    ("reference-pages.css", ".docs-sidebar nav a", "#281c11", "var(--muted)"),
    ("reference-pages.css", ".docs-content p", "#281c11", "var(--muted)"),
    ("reference-pages.css", ".docs-workflow span", "#2a1e12", "var(--muted)"),
    ("reference-pages.css", ".boundary-grid .mono", "#2a1e12", "var(--muted)"),
    ("console.css", ".console-sitebar > a:last-child", "#24190f", "var(--text)"),
]

# Straight text swaps, each asserted to occur exactly once.
SWAPS = [
    # The architecture page painted its standalone system section with the page
    # ground. On a slate ground that puts the beige panel tokens this element
    # already carries (from `.system-section`) over a dark background. Letting
    # `.system-section`'s own beige through keeps one component on one plane.
    (
        "reference-pages.css",
        """.architecture-page .system-standalone {
  min-height: auto;
  padding-top: 40px;
  padding-bottom: 75px;
  background: var(--bg);
}""",
        """.architecture-page .system-standalone {
  min-height: auto;
  padding-top: 40px;
  padding-bottom: 75px;
  /* Deliberately no background. This section used to repaint itself with the
     page ground to read as full-bleed; on the slate ground that would drop the
     dark ink the panel tokens give it onto a dark surface. Inheriting
     `.system-section`'s beige keeps the standalone view on the same plane as
     the same component everywhere else. */
}""",
    ),
    # A button filled with the plane's ink needs the plane's anti-ink as its
    # label. `--bg` used to be that, but the ground is dark now, so the label
    # has to come from a token that still inverts with the plane.
    (
        "globals.css",
        """.button-light {
  background: var(--text);
  color: var(--bg);
}
.button-light:hover {
  /* Same reason, one step further: the fill darkens away from its light label. */
  background: #150e07;
}""",
        """.button-light {
  /* The label is the plane's anti-ink, so it inverts with the fill: a dark
     button under a cream label on a beige panel, a light button under a dark
     label on the slate ground. --bg no longer works here — it is the ground,
     so inside a panel it handed slate type to a near-black fill. */
  background: var(--text);
  color: var(--accent-ink);
}
.button-light:hover {
  /* Mixed rather than fixed. A hard-coded darker hex would drive the ground
     plane's light fill down toward its own dark label and cost the contrast the
     hover is supposed to add; blending toward --text moves away from the label
     on both planes. */
  background: color-mix(in srgb, var(--text) 86%, var(--bg));
}""",
    ),
    (
        "globals.css",
        """.button-primary:hover {
  /* The fill is dark and its label is light now, so hover deepens for the same
     reason it used to lift: moving the fill toward its own label costs contrast
     instead of gaining it. */
  background: #40314f;
}""",
        """.button-primary:hover {
  /* Blended, not fixed, for the same reason as .button-light:hover: the fill
     and its label swap polarity between the two planes, so hover has to move
     away from the label whichever way round they are. */
  background: color-mix(in srgb, var(--accent) 88%, var(--text));
}""",
    ),
    (
        "globals.css",
        """.button-outline:hover {
  background: #1f150c08;
  border-color: #273f5e;
}""",
        """.button-outline:hover {
  /* --accent-wash is the one wash token that flips with the plane: white at 10%
     over the slate ground, plum at 7% over a beige panel. */
  background: var(--accent-wash);
  border-color: var(--line);
}""",
    ),
]


def blank_comments(text: str) -> str:
    """Same length as `text`, so offsets stay usable against the original."""
    return re.sub(r"/\*.*?\*/", lambda m: " " * len(m.group(0)), text, flags=re.S)


def rule_spans(text: str):
    """(selector_list, body_start, body_end) for every style rule, orig offsets."""
    t = blank_comments(text)
    out, i, n = [], 0, len(t)
    while i < n:
        b = t.find("{", i)
        if b < 0:
            break
        sel = t[i:b].strip()
        depth, k = 0, b
        while k < n:
            if t[k] == "{":
                depth += 1
            elif t[k] == "}":
                depth -= 1
                if depth == 0:
                    break
            k += 1
        if not sel.startswith("@"):
            out.append((sel, b + 1, k))
        i = k + 1
    return out


def main() -> int:
    by_file = {}
    for f, sel, lit, tok in FLIPS:
        by_file.setdefault(f, []).append((sel, lit, tok))

    failures = 0
    for f, jobs in by_file.items():
        p = APP / f
        text = p.read_text(encoding="utf-8")
        spans = rule_spans(text)
        edits = []
        for sel, lit, tok in jobs:
            owned = [s for s in spans if sel in [x.strip() for x in s[0].split(",")]]
            hit = None
            for _, bs, be in owned:
                m = re.search(r"(?<![-\w])color\s*:\s*" + re.escape(lit) + r"\s*;", text[bs:be], re.I)
                if m:
                    hit = (bs + m.start(), bs + m.end())
                    break
            if hit is None:
                print(f"  !! {f}: no 'color: {lit}' in {sel} ({len(owned)} matching rules)")
                failures += 1
                continue
            edits.append((*hit, f"color: {tok};", sel, lit, tok))
        edits.sort(key=lambda e: -e[0])
        for st, en, new, sel, lit, tok in edits:
            text = text[:st] + new + text[en:]
            print(f"  {f:<20} {sel:<40} {lit} -> {tok}")
        p.write_text(text, encoding="utf-8")

    for f, old, new in SWAPS:
        p = APP / f
        text = p.read_text(encoding="utf-8")
        n = text.count(old)
        if n != 1:
            print(f"  !! {f}: swap block occurs {n} times, expected 1")
            failures += 1
            continue
        p.write_text(text.replace(old, new), encoding="utf-8")
        print(f"  {f:<20} swap applied ({len(old)} -> {len(new)} bytes)")

    print(f"\n{'FAILED' if failures else 'OK'} — {failures} problem(s)")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
