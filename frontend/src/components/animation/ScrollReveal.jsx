import { useEffect, useRef, useState } from 'react';

export default function ScrollReveal({
  children,
  direction = 'up', // 'up' | 'scale' | 'left' | 'right'
  delay = 0,        // delay in ms
  duration = 800,   // duration in ms
  threshold = 0.15  // visibility threshold before triggering
}) {
  const ref = useRef(null);
  const [isRevealed, setIsRevealed] = useState(false);

  useEffect(() => {
    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting) {
          setIsRevealed(true);
          if (ref.current) {
            observer.unobserve(ref.current);
          }
        }
      },
      { threshold }
    );

    const currentRef = ref.current;
    if (currentRef) {
      observer.observe(currentRef);
    }

    return () => {
      if (currentRef) {
        observer.unobserve(currentRef);
      }
    };
  }, [threshold]);

  const style = {
    transitionDelay: `${delay}ms`,
    transitionDuration: `${duration}ms`
  };

  return (
    <div
      ref={ref}
      className={`reveal reveal-${direction} ${isRevealed ? 'reveal-active' : ''}`}
      style={style}
    >
      {children}
    </div>
  );
}
