"use client";

import { useEffect, useRef } from "react";
import type * as THREE from "three";
import { useReducedMotion } from "@/lib/use-reduced-motion";
import { useThreeScene } from "@/lib/three/use-three-scene";
import { createLensSculpture, LENS_REST, type LensSculpture } from "@/lib/three/lens-sculpture";
import { sampleLens, type LensState } from "@/lib/three/lens-states";
import { createLensCoreMaterial, type LensCoreUniforms } from "@/lib/three/lens-core-material";

// Sentinel's signal lens. On desktop, without reduced motion, the hero scroll
// poses it: the sculpture opens up, the core brightens, the camera pushes in,
// and it settles again as the story moves on. Reduced motion and mobile never
// mount this component — they keep the static WebP poster.
export default function SignalLens({ onReady }: { onReady: () => void }) {
  const host = useRef<HTMLDivElement>(null);
  const reduced = useReducedMotion();
  const ready = useRef(onReady);
  ready.current = onReady;

  const sculpture = useRef<LensSculpture | null>(null);
  const uniforms = useRef<LensCoreUniforms | null>(null);
  const camera = useRef<THREE.PerspectiveCamera | null>(null);
  const pose = useRef<LensState>(sampleLens(0));

  const controller = useThreeScene(
    host,
    {
      env: "studio",
      rootMargin: "100px",
      pointerTarget: (element) => element.closest(".hero-signal") ?? element,
      init: ({ scene, camera: view }) => {
        const lens = createLensSculpture();
        const core = createLensCoreMaterial();
        lens.core.material = core.material;
        camera.current = view;
        uniforms.current = core.uniforms;
        sculpture.current = lens;
        scene.add(lens.group);
        lens.lights.forEach((light) => scene.add(light));
      },
      update: ({ t, pointer, progress }) => {
        const lens = sculpture.current;
        const core = uniforms.current;
        if (!lens || !core) return;

        // The scroll pose is damped toward its target so scrubbing reads as a
        // continuous morph rather than a jump between keyframes.
        const target = sampleLens(progress);
        const current = pose.current;
        for (const key of Object.keys(current) as (keyof LensState)[]) {
          current[key] += (target[key] - current[key]) * 0.12;
        }

        lens.group.scale.setScalar(current.bodyScale);
        lens.rings.scale.setScalar(current.ringScale);
        lens.blades.scale.setScalar(current.bladeScale);
        lens.core.scale.setScalar(current.coreScale);
        lens.arc.scale.setScalar(current.arcScale);
        lens.arc.rotation.z = -1.43 + current.arcSpin;
        lens.ticks.rotation.z = current.tickSpin;
        lens.materials.accent.emissiveIntensity = current.emissive;

        core.uTime.value = t;
        core.uProgress.value = current.coreProgress;
        core.uEmissive.value = current.emissive;

        const point = lens.lights[1] as THREE.PointLight;
        point.intensity = 14 * (1 + current.coreProgress * 1.1);

        if (camera.current) camera.current.position.z = current.cameraZ;

        // Pointer parallax and idle drift, unchanged from the resting sculpture.
        lens.group.rotation.y +=
          (LENS_REST.y + pointer.x * 0.28 + Math.sin(t * 0.22) * 0.08 - lens.group.rotation.y) *
          0.035;
        lens.group.rotation.x += (LENS_REST.x - pointer.y * 0.2 - lens.group.rotation.x) * 0.035;
        lens.group.position.y = Math.sin(t * 0.45) * 0.055;
        lens.innerArc.rotation.z = 0.9 + t * 0.075;
        lens.core.rotation.z = t * 0.18;
      },
      dispose: () => {
        sculpture.current = null;
        uniforms.current = null;
        camera.current = null;
      },
      onReady: () => ready.current(),
    },
    { enabled: true },
  );

  // Drive the pose from the hero's scroll. No pin, so this adds no pin spacer.
  //
  // The range is deliberately short. The lens is roughly a viewport tall, so a
  // morph spread across the hero's full exit would play its most dramatic
  // states below the fold — the arc has to finish while the core is still on
  // screen. At ~44% of the viewport the core is just leaving; everything before
  // that is visible.
  useEffect(() => {
    if (reduced) return;
    const hero = host.current?.closest(".hero");
    const scene = controller.current;
    if (!hero || !scene) return;
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
        trigger: hero,
        start: "top top",
        end: "+=44%",
        invalidateOnRefresh: true,
        onUpdate: (self) => scene.progress.set(self.progress),
      });
      cleanup = () => trigger.kill();
    })();
    return () => {
      cancelled = true;
      cleanup();
    };
  }, [reduced, controller]);

  return <div className="lens-canvas" ref={host} />;
}
