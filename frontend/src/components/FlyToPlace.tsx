import React, { useEffect } from 'react';
import { useMap } from 'react-leaflet';
import type { Places } from '../types/places'

interface FlyToPlaceProps {
    place: Places | null;
}

// The sidebar sits beside the map rather than over it, so even padding is enough
const MAP_PADDING: [number, number] = [20, 20];

export const FlyToPlace: React.FC<FlyToPlaceProps> = ({ place }) => {
    const map = useMap();

    useEffect(() => {
        if (!place) return;

        map.stop();
        map.flyToBounds(place.bounds, {
            padding: MAP_PADDING,
            maxZoom: 16,
            duration: 1.5,
        });
    }, [map, place]);

    return null;
}

export default FlyToPlace;
