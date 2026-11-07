// Split a heading into words and reveal them on enter, once.
// Skips headings that contain markup (e.g. a <br>) so the line breaks stay intact.
export function words(node: HTMLElement) {
  const onlyText = [...node.childNodes].every((n) => n.nodeType === Node.TEXT_NODE);
  if (!onlyText) return { destroy() {} };

  const text = node.textContent ?? "";
  const parts = text.split(/(\s+)/);
  node.textContent = "";
  const spans: HTMLSpanElement[] = [];

  for (const part of parts) {
    if (/^\s+$/.test(part)) {
      node.appendChild(document.createTextNode(part));
      continue;
    }
    const outer = document.createElement("span");
    outer.style.display = "inline-block";
    outer.style.overflow = "hidden";
    outer.style.verticalAlign = "top";
    const inner = document.createElement("span");
    inner.style.display = "inline-block";
    inner.style.willChange = "transform";
    inner.textContent = part;
    outer.appendChild(inner);
    node.appendChild(outer);
    spans.push(inner);
  }

  if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) {
    return { destroy() {} };
  }

  let killed = false;
  let ctx: { revert: () => void } | null = null;

  void (async () => {
    const gsapMod = await import("gsap");
    const stMod = await import("gsap/ScrollTrigger");
    if (killed) return;
    const gsap = gsapMod.gsap ?? gsapMod.default;
    const ScrollTrigger = stMod.ScrollTrigger ?? stMod.default;
    gsap.registerPlugin(ScrollTrigger);

    ctx = gsap.context(() => {
      gsap.fromTo(
        spans,
        { yPercent: 110 },
        {
          yPercent: 0,
          duration: 0.7,
          ease: "power3.out",
          stagger: 0.045,
          scrollTrigger: { trigger: node, start: "top 88%", once: true },
        },
      );
    }, node);
  })();

  return {
    destroy() {
      killed = true;
      ctx?.revert();
    },
  };
}
