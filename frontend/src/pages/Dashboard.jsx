import { useState, useEffect } from 'react';
import StatusPanel from '../components/StatusPanel.jsx';
import DemandChart from '../components/DemandChart.jsx';
import AlertPanel from '../components/AlertPanel.jsx';
import TierBadge from '../components/TierBadge.jsx';
import FieldSelector from '../components/FieldSelector.jsx';
import {
  getDashboardSummary,
  getDemandChart,
  getDashboardAlerts,
} from '../api/adapters/index.js';

const Dashboard = () => {
  const [demoState, setDemoState] = useState('success');
  const [field, setField] = useState('coding');
  const [refreshKey, setRefreshKey] = useState(0);

  const [summary, setSummary] = useState({ state: 'loading' });
  const [chart, setChart] = useState({ state: 'loading' });
  const [alerts, setAlerts] = useState({ state: 'loading' });

  useEffect(() => {
    let isMounted = true;

    const run = async () => {
      setSummary({ state: 'loading' });
      setChart({ state: 'loading' });
      setAlerts({ state: 'loading' });

      const [summaryData, chartData, alertsData] = await Promise.all([
        getDashboardSummary({ forceState: demoState, field }),
        getDemandChart({ forceState: demoState, field }),
        getDashboardAlerts({ forceState: demoState, field })
      ]);

      if (isMounted) {
        setSummary(summaryData);
        setChart(chartData);
        setAlerts(alertsData);
      }
    };

    run();

    return () => {
      isMounted = false;
    };
  }, [demoState, field, refreshKey]);

  const stateLabels = { success: '성공', loading: '로딩 중', empty: '데이터 없음', error: '오류' };

  const renderDemoSwitcher = () => (
    <div className="toolbar">
      <div className="toolbar-label">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
          <path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z"></path>
          <polyline points="3.27 6.96 12 12.01 20.73 6.96"></polyline>
          <line x1="12" y1="22.08" x2="12" y2="12"></line>
        </svg>
        데모 환경 설정
      </div>
      <div className="button-group">
        {['success', 'loading', 'empty', 'error'].map(state => (
          <button
            key={state}
            type="button"
            onClick={() => setDemoState(state)}
            className={`btn ${demoState === state ? 'active' : ''}`}
          >
            {stateLabels[state]}
          </button>
        ))}
      </div>
      <div style={{ marginLeft: 'auto', fontSize: '0.75rem', color: 'var(--color-text-light)' }}>
        * 이 대시보드는 가상의 시뮬레이션 데이터를 제공합니다
      </div>
    </div>
  );

  return (
    <div>
      <div className="page-header">
        <div>
          <h1 className="page-title">대시보드</h1>
          <p className="page-subtitle">AI 기반 수강 수요 예측 및 운영 현황</p>
        </div>
        <div style={{ display: 'flex', alignItems: 'flex-end', gap: 'var(--space-3)' }}>
          <FieldSelector
            value={field}
            onChange={setField}
            style={{ marginBottom: 0 }}
          />
          <button
            type="button"
            className="btn"
            onClick={() => setRefreshKey(k => k + 1)}
            style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-1)', whiteSpace: 'nowrap', marginBottom: 'var(--space-4)' }}
            title="데이터 새로고침"
          >
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <polyline points="23 4 23 10 17 10"></polyline>
              <polyline points="1 20 1 14 7 14"></polyline>
              <path d="M3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15"></path>
            </svg>
            새로고침
          </button>
        </div>
      </div>

      {renderDemoSwitcher()}

      <div className="grid-auto-fit" style={{ marginBottom: 'var(--space-8)' }}>
        {summary.state === 'loading' && (
          <StatusPanel variant="loading" title="데이터 로딩 중" message="요약 지표를 불러오고 있습니다." />
        )}
        {summary.state === 'error' && (
          <StatusPanel variant="error" title="오류 발생" message={summary.error} />
        )}
        {summary.state === 'empty' && (
          <StatusPanel variant="empty" title="데이터 없음" message="표시할 요약 지표가 없습니다." />
        )}
        {summary.state === 'success' && summary.data?.map(card => (
          <div key={card.id} className="card">
            <h3 className="metric-label">{card.label}</h3>
            <div style={{ display: 'flex', alignItems: 'baseline', gap: 'var(--space-2)' }}>
              {card.id === 'demand-index' ? (
                <div style={{ marginTop: 'var(--space-2)' }}>
                  <TierBadge tier={card.value} />
                </div>
              ) : (
                <span className="metric-value">{card.value}</span>
              )}
            </div>
            {card.trend && (
              <div className={card.trendDirection === 'up' ? 'trend-up' : 'trend-down'}>
                {card.trendDirection === 'up' ? (
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><polyline points="23 6 13.5 15.5 8.5 10.5 1 18"></polyline><polyline points="17 6 23 6 23 12"></polyline></svg>
                ) : (
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><polyline points="23 18 13.5 8.5 8.5 13.5 1 6"></polyline><polyline points="17 18 23 18 23 12"></polyline></svg>
                )}
                <span>{card.trend}{card.trendLabel ? ` ${card.trendLabel}` : ''}</span>
              </div>
            )}
          </div>
        ))}
      </div>

      <div className="grid-auto-fit" style={{ gridTemplateColumns: 'repeat(auto-fit, minmax(450px, 1fr))' }}>
        <div className="card">
          <h2 className="card-header">
            예상 수요 트렌드
            <span style={{ fontSize: '0.75rem', fontWeight: 'normal', color: 'var(--color-text-muted)', backgroundColor: 'var(--color-background)', padding: '4px 8px', borderRadius: '4px' }}>최근 30일</span>
          </h2>
          {chart.state === 'loading' && <StatusPanel variant="loading" message="수요 예측 데이터를 분석 중입니다..." />}
          {chart.state === 'error' && <StatusPanel variant="error" title="오류" message={chart.error} />}
          {chart.state === 'empty' && <StatusPanel variant="empty" message="선택한 기간에 대한 차트 데이터가 없습니다." />}
          {chart.state === 'success' && <DemandChart data={chart.data} />}
        </div>

        <div className="card">
          <h2 className="card-header">
            시스템 알림
            {alerts.state === 'success' && alerts.data?.length > 0 && (
              <span style={{
                backgroundColor: 'var(--color-error-bg)',
                color: 'var(--color-error-text)',
                fontSize: '0.75rem',
                padding: '2px 8px',
                borderRadius: '12px'
              }}>
                {alerts.data.length}건
              </span>
            )}
          </h2>
          {alerts.state === 'loading' && <StatusPanel variant="loading" message="실시간 알림을 동기화 중입니다..." />}
          {alerts.state === 'error' && <StatusPanel variant="error" title="오류" message={alerts.error} />}
          {alerts.state === 'empty' && <StatusPanel variant="empty" message="모든 시스템이 정상입니다. 활성 알림이 없습니다." />}
          {alerts.state === 'success' && <AlertPanel alerts={alerts.data} />}
        </div>
      </div>
    </div>
  );
};

export default Dashboard;
