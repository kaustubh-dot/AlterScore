import Lenis from "lenis";
import { useEffect } from "react";
import { gsap } from "gsap";
import { ScrollTrigger } from "gsap/ScrollTrigger";
import { CustomEase } from "gsap/CustomEase";

gsap.registerPlugin(ScrollTrigger, CustomEase);

CustomEase.create("alterQuart", "0.76,0,0.24,1");

export default function useLenis(disabled = false) {
  useEffect(() => {
    if (disabled) return;
    const lenis = new Lenis({
      lerp: 0.05,          // Incredibly smooth, liquid inertial scroll glide
      duration: 1.8,       // Longer luxurious deceleration duration
      smoothWheel: true,
      wheelMultiplier: 0.95, // Soft, premium wheel scaling
    });

    const update = (time) => {
      lenis.raf(time * 1000);
    };

    lenis.on("scroll", ScrollTrigger.update);
    gsap.ticker.add(update);
    gsap.ticker.lagSmoothing(0);

    return () => {
      gsap.ticker.remove(update);
      lenis.destroy();
    };
  }, [disabled]);
}
