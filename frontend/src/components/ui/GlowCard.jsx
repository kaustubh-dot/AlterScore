import { useRef, useState } from 'react';
import './GlowCard.css';

export default function GlowCard({ children, className = '', ...props }) {
  const ref = useRef(null);
  const [coords, setCoords] = useState({ x: 0, y: 0 });
  const [isHovered, setIsHovered] = useState(false);

  const handleMouseMove = (e) => {
    if (!ref.current) return;
    const { left, top } = ref.current.getBoundingClientRect();
    setCoords({
      x: e.clientX - left,
      y: e.clientY - top
    });
  };

  const style = {
    '--mouse-x': `${coords.x}px`,
    '--mouse-y': `${coords.y}px`
  };

  return (
    <div
      ref={ref}
      className={`glow-card glass ${isHovered ? 'glow-card-hover' : ''} ${className}`}
      onMouseMove={handleMouseMove}
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
      style={style}
      {...props}
    >
      <div
        className="glow-card-spotlight"
        style={{
          left: `${coords.x}px`,
          top: `${coords.y}px`
        }}
      />
      <div className="glow-card-content">{children}</div>
    </div>
  );
}
