// frontend/src/components/map/HazardMap.tsx
import React, { useEffect, useState, useCallback } from 'react';
import { MapContainer, TileLayer, GeoJSON, Marker, Popup } from 'react-leaflet';
import type { Layer } from 'leaflet';
import type { Feature, Geometry } from 'geojson';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';

import LocationController from './LocationController';
import type { HazardFeatureCollection, HazardProperties, LatLngTuple } from '../../types/hazards';

// Leaflet default marker icon resolution for bundlers
import markerIcon2x from 'leaflet/dist/images/marker-icon-2x.png';
import markerIcon from 'leaflet/dist/images/marker-icon.png';
import markerShadow from 'leaflet/dist/images/marker-shadow.png';

const DefaultIcon = L.icon({
  iconUrl: markerIcon,
  iconRetinaUrl: markerIcon2x,
  shadowUrl: markerShadow,
  iconSize: [25, 41],
  iconAnchor: [12, 41],
  popupAnchor: [1, -34],
  shadowSize: [41, 41],
});

L.Marker.prototype.options.icon = DefaultIcon;

export const HazardMap: React.FC = () => {
  // Default fallback center (California)
  const defaultCenter: LatLngTuple = [36.7783, -119.4179];
  const [userLocation, setUserLocation] = useState<LatLngTuple | null>(null);

  // Prevents the function from being recreated on every render
  const handleLocationFound = useCallback((coords: LatLngTuple) => {
    setUserLocation(coords);
  }, []);
  const [earthquakeData, setEarthquakeData] = useState<HazardFeatureCollection | null>(null);
  const [wildfireData, setWildfireData] = useState<HazardFeatureCollection | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    // Fetch earthquake data
    fetch('/api/hazards/earthquakes')
      .then((res) => {
        if (!res.ok) {
          throw new Error(`HTTP error: ${res.status}`);
        }
        return res.json() as Promise<HazardFeatureCollection>;
      })
      .then((data) => {
        setEarthquakeData(data);
        setIsLoading(false);
      })
      .catch((err: Error) => {
        console.error('Failed to load hazard GeoJSON:', err);
        setError(err.message);
        setIsLoading(false);
      });
    
    // Fetch wildfire data
    fetch('/api/hazards/wildfires')
      .then((res) => {
        if (!res.ok) {
          throw new Error('HTTP error: ${res.status}');
        }
        return res.json() as Promise<HazardFeatureCollection>;
      })
      .then((data) => {
        setWildfireData(data);
        setIsLoading(false);
      })
      .catch((err: Error) => {
        console.error('Failed to load hazard GeoJSON:', err);
        setError(err.message);
        setIsLoading(false);
      });
  }, []);

  const onEachHazardFeature = (
    feature: Feature<Geometry, HazardProperties>,
    layer: Layer
  ) => {
    if (feature.properties && feature.properties.title) {
      layer.bindPopup(`
        <div style="font-family: sans-serif; font-size: 13px;">
          <h4 style="margin: 0 0 4px 0;">${feature.properties.title}</h4>
          ${feature.properties.place ? `<p style="margin: 0;">Location: ${feature.properties.place}</p>` : ''}
          ${feature.properties.mag ? `<p style="margin: 0;">Magnitude: <strong>${feature.properties.mag}</strong></p>` : ''}
          ${feature.properties.size ? `<p style="margin: 0;">Size: ${feature.properties.size}</p>` : ''}
        </div>
      `);
    }
  };

  // Converts standard points into Leaflet circles using the backend properties
  const createCircleMarker = (feature: Feature<Geometry, any>, latlng: L.LatLng) => {
    const { radius, fillColor, fillOpacity } = feature.properties;
    
    return L.circle(latlng, {
      radius: radius || 500,
      fillColor: fillColor || 'gray',
      color: fillColor || 'gray', // Outline color
      weight: 1,
      fillOpacity: fillOpacity || 0.4,
    });
  };

  const setWildfireStyle = () => {
    return {
      fillColor: 'red',
      color: 'red', // Outline color
      weight: 1,
      fillOpacity: 0.4,
    };
  };

  return (
    <div style={{ height: '100vh', width: '100%', position: 'relative' }}>
      {isLoading && (
        <div style={{
          position: 'absolute',
          top: 16,
          right: 16,
          zIndex: 1000,
          background: 'rgba(255, 255, 255, 0.9)',
          padding: '6px 12px',
          borderRadius: 4,
          boxShadow: '0 2px 4px rgba(0,0,0,0.15)',
          fontSize: 12
        }}>
          Loading hazard layers...
        </div>
      )}

      {error && (
        <div style={{
          position: 'absolute',
          bottom: 16,
          left: 16,
          zIndex: 1000,
          background: '#fee2e2',
          color: '#991b1b',
          padding: '8px 12px',
          borderRadius: 4,
          fontSize: 12
        }}>
          Layer error: {error}
        </div>
      )}

      <MapContainer
        center={defaultCenter}
        zoom={6}
        style={{ height: '100%', width: '100%' }}
      >
        <TileLayer
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
        />

        <LocationController onLocationFound={handleLocationFound} />

        {userLocation && (
          <Marker position={userLocation}>
            <Popup>
              <strong>You are here</strong>
            </Popup>
          </Marker>
        )}

        {earthquakeData && (
          <GeoJSON
            key={JSON.stringify(earthquakeData)}
            data={earthquakeData}
            onEachFeature={onEachHazardFeature}
            pointToLayer={createCircleMarker}
          />
        )}

        {wildfireData && (
          <GeoJSON
            key={JSON.stringify(wildfireData)}
            data={wildfireData}
            onEachFeature={onEachHazardFeature}
            style={setWildfireStyle}
          />
        )}
      </MapContainer>
    </div>
  );
};

export default HazardMap;