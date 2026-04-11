import {
  ComposedChart,
  Line,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
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
    range: [d.lower, d.upper]
  }));

  return (
    <div className="chart-surface">
      <div className="chart-surface__summary">
        <div>
          <p className="chart-surface__eyebrow">예측 해석 가이드</p>
          <p className="chart-surface__description">
            실선은 예상 수요, 점선은 예측 범위를 뜻합니다. 상·하한 간격이 넓을수록 운영과 마케팅 대응 폭을 더 여유 있게 잡아야 합니다.
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
            <linearGradient id="colorValue" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="var(--color-primary)" stopOpacity={0.2}/>
              <stop offset="95%" stopColor="var(--color-primary)" stopOpacity={0}/>
            </linearGradient>
            <linearGradient id="colorRange" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor="var(--color-info-border)" stopOpacity={0.4}/>
              <stop offset="100%" stopColor="var(--color-info-border)" stopOpacity={0.12}/>
            </linearGradient>
          </defs>
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
            wrapperStyle={{ paddingTop: '20px', fontSize: '12px', color: 'var(--color-text-muted)' }}
            iconType="circle"
          />
          
          <Area 
            type="monotone" 
            dataKey="upper" 
            stroke="none" 
            fill="url(#colorRange)" 
            legendType="none"
            tooltipType="none"
          />
          <Area 
            type="monotone" 
            dataKey="lower" 
            stroke="none" 
            fill="var(--color-surface)" 
            legendType="none"
            tooltipType="none"
          />
          
          <Area 
            type="monotone" 
            dataKey="value" 
            name="예상 수요" 
            stroke="var(--color-primary)" 
            strokeWidth={3}
            fill="url(#colorValue)"
            activeDot={{ r: 6, strokeWidth: 0, fill: 'var(--color-primary)' }} 
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
