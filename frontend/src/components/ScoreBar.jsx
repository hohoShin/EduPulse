const ScoreBar = ({ score, label, recommended }) => {
  const normalizedScore = Math.min(Math.max(score ?? 0, 0), 1);
  const percentage = Math.round(normalizedScore * 100);

  return (
    <div className="score-bar">
      <div className="score-bar__header">
        <div>
          <span className="score-bar__label">{label || '추천 적합도'}</span>
          <p className="score-bar__description">수요, 경쟁 강도, 검색 흐름을 함께 반영한 우선 검토 점수입니다.</p>
        </div>
        <div className="score-bar__meta">
          <span className="score-bar__percentage">
            {percentage}%
          </span>
          {recommended && (
            <span className="score-bar__badge">우선 추천</span>
          )}
        </div>
      </div>
      <div className="score-bar__track">
        <div
          className="score-bar__fill"
          style={{ width: `${percentage}%` }}
        />
      </div>
    </div>
  );
};

export default ScoreBar;
