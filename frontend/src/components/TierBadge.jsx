import React from 'react';

const TierBadge = ({ tier }) => {
  const getStyles = (tier) => {
    switch (tier?.toLowerCase()) {
      case 'high':
        return { bg: '#dcfce7', text: '#166534', border: '#bbf7d0' };
      case 'mid':
        return { bg: '#fef9c3', text: '#854d0e', border: '#fef08a' };
      case 'low':
        return { bg: '#fee2e2', text: '#991b1b', border: '#fecaca' };
      default:
        return { bg: '#f1f5f9', text: '#475569', border: '#e2e8f0' };
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
        display: 'inline-block',
        padding: '0.25rem 0.75rem',
        borderRadius: '9999px',
        fontSize: '0.875rem',
        fontWeight: 'bold',
        backgroundColor: style.bg,
        color: style.text,
        border: `1px solid ${style.border}`,
      }}
    >
      {tier ? `${getTierLabel(tier)} 등급` : '알 수 없음'}
    </span>
  );
};

export default TierBadge;
