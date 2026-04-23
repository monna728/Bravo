import { useState } from 'react';
import { predictDemand } from '../api/rushHourAPI';

const BOROUGHS = ['Manhattan', 'Brooklyn', 'Queens', 'Bronx', 'Staten Island'];
const TIME_OPTIONS = [
  { value: 'all',       label: 'All Day' },
  { value: 'morning',   label: 'Morning' },
  { value: 'afternoon', label: 'Afternoon' },
  { value: 'evening',   label: 'Evening' },
  { value: 'night',     label: 'Night' },
];

function todayISO() {
  return new Date().toISOString().split('T')[0];
}
function offsetISO(days) {
  const d = new Date();
  d.setDate(d.getDate() + days);
  return d.toISOString().split('T')[0];
}

/**
 * BoroughSearch — input panel for selecting borough, date range, and time of day.
 * Calls /predict and passes result to onResult callback.
 *
 * Props:
 *   onResult(result) — called with the full API response on success
 *   onError(msg)     — called with an error string on failure
 */
export default function BoroughSearch({ onResult, onError }) {
  const [borough, setBorough]     = useState('Manhattan');
  const [startDate, setStartDate] = useState(todayISO());
  const [endDate, setEndDate]     = useState(offsetISO(6));
  const [timeOfDay, setTimeOfDay] = useState('all');
  const [loading, setLoading]     = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!borough || !startDate || !endDate) return;
    setLoading(true);
    onError(null);
    try {
      const result = await predictDemand({ borough, startDate, endDate, timeOfDay });
      onResult(result);
    } catch (err) {
      onError(err.message || 'Prediction failed. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      {/* Borough selector */}
      <div>
        <label className="block text-xs font-semibold text-gray-500 uppercase tracking-widest mb-2">
          Borough
        </label>
        <div className="flex flex-wrap gap-2">
          {BOROUGHS.map((b) => (
            <button
              key={b}
              type="button"
              onClick={() => setBorough(b)}
              className={`px-3 py-1.5 rounded-full text-sm font-semibold transition-all border ${
                borough === b
                  ? 'bg-blue-500 text-white border-blue-500 shadow-sm'
                  : 'bg-white text-gray-600 border-gray-200 hover:border-blue-300 hover:text-blue-500'
              }`}
            >
              {b}
            </button>
          ))}
        </div>
      </div>

      {/* Date range */}
      <div className="grid grid-cols-2 gap-3">
        <div>
          <label className="block text-xs font-semibold text-gray-500 uppercase tracking-widest mb-1">
            From
          </label>
          <input
            type="date"
            value={startDate}
            onChange={(e) => setStartDate(e.target.value)}
            className="w-full border border-gray-200 rounded-xl px-3 py-2 text-sm text-gray-700 focus:outline-none focus:ring-2 focus:ring-blue-300"
            required
          />
        </div>
        <div>
          <label className="block text-xs font-semibold text-gray-500 uppercase tracking-widest mb-1">
            To
          </label>
          <input
            type="date"
            value={endDate}
            onChange={(e) => setEndDate(e.target.value)}
            min={startDate}
            className="w-full border border-gray-200 rounded-xl px-3 py-2 text-sm text-gray-700 focus:outline-none focus:ring-2 focus:ring-blue-300"
            required
          />
        </div>
      </div>

      {/* Time of day */}
      <div>
        <label className="block text-xs font-semibold text-gray-500 uppercase tracking-widest mb-2">
          Time of Day
        </label>
        <div className="flex flex-wrap gap-2">
          {TIME_OPTIONS.map((t) => (
            <button
              key={t.value}
              type="button"
              onClick={() => setTimeOfDay(t.value)}
              className={`px-3 py-1 rounded-full text-xs font-semibold transition-all border ${
                timeOfDay === t.value
                  ? 'bg-gray-800 text-white border-gray-800'
                  : 'bg-white text-gray-500 border-gray-200 hover:border-gray-400'
              }`}
            >
              {t.label}
            </button>
          ))}
        </div>
      </div>

      {/* Submit */}
      <button
        type="submit"
        disabled={loading}
        className="w-full py-3 bg-blue-500 hover:bg-blue-600 disabled:opacity-50 disabled:cursor-not-allowed text-white font-bold rounded-2xl transition-all text-sm shadow-sm"
      >
        {loading ? (
          <span className="flex items-center justify-center gap-2">
            <svg className="w-4 h-4 animate-spin" viewBox="0 0 24 24" fill="none">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z" />
            </svg>
            Analysing crowd signals…
          </span>
        ) : (
          'Get Prediction'
        )}
      </button>
    </form>
  );
}
