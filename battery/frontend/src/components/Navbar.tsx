import React from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { useSetups } from '../context/SetupContext';

const Navbar: React.FC = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const { setups, activeSetup, setActiveSetupId } = useSetups();

  return (
    <nav style={{ 
      background: '#fff', 
      borderBottom: '1px solid #e1e4e8', 
      padding: '0.75rem 2rem', 
      display: 'flex', 
      justifyContent: 'space-between', 
      alignItems: 'center',
      position: 'sticky',
      top: 0,
      zIndex: 100,
      boxShadow: '0 2px 4px rgba(0,0,0,0.02)'
    }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: '2rem' }}>
        <div 
          onClick={() => navigate('/')}
          style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', fontSize: '1.25rem', fontWeight: 'bold', color: '#2d3748', cursor: 'pointer' }}
        >
          <span>🔋</span> BatteryOpt
        </div>
        
        <div style={{ display: 'flex', gap: '1rem' }}>
          <button 
            onClick={() => navigate('/')}
            style={{ 
              background: 'none', 
              border: 'none', 
              color: location.pathname === '/' ? '#3498db' : '#4a5568',
              fontWeight: location.pathname === '/' ? 'bold' : 'normal',
              cursor: 'pointer',
              fontSize: '0.95rem'
            }}
          >
            Operations
          </button>
          <button 
            onClick={() => navigate('/global')}
            style={{ 
              background: 'none', 
              border: 'none', 
              color: location.pathname === '/global' ? '#3498db' : '#4a5568',
              fontWeight: location.pathname === '/global' ? 'bold' : 'normal',
              cursor: 'pointer',
              fontSize: '0.95rem'
            }}
          >
            Global Dashboard
          </button>
        </div>
      </div>

      <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
        <div style={{ fontSize: '0.85rem', color: '#666', fontWeight: 'bold' }}>ACTIVE SETUP:</div>
        <select 
          value={activeSetup?.id || ''} 
          onChange={(e) => setActiveSetupId(parseInt(e.target.value))}
          style={{ 
            padding: '0.4rem 0.8rem', 
            borderRadius: '6px', 
            border: '1px solid #cbd5e0',
            background: '#f8fafc',
            color: '#2d3748',
            fontWeight: '600',
            outline: 'none',
            cursor: 'pointer'
          }}
        >
          {setups.map(s => (
            <option key={s.id} value={s.id}>{s.name}</option>
          ))}
        </select>
        
        <button 
          onClick={() => alert('Setup Management coming soon!')} // TODO: Add setup management page
          style={{
            background: '#edf2f7',
            border: 'none',
            borderRadius: '50%',
            width: '32px',
            height: '32px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            cursor: 'pointer',
            fontSize: '1rem'
          }}
          title="Manage Setups"
        >
          ⚙️
        </button>
      </div>
    </nav>
  );
};

export default Navbar;
