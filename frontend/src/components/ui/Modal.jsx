import { useEffect, useId, useRef } from 'react';
import { createPortal } from 'react-dom';
import './Modal.css';

export default function Modal({
  isOpen,
  title,
  message,
  confirmText = 'Confirm',
  cancelText = 'Cancel',
  onConfirm,
  onCancel,
  actions,
  actionsClassName = '',
}) {
  const titleId = useId();
  const messageId = useId();
  const modalRef = useRef(null);
  const previouslyFocusedRef = useRef(null);
  const previousOverflowRef = useRef('');

  useEffect(() => {
    if (!isOpen) return undefined;

    previouslyFocusedRef.current = document.activeElement;
    previousOverflowRef.current = document.body.style.overflow;
    document.body.style.overflow = 'hidden';
    requestAnimationFrame(() => {
      const firstButton = modalRef.current?.querySelector('button');
      firstButton?.focus({ preventScroll: true });
    });

    return () => {
      document.body.style.overflow = previousOverflowRef.current;
      const previouslyFocused = previouslyFocusedRef.current;
      if (previouslyFocused?.isConnected) previouslyFocused.focus({ preventScroll: true });
    };
  }, [isOpen]);

  useEffect(() => {
    if (!isOpen) return undefined;

    const handleKeyDown = (event) => {
      if (event.key === 'Escape') {
        event.preventDefault();
        onCancel();
        return;
      }

      if (event.key !== 'Tab') return;

      const focusable = modalRef.current?.querySelectorAll(
        'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
      );
      if (!focusable || focusable.length === 0) return;

      const first = focusable[0];
      const last = focusable[focusable.length - 1];
      if (event.shiftKey && document.activeElement === first) {
        event.preventDefault();
        last.focus();
      } else if (!event.shiftKey && document.activeElement === last) {
        event.preventDefault();
        first.focus();
      }
    };

    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, [isOpen, onCancel]);

  if (!isOpen) return null;

  return createPortal(
    <div className="modal-overlay" onClick={onCancel}>
      <div
        ref={modalRef}
        className="modal-card glass"
        role="dialog"
        aria-modal="true"
        aria-labelledby={titleId}
        aria-describedby={messageId}
        onClick={(e) => e.stopPropagation()}
      >
        <div className="modal-content">
          <h3 id={titleId} className="modal-title gradient-text-accent">{title}</h3>
          <p id={messageId} className="modal-message">{message}</p>
        </div>
        <div className={`modal-actions ${actionsClassName}`.trim()}>
          {actions || (
            <>
              <button type="button" className="btn btn-ghost" onClick={onCancel}>
                {cancelText}
              </button>
              <button type="button" className="btn btn-primary" onClick={onConfirm}>
                {confirmText}
              </button>
            </>
          )}
        </div>
      </div>
    </div>,
    document.body,
  );
}
