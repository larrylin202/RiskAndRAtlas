import React, { useEffect } from 'react';
import { useMap } from 'react-leaflet';
import type { LatLngTuple } from '../../types/hazards';

interface LocationControllerProps {
  onLocationFound?: (coords: LatLngTuple) => void;
}

export const LocationController: React.FC<LocationControllerProps> = ({ onLocationFound }) => {
  const map = useMap();

  useEffect(() => {
    // Flag to track if THIS specific render cycle was unmounted
    let isCancelled = false;

    if (!navigator.geolocation) {
      console.warn('Geolocation is not supported by your browser.');
      return;
    }

    navigator.geolocation.getCurrentPosition(
      (position: GeolocationPosition) => {
        // If React Strict Mode unmounted this component while waiting, ignore the result
        if (isCancelled) return;

        const { latitude, longitude } = position.coords;
        const userCoords: LatLngTuple = [latitude, longitude];

        // Stop any running animations and fly cleanly to the new coordinates
        map.stop();
        map.flyTo(userCoords, 12, { animate: true, duration: 1.5 });

        if (onLocationFound) {
          onLocationFound(userCoords);
        }
      },
      (error: GeolocationPositionError) => {
        console.warn(`Geolocation error (${error.code}): ${error.message}`);
      },
      {
        enableHighAccuracy: true,
        timeout: 10000,
        maximumAge: 60000,
      }
    );

    // Cleanup: When Strict Mode unmounts the component, cancel the pending callback
    return () => {
      isCancelled = true;
    };
  }, [map, onLocationFound]);

  return null;
};

export default LocationController;