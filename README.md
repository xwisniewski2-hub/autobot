# Rising Sun Kustoms — Website Repo

## Live site
`index.html` at the repo root is the live site, served by GitHub Pages at
https://xwisniewski2-hub.github.io/autobot/

It's a single self-contained file (images embedded as base64) — no build step needed.
GSAP/ScrollTrigger/Lenis and Google Fonts load from CDN with a graceful fallback if
those are unreachable.

## Backend
Booking form ("Book your slot") submits directly to a Supabase project via the public
REST API. The anon key in `index.html` is safe to expose — row-level security only
allows public INSERT into the `appointments` table, no read/update/delete.

## Repo structure
- `index.html` — the live, deployed site
- `dev/template.html` — the *editable* source (placeholders like `__IMG_v1__` swapped
  for base64 image data at build time). Edit this, not the raw `index.html`, when
  making design/copy changes — then rebuild.
- `source-assets/references/` — the two AI-generated hero bike images + the original
  logo photo
- `source-assets/catalog/` — full-size PNGs of six paint-scheme variants generated
  during development (no longer used on the live site, kept as raw material)
- `source-assets/cutouts/` — transparent PNG cutouts (background removed locally,
  free, via rembg) of the bikes and variants
- `source-assets/web-optimized/` — trimmed/resized WebP versions actually embedded
  in `index.html`
- `docs/` — creative direction, image prompts, and build notes from development

## Contact
Phone number is wired as a `tel:` link on the "Call the shop" button — not displayed
as text anywhere on the page.
