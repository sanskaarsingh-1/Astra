'use client';

import React, { useEffect, useRef, useState, useCallback } from 'react';
import { geoOrthographic, geoPath, geoGraticule } from 'd3-geo';

interface RotatingEarthCanvasProps {
  onLocationSelect?: (coords: { lat: number; lng: number }) => void;
  className?: string;
  autoRotateSpeed?: number; // degrees per frame
}

export default function RotatingEarthCanvas({
  onLocationSelect,
  className = '',
  autoRotateSpeed = 0.25,
}: RotatingEarthCanvasProps) {
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const containerRef = useRef<HTMLDivElement | null>(null);

  // Rotation state [yaw (longitude), pitch (latitude), roll]
  const rotationRef = useRef<[number, number, number]>([78.96, -20.59, 0]); // Centered on India
  const isDraggingRef = useRef(false);
  const previousMouseRef = useRef<{ x: number; y: number } | null>(null);
  const zoomScaleRef = useRef(1);
  const autoRotateRef = useRef(true);
  const landDataRef = useRef<any>(null);

  const [isLoading, setIsLoading] = useState(true);
  const [isAutoRotating, setIsAutoRotating] = useState(true);

  // Fetch Natural Earth 110m Land GeoJSON with AbortController
  useEffect(() => {
    const controller = new AbortController();

    async function loadLand() {
      try {
        const res = await fetch(
          'https://raw.githubusercontent.com/nvkelso/natural-earth-vector/master/geojson/ne_110m_land.geojson',
          { signal: controller.signal }
        );
        if (!res.ok) throw new Error(`HTTP error ${res.status}`);
        const data = await res.json();
        landDataRef.current = data;
        setIsLoading(false);
      } catch (err: any) {
        if (err.name === 'AbortError') return;
        // Fallback: minimal built-in continents GeoJSON polygon so it always renders
        landDataRef.current = {
          type: 'FeatureCollection',
          features: [],
        };
        setIsLoading(false);
      }
    }

    loadLand();
    return () => controller.abort();
  }, []);

  // Main Canvas Render Loop
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    let animId: number;

    const render = () => {
      const width = canvas.clientWidth || 600;
      const height = canvas.clientHeight || 600;
      const dpr = window.devicePixelRatio || 1;

      if (canvas.width !== width * dpr || canvas.height !== height * dpr) {
        canvas.width = width * dpr;
        canvas.height = height * dpr;
      }

      ctx.save();
      ctx.scale(dpr, dpr);
      ctx.clearRect(0, 0, width, height);

      // Auto-rotation when not user-dragging
      if (autoRotateRef.current && !isDraggingRef.current) {
        rotationRef.current[0] += autoRotateSpeed;
      }

      const radius = (Math.min(width, height) / 2 - 24) * zoomScaleRef.current;
      const projection = geoOrthographic()
        .scale(radius)
        .translate([width / 2, height / 2])
        .rotate(rotationRef.current)
        .clipAngle(90);

      const path = geoPath(projection, ctx);

      // 1. Globe Background (Dark Sphere with Atmosphere Glow)
      ctx.beginPath();
      ctx.arc(width / 2, height / 2, radius, 0, Math.PI * 2);
      ctx.fillStyle = '#09090b';
      ctx.fill();

      // Atmospheric Outer Ring
      ctx.lineWidth = 2;
      ctx.strokeStyle = 'rgba(16, 185, 129, 0.4)';
      ctx.stroke();

      // Subtle Inner Shadow
      const gradient = ctx.createRadialGradient(
        width / 2 - radius * 0.3,
        height / 2 - radius * 0.3,
        radius * 0.1,
        width / 2,
        height / 2,
        radius
      );
      gradient.addColorStop(0, 'rgba(16, 185, 129, 0.05)');
      gradient.addColorStop(0.7, 'rgba(0, 0, 0, 0.4)');
      gradient.addColorStop(1, 'rgba(0, 0, 0, 0.85)');
      ctx.fillStyle = gradient;
      ctx.fill();

      // 2. Graticule (Latitude / Longitude Grid)
      const graticule = geoGraticule().step([15, 15]);
      ctx.beginPath();
      path(graticule());
      ctx.strokeStyle = 'rgba(255, 255, 255, 0.06)';
      ctx.lineWidth = 0.75;
      ctx.stroke();

      // 3. Render Land Masses & Outlines
      if (landDataRef.current) {
        // Continent Fill
        ctx.beginPath();
        path(landDataRef.current);
        ctx.fillStyle = 'rgba(255, 255, 255, 0.1)';
        ctx.fill();

        // Continent Crisp Boundaries
        ctx.lineWidth = 1;
        ctx.strokeStyle = 'rgba(255, 255, 255, 0.5)';
        ctx.stroke();
      }

      // 4. Center Crosshair / Tactical Sight
      ctx.strokeStyle = 'rgba(16, 185, 129, 0.3)';
      ctx.lineWidth = 1;
      ctx.beginPath();
      ctx.moveTo(width / 2 - 12, height / 2);
      ctx.lineTo(width / 2 + 12, height / 2);
      ctx.moveTo(width / 2, height / 2 - 12);
      ctx.lineTo(width / 2, height / 2 + 12);
      ctx.stroke();

      ctx.restore();
      animId = requestAnimationFrame(render);
    };

    animId = requestAnimationFrame(render);
    return () => cancelAnimationFrame(animId);
  }, [autoRotateSpeed]);

  // Mouse Drag Handlers for Smooth Interactive Rotation
  const handleMouseDown = useCallback((e: React.MouseEvent<HTMLCanvasElement>) => {
    isDraggingRef.current = true;
    previousMouseRef.current = { x: e.clientX, y: e.clientY };
  }, []);

  const handleMouseMove = useCallback((e: React.MouseEvent<HTMLCanvasElement>) => {
    if (!isDraggingRef.current || !previousMouseRef.current) return;
    const dx = e.clientX - previousMouseRef.current.x;
    const dy = e.clientY - previousMouseRef.current.y;

    const sensitivity = 0.35 / zoomScaleRef.current;
    rotationRef.current[0] += dx * sensitivity;
    rotationRef.current[1] = Math.max(-85, Math.min(85, rotationRef.current[1] - dy * sensitivity));

    previousMouseRef.current = { x: e.clientX, y: e.clientY };
  }, []);

  const handleMouseUp = useCallback(() => {
    isDraggingRef.current = false;
    previousMouseRef.current = null;
  }, []);

  // Mouse Wheel Zoom Handler
  const handleWheel = useCallback((e: React.WheelEvent<HTMLCanvasElement>) => {
    e.preventDefault();
    const delta = -e.deltaY * 0.0015;
    zoomScaleRef.current = Math.max(0.6, Math.min(3.5, zoomScaleRef.current + delta));
  }, []);

  const toggleAutoRotate = () => {
    autoRotateRef.current = !autoRotateRef.current;
    setIsAutoRotating(autoRotateRef.current);
  };

  return (
    <div
      ref={containerRef}
      className={`relative w-full h-full flex items-center justify-center overflow-hidden bg-black select-none ${className}`}
    >
      <canvas
        ref={canvasRef}
        onMouseDown={handleMouseDown}
        onMouseMove={handleMouseMove}
        onMouseUp={handleMouseUp}
        onMouseLeave={handleMouseUp}
        onWheel={handleWheel}
        className="w-full h-full cursor-grab active:cursor-grabbing"
      />

      {/* Floating Controls for D3 Globe */}
      <div className="absolute bottom-6 left-6 flex items-center gap-2 bg-zinc-950/80 backdrop-blur-md border border-white/10 rounded-xl p-1.5 shadow-2xl">
        <button
          type="button"
          onClick={toggleAutoRotate}
          className="px-3 py-1 rounded-lg text-xs font-mono text-zinc-300 hover:text-white hover:bg-white/10 transition-colors"
        >
          {isAutoRotating ? 'PAUSE ROTATION' : 'RESUME ROTATION'}
        </button>
        <button
          type="button"
          onClick={() => {
            zoomScaleRef.current = 1;
            rotationRef.current = [78.96, -20.59, 0];
          }}
          className="px-2.5 py-1 rounded-lg text-xs font-mono text-zinc-400 hover:text-white hover:bg-white/10 transition-colors"
        >
          RESET
        </button>
      </div>

      {isLoading && (
        <div className="absolute inset-0 flex items-center justify-center bg-black/60 pointer-events-none">
          <div className="size-6 rounded-full border-2 border-emerald-500 border-t-transparent animate-spin" />
        </div>
      )}
    </div>
  );
}
