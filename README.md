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

## The two tabs

**SEO analysis** is everything above: Search Console, GA4, SERP by market,
backlinks.

**Blog Pumper** reports the publishing pipeline, read from the same Blog Topics
sheet the publisher itself works from — per-property queue depth, runway in weeks
at two posts a week, what is next up, and what has gone live. It reports and
never writes: topping the queue up is the SEO specialist's job, and a thin queue
is a fact to surface rather than something for this repo to fix.

Compass Furniture has a tab in the sheet but is deliberately excluded, because it
is ON HOLD in the publisher and showing a queue would imply posts are coming.

The sheet must be shared with this repo's service account as **Viewer**. If it is
not, the blog panel says so and the run still succeeds — the blog fetch is
wrapped like Search Console and GA4 are, so a sheet problem cannot cost the day's
search data.

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

It also publishes **only** `index.html`, `data.json`, `robots.txt` and
`_headers` — the page never requests anything else — so `keywords.json`,
`requirements.txt` and `scripts/` stop being downloadable at all. That is a real
reduction on its own, separate from the auth gate.

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
