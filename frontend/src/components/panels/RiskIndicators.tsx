import React from 'react';

const RiskIndicators: React.FC = () => {
  return (
    <section
      style={{
        position: 'absolute',
        top: '20px',
        left: '20px',
        zIndex: 1000,
        width: '300px',
        padding: '20px',
        backgroundColor: 'white',
        borderRadius: '10px',
        boxShadow: '0 2px 10px rgba(0, 0, 0, 0.2)',
      }}
    >
      <h2>Risk Indicators</h2>

      <p>Earthquake Risk: --</p>
      <p>Wildfire Risk: --</p>
      <p>Environmental Risk: --</p>

      <hr />

      <strong>Overall Risk: --</strong>
    </section>
  );
};

export default RiskIndicators;