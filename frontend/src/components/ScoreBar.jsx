import React from 'react';

const ScoreBar = ({ score, label, recommended }) => {
  const percentage = Math.round((score ?? 0) * 100);

  return (
    <div style={{ marginBottom: '0.75rem' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.25rem' }}>
        <span style={{ fontSize: '0.875rem', color: '#374151' }}>{label}</span>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <span style={{ fontSize: '0.875rem', fontWeight: 600, color: '#4F46E5' }}>
            {percentage}%
          </span>
          {recommended && (
            <span
              style={{
                fontSize: '0.75rem',
                fontWeight: 600,
                color: '#065F46',
                backgroundColor: '#D1FAE5',
                padding: '0.125rem 0.5rem',
                borderRadius: '9999px',
              }}
            >
              추천
            </span>
          )}
        </div>
      </div>
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
            backgroundColor: 'var(--color-primary, #4F46E5)',
            borderRadius: '9999px',
            transition: 'width 0.4s ease',
          }}
        />
      </div>
    </div>
  );
};

export default ScoreBar;
