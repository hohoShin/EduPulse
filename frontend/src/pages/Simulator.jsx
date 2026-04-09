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
      <h1 style={{ fontSize: '1.875rem', fontWeight: 'bold', marginBottom: '1.5rem', color: '#0f172a', display: 'flex', alignItems: 'center' }}>
        시뮬레이터
        <span style={{ marginLeft: '1rem', fontSize: '0.875rem', backgroundColor: '#fef3c7', color: '#92400e', padding: '0.25rem 0.75rem', borderRadius: '9999px', fontWeight: 'bold' }}>데모 버전</span>
      </h1>
      
      <div style={{ display: 'flex', gap: '2rem', flexWrap: 'wrap' }}>
        <div style={{ flex: '1 1 300px', backgroundColor: '#ffffff', padding: '1.5rem', borderRadius: '0.5rem', border: '1px solid #e2e8f0' }}>
          <h2 style={{ fontSize: '1.25rem', fontWeight: '600', marginBottom: '1rem', color: '#1e293b' }}>강좌 정보</h2>
          
          <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
            <div>
              <label htmlFor="courseName" style={{ display: 'block', marginBottom: '0.5rem', fontWeight: '500', color: '#475569' }}>강좌명</label>
              <input
                id="courseName"
                name="courseName"
                type="text"
                value={formData.courseName}
                onChange={handleChange}
                placeholder="예: 고급 게임 엔진 디자인"
                style={{ width: '100%', padding: '0.5rem', borderRadius: '0.375rem', border: '1px solid #cbd5e1' }}
              />
            </div>
            
            <div>
              <label htmlFor="field" style={{ display: 'block', marginBottom: '0.5rem', fontWeight: '500', color: '#475569' }}>분야</label>
              <select
                id="field"
                name="field"
                value={formData.field}
                onChange={handleChange}
                style={{ width: '100%', padding: '0.5rem', borderRadius: '0.375rem', border: '1px solid #cbd5e1' }}
              >
                <option value="">분야 선택</option>
                <option value="coding">코딩</option>
                <option value="security">보안</option>
                <option value="game">게임 개발</option>
                <option value="art">아트 & 디자인</option>
              </select>
            </div>
            
            <div>
              <label htmlFor="startDate" style={{ display: 'block', marginBottom: '0.5rem', fontWeight: '500', color: '#475569' }}>개강 예정일</label>
              <input
                id="startDate"
                name="startDate"
                type="date"
                value={formData.startDate}
                onChange={handleChange}
                style={{ width: '100%', padding: '0.5rem', borderRadius: '0.375rem', border: '1px solid #cbd5e1' }}
              />
            </div>

            {validationError && (
              <div style={{ color: '#ef4444', fontSize: '0.875rem', marginTop: '0.5rem' }}>
                {validationError}
              </div>
            )}
            
            <button
              type="submit"
              disabled={uiState.state === 'loading'}
              style={{
                marginTop: '1rem',
                padding: '0.75rem',
                backgroundColor: '#2563eb',
                color: '#ffffff',
                border: 'none',
                borderRadius: '0.375rem',
                fontWeight: 'bold',
                cursor: uiState.state === 'loading' ? 'not-allowed' : 'pointer',
                opacity: uiState.state === 'loading' ? 0.7 : 1
              }}
            >
              {uiState.state === 'loading' ? '시뮬레이션 중...' : '시뮬레이션 실행'}
            </button>
          </form>
        </div>

        <div style={{ flex: '2 1 500px' }}>
          {uiState.state === 'empty' && (
             <div style={{ backgroundColor: '#ffffff', padding: '1.5rem', borderRadius: '0.5rem', border: '1px solid #e2e8f0', height: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
               <StatusPanel 
                 variant="empty" 
                 title="시뮬레이션 준비 완료" 
                 message="좌측에 강좌 정보를 입력하고 시뮬레이션을 실행하여 예상 수요 및 운영 가이드를 확인하세요."
               />
             </div>
          )}

          {uiState.state === 'loading' && (
            <div style={{ backgroundColor: '#ffffff', padding: '1.5rem', borderRadius: '0.5rem', border: '1px solid #e2e8f0', height: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
              <StatusPanel variant="loading" title="수요 시뮬레이션 중 (데모)..." message="시연 목적의 가상 예측 결과를 생성 중입니다." />
            </div>
          )}

          {uiState.state === 'error' && (
            <div style={{ backgroundColor: '#ffffff', padding: '1.5rem', borderRadius: '0.5rem', border: '1px solid #e2e8f0', height: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
              <StatusPanel variant="error" title="시뮬레이션 실패" message={uiState.error || '현재 시뮬레이션을 완료할 수 없습니다.'} />
            </div>
          )}

          {uiState.state === 'success' && uiState.data && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
              {uiState.data.demandTier?.toLowerCase() === 'low' && (
                <AlertPanel alerts={getLowTierAlerts(uiState.data)} />
              )}
              
              <div style={{ backgroundColor: '#ffffff', padding: '1.5rem', borderRadius: '0.5rem', border: '1px solid #e2e8f0' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '1.5rem', borderBottom: '1px solid #f1f5f9', paddingBottom: '1rem' }}>
                  <div>
                    <h2 style={{ fontSize: '1.5rem', fontWeight: 'bold', margin: '0 0 0.5rem 0', color: '#1e293b' }}>
                      {uiState.data.courseName}
                    </h2>
                    <p style={{ margin: 0, color: '#64748b', textTransform: 'capitalize' }}>분야: {getFieldLabel(uiState.data.field)}</p>
                  </div>
                  <TierBadge tier={uiState.data.demandTier} />
                </div>
                
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '1.5rem' }}>
                  <div>
                    <h3 style={{ fontSize: '0.875rem', fontWeight: '600', color: '#64748b', textTransform: 'uppercase', marginBottom: '0.5rem' }}>수요 예측</h3>
                    <div style={{ fontSize: '2.25rem', fontWeight: 'bold', color: '#0f172a', marginBottom: '0.25rem' }}>
                      {uiState.data.predictedCount} <span style={{ fontSize: '1rem', fontWeight: 'normal', color: '#64748b' }}>명</span>
                    </div>
                    <div style={{ fontSize: '0.875rem', color: '#475569' }}>
                      범위: {uiState.data.confidenceInterval.lower} - {uiState.data.confidenceInterval.upper}
                    </div>
                  </div>

                  <div>
                    <h3 style={{ fontSize: '0.875rem', fontWeight: '600', color: '#64748b', textTransform: 'uppercase', marginBottom: '0.5rem' }}>인력 & 운영</h3>
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem', marginTop: '0.5rem' }}>
                      <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                        <span style={{ color: '#475569' }}>필요 강사 수:</span>
                        <span style={{ fontWeight: '600', color: '#1e293b' }}>{uiState.data.operations.instructors}</span>
                      </div>
                      <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                        <span style={{ color: '#475569' }}>필요 강의실 수:</span>
                        <span style={{ fontWeight: '600', color: '#1e293b' }}>{uiState.data.operations.classrooms}</span>
                      </div>
                    </div>
                  </div>

                  <div>
                    <h3 style={{ fontSize: '0.875rem', fontWeight: '600', color: '#64748b', textTransform: 'uppercase', marginBottom: '0.5rem' }}>마케팅 가이드</h3>
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem', marginTop: '0.5rem' }}>
                      <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                        <span style={{ color: '#475569' }}>광고 시작:</span>
                        <span style={{ fontWeight: '600', color: '#1e293b' }}>{uiState.data.marketing.adWeeksBefore}주 전</span>
                      </div>
                      <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                        <span style={{ color: '#475569' }}>얼리버드 기간:</span>
                        <span style={{ fontWeight: '600', color: '#1e293b' }}>{uiState.data.marketing.earlybirdDays}일</span>
                      </div>
                      <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                        <span style={{ color: '#475569' }}>권장 할인율:</span>
                        <span style={{ fontWeight: '600', color: '#1e293b' }}>{(uiState.data.marketing.discountRate * 100).toFixed(0)}%</span>
                      </div>
                    </div>
                  </div>
                </div>
                
                <div style={{ marginTop: '2rem', fontSize: '0.75rem', color: '#94a3b8', textAlign: 'right' }}>
                  모델: {uiState.data.modelUsed} (가상 데이터) | 생성일: {new Date(uiState.data.predictionDate).toLocaleString()}
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
