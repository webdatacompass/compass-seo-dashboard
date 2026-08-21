# compass-seo-dashboard

Daily SEO performance dashboard for the six Compass sites: Search Console and
GA4, split by market (Qatar, Saudi, UAE), against a fixed list of targeted
keywords.

## How it works

```
.github/workflows/refresh.yml     daily 06:00 UTC
  └── scripts/fetch_data.py       Search Console + GA4  ->  data.json (committed back)
        keywords.json             the ONLY keywords tracked; edit to change what is measured
        data.json                 28-day metrics + rank history, one entry appended per day
              |
        index.html                single self-contained page; fetches data.json at load
```

Two deliberate choices worth knowing before changing anything:

- **Only the keywords in `keywords.json` are reported.** A targeted keyword with
  no Search Console impressions is recorded as *not ranking* (`pos = null`)
  rather than omitted, so a gap stays visible instead of disappearing from the
  report. Position averages are impression-weighted.
- **Search Console and GA4 fail independently.** Either one erroring falls back
  to the previous `data.json` values for that site rather than writing zeros, so
  an outage on one side cannot wipe the other's history. Backlinks are carried
  forward untouched; no Google API provides them.

Search Console data lags ~3 days and the window is 28 days, both set at the top
of `fetch_data.py`.

## The sheet

One vertical sheet, read top to bottom, answering three questions in order: is
search traffic up or down, which property needs attention now, and is the
publishing pipeline on schedule. The audience is mixed — the specialist doing the
work, the person who owns it, and group leadership who do not do SEO — so the top
of the page states a conclusion in words before any table appears.

Bands, in order:

| Band | Holds |
| --- | --- |
| Masthead | wordmark, property count, window, generation date |
| Hero | generated headline, group metrics, group position chart |
| Alert | the one property to act on, plus up to three to watch |
| Property table | all properties, ordered by urgency |
| Quick wins / Sessions | position 4–20 queries, traffic sources |
| Per-property detail | Search Console, SERP by market, GA4, backlinks |
| Footer | sources, freshness caveat |

Two tabs under the masthead: **Search performance** holds everything above, and
**Blog Pumper** holds the publishing pipeline on its own — queue depth and runway
per property (thinnest first), what is next up, and what has gone live. The tab
carries the total queued as a count, so a thin pipeline is visible without
switching. Both bars pin to the top as one unit; the choice is remembered.

The last band carries everything that needs a property chosen first: Search
Console KPIs against the prior period, top queries, impressions split by ranking
position, the full keyword table with a filter, top pages, SERP position by
market with its own trend, GA4 behaviour, and backlinks. Two switchers drive it —
property and market — and both remember your choice.

**The table is ordered by urgency, not by size.** A property lands in *Acting on*
if it is losing clicks, has under 3.5 weeks of queue left, or ranks for none of
the keywords it targets; everything else is *Steady*. Within each group the worst
change comes first. Red means one thing only — bad news, or the thing to act on —
so it is never used for a positive delta.

The publishing queue is folded in as the **Queue left** column and its own row
subtitle, read from the same Blog Topics sheet the publisher works from. It
reports and never writes: topping the queue up is the SEO specialist's job, and a
thin queue is a fact to surface rather than something for this repo to fix.
Compass Furniture has a tab in the sheet but is deliberately excluded, because it
is ON HOLD in the publisher and showing a queue would imply posts are coming.

The sheet must be shared with this repo's service account as **Viewer**. If it is
not, the Queue column reads "—" and the run still succeeds — the blog fetch is
wrapped like Search Console and GA4 are, so a sheet problem cannot cost the day's
search data.

### Nothing on the page is typed

Every figure and every sentence is derived in `index.html` from `data.json`,
including the headline and the alert copy. A hardcoded conclusion is a lie the
moment the data moves, and this page is often screenshotted and forwarded.

The derivations worth knowing:

| Shown | Derived as |
| --- | --- |
| Lead metric | sum of `cur.clicks`, against `prev.clicks` |
| Keywords ranking | queries with a non-null position, over all queries |
| Position chart | mean of `RANKHIST[*].GCC` per day, across properties with history |
| Share of clicks | that property's clicks over the highest |
| Queue left | `BLOG[domain].weeks`, at two posts per property per week |
| Quick wins | queries at position 4–20, by impressions |
| Session sources | channels summed, as a percentage of **total sessions** |
| Blended CTR | group clicks over group impressions |
| Impressions by position | impressions bucketed 1–3 / 4–10 / 11–20 / 21+ |
| Backlinks change | latest history point minus the first |

The position buckets exclude keywords that did not rank. The previous dashboard
bucketed with `p <= 3`, and `null <= 3` is true in JavaScript, so every tracked
keyword with no impressions was counted into the best bucket.

That last row is a real trap: GA4's channel breakdown does not reconcile with its
own session total (1,879 against 1,829 on 2026-08-20). Percentages are of the
session total, so they match the headline metric rather than each other.

The headline names a fraction ("up a seventh") only when the figure is within
half a point of it, and otherwise prints the percentage. The design's prototype
copy claimed "CTR halved" for a 40% fall and "every property except ITS improved
its average position" when only two of six had; both are now generated, so
neither can drift back into being wrong.

### Colour has one meaning each

The original palette gave a single accent two incompatible jobs — brand mark and
alarm — so a gain, a highlight and a loss all rendered the same, and the page
read as undifferentiated grey. The roles are now separate, and all four clear
WCAG AA on the sheet, the tint and the alert ground:

| Token | Means | Light | Noir |
| --- | --- | --- | --- |
| `--bad` | falling, broken, needs action | `#c02a10` | `#ff4a2b` |
| `--good` | improved | `#276b32` | `#7ecb8c` |
| `--warn` | not wrong yet, but close | `#8a5a10` | `#e0a63c` |
| `--focus` | look here, no judgement implied | `#1f4e79` | `#7fb3e6` |

Where it lands:

- **Deltas** are green up, red down. Previously a gain was the same grey as "no
  comparison available", so growth was invisible.
- **Runway** grades red under 3.5 weeks, amber under 5, green beyond. A figure
  that only turns red at the last moment gives no warning while there is still
  time to commission topics.
- **The act-on rows** carry a wash and a red edge, so the block that needs
  attention is findable without reading a number.
- **Steady** is green, because steady means fine.
- **Share-of-clicks bars** are red where action is needed and focus-navy for
  ordinary volume, replacing a neutral so pale the bar read as decoration.
- **Organic search** is focus-navy, not red. It is the channel search work moves,
  so it needs emphasis — but colouring it with the alarm made the most important
  row look like the worst one.

`--focus` exists precisely so "important" and "bad" stop being the same signal.

### Each property has its own colour

Separate from status, and never mixed with it. A property keeps one colour in the
table rail, the share-of-clicks bar, the property switcher, its detail band rule
and its own charts, so it can be followed down the page without reading names.

| Property | Light | Noir |
| --- | --- | --- |
| Compass Arabia | `#5c6118` olive | `#b9c266` |
| Compass FM GCC | `#0f6357` teal | `#5fc0b0` |
| Compass Waterproof | `#0a5aa8` blue | `#6fa8e8` |
| Compass Logistics | `#4a4bc4` indigo | `#9a9bf0` |
| Sunset Media | `#99306b` magenta | `#e07fb4` |
| Compass ITS | `#4a5560` slate | `#9aa8b4` |

These were picked against two constraints, not by eye: each must be distinct
from the others (closest pair is dE 26 in Lab, comfortably above the ~20 needed)
**and** from all four status colours (closest is dE 22). Arabia is olive rather
than its brand bronze because bronze sat dE 13 from the warn amber that the
runway column immediately beside it uses — the two would have been confusable in
exactly the spot where confusion costs most. Minimum contrast on the ground is
5.6:1 in light and 7.1:1 in noir.

If a property is added without a colour, it falls back to `--focus` rather than
rendering colourless.

The **per-property detail band takes a wash of the selected property's colour**,
so it is obvious at a glance whose numbers are on screen. 8% is the ceiling, not
a taste call: at 10% the muted labels drop below 4.5:1 against the wash, measured
for all six colours on both grounds. Light mixes toward the sheet; noir mixes
toward something darker than its own ground, because the noir company colours
are light and mixing them into the ground would lift it and cost that contrast.
Panels inside stay on the plain sheet so they read as cards on the wash. The
plain `background` declaration precedes the `color-mix()` one, so a browser
without `color-mix` gets the neutral ground rather than nothing.

### Two grounds

Everything from the property table down sits on `--ground` (`#f1ece7`), a
slightly deeper paper than the sheet above it, so the summary you read first and
the detail you dig through separate at a glance. Panels that are tinted on the
sheet invert inside that region — they become the lighter colour — so they still
read as raised rather than sunken.

### Charts

Each line chart carries a **numeric y axis** and a **dashed least-squares
trendline**, and states the trend in words underneath ("the trend is improving,
about 2.2 over the period"). Eyeballing direction on a 28-point line that wobbles
is exactly where people guess wrong, so the chart says it rather than implying it.

Two implementation points that are easy to get wrong:

- **The axis labels are HTML, not SVG text.** The plot is stretched horizontally
  with `preserveAspectRatio="none"`, which would distort any text inside it.
  Vertical scale is 1:1, so a viewBox y is a CSS pixel y, and the labels are
  positioned absolutely in a gutter beside the plot. Gridlines are drawn at the
  same computed values, so ticks and lines cannot drift apart.
- **Tick values are rounded to human numbers** (12 / 13 / 14, not 12.37 /
  13.44). The first pass biased toward coarse steps and drew only two gridlines
  across a four-point span; the thresholds now favour a finer step.

Direction markers survive from the original design and follow the metric:
position charts read Better at the top, and the backlinks chart — where more is
better — inverts to Worse at the top. The axis numbers alone would not prevent a
misread, since "lower is better" is not obvious to everyone looking at a
position figure.

### Look and feel

The light "Broadsheet" look: ink masthead and footer, Montserrat for headings and
numerals, Archivo for body, **radius 0 everywhere**, and rule weights used
semantically — hairline between rows, heavier between bands, ink under the table
header.

The sheet **fills the window**. The original design was a fixed 1120px card on a
grey desk, with a border and a shadow; on a real screen that reads as a window
inside a window, so the desk is gone. The broadsheet grammar is carried by the
ink bands and the rule weights rather than by a card edge. One `--pad` token
(`clamp(20px, 3.2vw, 60px)`) sets every band's side padding, so they all line up
and widen together, and the headline and lead metric are clamped so they stop
growing on very wide screens instead of stretching.

Both font families are **self-hosted** in `fonts/` (one variable file each, latin
subset). The page makes no third-party requests: it carries commercial figures
and is moving behind an auth gate, where a font call to a CDN would leak the
referrer.

A dark variant of the same layout exists and is opt-in via
`<html data-theme="noir">`, not `prefers-color-scheme` — this sheet is regularly
exported as an image and the export should not depend on whose laptop rendered
it.

The property table sheds columns as the window narrows, in order of how easily
the figure is found elsewhere on the row: Sessions at 1240px, then Share of
clicks and Avg pos at 1040px (where the two-column bands also collapse), then
Impressions and Queue left at 780px. Everything dropped reappears in the row
subtitle rather than disappearing — a mistake worth naming, because the reveal
was written twice as an inline `display:none` that the media query cannot
override, and both times the figures silently vanished on mobile instead.

Wide tables scroll inside their own box, so the page itself never scrolls
sideways. Brand assets are in `assets/` (wordmark and monogram, each in ink and
off-white). The masthead uses the **monogram**: the supplied wordmark is a
stacked lockup, so at masthead height its "COMPASS GROUP" text rendered about
10px tall and read as mush, and the band already says what this is in words.

## Running it locally

```bash
pip install -r requirements.txt
export GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account.json
python scripts/fetch_data.py
```

The service account needs read access granted per property: Search Console
(Settings > Users) and GA4 (Admin > Property Access Management, Viewer). In CI
the key comes from the `GOOGLE_CREDENTIALS` secret and is written to a temp file
at runtime; it is never committed.

Then open `index.html` — it reads `data.json` from the same directory.

## Hosting and access

Currently GitHub Pages at `analysis.compass-arabia.com`, which means **the
dashboard and its raw data are readable by anyone**: `/data.json` carries every
metric and all 199 targeted keywords with their positions, and `/keywords.json`
is the keyword strategy on its own.

GitHub Pages has no access control. A Pages site is public even when its
repository is private, and serving one privately needs an organisation on
Enterprise Cloud — so making this repo private would hide the source while
leaving the data served. Closing it means moving the hosting.

**In progress:** Cloudflare Pages with Cloudflare Access in front (free up to 50
users, real per-person sign-in rather than a shared password).

`.github/workflows/deploy.yml` does the deploying, and it is already committed.
It stays inert until two repo secrets exist, then publishes on every data
refresh. It uses **Direct Upload** rather than a Git connection, because a Git
connection can only be created through the dashboard's OAuth flow, and this way
the whole pipeline lives in the repo.

It also publishes **only** what the page requests: `index.html`, `data.json`,
`robots.txt`, `_headers`, `assets/` and `fonts/`. So `keywords.json`,
`requirements.txt` and `scripts/` stop being downloadable at all — a real
reduction on its own, separate from the auth gate. The step asserts both lists,
the forbidden one and the required one, because a quiet omission there ships a
page in fallback fonts with no wordmark.

### Finishing the setup

1. **Cloudflare API token** — dash.cloudflare.com > My Profile > API Tokens >
   Create Token, template *Edit Cloudflare Workers*, or a custom token with
   `Account / Cloudflare Pages / Edit`. Copy the account ID from any zone's
   overview sidebar.
2. **Repo secrets** (needs repo admin) — Settings > Secrets and variables >
   Actions:
   - `CLOUDFLARE_API_TOKEN`
   - `CLOUDFLARE_ACCOUNT_ID`

   The next data refresh deploys automatically; or run the *Deploy to Cloudflare
   Pages* workflow by hand.
3. **Cloudflare Access** — Zero Trust > Access > Applications > Add an
   application > **Self-hosted**, hostname `compass-seo-dashboard.pages.dev`.
   One policy: action *Allow*, include the specific emails. Email OTP needs no
   identity provider; add Google as an IdP for one-click sign-in.
4. **Then, with repo admin:** disable GitHub Pages (Settings > Pages) so
   `analysis.compass-arabia.com` stops serving the data unauthenticated. Delete
   `CNAME` at the same time — it is a Pages artefact and means nothing to
   Cloudflare.

Two traps in that order of operations:

- **Protecting *preview deployments* is not the same setting** and does not
  cover the production URL. It has to be a self-hosted application on the
  production hostname, or the site stays wide open while looking protected.
- **A custom domain cannot be added to a hostname that already has an Access
  policy.** If `analysis.compass-arabia.com` is ever pointed at Cloudflare
  Pages, add the custom domain *first*, then apply Access.

Interim mitigations already in place, and their limits:

| | |
|---|---|
| `index.html` carries `noindex, nofollow` | keeps the page out of search results |
| `robots.txt` disallows the data files | they cannot carry a meta tag themselves |
| `_headers` sets `X-Robots-Tag` | ignored by GitHub Pages; active once on Cloudflare |

None of that is access control. It keeps the dashboard out of search results;
anyone who requests a URL still gets it.

Still outstanding, and both need repo-admin rights:

- **Enforce HTTPS** (Settings > Pages). It is currently off, so
  `http://analysis.compass-arabia.com/data.json` serves over plaintext.
- **Disable Pages** once Cloudflare is live, so there is no second door.
