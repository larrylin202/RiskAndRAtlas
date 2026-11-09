import React, { useState } from 'react';
import DataRow from './DataRow';
import SidebarSearch from './SidebarSearch';
import useRiskScore, { type RiskScoreResponse } from '../../hooks/useRiskScore';
import type { LatLngTuple } from '../../types/hazards';
import type { Places } from '../../types/places';
import { getRiskLevel } from '../../utils/riskLevel';

import {
  AirQualityIcon,
  EarthquakeIcon,
  FireStationIcon,
  FloodIcon,
  HospitalIcon,
  ShelterIcon,
  WildfireIcon,
} from './icons';

type RiskKey = 'earthquake' | 'wildfire' | 'airQuality' | 'flood';

type IconComponent = React.ComponentType<React.SVGProps<SVGSVGElement>>;

// Hazard identity colours live in index.css (--atlas-hazard-*)
const RISKS: { key: RiskKey; label: string; icon: IconComponent; color: string }[] = [
  { key: 'earthquake', label: 'Earthquake', icon: EarthquakeIcon, color: 'var(--atlas-hazard-earthquake)' },
  { key: 'wildfire', label: 'Wildfire', icon: WildfireIcon, color: 'var(--atlas-hazard-wildfire)' },
  { key: 'airQuality', label: 'Air Quality', icon: AirQualityIcon, color: 'var(--atlas-hazard-air)' },
  { key: 'flood', label: 'Flood', icon: FloodIcon, color: 'var(--atlas-hazard-flood)' },
];

const FACILITIES: { label: string; icon: IconComponent }[] = [
  { label: 'Hospitals', icon: HospitalIcon },
  { label: 'Shelters', icon: ShelterIcon },
  { label: 'Fire Stations', icon: FireStationIcon },
];

const PENDING_SCORE = '--';

const formatScore = (score: number | null | undefined) =>
  typeof score === 'number' && Number.isFinite(score) ? score.toFixed(1) : PENDING_SCORE;

interface SidebarProps {
  // Location the scores are computed for (search result, map pick, or GPS)
  location: LatLngTuple | null;
  locationLabel: string | null;
  locationError: string | null;
  onSelectPlace: (place: Places) => void;
  // Changing this remounts the search bar so it picks up a new initialSearchText
  searchKey: number;
  initialSearchText: string;
}

export const Sidebar: React.FC<SidebarProps> = ({
  location,
  locationLabel,
  locationError,
  onSelectPlace,
  searchKey,
  initialSearchText,
}) => {
  const [openRow, setOpenRow] = useState<string | null>(null);
  const risk = useRiskScore(location);
  const riskData = risk.status === 'done' ? risk.data : null;

  const toggleRow = (label: string) =>
    setOpenRow((current) => (current === label ? null : label));

  const scoreFor = (key: RiskKey): number | null => {
    if (!riskData) return null;
    if (key === 'earthquake') return riskData.earthquake_risk;
    if (key === 'wildfire') return riskData.wildfire_risk;
    if (key === 'flood') return riskData.flood_risk;
    // Air quality is not scored by the backend yet
    return null;
  };

  const hazardDetail = (key: RiskKey, data: RiskScoreResponse): React.ReactNode => {
    if (key === 'earthquake') {
      const quake = data.strongest_earthquake;
      return (
        <>
          <p>Nearby earthquakes: {data.earthquake_count}</p>
          {quake && (
            <p>
              Highest-scoring event: magnitude {quake.magnitude.toFixed(1)},{' '}
              {quake.distance_km.toFixed(1)} km away
            </p>
          )}
        </>
      );
    }
    if (key === 'wildfire') {
      const fire = data.strongest_wildfire;
      return (
        <>
          <p>Nearby fire perimeters: {data.wildfire_count}</p>
          {fire && (
            <p>
              Highest-scoring fire: {fire.title ?? 'Unnamed fire'}, {fire.distance_km.toFixed(1)} km
              away
              {fire.size_acres !== null && `, ${fire.size_acres.toLocaleString()} acres`}
            </p>
          )}
        </>
      );
    }
    if (key === 'flood') {
      const gauge = data.nearest_flood_gauge;
      return (
        <>
          <p>Nearby active flood gauges: {data.flood_gauge_count}</p>
          {gauge && (
            <p>
              Nearest flood gauge: {gauge.title ?? 'Unnamed gauge'}, {gauge.distance_km.toFixed(1)}{' '}
              km away
            </p>
          )}
        </>
      );
    }
    return null;
  };

  const riskDetail = (key: RiskKey, score: number | null): React.ReactNode => {
    if (!location) return 'Choose a location to see this score.';
    if (risk.status === 'loading') return 'Loading risk score...';
    if (risk.status === 'error') return risk.message;
    if (key === 'airQuality') return 'Scoring integration pending.';
    if (score === null || !riskData) return 'No score available for this location.';

    return (
      <>
        <p>{getRiskLevel(score).description}</p>
        {hazardDetail(key, riskData)}
      </>
    );
  };

  const statusText = (() => {
    if (location && locationLabel) return `Showing data for ${locationLabel}`;
    if (locationError) return `${locationError} Search for a place or double-click the map.`;
    return 'Waiting for your location... or search for a place or double-click the map.';
  })();

  return (
    <aside className="atlas-sidebar">
      <header className="atlas-header">
        {/* Live text instead of a raster image: crisp at any DPI and themeable */}
        <h1 className="atlas-title">
          <span className="atlas-title__line">Risk &amp;</span>{' '}
          <span className="atlas-title__line">Resilience Atlas</span>
        </h1>
      </header>

      <div className="atlas-content">
        <SidebarSearch
          key={searchKey}
          initialText={initialSearchText}
          onSelectPlace={onSelectPlace}
        />

        <p className="current-location" aria-live="polite">
          {statusText}
        </p>

        <section aria-labelledby="risk-heading" className="risk-section">
          <h2 id="risk-heading">Risk Levels in your Area</h2>
          <p className="score-caption">Risk score: 0-100</p>
          {risk.status === 'error' && (
            <p role="alert" className="sidebar-error">
              {risk.message}
            </p>
          )}
          <div className="row-list">
            {RISKS.map(({ key, label, icon, color }) => {
              const score = scoreFor(key);
              return (
                <DataRow
                  key={key}
                  icon={icon}
                  label={label}
                  accent={color}
                  score={risk.status === 'loading' ? '...' : formatScore(score)}
                  level={score !== null && Number.isFinite(score) ? getRiskLevel(score) : null}
                  isOpen={openRow === label}
                  onToggle={() => toggleRow(label)}
                >
                  {riskDetail(key, score)}
                </DataRow>
              );
            })}
          </div>
        </section>

        <section aria-labelledby="facilities-heading" className="facility-section">
          <h2 id="facilities-heading">Facilities in your Area</h2>
          <div className="row-list">
            {FACILITIES.map(({ label, icon }) => (
              <DataRow
                key={label}
                icon={icon}
                label={label}
                isOpen={openRow === label}
                onToggle={() => toggleRow(label)}
              >
                Facility data integration pending.
              </DataRow>
            ))}
          </div>
        </section>
      </div>
    </aside>
  );
};

export default Sidebar;
