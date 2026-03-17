import { useState, useCallback } from 'react';
import { GoogleMap, useJsApiLoader, OverlayView } from '@react-google-maps/api';
import InfoCard from './InfoCard';
import FilterPanel from './FilterPanel';
import SearchBar from './SearchBar';
import Legend from './Legend';
import { LOCATIONS, TYPE_COLORS } from '../data/locations';

const NYC_CENTER = { lat: 40.7549, lng: -73.9840 };

const MAP_STYLES = [
  { featureType: 'poi', elementType: 'labels', stylers: [{ visibility: 'off' }] },
];

export default function Map() {
  const { isLoaded } = useJsApiLoader({
    googleMapsApiKey: process.env.REACT_APP_GOOGLE_MAPS_API_KEY,
  });

  const [hoveredLocation, setHoveredLocation] = useState(null);
  const [filters, setFilters] = useState({
    type: 'all',
    startDate: '',
    endDate: '',
    timeRange: [0, 24],
  });
  const [mapRef, setMapRef] = useState(null);

  const onLoad = useCallback((map) => setMapRef(map), []);

  const filteredLocations = LOCATIONS.filter((loc) => {
    if (filters.type !== 'all' && loc.type !== filters.type) return false;
    if (filters.startDate && loc.date < filters.startDate) return false;
    if (filters.endDate && loc.date > filters.endDate) return false;
    const hour = parseInt(loc.time.split(':')[0]);
    if (hour < filters.timeRange[0] || hour > filters.timeRange[1]) return false;
    return true;
  });

  if (!isLoaded) return (
    <div className="w-screen h-screen flex items-center justify-center bg-gray-900 text-white text-xl">
      Loading map...
    </div>
  );

  const getDemandColor = (score) => {
    if (score >= 80) return '#ef4444'; // red
    if (score >= 60) return '#f97316'; // orange
    if (score >= 40) return '#facc15'; // yellow
    if (score >= 20) return '#a3e635'; // lime
    return '#4ade80';                  // green
  };

  const getMarkerSize = (score) => {
    if (score >= 80) return 'w-6 h-6';
    if (score >= 60) return 'w-5 h-5';
    if (score >= 40) return 'w-4 h-4';
    return 'w-3 h-3';
  };

  return (
    <div className="relative w-screen h-screen">
      {/* Map */}
      <GoogleMap
        mapContainerClassName="w-full h-full"
        center={NYC_CENTER}
        zoom={12}
        onLoad={onLoad}
        options={{
          styles: MAP_STYLES,
          disableDefaultUI: true,
          zoomControl: true,
        }}
      >
        {/* Location Markers */}
        {filteredLocations.map((loc) => (
          <OverlayView
            key={loc.id}
            position={loc.position}
            mapPaneName={OverlayView.OVERLAY_MOUSE_TARGET}
          >
            <div
              className="relative"
              onMouseEnter={() => setHoveredLocation(loc)}
              onMouseLeave={() => setHoveredLocation(null)}
            >
              {/* Marker dot */}
              <div
                className={`${getMarkerSize(loc.demandScore)} rounded-full border-2 border-white shadow-lg cursor-pointer transition-transform hover:scale-150`}
                style={{ backgroundColor: getDemandColor(loc.demandScore) }}
              />

              {/* Info card on hover */}
              {hoveredLocation?.id === loc.id && (
                <div className="absolute z-50 bottom-6 left-1/2 -translate-x-1/2">
                  <InfoCard location={loc} />
                </div>
              )}
            </div>
          </OverlayView>
        ))}
      </GoogleMap>

      {/* Floating UI */}
      <SearchBar locations={LOCATIONS} mapRef={mapRef} />
      <FilterPanel filters={filters} setFilters={setFilters} />
      <Legend />
    </div>
  );
}