import React from 'react';

const AlertPanel = ({ alerts = [] }) => {
  if (!alerts || alerts.length === 0) {
    return (
      <div style={{ padding: '1rem', color: '#64748b', textAlign: 'center', backgroundColor: '#f8fafc', borderRadius: '0.5rem', border: '1px solid #e2e8f0' }}>
        활성화된 알림이 없습니다.
      </div>
    );
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
      {alerts.map((alert) => (
        <div 
          key={alert.id}
          style={{
            display: 'flex',
            alignItems: 'flex-start',
            padding: '1rem',
            borderRadius: '0.5rem',
            borderLeft: `4px solid ${alert.severity === 'critical' ? '#ef4444' : '#f59e0b'}`,
            backgroundColor: '#ffffff',
            boxShadow: '0 1px 3px 0 rgba(0, 0, 0, 0.1)'
          }}
        >
          <div style={{ marginRight: '1rem', fontSize: '1.25rem' }}>
            {alert.severity === 'critical' ? '🚨' : '⚠️'}
          </div>
          <div style={{ flex: 1 }}>
            <h4 style={{ margin: '0 0 0.25rem 0', fontWeight: 'bold', color: '#1e293b' }}>
              {alert.title}
            </h4>
            <p style={{ margin: 0, color: '#475569', fontSize: '0.875rem' }}>
              {alert.message}
            </p>
          </div>
          {alert.actionLabel && (
            <button
              type="button"
              style={{
                marginLeft: '1rem',
                padding: '0.375rem 0.75rem',
                backgroundColor: '#f1f5f9',
                color: '#334155',
                border: '1px solid #cbd5e1',
                borderRadius: '0.375rem',
                fontSize: '0.75rem',
                fontWeight: '600',
                cursor: 'pointer'
              }}
            >
              {alert.actionLabel}
            </button>
          )}
        </div>
      ))}
    </div>
  );
};

export default AlertPanel;
