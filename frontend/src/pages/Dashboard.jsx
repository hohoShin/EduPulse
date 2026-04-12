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

const PILLAR_COPY = {
  운영_효율화: '운영 효율화',
  마케팅_매출_연계: '마케팅·매출 연계',
  전략_기획: '전략 기획',
};

const SHOW_DEMO_SWITCHER = import.meta.env.DEV && import.meta.env.VITE_ADAPTER !== 'real';

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

  const summaryCards = summary.state === 'success' ? summary.data ?? [] : [];
  const demandSignalCard = summaryCards.find((card) => card.id === 'demand-index');
  const supportingSummaryCards = summaryCards.filter((card) => card.id !== 'demand-index');
  const alertItems = alerts.state === 'success' ? alerts.data ?? [] : [];
  const primaryAlert = alertItems[0] ?? null;

  const primaryAction = primaryAlert?.actionLabel
    ? {
        title: primaryAlert.actionLabel,
        detail: (
          <>
            {primaryAlert.title}에 맞춰 {PILLAR_COPY.마케팅_매출_연계} 또는
            <br />
            {PILLAR_COPY.운영_효율화} 대응을 시작하세요.
          </>
        ),
      }
    : {
        title: '다음 액션: 운영 현황 점검',
        detail: `${PILLAR_COPY.전략_기획} 인사이트와 현재 경고 상태를 함께 검토해 우선순위를 정리하세요.`,
      };

  const renderSummaryMetric = (card) => (
    <div key={card.id} className="dashboard-summary-card">
      <div className="dashboard-summary-card__header">
        <h3 className="metric-label">{card.label}</h3>
        {card.id === 'demand-index' && <span className="dashboard-summary-card__tag">핵심 신호</span>}
      </div>
      <div className="dashboard-summary-card__valueRow">
        {card.id === 'demand-index' ? (
          <TierBadge tier={card.value} />
        ) : (
          <span className="metric-value">{card.value}</span>
        )}
      </div>
      {card.trend && (
        <div className={card.trendDirection === 'up' ? 'trend-up' : card.trendDirection === 'down' ? 'trend-down' : 'trend-flat'}>
          {card.trendDirection === 'up' && (
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><polyline points="23 6 13.5 15.5 8.5 10.5 1 18"></polyline><polyline points="17 6 23 6 23 12"></polyline></svg>
          )}
          {card.trendDirection === 'down' && (
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><polyline points="23 18 13.5 8.5 8.5 13.5 1 6"></polyline><polyline points="17 18 23 18 23 12"></polyline></svg>
          )}
          {card.trendDirection === 'flat' && (
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><line x1="3" y1="12" x2="21" y2="12"></line></svg>
          )}
          <span>{card.trend}{card.trendLabel ? ` ${card.trendLabel}` : ''}</span>
        </div>
      )}
      <p className="dashboard-summary-card__description">
        {card.id === 'demand-index' ? (
          <>
            {PILLAR_COPY.전략_기획}과 {PILLAR_COPY.마케팅_매출_연계} 우선순위를 정할 때<br />기준이 되는 현재 수요 신호입니다.
          </>
        ) : (
          `${PILLAR_COPY.운영_효율화} 관점에서 지금 확인해야 할 기본 운영 지표입니다.`
        )}
      </p>
    </div>
  );

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
          <p className="page-subtitle dashboard-subtitle">{PILLAR_COPY.운영_효율화}, {PILLAR_COPY.마케팅_매출_연계}, {PILLAR_COPY.전략_기획}을 한 화면에서 연결하는 운영 커맨드 센터</p>
        </div>
        <div className="dashboard-header-controls">
          <FieldSelector
            value={field}
            onChange={setField}
            className="dashboard-header-select-wrapper"
            selectClassName="dashboard-header-matched-control"
            style={{ marginBottom: 0 }}
          />
          <button
            type="button"
            className="btn dashboard-header-matched-control dashboard-header-matched-btn"
            onClick={() => setRefreshKey(k => k + 1)}
            style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 'var(--space-1)', whiteSpace: 'nowrap' }}
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

      {SHOW_DEMO_SWITCHER && renderDemoSwitcher()}

      <section className="dashboard-priority-panel">
        <div className="dashboard-priority-panel__header">
          <div>
            <p className="dashboard-priority-panel__eyebrow">첫 화면 요약</p>
            <h2 className="dashboard-priority-panel__title">지금 확인해야 할 수요 신호, 운영 리스크, 다음 액션</h2>
            <p className="dashboard-priority-panel__description">
              {PILLAR_COPY.운영_효율화}와 {PILLAR_COPY.마케팅_매출_연계} 대응을 바로 시작할 수 있도록 현재 상태를 우선순위 중심으로 재정리했습니다.
            </p>
          </div>
        </div>

        {summary.state === 'loading' && (
          <StatusPanel variant="loading" title="데이터 로딩 중" message="우선순위 요약을 불러오고 있습니다." />
        )}
        {summary.state === 'error' && (
          <StatusPanel variant="error" title="오류 발생" message={summary.error} />
        )}
        {summary.state === 'empty' && (
          <StatusPanel variant="empty" title="데이터 없음" message="우선순위를 정리할 요약 지표가 없습니다." />
        )}

        {summary.state === 'success' && (
          <div className="dashboard-priority-grid">
            <div className="card dashboard-priority-card dashboard-priority-card--signal">
              <p className="dashboard-priority-card__eyebrow">현재 수요 신호</p>
              <div className="dashboard-priority-card__body" style={{ flex: 1 }}>
                {demandSignalCard ? renderSummaryMetric(demandSignalCard) : (
                  <StatusPanel variant="empty" message="수요 신호를 계산할 수 없습니다." />
                )}
              </div>
            </div>

            <div className="card dashboard-priority-card dashboard-priority-card--risk">
              <div className="dashboard-priority-card__headerRow">
                <p className="dashboard-priority-card__eyebrow">긴급 운영 리스크</p>
                {alertItems.length > 0 && <span className="dashboard-alert-count">{alertItems.length}건</span>}
              </div>
              {alerts.state === 'loading' && <StatusPanel variant="loading" message="리스크 신호를 정리 중입니다." />}
              {alerts.state === 'error' && <StatusPanel variant="error" title="오류" message={alerts.error} />}
              {alerts.state === 'empty' && <StatusPanel variant="empty" message="모든 시스템이 정상입니다. 즉시 대응이 필요한 리스크는 없습니다." />}
              {alerts.state === 'success' && primaryAlert && <AlertPanel alerts={[primaryAlert]} />}
            </div>

            <div className="card dashboard-priority-card dashboard-priority-card--action">
              <div>
                <p className="dashboard-priority-card__eyebrow">다음 액션</p>
                <h3 className="dashboard-action-title">{primaryAction.title}</h3>
                <p className="dashboard-action-description">{primaryAction.detail}</p>
              </div>
              <div className="dashboard-action-links" style={{ marginTop: 'auto' }}>
                <button type="button" className="btn btn-primary dashboard-action-button" onClick={() => setRefreshKey((k) => k + 1)}>
                  추천 상태 다시 확인
                </button>
                <p className="dashboard-action-helper">
                  바로가기 대신 현재 페이지에서 상태를 새로 불러와
                  <br />
                  우선순위를 다시 판단합니다.
                </p>
              </div>
            </div>
          </div>
        )}
      </section>

      {summary.state === 'success' && supportingSummaryCards.length > 0 && (
        <section className="dashboard-secondary-summary">
          <div className="dashboard-section-header">
            <div>
              <p className="dashboard-section-header__eyebrow">운영 기준선</p>
              <h2 className="dashboard-section-header__title">현재 운영 효율화에 필요한 기본 지표</h2>
            </div>
          </div>
          <div className="grid-auto-fit dashboard-summary-grid">
            {supportingSummaryCards.map(renderSummaryMetric)}
          </div>
        </section>
      )}

      <div className="grid-auto-fit dashboard-detail-grid">
        <div className="card">
          <div className="dashboard-card-header">
            <div>
              <h2 className="card-header">예상 수요 트렌드</h2>
              <p className="dashboard-card-header__description">{PILLAR_COPY.전략_기획} 판단을 위해 최근 수요 흐름과 예측 범위를 함께 확인합니다.</p>
            </div>
            <span className="dashboard-header-badge">최근 30일</span>
          </div>
          {chart.state === 'loading' && <StatusPanel variant="loading" message="수요 예측 데이터를 분석 중입니다..." />}
          {chart.state === 'error' && <StatusPanel variant="error" title="오류" message={chart.error} />}
          {chart.state === 'empty' && <StatusPanel variant="empty" message="선택한 기간에 대한 차트 데이터가 없습니다." />}
          {chart.state === 'success' && <DemandChart data={chart.data} />}
        </div>

        <div className="card">
          <div className="dashboard-card-header">
            <div>
              <h2 className="card-header">시스템 알림</h2>
              <p className="dashboard-card-header__description">{PILLAR_COPY.운영_효율화}와 {PILLAR_COPY.마케팅_매출_연계}에 영향을 주는 전체 경고 목록입니다.</p>
            </div>
            {alerts.state === 'success' && alerts.data?.length > 0 && (
              <span className="dashboard-alert-count">{alerts.data.length}건</span>
            )}
          </div>
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
