import React, { useState } from 'react';

interface MapSearchBarProps {
    onSearch: (name: string) => void;
    disabled?: boolean;
}

const MAX_SEARCH_LENGTH = 200;

export const MapSearchBar: React.FC<MapSearchBarProps> = ({ onSearch, disabled = false }) => {
    const [text, setText] = useState('');
    const trimmed = text.trim();

    const handleSubmit = (event: React.FormEvent<HTMLFormElement>) => {
        event.preventDefault();
        if (!trimmed) return;
        onSearch(trimmed);
    };

    return (
        <form className="map-search" role="search" onSubmit={handleSubmit}>
            <label htmlFor="map-search-input" className="visually-hidden">
                Search map...
            </label>
            <input
                id="map-search-input"
                type="search"
                value={text}
                onChange={(event) => setText(event.target.value)}
                maxLength={MAX_SEARCH_LENGTH}
                placeholder="Search for a city, address, or landmark"
                autoComplete="off"
            />
            <button type="submit" disabled={disabled || !trimmed}>
                Search
            </button>
        </form>
    );
};

export default MapSearchBar;