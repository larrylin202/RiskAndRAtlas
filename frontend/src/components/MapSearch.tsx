import React, { useEffect, useRef, useState } from 'react';
import MapSearchBar from './MapSearchBar';
import { searchMap } from '../services/api';
import type { Places } from '../types/places'

type SearchState =
    | { status: 'idle' }
    | { status: 'loading'; query: string }
    | { status: 'done'; query: string; places: Places[] }
    | { status: 'error'; query: string; message: string };


interface MapSearchProps {
    onSelectPlace: (places: Places) => void;
}

export const MapSearch: React.FC<MapSearchProps> = ({ onSelectPlace }) => {
    const [search, setSearch] = useState<SearchState>({ status: 'idle'});
    const controllerRef = useRef<AbortController | null>(null);

    useEffect(() => () => controllerRef.current?.abort(), []);

    const handleSearch = async (search_query: string) => {
        controllerRef.current?.abort();
        const controller = new AbortController();
        controllerRef.current = controller;

        setSearch({ status: 'loading', query: search_query });
        try {
            const places = await searchMap(search_query, controller.signal);
            setSearch({ status: 'done', query: search_query, places });
        } catch (err) {
            if (controller.signal.aborted) return;
            const message = err instanceof Error ? err.message : 'Something went wrong.';
            setSearch({ status: 'error', query: search_query, message });
        }
    };

    const handleSelect = (place: Places) => {
        onSelectPlace(place);
        setSearch({ status: 'idle' });
    };

    return (
        <div className="place-search-panel">
            <MapSearchBar onSearch={handleSearch} disabled={search.status === 'loading'} />

            {search.status === 'loading' && <p className="place-search-status">Searching...</p>}

            {search.status === 'error' && (
                <p className="place-search-status place-search-error">{search.message}</p>
            )}

            {search.status === 'done' && search.places.length === 0 && (
                <p className="place-search-status">No places found for "{search.query}".</p>
            )}

            {search.status === 'done' && search.places.length > 0 && (
                <ul className="place-search-results">
                    {search.places.map((place) => (
                        <li key={place.id}>
                            <button type="button" onClick={() => handleSelect(place)}>
                                <span className="place-label">{place.label}</span>
                            </button>
                        </li>
                    ))}
                </ul>
            )}
        </div>
    );
};

export default MapSearch;