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
    initialText?: string;
}

export const MapSearch: React.FC<MapSearchProps> = ({ onSelectPlace, initialText }) => {
    const [search, setSearch] = useState<SearchState>({ status: 'idle'});
    const [isOpen, setIsOpen] = useState(false);
    const controllerRef = useRef<AbortController | null>(null);

    useEffect(() => () => controllerRef.current?.abort(), []);

    const handleSearch = async (search_query: string) => {
        controllerRef.current?.abort();
        const controller = new AbortController();
        controllerRef.current = controller;

        setIsOpen(true);
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
        setIsOpen(false);
    };

    const handleBlur = (event: React.FocusEvent<HTMLDivElement>) => {
        if (event.currentTarget.contains(event.relatedTarget)) return;
        setIsOpen(false);
    };

    const handleFocus = () => setIsOpen(true);

    const handleKeyDown = (event: React.KeyboardEvent<HTMLDivElement>) => {
        if (event.key === 'Escape') setIsOpen(false);
    };

    const handleTextChange = (trimmedText: string) => {
        if (search.status === 'idle' || trimmedText === search.query) return;
        controllerRef.current?.abort();
        setSearch({ status: 'idle' });
        setIsOpen(false);
    }

    return (
        <div 
            className="place-search-panel"
            onFocus={handleFocus}
            onBlur={handleBlur}
            onKeyDown={handleKeyDown}
        >
            <MapSearchBar 
                onSearch={handleSearch} 
                onTextChange={handleTextChange} 
                busy={search.status === 'loading'} 
                initialText={initialText}
            />

            {isOpen && search.status === 'loading' && <p className="place-search-status">Searching...</p>}

            {isOpen && search.status === 'error' && (
                <p className="place-search-status place-search-error">{search.message}</p>
            )}

            {isOpen && search.status === 'done' && search.places.length === 0 && (
                <p className="place-search-status">No places found for "{search.query}".</p>
            )}

            {isOpen && search.status === 'done' && search.places.length > 0 && (
                <ul className="place-search-results">
                    {search.places.map((place) => (
                        <li key={place.id}>
                            <button 
                                type="button" 
                                onMouseDown={(event) => event.preventDefault()}
                                onClick={() => handleSelect(place)}
                            >
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