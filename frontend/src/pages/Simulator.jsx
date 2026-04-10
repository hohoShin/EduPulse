import React, { useState } from 'react';
import StatusPanel from '../components/StatusPanel.jsx';
import TierBadge from '../components/TierBadge.jsx';
import AlertPanel from '../components/AlertPanel.jsx';
import { simulateDemand } from '../api/adapters/index.js';

const Simulator = () => {
  const [formData, setFormData] = useState({
    courseName: '',
    field: '',
    startDate: '',
  });
  const [validationError, setValidationError] = useState('');
  const [uiState, setUiState] = useState({ state: 'empty', data: null, error: null, isDemo: true });

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
     } catch {
       setUiState({ 
         state: 'error', 
         data: null, 
         error: '시뮬레이션 중 예기치 않은 오류가 발생했습니다.', 
         isDemo: true 
       });
     }
  };

  const getFieldLabel = (field) => {
    switch(field?.toLowerCase()) {
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

            {validationError && (
              <div style={{ color: 'var(--color-error-text)', fontSize: '0.875rem', marginTop: 'var(--space-2)', display: 'flex', alignItems: 'center', gap: 'var(--space-1)' }}>
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="8" x2="12" y2="12"></line><line x1="12" y1="16" x2="12.01" y2="16"></line></svg>
                {validationError}
              </div>
            )}
            
            <div style={{ marginTop: 'var(--space-6)' }}>
              <button
                type="submit"
                disabled={uiState.state === 'loading'}
                className="btn-primary"
                style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', gap: 'var(--space-2)' }}
              >
                {uiState.state === 'loading' ? (
                  <>
                    <svg className="animate-spin" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><line x1="12" y1="2" x2="12" y2="6"></line><line x1="12" y1="18" x2="12" y2="22"></line><line x1="4.93" y1="4.93" x2="7.76" y2="7.76"></line><line x1="16.24" y1="16.24" x2="19.07" y2="19.07"></line><line x1="2" y1="12" x2="6" y2="12"></line><line x1="18" y1="12" x2="22" y2="12"></line><line x1="4.93" y1="19.07" x2="7.76" y2="16.24"></line><line x1="16.24" y1="7.76" x2="19.07" y2="4.93"></line></svg>
                    시뮬레이션 분석 중...
                  </>
                ) : (
                  <>
                    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><polygon points="5 3 19 12 5 21 5 3"></polygon></svg>
                    시뮬레이션 실행
                  </>
                )}
              </button>
            </div>
          </form>
        </div>

        <div style={{ flex: '2 1 500px' }}>
          {uiState.state === 'empty' && (
             <div className="card" style={{ height: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center', border: '1px dashed var(--color-border)', backgroundColor: 'var(--color-surface-hover)' }}>
               <StatusPanel 
                 variant="empty" 
                 title="시뮬레이션 준비 완료" 
                 message="좌측에 강좌 정보를 입력하고 시뮬레이션을 실행하여 예상 수요 및 운영 가이드를 확인하세요."
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
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 'var(--space-6)', borderBottom: '1px solid var(--color-border)', paddingBottom: 'var(--space-4)' }}>
                  <div>
                    <h2 style={{ fontSize: '1.5rem', fontWeight: '700', margin: '0 0 var(--space-2) 0', color: 'var(--color-text-main)' }}>
                      {uiState.data.courseName}
                    </h2>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-2)', color: 'var(--color-text-muted)', fontSize: '0.875rem' }}>
                      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><rect x="3" y="4" width="18" height="18" rx="2" ry="2"></rect><line x1="16" y1="2" x2="16" y2="6"></line><line x1="8" y1="2" x2="8" y2="6"></line><line x1="3" y1="10" x2="21" y2="10"></line></svg>
                      {new Date(formData.startDate).toLocaleDateString('ko-KR', { year: 'numeric', month: 'long', day: 'numeric' })} 개강 예정
                      <span style={{ color: 'var(--color-border)' }}>|</span>
                      분야: {getFieldLabel(uiState.data.field)}
                    </div>
                  </div>
                  <TierBadge tier={uiState.data.demandTier} />
                </div>
                
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: 'var(--space-6)' }}>
                  <div style={{ backgroundColor: 'var(--color-background)', padding: 'var(--space-4)', borderRadius: 'var(--radius-md)' }}>
                    <h3 className="metric-label">수요 예측</h3>
                    <div className="metric-value" style={{ color: 'var(--color-primary)' }}>
                      {uiState.data.predictedCount} <span style={{ fontSize: '1rem', fontWeight: '500', color: 'var(--color-text-muted)' }}>명</span>
                    </div>
                    <div style={{ fontSize: '0.875rem', color: 'var(--color-text-muted)', marginTop: 'var(--space-1)' }}>
                      신뢰 구간: {uiState.data.confidenceInterval.lower} ~ {uiState.data.confidenceInterval.upper}명
                    </div>
                  </div>

                  <div style={{ backgroundColor: 'var(--color-background)', padding: 'var(--space-4)', borderRadius: 'var(--radius-md)' }}>
                    <h3 className="metric-label">운영 가이드</h3>
                    <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-2)' }}>
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                        <span style={{ color: 'var(--color-text-muted)', fontSize: '0.875rem' }}>필요 강사 수</span>
                        <span style={{ fontWeight: '600', color: 'var(--color-text-main)' }}>{uiState.data.operations.instructors}명</span>
                      </div>
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                        <span style={{ color: 'var(--color-text-muted)', fontSize: '0.875rem' }}>권장 강의실</span>
                        <span style={{ fontWeight: '600', color: 'var(--color-text-main)' }}>{uiState.data.operations.classrooms}개</span>
                      </div>
                    </div>
                  </div>

                  <div style={{ backgroundColor: 'var(--color-background)', padding: 'var(--space-4)', borderRadius: 'var(--radius-md)' }}>
                    <h3 className="metric-label">마케팅 제안</h3>
                    <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-2)' }}>
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                        <span style={{ color: 'var(--color-text-muted)', fontSize: '0.875rem' }}>캠페인 시작</span>
                        <span style={{ fontWeight: '600', color: 'var(--color-text-main)' }}>{uiState.data.marketing.adWeeksBefore}주 전</span>
                      </div>
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                        <span style={{ color: 'var(--color-text-muted)', fontSize: '0.875rem' }}>얼리버드 혜택</span>
                        <span style={{ fontWeight: '600', color: 'var(--color-text-main)' }}>{uiState.data.marketing.earlybirdDays}일</span>
                      </div>
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                        <span style={{ color: 'var(--color-text-muted)', fontSize: '0.875rem' }}>권장 할인율</span>
                        <span style={{ fontWeight: '600', color: 'var(--color-success-text)' }}>{(uiState.data.marketing.discountRate * 100).toFixed(0)}%</span>
                      </div>
                    </div>
                  </div>
                </div>
                
                <div style={{ marginTop: 'var(--space-6)', paddingTop: 'var(--space-4)', borderTop: '1px solid var(--color-border)', fontSize: '0.75rem', color: 'var(--color-text-light)', display: 'flex', justifyContent: 'space-between' }}>
                  <span>AI 모델: {uiState.data.modelUsed}</span>
                  <span>분석 시간: {new Date(uiState.data.predictionDate).toLocaleString('ko-KR')}</span>
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
