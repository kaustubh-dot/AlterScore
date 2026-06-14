import { useEffect, useRef, useState } from 'react';

export default function TextReveal({ text, delay = 0, duration = 1000 }) {
  const ref = useRef(null);
  const [revealed, setRevealed] = useState(false);

  useEffect(() => {
    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting) {
          setRevealed(true);
          if (ref.current) {
            observer.unobserve(ref.current);
          }
        }
      },
      { threshold: 0.05 }
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
  }, []);

  // Split string by spaces to handle wrapping and staggering word by word
  const words = text.split(' ');

  return (
    <span 
      ref={ref} 
      style={{ 
        display: 'inline',
        whiteSpace: 'normal'
      }}
    >
      {words.map((word, idx) => (
        <span 
          key={idx}
          style={{ 
            display: 'inline-block', 
            overflow: 'hidden', 
            verticalAlign: 'bottom',
            paddingRight: '0.22em',
            paddingBottom: '2px'
          }}
        >
          <span 
            style={{
              display: 'inline-block',
              transform: revealed ? 'translateY(0)' : 'translateY(105%)',
              transition: `transform ${duration}ms cubic-bezier(0.16, 1, 0.3, 1)`,
              transitionDelay: `${delay + idx * 30}ms`,
              willChange: 'transform'
            }}
          >
            {word === '' ? '\u00A0' : word}
          </span>
        </span>
      ))}
    </span>
  );
}
