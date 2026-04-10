import React, { useState, useEffect, useCallback } from 'react';
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
      setDemographicsData(demo.data);
      setCompetitorsData(comp.data);
      setOptimalStartData(optimal.data);
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
  const saturationLevel = saturationIndex >= 1.5 ? 'high' : saturationIndex >= 0.8 ? 'mid' : 'low';

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
            <span className="badge">데모 버전</span>
          </h1>
          <p className="page-subtitle">수강생 인구통계, 경쟁 학원 동향, 최적 개강일을 분석합니다.</p>
        </div>
        <button
          onClick={fetchData}
          style={{
            padding: 'var(--space-2) var(--space-4)',
            backgroundColor: 'var(--color-primary)',
            color: '#fff',
            border: 'none',
            borderRadius: 'var(--radius-md)',
            fontSize: '0.875rem',
            fontWeight: '600',
            cursor: 'pointer',
          }}
        >
          새로고침
        </button>
      </div>

      <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-4)', marginBottom: 'var(--space-6)', flexWrap: 'wrap' }}>
        <FieldSelector value={field} onChange={setField} />
        <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-2)' }}>
          <label style={{ fontSize: '0.875rem', color: 'var(--color-text-muted)', whiteSpace: 'nowrap' }}>시작일</label>
          <input
            type="date"
            value={startDate}
            onChange={(e) => setStartDate(e.target.value)}
            style={{
              padding: 'var(--space-1) var(--space-2)',
              border: '1px solid var(--color-border)',
              borderRadius: 'var(--radius-sm)',
              fontSize: '0.875rem',
              color: 'var(--color-text-main)',
              backgroundColor: 'var(--color-surface)',
            }}
          />
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-2)' }}>
          <label style={{ fontSize: '0.875rem', color: 'var(--color-text-muted)', whiteSpace: 'nowrap' }}>종료일</label>
          <input
            type="date"
            value={endDate}
            onChange={(e) => setEndDate(e.target.value)}
            style={{
              padding: 'var(--space-1) var(--space-2)',
              border: '1px solid var(--color-border)',
              borderRadius: 'var(--radius-sm)',
              fontSize: '0.875rem',
              color: 'var(--color-text-main)',
              backgroundColor: 'var(--color-surface)',
            }}
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

          {/* SECTION A: 수강생 인구통계 */}
          <div className="card">
            <h2 className="card-header">
              수강생 인구통계
              {trendLabel && (
                <span style={{ ...trendStyle, fontSize: '0.75rem', fontWeight: '600', padding: '2px 10px', borderRadius: 'var(--radius-full)' }}>
                  {trendLabel}
                </span>
              )}
              {totalStudents > 0 && (
                <span style={{ fontSize: '0.75rem', color: 'var(--color-text-muted)', fontWeight: '400', marginLeft: 'var(--space-2)' }}>
                  총 {totalStudents.toLocaleString()}명
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
                      outerRadius={80}
                      dataKey="value"
                      label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                    >
                      {ageDistData.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={PIE_COLORS[index % PIE_COLORS.length]} />
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
                    <Legend />
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
                {openingsDelta && (
                  <div style={{ fontSize: '0.75rem', fontWeight: '600', color: openingsDelta.up ? 'var(--color-error-text)' : 'var(--color-success-text)', marginTop: 'var(--space-1)' }}>
                    {openingsDelta.text} {openingsDelta.up ? '↑' : '↓'} 전분기 대비
                  </div>
                )}
              </div>

              <div style={{ backgroundColor: 'var(--color-background)', padding: 'var(--space-4)', borderRadius: 'var(--radius-md)' }}>
                <h3 className="metric-label">경쟁 학원 평균 수강료</h3>
                <div className="metric-value" style={{ color: 'var(--color-primary)' }}>
                  {competitorsData?.competitor_avg_price
                    ? `${(competitorsData.competitor_avg_price / 10000).toLocaleString()}만원`
                    : '-'}
                </div>
                {priceDelta && (
                  <div style={{ fontSize: '0.75rem', fontWeight: '600', color: priceDelta.up ? 'var(--color-error-text)' : 'var(--color-success-text)', marginTop: 'var(--space-1)' }}>
                    {priceDelta.text} {priceDelta.up ? '↑' : '↓'} 전분기 대비
                  </div>
                )}
              </div>
            </div>

            <div style={{ marginBottom: 'var(--space-5)' }}>
              <h3 style={{ fontSize: '0.875rem', fontWeight: '600', color: 'var(--color-text-muted)', marginBottom: 'var(--space-3)' }}>시장 포화도</h3>
              <RiskGauge
                score={saturationNormalized}
                level={saturationLevel}
                label="포화도"
                labels={{ high: '포화', medium: '보통', low: '여유' }}
              />
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
              {optimalStartData?.top_candidates?.map((candidate, i) => (
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

                  <ScoreBar score={candidate.composite_score} recommended={i === 0} />

                  {(candidate.competitor_count != null || candidate.search_trend) && (
                    <div style={{ fontSize: '0.75rem', color: 'var(--color-text-muted)', marginTop: 'var(--space-2)', display: 'flex', gap: 'var(--space-2)', flexWrap: 'wrap' }}>
                      {candidate.competitor_count != null && (
                        <span>경쟁 {candidate.competitor_count}개</span>
                      )}
                      {candidate.search_trend && (
                        <span style={searchTrendStyle[candidate.search_trend] || {}}>
                          검색 {candidate.search_trend}
                        </span>
                      )}
                    </div>
                  )}
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
