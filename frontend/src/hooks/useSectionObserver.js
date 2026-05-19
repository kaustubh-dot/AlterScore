import { useEffect } from "react";

export default function useSectionObserver(dependencyKey = "") {
  useEffect(() => {
    let observer;

    const timer = window.setTimeout(() => {
      const sections = Array.from(document.querySelectorAll("[data-section]"));
      observer = new IntersectionObserver(
        (entries) => {
          entries.forEach((entry) => {
            if (entry.isIntersecting) entry.target.classList.add("in-view");
          });
        },
        { threshold: 0.2 },
      );

      sections.forEach((section) => observer.observe(section));
    }, 40);

    return () => {
      window.clearTimeout(timer);
      observer?.disconnect();
    };
  }, [dependencyKey]);
}
