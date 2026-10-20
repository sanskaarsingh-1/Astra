/**
 * Astra AI — Runtime API URL Resolution
 *
 * Priority (highest to lowest):
 *   1. localStorage["ASTRA_API_URL"]  — set via admin panel or browser console
 *   2. NEXT_PUBLIC_API_URL              — baked in at build time
 *   3. "http://localhost:8000"          — local dev fallback
 *
 * This allows the deployed Firebase site to point to the current Cloudflare
 * tunnel URL without requiring a rebuild/redeploy. Just open the browser
 * console on the deployed site and run:
 *   localStorage.setItem('ASTRA_API_URL', 'https://your-tunnel.trycloudflare.com')
 *   location.reload()
 */
export function getApiUrl(): string {
  // Check localStorage at runtime (works in browser, not during SSR)
  if (typeof window !== "undefined") {
    const stored = window.localStorage.getItem("ASTRA_API_URL");
    if (stored && stored.startsWith("http")) {
      return stored.replace(/\/$/, ""); // strip trailing slash
    }
  }
  // Fall back to build-time env var, then local dev default
  return (process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000").replace(/\/$/, "");
}

/**
 * Set the backend URL at runtime (persists across page reloads).
 * Call from browser console: setAstraApiUrl('https://xxx.trycloudflare.com')
 */
export function setApiUrl(url: string): void {
  if (typeof window !== "undefined") {
    window.localStorage.setItem("ASTRA_API_URL", url.replace(/\/$/, ""));
    console.log(`[Astra] Backend URL set to: ${url}`);
    console.log("[Astra] Reload the page to apply.");
  }
}

// Expose to browser console for easy tunnel URL switching
if (typeof window !== "undefined") {
  (window as any).setAstraApiUrl = setApiUrl;
  (window as any).getAstraApiUrl = getApiUrl;
}
