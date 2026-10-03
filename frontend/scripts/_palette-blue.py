"""Sentinel — the slate-blue re-key.

The user replaced the light-yellow ground with #3368a0. That colour is mid-blue
(L 41.4), so it inverts the theme's key a second time: cream text on it clears
AA at 5.25:1, while every tone of the light theme's dark ink sits at 1.1-2.0:1.
So the ladder is re-keyed into the blue family and the ink goes light again.

Two things made a lightness-blind inversion wrong here, and both are why this
pass reads the CSS property rather than just the colour:

  * A literal's job decides where it lands. #2e1f1e is --text in one place and
    a button fill in another; as ink it must become near-white, as a fill it
    must become near-white too — but #d4c3a6 is a border in one place and a
    card surface in another, and those go to opposite sides of the ground.
  * On a mid-blue ground the text band is narrow: 4.5:1 needs L >= 89.5, and
    pure white only reaches 5.79:1. So all ink is compressed into 89.5-97.5 and
    hierarchy comes from hue and size, not from lightness. That is the honest
    cost of a mid-tone ground and it is why the ladder below the ground is
    where the depth lives instead.

Run with APPLY=1 to write.
"""

import os
import re
import colorsys

FILES = ["src/app/globals.css", "src/app/experience.css", "src/app/console.css",
         "src/app/reference-pages.css"]

# ---------------------------------------------------------------- blue ladder
# The ground #3368a0 is in here so new_L 41.4 resolves to it exactly. Sorted by
# measured lightness at load, so the order written here does not matter.
BLUE = [
    "0b1826", "101f30", "15273b", "1a2f46", "1f3752", "243f5e",
    "29476a", "2e4f76", "34608f", "3368a0", "3a71ab", "437ab2",
    "4c83b9", "568bc0", "628fc4", "6f9acb", "7ea6d2", "8eb3da",
    "9fc1e3", "b1cfea", "c4dcf0", "d7e6f4", "e6effa", "f2f8fd", "fbfdff",
]

HEX = re.compile(r"#([0-9a-fA-F]{6})([0-9a-fA-F]{2})?\b")
MASK = re.compile(r"mask-image\s*:")
PROP = re.compile(r"([a-z-]+)\s*:\s*([^;{}]*#[0-9a-fA-F]{6}[^;{}]*)")


def rgb(h):
    return tuple(int(h[i : i + 2], 16) for i in (0, 2, 4))


def L_of(h):
    r, g, b = rgb(h)
    return (max(r, g, b) + min(r, g, b)) / 2 / 255 * 100


RAMP = sorted((L_of(h), rgb(h)) for h in BLUE)


def ramp(L):
    """Nearest blue-family colour at this lightness, interpolated in RGB."""
    return lookup(RAMP, L)


# Warm ink ladder, for the palette's cream. Its own lightness span is narrow —
# every one of these is above L 90 — so it takes a lightness, not a ramp walk.
CREAM = [
    "f4e9be", "faf0cc", "fdf4d2", "fff7e2", "fffaf0", "fffdf8",
]
CREAM_RAMP = sorted((L_of(h), rgb(h)) for h in CREAM)


def warm(L):
    return lookup(CREAM_RAMP, L)


def lookup(table, L):
    L = max(0.0, min(100.0, L))
    if L <= table[0][0]:
        return table[0][1]
    if L >= table[-1][0]:
        return table[-1][1]
    for i in range(len(table) - 1):
        l0, c0 = table[i]
        l1, c1 = table[i + 1]
        if l0 <= L <= l1:
            t = 0.0 if l1 == l0 else (L - l0) / (l1 - l0)
            return tuple(round(a + (b - a) * t) for a, b in zip(c0, c1))
    return table[-1][1]


def clamp(v, lo, hi):
    return max(lo, min(hi, v))


def target_L(prop, L):
    """Where this literal's lightness lands in the blue theme."""
    if prop == "color":
        # Ink. Darker ink in the light theme becomes brighter ink here, and the
        # whole band is squeezed against the top because a mid-blue ground
        # cannot carry anything dimmer at 4.5:1 — the floor is 90 because 89.5
        # lands at 4.49:1, which is a fail by a hair.
        #
        # Primary ink keeps the palette's cream and secondary ink goes cool.
        # That split is doing real work: squeezed into 90-97.5 the lightness
        # spread alone is invisible (4.5:1 against 5.1:1), so hierarchy has to
        # come from hue, and warm-on-cool is the one axis this palette gives.
        if L <= 25:
            return warm(97.5 - 0.35 * L)
        return clamp(97 - 0.16 * L, 90.0, 97.5)
    if prop.startswith("background"):
        # Surfaces sit *below* the ground. That is what keeps body copy legible
        # on a card: a surface lighter than the ground drops card text to
        # 3.95:1. The band is stretched rather than compressed — the source
        # surfaces are all within 16 points of the ground, and mapping them 1:1
        # leaves a card 1.06:1 from the page, which is to say invisible.
        if L >= 60:
            return clamp(41.4 - (90.8 - L) * 1.15, 18, 41.4)
        # Below 60 the only backgrounds are fills — buttons, badges, and the
        # low-alpha tints that sit on cards. They invert with the theme: a dark
        # chip on cream becomes a light chip on blue, and a 12% darkening wash
        # over a cream card becomes a 12% lightening wash over a navy one.
        # The deepest fills go warm, so the "contrast" button matches primary
        # ink rather than sitting a half-step off it in a second hue.
        if L <= 25:
            return warm(97.5 - 0.35 * L)
        return clamp(97 - 0.62 * L, 50, 97)
    if prop.startswith("border"):
        # A hairline on a mid-blue ground only reads if it is clearly lighter:
        # at the ground's own lightness the contrast is under 2:1 and the line
        # disappears. 74-84 puts it at 2.8-3.6:1 — present, but below the 4.8
        # of body copy, so rules never compete with the words they separate.
        return clamp(74 + 0.11 * L, 74, 84)
    if prop in ("fill", "stroke"):
        return clamp(88 - 0.14 * L, 62, 92)
    return None


# ------------------------------------------------- chromatic (accent / state)
# Hue, not saturation, separates these: the light theme's neutrals are a warm
# family at hue 0-47 and the accents sit well outside it (mauve 266, green 130).
# Amber is the exception — it lives at hue 39, inside the neutral band — so it
# is swapped by exact value.
SWAPS = {
    # Accent. On blue the mauve carries fills at a light value, and the
    # accent-coloured *labels* need an even paler lavender: mauve itself is only
    # 1.99:1 on this ground, so nothing accent-coloured can be text below 4.5:1
    # unless it is nearly white.
    "a290b7": "cdbde4",   # accent fill / border
    "b3a3c6": "dccff0",   # accent fill hover — brightens, as on any light-ground
    "8f7aa8": "c3b2dc",   # accent mid
    "65557b": "efe6fa",   # accent text
    # Success. Ten near-identical dark greens become one mint family, ordered so
    # the darker original lands brighter, matching the inversion. Every member
    # clears 4.5:1 on the ground, because these states are drawn as 4-5% washes
    # rather than solid fills — the wash barely moves the surface underneath, so
    # the ground is the only thing their text ever actually sits on. That leaves
    # no room for a shade ladder: at this ground the whole legible green range is
    # L 88-96, which is why the family reads as one colour at ten near-values.
    "3f5c45": "f1f8f2",   # L 96
    "3d6645": "eef7ef",   # L 95
    "406447": "eaf5ec",   # L 94
    "42634a": "e7f3e9",   # L 93
    "426347": "e5f2e8",   # L 92.5
    "43634a": "e4f2e6",   # L 92
    "46634a": "e0f0e3",   # L 91
    "47624b": "dfefe1",   # L 90.5
    "3f6b47": "dbedde",   # L 89.5
    "486b4e": "d6ebd9",   # L 88
    # Warning.
    "76561b": "f5edd6",
    "76571c": "f4ebcf",
}

# Shadows invert to near-white under a lightness map, which is useless. On a
# dark ground a shadow has to be a darker blue, at a little under half the
# source alpha — it reads far more strongly on blue than it did on cream.
SHADOW = "08192c"
SHADOW_ALPHA = 0.45


def convert(prop, tok, alpha):
    h = tok.lower()
    if h in SWAPS:
        return SWAPS[h]
    t = target_L(prop, L_of(h))
    if t is None:
        return h
    r, g, b = t if isinstance(t, tuple) else ramp(t)
    return f"{r:02x}{g:02x}{b:02x}"


def process(text):
    changed = 0

    def line_ok(line):
        # mask-image gradients are not palette; they are a stencil.
        return not MASK.search(line)

    out = []
    for line in text.split("\n"):
        if not line_ok(line) or "#" not in line:
            out.append(line)
            continue

        def repl_line(m):
            nonlocal changed
            prop = m.group(1)
            body = m.group(2)
            if prop == "box-shadow":
                def sh(sm):
                    nonlocal changed
                    changed += 1
                    return f"#{SHADOW}{int(SHADOW_ALPHA * 255):02x}"
                return f"{prop}: {HEX.sub(sh, body)}"
            if not (prop == "color" or prop.startswith("background")
                    or prop.startswith("border") or prop in ("fill", "stroke")):
                return m.group(0)

            def sub(sm):
                nonlocal changed
                tok, a = sm.group(1), sm.group(2)
                new = convert(prop, tok, a)
                if new != tok.lower():
                    changed += 1
                return "#" + new + (a or "")

            return f"{prop}: {HEX.sub(sub, body)}"

        out.append(PROP.sub(repl_line, line))
    return "\n".join(out), changed


if __name__ == "__main__":
    apply = os.environ.get("APPLY") == "1"
    total = 0
    for f in FILES:
        src = open(f, encoding="utf-8").read()
        dst, n = process(src)
        total += n
        print(f"{f:<28} {n:4d} literals")
        if apply:
            open(f, "w", encoding="utf-8", newline="").write(dst)
    print(f"{'TOTAL':<28} {total:4d}", "written" if apply else "(dry run)")
