#!/usr/bin/env python3
"""
Compass SEO dashboard — daily data fetcher.

Pulls Search Console + GA4 data for each property and writes data.json in the
exact shape index.html expects (SITES / RANK / RANKHIST). Backlinks are NOT
available via any Google API, so BACKLINKS is preserved from the existing
data.json and only its history date is appended.

Auth: a Google service-account key. Set GOOGLE_APPLICATION_CREDENTIALS to the
path of the key file (the GitHub Action does this from a repo secret). The
service account must be granted:
  - Search Console: added as a user on each property (Settings > Users)
  - GA4: added as Viewer on each property (Admin > Property Access Management)

Run:  python scripts/fetch_data.py
"""

import json
import os
import sys
import datetime as dt

from google.oauth2 import service_account
from googleapiclient.discovery import build
from google.analytics.data_v1beta import BetaAnalyticsDataClient
from google.analytics.data_v1beta.types import (
    RunReportRequest, DateRange, Metric, Dimension, OrderBy,
)

# ---------------------------------------------------------------------------
# CONFIG — one entry per property.
#   gsc  : the Search Console property identifier.
#          domain property -> "sc-domain:example.com"
#          URL-prefix      -> "https://example.com/"
#   ga4  : the numeric GA4 property id (Admin > Property Settings > Property ID),
#          or None if the site has no GA4 property.
# ---------------------------------------------------------------------------
SITES_CONFIG = [
    {"key": "compass-arabia.com",     "base": "compass-arabia.com",     "label": "Compass Arabia",     "gsc": "https://compass-arabia.com/",     "ga4": "540488783"},
    {"key": "compassfmgcc.com",       "base": "compassfmgcc.com",       "label": "Compass FM GCC",     "gsc": "https://compassfmgcc.com/",       "ga4": "540483026"},
    {"key": "compasswaterproof.com",  "base": "compasswaterproof.com",  "label": "Compass Waterproof", "gsc": "https://compasswaterproof.com/",  "ga4": "540489853"},
    {"key": "compass-lg.com",         "base": "compass-lg.com",         "label": "Compass Logistics",  "gsc": "https://compass-lg.com/",         "ga4": "542074726"},
    {"key": "sunsetmediame.com",      "base": "sunsetmediame.com",      "label": "Sunset Media",       "gsc": "https://sunsetmediame.com/",      "ga4": "541032468"},
    {"key": "compass-its.com",        "base": "compass-its.com",        "label": "Compass ITS",        "gsc": "https://compass-its.com/",        "ga4": None},
]

# GSC country dimension uses ISO-3166-1 alpha-3 lowercase codes.
MARKETS = {"QA": "qat", "SA": "sau", "AE": "are"}

GSC_LAG_DAYS = 3   # Search Console data is only final ~2-3 days back.
WINDOW_DAYS = 28

SCOPES = [
    "https://www.googleapis.com/auth/webmasters.readonly",
    "https://www.googleapis.com/auth/analytics.readonly",
]

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_PATH = os.path.join(REPO_ROOT, "data.json")


def creds():
    path = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")
    if not path or not os.path.exists(path):
        sys.exit("GOOGLE_APPLICATION_CREDENTIALS not set or file missing.")
    return service_account.Credentials.from_service_account_file(path, scopes=SCOPES)


def date_ranges(today):
    """Return (cur_start, cur_end, prev_start, prev_end) as ISO strings."""
    end = today - dt.timedelta(days=GSC_LAG_DAYS)
    start = end - dt.timedelta(days=WINDOW_DAYS - 1)
    prev_end = start - dt.timedelta(days=1)
    prev_start = prev_end - dt.timedelta(days=WINDOW_DAYS - 1)
    iso = lambda d: d.isoformat()
    return iso(start), iso(end), iso(prev_start), iso(prev_end)


# ----------------------------- Search Console ------------------------------

def gsc_query(svc, site_url, start, end, dimensions=None, country=None, row_limit=10):
    body = {"startDate": start, "endDate": end, "rowLimit": row_limit}
    if dimensions:
        body["dimensions"] = dimensions
    if country:
        body["dimensionFilterGroups"] = [{
            "filters": [{"dimension": "country", "operator": "equals", "expression": country}]
        }]
    return svc.searchanalytics().query(siteUrl=site_url, body=body).execute().get("rows", [])


def agg_totals(rows):
    """Aggregate (no-dimension) query returns a single row, or [] if no data."""
    if not rows:
        return None
    r = rows[0]
    return {
        "clicks": int(round(r.get("clicks", 0))),
        "impr": int(round(r.get("impressions", 0))),
        "ctr": round(r.get("ctr", 0) * 100, 1),
        "pos": round(r.get("position", 0), 1),
    }


def top_list(rows, order):
    """order='query'  -> [query, clicks, impr, ctr, pos]  (SITES.queries)
       order='page'   -> [url,   clicks, impr, ctr, pos]  (SITES.pages)
       order='kw'     -> [query, pos, clicks, impr]       (RANK.kw)"""
    out = []
    for r in rows:
        keys = r.get("keys", [""])[0]
        clicks = int(round(r.get("clicks", 0)))
        impr = int(round(r.get("impressions", 0)))
        ctr = round(r.get("ctr", 0) * 100, 1)
        pos = round(r.get("position", 0), 1)
        if order == "kw":
            out.append([keys, pos, clicks, impr])
        else:
            out.append([keys, clicks, impr, ctr, pos])
    return out


def fetch_gsc_site(svc, cfg, cur, prev):
    site = cfg["gsc"]
    cur_totals = agg_totals(gsc_query(svc, site, cur[0], cur[1], row_limit=1))
    prev_totals = agg_totals(gsc_query(svc, site, prev[0], prev[1], row_limit=1))
    queries = top_list(gsc_query(svc, site, cur[0], cur[1], dimensions=["query"]), "query")
    pages = top_list(gsc_query(svc, site, cur[0], cur[1], dimensions=["page"]), "page")

    rank = {}
    for m, code in MARKETS.items():
        totals = agg_totals(gsc_query(svc, site, cur[0], cur[1], country=code, row_limit=1))
        kw = top_list(gsc_query(svc, site, cur[0], cur[1], dimensions=["query"], country=code), "kw")
        if totals is None:
            totals = {"clicks": 0, "impr": 0, "ctr": 0.0, "pos": None}
        rank[m] = {**totals, "kw": kw}

    return {
        "cur": cur_totals or {"clicks": 0, "impr": 0, "ctr": 0.0, "pos": 0.0},
        "prev": prev_totals,  # None -> dashboard shows "no prior period"
        "queries": queries,
        "pages": pages,
    }, rank, (cur_totals["pos"] if cur_totals else None)


# --------------------------------- GA4 -------------------------------------

def fmt_dur(secs):
    secs = int(round(secs))
    if secs < 60:
        return f"{secs}s"
    return f"{secs // 60}m {secs % 60:02d}s"


def ga4_run(client, prop, metrics, dimensions=None, order_metric=None, limit=10):
    req = RunReportRequest(
        property=f"properties/{prop}",
        date_ranges=[DateRange(start_date=f"{WINDOW_DAYS}daysAgo", end_date="yesterday")],
        metrics=[Metric(name=m) for m in metrics],
        dimensions=[Dimension(name=d) for d in (dimensions or [])],
        limit=limit,
    )
    if order_metric:
        req.order_bys = [OrderBy(metric=OrderBy.MetricOrderBy(metric_name=order_metric), desc=True)]
    return client.run_report(req)


def fetch_ga4_site(client, prop):
    # Totals
    tot = ga4_run(client, prop, [
        "totalUsers", "sessions", "engagementRate",
        "userEngagementDuration", "eventCount", "keyEvents",
    ], limit=1)
    if not tot.rows:
        return {"users": 0, "sessions": 0, "engRate": 0.0, "avgEng": "0s",
                "events": 0, "keyEvents": 0, "channels": [], "topPages": []}
    v = tot.rows[0].metric_values
    users = int(v[0].value or 0)
    sessions = int(v[1].value or 0)
    eng_rate = round(float(v[2].value or 0) * 100, 2)
    eng_dur = float(v[3].value or 0)
    events = int(v[4].value or 0)
    key_events = int(float(v[5].value or 0))
    avg_eng = fmt_dur(eng_dur / sessions) if sessions else "0s"

    # Channels
    ch = ga4_run(client, prop, ["sessions"], ["sessionDefaultChannelGroup"],
                 order_metric="sessions", limit=25)
    channels = []
    for row in ch.rows:
        name = row.dimension_values[0].value
        s = int(row.metric_values[0].value or 0)
        pct = round(s / sessions * 100, 2) if sessions else 0.0
        channels.append([name, s, pct])

    # Top pages
    tp = ga4_run(client, prop, ["screenPageViews", "totalUsers"], ["pagePath"],
                 order_metric="screenPageViews", limit=10)
    top_pages = [[r.dimension_values[0].value,
                  int(r.metric_values[0].value or 0),
                  int(r.metric_values[1].value or 0)] for r in tp.rows]

    return {"users": users, "sessions": sessions, "engRate": eng_rate, "avgEng": avg_eng,
            "events": events, "keyEvents": key_events, "channels": channels, "topPages": top_pages}


# --------------------------------- main ------------------------------------

def append_history(hist, date_str, value):
    """Append [date, value] to a history list, replacing today's entry on re-run."""
    hist = list(hist or [])
    if hist and hist[-1][0] == date_str:
        hist[-1] = [date_str, value]
    else:
        hist.append([date_str, value])
    return hist


def main():
    today = dt.date.today()
    date_str = today.isoformat()
    cur_s, cur_e, prev_s, prev_e = date_ranges(today)
    print(f"GSC window cur={cur_s}..{cur_e} prev={prev_s}..{prev_e}")

    c = creds()
    gsc = build("webmasters", "v3", credentials=c, cache_discovery=False)
    ga = BetaAnalyticsDataClient(credentials=c)

    # Load existing data.json (for BACKLINKS, RANKHIST history, and per-site fallback).
    existing = {}
    if os.path.exists(DATA_PATH):
        with open(DATA_PATH, encoding="utf-8") as f:
            existing = json.load(f)
    old_sites = existing.get("SITES", {})
    old_rankhist = existing.get("RANKHIST", {})
    backlinks = existing.get("BACKLINKS", {})

    SITES, RANK, RANKHIST = {}, {}, {}

    for cfg in SITES_CONFIG:
        key = cfg["key"]
        old_entry = old_sites.get(key, {})

        # --- Search Console (critical for this site) ---
        try:
            gsc_data, rank, gcc_pos = fetch_gsc_site(gsc, cfg, (cur_s, cur_e), (prev_s, prev_e))
            RANK[key] = rank
            rh = old_rankhist.get(key, {})
            new_rh = {m: append_history(rh.get(m, []), date_str, rank[m]["pos"]) for m in MARKETS}
            new_rh["GCC"] = append_history(rh.get("GCC", []), date_str, gcc_pos)
            RANKHIST[key] = new_rh
            print(f"OK  GSC {key}: clicks={gsc_data['cur']['clicks']} pos={gsc_data['cur']['pos']}")
        except Exception as e:
            print(f"ERR GSC {key}: {e} — keeping previous GSC data", file=sys.stderr)
            gsc_data = {k: old_entry.get(k) for k in ("cur", "prev", "queries", "pages")}
            if key in existing.get("RANK", {}):
                RANK[key] = existing["RANK"][key]
            if key in old_rankhist:
                RANKHIST[key] = old_rankhist[key]

        # --- GA4 (independent; failure must not wipe GSC data) ---
        if cfg["ga4"]:
            try:
                ga4 = fetch_ga4_site(ga, cfg["ga4"])
                print(f"OK  GA4 {key}: sessions={ga4['sessions']} users={ga4['users']}")
            except Exception as e:
                print(f"ERR GA4 {key}: {e} — keeping previous GA4 data", file=sys.stderr)
                ga4 = old_entry.get("ga4")
        else:
            ga4 = None

        SITES[key] = {"base": cfg["base"], "label": cfg["label"], **gsc_data, "ga4": ga4}

    # BACKLINKS: preserve values, append today's date to each history (no API for this).
    for key, bl in backlinks.items():
        bl["history"] = append_history(bl.get("history", []), date_str, bl.get("total"))

    out = {
        "generated": date_str,
        "SITES": SITES,
        "BACKLINKS": backlinks,
        "RANK": RANK,
        "RANKHIST": RANKHIST,
    }
    with open(DATA_PATH, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=1)
    print(f"Wrote {DATA_PATH} ({len(SITES)} sites)")


if __name__ == "__main__":
    main()
