import { useEffect, useRef } from "react";

const GLASS_PANES = [
  { x: 0.57, y: 0.14, w: 0.34, h: 0.34, depth: 1.1 },
  { x: 0.08, y: 0.5, w: 0.28, h: 0.28, depth: -0.8 },
  { x: 0.64, y: 0.64, w: 0.24, h: 0.2, depth: 0.55 },
];

function roundedRect(context, x, y, width, height, radius) {
  const r = Math.min(radius, width / 2, height / 2);
  context.beginPath();
  context.moveTo(x + r, y);
  context.lineTo(x + width - r, y);
  context.quadraticCurveTo(x + width, y, x + width, y + r);
  context.lineTo(x + width, y + height - r);
  context.quadraticCurveTo(x + width, y + height, x + width - r, y + height);
  context.lineTo(x + r, y + height);
  context.quadraticCurveTo(x, y + height, x, y + height - r);
  context.lineTo(x, y + r);
  context.quadraticCurveTo(x, y, x + r, y);
  context.closePath();
}

export default function AmbientField() {
  const canvasRef = useRef(null);
  const pointerRef = useRef({ x: 0.5, y: 0.5 });

  useEffect(() => {
    const canvas = canvasRef.current;
    const context = canvas?.getContext("2d");
    if (!canvas || !context) return undefined;

    let frame = 0;
    let width = 0;
    let height = 0;
    let dpr = 1;

    const resize = () => {
      dpr = Math.min(window.devicePixelRatio || 1, 2);
      width = window.innerWidth;
      height = window.innerHeight;
      canvas.width = Math.floor(width * dpr);
      canvas.height = Math.floor(height * dpr);
      canvas.style.width = `${width}px`;
      canvas.style.height = `${height}px`;
      context.setTransform(dpr, 0, 0, dpr, 0, 0);
    };

    const onPointerMove = (event) => {
      pointerRef.current = {
        x: event.clientX / Math.max(window.innerWidth, 1),
        y: event.clientY / Math.max(window.innerHeight, 1),
      };
    };

    const drawGlassPane = (pane, pointer, timeSeconds) => {
      const drift = Math.sin(timeSeconds * 0.12 + pane.depth) * 7;
      const parallaxX = (pointer.x - 0.5) * 26 * pane.depth;
      const parallaxY = (pointer.y - 0.5) * 18 * pane.depth;
      const x = width * pane.x + parallaxX;
      const y = height * pane.y + parallaxY + drift;
      const w = width * pane.w;
      const h = height * pane.h;
      const radius = Math.min(28, Math.max(16, width * 0.018));

      context.save();
      context.shadowBlur = 48;
      context.shadowColor = "rgba(73, 144, 255, 0.12)";
      roundedRect(context, x, y, w, h, radius);
      const paneFill = context.createLinearGradient(x, y, x + w, y + h);
      paneFill.addColorStop(0, "rgba(255, 255, 255, 0.052)");
      paneFill.addColorStop(0.48, "rgba(115, 190, 255, 0.024)");
      paneFill.addColorStop(1, "rgba(39, 229, 198, 0.028)");
      context.fillStyle = paneFill;
      context.fill();
      context.shadowBlur = 0;
      context.strokeStyle = "rgba(219, 235, 255, 0.11)";
      context.lineWidth = 1;
      context.stroke();

      context.clip();
      context.globalAlpha = 0.5;
      for (let index = 0; index < 4; index += 1) {
        const yy = y + h * (0.24 + index * 0.16);
        context.beginPath();
        context.moveTo(x + w * 0.08, yy);
        context.lineTo(x + w * 0.92, yy + Math.sin(timeSeconds * 0.18 + index) * 3);
        context.strokeStyle = "rgba(219, 235, 255, 0.055)";
        context.lineWidth = 0.8;
        context.stroke();
      }
      context.restore();
    };

    const draw = (time) => {
      const t = time * 0.001;
      const pointer = pointerRef.current;

      const base = context.createLinearGradient(0, 0, width, height);
      base.addColorStop(0, "#030711");
      base.addColorStop(0.5, "#07101d");
      base.addColorStop(1, "#02040a");
      context.fillStyle = base;
      context.fillRect(0, 0, width, height);

      const cursorGlow = context.createRadialGradient(
        width * (0.46 + (pointer.x - 0.5) * 0.08),
        height * (0.38 + (pointer.y - 0.5) * 0.08),
        0,
        width * (0.46 + (pointer.x - 0.5) * 0.08),
        height * (0.38 + (pointer.y - 0.5) * 0.08),
        Math.max(width, height) * 0.52,
      );
      cursorGlow.addColorStop(0, "rgba(91, 154, 255, 0.095)");
      cursorGlow.addColorStop(0.38, "rgba(48, 211, 191, 0.048)");
      cursorGlow.addColorStop(1, "rgba(2, 4, 10, 0)");
      context.fillStyle = cursorGlow;
      context.fillRect(0, 0, width, height);

      context.save();
      context.globalCompositeOperation = "screen";
      context.lineCap = "round";
      context.filter = "blur(42px)";

      const ribbons = [
        { y: 0.22, color: "rgba(91, 154, 255, 0.105)", width: 150, speed: 0.16 },
        { y: 0.5, color: "rgba(52, 218, 194, 0.075)", width: 112, speed: -0.12 },
        { y: 0.73, color: "rgba(164, 184, 255, 0.06)", width: 98, speed: 0.1 },
      ];

      ribbons.forEach((ribbon, index) => {
        const lift = Math.sin(t * ribbon.speed + index) * height * 0.045;
        context.beginPath();
        context.moveTo(-width * 0.12, height * ribbon.y + lift);
        context.bezierCurveTo(
          width * 0.22,
          height * (ribbon.y - 0.15) - lift * 0.4,
          width * 0.6,
          height * (ribbon.y + 0.17) + lift * 0.6,
          width * 1.12,
          height * (ribbon.y - 0.04) - lift * 0.25,
        );
        context.strokeStyle = ribbon.color;
        context.lineWidth = Math.min(ribbon.width, width * 0.16);
        context.stroke();
      });
      context.restore();

      context.save();
      context.globalAlpha = 0.48;
      for (let index = 0; index < 10; index += 1) {
        const x = (width / 9) * index + Math.sin(t * 0.08 + index) * 8;
        context.beginPath();
        context.moveTo(x, height * 0.08);
        context.lineTo(x + width * 0.08, height * 0.92);
        context.strokeStyle = "rgba(219, 235, 255, 0.022)";
        context.lineWidth = 1;
        context.stroke();
      }
      context.restore();

      GLASS_PANES.forEach((pane) => drawGlassPane(pane, pointer, t));

      context.save();
      context.globalCompositeOperation = "screen";
      context.fillStyle = "rgba(100, 232, 214, 0.55)";
      for (let index = 0; index < 22; index += 1) {
        const seed = index * 97.13;
        const x = (Math.sin(seed) * 0.5 + 0.5) * width;
        const y = ((Math.cos(seed * 1.7) * 0.5 + 0.5) * height + t * (5 + (index % 5))) % height;
        const alpha = 0.025 + Math.sin(t * 0.42 + index) * 0.012;
        context.globalAlpha = Math.max(alpha, 0.012);
        context.fillRect(x, y, index % 6 === 0 ? 16 : 6, 1);
      }
      context.restore();

      frame = requestAnimationFrame(draw);
    };

    resize();
    window.addEventListener("resize", resize);
    window.addEventListener("pointermove", onPointerMove);
    frame = requestAnimationFrame(draw);

    return () => {
      cancelAnimationFrame(frame);
      window.removeEventListener("resize", resize);
      window.removeEventListener("pointermove", onPointerMove);
    };
  }, []);

  return <canvas ref={canvasRef} className="ambient-field" aria-hidden="true" />;
}
