import type { Places, MapSearchResponse } from "../types/places";

export async function searchMap(search_query: string, signal?: AbortSignal): Promise<Places[]> {
    const params = new URLSearchParams({ q: search_query });
    const res = await fetch(`/api/geocode/search?${params}`, { signal });

    let body: unknown = null;
    try {
        body = await res.json();
    } catch {

    }

    if (!res.ok) {
        const message =
            body && typeof body === 'object' && 'error' in body && typeof body.error === 'string'
                ? body.error
                : `Search failed (HTTP ${res.status}).`;
        throw new Error (message);
    }

    if (!body || !Array.isArray((body as MapSearchResponse).results)) {
        throw new Error('Unexpected response from the server.');
    }
    return (body as MapSearchResponse).results;
}