import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import Layout from './components/Layout.jsx';
import Dashboard from './pages/Dashboard.jsx';
import Simulator from './pages/Simulator.jsx';
import StatusPanel from './components/StatusPanel.jsx';
import Marketing from './pages/Marketing.jsx';
import Operations from './pages/Operations.jsx';
import Market from './pages/Market.jsx';

const NotFound = () => (
  <div style={{ padding: '2rem' }}>
    <StatusPanel 
      variant="error" 
      title="페이지를 찾을 수 없음" 
      message="찾으시는 페이지가 존재하지 않습니다." 
    />
  </div>
);

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Layout />}>
          <Route index element={<Dashboard />} />
          <Route path="simulator" element={<Simulator />} />
          <Route path="marketing" element={<Marketing />} />
          <Route path="operations" element={<Operations />} />
          <Route path="market" element={<Market />} />
          <Route path="*" element={<NotFound />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}

export default App;
