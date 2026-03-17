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
  const [filters, setFilters] = useState({ type: 'all', borough: 'all', date: '' });
  const [mapRef, setMapRef] = useState(null);

  const onLoad = useCallback((map) => setMapRef(map), []);

  const filteredLocations = LOCATIONS.filter((loc) => {
    if (filters.type !== 'all' && loc.type !== filters.type) return false;
    if (filters.borough !== 'all' && loc.borough !== filters.borough) return false;
    return true;
  });

  if (!isLoaded) return (
    <div className="w-screen h-screen flex items-center justify-center bg-gray-900 text-white text-xl">
      Loading map...
    </div>
  );

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
              <div className={`w-4 h-4 rounded-full border-2 border-white shadow-lg cursor-pointer transition-transform hover:scale-150 ${TYPE_COLORS[loc.type] || 'bg-gray-500'}`} />

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