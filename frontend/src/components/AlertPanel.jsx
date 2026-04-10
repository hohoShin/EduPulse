import React from 'react';

const AlertPanel = ({ alerts = [] }) => {
  if (!alerts || alerts.length === 0) {
    return (
      <div style={{
        padding: 'var(--space-6)',
        color: 'var(--color-text-muted)',
        textAlign: 'center',
        backgroundColor: 'var(--color-surface-hover)',
        borderRadius: 'var(--radius-lg)',
        border: '1px dashed var(--color-border)',
        fontSize: '0.875rem'
      }}>
        활성화된 알림이 없습니다.
      </div>
    );
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-3)' }}>
      {alerts.map((alert) => {
        const isCritical = alert.severity === 'critical';
        return (
          <div 
            key={alert.id}
            style={{
              display: 'flex',
              alignItems: 'flex-start',
              padding: 'var(--space-4)',
              borderRadius: 'var(--radius-md)',
              borderLeft: `4px solid ${isCritical ? 'var(--color-error-text)' : '#F59E0B'}`,
              backgroundColor: 'var(--color-surface)',
              boxShadow: 'var(--shadow-sm)',
              border: '1px solid var(--color-border)',
              borderLeftWidth: '4px',
              transition: 'transform var(--transition-fast), box-shadow var(--transition-fast)'
            }}
            onMouseOver={(e) => {
              e.currentTarget.style.transform = 'translateY(-1px)';
              e.currentTarget.style.boxShadow = 'var(--shadow-md)';
            }}
            onMouseOut={(e) => {
              e.currentTarget.style.transform = 'none';
              e.currentTarget.style.boxShadow = 'var(--shadow-sm)';
            }}
          >
            <div style={{ marginRight: 'var(--space-3)', color: isCritical ? 'var(--color-error-text)' : '#F59E0B' }}>
              {isCritical ? (
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"></path>
                  <line x1="12" y1="9" x2="12" y2="13"></line>
                  <line x1="12" y1="17" x2="12.01" y2="17"></line>
                </svg>
              ) : (
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <circle cx="12" cy="12" r="10"></circle>
                  <line x1="12" y1="8" x2="12" y2="12"></line>
                  <line x1="12" y1="16" x2="12.01" y2="16"></line>
                </svg>
              )}
            </div>
            <div style={{ flex: 1 }}>
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 'var(--space-1)' }}>
                <h4 style={{ margin: 0, fontWeight: '600', color: 'var(--color-text-main)', fontSize: '0.875rem' }}>
                  {alert.title}
                </h4>
                <span style={{ fontSize: '0.75rem', color: 'var(--color-text-light)' }}>방금 전</span>
              </div>
              <p style={{ margin: 0, color: 'var(--color-text-muted)', fontSize: '0.875rem', lineHeight: '1.5' }}>
                {alert.message}
              </p>
            </div>
            {alert.actionLabel && (
              <button
                type="button"
                style={{
                  marginLeft: 'var(--space-4)',
                  padding: 'var(--space-2) var(--space-3)',
                  backgroundColor: 'var(--color-surface)',
                  color: 'var(--color-text-main)',
                  border: '1px solid var(--color-border)',
                  borderRadius: 'var(--radius-sm)',
                  fontSize: '0.75rem',
                  fontWeight: '500',
                  cursor: 'pointer',
                  transition: 'all var(--transition-fast)',
                  whiteSpace: 'nowrap'
                }}
                onMouseOver={(e) => {
                  e.currentTarget.style.backgroundColor = 'var(--color-surface-hover)';
                  e.currentTarget.style.borderColor = 'var(--color-text-muted)';
                }}
                onMouseOut={(e) => {
                  e.currentTarget.style.backgroundColor = 'var(--color-surface)';
                  e.currentTarget.style.borderColor = 'var(--color-border)';
                }}
              >
                {alert.actionLabel}
              </button>
            )}
          </div>
        );
      })}
    </div>
  );
};

export default AlertPanel;
