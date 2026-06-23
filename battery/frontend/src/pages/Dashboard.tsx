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
      let cumulativeRealizedProfit = 0;
      let cumulativeDegradation = 0;
      
      const dailyAgg: Record<string, { expected: number; realized: number }> = {};

      // Determine delta_t in hours
      const timeDiffHours = result.telemetry.length > 1
        ? (new Date(result.telemetry[1].time).getTime() - new Date(result.telemetry[0].time).getTime()) / 3600000
        : 1;

      const combined = result.telemetry.map((t: any) => {
        const plan = result.plans.find((p: any) => p.target_time === t.time);
        
        // Expected metrics based on Day-Ahead prices
        const buyCost = plan ? plan.expected_grid_buy_kw * t.price_buy_usd_per_kwh : 0;
        const sellRevenue = plan ? plan.expected_grid_sell_kw * t.price_sell_usd_per_kwh : 0;
        const profit = sellRevenue - buyCost;
        cumulativeProfit += profit;

        // Realized metrics based on Realized Spot prices (Intraday)
        const realizedBuyCost = plan ? plan.expected_grid_buy_kw * t.realized_price_buy_usd_per_kwh : 0;
        const realizedSellRevenue = plan ? plan.expected_grid_sell_kw * t.realized_price_sell_usd_per_kwh : 0;
        const realizedProfit = realizedSellRevenue - realizedBuyCost;
        cumulativeRealizedProfit += realizedProfit;

        // Calculate degradation cost (approx based on alpha * (P_charge^2 + P_discharge^2))
        const alpha = 0.001; 
        const degradation = plan ? alpha * (Math.pow(plan.cmd_charge_kw, 2) + Math.pow(plan.cmd_discharge_kw, 2)) : 0;
        cumulativeDegradation += degradation;

        // Daily aggregation for histogram
        const day = t.time.split('T')[0];
        if (!dailyAgg[day]) {
          dailyAgg[day] = { expected: 0, realized: 0 };
        }
        dailyAgg[day].expected += profit;
        dailyAgg[day].realized += realizedProfit;

        return {
          ...t,
          ...plan,
          profit,
          cumulativeProfit,
          realizedProfit,
          cumulativeRealizedProfit,
          buyCost,
          sellRevenue,
          realizedBuyCost,
          realizedSellRevenue,
          degradation,
          cumulativeDegradation,
          neg_cmd_discharge_kw: plan ? -plan.cmd_discharge_kw : 0,
          neg_expected_grid_sell_kw: plan ? -plan.expected_grid_sell_kw : 0,
          formattedTime: new Date(t.time).toLocaleString([], { month: 'short', day: 'numeric', hour: '2-digit' })
        };
      });

      // Format daily returns for histogram
      const dailyReturns = Object.entries(dailyAgg).map(([date, val]) => ({
        date,
        expectedProfit: val.expected,
        realizedProfit: val.realized,
        formattedDate: new Date(date).toLocaleDateString([], { month: 'short', day: 'numeric' })
      })).sort((a, b) => a.date.localeCompare(b.date));

      // Calculate SoC distribution for calendar wear analysis
      let soc0to20 = 0;
      let soc20to40 = 0;
      let soc40to60 = 0;
      let soc60to80 = 0;
      let soc80to100 = 0;
      let totalSoCPoints = 0;

      combined.forEach((t: any) => {
        if (t.expected_soc_kwh != null && activeSetup) {
          const cap = activeSetup.max_capacity_kwh || 13.5;
          const ratio = (t.expected_soc_kwh / cap) * 100;
          if (ratio <= 20) soc0to20++;
          else if (ratio <= 40) soc20to40++;
          else if (ratio <= 60) soc40to60++;
          else if (ratio <= 80) soc60to80++;
          else soc80to100++;
          totalSoCPoints++;
        }
      });

      const socDistribution = totalSoCPoints > 0 ? [
        { name: '0-20%', percentage: (soc0to20 / totalSoCPoints) * 100 },
        { name: '20-40%', percentage: (soc20to40 / totalSoCPoints) * 100 },
        { name: '40-60%', percentage: (soc40to60 / totalSoCPoints) * 100 },
        { name: '60-80%', percentage: (soc60to80 / totalSoCPoints) * 100 },
        { name: '80-100%', percentage: (soc80to100 / totalSoCPoints) * 100 },
      ] : [];

      setData({ combined, dailyReturns, socDistribution });
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
    if (!data || !activeSetup) return null;
    const totalBuyCost = data.combined.reduce((acc: number, curr: any) => acc + (curr.buyCost || 0), 0);
    const totalSellRevenue = data.combined.reduce((acc: number, curr: any) => acc + (curr.sellRevenue || 0), 0);
    
    const totalRealizedBuyCost = data.combined.reduce((acc: number, curr: any) => acc + (curr.realizedBuyCost || 0), 0);
    const totalRealizedSellRevenue = data.combined.reduce((acc: number, curr: any) => acc + (curr.realizedSellRevenue || 0), 0);
    
    const totalDegradation = data.combined.reduce((acc: number, curr: any) => acc + (curr.degradation || 0), 0);

    const expectedProfit = totalSellRevenue - totalBuyCost;
    const realizedProfit = totalRealizedSellRevenue - totalRealizedBuyCost;

    // Calculate throughput for EFC
    const timeDiffHours = data.combined.length > 1
      ? (new Date(data.combined[1].time).getTime() - new Date(data.combined[0].time).getTime()) / 3600000
      : 1;
    const totalChargeKwh = data.combined.reduce((acc: number, curr: any) => acc + (curr.cmd_charge_kw || 0), 0) * timeDiffHours;
    const totalDischargeKwh = data.combined.reduce((acc: number, curr: any) => acc + (curr.cmd_discharge_kw || 0), 0) * timeDiffHours;
    
    const capacity = activeSetup.max_capacity_kwh || 13.5;
    const efc = (totalChargeKwh + totalDischargeKwh) / (2 * capacity);
    
    // Estimate State of Health capacity fade: 0.0033% per cycle (typical LFP cell life)
    const soh = Math.max(0, 100 - (efc * 0.0033));

    return {
      totalBuyCost,
      totalSellRevenue,
      netProfit: expectedProfit,
      totalRealizedBuyCost,
      totalRealizedSellRevenue,
      netRealizedProfit: realizedProfit,
      profitVariance: realizedProfit - expectedProfit,
      buyVariance: totalRealizedBuyCost - totalBuyCost,
      sellVariance: totalRealizedSellRevenue - totalSellRevenue,
      totalDegradation,
      efc,
      soh
    };
  }, [data, activeSetup]);

  const chartCardStyle: React.CSSProperties = {
    marginBottom: '2rem',
    padding: '1.5rem',
    background: '#fff',
    border: '1px solid #e2e8f0',
    borderRadius: '12px',
    boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.05), 0 2px 4px -1px rgba(0, 0, 0, 0.03)'
  };

  const metricCardStyle: React.CSSProperties = {
    padding: '1.25rem',
    background: '#fff',
    border: '1px solid #e2e8f0',
    borderRadius: '12px',
    boxShadow: '0 2px 4px rgba(0,0,0,0.02)',
    display: 'flex',
    flexDirection: 'column',
    gap: '0.5rem'
  };

  const badgeStyle = (val: number, isCost: boolean = false): React.CSSProperties => {
    const isGood = isCost ? val <= 0 : val >= 0;
    const bg = isGood ? '#e6fffa' : '#fff5f5';
    const color = isGood ? '#319795' : '#e53e3e';
    
    return {
      display: 'inline-flex',
      alignItems: 'center',
      padding: '0.125rem 0.5rem',
      borderRadius: '9999px',
      fontSize: '0.75rem',
      fontWeight: 'bold',
      backgroundColor: bg,
      color: color,
      marginLeft: '0.5rem'
    };
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
        <SkeletonCard height={100} />
        <SkeletonCard height={100} />
        <SkeletonCard height={100} />
        <SkeletonCard height={100} />
      </div>
      <SkeletonCard height={300} />
      <SkeletonCard height={300} />
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
        gridTemplateColumns: `repeat(auto-fit, minmax(220px, 1fr))`, 
        gap: '1rem', 
        marginBottom: '2rem',
        position: 'sticky',
        top: '-1rem',
        zIndex: 10,
        backgroundColor: '#f5f7f9',
        padding: '1rem 0'
      }}>
        {/* Net Profit Card */}
        <div style={metricCardStyle}>
          <div style={{ fontSize: '0.75rem', fontWeight: 'bold', color: '#718096', textTransform: 'uppercase' }}>Net Profit</div>
          <div style={{ display: 'flex', alignItems: 'baseline', flexWrap: 'wrap' }}>
            <span style={{ fontSize: '1.25rem', fontWeight: 'bold', color: (metrics?.netRealizedProfit || 0) >= 0 ? '#38a169' : '#e53e3e' }}>
              ${metrics?.netRealizedProfit.toFixed(2)} <span style={{ fontSize: '0.8rem', fontWeight: 'normal', color: '#718096' }}>realized</span>
            </span>
            <span style={badgeStyle(metrics?.profitVariance || 0)}>
              {metrics && metrics.profitVariance >= 0 ? '+' : ''}{metrics?.profitVariance.toFixed(2)} var
            </span>
          </div>
          <div style={{ fontSize: '0.75rem', color: '#a0aec0' }}>
            Expected: ${metrics?.netProfit.toFixed(2)} (Day-Ahead Plan)
          </div>
        </div>

        {/* Grid Buy Cost Card */}
        <div style={metricCardStyle}>
          <div style={{ fontSize: '0.75rem', fontWeight: 'bold', color: '#718096', textTransform: 'uppercase' }}>Grid Buy Cost</div>
          <div style={{ display: 'flex', alignItems: 'baseline', flexWrap: 'wrap' }}>
            <span style={{ fontSize: '1.25rem', fontWeight: 'bold', color: '#e53e3e' }}>
              ${metrics?.totalRealizedBuyCost.toFixed(2)} <span style={{ fontSize: '0.8rem', fontWeight: 'normal', color: '#718096' }}>realized</span>
            </span>
            <span style={badgeStyle(metrics?.buyVariance || 0, true)}>
              {metrics && metrics.buyVariance >= 0 ? '+' : ''}{metrics?.buyVariance.toFixed(2)} var
            </span>
          </div>
          <div style={{ fontSize: '0.75rem', color: '#a0aec0' }}>
            Expected: ${metrics?.totalBuyCost.toFixed(2)}
          </div>
        </div>

        {/* Grid Sell Revenue Card */}
        <div style={metricCardStyle}>
          <div style={{ fontSize: '0.75rem', fontWeight: 'bold', color: '#718096', textTransform: 'uppercase' }}>Grid Sell Revenue</div>
          <div style={{ display: 'flex', alignItems: 'baseline', flexWrap: 'wrap' }}>
            <span style={{ fontSize: '1.25rem', fontWeight: 'bold', color: '#38a169' }}>
              ${metrics?.totalRealizedSellRevenue.toFixed(2)} <span style={{ fontSize: '0.8rem', fontWeight: 'normal', color: '#718096' }}>realized</span>
            </span>
            <span style={badgeStyle(metrics?.sellVariance || 0)}>
              {metrics && metrics.sellVariance >= 0 ? '+' : ''}{metrics?.sellVariance.toFixed(2)} var
            </span>
          </div>
          <div style={{ fontSize: '0.75rem', color: '#a0aec0' }}>
            Expected: ${metrics?.totalSellRevenue.toFixed(2)}
          </div>
        </div>

        {/* Battery Health Card (Global vs Job conditional details) */}
        <div style={metricCardStyle}>
          {isGlobal ? (
            <>
              <div style={{ fontSize: '0.75rem', fontWeight: 'bold', color: '#718096', textTransform: 'uppercase' }}>Battery Health</div>
              <div style={{ fontSize: '1.25rem', fontWeight: 'bold', color: '#805ad5' }}>
                {metrics?.soh.toFixed(3)}% <span style={{ fontSize: '0.8rem', fontWeight: 'normal', color: '#718096' }}>SoH</span>
              </div>
              <div style={{ fontSize: '0.75rem', color: '#a0aec0' }}>
                Throughput EFC: {metrics?.efc.toFixed(2)} cycles
              </div>
            </>
          ) : (
            <>
              <div style={{ fontSize: '0.75rem', fontWeight: 'bold', color: '#718096', textTransform: 'uppercase' }}>Est. Battery Wear</div>
              <div style={{ fontSize: '1.25rem', fontWeight: 'bold', color: '#805ad5' }}>
                ${metrics?.totalDegradation.toFixed(2)}
              </div>
              <div style={{ fontSize: '0.75rem', color: '#a0aec0' }}>
                Calculated degradation cost penalty
              </div>
            </>
          )}
        </div>
      </div>

      {/* Row 1: Cumulative Profit Comparison Chart */}
      <section style={chartCardStyle}>
        <h2 style={{ marginTop: 0, fontSize: '1.1rem', color: '#2d3748' }}>Cumulative Net Profit Comparison (USD)</h2>
        <div style={{ width: '100%', height: 300 }}>
          <ResponsiveContainer>
            <AreaChart data={data.combined}>
              <defs>
                <linearGradient id="colorRealized" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#319795" stopOpacity={0.2}/>
                  <stop offset="95%" stopColor="#319795" stopOpacity={0.0}/>
                </linearGradient>
                <linearGradient id="colorExpected" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#a0aec0" stopOpacity={0.1}/>
                  <stop offset="95%" stopColor="#a0aec0" stopOpacity="0.0"/>
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" vertical={false} stroke={GRID_COLOR} />
              <XAxis dataKey="formattedTime" stroke={AXIS_COLOR} fontSize={10} interval={Math.floor(data.combined.length / 6)} />
              <YAxis stroke={AXIS_COLOR} fontSize={10} />
              <Tooltip formatter={(value: number) => [`$${value.toFixed(2)}`]} />
              <Legend verticalAlign="top" height={36} iconSize={10} wrapperStyle={{ fontSize: '12px' }} />
              <Area type="monotone" dataKey="cumulativeRealizedProfit" stroke="#319795" name="Realized Net Profit (Backtest)" strokeWidth={2} fillOpacity={1} fill="url(#colorRealized)" />
              <Area type="monotone" dataKey="cumulativeProfit" stroke="#a0aec0" name="Expected Net Profit (Plan)" strokeWidth={2} strokeDasharray="5 5" fillOpacity={1} fill="url(#colorExpected)" />
              <ReferenceLine y={0} stroke="#333" strokeWidth={1} />
            </AreaChart>
          </ResponsiveContainer>
        </div>
      </section>

      {/* Row 2: Market Spot Prices (Common for both Views) */}
      <section style={chartCardStyle}>
        <h2 style={{ marginTop: 0, fontSize: '1.1rem', color: '#2d3748' }}>Market Spot Prices: Day-Ahead Plan vs. Realized Intraday (USD/kWh)</h2>
        <div style={{ width: '100%', height: 300 }}>
          <ResponsiveContainer>
            <LineChart data={data.combined}>
              <CartesianGrid strokeDasharray="3 3" vertical={false} stroke={GRID_COLOR} />
              <XAxis dataKey="formattedTime" stroke={AXIS_COLOR} fontSize={10} interval={Math.floor(data.combined.length / 6)} />
              <YAxis stroke={AXIS_COLOR} fontSize={10} />
              <Tooltip formatter={(value: number) => [`$${value.toFixed(4)}`]} />
              <Legend verticalAlign="top" height={36} iconSize={10} wrapperStyle={{ fontSize: '12px' }} />
              <Line type="stepAfter" dataKey="price_buy_usd_per_kwh" stroke="#a0aec0" name="Day-Ahead Buy (Plan)" dot={false} strokeWidth={1.5} strokeDasharray="3 3" />
              <Line type="stepAfter" dataKey="realized_price_buy_usd_per_kwh" stroke="#e53e3e" name="Intraday Buy (Realized)" dot={false} strokeWidth={2} />
              <Line type="stepAfter" dataKey="realized_price_sell_usd_per_kwh" stroke="#38a169" name="Intraday Sell (Realized)" dot={false} strokeWidth={2} />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </section>

      {/* Conditional Layout for Global vs. Job Details */}
      {isGlobal ? (
        <>
          {/* Row 3: Daily Returns & Battery State of Charge Distribution */}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(450px, 1fr))', gap: '1.5rem', marginBottom: '2rem' }}>
            {/* Daily returns */}
            <section style={chartCardStyle}>
              <h2 style={{ marginTop: 0, fontSize: '1.1rem', color: '#2d3748' }}>Daily Returns Comparison (USD)</h2>
              <div style={{ width: '100%', height: 250 }}>
                <ResponsiveContainer>
                  <BarChart data={data.dailyReturns}>
                    <CartesianGrid strokeDasharray="3 3" vertical={false} stroke={GRID_COLOR} />
                    <XAxis dataKey="formattedDate" stroke={AXIS_COLOR} fontSize={10} />
                    <YAxis stroke={AXIS_COLOR} fontSize={10} />
                    <Tooltip formatter={(value: number) => [`$${value.toFixed(2)}`]} />
                    <Legend verticalAlign="top" height={36} iconSize={10} wrapperStyle={{ fontSize: '12px' }} />
                    <Bar dataKey="expectedProfit" fill="#a0aec0" name="Expected Profit" />
                    <Bar dataKey="realizedProfit" name="Realized Profit">
                      {data.dailyReturns.map((entry: any, index: number) => (
                        <Cell key={`cell-${index}`} fill={entry.realizedProfit >= 0 ? '#319795' : '#f56565'} />
                      ))}
                    </Bar>
                    <ReferenceLine y={0} stroke="#333" />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </section>

            {/* Battery State of Charge (SoC) Distribution */}
            <section style={chartCardStyle}>
              <h2 style={{ marginTop: 0, fontSize: '1.1rem', color: '#2d3748' }}>Battery SoC Level Distribution (Calendar Wear Risk)</h2>
              <div style={{ width: '100%', height: 250 }}>
                <ResponsiveContainer>
                  <BarChart data={data.socDistribution}>
                    <CartesianGrid strokeDasharray="3 3" vertical={false} stroke={GRID_COLOR} />
                    <XAxis dataKey="name" stroke={AXIS_COLOR} fontSize={10} />
                    <YAxis stroke={AXIS_COLOR} fontSize={10} unit="%" />
                    <Tooltip formatter={(value: number) => [`${value.toFixed(1)}%`, 'Time Spent']} />
                    <Bar dataKey="percentage" name="Percentage of Time" radius={[4, 4, 0, 0]}>
                      {data.socDistribution.map((entry: any, index: number) => {
                        const colors = ['#e53e3e', '#3182ce', '#38a169', '#3182ce', '#e53e3e'];
                        return <Cell key={`cell-${index}`} fill={colors[index] || '#3182ce'} />;
                      })}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </section>
          </div>
        </>
      ) : (
        <>
          {/* Row 3: Daily Returns & SoC Details */}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(450px, 1fr))', gap: '1.5rem', marginBottom: '2rem' }}>
            <section style={chartCardStyle}>
              <h2 style={{ marginTop: 0, fontSize: '1.1rem', color: '#2d3748' }}>Daily Returns Comparison (USD)</h2>
              <div style={{ width: '100%', height: 250 }}>
                <ResponsiveContainer>
                  <BarChart data={data.dailyReturns}>
                    <CartesianGrid strokeDasharray="3 3" vertical={false} stroke={GRID_COLOR} />
                    <XAxis dataKey="formattedDate" stroke={AXIS_COLOR} fontSize={10} />
                    <YAxis stroke={AXIS_COLOR} fontSize={10} />
                    <Tooltip formatter={(value: number) => [`$${value.toFixed(2)}`]} />
                    <Legend verticalAlign="top" height={36} iconSize={10} wrapperStyle={{ fontSize: '12px' }} />
                    <Bar dataKey="expectedProfit" fill="#a0aec0" name="Expected Profit" />
                    <Bar dataKey="realizedProfit" name="Realized Profit">
                      {data.dailyReturns.map((entry: any, index: number) => (
                        <Cell key={`cell-${index}`} fill={entry.realizedProfit >= 0 ? '#319795' : '#f56565'} />
                      ))}
                    </Bar>
                    <ReferenceLine y={0} stroke="#333" />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </section>

            <section style={chartCardStyle}>
              <h2 style={{ marginTop: 0, fontSize: '1.1rem', color: '#2d3748' }}>Battery State of Charge (SoC) Details</h2>
              <div style={{ width: '100%', height: 250 }}>
                <ResponsiveContainer>
                  <AreaChart data={data.combined}>
                    <CartesianGrid strokeDasharray="3 3" vertical={false} stroke={GRID_COLOR} />
                    <XAxis dataKey="formattedTime" stroke={AXIS_COLOR} fontSize={10} interval={Math.floor(data.combined.length / 4)} />
                    <YAxis stroke={AXIS_COLOR} fontSize={10} />
                    <Tooltip formatter={(value: number) => [`${value.toFixed(2)} kWh`, 'SoC']} />
                    <Area type="monotone" dataKey="expected_soc_kwh" stroke="#805ad5" fill="#805ad5" fillOpacity={0.1} name="Battery SoC (kWh)" />
                  </AreaChart>
                </ResponsiveContainer>
              </div>
            </section>
          </div>

          {/* Row 4: Load Profiles and Battery Dispatch Commands */}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(450px, 1fr))', gap: '1.5rem', marginBottom: '2rem' }}>
            <section style={chartCardStyle}>
              <h2 style={{ marginTop: 0, fontSize: '1.1rem', color: '#2d3748' }}>Load & Solar Profiles (kW)</h2>
              <div style={{ width: '100%', height: 250 }}>
                <ResponsiveContainer>
                  <AreaChart data={data.combined}>
                    <CartesianGrid strokeDasharray="3 3" vertical={false} stroke={GRID_COLOR} />
                    <XAxis dataKey="formattedTime" stroke={AXIS_COLOR} fontSize={10} interval={Math.floor(data.combined.length / 4)} />
                    <YAxis stroke={AXIS_COLOR} fontSize={10} />
                    <Tooltip formatter={(value: number) => [`${value.toFixed(2)} kW`]} />
                    <Legend verticalAlign="top" height={36} iconSize={10} wrapperStyle={{ fontSize: '12px' }} />
                    <Area type="monotone" dataKey="load_kw" stroke="#3182ce" fill="#3182ce" fillOpacity={0.15} name="Microgrid Load" />
                    <Area type="monotone" dataKey="solar_kw" stroke="#d69e2e" fill="#d69e2e" fillOpacity={0.15} name="Solar Generation" />
                  </AreaChart>
                </ResponsiveContainer>
              </div>
            </section>

            <section style={chartCardStyle}>
              <h2 style={{ marginTop: 0, fontSize: '1.1rem', color: '#2d3748' }}>Optimized Battery Dispatch Commands (kW)</h2>
              <div style={{ width: '100%', height: 250 }}>
                <ResponsiveContainer>
                  <BarChart data={data.combined}>
                    <CartesianGrid strokeDasharray="3 3" vertical={false} stroke={GRID_COLOR} />
                    <XAxis dataKey="formattedTime" stroke={AXIS_COLOR} fontSize={10} interval={Math.floor(data.combined.length / 4)} />
                    <YAxis stroke={AXIS_COLOR} fontSize={10} />
                    <Tooltip formatter={(value: number) => [`${value.toFixed(2)} kW`]} />
                    <Legend verticalAlign="top" height={36} iconSize={10} wrapperStyle={{ fontSize: '12px' }} />
                    <ReferenceLine y={0} stroke="#000" />
                    <Bar dataKey="cmd_charge_kw" fill="#3182ce" name="Charge Command" />
                    <Bar dataKey="neg_cmd_discharge_kw" fill="#ed8936" name="Discharge Command" />
                  </BarChart>
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
