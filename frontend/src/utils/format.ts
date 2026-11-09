import type { LatLngTuple } from '../types/hazards';

export const formatCoords = ([lat, lon]: LatLngTuple) => `${lat.toFixed(5)}, ${lon.toFixed(5)}`;
