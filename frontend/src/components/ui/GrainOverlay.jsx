import { useEffect, useRef } from "react";

export default function GrainOverlay() {
  const canvasRef = useRef(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    const context = canvas?.getContext("2d", { alpha: true });
    if (!canvas || !context) return undefined;

    let timer = 0;
    const width = 360;
    const height = 240;

    canvas.width = width;
    canvas.height = height;

    const draw = () => {
      const imageData = context.createImageData(width, height);
      const data = imageData.data;

      for (let index = 0; index < data.length; index += 4) {
        const value = 140 + Math.random() * 115;
        data[index] = value;
        data[index + 1] = value;
        data[index + 2] = value;
        data[index + 3] = Math.random() * 22;
      }

      context.putImageData(imageData, 0, 0);
      timer = window.setTimeout(draw, 180);
    };

    draw();
    return () => {
      window.clearTimeout(timer);
    };
  }, []);

  return <canvas ref={canvasRef} className="grain-overlay" aria-hidden="true" />;
}
