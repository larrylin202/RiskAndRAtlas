// frontend/src/App.tsx
import React from 'react';
import HazardMap from './components/map/HazardMap';

export const App: React.FC = () => {
  return (
    <main style={{ margin: 0, padding: 0, height: '100vh', width: '100vw', overflow: 'hidden' }}>
      <HazardMap />
    </main>
  );
};

export default App;