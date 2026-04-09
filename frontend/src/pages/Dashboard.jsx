import { useState, useEffect } from 'react';
import StatusPanel from '../components/StatusPanel.jsx';
import DemandChart from '../components/DemandChart.jsx';
import AlertPanel from '../components/AlertPanel.jsx';
import TierBadge from '../components/TierBadge.jsx';
import {
  getDashboardSummary,
  getDemandChart,
  getDashboardAlerts,
} from '../api/adapters/index.js';

const Dashboard = () => {
  const [demoState, setDemoState] = useState('success');

  const [summary, setSummary] = useState({ state: 'loading' });
  const [chart, setChart] = useState({ state: 'loading' });
  const [alerts, setAlerts] = useState({ state: 'loading' });

  useEffect(() => {
    let isMounted = true;
    
    const fetchDashboardData = async () => {
      const [summaryData, chartData, alertsData] = await Promise.all([
        getDashboardSummary({ forceState: demoState }),
        getDemandChart({ forceState: demoState }),
        getDashboardAlerts({ forceState: demoState })
      ]);
      
      if (isMounted) {
        setSummary(summaryData);
        setChart(chartData);
        setAlerts(alertsData);
      }
    };
    
    fetchDashboardData();
    
    return () => {
      isMounted = false;
    };
  }, [demoState]);

  const stateLabels = { success: '성공', loading: '로딩 중', empty: '데이터 없음', error: '오류' };

  const renderDemoSwitcher = () => (
    <div style={{ marginBottom: '2rem', padding: '1rem', backgroundColor: '#f1f5f9', borderRadius: '0.5rem', display: 'flex', alignItems: 'center', gap: '1rem', flexWrap: 'wrap' }}>
      <strong style={{ color: '#475569' }}>🧪 데모 환경</strong>
      <div style={{ display: 'flex', gap: '0.5rem' }}>
        {['success', 'loading', 'empty', 'error'].map(state => (
          <button
            key={state}
            type="button"
            onClick={() => setDemoState(state)}
            style={{
              padding: '0.5rem 1rem',
              borderRadius: '0.25rem',
              border: '1px solid #cbd5e1',
              backgroundColor: demoState === state ? '#3b82f6' : '#ffffff',
              color: demoState === state ? '#ffffff' : '#334155',
              cursor: 'pointer',
              fontWeight: '500',
              textTransform: 'capitalize'
            }}
          >
            {stateLabels[state]}
          </button>
        ))}
      </div>
      <span style={{ fontSize: '0.875rem', color: '#64748b', marginLeft: 'auto' }}>
        데이터는 데모 목적으로 제공된 가상의 데이터입니다
      </span>
    </div>
  );

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem' }}>
        <h1 style={{ fontSize: '1.875rem', fontWeight: 'bold', margin: 0, color: '#0f172a' }}>대시보드</h1>
      </div>

      {renderDemoSwitcher()}

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))', gap: '1.5rem', marginBottom: '2rem' }}>
        {summary.state === 'loading' && (
          <StatusPanel variant="info" message="요약 지표를 불러오는 중입니다..." />
        )}
        {summary.state === 'error' && (
          <StatusPanel variant="error" title="오류" message={summary.error} />
        )}
        {summary.state === 'empty' && (
          <StatusPanel variant="empty" message="사용 가능한 지표가 없습니다." />
        )}
        {summary.state === 'success' && summary.data?.map(card => (
          <div key={card.id} style={{ backgroundColor: 'white', padding: '1.5rem', borderRadius: '0.5rem', border: '1px solid #e2e8f0', boxShadow: '0 1px 3px 0 rgba(0, 0, 0, 0.1)' }}>
            <h3 style={{ margin: '0 0 0.5rem 0', fontSize: '0.875rem', color: '#64748b', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
              {card.label}
            </h3>
            <div style={{ display: 'flex', alignItems: 'baseline', gap: '0.5rem' }}>
              {card.id === 'demand-index' ? (
                <TierBadge tier={card.value} />
              ) : (
                <span style={{ fontSize: '2rem', fontWeight: 'bold', color: '#0f172a' }}>{card.value}</span>
              )}
            </div>
            {card.trend && (
              <div style={{ marginTop: '0.5rem', fontSize: '0.875rem', color: card.trendDirection === 'up' ? '#16a34a' : '#dc2626', display: 'flex', alignItems: 'center', gap: '0.25rem' }}>
                <span>{card.trendDirection === 'up' ? '↑' : '↓'}</span>
                <span>{card.trend}{card.trendLabel ? ` ${card.trendLabel}` : ''}</span>
              </div>
            )}
          </div>
        ))}
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(400px, 1fr))', gap: '2rem' }}>
        <div style={{ backgroundColor: 'white', padding: '1.5rem', borderRadius: '0.5rem', border: '1px solid #e2e8f0', boxShadow: '0 1px 3px 0 rgba(0, 0, 0, 0.1)' }}>
          <h2 style={{ fontSize: '1.25rem', fontWeight: 'bold', margin: '0 0 1.5rem 0', color: '#1e293b' }}>
            예상 수요
          </h2>
          {chart.state === 'loading' && <StatusPanel variant="info" message="수요 예측 데이터를 불러오는 중입니다..." />}
          {chart.state === 'error' && <StatusPanel variant="error" title="오류" message={chart.error} />}
          {chart.state === 'empty' && <StatusPanel variant="empty" message="선택한 기간에 대한 차트 데이터가 없습니다." />}
          {chart.state === 'success' && <DemandChart data={chart.data} />}
        </div>

        <div style={{ backgroundColor: 'white', padding: '1.5rem', borderRadius: '0.5rem', border: '1px solid #e2e8f0', boxShadow: '0 1px 3px 0 rgba(0, 0, 0, 0.1)' }}>
          <h2 style={{ fontSize: '1.25rem', fontWeight: 'bold', margin: '0 0 1.5rem 0', color: '#1e293b' }}>
            액션 알림
          </h2>
          {alerts.state === 'loading' && <StatusPanel variant="info" message="시스템 알림을 불러오는 중입니다..." />}
          {alerts.state === 'error' && <StatusPanel variant="error" title="오류" message={alerts.error} />}
          {alerts.state === 'empty' && <StatusPanel variant="empty" message="모든 것이 정상입니다. 활성 알림이 없습니다." />}
          {alerts.state === 'success' && <AlertPanel alerts={alerts.data} />}
        </div>
      </div>
    </div>
  );
};

export default Dashboard;