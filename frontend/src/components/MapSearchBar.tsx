import React, { useState } from 'react';

interface MapSearchBarProps {
    onSearch: (name: string) => void;
    onTextChange?: (trimmedText: string) => void;
    busy?: boolean;
    initialText?: string;
}

const MAX_SEARCH_LENGTH = 200;

export const MapSearchBar: React.FC<MapSearchBarProps> = ({ onSearch, onTextChange, busy = false, initialText = '' }) => {
    const [text, setText] = useState(initialText);
    const trimmed = text.trim();

    const handleChange = (event: React.ChangeEvent<HTMLInputElement>) => {
        const value = event.target.value;
        setText(value);
        onTextChange?.(value.trim());
    }

    const handleSubmit = (event: React.FormEvent<HTMLFormElement>) => {
        event.preventDefault();
        if (!trimmed || busy) return;
        onSearch(trimmed);
    };

    return (
        <form className="map-search" role="search" onSubmit={handleSubmit}>
            <label htmlFor="map-search-input" className="visually-hidden">
                Search for a location
            </label>
            <input
                id="map-search-input"
                type="search"
                value={text}
                onChange={handleChange}
                maxLength={MAX_SEARCH_LENGTH}
                placeholder="Search for a city, address, or landmark"
                autoComplete="off"
            />
            <button 
                type="submit"  
                disabled={!trimmed}
                aria-disabled={busy}
                onMouseDown={(event) => event.preventDefault()}
            >
                {busy ? 'Searching...' : 'Search'}
            </button>
        </form>
    );
};

export default MapSearchBar;