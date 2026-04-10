import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { LineChart, Line, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ReferenceLine, ResponsiveContainer } from 'recharts';
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

  const fetchData = async () => {
    setLoading(true);
    setError(null);
    try {
      const [lead, timing] = await Promise.all([
        getLeadConversion({ field }),
        getMarketingTiming({ field }),
      ]);
      setLeadData(lead.data);
      setTimingData(timing.data);
    } catch {
      setError('데이터를 불러오는 중 오류가 발생했습니다.');
    }
    setLoading(false);
  };

  useEffect(() => {
    fetchData();
  }, [field]);

  const conversionTrendData = leadData?.conversion_rate_trend
    ? leadData.conversion_rate_trend.map((v, i) => ({ week: `${i + 1}주`, rate: parseFloat((v * 100).toFixed(1)) }))
    : [];

  const consultationTrendData = leadData?.consultation_count_trend
    ? leadData.consultation_count_trend.map((v, i) => ({ week: `${i + 1}주`, count: v }))
    : [];

  const targetRatePercent = leadData?.target_conversion_rate != null
    ? parseFloat((leadData.target_conversion_rate * 100).toFixed(1))
    : null;

  const conversionChangeRate = leadData?.estimated_conversions != null && leadData?.previous_conversions != null && leadData.previous_conversions !== 0
    ? ((leadData.estimated_conversions - leadData.previous_conversions) / leadData.previous_conversions * 100).toFixed(1)
    : null;

  const currentTierKey = leadData?.current_demand_tier?.toLowerCase();

  const tierColors = {
    high: { bg: 'var(--color-success-bg)', text: 'var(--color-success-text)', border: '#86efac' },
    mid: { bg: 'var(--color-warning-bg)', text: 'var(--color-warning-text)', border: '#fcd34d' },
    low: { bg: 'var(--color-error-bg)', text: 'var(--color-error-text)', border: '#fca5a5' },
  };

  return (
    <div>
      <div className="page-header">
        <div>
          <h1 className="page-title">
            마케팅 분석
            <span className="badge">데모 버전</span>
          </h1>
          <p className="page-subtitle">잠재 수강생 전환 예측과 수요 등급별 광고 타이밍을 분석합니다.</p>
        </div>
        <button
          onClick={fetchData}
          disabled={loading}
          className="btn-primary"
          style={{ alignSelf: 'flex-start', display: 'flex', alignItems: 'center', gap: 'var(--space-2)' }}
        >
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
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

          {/* SECTION A: 잠재 수강생 전환 예측 */}
          <div className="card">
            <h2 className="card-header">잠재 수강생 전환 예측</h2>

            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: 'var(--space-6)', marginBottom: 'var(--space-6)' }}>
              <div style={{ backgroundColor: 'var(--color-background)', padding: 'var(--space-4)', borderRadius: 'var(--radius-md)' }}>
                <h3 className="metric-label">예상 전환 수</h3>
                <div className="metric-value" style={{ color: 'var(--color-primary)', display: 'flex', alignItems: 'baseline', gap: 'var(--space-2)' }}>
                  {leadData?.estimated_conversions ?? '-'}
                  <span style={{ fontSize: '1rem', fontWeight: '500', color: 'var(--color-text-muted)' }}>명</span>
                  {conversionChangeRate !== null && (
                    <span style={{
                      fontSize: '0.875rem',
                      fontWeight: '600',
                      color: parseFloat(conversionChangeRate) >= 0 ? 'var(--color-success-text)' : 'var(--color-error-text)',
                    }}>
                      {parseFloat(conversionChangeRate) >= 0 ? `+${conversionChangeRate}%` : `${conversionChangeRate}%`}
                    </span>
                  )}
                </div>
                {leadData?.previous_conversions != null && (
                  <div style={{ fontSize: '0.75rem', color: 'var(--color-text-muted)', marginTop: 'var(--space-1)' }}>
                    전월: {leadData.previous_conversions}명
                  </div>
                )}
              </div>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(350px, 1fr))', gap: 'var(--space-6)', marginBottom: 'var(--space-6)' }}>
              <div>
                <h3 style={{ fontSize: '0.875rem', fontWeight: '600', color: 'var(--color-text-muted)', marginBottom: 'var(--space-3)' }}>전환율 트렌드 (%)</h3>
                <ResponsiveContainer width="100%" height={250}>
                  <LineChart data={conversionTrendData}>
                    <CartesianGrid strokeDasharray="3 3" stroke="var(--color-border)" />
                    <XAxis dataKey="week" tick={{ fontSize: 12, fill: 'var(--color-text-muted)' }} />
                    <YAxis tick={{ fontSize: 12, fill: 'var(--color-text-muted)' }} unit="%" />
                    <Tooltip formatter={(v) => [`${v}%`, '전환율']} />
                    {targetRatePercent !== null && (
                      <ReferenceLine
                        y={targetRatePercent}
                        stroke="#f59e0b"
                        strokeDasharray="4 4"
                        label={{ value: `목표 ${targetRatePercent}%`, position: 'insideTopRight', fontSize: 11, fill: '#f59e0b' }}
                      />
                    )}
                    <Line type="monotone" dataKey="rate" stroke="#4F46E5" strokeWidth={2} dot={{ r: 4 }} activeDot={{ r: 6 }} />
                  </LineChart>
                </ResponsiveContainer>
              </div>

              <div>
                <h3 style={{ fontSize: '0.875rem', fontWeight: '600', color: 'var(--color-text-muted)', marginBottom: 'var(--space-3)' }}>상담 건수 트렌드</h3>
                <ResponsiveContainer width="100%" height={250}>
                  <BarChart data={consultationTrendData}>
                    <CartesianGrid strokeDasharray="3 3" stroke="var(--color-border)" />
                    <XAxis dataKey="week" tick={{ fontSize: 12, fill: 'var(--color-text-muted)' }} />
                    <YAxis tick={{ fontSize: 12, fill: 'var(--color-text-muted)' }} />
                    <Tooltip formatter={(v) => [v, '상담 건수']} />
                    <Bar dataKey="count" fill="#4F46E5" radius={[4, 4, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </div>

            {leadData?.recommendations?.length > 0 && (
              <div style={{ backgroundColor: 'var(--color-info-bg)', padding: 'var(--space-4)', borderRadius: 'var(--radius-md)' }}>
                <h3 style={{ fontSize: '0.875rem', fontWeight: '600', color: 'var(--color-info-text)', marginBottom: 'var(--space-3)' }}>추천 사항</h3>
                <ul style={{ margin: 0, paddingLeft: 'var(--space-5)', display: 'flex', flexDirection: 'column', gap: 'var(--space-2)' }}>
                  {leadData.recommendations.map((rec, i) => {
                    const text = typeof rec === 'string' ? rec : rec.text;
                    const link = typeof rec === 'object' && rec.link ? rec.link : null;
                    return (
                      <li key={i} style={{ color: 'var(--color-info-text)', fontSize: '0.875rem', display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 'var(--space-3)' }}>
                        <span>{text}</span>
                        {link && (
                          <Link
                            to={link}
                            style={{ fontSize: '0.75rem', color: 'var(--color-primary)', textDecoration: 'none', whiteSpace: 'nowrap', fontWeight: '600' }}
                          >
                            바로가기 →
                          </Link>
                        )}
                      </li>
                    );
                  })}
                </ul>
              </div>
            )}
          </div>

          {/* SECTION B: 광고 타이밍 추천 */}
          <div className="card">
            <h2 className="card-header">광고 타이밍 추천</h2>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: 'var(--space-4)' }}>
              {(Array.isArray(timingData) ? timingData : timingData?.tiers)?.map((item) => {
                const tierKey = item.demand_tier?.toLowerCase();
                const colors = tierColors[tierKey] || tierColors.mid;
                const isActive = currentTierKey && tierKey === currentTierKey;
                return (
                  <div
                    key={item.demand_tier}
                    style={{
                      backgroundColor: colors.bg,
                      border: isActive ? `2px solid ${colors.border}` : `1px solid ${colors.border}`,
                      borderRadius: 'var(--radius-md)',
                      padding: 'var(--space-5)',
                      boxShadow: isActive ? '0 0 0 3px rgba(0,0,0,0.08)' : 'none',
                      opacity: currentTierKey && !isActive ? 0.5 : 1,
                      transition: 'box-shadow 0.2s, opacity 0.2s',
                    }}
                  >
                    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 'var(--space-3)' }}>
                      <TierBadge tier={item.demand_tier} />
                      {isActive && (
                        <span style={{ fontSize: '0.7rem', fontWeight: '700', color: colors.text, background: colors.border, padding: '2px 6px', borderRadius: '999px' }}>현재</span>
                      )}
                    </div>
                    <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-3)' }}>
                      <div>
                        <div style={{ fontSize: '0.75rem', color: colors.text, fontWeight: '600', marginBottom: 'var(--space-1)' }}>광고 시작</div>
                        <div style={{ fontSize: '1.5rem', fontWeight: '700', color: colors.text }}>
                          {item.ad_launch_weeks_before}주 전
                        </div>
                      </div>
                      <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                        <div>
                          <div style={{ fontSize: '0.75rem', color: colors.text, opacity: 0.8 }}>얼리버드</div>
                          <div style={{ fontWeight: '600', color: colors.text }}>{item.earlybird_duration_days}일</div>
                        </div>
                        <div>
                          <div style={{ fontSize: '0.75rem', color: colors.text, opacity: 0.8 }}>할인율</div>
                          <div style={{ fontWeight: '600', color: colors.text }}>{item.discount_rate}%</div>
                        </div>
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>

        </div>
      )}
    </div>
  );
};

export default Marketing;
