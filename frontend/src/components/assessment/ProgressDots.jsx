export default function ProgressDots({ total, current }) {
  return (
    <div className="progress-dots" aria-label={`Question ${current + 1} of ${total}`}>
      {Array.from({ length: total }, (_, index) => (
        <span
          key={index}
          className={[
            index < current ? "is-past" : "",
            index === current ? "is-current" : "",
          ].join(" ")}
        />
      ))}
    </div>
  );
}
