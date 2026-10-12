 // frontend/src/App.tsx
import React, { useState } from 'react';
import HazardMap from './components/map/HazardMap';
import RiskIndicators from './components/panels/RiskIndicators';
import type { LatLngTuple } from './types/hazards';

export const App: React.FC = () => {
  const [userLocation, setUserLocation] = useState<LatLngTuple | null>(null);
  const [locationError, setLocationError] = useState<string | null>(null);

  return (
    <main style={{ margin: 0, padding: 0, height: '100%', width: '100%', overflow: 'hidden' }}>
      <HazardMap onUserLocationChange={setUserLocation} onLocationError={setLocationError} />
      <RiskIndicators userLocation={userLocation} locationError={locationError} />
    </main>
  );
};

export default App;
