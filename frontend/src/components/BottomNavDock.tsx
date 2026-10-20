'use client';

import React, { useState, useEffect } from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { Home, Target, Globe, Layers } from 'lucide-react';

export default function BottomNavDock() {
  const pathname = usePathname();
  const [activeItem, setActiveItem] = useState<string>('home');

  // Active item tracking based on current pathname
  useEffect(() => {
    if (pathname === '/mission') {
      setActiveItem('mission');
    } else if (pathname === '/earth' || pathname === '/earth-view') {
      setActiveItem('earth');
    } else if (pathname === '/analyze') {
      setActiveItem('analyze');
    } else {
      setActiveItem('home');
    }
  }, [pathname]);

  const items = [
    {
      id: 'home',
      label: 'Home',
      icon: Home,
      href: '/',
      onClick: (e: React.MouseEvent) => {
        if (pathname === '/') {
          e.preventDefault();
          window.scrollTo({ top: 0, behavior: 'smooth' });
          setActiveItem('home');
        }
      },
    },
    {
      id: 'analyze',
      label: 'Analyze',
      icon: Layers,
      href: '/analyze',
    },
    {
      id: 'earth',
      label: 'Earth',
      icon: Globe,
      href: '/earth',
    },
    {
      id: 'mission',
      label: 'Mission',
      icon: Target,
      href: '/mission',
    },
  ];

  return (
    <nav
      aria-label="Navigation Dock"
      className="fixed right-3 sm:right-6 top-1/2 -translate-y-1/2 z-50 pointer-events-auto select-none"
    >
      <div className="flex flex-col items-center gap-2.5 sm:gap-3 rounded-full bg-neutral-900/85 py-3 px-2 shadow-2xl ring-1 ring-white/10 backdrop-blur-xl sm:py-4 sm:px-2.5">
        {items.map((item) => {
          const Icon = item.icon;
          const isActive = activeItem === item.id;

          return (
            <Link
              key={item.id}
              href={item.href}
              onClick={item.onClick}
              aria-label={item.label}
              className={`group relative grid h-10 w-10 sm:h-12 sm:w-12 place-items-center rounded-2xl ring-1 transition-all duration-200 hover:-translate-x-0.5 active:scale-95 ${
                isActive
                  ? 'bg-white/15 ring-white/25 text-white shadow-sm'
                  : 'bg-white/5 ring-white/10 text-zinc-400 hover:text-white hover:bg-white/10'
              }`}
            >
              <Icon
                className="h-5 w-5 transition-transform duration-200"
                strokeWidth={2}
              />
              {/* Subtle active indicator dot */}
              {isActive && (
                <span className="absolute -left-1 size-1.5 rounded-full bg-white" />
              )}

              {/* Floating Tooltip to the left */}
              <span className="absolute right-full mr-3 px-2.5 py-1 rounded-md bg-zinc-900 border border-white/10 text-xs font-body text-white opacity-0 group-hover:opacity-100 transition-all duration-200 pointer-events-none whitespace-nowrap shadow-xl backdrop-blur-md translate-x-1 group-hover:translate-x-0 hidden sm:block">
                {item.label}
              </span>
            </Link>
          );
        })}
      </div>
    </nav>
  );
}
