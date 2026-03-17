import { useState, useMemo } from 'react';
import Map from '../components/Map';
import { LOCATIONS, BOROUGHS, EVENT_TYPES, TYPE_COLORS, TYPE_TEXT_COLORS, TYPE_BG_LIGHT } from '../data/locations';

const DEMAND_BAR_COLOR = (score) =>
  score >= 70 ? 'bg-red-500' : score >= 40 ? 'bg-yellow-400' : 'bg-green-400';

export default function ListPage() {
  const [selectedBorough, setSelectedBorough] = useState('');
  const [selectedType, setSelectedType] = useState('');
  const [startDate, setStartDate] = useState('');
  const [endDate, setEndDate] = useState('');
  const [timeRange, setTimeRange] = useState([0, 24]);

  const timeLabel = (h) => {
    const suffix = h >= 12 ? 'pm' : 'am';
    const hour = h % 12 === 0 ? 12 : h % 12;
    return `${hour}${suffix}`;
  };

  const filtered = useMemo(() => {
    return LOCATIONS.filter((loc) => {
      if (selectedType && loc.type !== selectedType) return false;
      const hour = parseInt(loc.time.split(':')[0]);
      if (hour < timeRange[0] || hour > timeRange[1]) return false;
      return true;
    });
  }, [selectedType, timeRange]);

  // Borough view — rank boroughs by avg demand score
  const boroughRankings = useMemo(() => {
    return BOROUGHS.map((borough) => {
      const locs = filtered.filter((l) => l.borough === borough);
      const avgScore = locs.length
        ? Math.round(locs.reduce((sum, l) => sum + l.demandScore, 0) / locs.length)
        : 0;
      const types = [...new Set(locs.map((l) => l.type))];
      return { borough, avgScore, types, count: locs.length };
    }).sort((a, b) => b.avgScore - a.avgScore);
  }, [filtered]);

  // Location view — rank locations within selected borough
  const locationRankings = useMemo(() => {
    return filtered
      .filter((l) => l.borough === selectedBorough)
      .sort((a, b) => b.demandScore - a.demandScore);
  }, [filtered, selectedBorough]);

  return (
    <div className="w-screen h-screen bg-gray-50 overflow-y-auto">
      <div className="max-w-2xl mx-auto px-4 py-6">

        {/* Header */}
        <div className="mb-6 pl-24">
          <h1 className="text-2xl font-bold text-gray-900">RushHour</h1>
          <p className="text-gray-500 text-sm mt-1">Browse and filter NYC taxi demand by event and location</p>
        </div>

        {/* Filters */}
        <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-4 mb-6 space-y-4">

          {/* Date range */}
          <div>
            <label className="text-xs font-semibold text-gray-500 uppercase tracking-wide">Date Range</label>
            <div className="flex gap-2 mt-1">
              <input
                type="date"
                value={startDate}
                onChange={(e) => setStartDate(e.target.value)}
                className="flex-1 text-sm border border-gray-200 rounded-lg px-3 py-1.5 focus:outline-none focus:ring-2 focus:ring-blue-400"
              />
              <span className="text-gray-400 self-center text-sm">to</span>
              <input
                type="date"
                value={endDate}
                onChange={(e) => setEndDate(e.target.value)}
                className="flex-1 text-sm border border-gray-200 rounded-lg px-3 py-1.5 focus:outline-none focus:ring-2 focus:ring-blue-400"
              />
            </div>
          </div>

          {/* Time scrubber */}
          <div>
            <label className="text-xs font-semibold text-gray-500 uppercase tracking-wide">
              Time Range: <span className="text-blue-500 normal-case font-medium">{timeLabel(timeRange[0])} – {timeLabel(timeRange[1])}</span>
            </label>
            <div className="flex gap-3 mt-2 items-center">
              <span className="text-xs text-gray-400">12am</span>
              <input
                type="range"
                min={0} max={24} value={timeRange[0]}
                onChange={(e) => setTimeRange([Math.min(Number(e.target.value), timeRange[1] - 1), timeRange[1]])}
                className="flex-1 accent-blue-500"
              />
              <input
                type="range"
                min={0} max={24} value={timeRange[1]}
                onChange={(e) => setTimeRange([timeRange[0], Math.max(Number(e.target.value), timeRange[0] + 1)])}
                className="flex-1 accent-blue-500"
              />
              <span className="text-xs text-gray-400">12am</span>
            </div>
          </div>

          {/* Event type */}
          <div>
            <label className="text-xs font-semibold text-gray-500 uppercase tracking-wide">Event Type</label>
            <div className="flex gap-2 mt-1 flex-wrap">
              <button
                onClick={() => setSelectedType('')}
                className={`px-3 py-1 rounded-full text-sm font-medium transition-all ${!selectedType ? 'bg-blue-500 text-white' : 'bg-gray-100 text-gray-600 hover:bg-gray-200'}`}
              >
                All
              </button>
              {EVENT_TYPES.map((t) => (
                <button
                  key={t}
                  onClick={() => setSelectedType(t === selectedType ? '' : t)}
                  className={`px-3 py-1 rounded-full text-sm font-medium capitalize transition-all ${
                    selectedType === t
                      ? `${TYPE_COLORS[t]} text-white`
                      : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                  }`}
                >
                  {t}
                </button>
              ))}
            </div>
          </div>

          {/* Borough */}
          <div>
            <label className="text-xs font-semibold text-gray-500 uppercase tracking-wide">Borough</label>
            <div className="flex gap-2 mt-1 flex-wrap">
              <button
                onClick={() => setSelectedBorough('')}
                className={`px-3 py-1 rounded-full text-sm font-medium transition-all ${!selectedBorough ? 'bg-blue-500 text-white' : 'bg-gray-100 text-gray-600 hover:bg-gray-200'}`}
              >
                All
              </button>
              {BOROUGHS.map((b) => (
                <button
                  key={b}
                  onClick={() => setSelectedBorough(b === selectedBorough ? '' : b)}
                  className={`px-3 py-1 rounded-full text-sm font-medium transition-all ${
                    selectedBorough === b
                      ? 'bg-blue-500 text-white'
                      : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                  }`}
                >
                  {b}
                </button>
              ))}
            </div>
          </div>
        </div>

        {/* Results */}
        {!selectedBorough ? (
          <>
            <h2 className="text-sm font-semibold text-gray-500 uppercase tracking-wide mb-3">Top Boroughs by Demand</h2>
            <div className="space-y-3">
              {boroughRankings.map((item, i) => (
                <button
                  key={item.borough}
                  onClick={() => setSelectedBorough(item.borough)}
                  className="w-full bg-white rounded-2xl shadow-sm border border-gray-100 p-4 flex items-center gap-4 hover:border-blue-300 hover:shadow-md transition-all text-left"
                >
                  {/* Rank */}
                  <span className="text-2xl font-bold text-gray-200 w-8">#{i + 1}</span>

                  {/* Info */}
                  <div className="flex-1">
                    <div className="flex items-center justify-between mb-1">
                      <h3 className="font-semibold text-gray-900">{item.borough}</h3>
                      <span className="text-sm font-bold text-gray-900">{item.avgScore}<span className="text-gray-400 font-normal text-xs">/100</span></span>
                    </div>
                    <div className="w-full bg-gray-100 rounded-full h-1.5 mb-2">
                      <div className={`h-1.5 rounded-full ${DEMAND_BAR_COLOR(item.avgScore)}`} style={{ width: `${item.avgScore}%` }} />
                    </div>
                    <div className="flex gap-1 flex-wrap">
                      {item.types.map((t) => (
                        <span key={t} className={`text-xs px-2 py-0.5 rounded-full capitalize font-medium ${TYPE_TEXT_COLORS[t]} ${TYPE_BG_LIGHT[t]}`}>{t}</span>
                      ))}
                      <span className="text-xs text-gray-400 ml-1">{item.count} event{item.count !== 1 ? 's' : ''}</span>
                    </div>
                  </div>

                  <svg xmlns="http://www.w3.org/2000/svg" className="w-4 h-4 text-gray-300" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><polyline points="9 18 15 12 9 6"/></svg>
                </button>
              ))}
            </div>
          </>
        ) : (
          <>
            <div className="flex items-center gap-2 mb-3">
              <button onClick={() => setSelectedBorough('')} className="text-blue-500 text-sm hover:underline">← All Boroughs</button>
              <span className="text-gray-300">/</span>
              <h2 className="text-sm font-semibold text-gray-800">{selectedBorough}</h2>
            </div>

            {locationRankings.length === 0 ? (
              <div className="bg-white rounded-2xl p-8 text-center text-gray-400 border border-gray-100">
                No locations match your filters.
              </div>
            ) : (
              <div className="space-y-3">
                {locationRankings.map((loc, i) => (
                  <div key={loc.id} className="bg-white rounded-2xl shadow-sm border border-gray-100 p-4 flex items-center gap-4">
                    <span className="text-2xl font-bold text-gray-200 w-8">#{i + 1}</span>
                    <div className="flex-1">
                      <div className="flex items-center justify-between mb-0.5">
                        <h3 className="font-semibold text-gray-900">{loc.name}</h3>
                        <span className="text-sm font-bold text-gray-900">{loc.demandScore}<span className="text-gray-400 font-normal text-xs">/100</span></span>
                      </div>
                      <p className="text-xs text-gray-500 mb-2">{loc.eventName} · {loc.time}</p>
                      <div className="w-full bg-gray-100 rounded-full h-1.5 mb-2">
                        <div className={`h-1.5 rounded-full ${DEMAND_BAR_COLOR(loc.demandScore)}`} style={{ width: `${loc.demandScore}%` }} />
                      </div>
                      <span className={`text-xs px-2 py-0.5 rounded-full capitalize font-medium ${TYPE_TEXT_COLORS[loc.type]} ${TYPE_BG_LIGHT[loc.type]}`}>{loc.type}</span>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
}