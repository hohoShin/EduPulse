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
  const [resultError, setResultError] = useState('');
  const [timeSlots, setTimeSlots] = useState({});

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
    if (validationError) setValidationError('');
    if (resultError) setResultError('');
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
    setResultError('');
    try {
      const [risk, schedule] = await Promise.all([
        getClosureRisk(formData),
        getScheduleSuggest(formData),
      ]);

      const errorState = [risk, schedule].find((state) => state?.state === 'error');
      if (errorState) {
        setRiskData(null);
        setScheduleData(null);
        setTimeSlots({});
        setResultError(errorState.error || '분석 중 오류가 발생했습니다. 다시 시도해주세요.');
        return;
      }

      setRiskData(risk?.state === 'success' ? risk.data : null);
      setScheduleData(schedule?.state === 'success' ? schedule.data : null);
      setTimeSlots({});
    } catch {
      setRiskData(null);
      setScheduleData(null);
      setTimeSlots({});
      setResultError('분석 중 오류가 발생했습니다. 다시 시도해주세요.');
    } finally {
      setLoading(false);
    }
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
          {resultError && !loading && !hasResults && (
            <div className="card" style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', minHeight: '300px' }}>
              <StatusPanel
                variant="error"
                title="분석 실패"
                message={resultError}
              />
            </div>
          )}

          {!resultError && !hasResults && !loading && (
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
            <div className="card" style={{ padding: 0, overflow: 'hidden' }}>
              {/* Response Brief Header */}
              <div style={{ 
                padding: 'var(--space-6)', 
                borderBottom: '1px solid var(--color-border)', 
                backgroundColor: isHighRisk ? 'var(--color-error-bg)' : 'var(--color-surface)' 
              }}>
                <div style={{ marginBottom: 'var(--space-4)' }}>
                  <div style={{ display: 'inline-flex', alignItems: 'center', gap: 'var(--space-2)', padding: 'var(--space-1) var(--space-3)', backgroundColor: isHighRisk ? '#fca5a5' : 'var(--color-success-bg)', color: isHighRisk ? 'var(--color-error-text)' : 'var(--color-success-text)', borderRadius: 'var(--radius-full)', fontSize: '0.75rem', fontWeight: '700', letterSpacing: '0.05em', marginBottom: 'var(--space-3)' }}>
                    {isHighRisk ? 'ACTION REQUIRED' : 'ON TRACK'}
                  </div>
                  <h2 style={{ fontSize: '1.5rem', fontWeight: '800', color: 'var(--color-text-main)', margin: '0 0 var(--space-2) 0', letterSpacing: '-0.02em' }}>
                    {isHighRisk ? '폐강 위험 감지 — 즉각적인 조치가 필요합니다' : '정상 개강 가능 — 운영 배정을 확정하세요'}
                  </h2>
                  <div style={{ color: 'var(--color-text-muted)', fontSize: '0.875rem' }}>
                    대상 강좌: <strong>{formData.courseName}</strong> • 개강일: <strong>{formData.startDate}</strong>
                  </div>
                </div>
                
                <p style={{ fontSize: '1rem', color: 'var(--color-text-main)', lineHeight: 1.6, margin: 0, paddingBottom: 'var(--space-4)', borderBottom: '1px dashed var(--color-border)' }}>
                  {(() => {
                    const hasData = riskData.predicted_enrollment != null && riskData.min_enrollment != null;
                    if (isHighRisk) {
                      return hasData 
                        ? `현재 예측 수강생은 ${riskData.predicted_enrollment}명으로 최소 개강 인원(${riskData.min_enrollment}명)에 ${Math.max(0, riskData.min_enrollment - riskData.predicted_enrollment)}명 미달합니다. 마케팅 강화를 통해 부족 인원을 충원하거나 시뮬레이터를 통해 개강 일정을 재조정하는 것을 권장합니다.`
                        : `폐강 위험이 높은 것으로 분석되었습니다. 마케팅 강화를 통해 수강생을 충원하거나 시뮬레이터를 통해 개강 일정을 재조정하는 것을 권장합니다.`;
                    }
                    return hasData
                      ? `현재 예측 수강생은 ${riskData.predicted_enrollment}명으로 최소 개강 인원(${riskData.min_enrollment}명)을 충족했습니다. 아래 제안된 강사 및 강의실 배정 계획을 검토하고 확정해 주세요.`
                      : `정상 개강이 가능한 것으로 분석되었습니다. 아래 제안된 강사 및 강의실 배정 계획을 검토하고 확정해 주세요.`;
                  })()}
                </p>

                {isHighRisk && (
                  <div style={{ display: 'flex', gap: 'var(--space-3)', marginTop: 'var(--space-4)', flexWrap: 'wrap' }}>
                    <Link
                      to="/marketing"
                      style={{
                        display: 'inline-flex',
                        alignItems: 'center',
                        gap: 'var(--space-2)',
                        padding: 'var(--space-3) var(--space-5)',
                        backgroundColor: 'var(--color-primary)',
                        borderRadius: 'var(--radius-md)',
                        color: 'white',
                        fontSize: '0.875rem',
                        fontWeight: '600',
                        textDecoration: 'none',
                        boxShadow: 'var(--shadow-sm)',
                        transition: 'all var(--transition-fast)'
                      }}
                    >
                      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M22 12h-4l-3 9L9 3l-3 9H2" /></svg>
                      마케팅 분석 바로가기
                    </Link>
                    <Link
                      to="/simulator"
                      style={{
                        display: 'inline-flex',
                        alignItems: 'center',
                        gap: 'var(--space-2)',
                        padding: 'var(--space-3) var(--space-5)',
                        backgroundColor: 'var(--color-surface)',
                        border: '1px solid var(--color-border)',
                        borderRadius: 'var(--radius-md)',
                        color: 'var(--color-text-main)',
                        fontSize: '0.875rem',
                        fontWeight: '600',
                        textDecoration: 'none',
                        boxShadow: 'var(--shadow-sm)',
                        transition: 'all var(--transition-fast)'
                      }}
                    >
                      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><polygon points="5 3 19 12 5 21 5 3" /></svg>
                      시뮬레이터에서 재분석
                    </Link>
                  </div>
                )}
              </div>

              <div style={{ padding: 'var(--space-6)' }}>
                {/* SECTION A: 위험도 지표 상세 */}
                <div style={{ marginBottom: 'var(--space-8)' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-2)', marginBottom: 'var(--space-4)' }}>
                    <div style={{ width: '24px', height: '24px', borderRadius: '4px', backgroundColor: 'var(--color-background)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                      <span style={{ fontSize: '0.75rem', fontWeight: 'bold', color: 'var(--color-text-muted)' }}>1</span>
                    </div>
                    <h3 style={{ fontSize: '1.125rem', fontWeight: '700', color: 'var(--color-text-main)', margin: 0 }}>수요 부족 및 위험도 상세</h3>
                  </div>

                  <div style={{ display: 'grid', gridTemplateColumns: 'minmax(250px, 1fr) minmax(200px, 1fr)', gap: 'var(--space-6)' }}>
                    <div style={{ backgroundColor: 'var(--color-background)', padding: 'var(--space-5)', borderRadius: 'var(--radius-lg)' }}>
                      <RiskGauge score={riskData.risk_score} level={riskData.risk_level} />
                      {riskTrendData.length > 0 && (
                        <div style={{ marginTop: 'var(--space-4)', paddingTop: 'var(--space-4)', borderTop: '1px dashed var(--color-border)' }}>
                          <h4 style={{ fontSize: '0.75rem', fontWeight: '600', color: 'var(--color-text-muted)', marginBottom: 'var(--space-2)', textTransform: 'uppercase' }}>위험도 추이</h4>
                          <ResponsiveContainer width="100%" height={80}>
                            <LineChart data={riskTrendData}>
                              <XAxis dataKey="week" hide />
                              <YAxis domain={[0, 100]} hide />
                              <Tooltip formatter={(v) => [`${v}%`, '위험도']} cursor={{stroke: 'var(--color-border)'}} contentStyle={{fontSize: '12px'}} />
                              <Line type="monotone" dataKey="score" stroke={isHighRisk ? '#ef4444' : '#f59e0b'} strokeWidth={2} dot={{ r: 2 }} activeDot={{ r: 4 }} />
                            </LineChart>
                          </ResponsiveContainer>
                        </div>
                      )}
                    </div>

                    <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-3)' }}>
                      {riskData.contributing_factors?.length > 0 && (
                        <div style={{ backgroundColor: 'var(--color-surface)', border: '1px solid var(--color-border)', borderRadius: 'var(--radius-md)', padding: 'var(--space-4)', flex: 1 }}>
                          <h4 style={{ fontSize: '0.875rem', fontWeight: '600', color: 'var(--color-text-main)', margin: '0 0 var(--space-3) 0' }}>주요 위험 요인</h4>
                          <ul style={{ margin: 0, padding: 0, listStyle: 'none', display: 'flex', flexDirection: 'column', gap: 'var(--space-2)' }}>
                            {riskData.contributing_factors.map((factor, i) => (
                              <li key={i} style={{ fontSize: '0.875rem', color: 'var(--color-text-muted)', display: 'flex', alignItems: 'flex-start', gap: 'var(--space-2)' }}>
                                <svg style={{ marginTop: '2px', flexShrink: 0, color: 'var(--color-warning-text)' }} width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>
                                {factor}
                              </li>
                            ))}
                          </ul>
                        </div>
                      )}
                    </div>
                  </div>
                </div>

                {/* SECTION B: 강사/강의실 배정 */}
                <div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-2)', marginBottom: 'var(--space-4)' }}>
                    <div style={{ width: '24px', height: '24px', borderRadius: '4px', backgroundColor: 'var(--color-background)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                      <span style={{ fontSize: '0.75rem', fontWeight: 'bold', color: 'var(--color-text-muted)' }}>2</span>
                    </div>
                    <h3 style={{ fontSize: '1.125rem', fontWeight: '700', color: 'var(--color-text-main)', margin: 0 }}>운영 리소스 배정 (강사 및 강의실)</h3>
                  </div>
                  
                  <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: 'var(--space-4)', marginBottom: 'var(--space-5)' }}>
                    <div style={{ backgroundColor: 'var(--color-surface)', padding: 'var(--space-4)', borderRadius: 'var(--radius-md)', border: '1px solid var(--color-border)', display: 'flex', alignItems: 'center', gap: 'var(--space-3)' }}>
                      <div style={{ padding: 'var(--space-2)', backgroundColor: 'var(--color-info-bg)', borderRadius: 'var(--radius-md)', color: 'var(--color-primary)' }}>
                        <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2" /><circle cx="12" cy="7" r="4" /></svg>
                      </div>
                      <div>
                        <div style={{ fontSize: '0.75rem', fontWeight: '600', color: 'var(--color-text-muted)', textTransform: 'uppercase', marginBottom: '2px' }}>투입 강사 인력</div>
                        <div style={{ fontSize: '1.5rem', fontWeight: '700', color: 'var(--color-text-main)' }}>{scheduleData.required_instructors}<span style={{ fontSize: '0.875rem', fontWeight: '500', color: 'var(--color-text-muted)' }}>명 필요</span></div>
                      </div>
                    </div>
                    <div style={{ backgroundColor: 'var(--color-surface)', padding: 'var(--space-4)', borderRadius: 'var(--radius-md)', border: '1px solid var(--color-border)', display: 'flex', alignItems: 'center', gap: 'var(--space-3)' }}>
                      <div style={{ padding: 'var(--space-2)', backgroundColor: 'var(--color-info-bg)', borderRadius: 'var(--radius-md)', color: 'var(--color-primary)' }}>
                        <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><rect x="3" y="3" width="18" height="18" rx="2" /><path d="M3 9h18M9 21V9" /></svg>
                      </div>
                      <div>
                        <div style={{ fontSize: '0.75rem', fontWeight: '600', color: 'var(--color-text-muted)', textTransform: 'uppercase', marginBottom: '2px' }}>사용 강의실</div>
                        <div style={{ fontSize: '1.5rem', fontWeight: '700', color: 'var(--color-text-main)' }}>{scheduleData.required_classrooms}<span style={{ fontSize: '0.875rem', fontWeight: '500', color: 'var(--color-text-muted)' }}>개 배정</span></div>
                      </div>
                    </div>
                  </div>

                  {scheduleData.assignment_plan?.classes?.length > 0 && (
                    <div style={{ overflowX: 'auto', backgroundColor: 'var(--color-surface)', borderRadius: 'var(--radius-md)', border: '1px solid var(--color-border)' }}>
                      <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left' }}>
                        <thead style={{ backgroundColor: 'var(--color-background)' }}>
                          <tr>
                            {['강좌 그룹', '강사 배정', '강의 시간대', '강의실 위치'].map((h) => (
                              <th
                                key={h}
                                style={{
                                  padding: 'var(--space-3) var(--space-4)',
                                  fontWeight: '600',
                                  fontSize: '0.8125rem',
                                  color: 'var(--color-text-muted)',
                                  borderBottom: '1px solid var(--color-border)',
                                  whiteSpace: 'nowrap'
                                }}
                              >
                                {h}
                              </th>
                            ))}
                          </tr>
                        </thead>
                        <tbody>
                          {scheduleData.assignment_plan.classes.map((cls, i) => (
                            <tr key={i} style={{ transition: 'background-color var(--transition-fast)' }}>
                              <td style={{ padding: 'var(--space-3) var(--space-4)', borderBottom: '1px solid var(--color-border)', fontSize: '0.875rem', color: 'var(--color-text-main)', fontWeight: '500' }}>
                                {cls.class_name}
                              </td>
                              <td style={{ padding: 'var(--space-3) var(--space-4)', borderBottom: '1px solid var(--color-border)' }}>
                                <div style={{ display: 'inline-flex', alignItems: 'center', gap: '6px', padding: '4px 10px', backgroundColor: 'var(--color-background)', borderRadius: 'var(--radius-full)', fontSize: '0.8125rem', color: 'var(--color-text-main)' }}>
                                  <div style={{ width: '6px', height: '6px', borderRadius: '50%', backgroundColor: 'var(--color-primary)' }}></div>
                                  {cls.instructor_slot}
                                </div>
                              </td>
                              <td style={{ padding: 'var(--space-3) var(--space-4)', borderBottom: '1px solid var(--color-border)' }}>
                                <select
                                  value={timeSlots[i] !== undefined ? timeSlots[i] : cls.time_slot}
                                  onChange={(e) => handleTimeSlotChange(i, e.target.value)}
                                  className="form-control"
                                  style={{ padding: '6px 12px', fontSize: '0.875rem', minWidth: '180px', backgroundColor: 'var(--color-surface)', borderColor: 'var(--color-border)' }}
                                >
                                  {TIME_SLOT_OPTIONS.map((opt) => (
                                    <option key={opt} value={opt}>{opt}</option>
                                  ))}
                                </select>
                              </td>
                              <td style={{ padding: 'var(--space-3) var(--space-4)', borderBottom: '1px solid var(--color-border)', fontSize: '0.875rem', color: 'var(--color-text-main)' }}>
                                {cls.classroom}
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  )}

                  {scheduleData.assignment_plan?.summary && (
                    <div style={{ marginTop: 'var(--space-4)', padding: 'var(--space-3)', backgroundColor: 'var(--color-background)', borderRadius: 'var(--radius-md)', fontSize: '0.875rem', color: 'var(--color-text-muted)', display: 'flex', alignItems: 'center', gap: 'var(--space-2)' }}>
                      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><circle cx="12" cy="12" r="10"/><line x1="12" y1="16" x2="12" y2="12"/><line x1="12" y1="8" x2="12.01" y2="8"/></svg>
                      {scheduleData.assignment_plan.summary}
                    </div>
                  )}
                  <div style={{ marginTop: 'var(--space-3)', fontSize: '0.75rem', color: 'var(--color-text-light)', textAlign: 'right' }}>
                    * 운영 계획 확정은 데모 모드에서 저장되지 않습니다.
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default Operations;
