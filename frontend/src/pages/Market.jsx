import { useState, useEffect, useCallback } from 'react';
import { PieChart, Pie, Cell, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import StatusPanel from '../components/StatusPanel.jsx';
import FieldSelector from '../components/FieldSelector.jsx';
import TierBadge from '../components/TierBadge.jsx';
import RiskGauge from '../components/RiskGauge.jsx';
import ScoreBar from '../components/ScoreBar.jsx';
import { getDemographics, getCompetitors, getOptimalStart } from '../api/adapters/index.js';

const AGE_GROUP_COLORS = {
  '20대': '#8070ED',
  '30대': '#75C6BE',
  '40대 이상': '#ED864C',
};

const getAgeGroupColor = (group) => AGE_GROUP_COLORS[group] || 'var(--color-text-muted)';

const trendBadgeStyle = {
  증가: { backgroundColor: 'var(--color-success-bg)', color: 'var(--color-success-text)' },
  안정: { backgroundColor: 'var(--color-info-bg)', color: 'var(--color-info-text)' },
  감소: { backgroundColor: 'var(--color-error-bg)', color: 'var(--color-error-text)' },
};

const searchTrendStyle = {
  상승: { color: 'var(--color-success-text)' },
  안정: { color: 'var(--color-text-muted)' },
  하락: { color: 'var(--color-error-text)' },
};

const formatKoreanDate = (dateStr) => {
  if (!dateStr) return '';
  return new Date(dateStr).toLocaleDateString('ko-KR', { year: 'numeric', month: 'long', day: 'numeric' });
};

const formatDelta = (current, previous, unit) => {
  if (current == null || previous == null) return null;
  const delta = current - previous;
  if (delta === 0) return null;
  const sign = delta > 0 ? '+' : '';
  return { text: `${sign}${delta}${unit}`, up: delta > 0 };
};

const renderAgeDistributionLabel = ({ cx, cy, midAngle, outerRadius, percent, name }) => {
  const RADIAN = Math.PI / 180;
  const radius = outerRadius + 18;
  const x = cx + radius * Math.cos(-midAngle * RADIAN);
  const y = cy + radius * Math.sin(-midAngle * RADIAN);

  return (
    <text
      x={x}
      y={y}
      fill={getAgeGroupColor(name)}
      textAnchor={x > cx ? 'start' : 'end'}
      dominantBaseline="central"
      fontSize={12}
      fontWeight={600}
    >
      {`${name} ${(percent * 100).toFixed(0)}%`}
    </text>
  );
};

const Market = () => {
  const [field, setField] = useState('coding');
  const [demographicsData, setDemographicsData] = useState(null);
  const [competitorsData, setCompetitorsData] = useState(null);
  const [optimalStartData, setOptimalStartData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [startDate, setStartDate] = useState('');
  const [endDate, setEndDate] = useState('');

  const fetchData = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [demo, comp, optimal] = await Promise.all([
        getDemographics({ field }),
        getCompetitors({ field }),
        getOptimalStart({ field, startDate, endDate }),
      ]);

      const errorState = [demo, comp, optimal].find((state) => state?.state === 'error');
      if (errorState) {
        setDemographicsData(null);
        setCompetitorsData(null);
        setOptimalStartData(null);
        setError(errorState.error || '데이터를 불러오는 중 오류가 발생했습니다.');
        return;
      }

      setDemographicsData(demo?.state === 'success' ? demo.data : null);
      setCompetitorsData(comp?.state === 'success' ? comp.data : null);
      setOptimalStartData(optimal?.state === 'success' ? optimal.data : null);
    } catch (err) {
      setError(err?.message || '데이터를 불러오는 중 오류가 발생했습니다.');
    } finally {
      setLoading(false);
    }
  }, [field, startDate, endDate]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  const ageDistData = demographicsData?.age_distribution
    ? demographicsData.age_distribution.map((item) => ({ name: item.group, value: item.ratio }))
    : [];

  const purposeDistData = demographicsData?.purpose_distribution
    ? demographicsData.purpose_distribution.map((item) => ({ name: item.purpose, value: item.ratio }))
    : [];

  const totalStudents = demographicsData?.total_students ?? 0;

  const trendLabel = demographicsData?.trend;
  const trendStyle = trendBadgeStyle[trendLabel] || trendBadgeStyle['안정'];

  const saturationIndex = competitorsData?.saturation_index ?? 0;
  const saturationNormalized = Math.min(saturationIndex / 2, 1);
  const saturationLevel = saturationIndex >= 1.5 ? 'high' : saturationIndex >= 0.8 ? 'medium' : 'low';

  const openingsDelta = formatDelta(
    competitorsData?.competitor_openings,
    competitorsData?.previous_openings,
    '개'
  );
  const priceDelta = formatDelta(
    competitorsData?.competitor_avg_price != null ? competitorsData.competitor_avg_price / 10000 : null,
    competitorsData?.previous_avg_price != null ? competitorsData.previous_avg_price / 10000 : null,
    '만원'
  );

  return (
    <div>
      <div className="page-header">
        <div>
          <h1 className="page-title">
            시장 분석
            <span className="badge">전략 기획 보드</span>
          </h1>
          <p className="page-subtitle">타겟 수강생 파악부터 경쟁 동향을 거쳐 최적의 개강일을 결정하는 전략 기획 보드입니다.</p>
        </div>
        <button
          type="button"
          onClick={fetchData}
          className="btn btn-primary"
          style={{ width: 'auto' }}
        >
          데이터 갱신
        </button>
      </div>

      <div className="toolbar">
        <div className="toolbar-label">
          <svg width="16" height="16" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2" aria-hidden="true">
            <path strokeLinecap="round" strokeLinejoin="round" d="M3 4a1 1 0 011-1h16a1 1 0 011 1v2.586a1 1 0 01-.293.707l-6.414 6.414a1 1 0 00-.293.707V17l-4 4v-6.586a1 1 0 00-.293-.707L3.293 7.293A1 1 0 013 6.586V4z" />
          </svg>
          분석 조건
        </div>
        <FieldSelector value={field} onChange={setField} />
        <div style={{ width: '1px', height: '24px', backgroundColor: 'var(--color-border)', margin: '0 var(--space-2)' }}></div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-2)' }}>
          <label htmlFor="startDate" style={{ fontSize: '0.875rem', color: 'var(--color-text-muted)', whiteSpace: 'nowrap' }}>탐색 시작일</label>
          <input
            id="startDate"
            type="date"
            value={startDate}
            onChange={(e) => setStartDate(e.target.value)}
            className="form-control"
            style={{ padding: 'var(--space-1) var(--space-2)', width: 'auto', marginBottom: 0 }}
          />
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-2)' }}>
          <label htmlFor="endDate" style={{ fontSize: '0.875rem', color: 'var(--color-text-muted)', whiteSpace: 'nowrap' }}>탐색 종료일</label>
          <input
            id="endDate"
            type="date"
            value={endDate}
            onChange={(e) => setEndDate(e.target.value)}
            className="form-control"
            style={{ padding: 'var(--space-1) var(--space-2)', width: 'auto', marginBottom: 0 }}
          />
        </div>
      </div>

      {error ? (
        <StatusPanel variant="error" title="데이터 로드 실패" message={error} />
      ) : loading ? (
        <div className="card" style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', minHeight: '300px' }}>
          <StatusPanel variant="loading" title="시장 데이터 분석 중..." message="인구통계 및 경쟁 현황을 불러오고 있습니다." />
        </div>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-6)' }}>
          <div className="dashboard-priority-grid" style={{ gridTemplateColumns: '1fr 1fr', marginBottom: '0' }}>
            {/* SECTION A: 수강생 인구통계 */}
            <div className="card dashboard-priority-card dashboard-priority-card--risk">
              <div className="dashboard-card-header">
                <div>
                  <div className="dashboard-priority-card__eyebrow">Step 1. 타겟 분석</div>
                  <h2 className="dashboard-section-header__title" style={{ fontSize: '1.25rem' }}>
                    수강생 인구통계
                    {trendLabel && (
                      <span className="badge" style={{ ...trendStyle, padding: '2px 10px', marginLeft: 'var(--space-2)' }}>
                        {trendLabel}
                      </span>
                    )}
                  </h2>
                  <p className="dashboard-card-header__description">
                    현재 유입되는 주요 타겟 연령과 목적을 파악합니다.
                    {totalStudents > 0 && ` (총 ${totalStudents.toLocaleString()}명)`}
                  </p>
                </div>
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr', gap: 'var(--space-6)' }}>
                <div>
                  <h3 style={{ fontSize: '0.875rem', fontWeight: '600', color: 'var(--color-text-muted)', marginBottom: 'var(--space-3)' }}>연령대 분포</h3>
                  <ResponsiveContainer width="100%" height={250}>
                    <PieChart>
                      <Pie
                        data={ageDistData}
                        cx="50%"
                        cy="50%"
                        outerRadius={80}
                        dataKey="value"
                        label={renderAgeDistributionLabel}
                      >
                        {ageDistData.map((entry, index) => (
                          <Cell key={`age-cell-${entry.name}`} fill={getAgeGroupColor(entry.name)} />
                        ))}
                      </Pie>
                      <Tooltip
                        formatter={(v) => [
                          totalStudents > 0
                            ? `${(v * 100).toFixed(0)}% (${(v * totalStudents).toFixed(0)}명)`
                            : `${(v * 100).toFixed(0)}%`,
                          '비율'
                        ]}
                      />
                      <Legend formatter={(value) => <span style={{ color: getAgeGroupColor(value), fontWeight: 600 }}>{value}</span>} />
                    </PieChart>
                  </ResponsiveContainer>
                </div>

                <div>
                  <h3 style={{ fontSize: '0.875rem', fontWeight: '600', color: 'var(--color-text-muted)', marginBottom: 'var(--space-3)' }}>수강 목적 분포</h3>
                  <ResponsiveContainer width="100%" height={250}>
                    <BarChart data={purposeDistData} layout="vertical" margin={{ left: 10 }} barCategoryGap="12%">
                      <CartesianGrid strokeDasharray="3 3" stroke="var(--color-border)" />
                      <XAxis type="number" tick={{ fontSize: 12, fill: 'var(--color-text-muted)' }} />
                      <YAxis type="category" dataKey="name" tick={{ fontSize: 12, fill: 'var(--color-text-muted)' }} width={80} />
                      <Tooltip cursor={{ fill: 'rgba(0,0,0,0.05)' }} />
                      <Bar dataKey="value" barSize={12} fill="var(--color-primary)" radius={[0, 4, 4, 0]} />
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              </div>
            </div>

            {/* SECTION B: 경쟁 학원 동향 */}
            <div className="card dashboard-priority-card dashboard-priority-card--risk">
              <div className="dashboard-card-header">
                <div>
                  <div className="dashboard-priority-card__eyebrow">Step 2. 경쟁 환경</div>
                  <h2 className="dashboard-section-header__title" style={{ fontSize: '1.25rem' }}>경쟁 학원 동향</h2>
                  <p className="dashboard-card-header__description">주변 경쟁 학원의 신규 개설 및 수강료 변화를 확인합니다.</p>
                </div>
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: 'var(--space-4)', marginBottom: 'var(--space-6)' }}>
                <div className="brief-metric-card" style={{ boxShadow: 'none' }}>
                  <h3 className="brief-metric-label">신규 경쟁 학원</h3>
                  <div className="brief-metric-value" style={{ color: 'var(--color-primary)' }}>
                    {competitorsData?.competitor_openings ?? '-'}
                    <span style={{ fontSize: '1rem', fontWeight: '500', color: 'var(--color-text-muted)' }}>개</span>
                  </div>
                  {openingsDelta && (
                    <div className={openingsDelta.up ? 'trend-down' : 'trend-up'} style={{ marginTop: 'var(--space-1)' }}>
                      {openingsDelta.text} {openingsDelta.up ? '↑' : '↓'} 전분기 대비
                    </div>
                  )}
                </div>

                <div className="brief-metric-card" style={{ boxShadow: 'none' }}>
                  <h3 className="brief-metric-label">경쟁 학원 평균 수강료</h3>
                  <div className="brief-metric-value" style={{ color: 'var(--color-primary)' }}>
                    {competitorsData?.competitor_avg_price
                      ? `${(competitorsData.competitor_avg_price / 10000).toLocaleString()}만원`
                      : '-'}
                  </div>
                  {priceDelta && (
                    <div className={priceDelta.up ? 'trend-down' : 'trend-up'} style={{ marginTop: 'var(--space-1)' }}>
                      {priceDelta.text} {priceDelta.up ? '↑' : '↓'} 전분기 대비
                    </div>
                  )}
                </div>
              </div>

              <div style={{ marginBottom: 'var(--space-5)', padding: 'var(--space-4)', backgroundColor: 'var(--color-surface)', border: '1px solid var(--color-border)', borderRadius: 'var(--radius-md)' }}>
                <RiskGauge
                  score={saturationNormalized}
                  level={saturationLevel}
                  label="현재 지역 시장 포화도"
                  labels={{ high: '포화', medium: '보통', low: '여유' }}
                />
              </div>

              {competitorsData?.recommendation && (
                <div className="state-panel state-panel--info" style={{ marginTop: 'auto' }}>
                  <div className="state-panel__row">
                    <div className="state-panel__icon">
                      <svg width="20" height="20" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2" aria-hidden="true">
                        <path strokeLinecap="round" strokeLinejoin="round" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                      </svg>
                    </div>
                    <div className="state-panel__body">
                      <h4 className="state-panel__title" style={{ fontSize: '0.875rem' }}>경쟁 대응 조언</h4>
                      <p className="state-panel__message">{competitorsData.recommendation}</p>
                    </div>
                  </div>
                </div>
              )}
            </div>
          </div>

          {/* SECTION C: 최적 개강일 추천 */}
          <div className="dashboard-priority-panel" style={{ marginBottom: 0, marginTop: 'var(--space-4)' }}>
            <div className="dashboard-priority-panel__header">
              <div>
                <div className="dashboard-priority-panel__eyebrow">Step 3. 전략적 결론</div>
                <h2 className="dashboard-priority-panel__title">최적 개강일 추천</h2>
                <p className="dashboard-priority-panel__description">분석된 수요와 경쟁 환경을 바탕으로 산출된 가장 유리한 개강 일정입니다.</p>
              </div>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 320px', gap: 'var(--space-6)' }}>
              {optimalStartData?.top_candidates?.length > 0 && (() => {
                const primaryCandidate = optimalStartData.top_candidates[0];
                return (
                  <div className="card dashboard-priority-card dashboard-priority-card--signal" style={{ border: '2px solid var(--color-primary)', boxShadow: '0 10px 25px -5px rgba(79, 70, 229, 0.15)', height: '100%', display: 'flex', flexDirection: 'column' }}>
                    <div className="dashboard-priority-card__headerRow" style={{ alignItems: 'flex-start' }}>
                      <div>
                        <div style={{ fontSize: '0.875rem', fontWeight: 700, color: 'var(--color-primary)', marginBottom: 'var(--space-1)' }}>★ 최우선 추천 일정</div>
                        <div style={{ fontSize: '2.25rem', fontWeight: 800, color: 'var(--color-text-main)', letterSpacing: '-0.02em', lineHeight: 1.1 }}>
                          {formatKoreanDate(primaryCandidate.date)}
                        </div>
                      </div>
                      <TierBadge tier={primaryCandidate.demand_tier} />
                    </div>

                    <div style={{ marginTop: 'var(--space-4)', display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(120px, 1fr))', gap: 'var(--space-4)' }}>
                      <div className="brief-metric-card" style={{ border: 'none', backgroundColor: 'transparent', padding: '0' }}>
                        <div className="brief-metric-label">예상 수강생</div>
                        <div className="brief-metric-value" style={{ color: 'var(--color-primary)' }}>
                          {primaryCandidate.predicted_enrollment}<span style={{ fontSize: '1rem', color: 'var(--color-text-muted)' }}>명</span>
                        </div>
                      </div>
                      <div className="brief-metric-card" style={{ border: 'none', backgroundColor: 'transparent', padding: '0' }}>
                        <div className="brief-metric-label">경쟁 강도</div>
                        <div className="brief-metric-value">
                          {primaryCandidate.competitor_count ?? 0}<span style={{ fontSize: '1rem', color: 'var(--color-text-muted)' }}>개</span>
                        </div>
                      </div>
                      <div className="brief-metric-card" style={{ border: 'none', backgroundColor: 'transparent', padding: '0' }}>
                        <div className="brief-metric-label">검색 트렌드</div>
                        <div className="brief-metric-value" style={{ fontSize: '1.25rem', ...(searchTrendStyle[primaryCandidate.search_trend] || {}) }}>
                          {primaryCandidate.search_trend || '데이터 없음'}
                        </div>
                      </div>
                    </div>

                    <div style={{ marginTop: 'auto', paddingTop: 'var(--space-6)' }}>
                      <div style={{ padding: 'var(--space-5)', backgroundColor: 'var(--color-surface)', borderRadius: 'var(--radius-md)', border: '1px solid var(--color-border)' }}>
                        <ScoreBar score={primaryCandidate.composite_score} recommended={true} />
                        <div style={{ margin: 'var(--space-4) 0 0 0', fontSize: '0.925rem', color: 'var(--color-text-muted)', lineHeight: 1.6, borderTop: '1px dashed var(--color-border)', paddingTop: 'var(--space-4)' }}>
                          <p style={{ margin: 0, fontWeight: 500, color: 'var(--color-text-main)', marginBottom: 'var(--space-2)' }}>추천 사유:</p>
                          {ageDistData?.[0]?.name && trendLabel ? (
                            `현재 핵심 타겟인 ${ageDistData[0].name}의 수요가 ${trendLabel === '상승' || trendLabel === '증가' ? '증가' : '안정적으로 유지'}되고 있으며, `
                          ) : ''}
                          경쟁 학원의 견제가 상대적으로 낮을 것으로 예측되는 구간입니다. 
                          시장 매력도 {primaryCandidate.composite_score}점으로, <strong>가장 높은 학생 전환율</strong>이 기대되는 시점입니다.
                        </div>
                      </div>
                    </div>
                  </div>
                );
              })()}

              <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-4)', height: '100%' }}>
                <h3 style={{ fontSize: '0.875rem', fontWeight: 700, color: 'var(--color-text-muted)', margin: 0, textTransform: 'uppercase', letterSpacing: '0.05em' }}>대안 일정</h3>
                <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-3)' }}>
                  {optimalStartData?.top_candidates?.slice(1).map((candidate) => (
                    <div
                      key={`alt-candidate-${candidate.date}`}
                      className="card"
                      style={{ padding: 'var(--space-4)', display: 'flex', flexDirection: 'column', gap: 'var(--space-3)' }}
                    >
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                        <div style={{ fontSize: '1rem', fontWeight: 700, color: 'var(--color-text-main)' }}>
                          {formatKoreanDate(candidate.date)}
                        </div>
                        <TierBadge tier={candidate.demand_tier} />
                      </div>
                      
                      <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.875rem' }}>
                        <span style={{ color: 'var(--color-text-muted)' }}>예상 수강: <strong style={{ color: 'var(--color-text-main)' }}>{candidate.predicted_enrollment}명</strong></span>
                        <span style={{ color: 'var(--color-text-muted)' }}>점수: <strong style={{ color: 'var(--color-text-main)' }}>{candidate.composite_score}점</strong></span>
                      </div>
                    </div>
                  ))}
                  {(!optimalStartData?.top_candidates || optimalStartData.top_candidates.length <= 1) && (
                    <div className="state-panel state-panel--empty">
                      대안 일정이 없습니다.
                    </div>
                  )}
                </div>
              </div>
            </div>
          </div>

        </div>
      )}
    </div>
  );
};

export default Market;
