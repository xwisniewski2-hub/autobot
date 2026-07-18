# RISING SUN KUSTOMS — V3 CREATIVE DIRECTION
### "The Ride Down" — a cinematic scroll-driven site for a motorcycle repair & custom fabrication shop

## THE BIG IDEA
Two custom bikes enter the hero — one from the left, one from the right — then ride down
the page as the visitor scrolls. Content (titles, services, builds, story) reveals around
them as they pass. Behind everything, in the deepest layer of the browser, a faint
motorcycle-history timeline drifts by: a century of riding, ghosted in technical type.

## WORLD
Dark cinematic garage. Near-black base, film grain, sharp corners.
One work light after hours. Aurora glow: 2–3 huge, extremely blurred crimson and
patriot-blue gradient blobs drifting slowly behind all content.

## PALETTE (full flag treatment — crimson leads, blue and white ride support)
- Base garage black: #0B0B0D
- Panel steel:       #131318
- Crimson (lead):    #E23B3B   — matches the sunburst logo
- Patriot blue:      #2E5FD8
- Star white:        #F5F2EA   (warm) / #FAFAFA (pure, for headline pops)
- Gunmetal label:    #8A8F98   — technical micro-text
- Chrome line:       #C9CDD4   — thin rules and dividers

## TYPOGRAPHY (both voices, as ordered)
- Headlines: BOLD CONDENSED — Anton (all-caps, tight tracking) — hits like tank lettering
- Technical: IBM Plex Mono — labels, specs, years, coordinates, timeline entries
- Body: Inter — short confident copy, no hype

## BRAND MARK
The Rising Sun Kustoms sunburst (red/white rays). Recreated as inline SVG for the header
and favicon — crisp at any size, 0 credits. Original logo kept at assets/references/rsk-logo.jpeg.

## THE SPINE (scroll system)
Vertical scroll, Lenis smooth. Two bike cutouts on a fixed mid-layer:
- Bike 1 "OLD GLORY" (crimson cruiser, faces right) enters from the LEFT edge in the hero.
- Bike 2 "MIDNIGHT RUN" (navy bobber, faces left) enters from the RIGHT edge.
They meet, then ride DOWN the page — their y-position mapped to scroll progress via
GSAP ScrollTrigger, weaving left/right past section content, gentle bob + lean for life,
soft real shadows beneath. Slow & luxurious timing (1.2–1.8s, power3.out, ~0.15s staggers).

## LAYER STACK
z-0  Timeline (deepest): faint IBM Plex Mono era entries drifting upward slower than
     scroll (parallax) — 1901 first V-twins → board track era → war bikes come home →
     bobbers born in backyards → choppers take the highway → superbikes arrive →
     the custom scene goes pro → TODAY: YOUR BUILD. Pure CSS/JS, 0 credits, no trademarks.
z-1  Readability tint + film grain + vignette
z-2  Aurora blobs (crimson + blue, blurred 120px+, slow drift)
z-5  THE BIKES (fixed, scroll-driven)
z-10 Content: sections, panels, type

## SECTIONS
1 HERO — sunburst mark, RISING SUN KUSTOMS in Anton, taglines, both bikes enter. Word-by-word headline assembly.
2 THE SHOP — short story lines, big editorial type, animated highlight rules.
3 WHAT WE DO — image-free. Four service cards: 01 MAINTENANCE / 02 REPAIR / 03 WELDING / 04 CUSTOM FAB. Crimson border sweep, hover bloom, floating numeric labels.
4 THE BUILDS — six featured builds in flag colorways, 3D tilt pop-out cards, cutouts popping past card edges over CSS backplates.
5 THE CREED — kinetic typography, chips, thin animated lines. Ride free. Build American. Weld strong.
6 FINAL CTA — best build cutout reused, one line, booking/contact CTA, minimal footer.
MENU — fullscreen takeover, giant nav type, oversized reused cutout preview, pixel-clean X.

## MOBILE (<768px)
Bikes shrink and ride a single centered lane; timeline density reduced; catalog stacks;
tilt disabled; everything still breathes.

## BUDGET LEDGER (cheap mode — running)
- Bike 1 (GPT Image 2 low/1k): 0.5 cr — job ecc9c17a
- Bike 2 (GPT Image 2 low/1k): 0.5 cr — job cc3ae49a
- Planned next: 6 build colorways ≈ 3 cr (preflight first) · cutouts 0 cr (local rembg) · everything else CSS = 0 cr
