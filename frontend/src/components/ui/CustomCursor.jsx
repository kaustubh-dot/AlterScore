import { useEffect, useState, useRef } from 'react';
import './CustomCursor.css';

export default function CustomCursor({ variant = 'default' }) {
  const dotRef = useRef(null);
  const ringRef = useRef(null);
  const [hovered, setHovered] = useState(false);
  const [clicked, setClicked] = useState(false);
  const [hidden, setHidden] = useState(true);
  const [isFinePointer, setIsFinePointer] = useState(false);

  useEffect(() => {
    const pointerQuery = window.matchMedia('(pointer: fine)');
    const updatePointerMode = () => {
      setIsFinePointer(pointerQuery.matches && window.innerWidth > 768);
    };

    updatePointerMode();
    pointerQuery.addEventListener('change', updatePointerMode);
    window.addEventListener('resize', updatePointerMode);

    return () => {
      pointerQuery.removeEventListener('change', updatePointerMode);
      window.removeEventListener('resize', updatePointerMode);
    };
  }, []);

  useEffect(() => {
    if (!isFinePointer) {
      document.body.classList.remove('custom-cursor-active');
      return undefined;
    }

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
    const onTouchStart = () => {
      setHidden(true);
      setClicked(false);
    };

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
    window.addEventListener('touchstart', onTouchStart, { passive: true });

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
      window.removeEventListener('touchstart', onTouchStart);
      cancelAnimationFrame(animationFrameId);
      document.body.classList.remove('custom-cursor-active');
    };
  }, [isFinePointer]);

  // The assessment uses a minimalistic cursor: just the dot tracking the
  // pointer directly, with no animated trailing ring, for a calmer focus state.
  const minimal = variant === 'assessment';

  if (!isFinePointer) {
    return null;
  }

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
