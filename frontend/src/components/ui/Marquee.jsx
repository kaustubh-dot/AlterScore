import './Marquee.css';

export default function Marquee({ 
  items = [], 
  direction = 'left', 
  speed = 'fast' // 'slow' | 'medium' | 'fast'
}) {
  // Join items with separators
  const content = items.join(' \u00B7 ') + ' \u00B7 ';

  return (
    <div className={`marquee-container ${speed} ${direction}`}>
      <div className="marquee-track">
        <div className="marquee-content">{content}</div>
        <div className="marquee-content" aria-hidden="true">{content}</div>
      </div>
    </div>
  );
}
