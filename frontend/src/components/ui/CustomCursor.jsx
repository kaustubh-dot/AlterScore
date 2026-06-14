import { useEffect, useState, useRef } from 'react';
import './CustomCursor.css';

export default function CustomCursor() {
  const dotRef = useRef(null);
  const ringRef = useRef(null);
  const [hovered, setHovered] = useState(false);
  const [clicked, setClicked] = useState(false);
  const [hidden, setHidden] = useState(true);

  useEffect(() => {
    let mouseX = 0, mouseY = 0;
    let ringX = 0, ringY = 0;

    // Hide the native cursor only while this component is mounted. The matching
    // `cursor: none` rule is scoped to this class so routes that don't render
    // the custom cursor (e.g. the assessment flow) keep the normal pointer.
    document.body.classList.add('custom-cursor-active');

    const onMouseMove = (e) => {
      mouseX = e.clientX;
      mouseY = e.clientY;
      setHidden(false);
      
      if (dotRef.current) {
        dotRef.current.style.transform = `translate3d(${mouseX}px, ${mouseY}px, 0) translate(-50%, -50%)`;
      }
    };

    const onMouseDown = () => setClicked(true);
    const onMouseUp = () => setClicked(false);
    const onMouseEnter = () => setHidden(false);
    const onMouseLeave = () => setHidden(true);

    window.addEventListener('mousemove', onMouseMove);
    window.addEventListener('mousedown', onMouseDown);
    window.addEventListener('mouseup', onMouseUp);
    document.addEventListener('mouseenter', onMouseEnter);
    document.addEventListener('mouseleave', onMouseLeave);

    const addHoverListeners = () => {
      const targets = document.querySelectorAll('a, button, [role="button"], input, select, textarea, .option-pill, .scenario-pill, .likert-option, .badge-tag, .btn, .option-pill-btn');
      targets.forEach(t => {
        t.addEventListener('mouseenter', () => setHovered(true));
        t.addEventListener('mouseleave', () => setHovered(false));
      });
    };

    addHoverListeners();
    const interval = setInterval(addHoverListeners, 1000);

    let animationFrameId;
    const render = () => {
      ringX += (mouseX - ringX) * 0.16;
      ringY += (mouseY - ringY) * 0.16;

      if (ringRef.current) {
        ringRef.current.style.transform = `translate3d(${ringX}px, ${ringY}px, 0) translate(-50%, -50%)`;
      }

      animationFrameId = requestAnimationFrame(render);
    };
    render();

    return () => {
      window.removeEventListener('mousemove', onMouseMove);
      window.removeEventListener('mousedown', onMouseDown);
      window.removeEventListener('mouseup', onMouseUp);
      document.removeEventListener('mouseenter', onMouseEnter);
      document.removeEventListener('mouseleave', onMouseLeave);
      cancelAnimationFrame(animationFrameId);
      clearInterval(interval);
      document.body.classList.remove('custom-cursor-active');
    };
  }, []);

  return (
    <>
      <div 
        ref={dotRef} 
        className={`cursor-dot ${hidden ? 'hidden' : ''} ${hovered ? 'hover' : ''} ${clicked ? 'active' : ''}`} 
      />
      <div 
        ref={ringRef} 
        className={`cursor-ring ${hidden ? 'hidden' : ''} ${hovered ? 'hover' : ''} ${clicked ? 'active' : ''}`} 
      >
        <div className="cursor-ring-inner" />
      </div>
    </>
  );
}
