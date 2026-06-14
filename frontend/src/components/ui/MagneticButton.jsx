import { useRef, useState } from 'react';

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

  const handleMouseMove = (e) => {
    if (disabled || !ref.current) return;
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

  const isIdle = position.x === 0 && position.y === 0;
  const style = {
    transform: `translate3d(${position.x}px, ${position.y}px, 0)`,
    transition: isIdle
      ? 'transform var(--duration-normal) var(--ease-spring)'
      : 'transform 100ms cubic-bezier(0.25, 1, 0.5, 1)',
    willChange: 'transform'
  };

  return (
    <button
      ref={ref}
      type={type}
      className={`btn btn-${variant} ${className}`}
      onClick={onClick}
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
