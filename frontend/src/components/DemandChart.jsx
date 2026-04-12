import {
  ComposedChart,
  Line,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ReferenceLine,
  ResponsiveContainer
} from 'recharts';

const DemandChart = ({ data = [] }) => {
  if (!data || data.length === 0) {
    return (
      <div className="chart-empty-state">
        차트 데이터가 없습니다.
      </div>
    );
  }

  // Transform data slightly to have a combined band for confidence interval
  const formattedData = data.map(d => ({
    ...d,
    range: (d.lower != null && d.upper != null) ? [d.lower, d.upper] : null,
  }));

  // Find the boundary date between actual and forecast
  const lastActual = formattedData.filter(d => d.category === 'actual').slice(-1)[0];
  const boundaryDate = lastActual?.date ?? null;

  return (
    <div className="chart-surface">
      <div className="chart-surface__summary">
        <div>
          <p className="chart-surface__eyebrow">예측 해석 가이드</p>
          <p className="chart-surface__description">
            실선은 주간 수요 추이(과거 실적 + 미래 예측)입니다.
            <br />
            점선 구간은 예측 신뢰 범위이며, 간격이 넓을수록 운영·마케팅 대응 폭을 여유 있게 잡아야 합니다.
          </p>
        </div>
      </div>
      <div className="chart-surface__canvas">
        <ResponsiveContainer width="100%" height="100%">
        <ComposedChart
          data={formattedData}
          margin={{
            top: 20,
            right: 20,
            left: 0,
            bottom: 0,
          }}
        >
          <defs>
            <linearGradient id="colorRange" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor="var(--color-info-border)" stopOpacity={0.4}/>
              <stop offset="100%" stopColor="var(--color-info-border)" stopOpacity={0.12}/>
            </linearGradient>
          </defs>
          {boundaryDate && (
            <ReferenceLine
              x={boundaryDate}
              stroke="var(--color-text-muted)"
              strokeDasharray="6 3"
              label={{ value: '예측 시작', position: 'top', fill: 'var(--color-text-muted)', fontSize: 11 }}
            />
          )}
          <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="var(--color-border)" />
          <XAxis 
            dataKey="date" 
            tickFormatter={(value) => {
              const date = new Date(value);
              return `${date.getMonth() + 1}/${date.getDate()}`;
            }}
            stroke="var(--color-text-light)"
            tick={{ fill: 'var(--color-text-muted)', fontSize: 12 }}
            axisLine={false}
            tickLine={false}
            dy={10}
          />
          <YAxis 
            stroke="var(--color-text-light)" 
            tick={{ fill: 'var(--color-text-muted)', fontSize: 12 }}
            axisLine={false}
            tickLine={false}
            dx={-10}
          />
          <Tooltip 
            contentStyle={{ 
              borderRadius: 'var(--radius-md)', 
              border: '1px solid var(--color-border)', 
              boxShadow: 'var(--shadow-lg)',
              backgroundColor: 'var(--color-surface)'
            }}
            labelFormatter={(value) => new Date(value).toLocaleDateString()}
            itemStyle={{ color: 'var(--color-text-main)', fontSize: '0.875rem' }}
          />
          <Legend 
            wrapperStyle={{ paddingTop: '10px', fontSize: '12px', color: 'var(--color-text-muted)' }}
            iconType="circle"
          />
          
          <Area 
            type="monotone" 
            dataKey="range" 
            stroke="none" 
            fill="url(#colorRange)" 
            legendType="none"
            tooltipType="none"
          />
          <Area 
            type="monotone" 
            dataKey="value" 
            name="예상 수요" 
            stroke="var(--color-primary)" 
            strokeWidth={3}
            fill="none"
            activeDot={{ r: 6, strokeWidth: 0, fill: 'var(--color-primary)' }} 
          />
          <Line 
            type="monotone" 
            dataKey="upper" 
            stroke="var(--color-surface)" 
            strokeWidth={4}
            dot={false}
            activeDot={false}
            legendType="none"
            tooltipType="none"
          />
          <Line 
            type="monotone" 
            dataKey="upper" 
            name="상한선" 
            stroke="var(--color-info-border)" 
            strokeWidth={2}
            strokeDasharray="4 4"
            dot={false}
            activeDot={false}
          />
          <Line 
            type="monotone" 
            dataKey="lower" 
            stroke="var(--color-surface)" 
            strokeWidth={4}
            dot={false}
            activeDot={false}
            legendType="none"
            tooltipType="none"
          />
          <Line 
            type="monotone" 
            dataKey="lower" 
            name="하한선" 
            stroke="var(--color-info-border)" 
            strokeWidth={2}
            strokeDasharray="4 4"
            dot={false}
            activeDot={false}
          />
        </ComposedChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
};

export default DemandChart;
