import React, { useEffect } from 'react';
import { useMap } from 'react-leaflet';
import type { LatLngTuple } from '../../types/hazards';

interface LocationControllerProps {
  onLocationFound?: (coords: LatLngTuple) => void;
  onLocationError?: (message: string) => void;
  // Set to false once the user picks a spot manually so a late GPS fix doesn't override it
  enabled?: boolean;
}

export const LocationController: React.FC<LocationControllerProps> = ({
  onLocationFound,
  onLocationError,
  enabled = true,
}) => {
  const map = useMap();

  useEffect(() => {
    // Flag to track if THIS specific render cycle was unmounted
    let isCancelled = false;

    if (!enabled) return;

    if (!navigator.geolocation) {
      console.warn('Geolocation is not supported by your browser.');
      onLocationError?.('Location is not supported by your browser.');
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
        if (isCancelled) return;

        console.warn(`Geolocation error (${error.code}): ${error.message}`);
        onLocationError?.(
          error.code === error.PERMISSION_DENIED
            ? 'Location access was denied.'
            : 'Your location could not be determined.'
        );
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
  }, [map, onLocationFound, onLocationError, enabled]);

  return null;
};

export default LocationController;