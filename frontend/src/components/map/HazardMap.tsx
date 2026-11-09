import React, { useEffect, useState, useCallback } from 'react';
import { MapContainer, TileLayer, GeoJSON, Marker, CircleMarker, Popup, useMapEvents, ZoomControl } from 'react-leaflet';
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
import FlyToPlace from '../FlyToPlace';
import type { Places } from '../../types/places';
import { formatCoords } from '../../utils/format';

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

const HAZARD_LAYERS = {
  earthquakes: { url: '/api/hazards/earthquakes', name: 'earthquake' },
  wildfires: { url: '/api/hazards/wildfires', name: 'wildfire' },
  floods: { url: '/api/hazards/floods', name: 'flood' },
} as const;

type HazardLayerKey = keyof typeof HAZARD_LAYERS;

const ALL_LAYER_KEYS = Object.keys(HAZARD_LAYERS) as HazardLayerKey[];

const fetchHazardLayer = async (url: string, signal: AbortSignal) => {
  const res = await fetch(url, { signal });
  if (!res.ok) throw new Error(`HTTP ${res.status} for ${url}`);
  return (await res.json()) as HazardFeatureCollection;
};

// ['wildfires', 'floods'] -> "wildfire and flood"
const listLayerNames = (keys: HazardLayerKey[]) => {
  const names = keys.map((key) => HAZARD_LAYERS[key].name);
  if (names.length <= 1) return names.join('');
  return `${names.slice(0, -1).join(', ')} and ${names[names.length - 1]}`;
};

// Lets the user pick a location by double-clicking the map
const MapDoubleClickHandler: React.FC<{ onPick: (coords: LatLngTuple) => void }> = ({ onPick }) => {
  useMapEvents({
    dblclick: (event) => onPick([event.latlng.lat, event.latlng.lng]),
  });
  return null;
};

interface HazardMapProps {
  deviceLocation: LatLngTuple | null;
  selectedPlace: Places | null;
  pickedLocation: LatLngTuple | null;
  onDeviceLocationFound?: (coords: LatLngTuple) => void;
  onLocationError?: (message: string) => void;
  onMapPick?: (coords: LatLngTuple) => void;
}

export const HazardMap: React.FC<HazardMapProps> = ({
  deviceLocation,
  selectedPlace,
  pickedLocation,
  onDeviceLocationFound,
  onLocationError,
  onMapPick,
}) => {
  // Default fallback center (California)
  const defaultCenter: LatLngTuple = [36.7783, -119.4179];
  const hasChosenLocation = selectedPlace !== null || pickedLocation !== null;

  const handleMapPick = useCallback((coords: LatLngTuple) => onMapPick?.(coords), [onMapPick]);

  // Each layer loads independently; one failing must not hide the others
  const [layers, setLayers] = useState<Partial<Record<HazardLayerKey, HazardFeatureCollection>>>({});
  // Layers still to fetch: all of them at first, only the failed ones on retry
  const [pendingLayers, setPendingLayers] = useState<HazardLayerKey[]>(ALL_LAYER_KEYS);
  const [failedLayers, setFailedLayers] = useState<HazardLayerKey[]>([]);
  const isLoading = pendingLayers.length > 0;

  useEffect(() => {
    if (pendingLayers.length === 0) return;
    const controller = new AbortController();

    Promise.allSettled(
      pendingLayers.map((key) => fetchHazardLayer(HAZARD_LAYERS[key].url, controller.signal))
    ).then((results) => {
      if (controller.signal.aborted) return;

      const loaded: Partial<Record<HazardLayerKey, HazardFeatureCollection>> = {};
      const failed: HazardLayerKey[] = [];
      results.forEach((result, i) => {
        const key = pendingLayers[i];
        if (result.status === 'fulfilled') loaded[key] = result.value;
        else {
          console.error(`Failed to load ${key} hazard layer:`, result.reason);
          failed.push(key);
        }
      });

      setLayers((current) => ({ ...current, ...loaded }));
      setFailedLayers(failed);
      setPendingLayers([]);
    });

    return () => controller.abort();
  }, [pendingLayers]);

  const retryFailedLayers = () => {
    setPendingLayers(failedLayers);
    setFailedLayers([]);
  };

  const onEachHazardFeature = (
    feature: Feature<Geometry, HazardProperties>,
    layer: Layer
  ) => {
    if (feature.properties && feature.properties.title) {
      const titleText = feature.properties.title

      const buildPopup = () => {
        const div = document.createElement('div');
        div.className = "hazard-popup";

        const title = document.createElement('h4');

        title.textContent = titleText

        div.append(title)

        if (feature.properties.place) {
          const locationText = document.createElement('p')

          locationText.textContent = `Location: ${feature.properties.place}`

          div.append(locationText)
        }
      
        if (feature.properties.mag != null) {
          const magnitudeText = document.createElement('p')

          const magnitudeNumber = document.createElement('strong')
          magnitudeNumber.textContent = String(feature.properties.mag)

          magnitudeText.textContent = `Magnitude: `
          magnitudeText.append(magnitudeNumber)

          div.append(magnitudeText)
        }

        return div
      }

      layer.bindPopup(buildPopup);
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
    <div className="hazard-map">
      {/* Top-left keeps clear of the zoom control (top-right) and attribution (bottom-right) */}
      <div className="map-status-stack">
        {isLoading && (
          <p className="map-status" role="status">
            <span className="map-spinner" aria-hidden="true" />
            Loading hazard layers…
          </p>
        )}

        {failedLayers.length > 0 && !isLoading && (
          <div className="map-status map-status--error" role="alert">
            <span>Couldn't load {listLayerNames(failedLayers)} data.</span>
            <button type="button" className="map-status__retry" onClick={retryFailedLayers}>
              Retry
            </button>
          </div>
        )}
      </div>

      <MapContainer
        className="hazard-map__container"
        center={defaultCenter}
        zoom={6}
        zoomControl={false}
        doubleClickZoom={false}
      >
        <ZoomControl 
          position='topright'
        />

        <TileLayer
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
        />

        <LocationController
          onLocationFound={onDeviceLocationFound}
          onLocationError={onLocationError}
          enabled={!hasChosenLocation}
        />

        <MapDoubleClickHandler onPick={handleMapPick} />
        
        <FlyToPlace place={selectedPlace} />

        {deviceLocation && (
          <CircleMarker
            center={deviceLocation}
            radius={8}
            pathOptions={{ color: '#ffffff', weight: 2, fillColor: '#2563eb', fillOpacity: 1 }}
          >
            <Popup>
              <strong>You are here</strong>
            </Popup>
          </CircleMarker>
        )}

        {selectedPlace && (
          <Marker position={[selectedPlace.lat, selectedPlace.lon]}>
            <Popup>{selectedPlace.label}</Popup>
          </Marker>
        )}

        {pickedLocation && (
          <Marker position={pickedLocation}>
            <Popup>
              <strong>Selected location</strong>
              <br />
              {formatCoords(pickedLocation)}
            </Popup>
          </Marker>
        )}

        {layers.earthquakes && (
          <GeoJSON
            data={layers.earthquakes}
            onEachFeature={onEachHazardFeature}
            pointToLayer={createCircleMarker}
          />
        )}

        {layers.wildfires && (
          <GeoJSON
            data={layers.wildfires}
            onEachFeature={onEachHazardFeature}
            style={setWildfireStyle}
          />
        )}

        {layers.floods && (
          <GeoJSON
            data={layers.floods}
            onEachFeature={onEachHazardFeature}
          />
        )}
      </MapContainer>
    </div>
  );
};

export default HazardMap;
