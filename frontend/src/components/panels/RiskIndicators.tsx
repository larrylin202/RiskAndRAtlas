
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
      setError(null);
      setIsLoading(false);
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

        setError(
          err instanceof Error ? err.message : 'An unexpected error occurred.'
        );
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

  const formatScore = (score: number | null | undefined): string => {
    return typeof score === 'number' && Number.isFinite(score)
      ? `${score.toFixed(2)} / 100`
      : '-- / 100';
  };

  const renderPending = () => (
    <span style={{ color: '#6b7280', fontSize: '12px' }}>Pending</span>
  );

  const indicatorStyle: React.CSSProperties = {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'space-between',
    gap: '12px',
    padding: '10px 0',
    borderBottom: '1px solid #e5e7eb',
  };

  const labelStyle: React.CSSProperties = {
    margin: 0,
    fontWeight: 600,
    fontSize: '14px',
    color: '#1f2937',
  };

  const descriptionStyle: React.CSSProperties = {
    margin: '3px 0 0',
    fontSize: '12px',
    color: '#6b7280',
  };

  const sectionHeadingStyle: React.CSSProperties = {
    margin: '16px 0 4px',
    fontSize: '15px',
    color: '#374151',
  };

  return (
    <section
      style={{
        position: 'absolute',
        top: '20px',
        left: '20px',
        zIndex: 1000,
        width: '300px',
        maxHeight: 'calc(100% - 40px)',
        overflowY: 'auto',
        padding: '20px',
        backgroundColor: 'white',
        borderRadius: '10px',
        boxShadow: '0 2px 10px rgba(0, 0, 0, 0.2)',
      }}
    >
      <h2 style={{ margin: '0 0 8px', fontSize: '21px' }}>
        Risk Indicators
      </h2>

      {!userLocation && (
        <p style={descriptionStyle}>Waiting for your location...</p>
      )}

      {userLocation && isLoading && (
        <p style={descriptionStyle}>Loading risk scores...</p>
      )}

      {error && (
        <p role="alert" style={{ color: '#b91c1c', fontSize: '13px' }}>
          Error loading risk score: {error}
        </p>
      )}

      <h3 style={sectionHeadingStyle}>Hazard Risks</h3>

      <div style={{ ...indicatorStyle, borderBottom: 'none' }}>
        <div>
          <p style={labelStyle}>Earthquake Risk</p>
          <p style={descriptionStyle}>Live backend score</p>
        </div>
        <strong style={{ fontSize: '14px', whiteSpace: 'nowrap' }}>
          {riskData && !error
            ? formatScore(riskData.earthquake_risk)
            : '-- / 100'}
        </strong>
      </div>

      {riskData && !error && (
        <div
          style={{
            margin: '8px 0 12px',
            padding: '10px',
            backgroundColor: '#f9fafb',
            borderRadius: '6px',
            borderBottom: '1px solid #e5e7eb',
          }}
        >
          <p style={{ ...labelStyle, fontSize: '13px' }}>
            Earthquake Details
          </p>
          <p style={descriptionStyle}>
            Nearby earthquakes: {riskData.earthquake_count}
          </p>

          {riskData.strongest_earthquake && (
            <p style={descriptionStyle}>
              Highest-scoring event: magnitude{' '}
              {riskData.strongest_earthquake.magnitude.toFixed(2)},{' '}
              {riskData.strongest_earthquake.distance_km.toFixed(1)} km away
            </p>
          )}
        </div>
      )}

      <div style={indicatorStyle}>
        <div>
          <p style={labelStyle}>Wildfire Risk</p>
          <p style={descriptionStyle}>Scoring integration pending</p>
        </div>
        {renderPending()}
      </div>

      <div style={indicatorStyle}>
        <div>
          <p style={labelStyle}>Flood Risk</p>
          <p style={descriptionStyle}>Scoring integration pending</p>
        </div>
        {renderPending()}
      </div>

      <div style={indicatorStyle}>
        <div>
          <p style={labelStyle}>Air Quality Risk</p>
          <p style={descriptionStyle}>Scoring integration pending</p>
        </div>
        {renderPending()}
      </div>

      <h3 style={sectionHeadingStyle}>Community Resilience</h3>

      <div style={indicatorStyle}>
        <div>
          <p style={labelStyle}>Hospital Readiness</p>
          <p style={descriptionStyle}>Indicator integration pending</p>
        </div>
        {renderPending()}
      </div>

      <div style={indicatorStyle}>
        <div>
          <p style={labelStyle}>Shelter Readiness</p>
          <p style={descriptionStyle}>Indicator integration pending</p>
        </div>
        {renderPending()}
      </div>

      <div style={indicatorStyle}>
        <div>
          <p style={labelStyle}>Fire Station Readiness</p>
          <p style={descriptionStyle}>Indicator integration pending</p>
        </div>
        {renderPending()}
      </div>

      <div
        style={{
          marginTop: '18px',
          paddingTop: '14px',
          borderTop: '2px solid #e5e7eb',
        }}
      >
        <p
          style={{
            margin: '0 0 6px',
            fontSize: '13px',
            color: '#4b5563',
          }}
        >
          Combined Risk Score
        </p>

        <strong style={{ fontSize: '24px', color: '#1f2937' }}>
          {riskData && !error
            ? formatScore(riskData.combined_risk)
            : '-- / 100'}
        </strong>
      </div>
    </section>
  );
};

export default RiskIndicators;
