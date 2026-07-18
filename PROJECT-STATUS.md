# RISING SUN KUSTOMS — PROJECT STATUS & HANDOFF
### Last updated: v1 (see Versioning section) — read this file first in any new chat

---

## 1. WHAT THIS IS

A motorcycle repair, maintenance, welding & custom fabrication shop website, built for
**eventual resale to a new owner**. Everything is built to be functional and
"plug-and-play ready" for whoever buys the shop and this site — real accounts, a real
database, a real admin panel, not placeholders.

**Owner (current):** the user in this chat, GitHub handle `xwisniewski2-hub`.
**Repo:** `xwisniewski2-hub/autobot` (public — required for free GitHub Pages hosting).
**Live URL:** https://xwisniewski2-hub.github.io/autobot/
**Do NOT touch:** `xwisniewski2-hub/alphaomegatides` or `xwisniewski2-hub/nexpepstep` —
separate unrelated projects. Never referenced or modified by anything below.

---

## 2. VERSIONING SCHEME (starting now — READ THIS)

Per the user's explicit instruction: **every edit from this point forward gets a clear
version number, v1, v2, v3...** This is separate from the old "V1/V2/V3" design-era
naming (Americana / dark-tech-early / dark-tech-current) used earlier in the project —
those were big creative pivots. This new v1, v2, v3... sequence tracks every
functional change from here on, for easy handoff and easy tracking in future chats.

**How it works:**
- Every version's built HTML is saved to `versions/vN.html` in the repo (e.g.
  `versions/v1.html`, `versions/v2.html`).
- `index.html` at the repo root is ALWAYS a copy of the latest version — that's what's
  actually live on GitHub Pages.
- `dev/template.html` is the editable source (placeholders like `__IMG_v1__` instead of
  baked-in base64) — always represents the current/latest version too.
- Every commit message is prefixed `vN: <description>`.
- Git tags (`git tag v1`, `git tag v2`, ...) mark each version on the `autobot` repo for
  easy reference.

**v1 = this current push** (sticky submit buttons fix — see Section 6, "Changelog").

---

## 3. TECH STACK

- **Frontend:** one self-contained HTML file (`index.html`). No build framework —
  vanilla JS, CSS, GSAP + ScrollTrigger + Lenis (via CDN, with graceful no-CDN
  fallback), Google Fonts (Anton, IBM Plex Mono, Inter).
- **Hosting:** GitHub Pages, free tier, deployed from the `master` branch root.
- **Backend/database:** Supabase (free tier, $0/month, confirmed before creation).
  - Project name: `rising-sun-kustoms`
  - Project ref / ID: `vfmrqnnmhkjlljpvogdx`
  - Project URL: `https://vfmrqnnmhkjlljpvogdx.supabase.co`
  - Org: `xwisniewski2-hub's Org` (org id `kcpqqfqbvjnrpmnnalhk`)
  - Anon/publishable key is embedded in `index.html` client-side — **this is safe and
    intentional**, protected entirely by Row Level Security (RLS) policies (see below),
    not by hiding the key.
- **Image generation:** Higgsfield MCP (GPT Image 2, low quality/1k resolution —
  "cheap mode"). Total spent across the whole project: **3.5 credits** out of a
  2,966-credit starting balance.
- **Local tools used:** `rembg` (free local background removal, 0 credits).

---

## 4. GITHUB ACCESS METHOD (IMPORTANT FOR FUTURE CHATS)

There is **no GitHub MCP connector** available, and Claude in Chrome has never
successfully connected in this environment. The working method:

- A **fine-grained GitHub Personal Access Token (PAT)**, scoped to ONLY the `autobot`
  repository, with **Contents: Read and write** permission (Metadata: Read-only is
  auto-included and required — that's normal).
- The user generated this at github.com/settings/personal-access-tokens/new and pasted
  it into chat.
- Per the user's explicit instruction: **do NOT revoke this token** — it stays active
  for future sessions ("we will make many changes don't revoke anything").
- Usage pattern (every time): `git clone` the repo into a sandbox temp folder using the
  token embedded in the HTTPS URL, copy the new `index.html` / `dev/template.html` in,
  commit, `git push`, then delete the local clone. The token is never echoed to
  chat output (all git commands pipe through `sed` to redact it from any printed URLs).
- **If the token expires or is lost:** ask the user to generate a new one with the same
  scope (autobot repo only, Contents read/write) and paste it in. It's already in this
  conversation's history if the same chat continues — reuse it from there if visible.

---

## 5. SUPABASE SCHEMA (as it exists right now)

### `public.profiles`
One row per signed-up user, auto-created by a trigger (`handle_new_user()`) on
`auth.users` insert. Columns: `id` (=auth.users.id), `email`, `full_name`, `role`
(`'customer'` default, or `'admin'`), `created_at`, `first_name`, `last_name`, `phone`,
`address_street`, `address_apt`, `address_city`, `address_state`, `address_zip`.
RLS: users read/update their own row; admins (via `is_admin()` helper function) can
read/update all rows.

### `public.services`
The priced job catalog — publicly readable (needed for the booking dropdowns), only
admins can insert/update/delete. Columns: `id`, `category`, `name`, `price` (numeric),
`duration_minutes`, `active`, `sort_order`, `created_at`. **16 rows seeded with
made-up but realistic prices** across categories: Maintenance, Repair, Welding, Custom
Fab, General (e.g. Oil & Filter Change $89, Full Tune-Up $179, Frame Weld $225 — see
the live Admin Panel → Services & Pricing tab for the full current list, since these
are editable and may have changed).

### `public.appointments`
Columns: `id`, `created_at`, `full_name`, `contact`, `appointment_date`,
`appointment_time`, `reason` (legacy, nullable), `notes` (current free-text field),
`status` (`pending`/`confirmed`/`completed`/`cancelled`), `service_id` (→services),
`price_at_booking` (numeric snapshot, so later price edits don't retroactively change
old bookings), `user_id` (→auth.users, **required, not nullable in practice**).

**RLS (current, as of v1):**
- INSERT: only `authenticated` users, and only where `user_id = auth.uid()` — i.e.
  **anonymous/guest booking is completely blocked at the database level**, not just
  hidden in the UI. A user must be signed in with a verified account to book.
- SELECT: users see only their own appointments; admins see all.
- UPDATE/DELETE: admins only (used by the Admin Panel's Bookings tab).

**Why "verified" is already satisfied:** Supabase projects have "Confirm email" enabled
by default, meaning `signInWithPassword` will not succeed until the user has clicked
the confirmation link (or, once configured, entered the OTP code — see Section 7,
item 2) sent to their email. So any `authenticated` session already implies a verified
email — no extra check was needed beyond requiring `authenticated` for the insert.

---

## 6. WHAT'S BUILT — FULL FEATURE LIST

- **Design:** dark cinematic garage aesthetic, full flag palette (crimson/blue/white),
  Rising Sun sunburst logo recreated as inline SVG (header, footer, favicon).
- **The scroll spine:** two AI-generated custom bikes ("Old Glory"-style crimson
  cruiser and a navy bobber) enter from opposite sides in the hero and ride down the
  page as the user scrolls, GSAP ScrollTrigger-driven. A faint motorcycle-history
  timeline (1901→today) drifts in the deepest background layer.
- **Sections:** Hero → The Shop → What We Do (4 service cards) → **Quick Quote**
  (inline pricing dropdown, embedded directly on the page) → The Creed → Final CTA.
- **Quick Quote widget:** pick a job from a custom dropdown, see the live price,
  click "Book This Job" → jumps straight into the booking flow with that service
  pre-selected.
- **Accounts (Supabase Auth, email+password):**
  - Sign In / Sign Up via the fullscreen menu → "Sign In / Sign Up" (label changes to
    "My Account" once signed in).
  - Sign-up form: First/Last Name, Email, Password (min 8 chars), Phone Number, and a
    collapsible "+ Add shipping address (optional)" section (Street, Apt/Suite, City,
    State, ZIP) — modeled on a reference design the user provided from another one of
    their projects (alphaomegatides.com).
  - An OTP ("6-digit code") verification step is built and wired client-side
    (`supabase.auth.verifyOtp`), but **will not actually deliver a numeric code by
    default** — see Section 7, item 2, for the one manual dashboard step needed.
  - "My Account" panel: shows the signed-in user's own appointments with live status,
    and (if admin) an "Open Admin Panel" button.
- **Booking:** requires a signed-in, verified account (guest booking is blocked, see
  Section 5). If a signed-out user tries to book, they're routed into sign-in/sign-up
  first, and the booking flow **automatically resumes** (with any pre-selected service
  intact) right after successful sign-in or OTP verification.
- **Custom dropdowns:** both the Quick Quote and the booking-form service pickers use a
  hand-built compact dropdown component, NOT a native HTML `<select>`. This was a
  deliberate fix — native `<select>` elements on iOS Safari trigger a full-screen
  native picker overlay that looked broken/oversized; the custom component avoids that
  entirely.
- **Admin Panel** (reachable via My Account → "Open Admin Panel", only visible/usable
  if the signed-in user's `profiles.role = 'admin'`):
  - **Bookings tab:** every appointment, with an inline status dropdown
    (pending/confirmed/completed/cancelled) and a delete button.
  - **Services & Pricing tab:** every service, inline-editable (category, name, price,
    active/hidden toggle), plus a form to add brand new services. This is the "fully
    customizable" pricing control — no code required to change prices going forward.
- **Call the shop:** a `tel:+19086925942` link — the phone number is never shown as
  visible text anywhere on the page, only triggered on tap/click, per the user's
  request.
- **Side scroll buttons:** fixed control, top-right-ish of viewport, jumps to the very
  top or very bottom of the page.
- **Mobile fixes applied:**
  - Fixed header no longer overlaps section content (was a real bug introduced by an
    earlier spacing-tightening pass; fixed with a proper backdrop + clearance padding,
    and a stale leftover mobile media-query rule that was silently re-breaking it was
    found and removed).
  - Menu text no longer overflows on mobile (font-size clamp had too high a minimum).
  - Signup form's submit button is now in a **sticky footer** inside the modal — it
    never disappears off-screen no matter how long the form gets (this was the bug
    fixed in **v1**).

---

## 7. OUTSTANDING / TODO (nothing below is done yet)

1. **No admin account exists yet.** To create one:
   - User signs up on the live site with whatever email/password they want as the
     owner login.
   - User tells Claude that email address.
   - Claude runs: `update public.profiles set role='admin' where email='<that email>';`
     via the Supabase MCP `execute_sql`/`apply_migration` tool.
   - From then on, signing in with that account shows "Open Admin Panel" in My Account.

2. **OTP email code needs one manual Supabase dashboard step.** The sign-up flow
   promises "a verification code will be sent" and has a working code-entry screen,
   but Supabase's default confirmation email only includes a link, not a visible code,
   until the email template is customized. This can't be done via any available MCP
   tool (it's a GoTrue/Auth dashboard setting, not a SQL-accessible table). Steps for
   the user (or future Claude instance walking them through it):
   - Supabase Dashboard → Authentication → Email Templates → "Confirm signup"
   - Add `{{ .Token }}` somewhere in the template body (that's the 6-digit code)
   - Save
   - Until this is done, sign-ups will get a confirmation **link** instead — still
     functional, just not the exact visual promised.

3. **New-booking email notifications are NOT built yet.** The user wants: when someone
   books a job, (a) an email alert goes to the shop, and (b) it shows up in the Admin
   Panel (part b is already live/done — every booking appears in Admin → Bookings in
   real time with no extra work needed). For part (a), this requires:
   - A **free email-sending API key** — Resend (resend.com) was recommended: free
     tier, no credit card, ~2 minute signup.
   - The **destination email address** to notify on new bookings.
   - Once both are provided, the plan is: a Supabase Edge Function (deployable via the
     `Supabase:deploy_edge_function` MCP tool) triggered by a database webhook/trigger
     on `appointments` INSERT, which calls the Resend API to send the email.
   - **As of this writing, neither the API key nor the notification email address has
     been provided.** This is the next thing to ask the user for.

4. **No double-booking / calendar-conflict prevention.** The booking form lets anyone
   pick any date/time freely — there's no check against already-booked slots. Not
   requested yet, but worth flagging as a natural next feature (e.g., a query against
   existing `confirmed`/`pending` appointments for that date before allowing submit,
   or building out actual shop hours/slot logic).

5. **Vercel is NOT used and NOT needed.** The user asked about this once — clarified
   that GitHub Pages is the entire hosting solution already in place; there is no
   Vercel project for this repo and none is required.

---

## 8. FILE MAP (inside the `autobot` repo)

```
index.html                  ← LIVE site (GitHub Pages serves this). Always = latest vN.
dev/template.html           ← Editable source (has __IMG_v1__ / __IMG_bike2__ /
                               __SUN_SVG__ / __FAVICON__ placeholders swapped for
                               real base64/inline-SVG at build time via a Python script)
versions/v1.html, v2.html…  ← Snapshot of index.html at each versioned change (see §2)
source-assets/references/   ← The two AI-generated hero bike images + original logo photo
source-assets/catalog/      ← Six paint-scheme PNGs from early development (unused on
                               site now, kept as raw material)
source-assets/cutouts/      ← Transparent PNG cutouts (rembg, local, free)
source-assets/web-optimized/← Trimmed/resized WebP versions actually embedded in index.html
docs/                       ← creative-direction.md, image-prompts.md, video-prompt.md,
                               website-brief.md — original design/build notes
README.md                   ← Repo-level orientation (shorter version of this file)
PROJECT-STATUS.md           ← THIS FILE — full detailed history + TODOs
```

---

## 9. CHANGELOG

- **V1 (old naming)** — Americana vintage design. LOCKED, never touch
  (`rising-sun-kustoms-V1-FINAL-DO-NOT-TOUCH.html`, not in this repo's active path).
- **V2 (old naming)** — dark tech pivot, first Higgsfield-generated version, later
  superseded.
- **V3 (old naming, = current `index.html` lineage)** — "The Ride Down": scroll-driven
  two-bike spine, full business features, Supabase backend added progressively.
- **v1 (NEW numbering starts here)** — Fixed the sign-up/booking modal's submit button
  disappearing off-screen (now sticky-positioned, always visible while scrolling the
  form). This file (`PROJECT-STATUS.md`) created. Versioning scheme established.

---

## 10. QUICK-START FOR A FUTURE CLAUDE INSTANCE

If you're picking this up in a new chat with no memory of the above:
1. Read this file in full first.
2. The GitHub PAT may still be in this conversation's history if it's a continuation —
   reuse it (never ask the user to reveal it in plain chat if avoidable; if a new token
   is needed, walk them through generating one scoped to `autobot` only, Contents R/W).
2. The Supabase project ID is `vfmrqnnmhkjlljpvogdx` — use the Supabase MCP tools
   directly (`execute_sql`, `apply_migration`, etc.) rather than recreating anything.
3. Never touch `alphaomegatides` or `nexpepstep` repos.
4. Every change gets a new version number (see §2) — check `versions/` for the highest
   existing vN, and use vN+1.
5. Check Section 7 for what's still outstanding before assuming something is done.
