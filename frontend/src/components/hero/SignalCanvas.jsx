import React, { useEffect, useRef } from 'react';

export default function SignalCanvas() {
  const canvasRef = useRef(null);
  const mouseRef = useRef({ x: 0, y: 0, active: false, px: 0, py: 0 });
  const impulsesRef = useRef([]);

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

    // Handle Mouse Move
    const handleMouseMove = (e) => {
      mouseRef.current.px = mouseRef.current.x;
      mouseRef.current.py = mouseRef.current.y;
      mouseRef.current.x = e.clientX;
      mouseRef.current.y = e.clientY;
      mouseRef.current.active = true;
    };

    const handleMouseLeave = () => {
      mouseRef.current.active = false;
    };

    // Handle Click (Impulse ripple)
    const handleMouseClick = (e) => {
      impulsesRef.current.push({
        x: e.clientX,
        y: e.clientY,
        radius: 0,
        maxRadius: 180 + Math.random() * 80,
        opacity: 0.8,
        speed: 4 + Math.random() * 2,
        glyphs: Array.from({ length: 8 }, () => ({
          dx: (Math.random() - 0.5) * 50,
          dy: (Math.random() - 0.5) * 50,
          text: ['0', '1', 'CRT', 'NLP', 'Δ', 'ψ', '847', 'locus'][Math.floor(Math.random() * 8)],
        }))
      });
      // Limit total impulses
      if (impulsesRef.current.length > 5) {
        impulsesRef.current.shift();
      }
    };

    window.addEventListener('mousemove', handleMouseMove);
    window.addEventListener('mouseleave', handleMouseLeave);
    window.addEventListener('click', handleMouseClick);

    // Initialize Particles
    const particleCount = Math.min(Math.floor((width * height) / 10000), 150);
    const particles = Array.from({ length: particleCount }, () => ({
      x: Math.random() * width,
      y: Math.random() * height,
      vx: (Math.random() - 0.5) * 0.4,
      vy: (Math.random() - 0.5) * 0.4,
      radius: Math.random() * 1.2 + 0.6,
    }));

    // Initialize Glyphs
    const glyphTexts = ['CRT', 'NLP', 'locus', '0.72', '847', 'Δψ', '0.96', 'PSI', 'ROC', 'AUC', 'SHAP', 'DiCE'];
    const glyphs = Array.from({ length: 15 }, () => ({
      x: Math.random() * width,
      y: Math.random() * height,
      text: glyphTexts[Math.floor(Math.random() * glyphTexts.length)],
      opacity: Math.random() * 0.04 + 0.04,
      speed: Math.random() * 0.2 + 0.1,
      size: Math.floor(Math.random() * 3) + 9, // 9px to 11px
    }));

    // Waveform Settings
    const waveCount = 5;
    const waves = Array.from({ length: waveCount }, (_, i) => ({
      frequency: 0.002 + i * 0.001,
      amplitude: 25 + i * 12,
      speed: 0.015 - i * 0.002,
      phase: Math.random() * Math.PI * 2,
      y: height * 0.35 + (height * 0.3 * (i / waveCount)),
      alpha: 0.22 - i * 0.03,
    }));

    // Radar Scanline Settings
    let scanX = -100;
    const scanSpeed = 3.5;
    let timeSinceLastScan = 0;
    const scanInterval = 5000; // ms

    let lastTime = performance.now();

    // Render Loop
    const draw = (now) => {
      const delta = now - lastTime;
      lastTime = now;

      // Check prefers-reduced-motion
      if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
        ctx.fillStyle = '#020409';
        ctx.fillRect(0, 0, width, height);

        // Simple static radial glow
        const gradient = ctx.createRadialGradient(width / 2, height / 2, 50, width / 2, height / 2, width * 0.7);
        gradient.addColorStop(0, '#060B14');
        gradient.addColorStop(1, '#020409');
        ctx.fillStyle = gradient;
        ctx.fillRect(0, 0, width, height);
        return;
      }

      ctx.fillStyle = '#020409';
      ctx.fillRect(0, 0, width, height);

      // Subtle Center radial gradient glow
      const radialGlow = ctx.createRadialGradient(width / 2, height / 2, 0, width / 2, height / 2, width * 0.8);
      radialGlow.addColorStop(0, 'rgba(76, 110, 245, 0.04)');
      radialGlow.addColorStop(0.5, 'rgba(124, 58, 237, 0.015)');
      radialGlow.addColorStop(1, 'transparent');
      ctx.fillStyle = radialGlow;
      ctx.fillRect(0, 0, width, height);

      // Draw Particles & Connections
      ctx.strokeStyle = 'rgba(76, 110, 245, 0.04)';
      ctx.lineWidth = 0.8;
      particles.forEach((p, idx) => {
        // Move
        p.x += p.vx;
        p.y += p.vy;

        // Boundary bounce
        if (p.x < 0 || p.x > width) p.vx *= -1;
        if (p.y < 0 || p.y > height) p.vy *= -1;

        // Draw point
        ctx.beginPath();
        ctx.arc(p.x, p.y, p.radius, 0, Math.PI * 2);
        ctx.fillStyle = 'rgba(76, 110, 245, 0.15)';
        ctx.fill();

        // Connect to neighbors
        for (let j = idx + 1; j < particles.length; j++) {
          const p2 = particles[j];
          const distSq = (p.x - p2.x) ** 2 + (p.y - p2.y) ** 2;
          const maxDist = 90;
          if (distSq < maxDist * maxDist) {
            const dist = Math.sqrt(distSq);
            const alpha = (1 - dist / maxDist) * 0.09;
            
            // Mouse proximity highlights connections
            let hoverBonus = 0;
            if (mouseRef.current.active) {
              const mx = mouseRef.current.x;
              const my = mouseRef.current.y;
              const mDistSq1 = (p.x - mx) ** 2 + (p.y - my) ** 2;
              const mDistSq2 = (p2.x - mx) ** 2 + (p2.y - my) ** 2;
              if (mDistSq1 < 15000 || mDistSq2 < 15000) {
                hoverBonus = 0.12 * (1 - Math.min(mDistSq1, mDistSq2) / 15000);
              }
            }

            ctx.strokeStyle = `rgba(76, 110, 245, ${alpha + hoverBonus})`;
            ctx.beginPath();
            ctx.moveTo(p.x, p.y);
            ctx.lineTo(p2.x, p2.y);
            ctx.stroke();
          }
        }
      });

      // Draw Waveform Traces
      waves.forEach((w, idx) => {
        w.phase += w.speed;
        ctx.beginPath();
        ctx.lineWidth = idx === 0 ? 1.5 : 0.8;

        for (let x = 0; x < width; x += 4) {
          // Calculate standard sine wave
          let y = w.y + Math.sin(x * w.frequency + w.phase) * w.amplitude;

          // Mouse attraction/repulsion distortion
          if (mouseRef.current.active) {
            const mx = mouseRef.current.x;
            const my = mouseRef.current.y;
            const dx = x - mx;
            const dy = y - my;
            const dist = Math.sqrt(dx * dx + dy * dy);
            
            if (dist < 180) {
              // Lens/ripple distortion effect on the waves near mouse
              const strength = (1 - dist / 180) * 45;
              const angle = Math.atan2(dy, dx);
              y += Math.sin(angle) * strength;
            }
          }

          if (x === 0) {
            ctx.moveTo(x, y);
          } else {
            ctx.lineTo(x, y);
          }
        }

        const gradient = ctx.createLinearGradient(0, 0, width, 0);
        gradient.addColorStop(0, 'transparent');
        gradient.addColorStop(0.2, `rgba(76, 110, 245, ${w.alpha})`);
        gradient.addColorStop(0.5, `rgba(124, 58, 237, ${w.alpha * 1.2})`);
        gradient.addColorStop(0.8, `rgba(6, 182, 212, ${w.alpha})`);
        gradient.addColorStop(1, 'transparent');

        ctx.strokeStyle = gradient;
        ctx.stroke();
      });

      // Draw Floating Data Glyphs
      ctx.font = '500 10px JetBrains Mono';
      glyphs.forEach((g) => {
        g.x -= g.speed;
        if (g.x < -100) {
          g.x = width + 50;
          g.y = Math.random() * height;
        }

        // Draw glyph
        ctx.fillStyle = `rgba(125, 211, 252, ${g.opacity})`;
        ctx.fillText(g.text, g.x, g.y);
      });

      // Draw Impulse Ripples (Clicks)
      impulsesRef.current.forEach((imp, iIdx) => {
        imp.radius += imp.speed;
        imp.opacity -= 0.012;

        if (imp.opacity <= 0 || imp.radius >= imp.maxRadius) {
          // Mark for cleanup later
          return;
        }

        // Ripple ring
        ctx.strokeStyle = `rgba(76, 110, 245, ${imp.opacity * 0.4})`;
        ctx.lineWidth = 1.5;
        ctx.beginPath();
        ctx.arc(imp.x, imp.y, imp.radius, 0, Math.PI * 2);
        ctx.stroke();

        // Sub-ring
        ctx.strokeStyle = `rgba(6, 182, 212, ${imp.opacity * 0.2})`;
        ctx.lineWidth = 0.5;
        ctx.beginPath();
        ctx.arc(imp.x, imp.y, imp.radius * 0.7, 0, Math.PI * 2);
        ctx.stroke();

        // Expanding digital glyphs
        ctx.font = '7px JetBrains Mono';
        ctx.fillStyle = `rgba(16, 185, 129, ${imp.opacity * 0.7})`;
        imp.glyphs.forEach((gl) => {
          const gx = imp.x + gl.dx * (imp.radius / imp.maxRadius);
          const gy = imp.y + gl.dy * (imp.radius / imp.maxRadius);
          ctx.fillText(gl.text, gx, gy);
        });
      });
      // Remove dead impulses
      impulsesRef.current = impulsesRef.current.filter((imp) => imp.opacity > 0);

      // Draw Vertical Scan Line (Radar Sweep)
      timeSinceLastScan += delta;
      if (timeSinceLastScan >= scanInterval && scanX < -50) {
        scanX = -50;
        timeSinceLastScan = 0;
      }

      if (scanX >= -50 && scanX < width + 100) {
        scanX += scanSpeed;

        const scanGlow = ctx.createLinearGradient(scanX - 50, 0, scanX + 2, 0);
        scanGlow.addColorStop(0, 'transparent');
        scanGlow.addColorStop(0.8, 'rgba(76, 110, 245, 0.05)');
        scanGlow.addColorStop(1, 'rgba(6, 182, 212, 0.25)');

        ctx.fillStyle = scanGlow;
        ctx.fillRect(scanX - 50, 0, 52, height);

        // Core bright line
        ctx.fillStyle = 'rgba(6, 182, 212, 0.7)';
        ctx.fillRect(scanX, 0, 1.5, height);
      } else {
        scanX = -100; // Reset
      }

      animationId = requestAnimationFrame(draw);
    };

    animationId = requestAnimationFrame(draw);

    return () => {
      cancelAnimationFrame(animationId);
      window.removeEventListener('resize', handleResize);
      window.removeEventListener('mousemove', handleMouseMove);
      window.removeEventListener('mouseleave', handleMouseLeave);
      window.removeEventListener('click', handleMouseClick);
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
