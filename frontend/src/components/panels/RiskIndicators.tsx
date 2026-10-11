import React, { useEffect, useState } from 'react';
import type { LatLngTuple } from '../../types/hazards';

interface RiskIndicatorsProps {
  userLocation: LatLngTuple | null;
}

interface RiskScoreResponse {
  combined_risk: number;
  earthquake_risk: number | null;
  earthquake_count: number;
  latitude: number;
  longitude: number;
  strongest_earthquake: {
    age_days: number;
    distance_km: number;
    magnitude: number;
    score: number;
  } | null;
}

const RiskIndicators: React.FC<RiskIndicatorsProps> = ({ userLocation }) => {
  const [riskData, setRiskData] = useState<RiskScoreResponse | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!userLocation) {
      setRiskData(null);
      return;
    }

    const [latitude, longitude] = userLocation;
    const controller = new AbortController();

    const fetchRiskScore = async () => {
      setIsLoading(true);
      setError(null);

      try {
        const response = await fetch(
          `/api/risk/score?lat=${latitude}&lon=${longitude}`,
          { signal: controller.signal }
        );

        if (!response.ok) {
          throw new Error(`Unable to load risk score (HTTP ${response.status})`);
        }

        const data: RiskScoreResponse = await response.json();
        setRiskData(data);
      } catch (err) {
        if (err instanceof Error && err.name === 'AbortError') {
          return;
        }

        setError(err instanceof Error ? err.message : 'An unexpected error occurred.');
        setRiskData(null);
      } finally {
        if (!controller.signal.aborted) {
          setIsLoading(false);
        }
      }
    };

    void fetchRiskScore();

    return () => controller.abort();
  }, [userLocation]);

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

      {!userLocation && <p>Waiting for your location...</p>}

      {userLocation && isLoading && <p>Loading risk scores...</p>}

      {error && <p role="alert">Error: {error}</p>}

      {riskData && !error && (
        <>
          <p>
            Earthquake Risk:{' '}
            {riskData.earthquake_risk !== null
              ? `${riskData.earthquake_risk.toFixed(2)} / 100`
              : 'Unavailable'}
          </p>

          <p>Wildfire Risk: --</p>
          <p>Environmental Risk: --</p>

          <hr />

          <strong>
            Overall Risk: {riskData.combined_risk.toFixed(2)} / 100
          </strong>

          <p>Nearby earthquakes: {riskData.earthquake_count}</p>

          {riskData.strongest_earthquake && (
            <p>
              Highest-scoring nearby earthquake: magnitude{' '}
              {riskData.strongest_earthquake.magnitude.toFixed(2)},{' '}
              {riskData.strongest_earthquake.distance_km.toFixed(1)} km away
            </p>
          )}
        </>
      )}
    </section>
  );
};

export default RiskIndicators;
