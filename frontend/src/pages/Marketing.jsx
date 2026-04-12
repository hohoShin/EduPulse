import { useState, useEffect, useCallback } from 'react';
import { Link } from 'react-router-dom';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import StatusPanel from '../components/StatusPanel.jsx';
import FieldSelector from '../components/FieldSelector.jsx';
import TierBadge from '../components/TierBadge.jsx';
import { getLeadConversion, getMarketingTiming } from '../api/adapters/index.js';

const Marketing = () => {
  const [field, setField] = useState('coding');
  const [leadData, setLeadData] = useState(null);
  const [timingData, setTimingData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchData = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [lead, timing] = await Promise.all([
        getLeadConversion({ field }),
        getMarketingTiming({ field }),
      ]);

      const errorState = [lead, timing].find((state) => state?.state === 'error');
      if (errorState) {
        setLeadData(null);
        setTimingData(null);
        setError(errorState.error || '데이터를 불러오는 중 오류가 발생했습니다.');
        return;
      }

      setLeadData(lead?.state === 'success' ? lead.data : null);
      setTimingData(timing?.state === 'success' ? timing.data : null);
    } catch {
      setLeadData(null);
      setTimingData(null);
      setError('데이터를 불러오는 중 오류가 발생했습니다.');
    } finally {
      setLoading(false);
    }
  }, [field]);

  useEffect(() => {
    const timerId = window.setTimeout(() => {
      void fetchData();
    }, 0);

    return () => window.clearTimeout(timerId);
  }, [fetchData]);

  const consultationTrendData = leadData?.consultation_count_trend
    ? leadData.consultation_count_trend.map((v, i) => ({ week: `${i + 1}주`, count: v }))
    : [];

  const conversionChangeRate = leadData?.estimated_conversions != null && leadData?.previous_conversions != null && leadData.previous_conversions !== 0
    ? ((leadData.estimated_conversions - leadData.previous_conversions) / leadData.previous_conversions * 100).toFixed(1)
    : null;

  const timingArray = Array.isArray(timingData) ? timingData : timingData?.tiers;
  const currentTierKey = leadData?.current_demand_tier?.toLowerCase() || timingArray?.[0]?.demand_tier?.toLowerCase() || 'mid';

  const tierColors = {
    high: { bg: 'var(--color-success-bg)', text: 'var(--color-success-text)', border: 'var(--color-success-border)' },
    mid: { bg: 'var(--color-warning-bg)', text: 'var(--color-warning-text)', border: 'var(--color-warning-border)' },
    low: { bg: 'var(--color-error-bg)', text: 'var(--color-error-text)', border: 'var(--color-error-border)' },
  };

  return (
    <div>
      <div className="page-header">
        <div>
          <h1 className="page-title">
            마케팅 분석
            <span className="badge">수익 전략 콕핏</span>
          </h1>
          <p className="page-subtitle">수요 예측을 기반으로 잠재 전환율을 극대화하고 최적의 광고 집행 타이밍을 결정합니다.</p>
        </div>
        <button
          type="button"
          onClick={fetchData}
          disabled={loading}
          className="btn-primary"
          style={{ alignSelf: 'flex-start', display: 'flex', alignItems: 'center', gap: 'var(--space-2)' }}
        >
          <svg aria-hidden="true" focusable="false" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <polyline points="23 4 23 10 17 10" /><polyline points="1 20 1 14 7 14" />
            <path d="M3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15" />
          </svg>
          새로고침
        </button>
      </div>

      <div style={{ marginBottom: 'var(--space-6)' }}>
        <FieldSelector value={field} onChange={setField} />
      </div>

      {error && (
        <div className="card" style={{ marginBottom: 'var(--space-6)' }}>
          <StatusPanel variant="error" title="데이터 로드 실패" message={error} />
        </div>
      )}

      {loading ? (
        <div className="card" style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', minHeight: '300px' }}>
          <StatusPanel variant="loading" title="데이터 분석 중..." message="마케팅 데이터를 불러오고 있습니다." />
        </div>
      ) : !error && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-6)' }}>

          <div className="dashboard-priority-panel">
            <div className="dashboard-priority-panel__header">
              <div>
                <h2 className="dashboard-priority-panel__eyebrow">핵심 지표</h2>
                <h3 className="dashboard-priority-panel__title">잠재 수강생 전환 예측</h3>
                <p className="dashboard-priority-panel__description">현재 유입된 문의와 상담 트렌드를 바탕으로 최종 결제 전환을 예상합니다.</p>
              </div>
            </div>

            <div className="dashboard-priority-grid">
              <div className="card dashboard-priority-card dashboard-priority-card--signal">
                <div className="dashboard-priority-card__headerRow">
                  <h3 className="metric-label" style={{ margin: 0, color: 'var(--color-primary)' }}>이번 달 예상 전환 수</h3>
                </div>
                <div className="dashboard-priority-card__body">
                  <div className="metric-value" style={{ display: 'flex', alignItems: 'baseline', gap: 'var(--space-2)' }}>
                    {leadData?.estimated_conversions ?? '-'}
                    <span style={{ fontSize: '1rem', fontWeight: '500', color: 'var(--color-text-muted)' }}>명</span>
                    {conversionChangeRate !== null && (
                      <span style={{
                        fontSize: '0.875rem',
                        fontWeight: '600',
                        color: parseFloat(conversionChangeRate) >= 0 ? 'var(--color-success-text)' : 'var(--color-error-text)',
                        backgroundColor: parseFloat(conversionChangeRate) >= 0 ? 'var(--color-success-bg)' : 'var(--color-error-bg)',
                        padding: '2px 8px',
                        borderRadius: 'var(--radius-full)'
                      }}>
                        {parseFloat(conversionChangeRate) >= 0 ? `+${conversionChangeRate}%` : `${conversionChangeRate}%`}
                      </span>
                    )}
                  </div>
                  {leadData?.previous_conversions != null && (
                    <div style={{ fontSize: '0.75rem', color: 'var(--color-text-muted)', display: 'flex', justifyContent: 'space-between', borderTop: '1px solid var(--color-border)', paddingTop: 'var(--space-2)' }}>
                      <span>전월 대비 변동</span>
                      <span>전월 {leadData.previous_conversions}명</span>
                    </div>
                  )}
                </div>
              </div>

              <div className="card dashboard-priority-card">
                <div className="dashboard-priority-card__headerRow">
                  <h3 className="metric-label" style={{ margin: 0 }}>최근 상담 트렌드</h3>
                </div>
                <div className="dashboard-priority-card__body" style={{ height: '150px', minHeight: 0 }}>
                  {consultationTrendData.length > 0 ? (
                    <ResponsiveContainer width="100%" height="100%">
                      <BarChart data={consultationTrendData} margin={{ top: 10, right: 10, bottom: 0, left: -20 }}>
                        <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="var(--color-border)" />
                        <XAxis dataKey="week" tick={{ fontSize: 10, fill: 'var(--color-text-muted)' }} axisLine={false} tickLine={false} />
                        <YAxis tick={{ fontSize: 10, fill: 'var(--color-text-muted)' }} axisLine={false} tickLine={false} width={40} />
                        <Tooltip formatter={(v) => [v, '건']} cursor={{ fill: 'var(--color-surface-hover)' }} contentStyle={{ borderRadius: 'var(--radius-md)', fontSize: '0.75rem', border: '1px solid var(--color-border)', boxShadow: 'var(--shadow-sm)' }} />
                        <Bar dataKey="count" fill="var(--color-primary)" radius={[4, 4, 0, 0]} maxBarSize={30} />
                      </BarChart>
                    </ResponsiveContainer>
                  ) : (
                    <div className="chart-empty-state" style={{ height: '100%', border: 'none', backgroundColor: 'transparent' }}>데이터가 없습니다</div>
                  )}
                </div>
              </div>

              <div className="card dashboard-priority-card dashboard-priority-card--action">
                <div className="dashboard-priority-card__headerRow">
                  <h3 className="metric-label" style={{ margin: 0, color: 'var(--color-info-text)' }}>추천 액션</h3>
                </div>
                <div className="dashboard-priority-card__body">
                  {leadData?.recommendations?.length > 0 ? (
                    <div className="dashboard-action-links">
                      {leadData.recommendations.map((rec, index) => {
                        let text = '';
                        let link = null;

                        if (typeof rec === 'string') {
                          text = rec;
                        } else if (rec && typeof rec === 'object') {
                          // Handle double-nested object from realAdapter + mock json
                          if (rec.text && typeof rec.text === 'object') {
                            text = rec.text.text || '';
                            link = rec.text.link || rec.link || null;
                          } else {
                            text = rec.text || '';
                            link = rec.link || null;
                          }
                        }

                        const itemKey = `rec-${index}-${link || text.slice(0, 10)}`;

                        return (
                          <div key={itemKey} style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-2)', paddingBottom: 'var(--space-2)', borderBottom: '1px dashed var(--color-info-border)' }}>
                            <span style={{ fontSize: '0.8125rem', color: 'var(--color-info-text)', fontWeight: '500', lineHeight: 1.4 }}>{text}</span>
                            {link && (
                              <Link to={link} className="btn" style={{ fontSize: '0.75rem', alignSelf: 'flex-start', backgroundColor: 'var(--color-surface)', borderColor: 'var(--color-info-border)' }}>
                                바로가기 →
                              </Link>
                            )}
                          </div>
                        );
                      })}
                    </div>
                  ) : (
                    <div style={{ fontSize: '0.8125rem', color: 'var(--color-text-muted)' }}>현재 실행 가능한 추천 액션이 없습니다.</div>
                  )}
                </div>
              </div>
            </div>
          </div>

          <div className="dashboard-section-header">
            <div>
              <h2 className="dashboard-section-header__eyebrow">실행 전략</h2>
              <h3 className="dashboard-section-header__title">광고 타이밍 추천</h3>
              <p className="dashboard-card-header__description">
                수요 등급에 맞춰 가장 효율적인 광고 시작 시점과 얼리버드 프로모션을 제안합니다.
              </p>
            </div>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: 'var(--space-4)' }}>
            {timingArray?.map((item) => {
              const tierKey = item.demand_tier?.toLowerCase();
              const colors = tierColors[tierKey] || tierColors.mid;
              const isActive = tierKey === currentTierKey;
              
              return (
                <div
                  key={item.demand_tier}
                  className="card timing-card"
                  style={{
                    display: 'flex',
                    flexDirection: 'column',
                    gap: 'var(--space-4)',
                    padding: 'var(--space-5)',
                    backgroundColor: 'var(--color-surface)',
                    borderColor: 'var(--color-border)',
                    position: 'relative',
                    overflow: 'hidden'
                  }}
                >
                  <div style={{
                    position: 'absolute',
                    top: 0,
                    left: 0,
                    width: '4px',
                    height: '100%',
                    backgroundColor: colors.text
                  }} />

                  <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between' }}>
                    <TierBadge tier={item.demand_tier} />
                    {isActive && (
                      <span style={{ 
                        fontSize: '0.7rem', 
                        fontWeight: '700', 
                        color: colors.text, 
                        backgroundColor: colors.bg,
                        border: `1px solid ${colors.border}`,
                        padding: '2px 8px', 
                        borderRadius: 'var(--radius-full)' 
                      }}>
                        현재 수요
                      </span>
                    )}
                  </div>

                  <div className="timing-card-body" style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-4)', marginTop: 'var(--space-2)' }}>
                    <div style={{ 
                      display: 'flex', 
                      alignItems: 'baseline', 
                      justifyContent: 'space-between',
                      paddingBottom: 'var(--space-3)',
                      borderBottom: `1px solid ${isActive ? 'var(--color-border)' : 'rgba(0,0,0,0.05)'}`
                    }}>
                      <span style={{ fontSize: '0.8125rem', fontWeight: '600', color: 'var(--color-text-muted)' }}>광고 시작 타이밍</span>
                      <div style={{ display: 'flex', alignItems: 'baseline', gap: 'var(--space-1)' }}>
                        <span style={{ fontSize: '1.75rem', fontWeight: '800', color: isActive ? colors.text : 'var(--color-text-main)', lineHeight: 1 }}>{item.ad_launch_weeks_before}</span>
                        <span style={{ fontSize: '0.875rem', fontWeight: '600', color: 'var(--color-text-muted)' }}>주 전</span>
                      </div>
                    </div>
                    
                    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 'var(--space-4)' }}>
                      <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-1)' }}>
                        <span style={{ fontSize: '0.75rem', fontWeight: '600', color: 'var(--color-text-muted)' }}>얼리버드 기간</span>
                        <span style={{ fontSize: '1.125rem', fontWeight: '700', color: 'var(--color-text-main)' }}>{item.earlybird_duration_days}일</span>
                      </div>
                      <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-1)' }}>
                        <span style={{ fontSize: '0.75rem', fontWeight: '600', color: 'var(--color-text-muted)' }}>권장 할인율</span>
                        <span style={{ fontSize: '1.125rem', fontWeight: '700', color: 'var(--color-text-main)' }}>{Math.round(item.discount_rate * 100)}%</span>
                      </div>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>

        </div>
      )}
    </div>
  );
};

export default Marketing;
