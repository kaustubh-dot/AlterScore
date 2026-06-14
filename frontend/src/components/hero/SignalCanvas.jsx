import { useEffect, useRef } from 'react';

export default function SignalCanvas() {
  const canvasRef = useRef(null);
  const mouseRef = useRef({ x: 0, y: 0, targetX: 0, targetY: 0, active: false });

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    let animationId;
    let width = (canvas.width = window.innerWidth);
    let height = (canvas.height = window.innerHeight);

    // Handle Resize
    const handleResize = () => {
      width = canvas.width = window.innerWidth;
      height = canvas.height = window.innerHeight;
    };
    window.addEventListener('resize', handleResize);

    // Track Mouse Coordinates
    const handleMouseMove = (e) => {
      mouseRef.current.targetX = e.clientX;
      mouseRef.current.targetY = e.clientY;
      mouseRef.current.active = true;
    };

    const handleMouseLeave = () => {
      mouseRef.current.active = false;
    };

    window.addEventListener('mousemove', handleMouseMove);
    window.addEventListener('mouseleave', handleMouseLeave);

    // Particles array (subtle, monochrome data points)
    const particles = Array.from({ length: 45 }, () => ({
      x: Math.random() * width,
      y: Math.random() * height,
      vx: (Math.random() - 0.5) * 0.15,
      vy: (Math.random() - 0.5) * 0.15,
      radius: Math.random() * 1.0 + 0.3,
    }));

    let time = 0;

    // Render loop
    const draw = () => {
      // Check reduced motion preference
      if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
        ctx.fillStyle = '#080809';
        ctx.fillRect(0, 0, width, height);
        return;
      }

      ctx.fillStyle = '#080809';
      ctx.fillRect(0, 0, width, height);

      // Lerp mouse coordinates for smooth inertia trail
      const m = mouseRef.current;
      m.x += (m.targetX - m.x) * 0.08;
      m.y += (m.targetY - m.y) * 0.08;

      time += 0.004;

      // 1. Draw Subtle Drafting Grid Layout
      ctx.strokeStyle = 'rgba(255, 255, 255, 0.012)';
      ctx.lineWidth = 0.5;
      const gridSize = 120;
      
      // Calculate mouse-offset for parallax grid shift
      const gridOffsetX = m.active ? (m.x - width / 2) * 0.015 : 0;
      const gridOffsetY = m.active ? (m.y - height / 2) * 0.015 : 0;

      // Vertical lines
      for (let x = gridOffsetX % gridSize; x < width; x += gridSize) {
        ctx.beginPath();
        ctx.moveTo(x, 0);
        ctx.lineTo(x, height);
        ctx.stroke();
      }
      // Horizontal lines
      for (let y = gridOffsetY % gridSize; y < height; y += gridSize) {
        ctx.beginPath();
        ctx.moveTo(0, y);
        ctx.lineTo(width, y);
        ctx.stroke();
      }

      // 2. Draw Scientific Waveforms (Cognitive Signal Traces)
      const waveCount = 2;
      for (let w = 0; w < waveCount; w++) {
        ctx.beginPath();
        ctx.lineWidth = w === 0 ? 0.7 : 0.4;
        
        const phaseShift = w * Math.PI;
        const amplitude = w === 0 ? 32 : 16;
        const frequency = w === 0 ? 0.002 : 0.0035;
        const waveSpeed = w === 0 ? 0.8 : 1.2;

        for (let x = 0; x < width; x += 5) {
          // Standard wave equation
          let sineY = height * 0.5 + Math.sin(x * frequency + time * waveSpeed + phaseShift) * amplitude;
          
          // Mouse proximity deformation: wave bends slightly around mouse
          if (m.active) {
            const dx = x - m.x;
            const dy = sineY - m.y;
            const dist = Math.sqrt(dx * dx + dy * dy);
            if (dist < 200) {
              const force = (1 - dist / 200) * 30;
              const angle = Math.atan2(dy, dx);
              sineY += Math.sin(angle) * force;
            }
          }

          if (x === 0) {
            ctx.moveTo(x, sineY);
          } else {
            ctx.lineTo(x, sineY);
          }
        }
        
        ctx.strokeStyle = w === 0 ? 'rgba(255, 255, 255, 0.04)' : 'rgba(255, 255, 255, 0.02)';
        ctx.stroke();
      }

      // 3. Draw Floating Micro-particles with inertia
      particles.forEach((p) => {
        p.x += p.vx;
        p.y += p.vy;

        // Wrap around screen edges
        if (p.x < 0) p.x = width;
        if (p.x > width) p.x = 0;
        if (p.y < 0) p.y = height;
        if (p.y > height) p.y = 0;

        // Mouse displacement
        if (m.active) {
          const dx = p.x - m.x;
          const dy = p.y - m.y;
          const dist = Math.sqrt(dx * dx + dy * dy);
          if (dist < 120) {
            const force = (1 - dist / 120) * 1.2;
            const angle = Math.atan2(dy, dx);
            p.x += Math.cos(angle) * force;
            p.y += Math.sin(angle) * force;
          }
        }

        ctx.beginPath();
        ctx.arc(p.x, p.y, p.radius, 0, Math.PI * 2);
        ctx.fillStyle = 'rgba(255, 255, 255, 0.1)';
        ctx.fill();
      });

      animationId = requestAnimationFrame(draw);
    };

    animationId = requestAnimationFrame(draw);

    return () => {
      cancelAnimationFrame(animationId);
      window.removeEventListener('resize', handleResize);
      window.removeEventListener('mousemove', handleMouseMove);
      window.removeEventListener('mouseleave', handleMouseLeave);
    };
  }, []);

  return (
    <canvas
      ref={canvasRef}
      style={{
        position: 'absolute',
        top: 0,
        left: 0,
        width: '100%',
        height: '100%',
        display: 'block',
        pointerEvents: 'none',
        zIndex: 0,
      }}
    />
  );
}
