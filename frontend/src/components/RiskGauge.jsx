const levelConfig = {
  high: {
    textVar: 'var(--color-error-text)',
    bgVar: 'var(--color-error-bg)',
    barColor: 'var(--color-error-text)',
    label: '위험',
  },
  medium: {
    textVar: 'var(--color-warning-text)',
    bgVar: 'var(--color-warning-bg)',
    barColor: 'var(--color-warning-text)',
    label: '주의',
  },
  low: {
    textVar: 'var(--color-success-text)',
    bgVar: 'var(--color-success-bg)',
    barColor: 'var(--color-success-text)',
    label: '안전',
  },
};

const RiskGauge = ({ score, level, label, labels }) => {
  const config = levelConfig[level] || levelConfig.low;
  const effectiveLabels = labels || { high: '위험', medium: '주의', low: '안전' };
  const normalizedScore = Math.min(Math.max(score ?? 0, 0), 1);
  const percentage = Math.round(normalizedScore * 100);

  return (
    <div className="risk-gauge">
      {label && (
        <div className="risk-gauge__header">
          <div>
            <span className="risk-gauge__label">{label}</span>
            <p className="risk-gauge__description">점수가 높을수록 즉시 확인이 필요한 신호입니다.</p>
          </div>
          <div className="risk-gauge__meta">
            <span className="risk-gauge__percentage" style={{ color: config.textVar }}>
              {percentage}%
            </span>
            <span
              className="risk-gauge__pill"
              style={{ color: config.textVar, backgroundColor: config.bgVar }}
            >
              {effectiveLabels[level] ?? effectiveLabels.low}
            </span>
          </div>
        </div>
      )}
      <div className="risk-gauge__track">
        <div
          style={{
            width: `${percentage}%`,
            backgroundColor: config.barColor,
          }}
          className="risk-gauge__fill"
        />
      </div>
    </div>
  );
};

export default RiskGauge;
