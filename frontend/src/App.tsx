// frontend/src/App.tsx
import React, { useCallback, useMemo, useState } from 'react';
import HazardMap from './components/map/HazardMap';
import Sidebar from './components/sidebar/Sidebar';
import type { LatLngTuple } from './types/hazards';
import type { Places } from './types/places';
import { formatCoords } from './utils/format';

export const App: React.FC = () => {
  // GPS position, a place chosen from search, or a spot double-clicked on the map
  const [deviceLocation, setDeviceLocation] = useState<LatLngTuple | null>(null);
  const [selectedPlace, setSelectedPlace] = useState<Places | null>(null);
  const [pickedLocation, setPickedLocation] = useState<LatLngTuple | null>(null);
  const [pickCount, setPickCount] = useState(0);
  const [locationError, setLocationError] = useState<string | null>(null);

  const handleSelectPlace = useCallback((place: Places) => {
    setSelectedPlace(place);
    setPickedLocation(null);
  }, []);

  const handleMapPick = useCallback((coords: LatLngTuple) => {
    setPickedLocation(coords);
    setSelectedPlace(null);
    setPickCount((count) => count + 1);
  }, []);

  // The most recent explicit choice wins over GPS. Memoized so the sidebar's
  // risk-score fetch only reruns when the location actually changes.
  const activeLocation = useMemo<LatLngTuple | null>(() => {
    if (selectedPlace) return [selectedPlace.lat, selectedPlace.lon];
    return pickedLocation ?? deviceLocation;
  }, [selectedPlace, pickedLocation, deviceLocation]);

  let locationLabel: string | null = null;
  if (selectedPlace) locationLabel = selectedPlace.label ?? formatCoords([selectedPlace.lat, selectedPlace.lon]);
  else if (pickedLocation) locationLabel = formatCoords(pickedLocation);
  else if (deviceLocation) locationLabel = 'your current location';

  return (
    <main className="atlas-layout">
      <Sidebar
        location={activeLocation}
        locationLabel={locationLabel}
        locationError={locationError}
        onSelectPlace={handleSelectPlace}
        searchKey={pickCount}
        initialSearchText={pickedLocation ? formatCoords(pickedLocation) : ''}
      />
      <div className="atlas-map">
        <HazardMap
          deviceLocation={deviceLocation}
          selectedPlace={selectedPlace}
          pickedLocation={pickedLocation}
          onDeviceLocationFound={setDeviceLocation}
          onLocationError={setLocationError}
          onMapPick={handleMapPick}
        />
      </div>
    </main>
  );
};

export default App;
