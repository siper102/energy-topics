import React, { useState } from 'react';
import Dashboard from './Dashboard';
import { useNavigate } from 'react-router-dom';
import { useSetups } from '../context/SetupContext';

const GlobalDashboard: React.FC = () => {
  const { activeSetup, loading: setupLoading } = useSetups();
  const [startDate, setStartDate] = useState('');
  const [endDate, setEndDate] = useState('');
  const navigate = useNavigate();

  // We only pass the dates to Dashboard if both are set, otherwise we might fetch all data,
  // or we can pass them directly since the backend supports optional dates.
  
  return (
    <div style={{ maxWidth: '1400px', margin: '0 auto', padding: '2rem' }}>
      <header style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '2rem', background: '#fff', padding: '1.5rem', borderRadius: '12px', boxShadow: '0 2px 4px rgba(0,0,0,0.05)', border: '1px solid #e1e4e8' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '1.5rem' }}>
          <div>
            <h1 style={{ margin: 0, fontSize: '1.25rem' }}>Global Analysis: {activeSetup?.name || 'Loading...'}</h1>
            <p style={{ color: '#666', margin: 0, fontSize: '0.9rem' }}>
              View aggregated performance for this setup.
            </p>
          </div>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
          <div>
            <label style={{ fontSize: '0.8rem', fontWeight: 'bold', color: '#666', display: 'block', marginBottom: '0.25rem' }}>From Date</label>
            <input 
              type="date" 
              value={startDate} 
              onChange={e => setStartDate(e.target.value)} 
              style={{ padding: '0.5rem', borderRadius: '4px', border: '1px solid #ccc' }}
            />
          </div>
          <div>
            <label style={{ fontSize: '0.8rem', fontWeight: 'bold', color: '#666', display: 'block', marginBottom: '0.25rem' }}>To Date</label>
            <input 
              type="date" 
              value={endDate} 
              onChange={e => setEndDate(e.target.value)} 
              style={{ padding: '0.5rem', borderRadius: '4px', border: '1px solid #ccc' }}
            />
          </div>
          <button 
            onClick={() => { setStartDate(''); setEndDate(''); }}
            style={{ 
              padding: '0.5rem 1rem', 
              background: '#e1e4e8', 
              color: '#333', 
              border: 'none', 
              borderRadius: '6px', 
              cursor: 'pointer',
              fontWeight: 'bold',
              alignSelf: 'flex-end',
              height: '38px'
            }}
          >
            Clear Filter
          </button>
        </div>
      </header>

      {/* Render the Dashboard component as a child */}
      <div style={{ background: '#fff', borderRadius: '12px', padding: '1rem', boxShadow: '0 2px 4px rgba(0,0,0,0.05)', border: '1px solid #e1e4e8' }}>
        {setupLoading ? (
          <p>Loading setups...</p>
        ) : !activeSetup ? (
          <p>Please select a setup in the navbar.</p>
        ) : (
          <Dashboard startDate={startDate} endDate={endDate} isGlobal={true} />
        )}
      </div>
    </div>
  );
};

export default GlobalDashboard;
