import { Link } from 'react-router-dom';

const getSeverityMeta = (severity) => {
  switch (severity) {
    case 'critical':
      return {
        label: '긴급',
        icon: (
          <svg aria-hidden="true" focusable="false" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"></path>
            <line x1="12" y1="9" x2="12" y2="13"></line>
            <line x1="12" y1="17" x2="12.01" y2="17"></line>
          </svg>
        ),
      };
    case 'info':
      return {
        label: '안내',
        icon: (
          <svg aria-hidden="true" focusable="false" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <circle cx="12" cy="12" r="10"></circle>
            <line x1="12" y1="16" x2="12" y2="12"></line>
            <line x1="12" y1="8" x2="12.01" y2="8"></line>
          </svg>
        ),
      };
    case 'warning':
    default:
      return {
        label: '주의',
        icon: (
          <svg aria-hidden="true" focusable="false" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <circle cx="12" cy="12" r="10"></circle>
            <line x1="12" y1="8" x2="12" y2="12"></line>
            <line x1="12" y1="16" x2="12.01" y2="16"></line>
          </svg>
        ),
      };
  }
};

const ACTION_ROUTE_BY_LABEL = {
  '가격 조정': '/operations',
  '마케팅 계획 보기': '/marketing',
  '일정 조정': '/operations',
  '리포트 보기': '/market',
  '운영 계획 보기': '/operations',
};

const resolveActionTarget = (alert) => alert.actionUrl || ACTION_ROUTE_BY_LABEL[alert.actionLabel] || null;

const AlertPanel = ({ alerts = [] }) => {
  if (!alerts || alerts.length === 0) {
    return (
      <div className="alert-panel__empty">
        활성화된 알림이 없습니다.
      </div>
    );
  }

  return (
    <div className="alert-panel">
      {alerts.map((alert) => {
        const severity = alert.severity || 'warning';
        const severityMeta = getSeverityMeta(severity);
        const actionTarget = resolveActionTarget(alert);

        return (
          <div
            key={alert.id}
            className={`alert-panel__item alert-panel__item--${severity}`}
          >
            <div className="alert-panel__icon">{severityMeta.icon}</div>
            <div className="alert-panel__body">
              <div className="alert-panel__header">
                <div>
                  <span className={`alert-panel__severity alert-panel__severity--${severity}`}>{severityMeta.label}</span>
                  <h4 className="alert-panel__title">{alert.title}</h4>
                </div>
                <span className="alert-panel__timestamp">방금 전</span>
              </div>
              <p className="alert-panel__message">{alert.message}</p>
            </div>
            {alert.actionLabel && actionTarget && (
              <Link
                to={actionTarget}
                className="alert-panel__action"
                aria-label={`${alert.title} 조치: ${alert.actionLabel}`}
              >
                {alert.actionLabel}
              </Link>
            )}
          </div>
        );
      })}
    </div>
  );
};

export default AlertPanel;
