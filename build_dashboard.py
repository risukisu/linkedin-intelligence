"""
Build a clean browser-based LinkedIn Network Dashboard from the export data.
Outputs a single self-contained HTML file.
"""

import pandas as pd
import json
import os
from datetime import datetime, timedelta

from linkedin_data import find_export_dir, load_connections, load_shares, load_comments, load_reactions, load_profile, enrich_posts

EXPORT_DIR = find_export_dir()
OUTPUT_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "dashboard.html")

# =====================
# 1. LOAD & PROCESS DATA
# =====================

print("Loading data...")

conn_df = load_connections(EXPORT_DIR)
shares_df = load_shares(EXPORT_DIR)
comments_df = load_comments(EXPORT_DIR)
reactions_df = load_reactions(EXPORT_DIR)
profile_df = load_profile(EXPORT_DIR)
if profile_df is not None and len(profile_df) > 0:
    p = profile_df.iloc[0]
    profile_name = f"{p.get('First Name', '')} {p.get('Last Name', '')}".strip()
    profile_headline = str(p.get("Headline", "")) if pd.notna(p.get("Headline")) else ""
else:
    profile_name = "Your Network"
    profile_headline = ""

# =====================
# POST ENRICHMENT — match comments to posts by URL
# =====================

print("Enriching post data...")

posts_list_full = enrich_posts(shares_df, comments_df)

# Dashboard uses preview-only format (no full content needed in HTML)
posts_list = []
for p in posts_list_full:
    posts_list.append({
        "date": p["date"],
        "day": p["day"],
        "hour": p["hour"],
        "preview": p["preview"],
        "wordCount": p["wordCount"],
        "type": p["type"],
        "comments": p["comments"],
        "link": p["link"],
        "visibility": p["visibility"],
    })

# For chart data we need the shares_clean with URNs
shares_clean = shares_df.dropna(subset=["Date"]).copy()

# =====================
# ALL CONNECTIONS for filterable table
# =====================

print("Preparing connections data...")

all_connections = []
for _, r in conn_df.iterrows():
    all_connections.append({
        "name": r["Full Name"],
        "firstName": r["First Name"],
        "lastName": r["Last Name"],
        "company": r["Company"],
        "position": r["Position"],
        "seniority": r["Seniority"],
        "connected": r["Connected On"].strftime("%Y-%m-%d") if pd.notna(r["Connected On"]) else "",
        "year": int(r["Connected On"].year) if pd.notna(r["Connected On"]) else 0,
        "url": r.get("URL", "") if pd.notna(r.get("URL", "")) else "",
    })

# Get unique values for filter dropdowns
unique_companies = sorted(conn_df["Company"].value_counts().head(100).index.tolist())
unique_seniorities = ["C-Level / Founder", "VP", "Director", "Head of", "Manager / Lead", "Senior IC", "IC / Specialist", "Junior / Associate"]
unique_years = sorted(conn_df["Connected On"].dropna().dt.year.unique().tolist())

# =====================
# CHART DATA (same as before)
# =====================

top_companies = conn_df["Company"].value_counts().head(20)
companies_data = {"labels": top_companies.index.tolist(), "values": top_companies.values.tolist()}

seniority_order = ["C-Level / Founder", "VP", "Director", "Head of", "Manager / Lead", "Senior IC", "IC / Specialist", "Junior / Associate"]
seniority_counts = conn_df["Seniority"].value_counts().reindex(seniority_order).fillna(0).astype(int)
seniority_data = {"labels": seniority_counts.index.tolist(), "values": seniority_counts.values.tolist()}

monthly = conn_df.dropna(subset=["Connected On"]).set_index("Connected On").resample("ME").size().reset_index()
monthly.columns = ["Month", "New"]
monthly["Cumulative"] = monthly["New"].cumsum()
growth_data = {
    "labels": monthly["Month"].dt.strftime("%Y-%m").tolist(),
    "new": monthly["New"].tolist(),
    "cumulative": monthly["Cumulative"].tolist(),
}

yearly = conn_df.dropna(subset=["Connected On"]).copy()
yearly["Year"] = yearly["Connected On"].dt.year
yearly_counts = yearly.groupby("Year").size()
yearly_data = {"labels": yearly_counts.index.astype(str).tolist(), "values": yearly_counts.values.tolist()}

shares_m = shares_df.dropna(subset=["Date"]).set_index("Date").resample("ME").size().reset_index()
shares_m.columns = ["Month", "Posts"]
comments_m = comments_df.dropna(subset=["Date"]).set_index("Date").resample("ME").size().reset_index()
comments_m.columns = ["Month", "Comments"]
reactions_m = reactions_df.dropna(subset=["Date"]).set_index("Date").resample("ME").size().reset_index()
reactions_m.columns = ["Month", "Reactions"]
activity = shares_m.merge(comments_m, on="Month", how="outer").merge(reactions_m, on="Month", how="outer").fillna(0).sort_values("Month")
activity_data = {
    "labels": activity["Month"].dt.strftime("%Y-%m").tolist(),
    "posts": activity["Posts"].astype(int).tolist(),
    "comments": activity["Comments"].astype(int).tolist(),
    "reactions": activity["Reactions"].astype(int).tolist(),
}

sc = shares_df.dropna(subset=["Date"]).copy()
sc["Day"] = sc["Date"].dt.day_name()
day_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
by_day = sc["Day"].value_counts().reindex(day_order).fillna(0).astype(int)
day_data = {"labels": by_day.index.tolist(), "values": by_day.values.tolist()}

sc["Hour"] = sc["Date"].dt.hour
by_hour = sc["Hour"].value_counts().sort_index()
hour_data = {"labels": [f"{h}:00" for h in by_hour.index.tolist()], "values": by_hour.values.tolist()}

rxn_counts = reactions_df["Type"].value_counts() if "Type" in reactions_df.columns else pd.Series(dtype=int)
reactions_type_data = {"labels": rxn_counts.index.tolist(), "values": rxn_counts.values.tolist()}

clusters_s = conn_df["Company"].value_counts()
clusters_s = clusters_s[clusters_s >= 5]
clusters_data = {"labels": clusters_s.index.tolist(), "values": clusters_s.values.tolist()}

top_positions = conn_df["Position"].value_counts().head(20)
positions_data = {"labels": top_positions.index.tolist(), "values": top_positions.values.tolist()}

# Post type distribution
post_types = {}
for p in posts_list:
    t = p["type"]
    post_types[t] = post_types.get(t, 0) + 1
post_type_data = {"labels": list(post_types.keys()), "values": list(post_types.values())}

# Posts per month
posts_monthly = shares_clean.set_index("Date").resample("ME").size().reset_index()
posts_monthly.columns = ["Month", "Count"]
posts_monthly_data = {
    "labels": posts_monthly["Month"].dt.strftime("%Y-%m").tolist(),
    "values": posts_monthly["Count"].tolist(),
}

# Word count distribution buckets
wc_buckets = {"0 (Repost)": 0, "1-50": 0, "51-100": 0, "101-200": 0, "201-300": 0, "300+": 0}
for p in posts_list:
    w = p["wordCount"]
    if w == 0: wc_buckets["0 (Repost)"] += 1
    elif w <= 50: wc_buckets["1-50"] += 1
    elif w <= 100: wc_buckets["51-100"] += 1
    elif w <= 200: wc_buckets["101-200"] += 1
    elif w <= 300: wc_buckets["201-300"] += 1
    else: wc_buckets["300+"] += 1
word_count_data = {"labels": list(wc_buckets.keys()), "values": list(wc_buckets.values())}

# Dormant
cutoff = datetime.now() - timedelta(days=730)
dormant = conn_df[conn_df["Connected On"] < cutoff].sort_values("Connected On")
dormant_list = []
for _, r in dormant.head(200).iterrows():
    dormant_list.append({
        "name": r["Full Name"],
        "company": r["Company"],
        "position": r["Position"],
        "seniority": r["Seniority"],
        "connected": r["Connected On"].strftime("%Y-%m-%d") if pd.notna(r["Connected On"]) else "",
        "url": r.get("URL", "") if pd.notna(r.get("URL", "")) else "",
    })

senior = conn_df[conn_df["Seniority"].isin(["C-Level / Founder", "VP", "Director", "Head of"])].copy()

stats = {
    "total_connections": int(len(conn_df)),
    "unique_companies": int(conn_df["Company"].nunique()),
    "unique_positions": int(conn_df["Position"].nunique()),
    "total_posts": int(len(shares_df)),
    "total_comments": int(len(comments_df)),
    "total_reactions": int(len(reactions_df)),
    "senior_connections": int(len(senior)),
    "dormant_connections": int(len(dormant)),
    "earliest": conn_df["Connected On"].min().strftime("%b %Y") if conn_df["Connected On"].notna().any() else "N/A",
    "latest": conn_df["Connected On"].max().strftime("%b %Y") if conn_df["Connected On"].notna().any() else "N/A",
    "clusters_count": int(len(clusters_s)),
}

# =====================
# 2. BUILD HTML
# =====================

print("Building dashboard...")

html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>LinkedIn Intelligence</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.7/dist/chart.umd.min.js"></script>
<style>
:root {{
  --blue: #0A66C2;
  --blue-light: #E8F1FA;
  --blue-dark: #004182;
  --green: #057642;
  --amber: #E7A33E;
  --red: #CC1016;
  --bg: #F3F2EF;
  --card: #FFFFFF;
  --text: #191919;
  --text-muted: #666666;
  --border: #E0E0E0;
  --radius: 12px;
}}
* {{ margin:0; padding:0; box-sizing:border-box; }}
body {{ font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,'Helvetica Neue',Arial,sans-serif; background:var(--bg); color:var(--text); line-height:1.5; }}

/* Header */
.header {{ background:var(--blue); color:white; padding:24px 0; position:sticky; top:0; z-index:100; box-shadow:0 2px 12px rgba(0,0,0,.15); }}
.header-inner {{ max-width:1320px; margin:0 auto; padding:0 24px; display:flex; align-items:center; justify-content:space-between; }}
.header h1 {{ font-size:20px; font-weight:700; }}
.header p {{ font-size:13px; opacity:.85; margin-top:2px; }}
.header-right {{ font-size:13px; opacity:.8; text-align:right; }}

/* Nav */
nav {{ background:var(--card); border-bottom:1px solid var(--border); position:sticky; top:68px; z-index:99; }}
nav .nav-inner {{ max-width:1320px; margin:0 auto; padding:0 24px; display:flex; gap:2px; overflow-x:auto; }}
nav a {{ padding:12px 14px; text-decoration:none; color:var(--text-muted); font-size:13px; font-weight:600; white-space:nowrap; border-bottom:2px solid transparent; transition:all .15s; }}
nav a:hover, nav a.active {{ color:var(--blue); border-bottom-color:var(--blue); }}

/* Layout */
.container {{ max-width:1320px; margin:0 auto; padding:24px; }}
.section {{ display:none; animation:fadeIn .2s ease; }}
.section.active {{ display:block; }}
@keyframes fadeIn {{ from{{opacity:0;transform:translateY(6px)}} to{{opacity:1;transform:translateY(0)}} }}
.grid-2 {{ display:grid; grid-template-columns:1fr 1fr; gap:20px; }}
.grid-3 {{ display:grid; grid-template-columns:1fr 1fr 1fr; gap:20px; }}
@media(max-width:900px) {{ .grid-2,.grid-3 {{ grid-template-columns:1fr; }} }}

/* Cards */
.card {{ background:var(--card); border-radius:var(--radius); border:1px solid var(--border); padding:24px; margin-bottom:20px; }}
.card h2 {{ font-size:15px; font-weight:700; margin-bottom:16px; }}
.stats-grid {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(180px,1fr)); gap:14px; margin-bottom:24px; }}
.stat-card {{ background:var(--card); border-radius:var(--radius); padding:18px; border:1px solid var(--border); }}
.stat-card .label {{ font-size:11px; font-weight:600; text-transform:uppercase; letter-spacing:.5px; color:var(--text-muted); margin-bottom:4px; }}
.stat-card .value {{ font-size:28px; font-weight:700; color:var(--blue); line-height:1.2; }}
.stat-card .sub {{ font-size:11px; color:var(--text-muted); margin-top:2px; }}
.chart-container {{ position:relative; width:100%; max-height:400px; }}

/* Tables */
table {{ width:100%; border-collapse:collapse; font-size:13px; }}
thead th {{ background:var(--blue); color:white; padding:9px 12px; text-align:left; font-weight:600; font-size:11px; text-transform:uppercase; letter-spacing:.3px; position:sticky; top:0; z-index:2; }}
thead th:first-child {{ border-radius:8px 0 0 0; }}
thead th:last-child {{ border-radius:0 8px 0 0; }}
tbody td {{ padding:8px 12px; border-bottom:1px solid var(--border); }}
tbody tr:hover {{ background:var(--blue-light); }}
.table-wrapper {{ max-height:560px; overflow-y:auto; border-radius:8px; border:1px solid var(--border); }}

/* Badges */
.badge {{ display:inline-block; padding:2px 8px; border-radius:12px; font-size:11px; font-weight:600; white-space:nowrap; }}
.badge-blue {{ background:var(--blue-light); color:var(--blue); }}
.badge-green {{ background:#E6F4EA; color:var(--green); }}
.badge-amber {{ background:#FFF3E0; color:#B8860B; }}
.badge-red {{ background:#FDECEA; color:var(--red); }}
.badge-purple {{ background:#F3E5F5; color:#7B1FA2; }}
.badge-gray {{ background:#F5F5F5; color:#616161; }}

/* Inputs & Filters */
.search-box {{ width:100%; padding:10px 14px; border:1px solid var(--border); border-radius:8px; font-size:14px; margin-bottom:12px; outline:none; transition:border-color .15s; }}
.search-box:focus {{ border-color:var(--blue); box-shadow:0 0 0 3px rgba(10,102,194,.1); }}

/* Filter system */
.filter-bar {{ display:flex; gap:8px; flex-wrap:wrap; align-items:center; margin-bottom:14px; }}
.filter-tag {{ display:inline-flex; align-items:center; gap:6px; padding:5px 12px; border-radius:20px; font-size:12px; font-weight:600; background:var(--blue); color:white; animation:fadeIn .15s ease; }}
.filter-tag .remove {{ cursor:pointer; font-size:14px; opacity:.8; line-height:1; }}
.filter-tag .remove:hover {{ opacity:1; }}
.filter-add-btn {{ padding:5px 14px; border-radius:20px; font-size:12px; font-weight:600; border:1px dashed var(--blue); color:var(--blue); background:transparent; cursor:pointer; transition:all .15s; }}
.filter-add-btn:hover {{ background:var(--blue-light); }}

/* Filter dropdown */
.filter-dropdown {{ position:relative; display:inline-block; }}
.filter-menu {{ position:absolute; top:100%; left:0; margin-top:6px; background:var(--card); border:1px solid var(--border); border-radius:10px; box-shadow:0 8px 24px rgba(0,0,0,.12); z-index:50; min-width:280px; padding:12px; display:none; }}
.filter-menu.open {{ display:block; }}
.filter-menu label {{ display:block; font-size:12px; font-weight:600; color:var(--text-muted); margin-bottom:4px; text-transform:uppercase; letter-spacing:.3px; }}
.filter-menu select, .filter-menu input {{ width:100%; padding:8px 10px; border:1px solid var(--border); border-radius:6px; font-size:13px; margin-bottom:10px; outline:none; }}
.filter-menu select:focus, .filter-menu input:focus {{ border-color:var(--blue); }}
.filter-apply-btn {{ width:100%; padding:8px; border:none; background:var(--blue); color:white; border-radius:6px; font-size:13px; font-weight:600; cursor:pointer; }}
.filter-apply-btn:hover {{ background:var(--blue-dark); }}

.pill-group {{ display:flex; gap:6px; flex-wrap:wrap; margin-bottom:14px; }}
.pill {{ padding:6px 14px; border-radius:20px; font-size:12px; font-weight:600; border:1px solid var(--border); background:var(--card); cursor:pointer; transition:all .15s; }}
.pill:hover, .pill.active {{ background:var(--blue); color:white; border-color:var(--blue); }}

/* Post cards */
.post-card {{ border:1px solid var(--border); border-radius:10px; padding:16px; margin-bottom:12px; transition:border-color .15s; }}
.post-card:hover {{ border-color:var(--blue); }}
.post-meta {{ display:flex; gap:12px; align-items:center; margin-bottom:8px; flex-wrap:wrap; }}
.post-meta .date {{ font-size:12px; color:var(--text-muted); font-weight:600; }}
.post-preview {{ font-size:13px; color:var(--text); line-height:1.6; margin-bottom:8px; white-space:pre-wrap; word-break:break-word; }}
.post-stats {{ display:flex; gap:16px; font-size:12px; color:var(--text-muted); }}
.post-stats span {{ display:flex; align-items:center; gap:4px; }}
.post-link {{ font-size:12px; color:var(--blue); text-decoration:none; font-weight:600; }}
.post-link:hover {{ text-decoration:underline; }}

.result-count {{ font-size:13px; color:var(--text-muted); margin-bottom:12px; }}
</style>
</head>
<body>

<div class="header">
  <div class="header-inner">
    <div>
      <h1>LinkedIn Intelligence</h1>
      <p>{profile_name} — {profile_headline}</p>
    </div>
    <div class="header-right">
      {stats["total_connections"]:,} connections<br>
      {stats["earliest"]} – {stats["latest"]}
    </div>
  </div>
</div>

<nav>
  <div class="nav-inner">
    <a href="#" data-section="overview" class="active">Overview</a>
    <a href="#" data-section="connections">Connections</a>
    <a href="#" data-section="companies">Companies</a>
    <a href="#" data-section="seniority">Seniority</a>
    <a href="#" data-section="growth">Growth</a>
    <a href="#" data-section="posts">Posts</a>
    <a href="#" data-section="activity">Activity</a>
    <a href="#" data-section="clusters">Clusters</a>
    <a href="#" data-section="dormant">Dormant</a>
  </div>
</nav>

<div class="container">

  <!-- OVERVIEW -->
  <div class="section active" id="overview">
    <div class="stats-grid">
      <div class="stat-card"><div class="label">Connections</div><div class="value">{stats["total_connections"]:,}</div><div class="sub">Across {stats["unique_companies"]:,} companies</div></div>
      <div class="stat-card"><div class="label">Senior Network</div><div class="value">{stats["senior_connections"]:,}</div><div class="sub">VPs, Directors, C-Level, Founders</div></div>
      <div class="stat-card"><div class="label">Posts Published</div><div class="value">{stats["total_posts"]:,}</div><div class="sub">{stats["total_comments"]:,} comments made</div></div>
      <div class="stat-card"><div class="label">Reactions Given</div><div class="value">{stats["total_reactions"]:,}</div><div class="sub">Engagement with network</div></div>
      <div class="stat-card"><div class="label">Network Clusters</div><div class="value">{stats["clusters_count"]}</div><div class="sub">Companies with 5+ connections</div></div>
      <div class="stat-card"><div class="label">Dormant</div><div class="value">{stats["dormant_connections"]:,}</div><div class="sub">Connected 2+ years ago</div></div>
    </div>
    <div class="grid-2">
      <div class="card"><h2>Top 10 Companies</h2><div class="chart-container"><canvas id="overviewCompanies"></canvas></div></div>
      <div class="card"><h2>Seniority Distribution</h2><div class="chart-container"><canvas id="overviewSeniority"></canvas></div></div>
    </div>
    <div class="grid-2">
      <div class="card"><h2>Network Growth</h2><div class="chart-container"><canvas id="overviewGrowth"></canvas></div></div>
      <div class="card"><h2>Connections by Year</h2><div class="chart-container"><canvas id="overviewYearly"></canvas></div></div>
    </div>
  </div>

  <!-- CONNECTIONS (ALL — with multi-filter) -->
  <div class="section" id="connections">
    <div class="card">
      <h2>All Connections</h2>
      <input type="text" class="search-box" id="connSearch" placeholder="Search by name, company, or position...">
      <div class="filter-bar" id="connFilterBar">
        <div class="filter-dropdown" id="connFilterDropdown">
          <button class="filter-add-btn" id="connAddFilterBtn">+ Add Filter</button>
          <div class="filter-menu" id="connFilterMenu">
            <label>Filter Type</label>
            <select id="connFilterType">
              <option value="seniority">Seniority</option>
              <option value="company">Company</option>
              <option value="year">Connection Year</option>
              <option value="position">Position Contains</option>
            </select>
            <div id="connFilterValueWrap">
              <label>Value</label>
              <select id="connFilterValue"></select>
            </div>
            <div id="connFilterTextWrap" style="display:none">
              <label>Contains</label>
              <input type="text" id="connFilterText" placeholder="e.g. Engineer">
            </div>
            <button class="filter-apply-btn" id="connApplyFilter">Apply Filter</button>
          </div>
        </div>
      </div>
      <div class="result-count" id="connResultCount"></div>
      <div class="table-wrapper" id="connTableWrap"></div>
    </div>
  </div>

  <!-- COMPANIES -->
  <div class="section" id="companies">
    <div class="card"><h2>Top 20 Companies</h2><div class="chart-container" style="max-height:600px"><canvas id="companiesChart"></canvas></div></div>
    <div class="card"><h2>Company List</h2><div class="table-wrapper" id="companiesTableWrap"></div></div>
  </div>

  <!-- SENIORITY -->
  <div class="section" id="seniority">
    <div class="grid-2">
      <div class="card"><h2>Network by Seniority</h2><div class="chart-container"><canvas id="seniorityDonut"></canvas></div></div>
      <div class="card"><h2>Breakdown</h2><div class="table-wrapper" id="seniorityTableWrap"></div></div>
    </div>
    <div class="card"><h2>Top 20 Position Titles</h2><div class="chart-container" style="max-height:500px"><canvas id="positionsChart"></canvas></div></div>
  </div>

  <!-- GROWTH -->
  <div class="section" id="growth">
    <div class="card"><h2>Cumulative Network Growth</h2><div class="chart-container" style="max-height:450px"><canvas id="growthLine"></canvas></div></div>
    <div class="grid-2">
      <div class="card"><h2>New Connections per Month</h2><div class="chart-container"><canvas id="growthMonthly"></canvas></div></div>
      <div class="card"><h2>Connections by Year</h2><div class="chart-container"><canvas id="growthYearly"></canvas></div></div>
    </div>
  </div>

  <!-- POSTS (deep) -->
  <div class="section" id="posts">
    <div class="stats-grid">
      <div class="stat-card"><div class="label">Total Posts</div><div class="value">{len(posts_list)}</div></div>
      <div class="stat-card"><div class="label">Avg Words/Post</div><div class="value">{sum(p["wordCount"] for p in posts_list) // max(len(posts_list),1)}</div></div>
      <div class="stat-card"><div class="label">Your Comments</div><div class="value">{stats["total_comments"]}</div><div class="sub">On all posts (yours + others)</div></div>
      <div class="stat-card"><div class="label">Reactions Given</div><div class="value">{stats["total_reactions"]}</div></div>
    </div>
    <div class="grid-2">
      <div class="card"><h2>Posts per Month</h2><div class="chart-container"><canvas id="postsMonthly"></canvas></div></div>
      <div class="card"><h2>Post Type Distribution</h2><div class="chart-container"><canvas id="postTypeChart"></canvas></div></div>
    </div>
    <div class="grid-3">
      <div class="card"><h2>Posts by Day of Week</h2><div class="chart-container"><canvas id="postDayChart"></canvas></div></div>
      <div class="card"><h2>Posts by Hour</h2><div class="chart-container"><canvas id="postHourChart"></canvas></div></div>
      <div class="card"><h2>Word Count Distribution</h2><div class="chart-container"><canvas id="postWcChart"></canvas></div></div>
    </div>
    <div class="card">
      <h2>All Posts</h2>
      <input type="text" class="search-box" id="postSearch" placeholder="Search post content...">
      <div class="pill-group" id="postTypePills"></div>
      <div class="result-count" id="postResultCount"></div>
      <div id="postsList" style="max-height:700px;overflow-y:auto;"></div>
    </div>
  </div>

  <!-- ACTIVITY -->
  <div class="section" id="activity">
    <div class="card"><h2>Monthly Activity</h2><div class="chart-container" style="max-height:450px"><canvas id="activityLine"></canvas></div></div>
    <div class="grid-2">
      <div class="card"><h2>Reaction Types Given</h2><div class="chart-container"><canvas id="reactionsDonut"></canvas></div></div>
      <div class="card"><h2>Reaction Activity Over Time</h2><div class="chart-container"><canvas id="reactionsTimeline"></canvas></div></div>
    </div>
  </div>

  <!-- CLUSTERS -->
  <div class="section" id="clusters">
    <div class="grid-2">
      <div class="card"><h2>Network Clusters (5+ connections)</h2><div class="chart-container"><canvas id="clustersPie"></canvas></div></div>
      <div class="card"><h2>Cluster Details</h2><div class="table-wrapper" id="clustersTableWrap"></div></div>
    </div>
  </div>

  <!-- DORMANT -->
  <div class="section" id="dormant">
    <div class="card">
      <h2>Dormant Connections ({stats["dormant_connections"]:,} total)</h2>
      <input type="text" class="search-box" id="dormantSearch" placeholder="Search dormant connections...">
      <div class="table-wrapper" id="dormantTableWrap"></div>
    </div>
  </div>

</div>

<script>
const blue = '#0A66C2';
const palette = ['#0A66C2','#057642','#E7A33E','#CC1016','#5E35B1','#00838F','#C62828','#AD1457','#4527A0','#1565C0','#00695C','#EF6C00','#6A1B9A','#283593','#00796B','#D84315'];

Chart.defaults.font.family = "-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif";
Chart.defaults.font.size = 12;
Chart.defaults.plugins.legend.labels.usePointStyle = true;
Chart.defaults.plugins.legend.labels.pointStyle = 'circle';

// === DATA ===
const companies = {json.dumps(companies_data)};
const seniority = {json.dumps(seniority_data)};
const growth = {json.dumps(growth_data)};
const yearly = {json.dumps(yearly_data)};
const activityD = {json.dumps(activity_data)};
const dayData = {json.dumps(day_data)};
const hourData = {json.dumps(hour_data)};
const reactionsType = {json.dumps(reactions_type_data)};
const clustersD = {json.dumps(clusters_data)};
const positionsTop = {json.dumps(positions_data)};
const postTypeD = {json.dumps(post_type_data)};
const postsMonthlyD = {json.dumps(posts_monthly_data)};
const wordCountD = {json.dumps(word_count_data)};
const allPosts = {json.dumps(posts_list)};
const allConnections = {json.dumps(all_connections)};
const dormantD = {json.dumps(dormant_list)};
const uniqueCompanies = {json.dumps(unique_companies)};
const uniqueSeniorities = {json.dumps(unique_seniorities)};
const uniqueYears = {json.dumps(unique_years)};
const totalConn = {stats["total_connections"]};

// === NAV ===
document.querySelectorAll('nav a').forEach(a => {{
  a.addEventListener('click', e => {{
    e.preventDefault();
    document.querySelectorAll('nav a').forEach(x => x.classList.remove('active'));
    a.classList.add('active');
    document.querySelectorAll('.section').forEach(s => s.classList.remove('active'));
    document.getElementById(a.dataset.section).classList.add('active');
  }});
}});

// === HELPERS ===
function makeTable(headers, rows, id) {{
  const w = document.getElementById(id);
  let h = '<table><thead><tr>' + headers.map(x => '<th>'+x+'</th>').join('') + '</tr></thead><tbody>';
  rows.forEach(r => {{ h += '<tr>' + r.map(c => '<td>'+(c??'—')+'</td>').join('') + '</tr>'; }});
  h += '</tbody></table>';
  w.innerHTML = h;
}}

function badgeFor(s) {{
  const m = {{'C-Level / Founder':'badge-red','VP':'badge-amber','Director':'badge-blue','Head of':'badge-green','Manager / Lead':'badge-purple','Senior IC':'badge-blue','IC / Specialist':'badge-gray','Junior / Associate':'badge-gray'}};
  return '<span class="badge '+(m[s]||'badge-gray')+'">'+s+'</span>';
}}

function escHtml(s) {{ return s.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;'); }}

// === OVERVIEW ===
new Chart(document.getElementById('overviewCompanies'), {{
  type:'bar', data:{{ labels:companies.labels.slice(0,10), datasets:[{{ data:companies.values.slice(0,10), backgroundColor:blue, borderRadius:6, barPercentage:.7 }}] }},
  options:{{ indexAxis:'y', plugins:{{ legend:{{ display:false }} }}, scales:{{ x:{{ grid:{{ display:false }} }} }} }}
}});
new Chart(document.getElementById('overviewSeniority'), {{
  type:'doughnut', data:{{ labels:seniority.labels, datasets:[{{ data:seniority.values, backgroundColor:palette.slice(0,8), borderWidth:0 }}] }},
  options:{{ plugins:{{ legend:{{ position:'right' }} }}, cutout:'55%' }}
}});
new Chart(document.getElementById('overviewGrowth'), {{
  type:'line', data:{{ labels:growth.labels, datasets:[{{ label:'Cumulative', data:growth.cumulative, borderColor:blue, backgroundColor:'rgba(10,102,194,.08)', fill:true, tension:.3, pointRadius:0 }}] }},
  options:{{ plugins:{{ legend:{{ display:false }} }}, scales:{{ x:{{ display:false }}, y:{{ grid:{{ color:'#f0f0f0' }} }} }} }}
}});
new Chart(document.getElementById('overviewYearly'), {{
  type:'bar', data:{{ labels:yearly.labels, datasets:[{{ data:yearly.values, backgroundColor:blue, borderRadius:6, barPercentage:.6 }}] }},
  options:{{ plugins:{{ legend:{{ display:false }} }}, scales:{{ y:{{ grid:{{ color:'#f0f0f0' }} }} }} }}
}});

// === COMPANIES ===
new Chart(document.getElementById('companiesChart'), {{
  type:'bar', data:{{ labels:companies.labels, datasets:[{{ data:companies.values, backgroundColor:blue, borderRadius:4, barPercentage:.7 }}] }},
  options:{{ indexAxis:'y', plugins:{{ legend:{{ display:false }} }} }}
}});
makeTable(['Company','Connections','%'], companies.labels.map((c,i) => [c, companies.values[i], (companies.values[i]/totalConn*100).toFixed(1)+'%']), 'companiesTableWrap');

// === SENIORITY ===
new Chart(document.getElementById('seniorityDonut'), {{
  type:'doughnut', data:{{ labels:seniority.labels, datasets:[{{ data:seniority.values, backgroundColor:palette.slice(0,8), borderWidth:0 }}] }},
  options:{{ plugins:{{ legend:{{ position:'bottom' }} }}, cutout:'50%' }}
}});
makeTable(['Level','Count','%'], seniority.labels.map((s,i) => [s, seniority.values[i], (seniority.values[i]/totalConn*100).toFixed(1)+'%']), 'seniorityTableWrap');
new Chart(document.getElementById('positionsChart'), {{
  type:'bar', data:{{ labels:positionsTop.labels, datasets:[{{ data:positionsTop.values, backgroundColor:blue, borderRadius:4, barPercentage:.7 }}] }},
  options:{{ indexAxis:'y', plugins:{{ legend:{{ display:false }} }} }}
}});

// === GROWTH ===
new Chart(document.getElementById('growthLine'), {{
  type:'line', data:{{ labels:growth.labels, datasets:[{{ label:'Cumulative', data:growth.cumulative, borderColor:blue, backgroundColor:'rgba(10,102,194,.06)', fill:true, tension:.3, pointRadius:0 }}] }},
  options:{{ scales:{{ x:{{ ticks:{{ maxTicksLimit:20 }} }} }} }}
}});
new Chart(document.getElementById('growthMonthly'), {{
  type:'bar', data:{{ labels:growth.labels, datasets:[{{ label:'New', data:growth.new, backgroundColor:'rgba(10,102,194,.6)', borderRadius:2, barPercentage:1, categoryPercentage:1 }}] }},
  options:{{ plugins:{{ legend:{{ display:false }} }}, scales:{{ x:{{ display:false }} }} }}
}});
new Chart(document.getElementById('growthYearly'), {{
  type:'bar', data:{{ labels:yearly.labels, datasets:[{{ data:yearly.values, backgroundColor:blue, borderRadius:6, barPercentage:.6 }}] }},
  options:{{ plugins:{{ legend:{{ display:false }} }} }}
}});

// === POSTS ===
new Chart(document.getElementById('postsMonthly'), {{
  type:'bar', data:{{ labels:postsMonthlyD.labels, datasets:[{{ data:postsMonthlyD.values, backgroundColor:blue, borderRadius:3, barPercentage:.8 }}] }},
  options:{{ plugins:{{ legend:{{ display:false }} }}, scales:{{ x:{{ ticks:{{ maxTicksLimit:15 }} }} }} }}
}});
new Chart(document.getElementById('postTypeChart'), {{
  type:'doughnut', data:{{ labels:postTypeD.labels, datasets:[{{ data:postTypeD.values, backgroundColor:palette, borderWidth:0 }}] }},
  options:{{ plugins:{{ legend:{{ position:'right' }} }}, cutout:'50%' }}
}});
new Chart(document.getElementById('postDayChart'), {{
  type:'bar', data:{{ labels:dayData.labels, datasets:[{{ data:dayData.values, backgroundColor:blue, borderRadius:6, barPercentage:.6 }}] }},
  options:{{ plugins:{{ legend:{{ display:false }} }}, scales:{{ y:{{ beginAtZero:true }} }} }}
}});
new Chart(document.getElementById('postHourChart'), {{
  type:'bar', data:{{ labels:hourData.labels, datasets:[{{ data:hourData.values, backgroundColor:'#057642', borderRadius:6, barPercentage:.7 }}] }},
  options:{{ plugins:{{ legend:{{ display:false }} }}, scales:{{ y:{{ beginAtZero:true }} }} }}
}});
new Chart(document.getElementById('postWcChart'), {{
  type:'bar', data:{{ labels:wordCountD.labels, datasets:[{{ data:wordCountD.values, backgroundColor:'#E7A33E', borderRadius:6, barPercentage:.6 }}] }},
  options:{{ plugins:{{ legend:{{ display:false }} }}, scales:{{ y:{{ beginAtZero:true }} }} }}
}});

// Post list rendering
let postTypeFilter = 'all';
const postTypes = [...new Set(allPosts.map(p => p.type))];

// Build type pills
const pillsWrap = document.getElementById('postTypePills');
pillsWrap.innerHTML = '<span class="pill active" data-type="all">All</span>' + postTypes.map(t => '<span class="pill" data-type="'+t+'">'+t+'</span>').join('');

function renderPosts() {{
  const q = document.getElementById('postSearch').value.toLowerCase();
  let filtered = allPosts;
  if (postTypeFilter !== 'all') filtered = filtered.filter(p => p.type === postTypeFilter);
  if (q) filtered = filtered.filter(p => p.preview.toLowerCase().includes(q));

  document.getElementById('postResultCount').textContent = filtered.length + ' posts';

  const wrap = document.getElementById('postsList');
  if (filtered.length === 0) {{ wrap.innerHTML = '<p style="color:var(--text-muted);padding:20px">No posts match your filters.</p>'; return; }}

  let html = '';
  filtered.forEach(p => {{
    const typeBadge = {{'Media':'badge-purple','Link Share':'badge-blue','Long Text':'badge-green','Short Text':'badge-amber','Repost':'badge-gray'}}[p.type] || 'badge-gray';
    html += '<div class="post-card">';
    html += '<div class="post-meta">';
    html += '<span class="date">' + p.date + ' &middot; ' + p.day + ' ' + p.hour + ':00</span>';
    html += '<span class="badge ' + typeBadge + '">' + p.type + '</span>';
    if (p.comments > 0) html += '<span class="badge badge-green">' + p.comments + ' comment' + (p.comments>1?'s':'') + '</span>';
    html += '</div>';
    if (p.preview) html += '<div class="post-preview">' + escHtml(p.preview) + '</div>';
    html += '<div class="post-stats">';
    html += '<span>' + p.wordCount + ' words</span>';
    if (p.link) html += '<a href="' + p.link + '" target="_blank" class="post-link">View on LinkedIn &rarr;</a>';
    html += '</div></div>';
  }});
  wrap.innerHTML = html;
}}

pillsWrap.addEventListener('click', e => {{
  const pill = e.target.closest('.pill');
  if (!pill) return;
  pillsWrap.querySelectorAll('.pill').forEach(p => p.classList.remove('active'));
  pill.classList.add('active');
  postTypeFilter = pill.dataset.type;
  renderPosts();
}});
document.getElementById('postSearch').addEventListener('input', renderPosts);
renderPosts();

// === ACTIVITY ===
new Chart(document.getElementById('activityLine'), {{
  type:'line', data:{{ labels:activityD.labels, datasets:[
    {{ label:'Posts', data:activityD.posts, borderColor:blue, tension:.3, pointRadius:1 }},
    {{ label:'Comments', data:activityD.comments, borderColor:'#057642', tension:.3, pointRadius:1 }},
    {{ label:'Reactions', data:activityD.reactions, borderColor:'#E7A33E', tension:.3, pointRadius:1 }}
  ] }},
  options:{{ scales:{{ x:{{ ticks:{{ maxTicksLimit:20 }} }} }} }}
}});
new Chart(document.getElementById('reactionsDonut'), {{
  type:'doughnut', data:{{ labels:reactionsType.labels, datasets:[{{ data:reactionsType.values, backgroundColor:palette, borderWidth:0 }}] }},
  options:{{ plugins:{{ legend:{{ position:'bottom' }} }}, cutout:'50%' }}
}});
new Chart(document.getElementById('reactionsTimeline'), {{
  type:'line', data:{{ labels:activityD.labels, datasets:[{{ label:'Reactions Given', data:activityD.reactions, borderColor:'#E7A33E', backgroundColor:'rgba(231,163,62,.1)', fill:true, tension:.3, pointRadius:0 }}] }},
  options:{{ plugins:{{ legend:{{ display:false }} }}, scales:{{ x:{{ ticks:{{ maxTicksLimit:15 }} }} }} }}
}});

// === CLUSTERS ===
new Chart(document.getElementById('clustersPie'), {{
  type:'doughnut', data:{{ labels:clustersD.labels, datasets:[{{ data:clustersD.values, backgroundColor:palette.concat(palette), borderWidth:0 }}] }},
  options:{{ plugins:{{ legend:{{ position:'right', labels:{{ font:{{ size:11 }} }} }} }}, cutout:'40%' }}
}});
makeTable(['Company','Connections','%'], clustersD.labels.map((c,i) => [c, clustersD.values[i], (clustersD.values[i]/totalConn*100).toFixed(1)+'%']), 'clustersTableWrap');

// =============================================
// CONNECTIONS — multi-filter system
// =============================================
let connFilters = [];

function updateFilterValueOptions() {{
  const type = document.getElementById('connFilterType').value;
  const valWrap = document.getElementById('connFilterValueWrap');
  const txtWrap = document.getElementById('connFilterTextWrap');
  const sel = document.getElementById('connFilterValue');

  if (type === 'position') {{
    valWrap.style.display = 'none';
    txtWrap.style.display = 'block';
  }} else {{
    valWrap.style.display = 'block';
    txtWrap.style.display = 'none';
    sel.innerHTML = '';
    let opts = [];
    if (type === 'seniority') opts = uniqueSeniorities;
    else if (type === 'company') opts = uniqueCompanies;
    else if (type === 'year') opts = uniqueYears.map(String);
    opts.forEach(o => {{ const op = document.createElement('option'); op.value = o; op.textContent = o; sel.appendChild(op); }});
  }}
}}

document.getElementById('connFilterType').addEventListener('change', updateFilterValueOptions);
updateFilterValueOptions();

// Toggle dropdown
document.getElementById('connAddFilterBtn').addEventListener('click', e => {{
  e.stopPropagation();
  document.getElementById('connFilterMenu').classList.toggle('open');
}});
document.addEventListener('click', e => {{
  if (!e.target.closest('#connFilterDropdown')) document.getElementById('connFilterMenu').classList.remove('open');
}});

// Apply filter
document.getElementById('connApplyFilter').addEventListener('click', () => {{
  const type = document.getElementById('connFilterType').value;
  let value;
  if (type === 'position') {{
    value = document.getElementById('connFilterText').value.trim();
    if (!value) return;
  }} else {{
    value = document.getElementById('connFilterValue').value;
  }}
  // Prevent duplicate
  if (connFilters.some(f => f.type === type && f.value === value)) return;
  connFilters.push({{ type, value }});
  document.getElementById('connFilterMenu').classList.remove('open');
  document.getElementById('connFilterText').value = '';
  renderConnFilters();
  renderConnections();
}});

function renderConnFilters() {{
  const bar = document.getElementById('connFilterBar');
  // Remove old tags
  bar.querySelectorAll('.filter-tag').forEach(t => t.remove());
  const dropdown = document.getElementById('connFilterDropdown');
  connFilters.forEach((f, i) => {{
    const tag = document.createElement('span');
    tag.className = 'filter-tag';
    const labelMap = {{ seniority:'Seniority', company:'Company', year:'Year', position:'Position' }};
    tag.innerHTML = (labelMap[f.type]||f.type) + ': ' + f.value + ' <span class="remove" data-idx="'+i+'">&times;</span>';
    bar.insertBefore(tag, dropdown);
  }});
  // Bind remove
  bar.querySelectorAll('.filter-tag .remove').forEach(btn => {{
    btn.addEventListener('click', e => {{
      connFilters.splice(parseInt(e.target.dataset.idx), 1);
      renderConnFilters();
      renderConnections();
    }});
  }});
}}

function renderConnections() {{
  const q = document.getElementById('connSearch').value.toLowerCase();
  let data = allConnections;

  // Apply filters
  connFilters.forEach(f => {{
    if (f.type === 'seniority') data = data.filter(c => c.seniority === f.value);
    else if (f.type === 'company') data = data.filter(c => c.company === f.value);
    else if (f.type === 'year') data = data.filter(c => c.year === parseInt(f.value));
    else if (f.type === 'position') data = data.filter(c => c.position.toLowerCase().includes(f.value.toLowerCase()));
  }});

  // Apply search
  if (q) {{
    data = data.filter(c => c.name.toLowerCase().includes(q) || c.company.toLowerCase().includes(q) || c.position.toLowerCase().includes(q));
  }}

  document.getElementById('connResultCount').textContent = data.length.toLocaleString() + ' of ' + totalConn.toLocaleString() + ' connections';

  // Render table (limit to 500 for performance)
  const show = data.slice(0, 500);
  const wrap = document.getElementById('connTableWrap');
  let html = '<table><thead><tr><th>Name</th><th>Company</th><th>Position</th><th>Seniority</th><th>Connected</th></tr></thead><tbody>';
  show.forEach(c => {{
    const nameCell = c.url ? '<a href="'+c.url+'" target="_blank" style="color:'+blue+';text-decoration:none;font-weight:600">'+escHtml(c.name)+'</a>' : escHtml(c.name);
    html += '<tr><td>'+nameCell+'</td><td>'+escHtml(c.company)+'</td><td>'+escHtml(c.position)+'</td><td>'+badgeFor(c.seniority)+'</td><td>'+c.connected+'</td></tr>';
  }});
  if (data.length > 500) html += '<tr><td colspan="5" style="text-align:center;color:var(--text-muted);padding:12px">Showing 500 of '+data.length+' — refine your filters to see more</td></tr>';
  html += '</tbody></table>';
  wrap.innerHTML = html;
}}

document.getElementById('connSearch').addEventListener('input', renderConnections);
renderConnections();

// === DORMANT ===
function renderDormant(q) {{
  let data = dormantD;
  if (q) {{ const s = q.toLowerCase(); data = data.filter(c => c.name.toLowerCase().includes(s) || c.company.toLowerCase().includes(s) || c.position.toLowerCase().includes(s)); }}
  const wrap = document.getElementById('dormantTableWrap');
  let html = '<table><thead><tr><th>Name</th><th>Company</th><th>Position</th><th>Seniority</th><th>Connected</th></tr></thead><tbody>';
  data.forEach(c => {{
    const nameCell = c.url ? '<a href="'+c.url+'" target="_blank" style="color:'+blue+';text-decoration:none;font-weight:600">'+escHtml(c.name)+'</a>' : escHtml(c.name);
    html += '<tr><td>'+nameCell+'</td><td>'+escHtml(c.company)+'</td><td>'+escHtml(c.position)+'</td><td>'+badgeFor(c.seniority)+'</td><td>'+c.connected+'</td></tr>';
  }});
  html += '</tbody></table>';
  wrap.innerHTML = html;
}}
renderDormant('');
document.getElementById('dormantSearch').addEventListener('input', e => renderDormant(e.target.value));

</script>
</body>
</html>"""

with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
    f.write(html)

print(f"Dashboard saved to: {OUTPUT_PATH}")
