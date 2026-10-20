# Character Wave — What We Did & How It Works

Single-file interactive team showcase in `frontend/index.html` + photos in `frontend/images/`.
Run: `python3 -m http.server 8000` from `frontend/`, open `http://localhost:8000`.

## What we changed in this session

1. **Ran the site locally**
   - Started `python3 -m http.server 8000` in `frontend/`. No build step — plain HTML/CSS/JS.
   - Verified `index.html` (200) and all images in `images/` (200).

2. **Wired "Follow me" portfolio links (`PORTFOLIOS` map)**
   - Shrishti Malhotra → `https://srishti-portfolio-phi.vercel.app/`
   - Tejas Patil → `https://portfolio-flame-ten-50.vercel.app/`
   - Already present: Tushar (`tushar-portfolio-dev.web.app`), Trishika (`trishika-negi-portfolio.web.app`).
   - How it behaves: on the wave, clicking the `Follow me` pill on a card opens that member's portfolio in a new tab (`window.open`). In the detail view, the `Follow me` button links to the same URL via `setFollow()`. Members without an entry get a dimmed, non-clickable button (`aria-disabled="true"`).

3. **Uploaded Shrishti's photo**
   - Saved clipboard image to `images/shrishti-malhotra.png` (294×380 PNG).
   - Added `portraits.shrishti = "images/shrishti-malhotra.png"`.
   - Before, Shrishti used a large embedded base64 placeholder. Now both the wave card and detail view load the real file.

4. **Replaced YouTube button with Gmail (everyone)**
   - HTML: `socialYoutube` → `socialGmail`, YouTube play SVG → mail envelope SVG, `aria-label="Gmail"`.
   - CSS: `.squircle-yt` (dark red) → `.squircle-mail` (Gmail red gradient).
   - JS: `socialYoutube` variable → `socialGmail`, `SOCIALS` keys `youtube` → `gmail`. `applySocials()` reads `links.gmail || links.youtube` so old data still works.

5. **Wired work emails to Gmail buttons (`SOCIALS` map)**
   - Tejas → `mailto:tejasworkolo@gmail.com`
   - Shrishti → `mailto:malhotrashrishti2310@gmail.com`
   - Tushar → `mailto:tusharmali7726@gmail.com`
   - Trishika → `mailto:trishikaneg@gmail.com`
   - Clicking Gmail opens the user's mail client to that address.
   - Improved `setSocial()`: `mailto:` links drop `target="_blank"` (avoids a stray blank tab); normal https links keep `target="_blank"`.

## How the app works (overview, not line-by-line)

**Structure:** one `index.html` with embedded `<style>` and `<script>`. Three layers:

- **Wave (`#stage` > `#deck` > `.card` buttons):** 11 cards generated from the `profiles` array (name, role, color, portrait key, contribution). A `requestAnimationFrame` render loop positions every card in 3D each frame from a single `state.phase` value.
  - `wrappedDelta()` / `nearestIndex()` handle the infinite wrap-around so scrolling past the end loops back.
  - Pointer X/Y drives `targetPhase` (scrub through the wave) plus tilt and a radial highlight (`--pointer-x/y`). Wheel and arrow keys step `basePhase`. Double-click / Space toggles `orientation` (horizontal vs vertical layout). After ~4s idle, an auto-drift sine animation takes over.
  - Per-card style per frame: position (X/Y/Z), scale, rotateX/Y/Z, opacity, blur, and `--focus` (used for shadow/border glow). Focused card is sharp, large, front; distant cards shrink, fade, blur.
- **Detail view (`#detail`):** hidden overlay. `openDetailByProfile()` fills name, big card, role pill, contribution text, socials, Follow link, and the "All members" strip (`uniqueTeam()` dedupes repeat profiles). Entrance animations (`dTop/dLeft/dRight/dBottom`) replay on open and on strip-switch (`swap` class). `closeDetail()` hides it, restores body scroll. Escape / "Back to wave" closes.
- **Data maps:** `portraits` (portrait key → image URL), `profiles` (card order/content), `SOCIALS` (name → github/linkedin/gmail/discord), `PORTFOLIOS` (name → portfolio URL). Lookup is case-insensitive via `name.trim().toLowerCase()`. Missing links = dimmed buttons, never broken links.

## Why photos live in `images/` instead of inside `index.html`

- **File size:** `index.html` is already ~293KB because 4 portraits were pasted in as base64. Base64 inflates images ~33% and must download/parse before anything renders. Files in `images/` keep HTML small and let the browser fetch images in parallel with caching.
- **Caching:** `images/tejas-patil.png` etc. are cached by the browser across reloads; embedded base64 is re-downloaded with every HTML fetch.
- **Maintainability:** swapping a photo = replacing one file + one `portraits.xxx` line (what we did for Shrishti). With base64 you must regenerate a giant string and edit a 2000+ character line.
- **Tooling:** real files work with compression, resizing, lazy-loading (`loading="lazy"` on the strip), and `file`/`curl` checks. Base64 blocks all of that.
- **Convention kept:** All 6 team members (Tushar, Tejas, Trishika, Shrishti, Vnshika, and Samarth) now use `images/`. The leftover Shrishti base64 blob in `portraits` is now unused and can be deleted to shrink the file.

## Codebase map

- `frontend/index.html` — everything: styles (wave, cards, detail view, social dock, strip, animations, mobile/reduced-motion), markup (stage, SVG clip, detail overlay), script (data + render loop + detail logic).
- `frontend/images/` — `tushar-mali.png`, `tejas-patil.png`, `trishika.jpeg`, `shrishti-malhotra.png`, `vnshika-gupta.jpg`, `samarth-kulkarni.jpg`. Referenced only through the `portraits` map, so renaming = one-line change.
- No dependencies, no build, no backend. Any static server works.
