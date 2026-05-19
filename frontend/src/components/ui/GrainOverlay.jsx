import { useEffect, useRef } from "react";

export default function GrainOverlay() {
  const canvasRef = useRef(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    const context = canvas?.getContext("2d", { alpha: true });
    if (!canvas || !context) return undefined;

    let frame = 0;
    const width = 180;
    const height = 120;
    canvas.width = width;
    canvas.height = height;

    const draw = () => {
      const imageData = context.createImageData(width, height);
      const data = imageData.data;

      for (let index = 0; index < data.length; index += 4) {
        const value = Math.random() * 255;
        data[index] = value;
        data[index + 1] = value;
        data[index + 2] = value;
        data[index + 3] = 255;
      }

      context.putImageData(imageData, 0, 0);
      frame = requestAnimationFrame(draw);
    };

    frame = requestAnimationFrame(draw);
    return () => cancelAnimationFrame(frame);
  }, []);

  return <canvas ref={canvasRef} className="grain-overlay" aria-hidden="true" />;
}
