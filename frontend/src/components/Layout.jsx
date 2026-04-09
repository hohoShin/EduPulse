import React from 'react';
import { NavLink, Outlet } from 'react-router-dom';

const Layout = () => {
  return (
    <div className="app-shell" style={{ display: 'flex', minHeight: '100vh', fontFamily: 'system-ui, sans-serif' }}>
      <aside className="sidebar" style={{ width: '250px', backgroundColor: '#1e293b', color: 'white', padding: '1rem' }}>
        <h1 style={{ fontSize: '1.5rem', fontWeight: 'bold', marginBottom: '2rem' }}>EduPulse</h1>
        <nav style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
          <NavLink 
            to="/" 
            style={({ isActive }) => ({
              padding: '0.75rem 1rem',
              borderRadius: '0.375rem',
              textDecoration: 'none',
              color: isActive ? '#38bdf8' : '#cbd5e1',
              backgroundColor: isActive ? '#0f172a' : 'transparent',
              fontWeight: isActive ? '600' : 'normal'
            })}
          >
            대시보드
          </NavLink>
          <NavLink 
            to="/simulator" 
            style={({ isActive }) => ({
              padding: '0.75rem 1rem',
              borderRadius: '0.375rem',
              textDecoration: 'none',
              color: isActive ? '#38bdf8' : '#cbd5e1',
              backgroundColor: isActive ? '#0f172a' : 'transparent',
              fontWeight: isActive ? '600' : 'normal'
            })}
          >
            시뮬레이터
          </NavLink>
        </nav>
      </aside>
      <main className="main-content" style={{ flex: 1, backgroundColor: '#f8fafc', overflowY: 'auto' }}>
        <header className="header" style={{ backgroundColor: 'white', padding: '1rem 2rem', borderBottom: '1px solid #e2e8f0', display: 'flex', alignItems: 'center' }}>
          <h2 style={{ fontSize: '1.25rem', margin: 0, color: '#334155' }}>제어판</h2>
        </header>
        <div style={{ padding: '2rem' }}>
          <Outlet />
        </div>
      </main>
    </div>
  );
};

export default Layout;
