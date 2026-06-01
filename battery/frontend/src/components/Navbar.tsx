import React from 'react';
import { Link, useLocation } from 'react-router-dom';

const Navbar: React.FC = () => {
  const location = useLocation();

  const navStyle: React.CSSProperties = {
    padding: '0 2rem',
    background: '#ffffff',
    height: '64px',
    display: 'flex',
    alignItems: 'center',
    gap: '3rem',
    boxShadow: '0 1px 3px 0 rgba(0, 0, 0, 0.1), 0 1px 2px 0 rgba(0, 0, 0, 0.06)',
    marginBottom: '0',
    position: 'sticky',
    top: 0,
    zIndex: 100
  };

  const brandStyle: React.CSSProperties = {
    fontSize: '1.25rem',
    fontWeight: 'bold',
    color: '#2d3748',
    textDecoration: 'none',
    display: 'flex',
    alignItems: 'center',
    gap: '0.5rem'
  };

  const navLinksStyle: React.CSSProperties = {
    display: 'flex',
    gap: '1.5rem',
    height: '100%'
  };

  const getLinkStyle = (path: string): React.CSSProperties => ({
    color: location.pathname === path ? '#3182ce' : '#4a5568',
    textDecoration: 'none',
    fontWeight: '600',
    fontSize: '0.95rem',
    display: 'flex',
    alignItems: 'center',
    borderBottom: location.pathname === path ? '2px solid #3182ce' : '2px solid transparent',
    transition: 'all 0.2s ease',
    padding: '0 0.5rem'
  });

  return (
    <nav style={navStyle}>
      <Link to="/" style={brandStyle}>
        <span style={{ fontSize: '1.5rem' }}>🔋</span> BatteryOpt
      </Link>
      <div style={navLinksStyle}>
        <Link to="/dashboard" style={getLinkStyle('/dashboard')}>Dashboard</Link>
        <Link to="/jobs" style={getLinkStyle('/jobs')}>Jobs & Operations</Link>
      </div>
    </nav>
  );
};

export default Navbar;
