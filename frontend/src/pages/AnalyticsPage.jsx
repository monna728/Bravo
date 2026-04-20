import { useState, useEffect } from 'react';
import {
  WEEKLY_DEMAND,
  HOURLY_DEMAND,
  BOROUGH_BREAKDOWN,
  MONTHLY_TREND,
  EVENT_IMPACT,
  KPI_CARDS,
  AI_INSIGHTS,
} from '../data/analyticsData';

// ─── Mini chart helpers (pure SVG, no deps) ──────────────────────────────────

function SparkLine({ data, color = '#3b82f6', height = 40 }) {
  const max = Math.max(...data);
  const min = Math.min(...data);
  const range = max - min || 1;
  const w = 120;
  const h = height;
  const pts = data
    .map((v, i) => {
      const x = (i / (data.length - 1)) * w;
      const y = h - ((v - min) / range) * (h - 4) - 2;
      return `${x},${y}`;
    })
    .join(' ');
  return (
    <svg viewBox={`0 0 ${w} ${h}`} width={w} height={h} className="overflow-visible">
      <polyline points={pts} fill="none" stroke={color} strokeWidth="2" strokeLinejoin="round" />
    </svg>
  );
}

function BarChart({ data, valueKey, labelKey, color = '#3b82f6', height = 120 }) {
  const max = Math.max(...data.map((d) => d[valueKey]));
  return (
    <div className="flex items-end gap-1 h-full" style={{ height }}>
      {data.map((d, i) => {
        const pct = (d[valueKey] / max) * 100;
        return (
          <div key={i} className="flex flex-col items-center flex-1 gap-1">
            <div
              className="w-full rounded-t-sm transition-all duration-500"
              style={{ height: `${pct}%`, backgroundColor: color, opacity: 0.85 }}
              title={`${d[labelKey]}: ${d[valueKey]}`}
            />
            <span className="text-gray-500 text-xs">{d[labelKey]}</span>
          </div>
        );
      })}
    </div>
  );
}

function LineChart({ data, valueKey, labelKey, color = '#3b82f6', height = 120 }) {
  const vals = data.map((d) => d[valueKey]);
  const max = Math.max(...vals);
  const min = Math.min(...vals);
  const range = max - min || 1;
  const w = 400;
  const h = height;
  const pts = vals
    .map((v, i) => {
      const x = (i / (vals.length - 1)) * w;
      const y = h - ((v - min) / range) * (h - 10) - 5;
      return `${x},${y}`;
    })
    .join(' ');
  const area = `0,${h} ${pts} ${w},${h}`;

  return (
    <div className="relative w-full" style={{ height }}>
      <svg viewBox={`0 0 ${w} ${h}`} preserveAspectRatio="none" className="absolute inset-0 w-full h-full">
        <defs>
          <linearGradient id="areaGrad" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor={color} stopOpacity="0.25" />
            <stop offset="100%" stopColor={color} stopOpacity="0" />
          </linearGradient>
        </defs>
        <polygon points={area} fill="url(#areaGrad)" />
        <polyline points={pts} fill="none" stroke={color} strokeWidth="2.5" strokeLinejoin="round" />
      </svg>
      {/* x-axis labels */}
      <div className="absolute bottom-0 left-0 right-0 flex justify-between">
        {data.filter((_, i) => i % Math.floor(data.length / 6) === 0).map((d, i) => (
          <span key={i} className="text-xs text-gray-500">{d[labelKey]}</span>
        ))}
      </div>
    </div>
  );
}

function DonutChart({ segments }) {
  const total = segments.reduce((s, x) => s + x.value, 0);
  let cumAngle = -90;
  const r = 40;
  const cx = 50;
  const cy = 50;

  function polarToXY(deg, radius) {
    const rad = (deg * Math.PI) / 180;
    return { x: cx + radius * Math.cos(rad), y: cy + radius * Math.sin(rad) };
  }

  return (
    <svg viewBox="0 0 100 100" className="w-24 h-24">
      {segments.map((seg, i) => {
        const angle = (seg.value / total) * 360;
        const start = polarToXY(cumAngle, r);
        const end = polarToXY(cumAngle + angle, r);
        const largeArc = angle > 180 ? 1 : 0;
        const d = `M ${cx} ${cy} L ${start.x} ${start.y} A ${r} ${r} 0 ${largeArc} 1 ${end.x} ${end.y} Z`;
        cumAngle += angle;
        return <path key={i} d={d} fill={seg.color} opacity="0.85" />;
      })}
      <circle cx={cx} cy={cy} r={24} fill="white" />
    </svg>
  );
}

// ─── Sub-components ───────────────────────────────────────────────────────────

function KpiCard({ label, value, change }) {
  const positive = change >= 0;
  return (
    <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-4 flex flex-col gap-2">
      <span className="text-xs font-semibold text-gray-400 uppercase tracking-wide">{label}</span>
      <span className="text-2xl font-black text-gray-900">{value}</span>
      <span className={`text-xs font-semibold flex items-center gap-1 ${positive ? 'text-green-500' : 'text-red-400'}`}>
        {positive ? '▲' : '▼'} {Math.abs(change)}% vs last week
      </span>
    </div>
  );
}

function InsightCard({ insight }) {
  const bg = {
    opportunity: 'bg-blue-50 border-blue-200',
    warning: 'bg-amber-50 border-amber-200',
    info: 'bg-gray-50 border-gray-200',
  }[insight.type];
  const title = {
    opportunity: 'text-blue-700',
    warning: 'text-amber-700',
    info: 'text-gray-700',
  }[insight.type];
  return (
    <div className={`rounded-2xl border p-4 ${bg}`}>
      <div className="flex items-start gap-3">
        <span className="text-xl">{insight.icon}</span>
        <div>
          <h4 className={`font-semibold text-sm mb-1 ${title}`}>{insight.title}</h4>
          <p className="text-xs text-gray-600 leading-relaxed">{insight.body}</p>
        </div>
      </div>
    </div>
  );
}

// ─── AI Summary Panel ─────────────────────────────────────────────────────────

function AISummaryPanel() {
  const [summary, setSummary] = useState('');
  const [loading, setLoading] = useState(false);
  const [generated, setGenerated] = useState(false);

  const generateSummary = async () => {
    setLoading(true);
    setSummary('');
    setGenerated(true);

    const prompt = `You are an analytics AI for a ride-sharing company (like Uber) operating in NYC.
Here is their performance data this week:
- Total rides: 39,200 (up 6.4% WoW)
- Best day: Saturday 8,200 rides
- Revenue per ride: $4.50 (up 2.1%)
- Driver utilisation: 74% (down 1.2%)
- Avg wait time: 4.7 min (down 8.3%)
- Top borough: Manhattan (46% share, +8.2% trend)
- Queens declining: -1.4% for 3 straight weeks
- Friday 8-11pm demand 34% above driver supply
- Sports events drive 62% demand lift, concerts 78%
- Morning commuter rides up 22% YoY

Write a concise, confident 3-paragraph executive summary covering: (1) overall performance and headline metrics, (2) key risks and opportunities, (3) recommended immediate actions. Be specific and data-driven. Use plain prose, no bullet points or headers.`;

    try {
      const res = await fetch('https://api.anthropic.com/v1/messages', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          model: 'claude-sonnet-4-20250514',
          max_tokens: 1000,
          messages: [{ role: 'user', content: prompt }],
        }),
      });
      const data = await res.json();
      const text = data.content?.map((c) => c.text || '').join('') || 'Unable to generate summary.';
      setSummary(text);
    } catch {
      setSummary('Failed to connect to AI. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="bg-gray-900 rounded-2xl p-5 text-white relative overflow-hidden">
      {/* Background glow */}
      <div className="absolute top-0 right-0 w-40 h-40 bg-blue-500 rounded-full opacity-10 blur-3xl pointer-events-none" />
      <div className="relative z-10">
        <div className="flex items-center justify-between mb-3">
          <div className="flex items-center gap-2">
            <div className="w-6 h-6 rounded-full bg-blue-500 flex items-center justify-center">
              <svg className="w-3 h-3" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
                <path d="M12 2L2 7l10 5 10-5-10-5z"/><path d="M2 17l10 5 10-5"/><path d="M2 12l10 5 10-5"/>
              </svg>
            </div>
            <h3 className="font-bold text-sm tracking-wide">AI Executive Summary</h3>
          </div>
          <button
            onClick={generateSummary}
            disabled={loading}
            className="px-3 py-1.5 bg-blue-500 hover:bg-blue-400 disabled:opacity-50 text-white text-xs font-semibold rounded-full transition-all"
          >
            {loading ? 'Generating…' : generated ? 'Regenerate' : 'Generate Summary'}
          </button>
        </div>

        {!generated && (
          <p className="text-gray-500 text-sm">
            Click <span className="text-blue-400 font-medium">Generate Summary</span> to get an AI-powered analysis of your current week's performance.
          </p>
        )}

        {loading && (
          <div className="space-y-2 mt-2">
            {[80, 95, 70].map((w, i) => (
              <div key={i} className="h-3 bg-gray-700 rounded-full animate-pulse" style={{ width: `${w}%` }} />
            ))}
          </div>
        )}

        {summary && (
          <div className="text-gray-300 text-sm leading-relaxed space-y-3">
            {summary.split('\n\n').filter(Boolean).map((para, i) => (
              <p key={i}>{para}</p>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

// ─── Main Dashboard ───────────────────────────────────────────────────────────

export default function AnalyticsPage() {
  const [activeRange, setActiveRange] = useState('7d');

  const boroughColors = ['#3b82f6', '#8b5cf6', '#10b981', '#f59e0b', '#ef4444'];

  return (
    <div className="w-screen min-h-screen bg-gray-50 overflow-y-auto">
      <div className="max-w-3xl mx-auto px-4 py-6 pb-16">

        {/* Header */}
        <div className="mb-6 text-center">
          <h1 className="text-7xl font-black text-gray-500 tracking-tight mb-1">
            rush<span className="text-blue-400">hour</span>
          </h1>
          <p className="text-gray-400 text-sm tracking-widest uppercase">Analytics Dashboard</p>
        </div>

        {/* Date Range Tabs */}
        <div className="flex gap-2 mb-6 justify-center">
          {['7d', '30d', '90d'].map((r) => (
            <button
              key={r}
              onClick={() => setActiveRange(r)}
              className={`px-4 py-1.5 rounded-full text-sm font-semibold transition-all ${
                activeRange === r ? 'bg-blue-500 text-white shadow-sm' : 'bg-white text-gray-500 border border-gray-200 hover:bg-gray-50'
              }`}
            >
              {r === '7d' ? 'Last 7 Days' : r === '30d' ? 'Last 30 Days' : 'Last 90 Days'}
            </button>
          ))}
        </div>

        {/* KPI Cards */}
        <div className="grid grid-cols-2 gap-3 mb-6">
          {KPI_CARDS.map((kpi, i) => <KpiCard key={i} {...kpi} />)}
        </div>

        {/* AI Summary */}
        <div className="mb-6">
          <AISummaryPanel />
        </div>

        {/* AI Insights */}
        <div className="mb-6">
          <h2 className="text-xs font-semibold text-gray-400 uppercase tracking-widest mb-3">AI Insights</h2>
          <div className="space-y-3">
            {AI_INSIGHTS.map((ins) => <InsightCard key={ins.id} insight={ins} />)}
          </div>
        </div>

        {/* Hourly Demand */}
        <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-5 mb-6">
          <h2 className="text-sm font-semibold text-gray-800 mb-1">Hourly Demand Pattern</h2>
          <p className="text-xs text-gray-400 mb-4">Average ride requests by hour of day</p>
          <div className="flex items-end gap-0.5 h-28">
            {HOURLY_DEMAND.map((d, i) => {
              const max = Math.max(...HOURLY_DEMAND.map((x) => x.demand));
              const pct = (d.demand / max) * 100;
              const isPeak = d.demand >= 80;
              return (
                <div key={i} className="flex flex-col items-center flex-1 gap-0.5 group relative">
                  <div
                    className={`w-full rounded-t-sm transition-all duration-300 ${isPeak ? 'bg-blue-500' : 'bg-blue-200'}`}
                    style={{ height: `${pct}%` }}
                    title={`${d.hour}: ${d.demand}`}
                  />
                </div>
              );
            })}
          </div>
          <div className="flex justify-between mt-1">
            <span className="text-xs text-gray-400">12am</span>
            <span className="text-xs text-gray-400">6am</span>
            <span className="text-xs text-gray-400">12pm</span>
            <span className="text-xs text-gray-400">6pm</span>
            <span className="text-xs text-gray-400">11pm</span>
          </div>
        </div>

        {/* Weekly Rides + Revenue */}
        <div className="grid grid-cols-2 gap-3 mb-6">
          <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-4">
            <h2 className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-3">Rides by Day</h2>
            <div style={{ height: 100 }}>
              <BarChart data={WEEKLY_DEMAND} valueKey="rides" labelKey="day" color="#3b82f6" height={100} />
            </div>
          </div>
          <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-4">
            <h2 className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-3">Revenue ($) by Day</h2>
            <div style={{ height: 100 }}>
              <BarChart data={WEEKLY_DEMAND} valueKey="revenue" labelKey="day" color="#8b5cf6" height={100} />
            </div>
          </div>
        </div>

        {/* Monthly Revenue Trend */}
        <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-5 mb-6">
          <h2 className="text-sm font-semibold text-gray-800 mb-1">Revenue Trend</h2>
          <p className="text-xs text-gray-400 mb-4">Monthly gross revenue over the last 6 months</p>
          <LineChart data={MONTHLY_TREND} valueKey="revenue" labelKey="month" color="#3b82f6" height={110} />
        </div>

        {/* Borough Breakdown */}
        <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-5 mb-6">
          <h2 className="text-sm font-semibold text-gray-800 mb-1">Borough Breakdown</h2>
          <p className="text-xs text-gray-400 mb-4">Ride share % and week-on-week trend</p>
          <div className="flex items-center gap-6">
            <DonutChart
              segments={BOROUGH_BREAKDOWN.map((b, i) => ({ value: b.share, color: boroughColors[i] }))}
            />
            <div className="flex-1 space-y-2">
              {BOROUGH_BREAKDOWN.map((b, i) => (
                <div key={b.borough} className="flex items-center gap-2">
                  <div className="w-2.5 h-2.5 rounded-full flex-shrink-0" style={{ backgroundColor: boroughColors[i] }} />
                  <div className="flex-1">
                    <div className="flex justify-between items-center text-xs">
                      <span className="font-medium text-gray-700">{b.borough}</span>
                      <span className={`font-semibold ${b.trend >= 0 ? 'text-green-500' : 'text-red-400'}`}>
                        {b.trend >= 0 ? '+' : ''}{b.trend}%
                      </span>
                    </div>
                    <div className="w-full bg-gray-100 rounded-full h-1 mt-0.5">
                      <div className="h-1 rounded-full" style={{ width: `${b.share}%`, backgroundColor: boroughColors[i] }} />
                    </div>
                  </div>
                  <span className="text-xs text-gray-400 w-8 text-right">{b.share}%</span>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Event Impact */}
        <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-5">
          <h2 className="text-sm font-semibold text-gray-800 mb-1">Event Demand Lift</h2>
          <p className="text-xs text-gray-400 mb-4">Average % increase in rides during event windows</p>
          <div className="space-y-4">
            {EVENT_IMPACT.map((e) => (
              <div key={e.type}>
                <div className="flex justify-between items-center mb-1">
                  <div>
                    <span className="text-sm font-semibold text-gray-800">{e.type}</span>
                    <span className="text-xs text-gray-400 ml-2">· {e.events} events · Top: {e.topVenue}</span>
                  </div>
                  <span className="text-sm font-bold text-blue-500">+{e.avgLift}%</span>
                </div>
                <div className="w-full bg-gray-100 rounded-full h-2">
                  <div
                    className="h-2 rounded-full bg-blue-500 transition-all duration-700"
                    style={{ width: `${e.avgLift}%` }}
                  />
                </div>
              </div>
            ))}
          </div>
        </div>

      </div>
    </div>
  );
}
