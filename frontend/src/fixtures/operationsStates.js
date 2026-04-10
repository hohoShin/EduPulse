import { createUIState } from '../api/viewModels.js';

export const closureRiskData = {
  risk_score: 0.72,
  risk_level: "high",
  contributing_factors: [
    "예측 수강생 수 부족: 3명 (LOW 등급)",
    "신뢰 구간 하한(1.5명)이 최소 개강 인원(5명) 미만"
  ],
  recommendation: "마케팅 강화 및 조기 등록 할인 적용을 권장합니다. 개강 4주 전까지 최소 인원 미달 시 폐강을 검토하세요."
};

export const scheduleSuggestData = {
  course_name: "Python 웹개발",
  required_instructors: 2,
  required_classrooms: 1,
  assignment_plan: {
    classes: [
      { class_name: "A반", instructor_slot: "강사 1", time_slot: "오전 (09:00-12:00)", classroom: "강의실 1" },
      { class_name: "B반", instructor_slot: "강사 2", time_slot: "오후 (13:00-16:00)", classroom: "강의실 1" }
    ],
    summary: "30명 기준: 2개 반 편성 (반당 15명), 강사 2명, 강의실 1개 (오전/오후 분할)"
  }
};

export const closureRiskSuccess = createUIState({ state: 'success', isDemo: true, data: closureRiskData });
export const scheduleSuggestSuccess = createUIState({ state: 'success', isDemo: true, data: scheduleSuggestData });
