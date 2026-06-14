import { useEffect, useRef, useState } from 'react';

export default function TextReveal({ text, delay = 0, duration = 1000, mode = 'word' }) {
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

  const words = text.split(' ');
  let charCounter = 0;

  return (
    <span 
      ref={ref} 
      style={{ 
        display: 'inline',
        whiteSpace: 'normal'
      }}
    >
      {words.map((word, wordIdx) => {
        if (mode === 'char') {
          const chars = Array.from(word);
          return (
            <span 
              key={wordIdx}
              style={{ 
                display: 'inline-block', 
                whiteSpace: 'nowrap',
                paddingRight: '0.22em',
                paddingBottom: '2px',
                verticalAlign: 'bottom'
              }}
            >
              {chars.map((char, charIdx) => {
                const currentDelay = delay + charCounter * 15;
                charCounter++;
                return (
                  <span
                    key={charIdx}
                    style={{
                      display: 'inline-block',
                      overflow: 'hidden',
                      verticalAlign: 'bottom'
                    }}
                  >
                    <span
                      style={{
                        display: 'inline-block',
                        transform: revealed ? 'translateY(0)' : 'translateY(105%)',
                        transition: `transform ${duration}ms cubic-bezier(0.16, 1, 0.3, 1)`,
                        transitionDelay: `${currentDelay}ms`,
                        willChange: 'transform'
                      }}
                    >
                      {char}
                    </span>
                  </span>
                );
              })}
              {/* If it's not the last word, render a spacer character inside the word container */}
              {wordIdx < words.length - 1 && chars.length === 0 && (
                <span style={{ display: 'inline-block' }}>&nbsp;</span>
              )}
            </span>
          );
        }

        // Default 'word' mode
        return (
          <span 
            key={wordIdx}
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
                transitionDelay: `${delay + wordIdx * 30}ms`,
                willChange: 'transform'
              }}
            >
              {word === '' ? '\u00A0' : word}
            </span>
          </span>
        );
      })}
    </span>
  );
}
