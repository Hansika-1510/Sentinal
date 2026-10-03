"use client";

import { useRef } from "react";
import * as THREE from "three";
import { useThreeScene } from "@/lib/three/use-three-scene";

// This scene sits on the beige system panel, not the page ground, so it keeps
// the panel plane's dark values: BASE is that plane's --line, LIVE its plum
// accent. Only the rail's host changed — the section used to repaint itself
// with the page ground and now inherits the beige — so the values stay, and
// they are the ones the beige panel has always used.
const BASE_COLOR = 0x243a56;
const ACCENT = 0x4d3c60;
/** Matches `.route-base`'s 1px hairline once projected. */
const RAIL_RADIUS = 0.016;
/** Slightly fatter than the base, so the live run reads as the emphasised one. */
const LIVE_RADIUS = 0.026;
/** How far each anchor weaves along the view axis, in world units. */
const WEAVE = 0.62;
const HEAD_RADIUS = 0.09;

const BASE = new THREE.Color(BASE_COLOR);
const LIVE = new THREE.Color(ACCENT);

type Rail = {
  group: THREE.Group;
  base: THREE.Mesh<THREE.BufferGeometry, THREE.MeshBasicMaterial>;
  live: THREE.Mesh<THREE.BufferGeometry, THREE.MeshBasicMaterial>;
  head: THREE.Mesh<THREE.SphereGeometry, THREE.MeshBasicMaterial>;
  halo: THREE.Mesh<THREE.SphereGeometry, THREE.MeshBasicMaterial>;
  curve: THREE.CatmullRomCurve3 | null;
  /** Damped follow of the active step, 0..1 along the rail. */
  drawn: number;
  head0: THREE.Vector3;
};

/**
 * Move a point along the view axis while holding its screen position.
 *
 * Weaving the rail in depth is what makes it read as a physical wire rather
 * than a stroked path — but writing `position.z` alone would scale the
 * projected x/y away from the screen centre and slide the rail off the icons.
 * Travelling along the camera's own view ray cancels that exactly.
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

/**
 * The incident lifecycle as a 3D rail threaded through the node icons.
 *
 * A decorative layer, never a second source of truth: the thirteen
 * `.system-node` buttons keep every click, focus stop and accessible name, and
 * `#platform button` still resolves as before. The canvas is `aria-hidden` and
 * `pointer-events: none`, and mounts only above 1024px outside reduced motion,
 * so `.system-wiring` stays the real fallback for every other case.
 *
 * Anchors are measured from the DOM, so the rail cannot drift from the icons it
 * threads. Each anchor is then woven along the view axis with the projection
 * compensated, which leaves the screen path untouched while giving the rail real
 * depth: it swells toward the camera and recedes behind the icons it passes.
 */
export default function JourneyRoute3D({ active }: { active: number }) {
  const host = useRef<HTMLDivElement>(null);
  const rail = useRef<Rail | null>(null);
  const choice = useRef(active);
  choice.current = active;

  useThreeScene(
    host,
    {
      env: "graphite",
      rootMargin: "260px",
      pointerTarget: (element) => element.closest(".system-map") ?? element,
      init: ({ scene }) => {
        const group = new THREE.Group();
        const base = new THREE.Mesh(
          new THREE.BufferGeometry(),
          new THREE.MeshBasicMaterial({ color: BASE }),
        );
        const live = new THREE.Mesh(
          new THREE.BufferGeometry(),
          new THREE.MeshBasicMaterial({ color: LIVE }),
        );
        const head = new THREE.Mesh(
          new THREE.SphereGeometry(HEAD_RADIUS, 16, 12),
          new THREE.MeshBasicMaterial({ color: LIVE }),
        );
        const halo = new THREE.Mesh(
          new THREE.SphereGeometry(HEAD_RADIUS * 2.6, 16, 12),
          new THREE.MeshBasicMaterial({ color: LIVE, transparent: true, opacity: 0.16 }),
        );
        group.add(base, live, head, halo);
        scene.add(group);
        rail.current = {
          group,
          base,
          live,
          head,
          halo,
          curve: null,
          drawn: 0,
          head0: new THREE.Vector3(),
        };
      },
      resize: (width, height, camera) => {
        const current = rail.current;
        const root = host.current?.closest(".system-map");
        if (!current || !root || !width || !height) return;

        // The factory calls `resize` before the first render, and three.js only
        // refreshes a camera's matrix inside `render`. Without this the first
        // anchoring unprojects through an identity matrix and collapses.
        camera.updateMatrixWorld();

        const box = root.getBoundingClientRect();
        const icons = [...root.querySelectorAll(".system-node .node-icon")];
        if (icons.length < 2) return;

        const anchors = icons.map((icon, index) => {
          const rect = icon.getBoundingClientRect();
          return toWorld(
            rect.left + rect.width / 2,
            rect.top + rect.height / 2,
            box,
            camera,
            Math.sin(index * 0.62) * WEAVE,
          );
        });

        const curve = new THREE.CatmullRomCurve3(anchors, false, "centripetal", 0.5);
        current.curve = curve;

        current.base.geometry.dispose();
        current.base.geometry = new THREE.TubeGeometry(curve, 300, RAIL_RADIUS, 6, false);
        current.live.geometry.dispose();
        current.live.geometry = new THREE.TubeGeometry(curve, 300, LIVE_RADIUS, 6, false);

        current.drawn = 0;
      },
      update: ({ t, pointer }) => {
        const current = rail.current;
        if (!current?.curve) return;

        // A shallow tilt on the whole rail — enough to read as a volume, not
        // enough to break the thread through the icons.
        current.group.rotation.y = pointer.x * 0.06;
        current.group.rotation.x = -pointer.y * 0.05;

        // Same 13-step semantics as the SVG's `strokeDashoffset: 1 - (n+1)/13`,
        // but damped so the head glides between steps instead of snapping.
        const nodes = current.curve.points.length;
        const target = (choice.current + 1) / nodes;
        current.drawn += (target - current.drawn) * 0.12;

        const geometry = current.live.geometry.getIndex();
        if (geometry) {
          current.live.geometry.setDrawRange(0, Math.floor(geometry.count * current.drawn));
        }

        current.curve.getPointAt(Math.min(1, current.drawn), current.head0);
        current.head.position.copy(current.head0);
        current.halo.position.copy(current.head0);

        const pulse = 1 + Math.sin(t * 2.2) * 0.12;
        current.head.scale.setScalar(pulse);
        current.halo.scale.setScalar(pulse * (1 + Math.sin(t * 1.3) * 0.06));
      },
      dispose: () => {
        rail.current = null;
      },
    },
    { enabled: true },
  );

  return <div className="journey-3d" ref={host} />;
}
