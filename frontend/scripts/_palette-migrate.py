# One-off palette migration: re-tint the neutral ladder, swap accent + state colours.
# Not a build step. Run with APPLY=1 to write.
import re, glob, os

# Oxblood & Bone. Anchor stops by lightness, interpolated. The low stops exist to
# keep shadows/vignettes darker than the background; the high stops keep the top of
# the ramp from collapsing into a single value.
ANCHORS = [(1.5, "050403"), (3.0, "090807"), (4.5, "0e0c0a"), (6.0, "12100e"),
           (9.0, "1a1815"), (12.0, "221f1b"), (18.0, "332f29"), (23.0, "423d35"),
           (40.0, "6e695f"), (49.0, "857f74"), (58.0, "9c968a"), (70.0, "bdb4a4"),
           (80.0, "d6cdbd"), (88.0, "e9e2d6"), (94.0, "f0eadf"), (100.0, "f7f2e8")]

# Exact substitutions for chromatic literals (old -> new), applied verbatim.
# NOTE: #000 in globals.css:789 is a mask-image alpha, not a colour - never touch it.
SWAPS = {
    "ff7054": "a8443c",   # accent: vermilion -> deep oxblood (fills/borders)
    "ff6440": "a8443c",   # lens point light
    "ea3e20": "8f3229",   # lens emissive
    "fff4e4": "f7f2e8",   # lens key light / core warm white
    "94d7a4": "8fbf95",   # success green, desaturated
    "e8ba74": "d4a45f",   # warning amber, desaturated
    "b2d5ad": "a8c4a8", "adcf9f": "a3bfa0", "b2c894": "9db894",
    "a2c5a1": "9cb4a1", "a8c59a": "a1b59c", "a8c6a0": "9fb8a0",
    "9bb28c": "97a892", "629864": "6a8a70", "5b7547": "5e6f52",
    "405a31": "445138", "41562e": "455239", "637c45": "647055",
    "526747": "5c6650", "b38459": "b08659", "bb7960": "b37a62",
    "aa8858": "a8865c", "c6c9c1": "c9c4b8",
    "ff705410": "a8443c12", "ff70540c": "a8443c0e", "ff70542d": "a8443c30",
    "ff705413": "a8443c16", "ff705407": "a8443c0a", "ff705414": "a8443c17",
    "ff705408": "a8443c0b", "ff70540a": "a8443c0d", "ff70540b": "a8443c0e",
    "ff705435": "a8443c38", "ff705480": "a8443c80",
}

HEX = re.compile(r"#([0-9a-fA-F]{6})([0-9a-fA-F]{2})?\b")
# Guard the lookbehind so `border-color:` / `background-color:` are not rewritten.
TEXT_ACCENT = re.compile(r"(?<![-\w])color:(\s*)var\(--accent\)")


def near_neutral(r, g, b):
    return max(r, g, b) - min(r, g, b) <= 12


def remap(hex6):
    r, g, b = (int(hex6[i:i + 2], 16) for i in (0, 2, 4))
    L = (max(r, g, b) + min(r, g, b)) / 2 / 255 * 100
    if L <= ANCHORS[0][0]:
        return ANCHORS[0][1]
    if L >= ANCHORS[-1][0]:
        return ANCHORS[-1][1]
    for (l0, h0), (l1, h1) in zip(ANCHORS, ANCHORS[1:]):
        if l0 <= L <= l1:
            t = (L - l0) / (l1 - l0)
            a = [int(h0[i:i + 2], 16) for i in (0, 2, 4)]
            c = [int(h1[i:i + 2], 16) for i in (0, 2, 4)]
            return "".join(f"{round(a[i] + (c[i] - a[i]) * t):02x}" for i in range(3))
    return hex6


apply = os.environ.get("APPLY") == "1"
changed_total, seen, text_splits = 0, {}, 0

for path in sorted(glob.glob("src/app/*.css")):
    src = open(path, encoding="utf-8").read()

    def sub(m):
        global changed_total
        rgb, alpha = m.group(1), m.group(2) or ""
        low = rgb.lower()
        if low in SWAPS:
            new = SWAPS[low]
        else:
            r, g, b = (int(low[i:i + 2], 16) for i in (0, 2, 4))
            if not near_neutral(r, g, b):
                return m.group(0)
            new = remap(low)
        if new != low:
            changed_total += 1
            seen[f"#{low}"] = f"#{new}"
            return f"#{new}{alpha}"
        return m.group(0)

    out = HEX.sub(sub, src)
    out, n = TEXT_ACCENT.subn(r"color:\1var(--accent-text)", out)
    text_splits += n
    if apply and out != src:
        open(path, "w", encoding="utf-8").write(out)

print(f"{'APPLIED' if apply else 'DRY RUN'} - {changed_total} hex substitutions "
      f"({len(seen)} distinct), {text_splits} text-accent splits")
for old in sorted(seen, key=lambda h: sum(int(h[i:i + 2], 16) for i in (1, 3, 5))):
    print(f"  {old} -> {seen[old]}")
