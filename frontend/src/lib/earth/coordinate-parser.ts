/**
 * Astra AI — Geospatial Coordinate Parser
 * 
 * Supports:
 * - Decimal Degrees: "18.5204, 73.8567", "18.5204 73.8567", "18.5204,73.8567"
 * - Directional notation: "18.5204° N, 73.8567° E", "18.5204N, 73.8567E", "33.8688 S, 151.2093 E", "37.7749 N, 122.4194 W"
 * - Reverse directional: "122.4194 W, 37.7749 N"
 * - Labeled inputs: "lat: 18.5204, lng: 73.8567", "latitude: 18.52, longitude: 73.85", "lat=18.52, lon=73.85"
 * - Bracketed/parenthesized: "[18.5204, 73.8567]", "(18.5204, 73.8567)"
 * - Longitude-first automatic inversion: e.g. "122.4194, 37.7749" or "77.2090, 28.6139" (if first magnitude > 90 and second <= 90)
 * - Optional custom zoom: "18.5204, 73.8567, 14", "18.5204, 73.8567 z14", "18.5204, 73.8567 @15"
 */

export interface ParsedCoordinates {
  lat: number;
  lng: number;
  zoom: number;
}

const DEFAULT_TARGET_ZOOM = 13.5;

export function parseCoordinates(input: string): ParsedCoordinates | null {
  if (!input) return null;
  const raw = input.trim();
  if (!raw) return null;

  let clean = raw;
  let customZoom: number | undefined;

  // Check for explicit zoom suffixes: e.g. ", 14", " z14", " z=14", " @14", " zoom 14"
  const zoomSuffixMatch = clean.match(/(?:[,\s]+(?:z(?:oom)?\s*[:=]?\s*|@\s*))(\d{1,2}(?:\.\d+)?)$/i);
  if (zoomSuffixMatch) {
    const parsedZoom = parseFloat(zoomSuffixMatch[1]);
    if (!isNaN(parsedZoom) && parsedZoom >= 1 && parsedZoom <= 20) {
      customZoom = parsedZoom;
    }
    clean = clean.substring(0, zoomSuffixMatch.index).trim();
  }

  // 1. Directional coordinates: e.g. 28.6139° N, 77.2090° E or 28.6139N 77.2090E
  const dirPatternLatFirst = /^\[?\(?\s*([+-]?\d+(?:\.\d+)?)\s*°?\s*([NSns])\s*[,;\s]+\s*([+-]?\d+(?:\.\d+)?)\s*°?\s*([EWew])\s*\)?\]?$/;
  const dirMatch = clean.match(dirPatternLatFirst);
  if (dirMatch) {
    let lat = parseFloat(dirMatch[1]);
    if (dirMatch[2].toUpperCase() === 'S') lat = -Math.abs(lat);
    let lng = parseFloat(dirMatch[3]);
    if (dirMatch[4].toUpperCase() === 'W') lng = -Math.abs(lng);

    if (Math.abs(lat) <= 90 && Math.abs(lng) <= 180) {
      return { lat, lng, zoom: customZoom || DEFAULT_TARGET_ZOOM };
    }
  }

  // Directional coordinates with Longitude first: e.g. 77.2090° E, 28.6139° N
  const dirPatternLngFirst = /^\[?\(?\s*([+-]?\d+(?:\.\d+)?)\s*°?\s*([EWew])\s*[,;\s]+\s*([+-]?\d+(?:\.\d+)?)\s*°?\s*([NSns])\s*\)?\]?$/;
  const revDirMatch = clean.match(dirPatternLngFirst);
  if (revDirMatch) {
    let lng = parseFloat(revDirMatch[1]);
    if (revDirMatch[2].toUpperCase() === 'W') lng = -Math.abs(lng);
    let lat = parseFloat(revDirMatch[3]);
    if (revDirMatch[4].toUpperCase() === 'S') lat = -Math.abs(lat);

    if (Math.abs(lat) <= 90 && Math.abs(lng) <= 180) {
      return { lat, lng, zoom: customZoom || DEFAULT_TARGET_ZOOM };
    }
  }

  // 2. Labeled coordinates: e.g. "lat: 18.5204, lng: 73.8567" or "latitude=18.52, longitude=73.85"
  const labeledPattern = /lat(?:itude)?\s*[:=]?\s*([+-]?\d+(?:\.\d+)?)\s*[,;\s]+\s*(?:lon(?:gitude)?|lng)\s*[:=]?\s*([+-]?\d+(?:\.\d+)?)/i;
  const labeledMatch = clean.match(labeledPattern);
  if (labeledMatch) {
    const lat = parseFloat(labeledMatch[1]);
    const lng = parseFloat(labeledMatch[2]);
    if (Math.abs(lat) <= 90 && Math.abs(lng) <= 180) {
      return { lat, lng, zoom: customZoom || DEFAULT_TARGET_ZOOM };
    }
  }

  // Labeled coordinates reversed: e.g. "lon: 73.8567, lat: 18.5204"
  const revLabeledPattern = /(?:lon(?:gitude)?|lng)\s*[:=]?\s*([+-]?\d+(?:\.\d+)?)\s*[,;\s]+\s*lat(?:itude)?\s*[:=]?\s*([+-]?\d+(?:\.\d+)?)/i;
  const revLabeledMatch = clean.match(revLabeledPattern);
  if (revLabeledMatch) {
    const lng = parseFloat(revLabeledMatch[1]);
    const lat = parseFloat(revLabeledMatch[2]);
    if (Math.abs(lat) <= 90 && Math.abs(lng) <= 180) {
      return { lat, lng, zoom: customZoom || DEFAULT_TARGET_ZOOM };
    }
  }

  // 3. Numeric coordinates with optional delimiters, brackets, parentheses
  // Remove enclosing brackets [], {}, ()
  const stripped = clean.replace(/^[\[\(\{]/, '').replace(/[\]\)\}]$/, '').trim();
  const tokens = stripped
    .split(/[,;\s]+/)
    .map((t) => t.replace(/°/g, '').trim())
    .filter(Boolean);

  if (tokens.length >= 2 && tokens.length <= 3) {
    const v1 = parseFloat(tokens[0]);
    const v2 = parseFloat(tokens[1]);

    if (!isNaN(v1) && !isNaN(v2)) {
      if (tokens.length === 3 && customZoom === undefined) {
        const v3 = parseFloat(tokens[2]);
        if (!isNaN(v3) && v3 >= 1 && v3 <= 20) {
          customZoom = v3;
        }
      }

      // Check standard [lat, lng]
      if (Math.abs(v1) <= 90 && Math.abs(v2) <= 180) {
        return { lat: v1, lng: v2, zoom: customZoom || DEFAULT_TARGET_ZOOM };
      }

      // Check reversed [lng, lat] (if first coordinate magnitude > 90 and <= 180, it must be longitude)
      if (Math.abs(v1) <= 180 && Math.abs(v2) <= 90) {
        return { lat: v2, lng: v1, zoom: customZoom || DEFAULT_TARGET_ZOOM };
      }
    }
  }

  return null;
}
