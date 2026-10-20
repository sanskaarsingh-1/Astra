/**
 * Astra AI Earth View — Satellite Orbit Propagation
 * Derived from OSIRIS (MIT Licensed - Copyright (c) 2026 simplifaisoul)
 * Uses satellite.js SGP4/SDP4 to calculate real geodetic positions and ground tracks.
 */

import * as satellite from 'satellite.js';

export interface SatPosition {
  lat: number;
  lng: number;
  altKm: number;
}

/** Longitude wrapped to [-180, 180]. */
export function wrapLongitude(deg: number): number {
  return ((((deg + 180) % 360) + 360) % 360) - 180;
}

/**
 * Propagates one TLE to a given Date using SGP4.
 * Returns null if the satellite has re-entered or error occurs.
 */
export function propagateTLE(line1: string, line2: string, when: Date = new Date()): SatPosition | null {
  try {
    const satrec = satellite.twoline2satrec(line1, line2);
    if (!satrec || (satrec as any).error) return null;

    const positionAndVelocity = satellite.propagate(satrec, when);
    const positionEci = positionAndVelocity?.position;
    if (!positionEci || typeof positionEci === 'boolean') return null;

    const gmst = satellite.gstime(when);
    const geodetic = satellite.eciToGeodetic(positionEci, gmst);
    const lat = satellite.degreesLat(geodetic.latitude);
    const lng = wrapLongitude(satellite.degreesLong(geodetic.longitude));
    const altKm = geodetic.height;

    if (!Number.isFinite(lat) || !Number.isFinite(lng) || !Number.isFinite(altKm)) return null;
    if (altKm < 80 || altKm > 60000) return null;

    return { lat, lng, altKm };
  } catch {
    return null;
  }
}

/** Orbital period in minutes from mean motion */
export function orbitalPeriodMinutes(line2: string): number | null {
  const meanMotion = parseFloat(line2.substring(52, 63));
  if (!Number.isFinite(meanMotion) || meanMotion <= 0) return null;
  return 1440 / meanMotion;
}

/**
 * Samples one full revolution around the Earth starting from now.
 */
export function orbitPath(line1: string, line2: string, steps = 120, from: Date = new Date()): SatPosition[] {
  const period = orbitalPeriodMinutes(line2);
  if (!period) return [];
  const out: SatPosition[] = [];
  for (let i = 0; i <= steps; i++) {
    const when = new Date(from.getTime() + (period * 60_000 * i) / steps);
    const p = propagateTLE(line1, line2, when);
    if (p) out.push(p);
  }
  return out;
}

/** Splits ground track whenever it crosses the antimeridian (-180 / +180) */
export function splitAtAntimeridian(path: SatPosition[]): SatPosition[][] {
  if (path.length === 0) return [];
  const runs: SatPosition[][] = [];
  let run: SatPosition[] = [path[0]];
  for (let i = 1; i < path.length; i++) {
    if (Math.abs(path[i].lng - path[i - 1].lng) > 180) {
      runs.push(run);
      run = [];
    }
    run.push(path[i]);
  }
  if (run.length) runs.push(run);
  return runs.filter(r => r.length > 1);
}
