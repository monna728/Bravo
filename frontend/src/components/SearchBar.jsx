import { useState } from 'react';

export default function SearchBar({ locations, mapRef }) {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState([]);

  const handleSearch = (e) => {
    const val = e.target.value;
    setQuery(val);
    if (!val.trim()) return setResults([]);
    setResults(
      locations.filter((l) =>
        l.name.toLowerCase().includes(val.toLowerCase())
      )
    );
  };

  const handleSelect = (loc) => {
    mapRef?.panTo(loc.position);
    mapRef?.setZoom(15);
    setQuery(loc.name);
    setResults([]);
  };

  return (
    <div className="absolute top-4 left-1/2 -translate-x-1/2 z-10 w-80">
      <input
        type="text"
        value={query}
        onChange={handleSearch}
        placeholder="Search locations..."
        className="w-full px-4 py-2 rounded-full shadow-lg border border-gray-200 bg-white text-sm focus:outline-none focus:ring-2 focus:ring-blue-400"
      />
      {results.length > 0 && (
        <ul className="mt-1 bg-white rounded-xl shadow-lg border border-gray-100 overflow-hidden">
          {results.map((loc) => (
            <li
              key={loc.id}
              onClick={() => handleSelect(loc)}
              className="px-4 py-2 hover:bg-gray-50 cursor-pointer text-sm text-gray-700"
            >
              {loc.name}
              <span className="text-gray-400 text-xs ml-2">{loc.borough}</span>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}