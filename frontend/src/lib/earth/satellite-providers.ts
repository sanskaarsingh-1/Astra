/**
 * Astra Earth View — Satellite Imagery & Basemap Provider Abstraction
 * 
 * Legitimate, keyless public geospatial raster providers with graceful fallback hierarchy.
 * Complies with strict security and attribution invariants.
 */

export interface ImageryProviderConfig {
  id: string;
  name: string;
  category: 'satellite' | 'street' | 'dark';
  attribution: string;
  tiles: string[];
  tileSize: number;
  minZoom: number;
  maxZoom: number;
  requiresKey: boolean;
  isKeyConfigured?: boolean;
  description: string;
  termsUrl: string;
}

export const SATELLITE_IMAGERY_PROVIDERS: Record<string, ImageryProviderConfig> = {
  // 1. Primary Real High-Resolution Global Satellite Imagery (Sub-meter, Keyless)
  esri_world_imagery: {
    id: 'esri_world_imagery',
    name: 'Esri World Imagery',
    category: 'satellite',
    attribution: '© Esri, Maxar, Earthstar Geographics, CNES/Airbus DS, USDA FSA, USGS, Aerogrid, IGN, IGP, and the GIS User Community',
    tiles: [
      'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
    ],
    tileSize: 256,
    minZoom: 0,
    maxZoom: 19,
    requiresKey: false,
    description: 'High-resolution global optical satellite photography from 15m global down to 0.3m sub-meter resolution.',
    termsUrl: 'https://www.esri.com/en-us/legal/terms/full-master-agreement',
  },

  // 2. NASA GIBS MODIS Terra Daily True Color (Public Scientific Earth Observation)
  nasa_gibs_modis: {
    id: 'nasa_gibs_modis',
    name: 'NASA GIBS MODIS (True Color)',
    category: 'satellite',
    attribution: 'Imagery courtesy of NASA EOSDIS Worldview / Global Imagery Browse Services (GIBS)',
    tiles: [
      'https://gibs.earthdata.nasa.gov/wmts/epsg3857/best/MODIS_Terra_CorrectedReflectance_TrueColor/default/default/GoogleMapsCompatible_Level9/{z}/{y}/{x}.jpg',
    ],
    tileSize: 256,
    minZoom: 0,
    maxZoom: 9,
    requiresKey: false,
    description: 'Daily global true-color satellite observation from NASA Terra satellite showing true planetary weather and aerosol conditions.',
    termsUrl: 'https://www.earthdata.nasa.gov/engage/open-data-policy',
  },

  // 3. 2D Operational Baseline: OpenStreetMap Standard (Public Community Basemap)
  openstreetmap: {
    id: 'openstreetmap',
    name: 'OpenStreetMap Standard',
    category: 'street',
    attribution: '© OpenStreetMap contributors',
    tiles: [
      'https://a.tile.openstreetmap.org/{z}/{x}/{y}.png',
      'https://b.tile.openstreetmap.org/{z}/{x}/{y}.png',
      'https://c.tile.openstreetmap.org/{z}/{x}/{y}.png',
    ],
    tileSize: 256,
    minZoom: 0,
    maxZoom: 19,
    requiresKey: false,
    description: 'Community-driven open world map with comprehensive international borders, cities, transport, and coastlines.',
    termsUrl: 'https://www.openstreetmap.org/copyright',
  },

  // 4. 3D Tactical Baseline: Esri World Dark Gray Canvas
  esri_dark_gray: {
    id: 'esri_dark_gray',
    name: 'Esri Dark Gray Canvas',
    category: 'dark',
    attribution: '© Esri, DeLorme, NAVTEQ',
    tiles: [
      'https://server.arcgisonline.com/ArcGIS/rest/services/Canvas/World_Dark_Gray_Base/MapServer/tile/{z}/{y}/{x}',
    ],
    tileSize: 256,
    minZoom: 0,
    maxZoom: 16,
    requiresKey: false,
    description: 'Minimalist dark operational basemap designed specifically to highlight real-time tactical intelligence layers.',
    termsUrl: 'https://www.esri.com/en-us/legal/terms/full-master-agreement',
  },
};

/**
 * Provider Fallback Resolver
 * Returns the highest-priority operational tile source for a given display mode.
 * Note: CARTO is not used or required; 2D mode is strictly OpenStreetMap (optional zero-key baseline).
 */
export function getProviderForMode(mode: '2d' | '3d' | 'satellite'): ImageryProviderConfig {
  if (mode === 'satellite') {
    return SATELLITE_IMAGERY_PROVIDERS.esri_world_imagery;
  }
  if (mode === '2d') {
    return SATELLITE_IMAGERY_PROVIDERS.openstreetmap;
  }
  // 3d globe mode default
  return SATELLITE_IMAGERY_PROVIDERS.esri_dark_gray;
}
