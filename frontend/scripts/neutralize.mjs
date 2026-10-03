import fs from "node:fs/promises";

// Lock neutral surfaces to warm charcoal. Only recovery uses a green hue.
for (const file of [
  "src/app/experience.css",
  "src/app/console.css",
  "src/app/reference-pages.css",
]) {
  const content = await fs.readFile(file, "utf8");
  const result = content.replace(/#([0-9a-f]{6})([0-9a-f]{2})?\b/gi, (match, hex, alpha = "") => {
    const [r, g, b] = [0, 2, 4].map((i) => parseInt(hex.slice(i, i + 2), 16));
    if (
      ["94d7a4", "ff7054", "e8ba74"].includes(hex.toLowerCase()) ||
      Math.max(r, g, b) - Math.min(r, g, b) > 80 ||
      (g - r > 20 && g - b > 15)
    )
      return match;
    const value = Math.round(r * 0.3 + g * 0.5 + b * 0.2);
    return (
      "#" +
      [Math.min(255, value + 1), value, Math.max(0, value - 2)]
        .map((v) => v.toString(16).padStart(2, "0"))
        .join("") +
      alpha
    );
  });
  await fs.writeFile(file, result);
}
console.log("Neutral palette locked. Recovery color preserved.");
