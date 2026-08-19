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

**Planned:** Cloudflare Pages with Cloudflare Access in front (free up to 50
users, real per-person sign-in rather than a shared password). The pipeline does
not change — the Action still commits `data.json`, and Cloudflare builds from the
repo instead of Pages.

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
