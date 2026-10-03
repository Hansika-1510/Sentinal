"use client";

import { useEffect, useRef } from "react";
import * as THREE from "three";
import { useThreeScene } from "@/lib/three/use-three-scene";

// Marks, not surfaces. These materials are unlit and the graph is drawn over
// the evidence section's beige panel — not the page ground — so they keep the
// panel plane's dark values, the same inversion the stylesheet's sheet lines
// and sparkline bars use on that surface. Solved against the panel: every value
// here clears 3:1 on #f2e8d0. The host is the panel and not the ground, which
// matters because the ground is dark now and would need the opposite of these.
const NODE_COLOR = 0x1d2e43;
const ACCENT = 0x4d3c60;
const STRAND_COLOR = 0x2a4464;
/** Depth stagger in world units — see `pushDepth` for why it is this small. */
const DEPTH_STEP = 0.34;
/** How far from the root card a marker is allowed to sit, in world units. */
const CARD_MARGIN = 0.2;

const NODE_BASE = new THREE.Color(NODE_COLOR);
const NODE_HOT = new THREE.Color(ACCENT);
const STRAND_BASE = new THREE.Color(STRAND_COLOR);
const STRAND_HOT = new THREE.Color(ACCENT);
/**
 * Fixed end states for the active marker, a set fraction of the way to accent.
 *
 * An earlier version lerped straight at `NODE_HOT` with a small per-frame rate
 * and no cap. That still converges completely — two seconds of frames is
 * `1 - 0.09^120`, which is zero — so the crystal turned solid accent and its
 * facets flattened. The mix has to be the destination, not the step size.
 */
const NODE_ACTIVE = NODE_BASE.clone().lerp(NODE_HOT, 0.4);
const EMISSIVE_ACTIVE = NODE_BASE.clone().lerp(NODE_HOT, 0.75);
const ONE = new THREE.Vector3(1, 1, 1);

type Box = { minX: number; maxX: number; minY: number; maxY: number };

type Slot = {
  strand: THREE.Mesh<THREE.BufferGeometry, THREE.MeshBasicMaterial>;
  marker: THREE.Mesh<THREE.IcosahedronGeometry, THREE.MeshStandardMaterial>;
  ring: THREE.Mesh<THREE.TorusGeometry, THREE.MeshBasicMaterial>;
  scale: number;
};

type Graph = {
  group: THREE.Group;
  slots: Slot[];
  /** Card centres in world space — where each strand begins. */
  origins: THREE.Vector3[];
  /** Root card centre — where every strand converges. */
  focus: THREE.Vector3;
};

/**
 * Move a point along the view axis while holding its screen position.
 *
 * Nudging a point toward the camera scales its projected x/y away from the
 * screen centre, so writing `position.z` directly would slide the point off the
 * element it belongs to. Travelling along the camera's own view ray cancels
 * that exactly: the point gains depth and keeps its place.
 */
function pushDepth(
  point: THREE.Vector3,
  camera: THREE.PerspectiveCamera,
  z: number,
): THREE.Vector3 {
  const direction = point.sub(camera.position).normalize();
  const distance = (camera.position.z - z) / -direction.z;
  return camera.position.clone().add(direction.multiplyScalar(distance));
}

/** Project a viewport coordinate onto the world plane at depth `z`. */
function toWorld(
  clientX: number,
  clientY: number,
  canvas: DOMRect,
  camera: THREE.PerspectiveCamera,
  z: number,
): THREE.Vector3 {
  const ndcX = ((clientX - canvas.left) / canvas.width) * 2 - 1;
  const ndcY = -(((clientY - canvas.top) / canvas.height) * 2 - 1);
  return pushDepth(new THREE.Vector3(ndcX, ndcY, 0.5).unproject(camera), camera, z);
}

/** The world-space centre of a DOM element, at depth `z`. */
function worldCentre(
  element: Element,
  canvas: DOMRect,
  camera: THREE.PerspectiveCamera,
  z: number,
): THREE.Vector3 {
  const rect = element.getBoundingClientRect();
  return toWorld(rect.left + rect.width / 2, rect.top + rect.height / 2, canvas, camera, z);
}

/** The world-space footprint of a DOM element, as an axis-aligned box. */
function worldBox(
  element: Element,
  canvas: DOMRect,
  camera: THREE.PerspectiveCamera,
  z: number,
): Box {
  const rect = element.getBoundingClientRect();
  const corners = [
    toWorld(rect.left, rect.top, canvas, camera, z),
    toWorld(rect.right, rect.bottom, canvas, camera, z),
  ];
  return {
    minX: Math.min(corners[0].x, corners[1].x),
    maxX: Math.max(corners[0].x, corners[1].x),
    minY: Math.min(corners[0].y, corners[1].y),
    maxY: Math.max(corners[0].y, corners[1].y),
  };
}

/**
 * The evidence chain as a 3D constellation woven between the cards.
 *
 * A decorative layer, never a second source of truth: the five `.evidence-node`
 * buttons and the `aria-live` detail panel keep every click, focus stop and
 * accessible name they had. The canvas is `aria-hidden` and
 * `pointer-events: none`, and only mounts above 1024px, so the SVG beneath
 * stays the real fallback — the same one mobile and reduced motion already get.
 *
 * Anchors are read from the DOM rather than hard-coded, so the strands cannot
 * drift away from the cards they connect. Every marker deliberately sits in the
 * open space short of the root card: the canvas paints beneath the DOM, so
 * anything further along would simply be hidden behind it.
 */
export default function EvidenceGraph3D({ selected }: { selected: number }) {
  const host = useRef<HTMLDivElement>(null);
  const graph = useRef<Graph | null>(null);
  const choice = useRef(selected);
  choice.current = selected;

  const controller = useThreeScene(
    host,
    {
      env: "graphite",
      pixelRatioCap: 1.4,
      rootMargin: "260px",
      pointerTarget: (element) => element.closest(".evidence-canvas") ?? element,
      init: ({ scene }) => {
        const group = new THREE.Group();
        const canvasRoot = host.current?.closest(".evidence-canvas");
        const cards = canvasRoot?.querySelectorAll(".evidence-node") ?? [];
        const slots: Slot[] = [];

        cards.forEach(() => {
          // One material set per marker: they are lit and tinted individually,
          // so sharing an instance would make every card fight over one colour.
          const strand = new THREE.Mesh(
            new THREE.BufferGeometry(),
            new THREE.MeshBasicMaterial({ color: STRAND_COLOR }),
          );
          // A twenty-face solid: an octahedron spins through a dead-flat square
          // whenever a vertex faces the camera, which reads as a plain quad
          // rather than a crystal. This one keeps a faceted silhouette at every
          // angle.
          const marker = new THREE.Mesh(
            new THREE.IcosahedronGeometry(0.155, 0),
            new THREE.MeshStandardMaterial({
              color: NODE_COLOR,
              metalness: 0.25,
              roughness: 0.32,
              flatShading: true,
              // The graphite environment is near-black, so an env-lit-only
              // marker disappears into it. This emissive base is what makes the
              // facet read; the environment supplies the per-face variation.
              emissive: new THREE.Color(NODE_COLOR),
              emissiveIntensity: 0.5,
            }),
          );
          const ring = new THREE.Mesh(
            new THREE.TorusGeometry(0.235, 0.007, 6, 44),
            new THREE.MeshBasicMaterial({ color: NODE_COLOR, transparent: true, opacity: 0.75 }),
          );
          // Tilted off edge-on: a ring square to the camera would read as a
          // flat circle, and square to the view plane as a bare line. This
          // angle shows the ellipse, so it reads as an orbit around the crystal.
          ring.rotation.x = 1.15;
          group.add(strand, marker, ring);
          slots.push({ strand, marker, ring, scale: 1 });
        });

        scene.add(group);
        graph.current = { group, slots, origins: [], focus: new THREE.Vector3() };
      },
      resize: (width, height, camera) => {
        const current = graph.current;
        const canvasRoot = host.current?.closest(".evidence-canvas");
        if (!current || !canvasRoot || !width || !height) return;

        // The factory calls `resize` before the first render, and three.js only
        // refreshes a camera's matrix inside `render`. Without this the very
        // first — and for a static host, only — anchoring unprojects through an
        // identity matrix and every point collapses toward the origin.
        camera.updateMatrixWorld();

        const box = canvasRoot.getBoundingClientRect();
        const cards = [...canvasRoot.querySelectorAll(".evidence-node")];
        const rootCard = canvasRoot.querySelector(".root-cause-card");

        current.focus = rootCard
          ? worldCentre(rootCard, box, camera, 0)
          : new THREE.Vector3();
        const card = rootCard ? worldBox(rootCard, box, camera, 0) : null;

        current.origins = cards.map((card_, index) =>
          worldCentre(card_, box, camera, -DEPTH_STEP * (index % 3)),
        );

        cards.forEach((_, index) => {
          const slot = current.slots[index];
          const from = current.origins[index];
          if (!slot || !from) return;

          const midpoint = from.clone().lerp(current.focus, 0.5);
          midpoint.y += (from.y - current.focus.y) * 0.16;
          const curve = new THREE.QuadraticBezierCurve3(from.clone(), midpoint, current.focus.clone());

          // Walk out along the strand and stop short of the root card, so the
          // marker lands in open space instead of behind the card.
          let seat = curve.getPointAt(0.3);
          for (let u = 0.3; u <= 0.62; u += 0.02) {
            const point = curve.getPointAt(u);
            const inside =
              card &&
              point.x > card.minX - CARD_MARGIN &&
              point.x < card.maxX + CARD_MARGIN &&
              point.y > card.minY - CARD_MARGIN &&
              point.y < card.maxY + CARD_MARGIN;
            if (inside) break;
            seat = point;
          }

          slot.strand.geometry.dispose();
          slot.strand.geometry = new THREE.TubeGeometry(curve, 48, 0.0075, 6, false);

          const placed = pushDepth(seat, camera, -DEPTH_STEP * (index % 3) + 0.22);
          slot.marker.position.copy(placed);
          slot.ring.position.copy(placed);
        });
      },
      update: ({ t, pointer, progress }) => {
        const current = graph.current;
        if (!current) return;
        const active = choice.current;

        // A shallow tilt on the whole constellation — enough to read as a
        // volume, not enough to break the alignment with the cards.
        current.group.rotation.y = pointer.x * 0.11;
        current.group.rotation.x = -pointer.y * 0.08;

        current.slots.forEach((slot, index) => {
          const isActive = index === active;

          // Only a partial shift: the crystal should still read as a lit
          // material, with the rest of the accent carried by its glow and its
          // orbit ring.
          slot.marker.material.color.lerp(isActive ? NODE_ACTIVE : NODE_BASE, 0.12);
          slot.marker.material.emissive.lerp(isActive ? EMISSIVE_ACTIVE : NODE_BASE, 0.12);
          // Held well below the tone mapper's ceiling: past roughly 1.4 the
          // emissive clips and the facet detail flattens into one solid colour.
          slot.marker.material.emissiveIntensity +=
            ((isActive ? 0.8 + progress * 0.25 : 0.5) - slot.marker.material.emissiveIntensity) * 0.1;
          slot.marker.rotation.y = t * 0.6 + index;
          slot.marker.rotation.x = t * 0.35;
          slot.scale += ((isActive ? 1.45 : 1) - slot.scale) * 0.12;
          slot.marker.scale.copy(ONE).multiplyScalar(slot.scale);

          // Precesses about the world Y, so the tilted ring tumbles rather than
          // spinning in place — a torus spun about its own axis shows nothing.
          slot.ring.rotation.y = t * (isActive ? 0.55 : 0.22) + index;
          slot.ring.material.color.lerp(isActive ? STRAND_HOT : NODE_BASE, 0.1);
          slot.ring.material.opacity += ((isActive ? 1 : 0.75) - slot.ring.material.opacity) * 0.1;

          slot.strand.material.color.lerp(isActive ? STRAND_HOT : STRAND_BASE, 0.1);

          // Each strand draws on in turn — the direct analogue of the SVG's
          // staggered stroke-dashoffset. Full draw lands just past halfway,
          // while the canvas is still centred.
          const geometry = slot.strand.geometry.getIndex();
          if (geometry) {
            const local = THREE.MathUtils.clamp((progress * 1.9 - index * 0.1) / 0.55, 0, 1);
            slot.strand.geometry.setDrawRange(0, Math.floor(geometry.count * local));
          }
        });
      },
      dispose: () => {
        graph.current = null;
      },
    },
    { enabled: true },
  );

  // No pin — the strand draw is scrubbed off the canvas's own travel, so the
  // page keeps exactly the two pin spacers it had before this component.
  useEffect(() => {
    const scene = controller.current;
    const canvasRoot = host.current?.closest(".evidence-canvas");
    if (!scene || !canvasRoot) return;
    let cancelled = false;
    let cleanup = () => {};
    void (async () => {
      const [{ gsap }, { ScrollTrigger }] = await Promise.all([
        import("gsap"),
        import("gsap/ScrollTrigger"),
      ]);
      if (cancelled) return;
      gsap.registerPlugin(ScrollTrigger);
      const trigger = ScrollTrigger.create({
        trigger: canvasRoot,
        start: "top 78%",
        end: "bottom 55%",
        invalidateOnRefresh: true,
        onUpdate: (self) => scene.progress.set(self.progress),
      });
      // `create` does not fire onUpdate for the position it starts at, so a
      // section already on screen when this mounts would stay at zero.
      scene.progress.set(trigger.progress);
      cleanup = () => trigger.kill();
    })();
    return () => {
      cancelled = true;
      cleanup();
    };
  }, [controller]);

  return <div className="evidence-3d" ref={host} />;
}
