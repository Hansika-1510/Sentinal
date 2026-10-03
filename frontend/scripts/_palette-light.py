"""One-off: Oxblood & Bone (dark) -> Colour Hunt palette (light).

This is a *lightness inversion*, not a hue rotation, so the mapping is a damped
inversion: new_L = 100 - old_L - K*sin(pi*old_L/100). The sine term is the fix
for the one thing a straight inversion gets wrong on a light ground — midtones.
A dark theme's secondary copy sits at L 40-58 and inverts to L 42-60, which is
far too pale on a cream page. The sine pulls the middle down hardest (K at
L=50) while leaving both ends almost untouched, so the cream ground and the
near-black text land where the palette puts them.

Neutrals are the whole hue-38 warm family; the accents (oxblood / amber /
green) are swapped explicitly rather than ramped, since ramping a saturated
colour through a neutral ladder just produces mud.
"""
import re, glob, math, colorsys, os

# --- the light ramp ------------------------------------------------------
# Warm brown at the dark end, the palette's cream at the light end. The hue
# sweeps 4deg -> 47deg across the ladder, so the palette's own dusty brown
# (#946d6d) sits at its natural L=50.4 without banding. The top four are the
# near-white step; the bottom is the near-black text step.
RAMP_HEX = [
    "2e1f1e", "432e2d", "553b3a", "634746", "6f504f", "7d5c5b", "8a6867",
    "946d6d", "9f8078", "ad9484", "bda692", "cdbb9d", "dfd0b4", "efe3cb",
    "fdf4d2", "f8eedf", "fffaf0", "fffdf8",
]

def L_of(h):
    r, g, b = (int(h[i:i + 2], 16) for i in (0, 2, 4))
    return (max(r, g, b) + min(r, g, b)) / 2 / 255 * 100

RAMP = sorted((L_of(h), h) for h in RAMP_HEX)

def ramp(l):
    if l <= RAMP[0][0]:
        return RAMP[0][1]
    if l >= RAMP[-1][0]:
        return RAMP[-1][1]
    for (l0, h0), (l1, h1) in zip(RAMP, RAMP[1:]):
        if l0 <= l <= l1:
            t = (l - l0) / (l1 - l0) if l1 > l0 else 0.0
            a = [int(h0[i:i + 2], 16) for i in (0, 2, 4)]
            c = [int(h1[i:i + 2], 16) for i in (0, 2, 4)]
            return "".join(f"{round(a[i] + (c[i] - a[i]) * t):02x}" for i in range(3))
    return RAMP[-1][1]

K = 14.7

def map_hex(h):
    r, g, b = (int(h[i:i + 2], 16) for i in (0, 2, 4))
    old = (max(r, g, b) + min(r, g, b)) / 2 / 255 * 100
    new = 100 - old - K * math.sin(math.pi * old / 100)
    return ramp(max(0.0, min(100.0, new)))

# --- accents -------------------------------------------------------------
# Anything outside the warm-neutral band. Ramping these through a neutral
# ladder would just grey them out, so each maps to its explicit light-theme
# counterpart. Text-bearing greens/ambers are darkened to clear AA on cream;
# borders and fills only need the 3:1 component threshold.
SWAPS = {
    # oxblood -> the palette's mauve. --accent carries fills/borders/strokes;
    # --accent-text is the darker text-safe variant (5.6:1 on cream).
    "a8443c": "a290b7",
    "d67168": "6b5a82",
    "8f3229": "8f7aa8",
    "b37a62": "8f7aa8",
    # amber -> dark amber, AA on cream (4.8:1).
    "d4a45f": "8a6520",
    "b08659": "7d5c1e",
    "a8865c": "8a6520",
    # green -> dark green. Text uses clear 4.5:1; borders only need 3:1.
    "8fbf95": "47704f",
    "9db894": "527257",
    "a3bfa0": "4e7355",
    "a8c4a8": "4b7050",
    "445138": "3f6b47",
    "455239": "3d6645",
    "5e6f52": "486b4e",
    "5c6650": "3f5c45",
    "638c65": "47704f",
    "647055": "3f5c45",
    "6a8a70": "47704f",
    "97a892": "4f7154",
    "9cb4a1": "4d7355",
    "9fb8a0": "4d7355",
    "a1b59c": "4f7154",
    "b7d191": "4f7154",
    # a coral warning border and two low-alpha washes on the dark ground.
    # The near-white wash inverts to near-black so it stays a wash.
    "e98b67": "8a6520",
    "d68e39": "8a6520",
    "f7f2e8": "2e1f1e",
}

def is_warm_neutral(h):
    r, g, b = (int(h[i:i + 2], 16) / 255 for i in (0, 2, 4))
    hue, _, sat = colorsys.rgb_to_hls(r, g, b)
    return 20 <= hue * 360 <= 60 and sat < 0.45

HEX = re.compile(r"#([0-9a-fA-F]{6})([0-9a-fA-F]{2})?\b")
# The two mask-image gradient stops are alpha, not colour. Never rewrite them.
MASK = re.compile(r"mask-image\s*:")

def convert(text):
    out, seen = [], {}
    for line in text.split("\n"):
        if MASK.search(line):
            out.append(line)
            continue
        def sub(m):
            h, a = m.group(1).lower(), m.group(2) or ""
            key = h + a
            if key in seen:
                return seen[key]
            if h in SWAPS:
                new = SWAPS[h] + a
            elif is_warm_neutral(h):
                new = map_hex(h) + a
            else:
                new = h + a  # unknown chromatic: leave it, review by hand
            seen[key] = "#" + new
            return "#" + new
        out.append(HEX.sub(sub, line))
    return "\n".join(out)

def lum(h):
    def ch(c):
        c /= 255
        return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4
    r, g, b = (ch(int(h[i:i + 2], 16)) for i in (0, 2, 4))
    return 0.2126 * r + 0.7152 * g + 0.0722 * b

def contrast(a, b):
    la, lb = lum(a), lum(b)
    return (max(la, lb) + 0.05) / (min(la, lb) + 0.05)

APPLY = os.environ.get("APPLY") == "1"

if __name__ == "__main__":
    BG = "fdf4d2"
    print(f"ramp anchors: {len(RAMP)}  span L {RAMP[0][0]:.1f} -> {RAMP[-1][0]:.1f}")
    print("\n--- old token -> new (contrast on the new cream ground) ---")
    OLD = {
        "--bg": "12100e", "--surface": "1a1815", "--surface-raised": "221f1b",
        "--line": "332f29", "--line-strong": "423d35", "--dim": "6e695f",
        "--mid": "857f74", "--muted": "9c968a", "--text": "e9e2d6",
    }
    for name, h in OLD.items():
        new = map_hex(h)
        c = contrast(new, BG)
        flag = "OK " if c >= 4.5 else ("3:1" if c >= 3 else "!! ")
        print(f"  {name:16s} #{h} -> #{new}   {c:5.2f}:1  {flag}")
    print("\n--- accents ---")
    for old, new in SWAPS.items():
        c = contrast(new, BG)
        print(f"  #{old} -> #{new}   {c:5.2f}:1 on cream")

    total = changed = 0
    for f in sorted(glob.glob("src/app/*.css")):
        src = open(f, encoding="utf-8").read()
        dst = convert(src)
        n = sum(1 for a, b in zip(HEX.finditer(src), HEX.finditer(dst)) if a.group(0) != b.group(0))
        total += len(HEX.findall(src))
        changed += n
        print(f"{'WROTE' if APPLY else 'would write'} {f}: {n} substitutions")
        if APPLY:
            open(f, "w", encoding="utf-8").write(dst)
    print(f"\n{changed} of {total} literals changed. APPLY={'on' if APPLY else 'off (dry run)'}")
