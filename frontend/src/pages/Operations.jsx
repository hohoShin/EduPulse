import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import StatusPanel from '../components/StatusPanel.jsx';
import RiskGauge from '../components/RiskGauge.jsx';
import { getClosureRisk, getScheduleSuggest } from '../api/adapters/index.js';

const TIME_SLOT_OPTIONS = [
  '오전 (09:00-12:00)',
  '오후 (13:00-16:00)',
  '저녁 (18:00-21:00)',
  '주말 오전 (10:00-13:00)',
  '주말 오후 (14:00-17:00)',
];

const Operations = () => {
  const [formData, setFormData] = useState({ courseName: '', field: '', startDate: '' });
  const [riskData, setRiskData] = useState(null);
  const [scheduleData, setScheduleData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [validationError, setValidationError] = useState('');
  const [timeSlots, setTimeSlots] = useState({});

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
    if (validationError) setValidationError('');
  };

  const handleTimeSlotChange = (classIndex, value) => {
    setTimeSlots(prev => ({ ...prev, [classIndex]: value }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();

    if (!formData.courseName.trim()) {
      setValidationError('강좌명을 입력해주세요.');
      return;
    }
    if (!formData.field) {
      setValidationError('분야를 선택해주세요.');
      return;
    }
    if (!formData.startDate) {
      setValidationError('개강 예정일을 선택해주세요.');
      return;
    }

    setLoading(true);
    try {
      const [risk, schedule] = await Promise.all([
        getClosureRisk(formData),
        getScheduleSuggest(formData),
      ]);
      setRiskData(risk.data);
      setScheduleData(schedule.data);
      setTimeSlots({});
    } catch {
      setValidationError('분석 중 오류가 발생했습니다. 다시 시도해주세요.');
    }
    setLoading(false);
  };

  const hasResults = riskData && scheduleData;
  const isHighRisk = riskData?.risk_level === 'high';

  const riskTrendData = riskData?.risk_trend
    ? riskData.risk_trend.map((v, i) => ({ week: `${i + 1}주`, score: parseFloat((v * 100).toFixed(1)) }))
    : [];

  return (
    <div>
      <div className="page-header">
        <div>
          <h1 className="page-title">
            운영 관리
            <span className="badge">데모 버전</span>
          </h1>
          <p className="page-subtitle">폐강 위험도 평가와 강사/강의실 배정 계획을 관리합니다.</p>
        </div>
      </div>

      <div style={{ display: 'flex', gap: 'var(--space-6)', flexWrap: 'wrap', alignItems: 'flex-start' }}>
        {/* Form */}
        <div className="card" style={{ flex: '1 1 320px' }}>
          <h2 className="card-header">강좌 정보 입력</h2>
          <form onSubmit={handleSubmit}>
            <div className="form-group">
              <label htmlFor="courseName" className="form-label">강좌명</label>
              <input
                id="courseName"
                name="courseName"
                type="text"
                value={formData.courseName}
                onChange={handleChange}
                placeholder="예: 파이썬 기초 과정"
                className="form-control"
              />
            </div>

            <div className="form-group">
              <label htmlFor="field" className="form-label">분야</label>
              <select
                id="field"
                name="field"
                value={formData.field}
                onChange={handleChange}
                className="form-control"
              >
                <option value="">분야 선택</option>
                <option value="coding">코딩</option>
                <option value="security">보안</option>
                <option value="game">게임 개발</option>
                <option value="art">아트 &amp; 디자인</option>
              </select>
            </div>

            <div className="form-group">
              <label htmlFor="startDate" className="form-label">개강 예정일</label>
              <input
                id="startDate"
                name="startDate"
                type="date"
                value={formData.startDate}
                onChange={handleChange}
                className="form-control"
              />
            </div>

            {validationError && (
              <div style={{ color: 'var(--color-error-text)', fontSize: '0.875rem', marginTop: 'var(--space-2)', display: 'flex', alignItems: 'center', gap: 'var(--space-1)' }}>
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><circle cx="12" cy="12" r="10" /><line x1="12" y1="8" x2="12" y2="12" /><line x1="12" y1="16" x2="12.01" y2="16" /></svg>
                {validationError}
              </div>
            )}

            <div style={{ marginTop: 'var(--space-6)' }}>
              <button
                type="submit"
                disabled={loading}
                className="btn-primary"
                style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', gap: 'var(--space-2)' }}
              >
                {loading ? (
                  <>
                    <svg className="animate-spin" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><line x1="12" y1="2" x2="12" y2="6" /><line x1="12" y1="18" x2="12" y2="22" /><line x1="4.93" y1="4.93" x2="7.76" y2="7.76" /><line x1="16.24" y1="16.24" x2="19.07" y2="19.07" /><line x1="2" y1="12" x2="6" y2="12" /><line x1="18" y1="12" x2="22" y2="12" /><line x1="4.93" y1="19.07" x2="7.76" y2="16.24" /><line x1="16.24" y1="7.76" x2="19.07" y2="4.93" /></svg>
                    분석 중...
                  </>
                ) : (
                  <>
                    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><polygon points="5 3 19 12 5 21 5 3" /></svg>
                    분석 실행
                  </>
                )}
              </button>
            </div>
          </form>
        </div>

        {/* Results */}
        <div style={{ flex: '2 1 500px', display: 'flex', flexDirection: 'column', gap: 'var(--space-6)' }}>
          {!hasResults && !loading && (
            <div className="card" style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', minHeight: '300px', border: '1px dashed var(--color-border)', backgroundColor: 'var(--color-surface-hover)' }}>
              <StatusPanel
                variant="empty"
                title="분석 준비 완료"
                message="좌측에 강좌 정보를 입력하고 분석을 실행하세요."
              />
            </div>
          )}

          {loading && (
            <div className="card" style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', minHeight: '300px' }}>
              <StatusPanel variant="loading" title="운영 데이터 분석 중..." message="폐강 위험도와 배정 계획을 계산하고 있습니다." />
            </div>
          )}

          {hasResults && (
            <>
              {/* SECTION A: 폐강 위험도 평가 */}
              <div className="card">
                <h2 className="card-header">폐강 위험도 평가</h2>

                <div style={{ marginBottom: 'var(--space-5)' }}>
                  <RiskGauge score={riskData.risk_score} level={riskData.risk_level} />
                </div>

                {/* Enrollment comparison cards */}
                {riskData.predicted_enrollment != null && riskData.min_enrollment != null && (
                  <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(160px, 1fr))', gap: 'var(--space-4)', marginBottom: 'var(--space-5)' }}>
                    <div style={{ backgroundColor: 'var(--color-background)', padding: 'var(--space-4)', borderRadius: 'var(--radius-md)', textAlign: 'center' }}>
                      <div style={{ fontSize: '0.75rem', fontWeight: '600', color: 'var(--color-text-muted)', marginBottom: 'var(--space-1)' }}>예측 수강생</div>
                      <div style={{ fontSize: '1.75rem', fontWeight: '700', color: isHighRisk ? 'var(--color-error-text)' : 'var(--color-success-text)' }}>
                        {riskData.predicted_enrollment}
                        <span style={{ fontSize: '0.875rem', fontWeight: '500', color: 'var(--color-text-muted)' }}>명</span>
                      </div>
                    </div>
                    <div style={{ backgroundColor: 'var(--color-background)', padding: 'var(--space-4)', borderRadius: 'var(--radius-md)', textAlign: 'center' }}>
                      <div style={{ fontSize: '0.75rem', fontWeight: '600', color: 'var(--color-text-muted)', marginBottom: 'var(--space-1)' }}>최소 개강 인원</div>
                      <div style={{ fontSize: '1.75rem', fontWeight: '700', color: 'var(--color-text-main)' }}>
                        {riskData.min_enrollment}
                        <span style={{ fontSize: '0.875rem', fontWeight: '500', color: 'var(--color-text-muted)' }}>명</span>
                      </div>
                    </div>
                    <div style={{ backgroundColor: 'var(--color-background)', padding: 'var(--space-4)', borderRadius: 'var(--radius-md)', textAlign: 'center' }}>
                      <div style={{ fontSize: '0.75rem', fontWeight: '600', color: 'var(--color-text-muted)', marginBottom: 'var(--space-1)' }}>부족 인원</div>
                      <div style={{ fontSize: '1.75rem', fontWeight: '700', color: 'var(--color-error-text)' }}>
                        {Math.max(0, riskData.min_enrollment - riskData.predicted_enrollment)}
                        <span style={{ fontSize: '0.875rem', fontWeight: '500', color: 'var(--color-text-muted)' }}>명</span>
                      </div>
                    </div>
                  </div>
                )}

                {/* Mini risk trend chart */}
                {riskTrendData.length > 0 && (
                  <div style={{ marginBottom: 'var(--space-5)' }}>
                    <h3 style={{ fontSize: '0.875rem', fontWeight: '600', color: 'var(--color-text-muted)', marginBottom: 'var(--space-3)' }}>위험도 추이</h3>
                    <ResponsiveContainer width="100%" height={120}>
                      <LineChart data={riskTrendData}>
                        <CartesianGrid strokeDasharray="3 3" stroke="var(--color-border)" />
                        <XAxis dataKey="week" tick={{ fontSize: 11, fill: 'var(--color-text-muted)' }} />
                        <YAxis domain={[0, 100]} tick={{ fontSize: 11, fill: 'var(--color-text-muted)' }} unit="%" width={36} />
                        <Tooltip formatter={(v) => [`${v}%`, '위험도']} />
                        <Line type="monotone" dataKey="score" stroke="#ef4444" strokeWidth={2} dot={{ r: 3 }} activeDot={{ r: 5 }} />
                      </LineChart>
                    </ResponsiveContainer>
                  </div>
                )}

                {riskData.contributing_factors?.length > 0 && (
                  <div style={{ marginBottom: 'var(--space-5)' }}>
                    <h3 style={{ fontSize: '0.875rem', fontWeight: '600', color: 'var(--color-text-muted)', marginBottom: 'var(--space-3)' }}>주요 위험 요인</h3>
                    <ul style={{ margin: 0, paddingLeft: 'var(--space-5)', display: 'flex', flexDirection: 'column', gap: 'var(--space-2)' }}>
                      {riskData.contributing_factors.map((factor, i) => (
                        <li key={i} style={{ fontSize: '0.875rem', color: 'var(--color-text-main)' }}>{factor}</li>
                      ))}
                    </ul>
                  </div>
                )}

                {riskData.recommendation && (
                  <div style={{ backgroundColor: 'var(--color-info-bg)', padding: 'var(--space-4)', borderRadius: 'var(--radius-md)', marginBottom: isHighRisk ? 'var(--space-4)' : 0 }}>
                    <div style={{ fontSize: '0.875rem', color: 'var(--color-info-text)' }}>{riskData.recommendation}</div>
                  </div>
                )}

                {/* Marketing link button when high risk */}
                {isHighRisk && (
                  <div style={{ display: 'flex', gap: 'var(--space-3)', marginTop: 'var(--space-2)' }}>
                    <Link
                      to="/marketing"
                      style={{
                        display: 'inline-flex',
                        alignItems: 'center',
                        gap: 'var(--space-2)',
                        padding: 'var(--space-2) var(--space-4)',
                        backgroundColor: 'var(--color-error-bg)',
                        border: '1px solid #fca5a5',
                        borderRadius: 'var(--radius-md)',
                        color: 'var(--color-error-text)',
                        fontSize: '0.875rem',
                        fontWeight: '600',
                        textDecoration: 'none',
                      }}
                    >
                      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M22 12h-4l-3 9L9 3l-3 9H2" /></svg>
                      마케팅 강화 바로가기
                    </Link>
                  </div>
                )}
              </div>

              {/* SECTION B: 강사/강의실 배정 */}
              <div className="card">
                <h2 className="card-header">강사/강의실 배정</h2>

                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(160px, 1fr))', gap: 'var(--space-4)', marginBottom: 'var(--space-6)' }}>
                  <div style={{ backgroundColor: 'var(--color-background)', padding: 'var(--space-4)', borderRadius: 'var(--radius-md)', display: 'flex', alignItems: 'center', gap: 'var(--space-3)' }}>
                    <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="var(--color-primary)" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2" /><circle cx="12" cy="7" r="4" /></svg>
                    <div>
                      <div className="metric-label">필요 강사 수</div>
                      <div className="metric-value" style={{ color: 'var(--color-primary)' }}>{scheduleData.required_instructors}<span style={{ fontSize: '0.875rem', fontWeight: '500', color: 'var(--color-text-muted)' }}>명</span></div>
                    </div>
                  </div>
                  <div style={{ backgroundColor: 'var(--color-background)', padding: 'var(--space-4)', borderRadius: 'var(--radius-md)', display: 'flex', alignItems: 'center', gap: 'var(--space-3)' }}>
                    <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="var(--color-primary)" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><rect x="3" y="3" width="18" height="18" rx="2" /><path d="M3 9h18M9 21V9" /></svg>
                    <div>
                      <div className="metric-label">필요 강의실</div>
                      <div className="metric-value" style={{ color: 'var(--color-primary)' }}>{scheduleData.required_classrooms}<span style={{ fontSize: '0.875rem', fontWeight: '500', color: 'var(--color-text-muted)' }}>개</span></div>
                    </div>
                  </div>
                </div>

                {scheduleData.assignment_plan?.classes?.length > 0 && (
                  <div style={{ overflowX: 'auto' }}>
                    <table style={{ width: '100%', borderCollapse: 'collapse', border: '1px solid var(--color-border)' }}>
                      <thead>
                        <tr>
                          {['강좌명', '강사 슬롯', '시간대', '강의실'].map((h) => (
                            <th
                              key={h}
                              style={{
                                backgroundColor: 'var(--color-background)',
                                padding: 'var(--space-3)',
                                textAlign: 'left',
                                fontWeight: '600',
                                fontSize: '0.875rem',
                                color: 'var(--color-text-muted)',
                                borderBottom: '1px solid var(--color-border)',
                              }}
                            >
                              {h}
                            </th>
                          ))}
                        </tr>
                      </thead>
                      <tbody>
                        {scheduleData.assignment_plan.classes.map((cls, i) => (
                          <tr key={i}>
                            <td style={{ padding: 'var(--space-3)', borderBottom: '1px solid var(--color-border)', fontSize: '0.875rem', color: 'var(--color-text-main)' }}>{cls.class_name}</td>
                            <td style={{ padding: 'var(--space-3)', borderBottom: '1px solid var(--color-border)', fontSize: '0.875rem', color: 'var(--color-text-main)' }}>{cls.instructor_slot}</td>
                            <td style={{ padding: 'var(--space-3)', borderBottom: '1px solid var(--color-border)', fontSize: '0.875rem', color: 'var(--color-text-main)' }}>
                              <select
                                value={timeSlots[i] !== undefined ? timeSlots[i] : cls.time_slot}
                                onChange={(e) => handleTimeSlotChange(i, e.target.value)}
                                className="form-control"
                                style={{ padding: '4px 8px', fontSize: '0.875rem', minWidth: '180px' }}
                              >
                                {TIME_SLOT_OPTIONS.map((opt) => (
                                  <option key={opt} value={opt}>{opt}</option>
                                ))}
                              </select>
                            </td>
                            <td style={{ padding: 'var(--space-3)', borderBottom: '1px solid var(--color-border)', fontSize: '0.875rem', color: 'var(--color-text-main)' }}>{cls.classroom}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                )}

                {scheduleData.assignment_plan?.summary && (
                  <div style={{ marginTop: 'var(--space-4)', fontSize: '0.875rem', color: 'var(--color-text-muted)' }}>
                    {scheduleData.assignment_plan.summary}
                  </div>
                )}
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
};

export default Operations;
