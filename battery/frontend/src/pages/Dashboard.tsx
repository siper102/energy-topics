import React, { useEffect, useState, useMemo } from 'react';
import { dataService } from '../services/api';
import { useSetups } from '../context/SetupContext';
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
  ReferenceLine,
  Cell
} from 'recharts';

interface DashboardProps {
  startDate: string;
  endDate: string;
  isGlobal?: boolean;
}

const SkeletonCard: React.FC<{ height?: number; width?: string }> = ({ height = 300, width = '100%' }) => (
  <div style={{ 
    height, 
    width, 
    background: '#eee', 
    borderRadius: '12px', 
    marginBottom: '2rem',
    overflow: 'hidden',
    position: 'relative'
  }}>
    <div style={{
      position: 'absolute',
      top: 0,
      left: 0,
      width: '100%',
      height: '100%',
      background: 'linear-gradient(90deg, #eee 25%, #f5f5f5 50%, #eee 75%)',
      backgroundSize: '200% 100%',
      animation: 'shimmer 1.5s infinite linear'
    }} />
    <style>{`
      @keyframes shimmer {
        0% { background-position: -200% 0; }
        100% { background-position: 200% 0; }
      }
    `}</style>
  </div>
);

const Dashboard: React.FC<DashboardProps> = ({ startDate, endDate, isGlobal = false }) => {
  const { activeSetup } = useSetups();
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchData = async () => {
    if (!activeSetup) return;
    setLoading(true);
    try {
      const result = await dataService.getDashboardData(activeSetup.id, startDate, endDate);
      
      let cumulativeProfit = 0;
      let cumulativeDegradation = 0;
      const dailyAgg: Record<string, number> = {};

      const combined = result.telemetry.map((t: any) => {
        const plan = result.plans.find((p: any) => p.target_time === t.time);
        
        const buyCost = plan ? plan.expected_grid_buy_kw * t.price_buy_usd_per_kwh : 0;
        const sellRevenue = plan ? plan.expected_grid_sell_kw * t.price_sell_usd_per_kwh : 0;
        const profit = sellRevenue - buyCost;
        cumulativeProfit += profit;

        // Calculate degradation cost (approx based on alpha * (P_charge^2 + P_discharge^2))
        const alpha = 0.001; 
        const degradation = (isGlobal && plan) ? alpha * (Math.pow(plan.cmd_charge_kw, 2) + Math.pow(plan.cmd_discharge_kw, 2)) : 0;
        cumulativeDegradation += degradation;

        // Daily aggregation for histogram
        const day = t.time.split('T')[0];
        dailyAgg[day] = (dailyAgg[day] || 0) + profit;

        return {
          ...t,
          ...plan,
          profit,
          cumulativeProfit,
          degradation,
          cumulativeDegradation,
          neg_cmd_discharge_kw: plan ? -plan.cmd_discharge_kw : 0,
          neg_expected_grid_sell_kw: plan ? -plan.expected_grid_sell_kw : 0,
          formattedTime: new Date(t.time).toLocaleString([], { month: 'short', day: 'numeric', hour: '2-digit' })
        };
      });

      // Format daily returns for histogram
      const dailyReturns = Object.entries(dailyAgg).map(([date, profit]) => ({
        date,
        profit,
        formattedDate: new Date(date).toLocaleDateString([], { month: 'short', day: 'numeric' })
      })).sort((a, b) => a.date.localeCompare(b.date));

      setData({ combined, dailyReturns });
      setError(null);
    } catch (err: any) {
      console.error(err);
      setError('Failed to fetch dashboard data.');
    }
    setLoading(false);
  };

  useEffect(() => {
    fetchData();
  }, [startDate, endDate, activeSetup]);

  const metrics = useMemo(() => {
    if (!data) return null;
    const totalBuyCost = data.combined.reduce((acc: number, curr: any) => acc + (curr.expected_grid_buy_kw * curr.price_buy_usd_per_kwh || 0), 0);
    const totalSellRevenue = data.combined.reduce((acc: number, curr: any) => acc + (curr.expected_grid_sell_kw * curr.price_sell_usd_per_kwh || 0), 0);
    const totalDegradation = data.combined.reduce((acc: number, curr: any) => acc + (curr.degradation || 0), 0);
    return {
      totalBuyCost,
      totalSellRevenue,
      netProfit: totalSellRevenue - totalBuyCost,
      totalDegradation
    };
  }, [data]);

  const chartCardStyle: React.CSSProperties = {
    marginBottom: '2rem',
    padding: '1.5rem',
    background: '#fff',
    border: '1px solid #e1e4e8',
    borderRadius: '12px',
    boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)'
  };

  const metricCardStyle: React.CSSProperties = {
    padding: '1.5rem',
    background: '#fff',
    border: '1px solid #e1e4e8',
    borderRadius: '12px',
    textAlign: 'center',
    boxShadow: '0 2px 4px rgba(0,0,0,0.05)'
  };

  if (loading) return (
    <div style={{ width: '100%' }}>
      <div style={{ 
        display: 'grid', 
        gridTemplateColumns: 'repeat(4, 1fr)', 
        gap: '1rem', 
        marginBottom: '2rem',
        position: 'sticky',
        top: '-1rem',
        zIndex: 10,
        backgroundColor: '#f5f7f9',
        padding: '1rem 0'
      }}>
        <SkeletonCard height={80} />
        <SkeletonCard height={80} />
        <SkeletonCard height={80} />
        <SkeletonCard height={80} />
      </div>
      <SkeletonCard height={250} />
      <SkeletonCard height={250} />
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
        <SkeletonCard height={250} />
        <SkeletonCard height={250} />
      </div>
    </div>
  );

  if (error) return <div style={{ color: '#e74c3c', padding: '2rem', textAlign: 'center' }}>{error}</div>;
  if (!data || data.combined.length === 0) return <div style={{ padding: '2rem', textAlign: 'center' }}>No data found for this range.</div>;

  const AXIS_COLOR = "#2d3748";
  const GRID_COLOR = "#cbd5e0";

  return (
    <div style={{ width: '100%', animation: 'fadeIn 0.5s ease-out' }}>
      <style>{`
        @keyframes fadeIn {
          from { opacity: 0; transform: translateY(10px); }
          to { opacity: 1; transform: translateY(0); }
        }
      `}</style>
      
      {/* Metrics Row */}
      <div style={{ 
        display: 'grid', 
        gridTemplateColumns: `repeat(auto-fit, minmax(180px, 1fr))`, 
        gap: '1rem', 
        marginBottom: '2rem',
        position: 'sticky',
        top: '-1rem',
        zIndex: 10,
        backgroundColor: '#f5f7f9',
        padding: '1rem 0'
      }}>
        <div style={metricCardStyle}>
          <div style={{ fontSize: '0.8rem', color: '#666' }}>Grid Buy Cost</div>
          <div style={{ fontSize: '1.25rem', fontWeight: 'bold', color: '#e53e3e' }}>${metrics?.totalBuyCost.toFixed(2)}</div>
        </div>
        <div style={metricCardStyle}>
          <div style={{ fontSize: '0.8rem', color: '#666' }}>Grid Sell Revenue</div>
          <div style={{ fontSize: '1.25rem', fontWeight: 'bold', color: '#38a169' }}>${metrics?.totalSellRevenue.toFixed(2)}</div>
        </div>
        {isGlobal && (
          <div style={metricCardStyle}>
            <div style={{ fontSize: '0.8rem', color: '#666' }}>Est. Battery Wear</div>
            <div style={{ fontSize: '1.25rem', fontWeight: 'bold', color: '#805ad5' }}>${metrics?.totalDegradation.toFixed(2)}</div>
          </div>
        )}
        <div style={metricCardStyle}>
          <div style={{ fontSize: '0.8rem', color: '#666' }}>Net Profit</div>
          <div style={{ fontSize: '1.25rem', fontWeight: 'bold', color: (metrics?.netProfit || 0) >= 0 ? '#2ecc71' : '#e74c3c' }}>
            ${metrics?.netProfit.toFixed(2)}
          </div>
        </div>
      </div>

      {/* Row 1: Profit Chart */}
      <section style={chartCardStyle}>
        <h2 style={{ marginTop: 0, fontSize: '1.1rem' }}>Cumulative Net Profit (USD)</h2>
        <div style={{ width: '100%', height: 250 }}>
          <ResponsiveContainer>
            <AreaChart data={data.combined}>
              <CartesianGrid strokeDasharray="3 3" vertical={false} stroke={GRID_COLOR} />
              <XAxis dataKey="formattedTime" stroke={AXIS_COLOR} fontSize={10} interval={Math.floor(data.combined.length / 6)} />
              <YAxis stroke={AXIS_COLOR} fontSize={10} />
              <Tooltip formatter={(value: number) => [`$${value.toFixed(2)}`, 'Profit']} />
              <Area type="monotone" dataKey="cumulativeProfit" stroke="#2ecc71" fill="#2ecc71" fillOpacity={0.1} strokeWidth={2} />
              <ReferenceLine y={0} stroke="#333" strokeWidth={1} />
            </AreaChart>
          </ResponsiveContainer>
        </div>
      </section>

      {/* Row 2: Market Prices */}
      <section style={chartCardStyle}>
        <h2 style={{ marginTop: 0, fontSize: '1.1rem' }}>Market Prices (USD/kWh)</h2>
        <div style={{ width: '100%', height: 250 }}>
          <ResponsiveContainer>
            <LineChart data={data.combined}>
              <CartesianGrid strokeDasharray="3 3" vertical={false} stroke={GRID_COLOR} />
              <XAxis dataKey="formattedTime" stroke={AXIS_COLOR} fontSize={10} interval={Math.floor(data.combined.length / 6)} />
              <YAxis stroke={AXIS_COLOR} fontSize={10} />
              <Tooltip />
              <Legend verticalAlign="top" height={36} iconSize={10} wrapperStyle={{ fontSize: '10px' }}/>
              <Line type="stepAfter" dataKey="price_buy_usd_per_kwh" stroke="#e53e3e" name="Buy Price" dot={false} strokeWidth={2} />
              <Line type="stepAfter" dataKey="price_sell_usd_per_kwh" stroke="#38a169" name="Sell Price" dot={false} strokeWidth={2} />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </section>

      {isGlobal ? (
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem', marginBottom: '2rem' }}>
          <section style={chartCardStyle}>
            <h2 style={{ marginTop: 0, fontSize: '1.1rem' }}>Daily Returns (USD)</h2>
            <div style={{ width: '100%', height: 250 }}>
              <ResponsiveContainer>
                <BarChart data={data.dailyReturns}>
                  <CartesianGrid strokeDasharray="3 3" vertical={false} stroke={GRID_COLOR} />
                  <XAxis dataKey="formattedDate" stroke={AXIS_COLOR} fontSize={10} />
                  <YAxis stroke={AXIS_COLOR} fontSize={10} />
                  <Tooltip formatter={(value: number) => [`$${value.toFixed(2)}`, 'Profit']} />
                  <Bar dataKey="profit">
                    {data.dailyReturns.map((entry: any, index: number) => (
                      <Cell key={`cell-${index}`} fill={entry.profit >= 0 ? '#48bb78' : '#f56565'} />
                    ))}
                  </Bar>
                  <ReferenceLine y={0} stroke="#333" />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </section>

          <section style={chartCardStyle}>
            <h2 style={{ marginTop: 0, fontSize: '1.1rem' }}>Cumulative Battery Wear Cost (USD)</h2>
            <div style={{ width: '100%', height: 250 }}>
              <ResponsiveContainer>
                <AreaChart data={data.combined}>
                  <CartesianGrid strokeDasharray="3 3" vertical={false} stroke={GRID_COLOR} />
                  <XAxis dataKey="formattedTime" stroke={AXIS_COLOR} fontSize={10} interval={Math.floor(data.combined.length / 6)} />
                  <YAxis stroke={AXIS_COLOR} fontSize={10} />
                  <Tooltip formatter={(value: number) => [`$${value.toFixed(2)}`, 'Wear Cost']} />
                  <Area type="monotone" dataKey="cumulativeDegradation" stroke="#805ad5" fill="#805ad5" fillOpacity={0.1} strokeWidth={2} />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          </section>
        </div>
      ) : (
        <>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem', marginBottom: '2rem' }}>
            <section style={chartCardStyle}>
              <h2 style={{ marginTop: 0, fontSize: '1.1rem' }}>Load & Solar (kW)</h2>
              <div style={{ width: '100%', height: 250 }}>
                <ResponsiveContainer>
                  <AreaChart data={data.combined}>
                    <CartesianGrid strokeDasharray="3 3" vertical={false} stroke={GRID_COLOR} />
                    <XAxis dataKey="formattedTime" stroke={AXIS_COLOR} fontSize={10} interval={Math.floor(data.combined.length / 3)} />
                    <YAxis stroke={AXIS_COLOR} fontSize={10} />
                    <Tooltip />
                    <Area type="monotone" dataKey="load_kw" stackId="1" stroke="#3182ce" fill="#3182ce" name="Load" />
                    <Area type="monotone" dataKey="solar_kw" stackId="2" stroke="#d69e2e" fill="#d69e2e" name="Solar" />
                  </AreaChart>
                </ResponsiveContainer>
              </div>
            </section>

            <section style={chartCardStyle}>
              <h2 style={{ marginTop: 0, fontSize: '1.1rem' }}>Battery SoC (kWh)</h2>
              <div style={{ width: '100%', height: 250 }}>
                <ResponsiveContainer>
                  <AreaChart data={data.combined}>
                    <CartesianGrid strokeDasharray="3 3" vertical={false} stroke={GRID_COLOR} />
                    <XAxis dataKey="formattedTime" stroke={AXIS_COLOR} fontSize={10} interval={Math.floor(data.combined.length / 3)} />
                    <YAxis stroke={AXIS_COLOR} fontSize={10} />
                    <Tooltip />
                    <Area type="monotone" dataKey="expected_soc_kwh" stroke="#805ad5" fill="#805ad5" name="SoC (kWh)" />
                  </AreaChart>
                </ResponsiveContainer>
              </div>
            </section>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem', marginBottom: '2rem' }}>
            <section style={chartCardStyle}>
              <h2 style={{ marginTop: 0, fontSize: '1.1rem' }}>Dispatch Commands (kW)</h2>
              <div style={{ width: '100%', height: 250 }}>
                <ResponsiveContainer>
                  <BarChart data={data.combined}>
                    <CartesianGrid strokeDasharray="3 3" vertical={false} stroke={GRID_COLOR} />
                    <XAxis dataKey="formattedTime" stroke={AXIS_COLOR} fontSize={10} interval={Math.floor(data.combined.length / 3)} />
                    <YAxis stroke={AXIS_COLOR} fontSize={10} />
                    <Tooltip />
                    <ReferenceLine y={0} stroke="#000" />
                    <Bar dataKey="cmd_charge_kw" fill="#3182ce" name="Charge" />
                    <Bar dataKey="neg_cmd_discharge_kw" fill="#ed8936" name="Discharge" />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </section>

            <section style={chartCardStyle}>
              <h2 style={{ marginTop: 0, fontSize: '1.1rem' }}>Grid Buy/Sell Orders (kW)</h2>
              <div style={{ width: '100%', height: 250 }}>
                <ResponsiveContainer>
                  <AreaChart data={data.combined}>
                    <CartesianGrid strokeDasharray="3 3" vertical={false} stroke={GRID_COLOR} />
                    <XAxis dataKey="formattedTime" stroke={AXIS_COLOR} fontSize={10} interval={Math.floor(data.combined.length / 3)} />
                    <YAxis stroke={AXIS_COLOR} fontSize={10} />
                    <Tooltip />
                    <ReferenceLine y={0} stroke="#333" strokeWidth={1} />
                    <Area type="monotone" dataKey="expected_grid_buy_kw" stroke="#e53e3e" fill="#e53e3e" fillOpacity={0.1} name="Grid Buy" />
                    <Area type="monotone" dataKey="neg_expected_grid_sell_kw" stroke="#38a169" fill="#38a169" fillOpacity={0.1} name="Grid Sell" />
                  </AreaChart>
                </ResponsiveContainer>
              </div>
            </section>
          </div>
        </>
      )}
    </div>
  );
};

export default Dashboard;
