# SENTINEL

A cinematic, interactive landing page for an AI software incident response platform. The story follows one example incident from a production failure to evidence, a developer-authored fix, review, recovery, and incident memory.

## Run

Use Node.js 22 or newer.

```sh
npm install
npm run dev
```

On Windows PowerShell, use `npm.cmd` if local execution policy blocks `npm.ps1`. Open http://localhost:3000.

```sh
npm run build
npm start
```

Set `NEXT_PUBLIC_SITE_URL` to the deployed origin for canonical social-image URLs. See `.env.example`.

## Routes

- `/`: the complete landing experience, with all 17 narrative scenes.
- `/console`: interactive demo console, including incident search, incident memory, evidence tabs, developer guidance, operational approval, audit trail, incident replay, and recovery verification.
- `/architecture`: the explorable 13-node lifecycle and its authority boundaries.
- `/docs`: the operating model, GitHub context, agents, review, approval, and security documentation.

## Implementation

- Next.js App Router, React, TypeScript, Tailwind CSS v4.
- GSAP ScrollTrigger for timeline construction, evidence connections, section reveals, lifecycle progression, and the horizontal agent sequence.
- Motion (the current Framer Motion package) for magnetic links, pointer-based depth, and chart transitions.
- Lenis for smooth desktop scrolling, with native touch behavior.
- An original Three.js signal lens in the hero, plus a 3D evidence constellation and lifecycle rail in two narrative sections. All three are dynamically loaded on desktop. The hero's local WebP render and the existing SVG connectors and route are the mobile, reduced-motion, and WebGL fallback.
- Geist and JetBrains Mono via `next/font`; Phosphor icons.

WebGL is scoped to the hero lens and the two section scenes, and the app caps itself at four live contexts. Every scene pauses off screen and when the browser tab is hidden, and each one's DOM content — the evidence buttons, the thirteen lifecycle nodes — stays the interactive, accessible layer. The console preview loads near the viewport. Reduced-motion mode mounts no WebGL at all, and disables parallax, smooth scrolling, automatic hero cycling, and pinned sections. On smaller screens, the agent sequence becomes a vertical layout and the section scenes fall back to their SVG or poster artwork.

Butter's typography, object physicality, whitespace, and narrative motion informed the art direction. No Butter branding, copy, assets, or exact layouts are reused. See `DESIGN.md` for the design system and motion ownership.

## Demo boundaries

This is a frontend product experience with illustrative data. It makes no production API calls, modifies no application source code, and performs no infrastructure actions. Approval records live in the current demo session. The console's operational rollback is an alternative response while a developer prepares a permanent fix; the landing page also demonstrates the reviewed developer-fix path.

## Verification

```sh
npm run typecheck
npm run test:e2e
npm run audit
```

The browser checks use Playwright and a local Chrome installation. Override its location with `CHROME_PATH`, and the server origin with `BASE_URL`. Screenshots and audit reports are written to the ignored `artifacts` directory.

`npm run audit` measures performance, so run it against a production build (`npm run build` then `npm start`) rather than the dev server. Both `npm start` and the checks default to `http://127.0.0.1:3000`; set `BASE_URL` when serving the build on another port.
