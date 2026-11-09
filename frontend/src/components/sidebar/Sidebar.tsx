import React, { useState } from 'react';
import DataRow from './DataRow';
import SidebarSearch from './SidebarSearch';
import useRiskScore from '../../hooks/useRiskScore';
import type { LatLngTuple } from '../../types/hazards';
import type { Places } from '../../types/places';
import { getRiskLevel } from '../../utils/riskLevel';

import atlasTitle from '../../assets/sidebar/atlas-title.png';
import earthquakeIcon from '../../assets/sidebar/earthquake.svg';
import wildfireIcon from '../../assets/sidebar/wildfire.svg';
import airQualityIcon from '../../assets/sidebar/air-quality.svg';
import floodIcon from '../../assets/sidebar/flood.svg';
import hospitalIcon from '../../assets/sidebar/hospital.svg';
import shelterIcon from '../../assets/sidebar/shelter.svg';
import fireStationIcon from '../../assets/sidebar/fire-station.svg';

type RiskKey = 'earthquake' | 'wildfire' | 'airQuality' | 'flood';

const RISKS: { key: RiskKey; label: string; icon: string; color: string }[] = [
  { key: 'earthquake', label: 'Earthquake', icon: earthquakeIcon, color: '#f4c46a' },
  { key: 'wildfire', label: 'Wildfire', icon: wildfireIcon, color: '#e06646' },
  { key: 'airQuality', label: 'Air Quality', icon: airQualityIcon, color: '#a3b899' },
  { key: 'flood', label: 'Flood', icon: floodIcon, color: '#bac7d5' },
];

const FACILITIES = [
  { label: 'Hospitals', icon: hospitalIcon },
  { label: 'Shelters', icon: shelterIcon },
  { label: 'Fire Stations', icon: fireStationIcon },
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
    // Other hazards are not scored by the backend yet
    return null;
  };

  const riskDetail = (key: RiskKey, score: number | null): React.ReactNode => {
    if (!location) return 'Choose a location to see this score.';
    if (risk.status === 'loading') return 'Loading risk score...';
    if (risk.status === 'error') return risk.message;
    if (key !== 'earthquake') return 'Scoring integration pending.';
    if (score === null || !riskData) return 'No score available for this location.';

    return (
      <>
        <p>{getRiskLevel(score).description}</p>
        <p>Nearby earthquakes: {riskData.earthquake_count}</p>
        {riskData.strongest_earthquake && (
          <p>
            Highest-scoring event: magnitude {riskData.strongest_earthquake.magnitude.toFixed(1)},{' '}
            {riskData.strongest_earthquake.distance_km.toFixed(1)} km away
          </p>
        )}
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
        <h1>
          <img src={atlasTitle} alt="Risk & Resilience Atlas" className="atlas-title" />
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
