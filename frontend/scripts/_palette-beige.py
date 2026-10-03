"""Sentinel — the beige-on-light-blue re-key.

The user asked for a lighter blue ground with beige in between. The first half
is easy (#3368a0 -> #6f9acb); the second half forces the theme's second full
inversion, because a beige panel can only sit on the light-blue side of the
page if the ink goes dark again.

There is also a hard physical constraint that shapes everything below. On a
ground at luminance 0.308, AA needs the ink at luminance <= 0.0296. That is a
narrow band, and it is narrower than the surface band it has to serve: the same
ink that clears 4.5:1 on the blue reads 10-14:1 on a beige panel. So one token
set cannot give a leisurely ladder on the panels and also stay legal on the
ground — the ladder is solved against the *ground*, the worst case, and the
panels inherit a compressed but very legible range. Hierarchy on the ground
therefore comes from the narrow luminance steps that fit inside the band
(5.98 -> 4.52:1) plus the warm/cool hue split, exactly as it did on the blue.

Nothing here is a hue-blind inversion; as with the blue pass, a literal's job
decides where it lands:
  * `color` is ink and must end up dark, split warm (dusty brown) / cool
    (slate) so the palette's two ink families survive the flip.
  * `background` is either a surface (the dark navy cards, which become beige
    panels *above* the ground) or a decorative mark (the light-blue sheet lines
    and sparkline bars, which must become dark marks or they vanish).
  * `border*` and `stroke` are hairlines that were lighter than the old ground
    and must now be darker than the new one.

Run with APPLY=1 to write.
"""

import os
import re
import colorsys

FILES = ["src/app/globals.css", "src/app/experience.css", "src/app/console.css",
         "src/app/reference-pages.css"]

GROUND_OLD = "3368a0"
GROUND_NEW = "6f9acb"

HEX = re.compile(r"#([0-9a-fA-F]{6})([0-9a-fA-F]{2})?\b")
MASK = re.compile(r"mask-image\s*:")
PROP = re.compile(r"([a-z-]+)\s*:\s*([^;{}]*#[0-9a-fA-F]{6}[^;{}]*)")


# ------------------------------------------------------------------ maths
def to_lin(c):
    c /= 255
    return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4


def to_srgb(c):
    c = 0.0 if c < 0 else (1.0 if c > 1 else c)
    v = c * 12.92 if c <= 0.0031308 else 1.055 * (c ** (1 / 2.4)) - 0.055
    return max(0, min(255, round(v * 255)))


def rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def hexs(t):
    return "%02x%02x%02x" % t


def lum_of_lin(l):
    return 0.2126 * l[0] + 0.7152 * l[1] + 0.0722 * l[2]


def lum(h):
    return lum_of_lin([to_lin(c) for c in rgb(h)])


def hsl(h):
    r, g, b = [c / 255 for c in rgb(h)]
    hh, l, s = colorsys.rgb_to_hls(r, g, b)
    return hh * 360, s * 100, l * 100


def scale(base, target_lum):
    """Rescale a colour down to `target_lum`, holding its hue and chroma ratio.

    Linear scaling is what keeps a brown brown and a slate slate; a naive
    lightness map would drag both toward black and lose the warm/cool split
    that is doing the hierarchy work.
    """
    l = [to_lin(c) for c in rgb(base)]
    cur = lum_of_lin(l)
    if cur <= 0:
        return base.lstrip("#")
    k = target_lum / cur
    return hexs(tuple(to_srgb(c * k) for c in l))


def span(src_lo, src_hi, lum_lo, lum_hi):
    """Piecewise-linear map from a source-lightness range to a luminance range."""
    def f(L):
        t = 0.0 if src_hi == src_lo else (L - src_lo) / (src_hi - src_lo)
        t = max(0.0, min(1.0, t))
        return lum_lo + (lum_hi - lum_lo) * t
    return f


def lookup(points, L):
    """Linear RGB interpolation through (source-L, hex) anchors."""
    pts = sorted(points, key=lambda p: p[0])
    if L <= pts[0][0]:
        return pts[0][1]
    if L >= pts[-1][0]:
        return pts[-1][1]
    for i in range(len(pts) - 1):
        l0, h0 = pts[i]
        l1, h1 = pts[i + 1]
        if l0 <= L <= l1:
            t = 0.0 if l1 == l0 else (L - l0) / (l1 - l0)
            a, b = rgb(h0), rgb(h1)
            return hexs(tuple(round(x + (y - x) * t) for x, y in zip(a, b)))
    return pts[-1][1]


# ------------------------------------------------------- the target ladder
# Surfaces sit ABOVE the ground now, so the deepest source card becomes the
# deepest beige and the source surface nearest the old ground becomes the
# lightest beige. Anchors pass through the two tokens by construction.
SURFACE = [
    (18.0, "#d5c294"),
    (32.2, "#e6d7b4"),   # --surface-raised
    (36.5, "#efe3c8"),   # --surface
    (41.4, "#f7f0de"),
]

# Ink bands. Higher source lightness meant more contrast on the old dark
# ground, so it must mean more contrast (a darker target) here.
ink_warm = span(88.8, 92.4, 0.0175, 0.0085)   # cream family -> dusty brown
ink_cool = span(90.8, 92.9, 0.0290, 0.0150)   # cool whites   -> slate
ink_green = span(90.6, 92.9, 0.0270, 0.0215)  # mint family   -> deep green
ink_amber = span(88.4, 90.0, 0.0280, 0.0265)  # amber family  -> deep amber

BASE_WARM = "#3b2b1c"
BASE_COOL = "#22364d"
BASE_GREEN = "#1f3d2a"
BASE_AMBER = "#4a3a12"

# Hairlines were lighter than the old ground; they must be darker than the new
# one. 75.7-86 source maps to 3.4-4.4:1 on the ground — visible as boundaries,
# still under the 4.5 of body copy so a rule never competes with the words.
border_band = span(75.7, 86.0, 0.0550, 0.0320)
BASE_BORDER = "#2c4667"

# The decorative marks (sheet lines, sparkline bars, status dots) sit on beige
# panels and on the blue ground alike, so they are solved to read on either.
# 3:1 on the *ground* is the binding case: at their old value they were lighter
# than the ground and would simply vanish, and several of them (the sparkline,
# the status dot) carry state rather than being pure ornament, so they are held
# to the UI-component floor rather than treated as decoration.
mark_band = span(65.1, 75.9, 0.0640, 0.0380)
BASE_MARK = "#3a5a80"

# Shadows: on a light ground a shadow is a soft blue-grey at low alpha, not the
# near-black it had to be on the blue.
SHADOW = "33506f"
SHADOW_ALPHA = 0.18

# ------------------------------------------------- chromatic (exact value)
# These are unambiguous by value, and mixing them through the neutral map would
# turn a state colour into a shade of the page. Each maps into its own family.
SWAPS = {
    # Accent. The palette's mauve is 1.01:1 on the new ground — the same
    # luminance as the blue — so it cannot be a fill at its own value. It goes
    # dark plum, which clears 3:1 as a boundary and carries a light label.
    "cdbde4": "4d3c60",   # accent fill / border
    "dccff0": "40314f",   # accent fill hover — the fill is dark now, so hover
                          # deepens for the same reason it used to lift: moving
                          # toward the label costs contrast instead of gaining it
    "c3b2dc": "43345a",   # accent mid
    "efe6fa": "322545",   # accent text — dark plum type on the ground
    # Success. Ten near-identical mints become one deep green family. They are
    # drawn as 3-5% washes in places, so the ground is what their text sits on.
    "f1f8f2": None, "eef7ef": None, "eaf5ec": None, "e7f3e9": None,
    "e5f2e8": None, "e4f2e6": None, "e0f0e3": None, "dfefe1": None,
    "dbedde": None, "d6ebd9": None,
    # Warning.
    "f5edd6": None, "f4ebcf": None,
}

# Fill in the green/amber swaps from their own source lightness so the family
# keeps its internal order under the inversion.
for _g in ["f1f8f2", "eef7ef", "eaf5ec", "e7f3e9", "e5f2e8",
           "e4f2e6", "e0f0e3", "dfefe1", "dbedde", "d6ebd9"]:
    SWAPS[_g] = scale(BASE_GREEN, ink_green(hsl("#" + _g)[2]))
for _a in ["f5edd6", "f4ebcf"]:
    SWAPS[_a] = scale(BASE_AMBER, ink_amber(hsl("#" + _a)[2]))


def family(h):
    H, S, L = hsl(h)
    if 255 <= H <= 330:
        return "mauve"
    if 95 <= H <= 175:
        return "green"
    if 15 <= H <= 90:
        return "warm"
    if 175 <= H <= 255:
        return "cool"
    return "warm"


def target(prop, tok, alpha):
    h = tok.lower()

    if h in SWAPS:
        return SWAPS[h]
    if h == GROUND_OLD:
        return GROUND_NEW

    L = hsl(h)[2]
    fam = family(h)

    if prop == "color":
        if fam == "green":
            return scale(BASE_GREEN, ink_green(L))
        if fam == "warm":
            return scale(BASE_WARM, ink_warm(L))
        return scale(BASE_COOL, ink_cool(L))

    if prop.startswith("background"):
        if L >= 60:
            # A light background is either a decorative mark or a fill that
            # carries a label. Marks need to stay visible on beige and on blue;
            # a warm fill is the "light" button, which becomes the dark ink.
            if fam == "warm":
                return scale(BASE_WARM, ink_warm(max(L, 88.8)))
            if fam == "green":
                return scale(BASE_GREEN, ink_green(max(L, 90.6)))
            return lookup([(65.1, scale(BASE_MARK, mark_band(65.1))),
                           (75.9, scale(BASE_MARK, mark_band(75.9)))], L)
        # Surfaces: the dark navy cards become beige panels above the ground.
        return lookup(SURFACE, L)

    if prop.startswith("border") or prop in ("fill", "stroke"):
        if fam == "green":
            return scale(BASE_GREEN, ink_green(max(L, 90.6)))
        if fam == "warm":
            return scale(BASE_AMBER, ink_amber(min(L, 90.0)))
        return scale(BASE_BORDER, border_band(L))

    return None


def convert(prop, tok):
    t = target(prop, tok, None)
    return tok.lower() if t is None else t


def process(text):
    changed = 0
    pairs = {}

    out = []
    for line in text.split("\n"):
        if MASK.search(line) or "#" not in line:
            out.append(line)
            continue

        def repl_line(m):
            nonlocal changed
            prop, body = m.group(1), m.group(2)

            if prop == "box-shadow":
                def sh(sm):
                    nonlocal changed
                    changed += 1
                    return f"#{SHADOW}{int(SHADOW_ALPHA * 255):02x}"
                return f"{prop}: {HEX.sub(sh, body)}"

            named = (prop == "color" or prop.startswith(("background", "border"))
                     or prop in ("fill", "stroke") or prop.startswith("--"))
            if not named:
                return m.group(0)

            # A custom property has no property name to read, so fall back to
            # the token's own name for the same job hint.
            key = prop
            if prop.startswith("--"):
                if any(w in prop for w in ("line", "border")):
                    key = "border-top"
                elif any(w in prop for w in ("surface", "bg", "panel")):
                    key = "background"
                else:
                    key = "color"

            def sub(sm):
                nonlocal changed
                tok, a = sm.group(1), sm.group(2)
                new = convert(key, tok)
                if new != tok.lower():
                    changed += 1
                    pairs[tok.lower()] = new
                return "#" + new + (a or "")

            return f"{prop}: {HEX.sub(sub, body)}"

        out.append(PROP.sub(repl_line, line))
    return "\n".join(out), changed, pairs


if __name__ == "__main__":
    apply = os.environ.get("APPLY") == "1"
    total = 0
    allpairs = {}
    for f in FILES:
        src = open(f, encoding="utf-8").read()
        dst, n, pairs = process(src)
        total += n
        allpairs.update(pairs)
        print(f"{f:<30} {n:4d} literals")
        if apply:
            open(f, "w", encoding="utf-8", newline="").write(dst)
    print(f"{'TOTAL':<30} {total:4d}", "written" if apply else "(dry run)")
    print(f"\n{len(allpairs)} distinct source values -> target")
    for k in sorted(allpairs):
        print(f"  #{k} -> #{allpairs[k]}")
