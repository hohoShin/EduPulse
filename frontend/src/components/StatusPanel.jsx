import React from 'react';

const StatusPanel = ({ variant = 'info', title, message, children }) => {
  const styles = {
    info: { bg: '#eff6ff', border: '#bfdbfe', text: '#1e3a8a', icon: 'ℹ️' },
    warning: { bg: '#fffbeb', border: '#fde68a', text: '#92400e', icon: '⚠️' },
    error: { bg: '#fef2f2', border: '#fecaca', text: '#991b1b', icon: '🚨' },
    empty: { bg: '#f8fafc', border: '#e2e8f0', text: '#475569', icon: '📭' }
  };

  const currentStyle = styles[variant] || styles.info;

  return (
    <div style={{
      backgroundColor: currentStyle.bg,
      border: `1px solid ${currentStyle.border}`,
      borderRadius: '0.5rem',
      padding: '1.5rem',
      color: currentStyle.text,
      marginBottom: '1rem'
    }}>
      <div style={{ display: 'flex', alignItems: 'flex-start', gap: '1rem' }}>
        <span style={{ fontSize: '1.5rem' }}>{currentStyle.icon}</span>
        <div>
          {title && <h3 style={{ margin: '0 0 0.5rem 0', fontWeight: 'bold' }}>{title}</h3>}
          {message && <p style={{ margin: '0 0 1rem 0' }}>{message}</p>}
          {children}
        </div>
      </div>
    </div>
  );
};

export default StatusPanel;
