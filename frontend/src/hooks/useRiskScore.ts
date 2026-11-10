import { useEffect, useState } from 'react';
import type { LatLngTuple } from '../types/hazards';

export interface RiskScoreResponse {
  combined_risk: number;
  earthquake_risk: number | null;
  earthquake_count: number;
  latitude: number;
  longitude: number;

  air_quality_available: boolean;
  air_quality_risk: number | null;
  air_quality_aqi: number | null;
  air_quality_category: string | null;
  air_quality_pollutant: string | null;
  air_quality_observed_at: string | null;
  air_quality_site: string | null;
  air_quality_reporting_area: string | null;

  strongest_earthquake: {
    age_days: number;
    distance_km: number;
    magnitude: number;
    score: number;
  } | null;
  wildfire_risk: number | null;
  wildfire_count: number;
  strongest_wildfire: {
    title: string | null;
    size_acres: number | null;
    distance_km: number;
    score: number;
  } | null;
  flood_risk: number | null;
  flood_gauge_count: number;
  nearest_flood_gauge: {
    gauge_id: string;
    title: string | null;
    distance_km: number;
    score: number;
  } | null;
}

type RiskScoreState =
  | { status: 'idle' }
  | { status: 'loading' }
  | { status: 'done'; data: RiskScoreResponse }
  | { status: 'error'; message: string };

// Fetches the backend risk score for a location; refetches whenever it changes
export function useRiskScore(location: LatLngTuple | null): RiskScoreState {
  const [state, setState] = useState<RiskScoreState>({ status: 'idle' });

  useEffect(() => {
    if (!location) {
      setState({ status: 'idle' });
      return;
    }

    const [lat, lon] = location;
    const controller = new AbortController();
    setState({ status: 'loading' });

    fetch(`/api/risk/score?lat=${lat}&lon=${lon}`, { signal: controller.signal })
      .then((res) => {
        if (!res.ok) throw new Error(`Unable to load risk score (HTTP ${res.status}).`);
        return res.json() as Promise<RiskScoreResponse>;
      })
      .then((data) => setState({ status: 'done', data }))
      .catch((err: unknown) => {
        if (controller.signal.aborted) return;
        setState({
          status: 'error',
          message: err instanceof Error ? err.message : 'An unexpected error occurred.',
        });
      });

    return () => controller.abort();
  }, [location]);

  return state;
}

export default useRiskScore;
