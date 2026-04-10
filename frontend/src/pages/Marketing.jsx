import React, { useState, useEffect } from 'react';
import { LineChart, Line, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import StatusPanel from '../components/StatusPanel.jsx';
import FieldSelector from '../components/FieldSelector.jsx';
import TierBadge from '../components/TierBadge.jsx';
import { getLeadConversion, getMarketingTiming } from '../api/adapters/index.js';

const Marketing = () => {
  const [field, setField] = useState('coding');
  const [leadData, setLeadData] = useState(null);
  const [timingData, setTimingData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    async function fetchData() {
      const [lead, timing] = await Promise.all([
        getLeadConversion({ field }),
        getMarketingTiming({ field }),
      ]);
      setLeadData(lead.data);
      setTimingData(timing.data);
      setLoading(false);
    }
    fetchData();
  }, [field]);

  const conversionTrendData = leadData?.conversion_rate_trend
    ? leadData.conversion_rate_trend.map((v, i) => ({ week: `${i + 1}주`, rate: parseFloat((v * 100).toFixed(1)) }))
    : [];

  const consultationTrendData = leadData?.consultation_count_trend
    ? leadData.consultation_count_trend.map((v, i) => ({ week: `${i + 1}주`, count: v }))
    : [];

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
      </div>

      <div style={{ marginBottom: 'var(--space-6)' }}>
        <FieldSelector value={field} onChange={setField} />
      </div>

      {loading ? (
        <div className="card" style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', minHeight: '300px' }}>
          <StatusPanel variant="loading" title="데이터 분석 중..." message="마케팅 데이터를 불러오고 있습니다." />
        </div>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-6)' }}>

          {/* SECTION A: 잠재 수강생 전환 예측 */}
          <div className="card">
            <h2 className="card-header">잠재 수강생 전환 예측</h2>

            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: 'var(--space-6)', marginBottom: 'var(--space-6)' }}>
              <div style={{ backgroundColor: 'var(--color-background)', padding: 'var(--space-4)', borderRadius: 'var(--radius-md)' }}>
                <h3 className="metric-label">예상 전환 수</h3>
                <div className="metric-value" style={{ color: 'var(--color-primary)' }}>
                  {leadData?.estimated_conversions ?? '-'}
                  <span style={{ fontSize: '1rem', fontWeight: '500', color: 'var(--color-text-muted)' }}> 명</span>
                </div>
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
                  {leadData.recommendations.map((rec, i) => (
                    <li key={i} style={{ color: 'var(--color-info-text)', fontSize: '0.875rem' }}>{rec}</li>
                  ))}
                </ul>
              </div>
            )}
          </div>

          {/* SECTION B: 광고 타이밍 추천 */}
          <div className="card">
            <h2 className="card-header">광고 타이밍 추천</h2>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: 'var(--space-4)' }}>
              {timingData?.tiers?.map((item) => {
                const tierKey = item.demand_tier?.toLowerCase();
                const colors = tierColors[tierKey] || tierColors.mid;
                return (
                  <div
                    key={item.demand_tier}
                    style={{
                      backgroundColor: colors.bg,
                      border: `1px solid ${colors.border}`,
                      borderRadius: 'var(--radius-md)',
                      padding: 'var(--space-5)',
                    }}
                  >
                    <div style={{ marginBottom: 'var(--space-3)' }}>
                      <TierBadge tier={item.demand_tier} />
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
