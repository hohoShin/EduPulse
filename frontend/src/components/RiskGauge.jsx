import React from 'react';

const levelConfig = {
  high: {
    textVar: 'var(--color-error-text, #991B1B)',
    bgVar: 'var(--color-error-bg, #FEE2E2)',
    barColor: 'var(--color-error-text, #DC2626)',
    label: '위험',
  },
  medium: {
    textVar: 'var(--color-warning-text, #92400E)',
    bgVar: 'var(--color-warning-bg, #FEF3C7)',
    barColor: 'var(--color-warning-text, #D97706)',
    label: '주의',
  },
  low: {
    textVar: 'var(--color-success-text, #065F46)',
    bgVar: 'var(--color-success-bg, #D1FAE5)',
    barColor: 'var(--color-success-text, #059669)',
    label: '안전',
  },
};

const RiskGauge = ({ score, level, label, labels }) => {
  const config = levelConfig[level] || levelConfig.low;
  const effectiveLabels = labels || { high: '위험', medium: '주의', low: '안전' };
  const percentage = Math.round((score ?? 0) * 100);

  return (
    <div style={{ marginBottom: '0.75rem' }}>
      {label && (
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.25rem' }}>
          <span style={{ fontSize: '0.875rem', color: '#374151' }}>{label}</span>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <span style={{ fontSize: '0.875rem', fontWeight: 600, color: config.textVar }}>
              {percentage}%
            </span>
            <span
              style={{
                fontSize: '0.75rem',
                fontWeight: 600,
                color: config.textVar,
                backgroundColor: config.bgVar,
                padding: '0.125rem 0.5rem',
                borderRadius: '9999px',
              }}
            >
              {effectiveLabels[level] ?? effectiveLabels.low}
            </span>
          </div>
        </div>
      )}
      <div
        style={{
          width: '100%',
          height: '8px',
          backgroundColor: '#E5E7EB',
          borderRadius: '9999px',
          overflow: 'hidden',
        }}
      >
        <div
          style={{
            width: `${percentage}%`,
            height: '100%',
            backgroundColor: config.barColor,
            borderRadius: '9999px',
            transition: 'width 0.4s ease',
          }}
        />
      </div>
    </div>
  );
};

export default RiskGauge;
