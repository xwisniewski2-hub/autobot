# RSK V3 — WEBSITE BRIEF (as built)
Spine: vertical scroll. Two bike cutouts on a fixed layer enter the hero (Old Glory from
the left, Midnight Run from the right), then ride down the page — position keyframed to
scroll progress (GSAP ScrollTrigger scrub 1.2, Lenis smooth scroll when available).
Deep background: motorcycle-history timeline (12 eras, IBM Plex Mono) drifting on slow
parallax. Layers: timeline z0 · tint z1 · aurora z2 · grain z3 · riders z5 · content z10.
Sections: Hero / The Shop / What We Do (4 service cards) / The Builds (6 flag colorways,
3D tilt, pop-out cutouts on CSS backplates) / The Creed / Final CTA (reused Old Glory cutout).
Menu: fullscreen takeover, cutout preview swaps on hover, pixel-clean rotating X.
Motion: slow & luxurious (1.15–1.7s, power3.out, ~0.14s staggers). Reveals: fade + rise;
hero headline assembles word by word. Mobile <860px: single-lane riders, stacked grids,
tilt off, lighter timeline. prefers-reduced-motion respected. No autoplaying video anywhere.
