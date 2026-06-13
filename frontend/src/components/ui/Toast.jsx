import { useEffect, useState } from 'react';
import { CheckCircle, AlertTriangle, XCircle, Info, X } from 'lucide-react';
import './Toast.css';

export default function Toast({
  message,
  type = 'info', // 'success' | 'warning' | 'error' | 'info'
  onClose,
  duration = 4000
}) {
  const [progress, setProgress] = useState(100);

  useEffect(() => {
    const startTime = Date.now();
    const interval = setInterval(() => {
      const elapsed = Date.now() - startTime;
      const remaining = Math.max(0, 100 - (elapsed / duration) * 100);
      setProgress(remaining);
      if (remaining <= 0) {
        clearInterval(interval);
        onClose();
      }
    }, 30);

    return () => clearInterval(interval);
  }, [duration, onClose]);

  const getIcon = () => {
    switch (type) {
      case 'success':
        return <CheckCircle className="toast-icon success" size={18} />;
      case 'warning':
        return <AlertTriangle className="toast-icon warning" size={18} />;
      case 'error':
        return <XCircle className="toast-icon error" size={18} />;
      default:
        return <Info className="toast-icon info" size={18} />;
    }
  };

  return (
    <div className={`toast-container glass toast-${type}`}>
      <div className="toast-body">
        {getIcon()}
        <span className="toast-message">{message}</span>
        <button className="toast-close-btn" onClick={onClose}>
          <X size={14} />
        </button>
      </div>
      <div className="toast-progress-bar" style={{ width: `${progress}%` }} />
    </div>
  );
}
