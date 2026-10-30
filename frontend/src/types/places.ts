export interface Places {
    id: number;
    lat: number;
    lon: number;
    label: string | null;
    bounds: [[number, number], [number, number]]
}

export interface MapSearchResponse {
    results: Places[];
}