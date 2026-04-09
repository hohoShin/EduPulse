import React from 'react';

const StatusPanel = ({ variant = 'info', title, message, children }) => {
  const getIcon = (v) => {
    switch (v) {
      case 'info':
        return (
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <circle cx="12" cy="12" r="10"></circle>
            <line x1="12" y1="16" x2="12" y2="12"></line>
            <line x1="12" y1="8" x2="12.01" y2="8"></line>
          </svg>
        );
      case 'warning':
        return (
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"></path>
            <line x1="12" y1="9" x2="12" y2="13"></line>
            <line x1="12" y1="17" x2="12.01" y2="17"></line>
          </svg>
        );
      case 'error':
        return (
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <circle cx="12" cy="12" r="10"></circle>
            <line x1="15" y1="9" x2="9" y2="15"></line>
            <line x1="9" y1="9" x2="15" y2="15"></line>
          </svg>
        );
      case 'empty':
        return (
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <rect x="2" y="3" width="20" height="14" rx="2" ry="2"></rect>
            <line x1="8" y1="21" x2="16" y2="21"></line>
            <line x1="12" y1="17" x2="12" y2="21"></line>
          </svg>
        );
      case 'loading':
        return (
          <svg className="animate-spin" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <line x1="12" y1="2" x2="12" y2="6"></line>
            <line x1="12" y1="18" x2="12" y2="22"></line>
            <line x1="4.93" y1="4.93" x2="7.76" y2="7.76"></line>
            <line x1="16.24" y1="16.24" x2="19.07" y2="19.07"></line>
            <line x1="2" y1="12" x2="6" y2="12"></line>
            <line x1="18" y1="12" x2="22" y2="12"></line>
            <line x1="4.93" y1="19.07" x2="7.76" y2="16.24"></line>
            <line x1="16.24" y1="7.76" x2="19.07" y2="4.93"></line>
          </svg>
        );
      default:
        return null;
    }
  };

  const getStyle = (v) => {
    switch (v) {
      case 'info':
      case 'loading':
        return { bg: 'var(--color-info-bg)', border: 'var(--color-info-border)', text: 'var(--color-info-text)' };
      case 'warning':
        return { bg: 'var(--color-warning-bg)', border: 'var(--color-warning-border)', text: 'var(--color-warning-text)' };
      case 'error':
        return { bg: 'var(--color-error-bg)', border: 'var(--color-error-border)', text: 'var(--color-error-text)' };
      case 'empty':
        return { bg: 'var(--color-surface)', border: 'var(--color-border)', text: 'var(--color-text-muted)' };
      default:
        return { bg: 'var(--color-info-bg)', border: 'var(--color-info-border)', text: 'var(--color-info-text)' };
    }
  };

  const style = getStyle(variant);

  return (
    <div style={{
      backgroundColor: style.bg,
      border: `1px solid ${style.border}`,
      borderRadius: 'var(--radius-lg)',
      padding: 'var(--space-6)',
      color: style.text,
      display: 'flex',
      flexDirection: 'column',
      gap: 'var(--space-2)',
      boxShadow: 'var(--shadow-sm)'
    }}>
      <div style={{ display: 'flex', alignItems: 'flex-start', gap: 'var(--space-4)' }}>
        <div style={{ marginTop: '2px', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
          {getIcon(variant)}
        </div>
        <div style={{ flex: 1 }}>
          {title && <h3 style={{ margin: '0 0 var(--space-1) 0', fontWeight: '600', fontSize: '1rem' }}>{title}</h3>}
          {message && <p style={{ margin: 0, fontSize: '0.875rem', opacity: 0.9, lineHeight: '1.5' }}>{message}</p>}
          {children && <div style={{ marginTop: 'var(--space-4)' }}>{children}</div>}
        </div>
      </div>
    </div>
  );
};

export default StatusPanel;
