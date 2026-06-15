import { useEffect, useState, useRef } from 'react';
import './CustomCursor.css';

export default function CustomCursor({ variant = 'default' }) {
  const dotRef = useRef(null);
  const ringRef = useRef(null);
  const [hovered, setHovered] = useState(false);
  const [clicked, setClicked] = useState(false);
  const [hidden, setHidden] = useState(true);

  useEffect(() => {
    let mouseX = 0, mouseY = 0;
    let ringX = 0, ringY = 0;

    // Hide the native cursor only while this component is mounted; the matching
    // `cursor: none` rule is scoped to this class.
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

    const onMouseOver = (e) => {
      const target = e.target.closest('a, button, [role="button"], input, select, textarea, .option-pill, .scenario-pill, .likert-option, .badge-tag, .btn, .option-pill-btn');
      setHovered(!!target);
    };

    window.addEventListener('mousemove', onMouseMove);
    window.addEventListener('mousedown', onMouseDown);
    window.addEventListener('mouseup', onMouseUp);
    document.addEventListener('mouseenter', onMouseEnter);
    document.addEventListener('mouseleave', onMouseLeave);
    window.addEventListener('mouseover', onMouseOver);

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
      window.removeEventListener('mouseover', onMouseOver);
      cancelAnimationFrame(animationFrameId);
      document.body.classList.remove('custom-cursor-active');
    };
  }, []);

  // The assessment uses a minimalistic cursor: just the dot tracking the
  // pointer directly, with no animated trailing ring, for a calmer focus state.
  const minimal = variant === 'assessment';

  return (
    <>
      <div
        ref={dotRef}
        className={`cursor-dot ${variant} ${hidden ? 'hidden' : ''} ${hovered ? 'hover' : ''} ${clicked ? 'active' : ''}`}
      />
      {!minimal && (
        <div
          ref={ringRef}
          className={`cursor-ring ${variant} ${hidden ? 'hidden' : ''} ${hovered ? 'hover' : ''} ${clicked ? 'active' : ''}`}
        >
          <div className="cursor-ring-inner" />
        </div>
      )}
    </>
  );
}
