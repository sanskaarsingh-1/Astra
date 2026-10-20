'use client';

import React, {
  createContext,
  useContext,
  useEffect,
  useRef,
  useCallback,
  useState,
} from 'react';
import { useRouter, usePathname } from 'next/navigation';
import gsap from 'gsap';

interface ViewTransitionContextType {
  navigate: (url: string) => void;
  navigateWithIris: (url: string) => void;
  isTransitioning: boolean;
}

const ViewTransitionContext = createContext<ViewTransitionContextType>({
  navigate: () => {},
  navigateWithIris: () => {},
  isTransitioning: false,
});

export const useViewTransition = () => useContext(ViewTransitionContext);
export const useIrisTransition = useViewTransition;
export const usePageTransition = useViewTransition;

export default function PageTransition() {
  const router = useRouter();
  const pathname = usePathname();

  const containerRef = useRef<HTMLDivElement | null>(null);
  const circleRef = useRef<HTMLDivElement | null>(null);
  const isTransitioningRef = useRef(false);
  const [isTransitioning, setIsTransitioning] = useState(false);

  // Initial cinematic circular reveal on first load
  useEffect(() => {
    if (typeof window === 'undefined') return;
    const prefersReduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    if (prefersReduced || !circleRef.current || !containerRef.current) return;

    gsap.set(containerRef.current, { display: 'flex' });
    gsap.fromTo(
      circleRef.current,
      { scale: 0.1, opacity: 0.95 },
      {
        scale: 30,
        opacity: 0,
        duration: 0.85,
        ease: 'power2.out',
        onComplete: () => {
          if (containerRef.current) {
            gsap.set(containerRef.current, { display: 'none' });
          }
        },
      }
    );
  }, []);

  // When pathname changes after navigation, smoothly disperse the expanding circle
  useEffect(() => {
    if (!isTransitioningRef.current || !circleRef.current || !containerRef.current) return;

    gsap.fromTo(
      circleRef.current,
      { scale: 4, opacity: 1 },
      {
        scale: 35,
        opacity: 0,
        duration: 0.8,
        ease: 'power2.out',
        onComplete: () => {
          if (containerRef.current) {
            gsap.set(containerRef.current, { display: 'none' });
          }
          isTransitioningRef.current = false;
          setIsTransitioning(false);
        },
      }
    );
  }, [pathname]);

  // Navigate handler with slower, clearly visible expanding white glassmorphic circle
  const navigate = useCallback(
    (targetUrl: string) => {
      if (isTransitioningRef.current) return;
      if (!circleRef.current || !containerRef.current) {
        router.push(targetUrl);
        return;
      }

      const prefersReduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
      if (prefersReduced) {
        router.push(targetUrl);
        return;
      }

      isTransitioningRef.current = true;
      setIsTransitioning(true);

      gsap.set(containerRef.current, { display: 'flex' });

      // Slower cinematic spread: circle blooms visibly from center to cover the screen
      gsap.fromTo(
        circleRef.current,
        { scale: 0, opacity: 0.2 },
        {
          scale: 20,
          opacity: 1,
          duration: 0.65,
          ease: 'power2.inOut',
          onComplete: () => {
            router.push(targetUrl);
          },
        }
      );
    },
    [router]
  );

  // Global Internal Link Click Interceptor
  useEffect(() => {
    const handleDocumentClick = (e: MouseEvent) => {
      if (e.defaultPrevented || e.button !== 0) return;
      if (e.ctrlKey || e.metaKey || e.shiftKey || e.altKey) return;

      const anchor = (e.target as HTMLElement)?.closest('a');
      if (!anchor) return;

      if (
        anchor.target === '_blank' ||
        anchor.hasAttribute('download') ||
        anchor.getAttribute('rel')?.includes('external')
      ) {
        return;
      }

      const href = anchor.getAttribute('href');
      if (!href) return;

      if (
        href.startsWith('mailto:') ||
        href.startsWith('tel:') ||
        href.startsWith('javascript:')
      ) {
        return;
      }

      const currentPath = window.location.pathname;
      if (href.startsWith('#')) return;
      if (href.startsWith('/#') && (currentPath === '/' || currentPath === '')) {
        return;
      }

      try {
        const target = new URL(href, window.location.origin);
        if (target.origin !== window.location.origin) return;

        // Same URL with hash change: allow normal anchor scroll
        if (
          target.pathname === window.location.pathname &&
          target.search === window.location.search &&
          target.hash
        ) {
          return;
        }

        // Same exact URL: ignore redundant click
        if (
          target.pathname === window.location.pathname &&
          target.search === window.location.search &&
          !target.hash
        ) {
          e.preventDefault();
          return;
        }

        e.preventDefault();
        navigate(target.pathname + target.search + target.hash);
      } catch {
        // Fallback to standard browser navigation
      }
    };

    document.addEventListener('click', handleDocumentClick, { capture: true });
    return () => {
      document.removeEventListener('click', handleDocumentClick, { capture: true });
    };
  }, [navigate]);

  return (
    <ViewTransitionContext.Provider
      value={{
        navigate: (url) => navigate(url),
        navigateWithIris: (url) => navigate(url),
        isTransitioning,
      }}
    >
      {/* ── FULL-SCREEN CENTERED CONTAINER FOR EXPANDING CIRCLE ── */}
      <div
        ref={containerRef}
        aria-hidden="true"
        className="fixed inset-0 z-[99999] pointer-events-none select-none flex items-center justify-center overflow-hidden hidden"
      >
        {/* White Subtle Glassmorphic Blurry Expanding Circle */}
        <div
          ref={circleRef}
          className="size-48 rounded-full pointer-events-none will-change-transform border border-white/60 shadow-[0_0_120px_50px_rgba(255,255,255,0.3),inset_0_0_80px_rgba(255,255,255,0.2)]"
          style={{
            background:
              'radial-gradient(circle, rgba(255,255,255,0.22) 0%, rgba(255,255,255,0.1) 45%, rgba(255,255,255,0.02) 75%, transparent 100%)',
            backdropFilter: 'blur(20px)',
            WebkitBackdropFilter: 'blur(20px)',
          }}
        />
      </div>
    </ViewTransitionContext.Provider>
  );
}
