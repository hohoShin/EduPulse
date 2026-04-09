import React from 'react';
import {
  LineChart,
  Line,
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
      <div style={{ height: '300px', display: 'flex', alignItems: 'center', justifyContent: 'center', backgroundColor: '#f8fafc', borderRadius: '0.5rem', border: '1px dashed #cbd5e1', color: '#64748b' }}>
        차트 데이터가 없습니다.
      </div>
    );
  }

  return (
    <div style={{ width: '100%', height: '300px' }}>
      <ResponsiveContainer width="100%" height="100%">
        <LineChart
          data={data}
          margin={{
            top: 5,
            right: 30,
            left: 20,
            bottom: 5,
          }}
        >
          <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#e2e8f0" />
          <XAxis 
            dataKey="date" 
            tickFormatter={(value) => {
              const date = new Date(value);
              return `${date.getMonth() + 1}/${date.getDate()}`;
            }}
            stroke="#94a3b8" 
          />
          <YAxis stroke="#94a3b8" />
          <Tooltip 
            contentStyle={{ borderRadius: '0.5rem', border: 'none', boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06)' }}
            labelFormatter={(value) => new Date(value).toLocaleDateString()}
          />
          <Legend />
          <Line 
            type="monotone" 
            dataKey="value" 
            name="예상 수요" 
            stroke="#3b82f6" 
            strokeWidth={3}
            activeDot={{ r: 8 }} 
          />
          <Line 
            type="monotone" 
            dataKey="upper" 
            name="상한선" 
            stroke="#93c5fd" 
            strokeDasharray="5 5" 
          />
          <Line 
            type="monotone" 
            dataKey="lower" 
            name="하한선" 
            stroke="#93c5fd" 
            strokeDasharray="5 5" 
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
};

export default DemandChart;
