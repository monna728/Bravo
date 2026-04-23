import { useState, useEffect, useRef } from 'react';
import { RANGE_DATA } from '../data/analyticsData';
import BoroughSearch from '../components/BoroughSearch';
import PredictionResult from '../components/PredictionResult';

// ─── Chart components (pure SVG / CSS, no extra deps) ────────────────────────

function BarChart({ data, valueKey, labelKey, color = '#3b82f6', height = 100 }) {
  const max = Math.max(...data.map((d) => d[valueKey]));
  return (
    <div className="flex items-end gap-1" style={{ height }}>
      {data.map((d, i) => {
        const pct = (d[valueKey] / max) * 100;
        return (
          <div key={i} className="flex flex-col items-center flex-1 gap-1 h-full justify-end">
            <div
              className="w-full rounded-t-sm transition-all duration-700"
              style={{ height: `${pct}%`, backgroundColor: color, opacity: 0.85 }}
              title={`${d[labelKey]}: ${d[valueKey].toLocaleString()}`}
            />
            <span className="text-gray-500 text-xs leading-none">{d[labelKey]}</span>
          </div>
        );
      })}
    </div>
  );
}

function LineChart({ data, valueKey, labelKey, color = '#3b82f6', height = 110 }) {
  const vals = data.map((d) => d[valueKey]);
  const max = Math.max(...vals);
  const min = Math.min(...vals);
  const range = max - min || 1;
  const W = 400; const H = height - 16;
  const pts = vals.map((v, i) => {
    const x = vals.length === 1 ? W / 2 : (i / (vals.length - 1)) * W;
    const y = H - ((v - min) / range) * (H - 8) - 4;
    return `${x},${y}`;
  }).join(' ');
  const area = `0,${H} ${pts} ${W},${H}`;
  return (
    <div className="relative w-full" style={{ height }}>
      <svg viewBox={`0 0 ${W} ${H}`} preserveAspectRatio="none" className="absolute inset-0 w-full" style={{ height: H }}>
        <defs>
          <linearGradient id="lg" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor={color} stopOpacity="0.22" />
            <stop offset="100%" stopColor={color} stopOpacity="0" />
          </linearGradient>
        </defs>
        <polygon points={area} fill="url(#lg)" />
        <polyline points={pts} fill="none" stroke={color} strokeWidth="2.5" strokeLinejoin="round" />
      </svg>
      <div className="absolute bottom-0 left-0 right-0 flex justify-between">
        {data.map((d, i) => <span key={i} className="text-xs text-gray-400">{d[labelKey]}</span>)}
      </div>
    </div>
  );
}

function DonutChart({ segments }) {
  const total = segments.reduce((s, x) => s + x.value, 0);
  let cum = -90;
  const r = 40; const cx = 50; const cy = 50;
  const xy = (deg, rad) => ({ x: cx + rad * Math.cos((deg * Math.PI) / 180), y: cy + rad * Math.sin((deg * Math.PI) / 180) });
  return (
    <svg viewBox="0 0 100 100" className="w-24 h-24 flex-shrink-0">
      {segments.map((seg, i) => {
        const angle = (seg.value / total) * 360;
        const s = xy(cum, r); const e = xy(cum + angle, r);
        const d = `M ${cx} ${cy} L ${s.x} ${s.y} A ${r} ${r} 0 ${angle > 180 ? 1 : 0} 1 ${e.x} ${e.y} Z`;
        cum += angle;
        return <path key={i} d={d} fill={seg.color} opacity="0.85" />;
      })}
      <circle cx={cx} cy={cy} r={24} fill="white" />
    </svg>
  );
}

// ─── KPI Card ─────────────────────────────────────────────────────────────────

function KpiCard({ label, value, change, compareLabel }) {
  const pos = change >= 0;
  return (
    <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-4 flex flex-col gap-1.5">
      <span className="text-xs font-semibold text-gray-400 uppercase tracking-wide">{label}</span>
      <span className="text-2xl font-black text-gray-900">{value}</span>
      <span className={`text-xs font-semibold flex items-center gap-1 ${pos ? 'text-green-500' : 'text-red-400'}`}>
        {pos ? '▲' : '▼'} {Math.abs(change)}% {compareLabel}
      </span>
    </div>
  );
}

// ─── Insight Card ─────────────────────────────────────────────────────────────

function InsightCard({ insight }) {
  const styles = {
    opportunity: { wrap: 'bg-blue-50 border-blue-200', title: 'text-blue-700' },
    warning:     { wrap: 'bg-amber-50 border-amber-200', title: 'text-amber-700' },
    info:        { wrap: 'bg-gray-50 border-gray-200', title: 'text-gray-700' },
  }[insight.type];
  return (
    <div className={`rounded-2xl border p-4 ${styles.wrap}`}>
      <div className="flex items-start gap-3">
        <span className="text-xl">{insight.icon}</span>
        <div>
          <h4 className={`font-semibold text-sm mb-1 ${styles.title}`}>{insight.title}</h4>
          <p className="text-xs text-gray-600 leading-relaxed">{insight.body}</p>
        </div>
      </div>
    </div>
  );
}

// ─── AI Summary Panel ─────────────────────────────

function AISummaryPanel({ summaryText, range }) {
  const [displayed, setDisplayed] = useState('');
  const [phase, setPhase]   = useState('idle'); // idle | thinking | streaming | done
  const intervalRef = useRef(null);
  const prevRange   = useRef(range);

  // Reset when range changes (if already generated)
  useEffect(() => {
    if (prevRange.current !== range) {
      prevRange.current = range;
      setDisplayed('');
      setPhase('idle');
      if (intervalRef.current) clearInterval(intervalRef.current);
    }
  }, [range]);

  const generate = () => {
    if (intervalRef.current) clearInterval(intervalRef.current);
    setDisplayed('');
    setPhase('thinking');

    setTimeout(() => {
      setPhase('streaming');
      const words = summaryText.split(' ');
      let i = 0;
      intervalRef.current = setInterval(() => {
        i++;
        setDisplayed(words.slice(0, i).join(' '));
        if (i >= words.length) {
          clearInterval(intervalRef.current);
          setPhase('done');
        }
      }, 28);
    }, 1400);
  };

  const isDone      = phase === 'done';
  const isStreaming = phase === 'streaming';
  const isThinking  = phase === 'thinking';
  const hasContent  = displayed.length > 0;

  return (
    <div className="bg-gray-900 rounded-2xl p-5 text-white relative overflow-hidden">
      <div className="absolute top-0 right-0 w-40 h-40 bg-blue-500 rounded-full opacity-10 blur-3xl pointer-events-none" />
      <div className="relative z-10">
        {/* Header */}
        <div className="flex items-center justify-between mb-3">
          <div className="flex items-center gap-2">
            <div className="w-6 h-6 rounded-full bg-blue-500 flex items-center justify-center">
              <svg className="w-3 h-3" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
                <path d="M12 2L2 7l10 5 10-5-10-5z"/><path d="M2 17l10 5 10-5"/><path d="M2 12l10 5 10-5"/>
              </svg>
            </div>
            <h3 className="font-bold text-sm tracking-wide">AI Executive Summary</h3>
            {(isThinking || isStreaming) && (
              <span className="text-xs text-blue-400 animate-pulse">● generating</span>
            )}
          </div>
          <button
            onClick={generate}
            disabled={isThinking || isStreaming}
            className="px-3 py-1.5 bg-blue-500 hover:bg-blue-400 disabled:opacity-40 disabled:cursor-not-allowed text-white text-xs font-semibold rounded-full transition-all"
          >
            {isThinking || isStreaming ? 'Generating…' : isDone ? 'Regenerate' : 'Generate Summary'}
          </button>
        </div>

        {/* Idle state */}
        {phase === 'idle' && (
          <p className="text-gray-500 text-sm">
            Click <span className="text-blue-400 font-medium">Generate Summary</span> for an AI-powered executive analysis of this period.
          </p>
        )}

        {/* Thinking skeleton */}
        {isThinking && (
          <div className="space-y-2">
            {[88, 96, 72, 96, 80, 64].map((w, i) => (
              <div key={i} className="h-2.5 bg-gray-700 rounded-full animate-pulse" style={{ width: `${w}%`, animationDelay: `${i * 80}ms` }} />
            ))}
          </div>
        )}

        {/* Streaming / done text */}
        {hasContent && (
          <div className="text-gray-300 text-sm leading-relaxed space-y-3">
            {displayed.split('\\n\\n').filter(Boolean).map((para, i) => (
              <p key={i}>
                {para}
                {/* blinking cursor on last paragraph while streaming */}
                {isStreaming && i === displayed.split('\\n\\n').filter(Boolean).length - 1 && (
                  <span className="inline-block w-0.5 h-3.5 bg-blue-400 ml-0.5 align-middle animate-pulse" />
                )}
              </p>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

// ─── Main Dashboard ───────────────────────────────────────────────────────────

const BOROUGH_COLORS = ['#3b82f6', '#8b5cf6', '#10b981', '#f59e0b', '#ef4444'];

export default function AnalyticsPage() {
  const [range, setRange] = useState('7d');
  const d = RANGE_DATA[range];
  const [predResult, setPredResult] = useState(null);
  const [predError, setPredError]   = useState(null);

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

        {/* Range tabs */}
        <div className="flex gap-2 mb-6 justify-center">
          {['7d', '30d', '90d'].map((r) => (
            <button
              key={r}
              onClick={() => setRange(r)}
              className={`px-4 py-1.5 rounded-full text-sm font-semibold transition-all ${
                range === r
                  ? 'bg-blue-500 text-white shadow-sm'
                  : 'bg-white text-gray-500 border border-gray-200 hover:bg-gray-50'
              }`}
            >
              {RANGE_DATA[r].label}
            </button>
          ))}
        </div>

        {/* KPI Cards */}
        <div className="grid grid-cols-2 gap-3 mb-6">
          {d.kpis.map((kpi, i) => (
            <KpiCard key={`${range}-${i}`} {...kpi} compareLabel={d.compareLabel} />
          ))}
        </div>

        {/* AI Summary */}
        <div className="mb-6">
          <AISummaryPanel summaryText={d.aiSummary} range={range} />
        </div>

        {/* AI Insights */}
        <div className="mb-6">
          <h2 className="text-xs font-semibold text-gray-400 uppercase tracking-widest mb-3">AI Insights</h2>
          <div className="space-y-3">
            {d.insights.map((ins) => <InsightCard key={`${range}-${ins.id}`} insight={ins} />)}
          </div>
        </div>

        {/* Hourly demand */}
        <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-5 mb-6">
          <h2 className="text-sm font-semibold text-gray-800 mb-1">Hourly Demand Pattern</h2>
          <p className="text-xs text-gray-400 mb-4">Average ride requests by hour of day</p>
          <div className="flex items-end gap-0.5 h-28">
            {d.hourly.map((val, i) => {
              const max = Math.max(...d.hourly);
              const pct = (val / max) * 100;
              return (
                <div key={i} className="flex-1 flex flex-col items-center justify-end h-full gap-0.5">
                  <div
                    className={`w-full rounded-t-sm transition-all duration-500 ${pct >= 84 ? 'bg-blue-500' : 'bg-blue-200'}`}
                    style={{ height: `${pct}%` }}
                  />
                </div>
              );
            })}
          </div>
          <div className="flex justify-between mt-1">
            {['12am','6am','12pm','6pm','11pm'].map((l) => (
              <span key={l} className="text-xs text-gray-400">{l}</span>
            ))}
          </div>
        </div>

        {/* Bar charts — rides & revenue */}
        <div className="grid grid-cols-2 gap-3 mb-6">
          <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-4">
            <h2 className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-3">
              {d.barChart.title}
            </h2>
            <BarChart data={d.barChart.data} valueKey="rides" labelKey="label" color="#3b82f6" height={100} />
          </div>
          <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-4">
            <h2 className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-3">
              Revenue ($)
            </h2>
            <BarChart data={d.barChart.data} valueKey="revenue" labelKey="label" color="#8b5cf6" height={100} />
          </div>
        </div>

        {/* Revenue trend line */}
        <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-5 mb-6">
          <h2 className="text-sm font-semibold text-gray-800 mb-1">{d.trendChart.title}</h2>
          <p className="text-xs text-gray-400 mb-4">{d.trendChart.subtitle}</p>
          <LineChart data={d.trendChart.data} valueKey="value" labelKey="label" color="#3b82f6" height={110} />
        </div>

        {/* Borough breakdown */}
        <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-5 mb-6">
          <h2 className="text-sm font-semibold text-gray-800 mb-1">Borough Breakdown</h2>
          <p className="text-xs text-gray-400 mb-4">Ride share % and period trend</p>
          <div className="flex items-center gap-6">
            <DonutChart segments={d.boroughs.map((b, i) => ({ value: b.share, color: BOROUGH_COLORS[i] }))} />
            <div className="flex-1 space-y-2">
              {d.boroughs.map((b, i) => (
                <div key={b.borough} className="flex items-center gap-2">
                  <div className="w-2.5 h-2.5 rounded-full flex-shrink-0" style={{ backgroundColor: BOROUGH_COLORS[i] }} />
                  <div className="flex-1">
                    <div className="flex justify-between items-center text-xs">
                      <span className="font-medium text-gray-700">{b.borough}</span>
                      <span className={`font-semibold ${b.trend >= 0 ? 'text-green-500' : 'text-red-400'}`}>
                        {b.trend >= 0 ? '+' : ''}{b.trend}%
                      </span>
                    </div>
                    <div className="w-full bg-gray-100 rounded-full h-1 mt-0.5">
                      <div className="h-1 rounded-full transition-all duration-500" style={{ width: `${b.share}%`, backgroundColor: BOROUGH_COLORS[i] }} />
                    </div>
                  </div>
                  <span className="text-xs text-gray-400 w-8 text-right">{b.share}%</span>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* ── Live Demand Forecast ──────────────────────────────────────── */}
        <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-5 mb-6">
          <h2 className="text-sm font-semibold text-gray-800 mb-1">Live Demand Forecast</h2>
          <p className="text-xs text-gray-400 mb-4">
            Predict crowd demand for any borough and date range using the RushHour analytical model.
          </p>
          <BoroughSearch
            onResult={(r) => { setPredResult(r); setPredError(null); }}
            onError={(msg) => { setPredError(msg); setPredResult(null); }}
          />
          {predError && (
            <div className="mt-4 bg-red-50 border border-red-200 rounded-xl px-4 py-3 text-sm text-red-600">
              {predError}
            </div>
          )}
          <PredictionResult result={predResult} />
        </div>

        {/* Event demand lift */}
        <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-5">
          <h2 className="text-sm font-semibold text-gray-800 mb-1">Event Demand Lift</h2>
          <p className="text-xs text-gray-400 mb-4">Average % increase in rides during event windows</p>
          <div className="space-y-4">
            {d.events.map((e) => (
              <div key={e.type}>
                <div className="flex justify-between items-center mb-1">
                  <div>
                    <span className="text-sm font-semibold text-gray-800">{e.type}</span>
                    <span className="text-xs text-gray-400 ml-2">· {e.count} events · Top: {e.topVenue}</span>
                  </div>
                  <span className="text-sm font-bold text-blue-500">+{e.avgLift}%</span>
                </div>
                <div className="w-full bg-gray-100 rounded-full h-2">
                  <div className="h-2 rounded-full bg-blue-500 transition-all duration-700" style={{ width: `${e.avgLift}%` }} />
                </div>
              </div>
            ))}
          </div>
        </div>

      </div>
    </div>
  );
}
