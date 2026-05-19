import { useEffect } from "react";
import { gsap } from "gsap";

export default function useMagneticButton(selector = "[data-magnetic]") {
  useEffect(() => {
    const elements = Array.from(document.querySelectorAll(selector));
    const cleanups = [];

    elements.forEach((element) => {
      const move = (event) => {
        const rect = element.getBoundingClientRect();
        const x = event.clientX - (rect.left + rect.width / 2);
        const y = event.clientY - (rect.top + rect.height / 2);
        const distance = Math.hypot(x, y);
        if (distance > 80) return;

        gsap.to(element, {
          x: Math.max(-8, Math.min(8, x * 0.12)),
          y: Math.max(-8, Math.min(8, y * 0.12)),
          duration: 0.28,
          ease: "power3.out",
        });
      };

      const leave = () => {
        gsap.to(element, {
          x: 0,
          y: 0,
          duration: 0.65,
          ease: "elastic.out(1, 0.38)",
        });
      };

      element.addEventListener("mousemove", move);
      element.addEventListener("mouseleave", leave);
      cleanups.push(() => {
        element.removeEventListener("mousemove", move);
        element.removeEventListener("mouseleave", leave);
      });
    });

    return () => cleanups.forEach((cleanup) => cleanup());
  });
}
