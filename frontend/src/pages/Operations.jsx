import React, { useState } from 'react';
import StatusPanel from '../components/StatusPanel.jsx';
import RiskGauge from '../components/RiskGauge.jsx';
import { getClosureRisk, getScheduleSuggest } from '../api/adapters/index.js';

const Operations = () => {
  const [formData, setFormData] = useState({ courseName: '', field: '', startDate: '' });
  const [riskData, setRiskData] = useState(null);
  const [scheduleData, setScheduleData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [validationError, setValidationError] = useState('');

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
    if (validationError) setValidationError('');
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
    } catch {
      setValidationError('분석 중 오류가 발생했습니다. 다시 시도해주세요.');
    }
    setLoading(false);
  };

  const hasResults = riskData && scheduleData;

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
                  <div style={{ backgroundColor: 'var(--color-info-bg)', padding: 'var(--space-4)', borderRadius: 'var(--radius-md)' }}>
                    <div style={{ fontSize: '0.875rem', color: 'var(--color-info-text)' }}>{riskData.recommendation}</div>
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
                            {[cls.class_name, cls.instructor_slot, cls.time_slot, cls.classroom].map((cell, j) => (
                              <td
                                key={j}
                                style={{
                                  padding: 'var(--space-3)',
                                  borderBottom: '1px solid var(--color-border)',
                                  fontSize: '0.875rem',
                                  color: 'var(--color-text-main)',
                                }}
                              >
                                {cell}
                              </td>
                            ))}
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                )}

                {scheduleData.summary && (
                  <div style={{ marginTop: 'var(--space-4)', fontSize: '0.875rem', color: 'var(--color-text-muted)' }}>
                    {scheduleData.summary}
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
