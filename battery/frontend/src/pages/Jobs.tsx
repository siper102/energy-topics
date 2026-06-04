import React, { useState, useEffect, useCallback } from 'react';
import { jobService } from '../services/api';
import Dashboard from './Dashboard';
import { useNavigate } from 'react-router-dom';
import { useSetups } from '../context/SetupContext';

interface Job {
  id: number;
  type: string;
  status: string;
  start_date: string;
  end_date: string;
  alpha: number;
  grid_fee: number;
  created_at: string;
  finished_at: string | null;
  error_message: string | null;
  net_profit?: number | null;
}

const Jobs: React.FC = () => {
  const { activeSetup, loading: setupLoading } = useSetups();
  const [jobs, setJobs] = useState<Job[]>([]);
  const [loading, setLoading] = useState(true);
  const [showTriggerForm, setShowTriggerForm] = useState(false);
  const [selectedJob, setSelectedJob] = useState<Job | null>(null);
  const [isClosing, setIsClosing] = useState(false);
  
  // Form state
  const [startDate, setStartDate] = useState('2025-06-01');
  const [endDate, setEndDate] = useState('2025-06-05');
  const [alpha, setAlpha] = useState(0.001);
  const [gridFee, setGridFee] = useState(0.01);
  const [submitting, setSubmitting] = useState(false);

  const navigate = useNavigate();

  const fetchJobs = async () => {
    if (!activeSetup) return;
    try {
      const data = await jobService.listJobs(activeSetup.id);
      setJobs(data);
    } catch (error) {
      console.error('Failed to fetch jobs:', error);
    } finally {
      setLoading(false);
    }
  };


  useEffect(() => {
    fetchJobs();
    const interval = setInterval(fetchJobs, 5000);
    return () => clearInterval(interval);
  }, [activeSetup]);

  const handleCloseModal = useCallback(() => {
    if (!selectedJob || isClosing) return;
    setIsClosing(true);
    setTimeout(() => {
      setSelectedJob(null);
      setIsClosing(false);
    }, 250); // match animation duration
  }, [selectedJob, isClosing]);

  // Close modal on ESC key
  const handleKeyDown = useCallback((event: KeyboardEvent) => {
    if (event.key === 'Escape') {
      handleCloseModal();
    }
  }, [handleCloseModal]);

  useEffect(() => {
    if (selectedJob) {
      window.addEventListener('keydown', handleKeyDown);
    } else {
      window.removeEventListener('keydown', handleKeyDown);
    }
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [selectedJob, handleKeyDown]);

  const handleTrigger = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!activeSetup) return;
    setSubmitting(true);
    try {
      await jobService.triggerFullJob(startDate, endDate, activeSetup.id, alpha, gridFee);
      setShowTriggerForm(false);
      fetchJobs();
    } catch (error) {
      console.error('Failed to trigger job:', error);
      alert('Failed to trigger job');
    } finally {
      setSubmitting(false);
    }
  };

  const cardStyle: React.CSSProperties = {
    background: '#fff',
    border: '1px solid #e1e4e8',
    borderRadius: '12px',
    padding: '1.5rem',
    marginBottom: '1rem',
    boxShadow: '0 2px 4px rgba(0,0,0,0.05)',
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    cursor: 'pointer',
    transition: 'all 0.2s ease',
  };

  const statusBadgeStyle = (status: string): React.CSSProperties => {
    let color = '#666';
    let bg = '#eee';
    if (status === 'SUCCESS') { color = '#155724'; bg = '#d4edda'; }
    if (status === 'FAILURE') { color = '#721c24'; bg = '#f8d7da'; }
    if (status === 'RUNNING') { color = '#856404'; bg = '#fff3cd'; }
    
    return {
      padding: '0.25rem 0.75rem',
      borderRadius: '20px',
      fontSize: '0.85rem',
      fontWeight: 'bold',
      backgroundColor: bg,
      color: color,
      textTransform: 'uppercase'
    };
  };

  const modalOverlayStyle: React.CSSProperties = {
    position: 'fixed',
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
    backgroundColor: 'rgba(0,0,0,0.5)',
    display: 'flex',
    justifyContent: 'center',
    alignItems: 'center',
    zIndex: 1000,
    padding: '2rem',
    backdropFilter: 'blur(4px)',
    animation: isClosing ? 'modalFadeOut 0.25s ease-in forwards' : 'modalFadeIn 0.25s ease-out forwards'
  };

  const modalContentStyle: React.CSSProperties = {
    background: '#f5f7f9',
    width: '100%',
    maxWidth: '1200px',
    maxHeight: '90vh',
    borderRadius: '16px',
    overflowY: 'auto',
    position: 'relative',
    padding: '2rem',
    boxShadow: '0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04)',
    animation: isClosing ? 'modalSlideOut 0.25s ease-in forwards' : 'modalSlideIn 0.25s ease-out forwards'
  };

  return (
    <div style={{ maxWidth: '1000px', margin: '0 auto', padding: '2rem' }}>
      <style>{`
        @keyframes modalFadeIn {
          from { opacity: 0; }
          to { opacity: 1; }
        }
        @keyframes modalFadeOut {
          from { opacity: 1; }
          to { opacity: 0; }
        }
        @keyframes modalSlideIn {
          from { transform: scale(0.95) translateY(20px); opacity: 0; }
          to { transform: scale(1) translateY(0); opacity: 1; }
        }
        @keyframes modalSlideOut {
          from { transform: scale(1) translateY(0); opacity: 1; }
          to { transform: scale(0.95) translateY(20px); opacity: 0; }
        }
        .job-card:hover {
          transform: translateY(-2px);
          box-shadow: 0 4px 8px rgba(0,0,0,0.1);
          border-color: #3498db;
        }
      `}</style>

      {setupLoading ? (
        <p>Loading setups...</p>
      ) : !activeSetup ? (
        <div style={{ textAlign: 'center', padding: '3rem', background: '#fff', borderRadius: '12px', border: '1px solid #e1e4e8' }}>
          <h2>No Setup Active</h2>
          <p>Please create or select a setup to view operations.</p>
        </div>
      ) : (
        <>
          <header style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '2rem' }}>
            <div>
              <h1 style={{ margin: 0 }}>Operations: {activeSetup.name}</h1>
              <p style={{ color: '#666', margin: 0 }}>Manage data ingestion and optimization for this setup.</p>
            </div>
            <button 
              onClick={() => setShowTriggerForm(!showTriggerForm)}
              style={{
                padding: '0.6rem 1.2rem',
                background: '#3498db',
                color: 'white',
                border: 'none',
                borderRadius: '6px',
                cursor: 'pointer',
                fontWeight: 'bold'
              }}
            >
              {showTriggerForm ? 'Cancel' : 'Trigger New Job'}
            </button>
          </header>

          {/* Setup Parameters Overview - Hidden when creating a new job to focus on inputs */}
          {!showTriggerForm && (
            <section style={{ 
              background: '#fff', 
              border: '1px solid #e1e4e8', 
              borderRadius: '12px', 
              padding: '1.25rem', 
              marginBottom: '2rem',
              boxShadow: '0 2px 4px rgba(0,0,0,0.02)'
            }}>
              <h3 style={{ margin: '0 0 1rem 0', fontSize: '0.9rem', color: '#4a5568', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                Setup Configuration
              </h3>
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(150px, 1fr))', gap: '1.5rem' }}>
                <div>
                  <div style={{ fontSize: '0.75rem', color: '#718096', marginBottom: '0.25rem' }}>Battery Capacity</div>
                  <div style={{ fontWeight: '600', color: '#2d3748' }}>{activeSetup.max_capacity_kwh} kWh</div>
                </div>
                <div>
                  <div style={{ fontSize: '0.75rem', color: '#718096', marginBottom: '0.25rem' }}>Max Power</div>
                  <div style={{ fontWeight: '600', color: '#2d3748' }}>{activeSetup.max_power_kw} kW</div>
                </div>
                <div>
                  <div style={{ fontSize: '0.75rem', color: '#718096', marginBottom: '0.25rem' }}>Efficiency (C/D)</div>
                  <div style={{ fontWeight: '600', color: '#2d3748' }}>{activeSetup.efficiency_charge * 100}% / {activeSetup.efficiency_discharge * 100}%</div>
                </div>
                <div>
                  <div style={{ fontSize: '0.75rem', color: '#718096', marginBottom: '0.25rem' }}>Solar Peak</div>
                  <div style={{ fontWeight: '600', color: '#2d3748' }}>{activeSetup.peak_power_kw} kWp</div>
                </div>
                <div>
                  <div style={{ fontSize: '0.75rem', color: '#718096', marginBottom: '0.25rem' }}>Location</div>
                  <div style={{ fontWeight: '600', color: '#2d3748' }}>{activeSetup.lat}, {activeSetup.lon}</div>
                </div>
                <div>
                  <div style={{ fontSize: '0.75rem', color: '#718096', marginBottom: '0.25rem' }}>Orientation</div>
                  <div style={{ fontWeight: '600', color: '#2d3748' }}>Tilt: {activeSetup.tilt}°, Azi: {activeSetup.azimuth}°</div>
                </div>
              </div>
            </section>
          )}

          {showTriggerForm && (
            <form onSubmit={handleTrigger} style={{ background: '#f8f9fa', padding: '2rem', borderRadius: '12px', marginBottom: '2rem', border: '1px solid #dee2e6' }}>
              <h3>Configure Integrated Job ({activeSetup.name})</h3>
              <p style={{ color: '#666', fontSize: '0.9rem', marginBottom: '1.5rem' }}>This will trigger both data ingestion and battery optimization for the selected range using this setup's parameters.</p>
          
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1.5rem', marginBottom: '1.5rem' }}>
            <div>
              <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: 'bold' }}>Start Date</label>
              <input type="date" value={startDate} onChange={e => setStartDate(e.target.value)} style={{ width: '100%', padding: '0.6rem', borderRadius: '4px', border: '1px solid #ccc' }} required />
            </div>
            <div>
              <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: 'bold' }}>End Date</label>
              <input type="date" value={endDate} onChange={e => setEndDate(e.target.value)} style={{ width: '100%', padding: '0.6rem', borderRadius: '4px', border: '1px solid #ccc' }} required />
            </div>
            <div>
              <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: 'bold' }}>Alpha (Degradation)</label>
              <input type="number" step="0.0001" value={alpha} onChange={e => setAlpha(Number(e.target.value))} style={{ width: '100%', padding: '0.6rem', borderRadius: '4px', border: '1px solid #ccc' }} />
            </div>
            <div>
              <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: 'bold' }}>Grid Fee (USD/kWh)</label>
              <input type="number" step="0.01" value={gridFee} onChange={e => setGridFee(Number(e.target.value))} style={{ width: '100%', padding: '0.6rem', borderRadius: '4px', border: '1px solid #ccc' }} />
            </div>
          </div>
          
          <button 
            type="submit" 
            disabled={submitting}
            style={{ 
              width: '100%', 
              padding: '0.8rem', 
              background: '#2ecc71', 
              color: 'white', 
              border: 'none', 
              borderRadius: '6px', 
              cursor: submitting ? 'not-allowed' : 'pointer',
              fontWeight: 'bold',
              fontSize: '1rem'
            }}
          >
            {submitting ? 'Starting...' : 'Run Ingestion + Optimization'}
          </button>
        </form>
      )}

      {loading && <p>Loading jobs...</p>}
      {!loading && jobs.length === 0 && <p>No jobs found. Trigger your first job!</p>}

      <div style={{ display: 'flex', flexDirection: 'column' }}>
        {jobs.map(job => (
          <div 
            key={job.id} 
            className="job-card"
            style={{
              ...cardStyle,
              borderLeft: selectedJob?.id === job.id ? '6px solid #3498db' : '1px solid #e1e4e8'
            }}
            onClick={() => job.status === 'SUCCESS' && setSelectedJob(job)}
          >
            <div style={{ flex: 1 }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '1rem', marginBottom: '0.5rem' }}>
                <span style={{ fontWeight: 'bold', fontSize: '1.1rem' }}>Job #{job.id}</span>
                <span style={statusBadgeStyle(job.status)}>{job.status}</span>
              </div>
              <div style={{ color: '#666', fontSize: '0.9rem' }}>
                <span>📅 {new Date(job.start_date).toLocaleDateString()} - {new Date(job.end_date).toLocaleDateString()}</span>
                <span style={{ marginLeft: '1.5rem' }}>⚙️ α={job.alpha}, fee=${job.grid_fee}</span>
              </div>
              {job.status === 'FAILURE' && job.error_message && (
                <div style={{ 
                  marginTop: '0.75rem', 
                  padding: '0.5rem 0.75rem', 
                  background: '#fff5f5', 
                  border: '1px solid #feb2b2', 
                  borderRadius: '6px',
                  color: '#c53030',
                  fontSize: '0.85rem',
                  maxWidth: '80%'
                }}>
                  <strong>Error:</strong> {job.error_message}
                </div>
              )}
              <div style={{ marginTop: '0.5rem', fontSize: '0.8rem', color: '#999' }}>
                Created: {new Date(job.created_at).toLocaleString()}
              </div>
            </div>
            
            <div style={{ textAlign: 'right' }}>
              {job.net_profit !== undefined && job.net_profit !== null && (
                <div style={{ 
                  fontSize: '0.95rem', 
                  fontWeight: '600', 
                  color: job.net_profit >= 0 ? '#2ecc71' : '#e74c3c',
                  marginBottom: '0.5rem',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'flex-end',
                  gap: '0.25rem'
                }}>
                  <span style={{ color: '#666', fontWeight: 'normal', marginRight: '0.25rem' }}>Net Profit:</span>
                  <span style={{ fontSize: '1.1rem' }}>{job.net_profit >= 0 ? '↑' : '↓'}</span>
                  <span>${Math.abs(job.net_profit).toFixed(2)}</span>
                </div>
              )}
              <div style={{ color: job.status === 'SUCCESS' ? '#3498db' : (job.status === 'FAILURE' ? '#e53e3e' : '#ccc'), fontWeight: 'bold' }}>
                {job.status === 'SUCCESS' ? 'View Analysis →' : (job.status === 'FAILURE' ? 'Job Failed' : 'Wait for success...')}
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Dashboard Modal */}
      {selectedJob && (
        <div style={modalOverlayStyle} onClick={handleCloseModal}>
          <div style={modalContentStyle} onClick={e => e.stopPropagation()}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '2rem' }}>
              <div>
                <h2 style={{ margin: 0 }}>Analysis for Job #{selectedJob.id}</h2>
                <p style={{ color: '#666', margin: 0 }}>
                  Range: {new Date(selectedJob.start_date).toLocaleDateString()} - {new Date(selectedJob.end_date).toLocaleDateString()}
                </p>
              </div>
              <button 
                onClick={handleCloseModal}
                style={{ 
                  padding: '0.5rem 1rem', 
                  background: '#e74c3c', 
                  color: 'white', 
                  border: 'none', 
                  borderRadius: '6px', 
                  cursor: 'pointer',
                  fontWeight: 'bold'
                }}
              >
                Close (Esc)
              </button>
            </div>
            
            <Dashboard 
              startDate={selectedJob.start_date.split('T')[0]} 
              endDate={selectedJob.end_date.split('T')[0]} 
            />
          </div>
        </div>
      )}
        </>
      )}
    </div>
  );
};

export default Jobs;
