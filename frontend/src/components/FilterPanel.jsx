const TYPES = ['all', 'concert', 'sports', 'festival'];
const BOROUGHS = ['all', 'Manhattan', 'Brooklyn', 'Queens', 'Bronx', 'Staten Island'];

export default function FilterPanel({ filters, setFilters }) {
  return (
    <div className="absolute top-4 right-4 z-10 bg-white rounded-2xl shadow-lg p-4 w-52 space-y-4">
      <h2 className="font-semibold text-gray-800 text-sm">Filters</h2>

      {/* Event Type */}
      <div>
        <label className="text-xs text-gray-500 uppercase tracking-wide">Event Type</label>
        <select
          value={filters.type}
          onChange={(e) => setFilters({ ...filters, type: e.target.value })}
          className="mt-1 w-full text-sm border border-gray-200 rounded-lg px-2 py-1.5 focus:outline-none focus:ring-2 focus:ring-blue-400"
        >
          {TYPES.map((t) => (
            <option key={t} value={t}>{t.charAt(0).toUpperCase() + t.slice(1)}</option>
          ))}
        </select>
      </div>

      {/* Borough */}
      <div>
        <label className="text-xs text-gray-500 uppercase tracking-wide">Borough</label>
        <select
          value={filters.borough}
          onChange={(e) => setFilters({ ...filters, borough: e.target.value })}
          className="mt-1 w-full text-sm border border-gray-200 rounded-lg px-2 py-1.5 focus:outline-none focus:ring-2 focus:ring-blue-400"
        >
          {BOROUGHS.map((b) => (
            <option key={b} value={b}>{b.charAt(0).toUpperCase() + b.slice(1)}</option>
          ))}
        </select>
      </div>

      {/* Date */}
      <div>
        <label className="text-xs text-gray-500 uppercase tracking-wide">Date</label>
        <input
          type="date"
          value={filters.date}
          onChange={(e) => setFilters({ ...filters, date: e.target.value })}
          className="mt-1 w-full text-sm border border-gray-200 rounded-lg px-2 py-1.5 focus:outline-none focus:ring-2 focus:ring-blue-400"
        />
      </div>
    </div>
  );
}