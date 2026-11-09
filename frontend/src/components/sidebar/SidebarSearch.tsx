import React, { useEffect, useRef, useState } from 'react';
import { searchMap } from '../../services/api';
import type { Places } from '../../types/places';
import mapPinIcon from '../../assets/sidebar/map-pin.svg';
import searchIcon from '../../assets/sidebar/search.svg';

type SearchState =
  | { status: 'idle' }
  | { status: 'loading'; query: string }
  | { status: 'done'; query: string; places: Places[] }
  | { status: 'error'; query: string; message: string };

interface SidebarSearchProps {
  onSelectPlace: (place: Places) => void;
  initialText?: string;
}

const MAX_SEARCH_LENGTH = 200;

// Location search bar at the top of the sidebar. Queries the backend geocoder
// and lists matches in a dropdown underneath.
export const SidebarSearch: React.FC<SidebarSearchProps> = ({ onSelectPlace, initialText = '' }) => {
  const [text, setText] = useState(initialText);
  const [search, setSearch] = useState<SearchState>({ status: 'idle' });
  const [isOpen, setIsOpen] = useState(false);
  const controllerRef = useRef<AbortController | null>(null);
  const trimmed = text.trim();
  const busy = search.status === 'loading';

  useEffect(() => () => controllerRef.current?.abort(), []);

  const runSearch = async (query: string) => {
    controllerRef.current?.abort();
    const controller = new AbortController();
    controllerRef.current = controller;

    setIsOpen(true);
    setSearch({ status: 'loading', query });
    try {
      const places = await searchMap(query, controller.signal);
      setSearch({ status: 'done', query, places });
    } catch (err) {
      if (controller.signal.aborted) return;
      const message = err instanceof Error ? err.message : 'Something went wrong.';
      setSearch({ status: 'error', query, message });
    }
  };

  const handleSubmit = (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!trimmed || busy) return;
    void runSearch(trimmed);
  };

  const handleChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const value = event.target.value;
    setText(value);
    // Results for an old query are stale once the text changes
    if (search.status !== 'idle' && value.trim() !== search.query) {
      controllerRef.current?.abort();
      setSearch({ status: 'idle' });
      setIsOpen(false);
    }
  };

  const handleSelect = (place: Places) => {
    if (place.label) setText(place.label);
    onSelectPlace(place);
    setSearch({ status: 'idle' });
    setIsOpen(false);
  };

  const handleBlur = (event: React.FocusEvent<HTMLFormElement>) => {
    if (event.currentTarget.contains(event.relatedTarget)) return;
    setIsOpen(false);
  };

  const handleKeyDown = (event: React.KeyboardEvent<HTMLFormElement>) => {
    if (event.key === 'Escape') setIsOpen(false);
  };

  const showDropdown = isOpen && search.status !== 'idle';

  return (
    <form
      className="search-wrap"
      role="search"
      onSubmit={handleSubmit}
      onFocus={() => setIsOpen(true)}
      onBlur={handleBlur}
      onKeyDown={handleKeyDown}
    >
      <img src={mapPinIcon} alt="" className="search-pin" />
      <label className="visually-hidden" htmlFor="location-search">
        Search Location
      </label>
      <input
        id="location-search"
        type="search"
        value={text}
        onChange={handleChange}
        maxLength={MAX_SEARCH_LENGTH}
        placeholder="Search Location"
        autoComplete="off"
      />
      <button
        type="submit"
        aria-label={busy ? 'Searching' : 'Search locations'}
        disabled={!trimmed}
        aria-disabled={busy}
        onMouseDown={(event) => event.preventDefault()}
      >
        <img src={searchIcon} alt="" />
      </button>

      {showDropdown && (
        <div className="search-results">
          {search.status === 'loading' && <p>Searching...</p>}

          {search.status === 'error' && <p className="search-error">{search.message}</p>}

          {search.status === 'done' && search.places.length === 0 && (
            <p>No places found for "{search.query}".</p>
          )}

          {search.status === 'done' && search.places.length > 0 && (
            <ul>
              {search.places.map((place) => (
                <li key={place.id}>
                  <button
                    type="button"
                    onMouseDown={(event) => event.preventDefault()}
                    onClick={() => handleSelect(place)}
                  >
                    {place.label ?? `${place.lat.toFixed(5)}, ${place.lon.toFixed(5)}`}
                  </button>
                </li>
              ))}
            </ul>
          )}
        </div>
      )}
    </form>
  );
};

export default SidebarSearch;
