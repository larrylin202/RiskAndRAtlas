// frontend/src/types/hazards.ts
import type { FeatureCollection, Point, Geometry } from 'geojson';

export interface HazardProperties {
  id?: string;
  title?: string;
  mag?: number;
  place?: string;
  time?: number;
  severity?: 'Low' | 'Medium' | 'High' | 'Extreme';
  hazardType?: 'earthquake' | 'wildfire' | 'flood' | 'aqi';
}

export type HazardFeatureCollection = FeatureCollection<Geometry, HazardProperties>;

export type LatLngTuple = [number, number];