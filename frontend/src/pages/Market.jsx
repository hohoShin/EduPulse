import React, { useState, useEffect } from 'react';
import { PieChart, Pie, Cell, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import StatusPanel from '../components/StatusPanel.jsx';
import FieldSelector from '../components/FieldSelector.jsx';
import TierBadge from '../components/TierBadge.jsx';
import RiskGauge from '../components/RiskGauge.jsx';
import ScoreBar from '../components/ScoreBar.jsx';
import { getDemographics, getCompetitors, getOptimalStart } from '../api/adapters/index.js';

const PIE_COLORS = ['#4F46E5', '#92400E', '#166534'];

const trendBadgeStyle = {
  증가: { backgroundColor: 'var(--color-success-bg)', color: 'var(--color-success-text)' },
  안정: { backgroundColor: 'var(--color-info-bg)', color: 'var(--color-info-text)' },
  감소: { backgroundColor: 'var(--color-error-bg)', color: 'var(--color-error-text)' },
};

const formatKoreanDate = (dateStr) => {
  if (!dateStr) return '';
  return new Date(dateStr).toLocaleDateString('ko-KR', { year: 'numeric', month: 'long', day: 'numeric' });
};

const Market = () => {
  const [field, setField] = useState('coding');
  const [demographicsData, setDemographicsData] = useState(null);
  const [competitorsData, setCompetitorsData] = useState(null);
  const [optimalStartData, setOptimalStartData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    async function fetchData() {
      const [demo, comp, optimal] = await Promise.all([
        getDemographics({ field }),
        getCompetitors({ field }),
        getOptimalStart({ field }),
      ]);
      setDemographicsData(demo.data);
      setCompetitorsData(comp.data);
      setOptimalStartData(optimal.data);
      setLoading(false);
    }
    fetchData();
  }, [field]);

  const ageDistData = demographicsData?.age_distribution
    ? Object.entries(demographicsData.age_distribution).map(([name, value]) => ({ name, value }))
    : [];

  const purposeDistData = demographicsData?.purpose_distribution
    ? Object.entries(demographicsData.purpose_distribution).map(([name, value]) => ({ name, value }))
    : [];

  const trendLabel = demographicsData?.trend;
  const trendStyle = trendBadgeStyle[trendLabel] || trendBadgeStyle['안정'];

  const saturationIndex = competitorsData?.saturation_index ?? 0;
  const saturationNormalized = Math.min(saturationIndex / 2, 1);
  const saturationLevel = saturationIndex >= 1.5 ? 'high' : saturationIndex >= 0.8 ? 'mid' : 'low';

  return (
    <div>
      <div className="page-header">
        <div>
          <h1 className="page-title">
            시장 분석
            <span className="badge">데모 버전</span>
          </h1>
          <p className="page-subtitle">수강생 인구통계, 경쟁 학원 동향, 최적 개강일을 분석합니다.</p>
        </div>
      </div>

      <div style={{ marginBottom: 'var(--space-6)' }}>
        <FieldSelector value={field} onChange={setField} />
      </div>

      {loading ? (
        <div className="card" style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', minHeight: '300px' }}>
          <StatusPanel variant="loading" title="시장 데이터 분석 중..." message="인구통계 및 경쟁 현황을 불러오고 있습니다." />
        </div>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-6)' }}>

          {/* SECTION A: 수강생 인구통계 */}
          <div className="card">
            <h2 className="card-header">
              수강생 인구통계
              {trendLabel && (
                <span style={{ ...trendStyle, fontSize: '0.75rem', fontWeight: '600', padding: '2px 10px', borderRadius: 'var(--radius-full)' }}>
                  {trendLabel}
                </span>
              )}
            </h2>

            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: 'var(--space-6)' }}>
              <div>
                <h3 style={{ fontSize: '0.875rem', fontWeight: '600', color: 'var(--color-text-muted)', marginBottom: 'var(--space-3)' }}>연령대 분포</h3>
                <ResponsiveContainer width="100%" height={250}>
                  <PieChart>
                    <Pie
                      data={ageDistData}
                      cx="50%"
                      cy="50%"
                      outerRadius={90}
                      dataKey="value"
                      label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                    >
                      {ageDistData.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={PIE_COLORS[index % PIE_COLORS.length]} />
                      ))}
                    </Pie>
                    <Tooltip formatter={(v) => [v, '비율']} />
                  </PieChart>
                </ResponsiveContainer>
              </div>

              <div>
                <h3 style={{ fontSize: '0.875rem', fontWeight: '600', color: 'var(--color-text-muted)', marginBottom: 'var(--space-3)' }}>수강 목적 분포</h3>
                <ResponsiveContainer width="100%" height={250}>
                  <BarChart data={purposeDistData} layout="vertical">
                    <CartesianGrid strokeDasharray="3 3" stroke="var(--color-border)" />
                    <XAxis type="number" tick={{ fontSize: 12, fill: 'var(--color-text-muted)' }} />
                    <YAxis type="category" dataKey="name" tick={{ fontSize: 12, fill: 'var(--color-text-muted)' }} width={80} />
                    <Tooltip />
                    <Bar dataKey="value" fill="#4F46E5" radius={[0, 4, 4, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </div>
          </div>

          {/* SECTION B: 경쟁 학원 동향 */}
          <div className="card">
            <h2 className="card-header">경쟁 학원 동향</h2>

            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: 'var(--space-6)', marginBottom: 'var(--space-6)' }}>
              <div style={{ backgroundColor: 'var(--color-background)', padding: 'var(--space-4)', borderRadius: 'var(--radius-md)' }}>
                <h3 className="metric-label">신규 경쟁 학원</h3>
                <div className="metric-value" style={{ color: 'var(--color-primary)' }}>
                  {competitorsData?.competitor_openings ?? '-'}
                  <span style={{ fontSize: '1rem', fontWeight: '500', color: 'var(--color-text-muted)' }}>개</span>
                </div>
              </div>

              <div style={{ backgroundColor: 'var(--color-background)', padding: 'var(--space-4)', borderRadius: 'var(--radius-md)' }}>
                <h3 className="metric-label">경쟁 학원 평균 수강료</h3>
                <div className="metric-value" style={{ color: 'var(--color-primary)' }}>
                  {competitorsData?.competitor_avg_price
                    ? `${(competitorsData.competitor_avg_price / 10000).toLocaleString()}만원`
                    : '-'}
                </div>
              </div>
            </div>

            <div style={{ marginBottom: 'var(--space-5)' }}>
              <h3 style={{ fontSize: '0.875rem', fontWeight: '600', color: 'var(--color-text-muted)', marginBottom: 'var(--space-3)' }}>시장 포화도</h3>
              <RiskGauge score={saturationNormalized} level={saturationLevel} />
            </div>

            {competitorsData?.recommendation && (
              <div style={{ backgroundColor: 'var(--color-info-bg)', padding: 'var(--space-4)', borderRadius: 'var(--radius-md)' }}>
                <div style={{ fontSize: '0.875rem', color: 'var(--color-info-text)' }}>{competitorsData.recommendation}</div>
              </div>
            )}
          </div>

          {/* SECTION C: 최적 개강일 추천 */}
          <div className="card">
            <h2 className="card-header">최적 개강일 추천</h2>

            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: 'var(--space-4)' }}>
              {optimalStartData?.candidates?.map((candidate, i) => (
                <div
                  key={i}
                  style={{
                    border: `1px solid ${i === 0 ? 'var(--color-primary)' : 'var(--color-border)'}`,
                    borderRadius: 'var(--radius-md)',
                    padding: 'var(--space-4)',
                    backgroundColor: i === 0 ? 'var(--color-info-bg)' : 'var(--color-surface)',
                  }}
                >
                  <div style={{ fontSize: '0.875rem', fontWeight: '600', color: 'var(--color-text-main)', marginBottom: 'var(--space-2)' }}>
                    {formatKoreanDate(candidate.date)}
                  </div>

                  <div style={{ display: 'flex', alignItems: 'baseline', gap: 'var(--space-1)', marginBottom: 'var(--space-2)' }}>
                    <span style={{ fontSize: '1.5rem', fontWeight: '700', color: 'var(--color-primary)' }}>
                      {candidate.predicted_enrollment}
                    </span>
                    <span style={{ fontSize: '0.875rem', color: 'var(--color-text-muted)' }}>명</span>
                  </div>

                  <div style={{ marginBottom: 'var(--space-3)' }}>
                    <TierBadge tier={candidate.demand_tier} />
                  </div>

                  <ScoreBar score={candidate.score} recommended={i === 0} />
                </div>
              ))}
            </div>
          </div>

        </div>
      )}
    </div>
  );
};

export default Market;
