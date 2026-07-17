import { useRef, useState } from 'react';
import useSound from '../../hooks/useSound';
import { prefersReducedMotion } from '../../lib/motionPreferences';

export default function MagneticButton({
  children,
  onClick,
  className = '',
  disabled = false,
  variant = 'primary', // 'primary' | 'ghost'
  type = 'button',
  ...props
}) {
  const ref = useRef(null);
  const [position, setPosition] = useState({ x: 0, y: 0 });
  const { playClick, playHover } = useSound();

  const handleMouseMove = (e) => {
    if (disabled || prefersReducedMotion() || !ref.current) return;
    const { clientX, clientY } = e;
    const { left, top, width, height } = ref.current.getBoundingClientRect();
    const x = clientX - (left + width / 2);
    const y = clientY - (top + height / 2);
    
    // Magnetic pull ratio: move up to 25% of distance
    const factor = 0.22;
    setPosition({ x: x * factor, y: y * factor });
  };

  const handleMouseLeave = () => {
    setPosition({ x: 0, y: 0 });
  };

  const handleMouseEnter = () => {
    if (!disabled) {
      playHover();
    }
  };

  const handleClick = (e) => {
    if (!disabled) {
      playClick();
      if (onClick) {
        onClick(e);
      }
    }
  };

  const isIdle = position.x === 0 && position.y === 0;
  const reducedMotion = prefersReducedMotion();
  const style = {
    transform: reducedMotion ? 'none' : `translate3d(${position.x}px, ${position.y}px, 0)`,
    transition: reducedMotion ? 'none' : isIdle
      ? 'transform var(--duration-normal) var(--ease-spring)'
      : 'transform 100ms cubic-bezier(0.25, 1, 0.5, 1)',
    willChange: reducedMotion ? 'auto' : 'transform'
  };

  return (
    <button
      ref={ref}
      type={type}
      className={`btn btn-${variant} ${className}`}
      onClick={handleClick}
      onMouseEnter={handleMouseEnter}
      disabled={disabled}
      onMouseMove={handleMouseMove}
      onMouseLeave={handleMouseLeave}
      style={style}
      {...props}
    >
      {children}
    </button>
  );
}
