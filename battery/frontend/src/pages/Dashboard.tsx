import React, { useEffect, useState } from 'react';
import { dataService } from '../services/api';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  AreaChart,
  Area,
  BarChart,
  Bar,
  ReferenceLine
} from 'recharts';

const Dashboard: React.FC = () => {
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchData = async () => {
    setLoading(true);
    try {
      const result = await dataService.getDashboardData();
      
      // Combine telemetry and plans for a single chart data source
      const combined = result.telemetry.map((t: any) => {
        const plan = result.plans.find((p: any) => p.target_time === t.time);
        return {
          ...t,
          ...plan,
          // For the dispatch chart, we want discharge to be negative
          neg_cmd_discharge_kw: plan ? -plan.cmd_discharge_kw : 0,
          neg_expected_grid_sell_kw: plan ? -plan.expected_grid_sell_kw : 0,
          // Format time for XAxis
          formattedTime: new Date(t.time).toLocaleString([], { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' })
        };
      });

      console.log('Combined Dashboard Data:', combined.slice(0, 5));
      setData(combined);
      setError(null);
    } catch (err: any) {
      console.error(err);
      setError('Failed to fetch dashboard data. Make sure you have ingested data and run optimization.');
    }
    setLoading(false);
  };

  useEffect(() => {
    fetchData();
  }, []);

  if (loading) return <div style={{ padding: '2rem', textAlign: 'center' }}>Loading dashboard...</div>;
  if (error) return <div style={{ color: '#e74c3c', padding: '2rem', textAlign: 'center', background: '#fdf2f2', margin: '2rem', borderRadius: '8px' }}>{error}</div>;
  if (!data || data.length === 0) return <div style={{ padding: '2rem', textAlign: 'center' }}>No data available. Go to the <strong>Jobs</strong> page to ingest data and run optimization.</div>;

  const chartCardStyle: React.CSSProperties = {
    marginBottom: '2rem',
    padding: '1.5rem',
    background: '#fff',
    border: '1px solid #e1e4e8',
    borderRadius: '12px',
    boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06)'
  };

  const gridContainerStyle: React.CSSProperties = {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fit, minmax(500px, 1fr))',
    gap: '2rem',
    marginBottom: '2rem'
  };

  const headerStyle: React.CSSProperties = {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: '2rem',
    paddingBottom: '1rem',
    borderBottom: '2px solid #f1f3f5'
  };

  const buttonStyle: React.CSSProperties = {
    padding: '0.6rem 1.2rem',
    cursor: 'pointer',
    backgroundColor: '#3498db',
    color: 'white',
    border: 'none',
    borderRadius: '6px',
    fontWeight: '600',
    transition: 'background-color 0.2s'
  };

  const AXIS_COLOR = "#2d3748";
  const GRID_COLOR = "#cbd5e0";

  return (
    <div style={{ maxWidth: '1400px', margin: '0 auto', padding: '2rem' }}>
      <header style={headerStyle}>
        <div>
          <h1 style={{ margin: 0, color: '#1a1a1a' }}>Energy Storage Dashboard</h1>
          <p style={{ margin: '0.5rem 0 0', color: '#666' }}>Real-time telemetry and optimized dispatch strategies</p>
        </div>
        <button 
          onClick={fetchData} 
          style={buttonStyle}
          onMouseOver={(e) => (e.currentTarget.style.backgroundColor = '#2980b9')}
          onMouseOut={(e) => (e.currentTarget.style.backgroundColor = '#3498db')}
        >
          Refresh Data
        </button>
      </header>

      {/* Row 1: Market Prices */}
      <section style={chartCardStyle}>
        <h2 style={{ marginTop: 0, fontSize: '1.25rem' }}>Market Prices (USD/kWh)</h2>
        <div style={{ width: '100%', height: 300 }}>
          <ResponsiveContainer>
            <LineChart data={data}>
              <CartesianGrid strokeDasharray="3 3" vertical={false} stroke={GRID_COLOR} />
              <XAxis 
                dataKey="formattedTime" 
                stroke={AXIS_COLOR}
                tick={{ fill: AXIS_COLOR, fontSize: 12, fontWeight: 'bold' }}
                interval={Math.floor(data.length / 10)}
              />
              <YAxis 
                stroke={AXIS_COLOR}
                tick={{ fill: AXIS_COLOR, fontSize: 12, fontWeight: 'bold' }}
              />
              <Tooltip />
              <Legend verticalAlign="top" height={36}/>
              <Line type="stepAfter" dataKey="price_buy_usd_per_kwh" stroke="#e53e3e" name="Buy Price" dot={false} strokeWidth={3} />
              <Line type="stepAfter" dataKey="price_sell_usd_per_kwh" stroke="#38a169" name="Sell Price" dot={false} strokeWidth={3} />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </section>

      <div style={gridContainerStyle}>
        {/* Row 2, Col 1: Load & Solar */}
        <section style={chartCardStyle}>
          <h2 style={{ marginTop: 0, fontSize: '1.25rem' }}>Load & Solar Generation (kW)</h2>
          <div style={{ width: '100%', height: 350 }}>
            <ResponsiveContainer>
              <AreaChart data={data}>
                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke={GRID_COLOR} />
                <XAxis 
                  dataKey="formattedTime" 
                  interval={Math.floor(data.length / 5)} 
                  stroke={AXIS_COLOR}
                  tick={{ fill: AXIS_COLOR, fontSize: 11, fontWeight: 'bold' }}
                />
                <YAxis 
                  stroke={AXIS_COLOR}
                  tick={{ fill: AXIS_COLOR, fontSize: 11, fontWeight: 'bold' }}
                />
                <Tooltip />
                <Legend verticalAlign="top" height={36}/>
                <Area type="monotone" dataKey="load_kw" stackId="1" stroke="#3182ce" fill="#3182ce" fillOpacity={0.8} name="Load" />
                <Area type="monotone" dataKey="solar_kw" stackId="2" stroke="#d69e2e" fill="#d69e2e" fillOpacity={0.8} name="Solar" />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </section>

        {/* Row 2, Col 2: Battery SOC */}
        <section style={chartCardStyle}>
          <h2 style={{ marginTop: 0, fontSize: '1.25rem' }}>Battery State of Charge (kWh)</h2>
          <div style={{ width: '100%', height: 350 }}>
            <ResponsiveContainer>
              <AreaChart data={data}>
                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke={GRID_COLOR} />
                <XAxis 
                  dataKey="formattedTime" 
                  interval={Math.floor(data.length / 5)} 
                  stroke={AXIS_COLOR}
                  tick={{ fill: AXIS_COLOR, fontSize: 11, fontWeight: 'bold' }}
                />
                <YAxis 
                  stroke={AXIS_COLOR}
                  tick={{ fill: AXIS_COLOR, fontSize: 11, fontWeight: 'bold' }}
                />
                <Tooltip />
                <Legend verticalAlign="top" height={36}/>
                <Area type="monotone" dataKey="expected_soc_kwh" stroke="#805ad5" fill="#805ad5" fillOpacity={0.8} name="SoC (kWh)" />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </section>
      </div>

      {/* Row 3: Dispatch Commands */}
      <section style={chartCardStyle}>
        <h2 style={{ marginTop: 0, fontSize: '1.25rem' }}>Battery Dispatch Strategy (kW)</h2>
        <div style={{ width: '100%', height: 350 }}>
          <ResponsiveContainer>
            <BarChart data={data}>
              <CartesianGrid strokeDasharray="3 3" vertical={false} stroke={GRID_COLOR} />
              <XAxis 
                dataKey="formattedTime" 
                interval={Math.floor(data.length / 10)} 
                stroke={AXIS_COLOR}
                tick={{ fill: AXIS_COLOR, fontSize: 11, fontWeight: 'bold' }}
              />
              <YAxis 
                stroke={AXIS_COLOR}
                tick={{ fill: AXIS_COLOR, fontSize: 11, fontWeight: 'bold' }}
              />
              <Tooltip />
              <Legend verticalAlign="top" height={36}/>
              <ReferenceLine y={0} stroke="#2d3748" strokeWidth={2} />
              <Bar dataKey="cmd_charge_kw" fill="#3182ce" name="Charge" />
              <Bar dataKey="neg_cmd_discharge_kw" fill="#ed8936" name="Discharge" />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </section>

      {/* Row 4: Grid Interaction */}
      <section style={chartCardStyle}>
        <h2 style={{ marginTop: 0, fontSize: '1.25rem' }}>Grid Interaction (kW)</h2>
        <div style={{ width: '100%', height: 350 }}>
          <ResponsiveContainer>
            <LineChart data={data}>
              <CartesianGrid strokeDasharray="3 3" vertical={false} stroke={GRID_COLOR} />
              <XAxis 
                dataKey="formattedTime" 
                interval={Math.floor(data.length / 10)} 
                stroke={AXIS_COLOR}
                tick={{ fill: AXIS_COLOR, fontSize: 11, fontWeight: 'bold' }}
              />
              <YAxis 
                stroke={AXIS_COLOR}
                tick={{ fill: AXIS_COLOR, fontSize: 11, fontWeight: 'bold' }}
              />
              <Tooltip />
              <Legend verticalAlign="top" height={36}/>
              <ReferenceLine y={0} stroke="#2d3748" strokeWidth={2} />
              <Line type="monotone" dataKey="expected_grid_buy_kw" stroke="#e53e3e" name="Grid Buy" strokeWidth={3} dot={false} />
              <Line type="monotone" dataKey="neg_expected_grid_sell_kw" stroke="#38a169" name="Grid Sell" strokeWidth={3} dot={false} />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </section>
    </div>
  );
};

export default Dashboard;
