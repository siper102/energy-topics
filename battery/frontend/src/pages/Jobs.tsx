import React, { useState, useEffect } from 'react';
import { dataService, optimizationService } from '../services/api';

const Jobs: React.FC = () => {
  const [startDate, setStartDate] = useState('2025-06-01');
  const [endDate, setEndDate] = useState('2025-06-05');
  const [alpha, setAlpha] = useState(0.001);
  const [gridFee, setGridFee] = useState(0.01);
  const [taskId, setTaskId] = useState<string | null>(null);
  const [status, setStatus] = useState<any>(null);
  const [loading, setLoading] = useState(false);

  const [ingestStatus, setIngestStatus] = useState<any>(null);

  const handleIngest = async () => {
    try {
      await dataService.triggerIngestion(startDate, endDate);
      setIngestStatus({ status: 'RUNNING', message: 'Triggered...' });
    } catch (error) {
      console.error(error);
      alert('Failed to trigger ingestion');
    }
  };

  useEffect(() => {
    let interval: any;
    if (ingestStatus?.status === 'RUNNING') {
      interval = setInterval(async () => {
        try {
          const data = await dataService.getIngestionStatus();
          setIngestStatus(data);
          if (data.status !== 'RUNNING') {
            clearInterval(interval);
          }
        } catch (error) {
          console.error(error);
        }
      }, 2000);
    }
    return () => clearInterval(interval);
  }, [ingestStatus]);

  const handleOptimize = async () => {
    setLoading(true);
    try {
      const data = await optimizationService.triggerOptimization(alpha, gridFee);
      setTaskId(data.task_id);
      setStatus({ status: 'PENDING' });
    } catch (error) {
      console.error(error);
      alert('Failed to trigger optimization');
    }
    setLoading(false);
  };

  useEffect(() => {
    let interval: any;
    if (taskId && status?.status !== 'SUCCESS' && status?.status !== 'FAILURE') {
      interval = setInterval(async () => {
        try {
          const data = await optimizationService.getStatus(taskId);
          setStatus(data);
          if (data.status === 'SUCCESS' || data.status === 'FAILURE') {
            clearInterval(interval);
          }
        } catch (error) {
          console.error(error);
        }
      }, 2000);
    }
    return () => clearInterval(interval);
  }, [taskId, status]);

  const sectionStyle: React.CSSProperties = {
    marginBottom: '2rem',
    padding: '1.5rem',
    border: '1px solid #ddd',
    borderRadius: '8px',
    background: '#f9f9f9'
  };

  const inputGroupStyle: React.CSSProperties = {
    marginBottom: '1rem'
  };

  const labelStyle: React.CSSProperties = {
    display: 'inline-block',
    width: '120px',
    fontWeight: 'bold'
  };

  return (
    <div>
      <h1>Jobs & Operations</h1>
      <p>Use this page to manually trigger system tasks and monitor their progress.</p>

      <section style={sectionStyle}>
        <h2>1. Data Management</h2>
        <p>Fetch energy market data (ENTSO-E) and solar forecasts (Open-Meteo).</p>
        <div style={inputGroupStyle}>
          <label style={labelStyle}>Start Date:</label>
          <input 
            type="date" 
            value={startDate} 
            onChange={(e) => setStartDate(e.target.value)} 
            style={{ padding: '0.4rem', borderRadius: '4px', border: '1px solid #ccc' }}
          />
        </div>
        <div style={inputGroupStyle}>
          <label style={labelStyle}>End Date:</label>
          <input 
            type="date" 
            value={endDate} 
            onChange={(e) => setEndDate(e.target.value)} 
            style={{ padding: '0.4rem', borderRadius: '4px', border: '1px solid #ccc' }}
          />
        </div>
        <button 
          onClick={handleIngest} 
          style={{ padding: '0.6rem 1.2rem', cursor: 'pointer', background: '#007bff', color: 'white', border: 'none', borderRadius: '4px' }}
        >
          {ingestStatus?.status === 'RUNNING' ? 'Ingesting...' : 'Trigger Data Ingestion'}
        </button>

        {ingestStatus && (
          <div style={{ marginTop: '1rem', padding: '1rem', background: '#fff', border: '1px solid #ccc', borderRadius: '4px' }}>
            <p><strong>Status:</strong> 
              <span style={{ 
                marginLeft: '0.5rem', 
                padding: '0.2rem 0.5rem', 
                borderRadius: '4px', 
                background: ingestStatus.status === 'SUCCESS' ? '#d4edda' : ingestStatus.status === 'FAILURE' ? '#f8d7da' : '#fff3cd',
                color: ingestStatus.status === 'SUCCESS' ? '#155724' : ingestStatus.status === 'FAILURE' ? '#721c24' : '#856404'
              }}>
                {ingestStatus.status}
              </span>
            </p>
            <p>{ingestStatus.message}</p>
          </div>
        )}
      </section>

      <section style={sectionStyle}>
        <h2>2. Battery Optimization</h2>
        <p>Run the Pyomo optimization engine (IPOPT) to generate a dispatch plan.</p>
        <div style={inputGroupStyle}>
          <label style={labelStyle}>Alpha:</label>
          <input 
            type="number" 
            step="0.001" 
            value={alpha} 
            onChange={(e) => setAlpha(Number(e.target.value))} 
            style={{ padding: '0.4rem', borderRadius: '4px', border: '1px solid #ccc' }}
          />
          <small style={{ marginLeft: '1rem', color: '#666' }}>Degradation penalty</small>
        </div>
        <div style={inputGroupStyle}>
          <label style={labelStyle}>Grid Fee:</label>
          <input 
            type="number" 
            step="0.01" 
            value={gridFee} 
            onChange={(e) => setGridFee(Number(e.target.value))} 
            style={{ padding: '0.4rem', borderRadius: '4px', border: '1px solid #ccc' }}
          />
          <small style={{ marginLeft: '1rem', color: '#666' }}>USD/kWh</small>
        </div>
        <button 
          onClick={handleOptimize} 
          disabled={loading}
          style={{ 
            padding: '0.6rem 1.2rem', 
            cursor: loading ? 'not-allowed' : 'pointer', 
            background: loading ? '#ccc' : '#28a745', 
            color: 'white', 
            border: 'none', 
            borderRadius: '4px' 
          }}
        >
          {loading ? 'Submitting...' : 'Run Optimization Job'}
        </button>

        {taskId && (
          <div style={{ marginTop: '1.5rem', padding: '1rem', background: '#fff', border: '1px solid #ccc', borderRadius: '4px' }}>
            <h3 style={{ marginTop: 0 }}>Optimization Status</h3>
            <p><strong>Task ID:</strong> <code style={{ background: '#eee', padding: '0.2rem' }}>{taskId}</code></p>
            <p>
              <strong>Status:</strong> 
              <span style={{ 
                marginLeft: '0.5rem', 
                padding: '0.2rem 0.5rem', 
                borderRadius: '4px', 
                background: status?.status === 'SUCCESS' ? '#d4edda' : status?.status === 'FAILURE' ? '#f8d7da' : '#fff3cd',
                color: status?.status === 'SUCCESS' ? '#155724' : status?.status === 'FAILURE' ? '#721c24' : '#856404'
              }}>
                {status?.status || 'PENDING'}
              </span>
            </p>
            {status?.error && (
              <div style={{ color: '#721c24', background: '#f8d7da', padding: '0.5rem', borderRadius: '4px' }}>
                <strong>Error:</strong> {status.error}
              </div>
            )}
            {status?.result && (
              <div style={{ marginTop: '1rem' }}>
                <strong>Result:</strong>
                <pre style={{ background: '#eee', padding: '0.5rem', borderRadius: '4px', overflowX: 'auto' }}>
                  {JSON.stringify(status.result, null, 2)}
                </pre>
              </div>
            )}
          </div>
        )}
      </section>
    </div>
  );
};

export default Jobs;
