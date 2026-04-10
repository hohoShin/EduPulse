export const createUIState = ({ state = 'loading', data = null, error = null, isDemo = false } = {}) => ({
  state,
  data,
  error,
  isDemo,
});

export const createSummaryCard = (id, label, value, unit, trend, trendLabel, trendDirection, icon) => ({
  id,
  label,
  value,
  unit,
  trend,
  trendLabel,
  trendDirection,
  icon,
});

export const createChartPoint = (date, value, upper = null, lower = null, category = null) => ({
  date,
  value,
  upper,
  lower,
  category,
});

export const createAlertItem = (id, title, message, severity, timestamp, actionLabel = null, actionUrl = null) => ({
  id,
  title,
  message,
  severity,
  timestamp,
  actionLabel,
  actionUrl,
});

export const createSimulatorResult = (options) => ({
  courseName: options.courseName,
  field: options.field,
  predictedCount: options.predictedCount,
  demandTier: options.demandTier,
  confidenceInterval: options.confidenceInterval || { lower: 0, upper: 0 },
  modelUsed: options.modelUsed,
  predictionDate: options.predictionDate,
  marketing: options.marketing || { adWeeksBefore: 0, earlybirdDays: 0, discountRate: 0 },
  operations: options.operations || { instructors: 0, classrooms: 0 },
});

export const createStatusItem = (serviceName, status, lastSync, metrics = {}) => ({
  serviceName,
  status,
  lastSync,
  metrics,
});
