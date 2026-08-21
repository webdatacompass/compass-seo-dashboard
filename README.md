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

## The page

Two tabs. **SEO analysis** holds a summary, an all-properties table, and a
per-property detail section driven by a property selector. **Blog Pumper** holds
the publishing pipeline: queue depth and runway per property, what is next up,
and what has gone live. The tab shows the total queued as a count, so a thin
pipeline is visible without switching.

Under the title, one generated sentence states the conclusion before any table
appears — the audience includes people who do not do SEO, and a sentence they can
read in two seconds beats a grid they have to interpret.

The per-property section carries Search Console KPIs against the prior period,
top queries, impressions split by ranking position, the full keyword table with a
filter, top pages, SERP position **per market** (GCC / Qatar / Saudi / UAE) with
its own trend, GA4 behaviour, and backlinks.

### Nothing on the page is typed

Every figure and the verdict sentence are derived in `index.html` from `data.json`.
A hardcoded conclusion is a lie the moment the data moves, and this page gets
screenshotted and forwarded. The verdict names a fraction ("up a seventh") only
when the figure is within half a point of one, and otherwise prints the
percentage.

| Shown | Derived as |
| --- | --- |
| Verdict sentence | group clicks vs prior, plus the worst standing problem |
| Keywords ranking | queries with a non-null position, over all queries |
| Share / quick wins | clicks over the highest; queries at position 4–20 |
| Queue left | `BLOG[domain].weeks`, at two posts per property per week |
| Impressions by position | impressions bucketed 1–3 / 4–10 / 11–20 / 21+ |
| Position trend | `RANKHIST[domain][market]`, per property and market |

### The hero

The brand monogram sits in the top-right corner of the header, at header size
rather than scaled up as decoration, and hides below 700px where the title needs
the width.

The verdict sentence is the focal point: an accent rule, then the conclusion at
clamp(22-32px), with the supporting clause below it at 14px muted so it reads as
support rather than competing. It was previously 16px sitting under two lines of
metadata, which buried the one sentence the page exists to deliver.

The at-a-glance row gives the first card -- clicks, the number every other figure
qualifies -- double width and a 58px value against 26px for the rest. Five
identical cards gave the eye nowhere to land. The hierarchy is size only: no new
colours, no new surfaces.

### Design

Dark ground, **one accent**, and colour used only where it encodes data — bars,
position pills, deltas. Structure comes from borders and spacing rather than from
tinted regions. Four large surfaces on the rendered page; smallest type is 12px;
system font stack, so there are no webfonts and no third-party requests at all.

This is the design the dashboard had before an attempted "Broadsheet" redesign,
and it was restored deliberately. That redesign was a print aesthetic doing a
screen dashboard's job: it reached about ten near-identical light surfaces, and
spent colour on region and identity instead of on data, so colour stopped meaning
anything. Every complaint it drew — hard to read, hard to scan, colours clashing,
everything blending — was a symptom of that, and each was answered by adding
another system rather than removing one. 44 CSS custom properties against this
version's 13 is the fingerprint.

Two things from that work were worth keeping and were ported back:

- **The verdict sentence** above.
- **Line charts for the two trends.** Position and backlink history each
  rendered as one bar per day, 29 and 30 rows, which is a lot of screen for a
  shape you cannot see. Both are now a single line with a numeric y axis and a
  dashed least-squares trendline, and each states its direction in words
  underneath. The axis labels are HTML, not SVG text: the plot is stretched
  horizontally with `preserveAspectRatio="none"`, which would distort anything
  drawn inside it, while the vertical scale stays 1:1 so a viewBox y is a CSS
  pixel y. Position charts mark *better* at the top; the backlink chart inverts,
  because more links is better.

Everything else from that period was data and infrastructure rather than visual
design, and is unaffected: the blog pipeline, per-market data, the noindex and
robots work, the deploy staging, and the Cloudflare workflow.

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
`robots.txt` and `_headers`. So `keywords.json`,
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
