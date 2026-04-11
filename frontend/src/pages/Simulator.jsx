import { useState } from 'react';
import { Link } from 'react-router-dom';
import StatusPanel from '../components/StatusPanel.jsx';
import TierBadge from '../components/TierBadge.jsx';
import AlertPanel from '../components/AlertPanel.jsx';
import { simulateDemand } from '../api/adapters/index.js';
import {
  scenarioBaseline,
  scenarioOptimistic,
  scenarioPessimistic,
} from '../fixtures/simulatorStates.js';

const SCENARIOS = [scenarioBaseline, scenarioOptimistic, scenarioPessimistic];

const ScenarioCard = ({ scenario, isActive }) => {
  const tierColor = {
    High: 'var(--color-success-text)',
    Mid: 'var(--color-warning-text)',
    Low: 'var(--color-error-text)',
  }[scenario.demandTier] || 'var(--color-text-main)';

  return (
    <div
      className="scenario-card"
      style={{
        borderTop: isActive ? `4px solid ${tierColor}` : '4px solid transparent',
        opacity: isActive ? 1 : 0.8,
      }}
    >
      <div className="scenario-header">
        <div>
          <h3 className="scenario-title">{scenario.label}</h3>
          <p className="scenario-desc">{scenario.description}</p>
        </div>
      </div>
      
      <div className="scenario-value-container">
        <span className="scenario-value" style={{ color: tierColor }}>
          {scenario.predictedCount}
        </span>
        <span className="scenario-unit">명 예상</span>
        <div style={{ marginLeft: 'auto' }}>
          <TierBadge tier={scenario.demandTier} />
        </div>
      </div>

      <div className="scenario-metrics">
        <div className="scenario-metric-row">
          <span className="scenario-metric-label">신뢰 구간</span>
          <span className="scenario-metric-val">{scenario.confidenceInterval.lower} ~ {scenario.confidenceInterval.upper}명</span>
        </div>
        <div className="scenario-metric-row">
          <span className="scenario-metric-label">광고 시작</span>
          <span className="scenario-metric-val">{scenario.marketing.adWeeksBefore}주 전</span>
        </div>
        <div className="scenario-metric-row">
          <span className="scenario-metric-label">권장 할인율</span>
          <span className="scenario-metric-val">{(scenario.marketing.discountRate * 100).toFixed(0)}%</span>
        </div>
        <div className="scenario-metric-row">
          <span className="scenario-metric-label">필요 강사</span>
          <span className="scenario-metric-val">{scenario.operations.instructors}명</span>
        </div>
      </div>
    </div>
  );
};

const Simulator = () => {
  const [formData, setFormData] = useState({
    courseName: '',
    field: '',
    startDate: '',
    tuitionFee: '',
  });
  const [validationError, setValidationError] = useState('');
  const [uiState, setUiState] = useState({ state: 'empty', data: null, error: null, isDemo: true });
  const [hasResult, setHasResult] = useState(false);

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData((prev) => ({ ...prev, [name]: value }));
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

    const todayStr = new Date().toISOString().split('T')[0];
    if (formData.startDate < todayStr) {
      setValidationError('개강 예정일은 미래의 날짜여야 합니다.');
      return;
    }

    setUiState({ state: 'loading', data: null, error: null, isDemo: true });

    try {
      const result = await simulateDemand(formData);
      setUiState(result);
      setHasResult(result.state === 'success');
    } catch {
      setUiState({
        state: 'error',
        data: null,
        error: '시뮬레이션 중 예기치 않은 오류가 발생했습니다.',
        isDemo: true
      });
    }
  };

  const handleReset = () => {
    setFormData({ courseName: '', field: '', startDate: '', tuitionFee: '' });
    setUiState({ state: 'empty', data: null, error: null, isDemo: true });
    setHasResult(false);
    setValidationError('');
  };

  const getFieldLabel = (field) => {
    switch (field?.toLowerCase()) {
      case 'coding': return '코딩';
      case 'security': return '보안';
      case 'game': return '게임 개발';
      case 'art': return '아트 & 디자인';
      default: return field;
    }
  };

  const getLowTierAlerts = (resultData) => {
    if (!resultData || resultData.demandTier?.toLowerCase() !== 'low') {
      return [];
    }
    return [
      {
        id: 'low-tier-risk',
        title: '낮은 수요 위험 감지',
        message: '이 강좌의 예상 등록 인원이 적습니다. 폐강을 피하려면 커리큘럼을 수정하거나 마케팅 기간을 늘리거나 타겟층을 변경하는 것을 고려해보세요.',
        severity: 'critical',
      }
    ];
  };

  return (
    <div>
      <div className="page-header">
        <div>
          <h1 className="page-title">
            시뮬레이터
            <span className="badge">데모 버전</span>
          </h1>
          <p className="page-subtitle">신규 강좌 개설 시 예상되는 수요와 운영 지표를 시뮬레이션합니다.</p>
        </div>
      </div>

      {/* 시나리오 비교 카드 */}
      <div className="card" style={{ marginBottom: 'var(--space-6)', backgroundColor: 'var(--color-surface)' }}>
        <div style={{ marginBottom: 'var(--space-4)' }}>
          <h2 className="card-header" style={{ marginBottom: 'var(--space-1)' }}>
            시나리오 비교 및 수요 브리프 기준선
            <span style={{ fontSize: '0.75rem', fontWeight: '600', color: 'var(--color-primary)', backgroundColor: 'var(--color-info-bg)', padding: '4px 8px', borderRadius: '4px' }}>Reference Data</span>
          </h2>
          <p style={{ fontSize: '0.875rem', color: 'var(--color-text-muted)' }}>
            과거 동일 분야의 개강 데이터를 기반으로 산출된 3가지 기준 시나리오를 먼저 비교하고, 좌측 패널에 실제 강좌 정보를 입력하면 맞춤 예측 브리프를 생성합니다.
          </p>
        </div>
        <div style={{ display: 'flex', gap: 'var(--space-4)', flexWrap: 'wrap' }}>
          {SCENARIOS.map(s => (
            <ScenarioCard
              key={s.scenario}
              scenario={s}
              isActive={s.scenario === 'baseline'}
            />
          ))}
        </div>
      </div>

      <div style={{ display: 'flex', gap: 'var(--space-6)', flexWrap: 'wrap', alignItems: 'flex-start' }}>
        <div className="card" style={{ flex: '1 1 350px' }}>
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
                placeholder="예: 고급 게임 엔진 디자인"
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
                <option value="art">아트 & 디자인</option>
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

            <div className="form-group">
              <label htmlFor="tuitionFee" className="form-label">수강료 (원, 선택)</label>
              <input
                id="tuitionFee"
                name="tuitionFee"
                type="number"
                min="0"
                step="10000"
                value={formData.tuitionFee}
                onChange={handleChange}
                placeholder="예: 500000"
                className="form-control"
              />
            </div>

            {validationError && (
              <div style={{ color: 'var(--color-error-text)', fontSize: '0.875rem', marginTop: 'var(--space-2)', display: 'flex', alignItems: 'center', gap: 'var(--space-1)' }}>
                <svg aria-hidden="true" focusable="false" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="8" x2="12" y2="12"></line><line x1="12" y1="16" x2="12.01" y2="16"></line></svg>
                {validationError}
              </div>
            )}

            <div style={{ marginTop: 'var(--space-6)', display: 'flex', gap: 'var(--space-3)' }}>
              <button
                type="submit"
                disabled={uiState.state === 'loading'}
                className="btn-primary"
                style={{ flex: 1, display: 'flex', justifyContent: 'center', alignItems: 'center', gap: 'var(--space-2)' }}
              >
                {uiState.state === 'loading' ? (
                  <>
                     <svg aria-hidden="true" focusable="false" className="animate-spin" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><line x1="12" y1="2" x2="12" y2="6"></line><line x1="12" y1="18" x2="12" y2="22"></line><line x1="4.93" y1="4.93" x2="7.76" y2="7.76"></line><line x1="16.24" y1="16.24" x2="19.07" y2="19.07"></line><line x1="2" y1="12" x2="6" y2="12"></line><line x1="18" y1="12" x2="22" y2="12"></line><line x1="4.93" y1="19.07" x2="7.76" y2="16.24"></line><line x1="16.24" y1="7.76" x2="19.07" y2="4.93"></line></svg>
                    시뮬레이션 분석 중...
                  </>
                ) : hasResult ? (
                  <>
                     <svg aria-hidden="true" focusable="false" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><polyline points="23 4 23 10 17 10"></polyline><polyline points="1 20 1 14 7 14"></polyline><path d="M3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15"></path></svg>
                    다시 실행
                  </>
                ) : (
                  <>
                     <svg aria-hidden="true" focusable="false" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><polygon points="5 3 19 12 5 21 5 3"></polygon></svg>
                    시뮬레이션 실행
                  </>
                )}
              </button>

              {hasResult && (
                <button
                  type="button"
                  className="btn"
                  onClick={handleReset}
                  style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-1)' }}
                >
                   <svg aria-hidden="true" focusable="false" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><line x1="18" y1="6" x2="6" y2="18"></line><line x1="6" y1="6" x2="18" y2="18"></line></svg>
                  조건 변경
                </button>
              )}
            </div>
          </form>
        </div>

        <div style={{ flex: '2 1 500px' }}>
          {uiState.state === 'empty' && (
            <div className="card" style={{ height: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center', border: '1px dashed var(--color-border)', backgroundColor: 'var(--color-surface-hover)' }}>
              <StatusPanel
                variant="empty"
                title="시뮬레이션 준비 완료"
                message="좌측에 강좌 정보를 입력하면 예상 수요, 필요한 운영 리소스, 권장 마케팅 액션을 한 번에 확인할 수 있습니다."
              />
            </div>
          )}

          {uiState.state === 'loading' && (
            <div className="card" style={{ height: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
              <StatusPanel variant="loading" title="수요 시뮬레이션 분석 중..." message="과거 데이터와 트렌드를 바탕으로 수요를 예측하고 있습니다." />
            </div>
          )}

          {uiState.state === 'error' && (
            <div className="card" style={{ height: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
              <StatusPanel variant="error" title="시뮬레이션 실패" message={uiState.error || '현재 시뮬레이션을 완료할 수 없습니다.'} />
            </div>
          )}

          {uiState.state === 'success' && uiState.data && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-6)' }}>
              {uiState.data.demandTier?.toLowerCase() === 'low' && (
                <AlertPanel alerts={getLowTierAlerts(uiState.data)} />
              )}

              <div className="card">
                <div className="brief-header">
                  <div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-2)', marginBottom: 'var(--space-2)' }}>
                      <span style={{ fontSize: '0.75rem', fontWeight: '700', color: 'var(--color-primary)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>시뮬레이션 브리프</span>
                      <span style={{ color: 'var(--color-border)' }}>|</span>
                      <span style={{ fontSize: '0.75rem', color: 'var(--color-text-muted)' }}>{new Date(uiState.data.predictionDate).toLocaleString('ko-KR')}</span>
                    </div>
                    <h2 className="brief-title">{uiState.data.courseName}</h2>
                    
                    <div className="brief-meta">
                      <div className="brief-meta-item">
                         <svg aria-hidden="true" focusable="false" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><rect x="3" y="4" width="18" height="18" rx="2" ry="2"></rect><line x1="16" y1="2" x2="16" y2="6"></line><line x1="8" y1="2" x2="8" y2="6"></line><line x1="3" y1="10" x2="21" y2="10"></line></svg>
                        {new Date(formData.startDate).toLocaleDateString('ko-KR', { year: 'numeric', month: 'long', day: 'numeric' })} 개강
                      </div>
                      <span className="brief-meta-divider">•</span>
                      <div className="brief-meta-item">
                        분야: {getFieldLabel(uiState.data.field)}
                      </div>
                      {formData.tuitionFee && (
                        <>
                          <span className="brief-meta-divider">•</span>
                          <div className="brief-meta-item">
                            수강료: {Number(formData.tuitionFee).toLocaleString('ko-KR')}원
                          </div>
                        </>
                      )}
                    </div>
                  </div>
                  <TierBadge tier={uiState.data.demandTier} />
                </div>

                <div className="brief-section">
                  <div className="brief-section-header">
                     <svg aria-hidden="true" focusable="false" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="var(--color-primary)" strokeWidth="2"><path d="M3 3v18h18"/><path d="M18 17V9"/><path d="M13 17V5"/><path d="M8 17v-3"/></svg>
                    <h3 className="brief-section-title">핵심 예측 지표</h3>
                  </div>
                  
                  <div className="brief-metric-grid">
                    <div className="brief-metric-card">
                      <div className="brief-metric-label">예상 수요 인원</div>
                      <div className="brief-metric-value brief-metric-value--primary">
                        {uiState.data.predictedCount} <span style={{ fontSize: '1rem', fontWeight: '500', color: 'var(--color-text-muted)' }}>명</span>
                      </div>
                      <div className="brief-metric-subtext">
                        신뢰 구간: {uiState.data.confidenceInterval.lower} ~ {uiState.data.confidenceInterval.upper}명
                      </div>
                    </div>

                    <div className="brief-metric-card">
                      <div className="brief-metric-label">AI 모델 신뢰도</div>
                      <div className="brief-metric-value">
                        High
                      </div>
                      <div className="brief-metric-subtext">
                        {uiState.data.modelUsed} 모델 적용
                      </div>
                    </div>
                  </div>
                </div>

                <div className="brief-section" style={{ marginTop: 'var(--space-4)' }}>
                  <div className="brief-section-header">
                     <svg aria-hidden="true" focusable="false" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="var(--color-success-text)" strokeWidth="2"><circle cx="12" cy="12" r="10"/><line x1="12" y1="16" x2="12" y2="12"/><line x1="12" y1="8" x2="12.01" y2="8"/></svg>
                    <h3 className="brief-section-title">운영 및 마케팅 가이드</h3>
                  </div>
                  
                  <div className="brief-metric-grid">
                    <div className="brief-metric-card" style={{ borderLeft: '3px solid var(--color-success-text)' }}>
                      <div className="brief-metric-label">권장 운영 리소스</div>
                      <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-2)' }}>
                        <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                          <span style={{ fontSize: '0.875rem', color: 'var(--color-text-muted)' }}>필요 강사</span>
                          <span style={{ fontSize: '0.875rem', fontWeight: '600', color: 'var(--color-text-main)' }}>{uiState.data.operations.instructors}명 배정 요망</span>
                        </div>
                        <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                          <span style={{ fontSize: '0.875rem', color: 'var(--color-text-muted)' }}>강의실</span>
                          <span style={{ fontSize: '0.875rem', fontWeight: '600', color: 'var(--color-text-main)' }}>{uiState.data.operations.classrooms}개 공간 확보</span>
                        </div>
                      </div>
                    </div>

                    <div className="brief-metric-card" style={{ borderLeft: '3px solid var(--color-primary)' }}>
                      <div className="brief-metric-label">최적 마케팅 액션</div>
                      <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-2)' }}>
                        <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                          <span style={{ fontSize: '0.875rem', color: 'var(--color-text-muted)' }}>캠페인 시작</span>
                          <span style={{ fontSize: '0.875rem', fontWeight: '600', color: 'var(--color-text-main)' }}>개강 {uiState.data.marketing.adWeeksBefore}주 전</span>
                        </div>
                        <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                          <span style={{ fontSize: '0.875rem', color: 'var(--color-text-muted)' }}>권장 할인율</span>
                          <span style={{ fontSize: '0.875rem', fontWeight: '600', color: 'var(--color-primary)' }}>{(uiState.data.marketing.discountRate * 100).toFixed(0)}% ({uiState.data.marketing.earlybirdDays}일간)</span>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>

                <div className="brief-actions">
                  <Link to="/operations" className="brief-action-link">
                     <svg aria-hidden="true" focusable="false" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><rect x="3" y="3" width="18" height="18" rx="2" ry="2"/><line x1="3" y1="9" x2="21" y2="9"/><line x1="9" y1="21" x2="9" y2="9"/></svg>
                    운영 계획 수립
                  </Link>
                  <Link to="/marketing" className="brief-action-link brief-action-link--primary">
                     <svg aria-hidden="true" focusable="false" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M21 11.5a8.38 8.38 0 0 1-.9 3.8 8.5 8.5 0 0 1-7.6 4.7 8.38 8.38 0 0 1-3.8-.9L3 21l1.9-5.7a8.38 8.38 0 0 1-.9-3.8 8.5 8.5 0 0 1 4.7-7.6 8.38 8.38 0 0 1 3.8-.9h.5a8.48 8.48 0 0 1 8 8v.5z"/></svg>
                    마케팅 캠페인 기획
                  </Link>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default Simulator;
