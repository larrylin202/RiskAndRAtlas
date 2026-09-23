// frontend/src/App.tsx
import React from 'react';
import HazardMap from './components/map/HazardMap';
import RiskIndicators from './components/panels/RiskIndicators';

export const App: React.FC = () => {
  return (
    <main style={{ margin: 0, padding: 0, height: '100%', width: '100%', overflow: 'hidden' }}>
      <HazardMap />
      <RiskIndicators />
    </main>
  );
};

export default App;