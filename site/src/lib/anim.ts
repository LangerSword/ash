import { gsap } from "gsap";
import { ScrollTrigger } from "gsap/ScrollTrigger";

gsap.registerPlugin(ScrollTrigger);

export function prefersReduced(): boolean {
  return typeof window !== "undefined" && window.matchMedia("(prefers-reduced-motion: reduce)").matches;
}

export function reveal(node: HTMLElement, opts: { y?: number; delay?: number } = {}) {
  if (prefersReduced()) return;
  const tween = gsap.from(node, {
    opacity: 0,
    y: opts.y ?? 8,
    duration: 0.5,
    delay: opts.delay ?? 0,
    ease: "power2.out",
    scrollTrigger: { trigger: node, start: "top 85%", once: true },
  });
  return {
    destroy() {
      tween.scrollTrigger?.kill();
      tween.kill();
    },
  };
}

export function drawRule(node: HTMLElement) {
  if (prefersReduced()) return;
  const tween = gsap.from(node, {
    scaleX: 0,
    transformOrigin: "left center",
    duration: 0.7,
    ease: "power2.inOut",
    scrollTrigger: { trigger: node, start: "top 90%", once: true },
  });
  return {
    destroy() {
      tween.scrollTrigger?.kill();
      tween.kill();
    },
  };
}
