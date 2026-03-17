import { useState } from 'react';

const TYPES = ['all', 'concert', 'sports', 'festival'];

const timeLabel = (h) => {
  const suffix = h >= 12 ? 'pm' : 'am';
  const hour = h % 12 === 0 ? 12 : h % 12;
  return `${hour}${suffix}`;
};

export default function FilterPanel({ filters, setFilters }) {
  return (
    <div className="absolute top-4 right-4 z-10 bg-white rounded-2xl shadow-lg p-4 w-56 space-y-4">
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

      {/* Date Range */}
      <div>
        <label className="text-xs text-gray-500 uppercase tracking-wide">Date Range</label>
        <input
          type="date"
          value={filters.startDate}
          onChange={(e) => setFilters({ ...filters, startDate: e.target.value })}
          className="mt-1 w-full text-sm border border-gray-200 rounded-lg px-2 py-1.5 focus:outline-none focus:ring-2 focus:ring-blue-400"
        />
        <input
          type="date"
          value={filters.endDate}
          onChange={(e) => setFilters({ ...filters, endDate: e.target.value })}
          className="mt-2 w-full text-sm border border-gray-200 rounded-lg px-2 py-1.5 focus:outline-none focus:ring-2 focus:ring-blue-400"
        />
      </div>

      {/* Time Scrubber */}
      <div>
        <label className="text-xs text-gray-500 uppercase tracking-wide">
          Time Range:{' '}
          <span className="text-blue-500 normal-case font-medium">
            {timeLabel(filters.timeRange[0])} – {timeLabel(filters.timeRange[1])}
          </span>
        </label>
        <div className="mt-2 space-y-1">
          <div className="flex items-center gap-2">
            <span className="text-xs text-gray-400 w-6">From</span>
            <input
              type="range"
              min={0} max={24}
              value={filters.timeRange[0]}
              onChange={(e) => setFilters({
                ...filters,
                timeRange: [Math.min(Number(e.target.value), filters.timeRange[1] - 1), filters.timeRange[1]]
              })}
              className="flex-1 accent-blue-500"
            />
          </div>
          <div className="flex items-center gap-2">
            <span className="text-xs text-gray-400 w-6">To</span>
            <input
              type="range"
              min={0} max={24}
              value={filters.timeRange[1]}
              onChange={(e) => setFilters({
                ...filters,
                timeRange: [filters.timeRange[0], Math.max(Number(e.target.value), filters.timeRange[0] + 1)]
              })}
              className="flex-1 accent-blue-500"
            />
          </div>
        </div>
      </div>
    </div>
  );
}