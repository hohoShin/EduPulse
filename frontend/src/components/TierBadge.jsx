import React from 'react';

const TierBadge = ({ tier }) => {
  const getStyles = (tier) => {
    switch (tier?.toLowerCase()) {
      case 'high':
        return { 
          bg: 'var(--color-success-bg)', 
          text: 'var(--color-success-text)', 
          border: 'var(--color-success-border)',
          icon: <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round"><polyline points="20 6 9 17 4 12"></polyline></svg>
        };
      case 'mid':
        return { 
          bg: 'var(--color-warning-bg)', 
          text: 'var(--color-warning-text)', 
          border: 'var(--color-warning-border)',
          icon: <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round"><line x1="5" y1="12" x2="19" y2="12"></line></svg>
        };
      case 'low':
        return { 
          bg: 'var(--color-error-bg)', 
          text: 'var(--color-error-text)', 
          border: 'var(--color-error-border)',
          icon: <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round"><line x1="12" y1="5" x2="12" y2="19"></line><polyline points="19 12 12 19 5 12"></polyline></svg>
        };
      default:
        return { 
          bg: 'var(--color-background)', 
          text: 'var(--color-text-muted)', 
          border: 'var(--color-border)',
          icon: <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="16" x2="12" y2="12"></line><line x1="12" y1="8" x2="12.01" y2="8"></line></svg>
        };
    }
  };

  const style = getStyles(tier);

  const getTierLabel = (tier) => {
    switch (tier?.toLowerCase()) {
      case 'high': return '높음';
      case 'mid': return '보통';
      case 'low': return '낮음';
      default: return '알 수 없음';
    }
  };

  return (
    <span
      style={{
        display: 'inline-flex',
        alignItems: 'center',
        gap: '4px',
        padding: '4px 10px',
        borderRadius: 'var(--radius-full)',
        fontSize: '0.75rem',
        fontWeight: '600',
        backgroundColor: style.bg,
        color: style.text,
        border: `1px solid ${style.border}`,
        letterSpacing: '0.025em',
        boxShadow: 'var(--shadow-sm)'
      }}
    >
      {style.icon}
      {tier ? `${getTierLabel(tier)} 등급` : '알 수 없음'}
    </span>
  );
};

export default TierBadge;
