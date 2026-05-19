export default function OptionCard({ selected, children, onClick }) {
  return (
    <button className={`option-card ${selected ? "is-selected" : ""}`} onClick={onClick} type="button">
      <span>{children}</span>
      <svg viewBox="0 0 24 24" aria-hidden="true">
        <path d="M5 12.5l4.2 4.2L19 7" />
      </svg>
    </button>
  );
}
