import React, { useEffect } from 'react';
import { useMap } from 'react-leaflet';
import type { Places } from '../types/places'

interface FlyToPlaceProps {
    place: Places | null;
}

const PANEL_SPACE = 380;

const WIDE_MAP_MIN_WIDTH = 700;

export const FlyToPlace: React.FC<FlyToPlaceProps> = ({ place }) => {
    const map = useMap();

    useEffect(() => {
        if (!place) return;

        const isWide = map.getSize().x >= WIDE_MAP_MIN_WIDTH;

        map.stop();
        map.flyToBounds(place.bounds, {
            paddingTopLeft: isWide ? [PANEL_SPACE, 20] : [20, 90],
            paddingBottomRight: [20, 20],
            maxZoom: 16,
            duration: 1.5,
        });
    }, [map, place]);

    return null;
}

export default FlyToPlace;