"""
Generate a mock dashboard.html with realistic sample data for screenshots.
No real LinkedIn data is used.
"""

import json
import random
from datetime import datetime, timedelta

random.seed(42)

# =====================
# MOCK DATA GENERATION
# =====================

COMPANIES = [
    "Google", "Meta", "Amazon", "Microsoft", "Apple", "Salesforce", "Stripe",
    "Shopify", "HubSpot", "Slack", "Notion", "Figma", "Datadog", "Snowflake",
    "Twilio", "Atlassian", "Adobe", "Oracle", "SAP", "ServiceNow",
    "Zoom", "Okta", "MongoDB", "Elastic", "Confluent", "dbt Labs",
    "Gong", "Outreach", "Clari", "Clay", "Apollo.io", "ZoomInfo",
]

POSITIONS = {
    "C-Level / Founder": ["CEO", "CTO", "CRO", "Co-Founder", "Chief Revenue Officer", "Founder & CEO"],
    "VP": ["VP of Sales", "VP of Engineering", "VP of Marketing", "VP of Product", "VP Revenue Operations"],
    "Director": ["Director of Sales", "Director of Engineering", "Director of Marketing", "Sales Director", "Engineering Director"],
    "Head of": ["Head of Growth", "Head of Product", "Head of RevOps", "Head of Partnerships", "Head of Customer Success"],
    "Manager / Lead": ["Engineering Manager", "Product Manager", "Sales Manager", "Team Lead", "RevOps Manager", "GTM Lead"],
    "Senior IC": ["Senior Engineer", "Senior Account Executive", "Senior PM", "Senior Data Scientist", "Senior Designer"],
    "IC / Specialist": ["Software Engineer", "Account Executive", "Data Analyst", "Solutions Consultant", "GTM Engineer"],
    "Junior / Associate": ["Associate PM", "Junior Developer", "Sales Development Rep", "Marketing Associate", "Intern"],
}

SENIORITY_WEIGHTS = [0.12, 0.08, 0.12, 0.10, 0.18, 0.15, 0.20, 0.05]
SENIORITIES = list(POSITIONS.keys())

FIRST_NAMES = ["Alex", "Jordan", "Sam", "Taylor", "Morgan", "Casey", "Riley", "Avery", "Quinn", "Blake",
               "Cameron", "Drew", "Emerson", "Finley", "Harper", "Jamie", "Kendall", "Logan", "Parker", "Reese",
               "Sasha", "Tatum", "Dakota", "Ellis", "Frankie", "Gray", "Hayden", "Indigo", "Jules", "Kit"]
LAST_NAMES = ["Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis", "Rodriguez", "Martinez",
              "Anderson", "Taylor", "Thomas", "Moore", "Jackson", "Martin", "Lee", "Harris", "Clark", "Lewis",
              "Walker", "Hall", "Allen", "Young", "King", "Wright", "Lopez", "Hill", "Scott", "Green"]

def random_date(start_year=2016, end_year=2026):
    start = datetime(start_year, 1, 1)
    end = datetime(end_year, 1, 20)
    delta = (end - start).days
    return start + timedelta(days=random.randint(0, delta))

# Generate 2400 mock connections
connections = []
for i in range(2400):
    seniority = random.choices(SENIORITIES, weights=SENIORITY_WEIGHTS, k=1)[0]
    company = random.choice(COMPANIES)
    position = random.choice(POSITIONS[seniority])
    first = random.choice(FIRST_NAMES)
    last = random.choice(LAST_NAMES)
    conn_date = random_date()
    connections.append({
        "name": f"{first} {last}",
        "firstName": first,
        "lastName": last,
        "company": company,
        "position": position,
        "seniority": seniority,
        "connected": conn_date.strftime("%Y-%m-%d"),
        "year": conn_date.year,
        "url": f"https://www.linkedin.com/in/{first.lower()}-{last.lower()}-{random.randint(1000,9999)}",
    })

connections.sort(key=lambda x: x["connected"], reverse=True)

# Company counts
from collections import Counter
company_counter = Counter(c["company"] for c in connections)
top_companies = company_counter.most_common(20)
companies_data = {"labels": [c[0] for c in top_companies], "values": [c[1] for c in top_companies]}

# Seniority counts
sen_counter = Counter(c["seniority"] for c in connections)
seniority_data = {
    "labels": SENIORITIES,
    "values": [sen_counter.get(s, 0) for s in SENIORITIES],
}

# Monthly growth
from collections import defaultdict
monthly_counts = defaultdict(int)
for c in connections:
    month_key = c["connected"][:7]
    monthly_counts[month_key] += 1

sorted_months = sorted(monthly_counts.keys())
cumulative = 0
growth_labels = []
growth_new = []
growth_cumulative = []
for m in sorted_months:
    cumulative += monthly_counts[m]
    growth_labels.append(m)
    growth_new.append(monthly_counts[m])
    growth_cumulative.append(cumulative)

growth_data = {"labels": growth_labels, "new": growth_new, "cumulative": growth_cumulative}

# Yearly
yearly_counts = defaultdict(int)
for c in connections:
    yearly_counts[c["year"]] += 1
sorted_years = sorted(yearly_counts.keys())
yearly_data = {"labels": [str(y) for y in sorted_years], "values": [yearly_counts[y] for y in sorted_years]}

# Clusters (5+)
clusters = [(c, n) for c, n in company_counter.most_common() if n >= 5]
clusters_data = {"labels": [c[0] for c in clusters], "values": [c[1] for c in clusters]}

# Top positions
pos_counter = Counter(c["position"] for c in connections)
top_pos = pos_counter.most_common(20)
positions_data = {"labels": [p[0] for p in top_pos], "values": [p[1] for p in top_pos]}

# Unique values for filters
unique_companies = sorted(set(c[0] for c in company_counter.most_common(100)))
unique_years = sorted(set(c["year"] for c in connections))

# Dormant (2+ years ago)
cutoff = datetime(2024, 1, 20)
dormant_list = [c for c in connections if c["connected"] < cutoff.strftime("%Y-%m-%d")]
dormant_list.sort(key=lambda x: x["connected"])
dormant_list = dormant_list[:200]

# Senior connections
senior = [c for c in connections if c["seniority"] in ["C-Level / Founder", "VP", "Director", "Head of"]]

# =====================
# MOCK POSTS
# =====================

POST_TOPICS = [
    "5 lessons I learned scaling a RevOps team from 0 to 20 people...",
    "Hot take: Most CRMs are configured wrong. Here's the #1 mistake...",
    "We reduced our sales cycle by 40%. Here's the framework we used...",
    "The future of GTM engineering isn't what you think...",
    "Unpopular opinion: Your sales team doesn't need more leads. They need better data.",
    "I automated 80% of our reporting last quarter. Here's how (step by step)...",
    "3 books that changed how I think about revenue operations...",
    "Just shipped a new internal tool that saves our team 10 hours/week...",
    "Why I stopped chasing tools and started chasing process...",
    "The best ops teams I've seen all share these 3 traits...",
    "Hiring managers: stop requiring Salesforce Admin cert for RevOps roles...",
    "I failed my first automation project. Best thing that happened to me...",
    "Signal-based selling isn't a trend. It's the new default.",
    "Here's the exact Salesforce dashboard I use for pipeline reviews...",
    "Why your forecasting is broken and how to fix it in 3 steps...",
    "We integrated Clay + HubSpot + Slack. The results were insane...",
    "As a PM turned ops leader, here's what I wish I knew sooner...",
    "The simple framework I use for every process decision...",
    "Remote RevOps teams outperform. Here's the data...",
    "AI won't replace RevOps. But RevOps people who use AI will replace those who don't.",
    "Recreated Miro/Figma for RevOps teams with CRM elements and tools...",
    "The user story format I learned as a PM is now my best AI prompting tool...",
    "Lovable and n8n are a match made in heaven. Here's what I built...",
    "Stop building dashboards nobody looks at. Start here instead...",
]

POST_TYPES = ["Long Text", "Short Text", "Media", "Link Share", "Repost"]
POST_TYPE_WEIGHTS = [0.35, 0.25, 0.15, 0.15, 0.10]

posts_list = []
post_date = datetime(2023, 3, 1)
for i in range(160):
    post_date += timedelta(days=random.randint(1, 7))
    if post_date > datetime(2026, 1, 15):
        break
    post_type = random.choices(POST_TYPES, weights=POST_TYPE_WEIGHTS, k=1)[0]
    topic = random.choice(POST_TOPICS)
    wc = {"Long Text": random.randint(120, 350), "Short Text": random.randint(20, 80),
           "Media": random.randint(30, 150), "Link Share": random.randint(10, 60), "Repost": 0}[post_type]
    comments = random.randint(0, 8) if post_type != "Repost" else 0
    posts_list.append({
        "date": post_date.strftime("%Y-%m-%d"),
        "day": post_date.strftime("%A"),
        "hour": random.choice([8, 9, 10, 12, 13, 15, 17]),
        "preview": topic if post_type != "Repost" else "",
        "wordCount": wc,
        "type": post_type,
        "comments": comments,
        "link": f"https://www.linkedin.com/feed/update/urn:li:share:{random.randint(7000000000000000000, 7999999999999999999)}",
        "visibility": "MEMBER_NETWORK",
    })

posts_list.reverse()

# Post type distribution
pt_counter = Counter(p["type"] for p in posts_list)
post_type_data = {"labels": list(pt_counter.keys()), "values": list(pt_counter.values())}

# Posts per month
pm_counter = defaultdict(int)
for p in posts_list:
    pm_counter[p["date"][:7]] += 1
sorted_pm = sorted(pm_counter.keys())
posts_monthly_data = {"labels": sorted_pm, "values": [pm_counter[m] for m in sorted_pm]}

# Day of week
day_counter = Counter(p["day"] for p in posts_list)
day_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
day_data = {"labels": day_order, "values": [day_counter.get(d, 0) for d in day_order]}

# Hour
hour_counter = Counter(p["hour"] for p in posts_list)
sorted_hours = sorted(hour_counter.keys())
hour_data = {"labels": [f"{h}:00" for h in sorted_hours], "values": [hour_counter[h] for h in sorted_hours]}

# Word count buckets
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

# Activity timeline (monthly)
activity_months = sorted(set(growth_labels[-36:]))  # last 3 years
activity_data = {
    "labels": activity_months,
    "posts": [pm_counter.get(m, 0) for m in activity_months],
    "comments": [random.randint(2, 25) for _ in activity_months],
    "reactions": [random.randint(15, 80) for _ in activity_months],
}

# Reaction types
reactions_type_data = {
    "labels": ["LIKE", "PRAISE", "EMPATHY", "ENTERTAINMENT", "INTEREST"],
    "values": [892, 234, 187, 98, 52],
}

total_conn = len(connections)
total_posts = len(posts_list)
total_comments = sum(activity_data["comments"])
total_reactions = sum(reactions_type_data["values"])

stats = {
    "total_connections": total_conn,
    "unique_companies": len(set(c["company"] for c in connections)),
    "total_posts": total_posts,
    "total_comments": total_comments,
    "total_reactions": total_reactions,
    "senior_connections": len(senior),
    "dormant_connections": len(dormant_list),
    "clusters_count": len(clusters),
    "earliest": "Mar 2016",
    "latest": "Jan 2026",
}

# =====================
# BUILD HTML (same template as real dashboard)
# =====================

print("Building mock dashboard...")

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
.header {{ background:var(--blue); color:white; padding:24px 0; position:sticky; top:0; z-index:100; box-shadow:0 2px 12px rgba(0,0,0,.15); }}
.header-inner {{ max-width:1320px; margin:0 auto; padding:0 24px; display:flex; align-items:center; justify-content:space-between; }}
.header h1 {{ font-size:20px; font-weight:700; }}
.header p {{ font-size:13px; opacity:.85; margin-top:2px; }}
.header-right {{ font-size:13px; opacity:.8; text-align:right; }}
nav {{ background:var(--card); border-bottom:1px solid var(--border); position:sticky; top:68px; z-index:99; }}
nav .nav-inner {{ max-width:1320px; margin:0 auto; padding:0 24px; display:flex; gap:2px; overflow-x:auto; }}
nav a {{ padding:12px 14px; text-decoration:none; color:var(--text-muted); font-size:13px; font-weight:600; white-space:nowrap; border-bottom:2px solid transparent; transition:all .15s; }}
nav a:hover, nav a.active {{ color:var(--blue); border-bottom-color:var(--blue); }}
.container {{ max-width:1320px; margin:0 auto; padding:24px; }}
.section {{ display:none; animation:fadeIn .2s ease; }}
.section.active {{ display:block; }}
@keyframes fadeIn {{ from{{opacity:0;transform:translateY(6px)}} to{{opacity:1;transform:translateY(0)}} }}
.grid-2 {{ display:grid; grid-template-columns:1fr 1fr; gap:20px; }}
.grid-3 {{ display:grid; grid-template-columns:1fr 1fr 1fr; gap:20px; }}
@media(max-width:900px) {{ .grid-2,.grid-3 {{ grid-template-columns:1fr; }} }}
.card {{ background:var(--card); border-radius:var(--radius); border:1px solid var(--border); padding:24px; margin-bottom:20px; }}
.card h2 {{ font-size:15px; font-weight:700; margin-bottom:16px; }}
.stats-grid {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(180px,1fr)); gap:14px; margin-bottom:24px; }}
.stat-card {{ background:var(--card); border-radius:var(--radius); padding:18px; border:1px solid var(--border); }}
.stat-card .label {{ font-size:11px; font-weight:600; text-transform:uppercase; letter-spacing:.5px; color:var(--text-muted); margin-bottom:4px; }}
.stat-card .value {{ font-size:28px; font-weight:700; color:var(--blue); line-height:1.2; }}
.stat-card .sub {{ font-size:11px; color:var(--text-muted); margin-top:2px; }}
.chart-container {{ position:relative; width:100%; max-height:400px; }}
table {{ width:100%; border-collapse:collapse; font-size:13px; }}
thead th {{ background:var(--blue); color:white; padding:9px 12px; text-align:left; font-weight:600; font-size:11px; text-transform:uppercase; letter-spacing:.3px; position:sticky; top:0; z-index:2; }}
thead th:first-child {{ border-radius:8px 0 0 0; }}
thead th:last-child {{ border-radius:0 8px 0 0; }}
tbody td {{ padding:8px 12px; border-bottom:1px solid var(--border); }}
tbody tr:hover {{ background:var(--blue-light); }}
.table-wrapper {{ max-height:560px; overflow-y:auto; border-radius:8px; border:1px solid var(--border); }}
.badge {{ display:inline-block; padding:2px 8px; border-radius:12px; font-size:11px; font-weight:600; white-space:nowrap; }}
.badge-blue {{ background:var(--blue-light); color:var(--blue); }}
.badge-green {{ background:#E6F4EA; color:var(--green); }}
.badge-amber {{ background:#FFF3E0; color:#B8860B; }}
.badge-red {{ background:#FDECEA; color:var(--red); }}
.badge-purple {{ background:#F3E5F5; color:#7B1FA2; }}
.badge-gray {{ background:#F5F5F5; color:#616161; }}
.search-box {{ width:100%; padding:10px 14px; border:1px solid var(--border); border-radius:8px; font-size:14px; margin-bottom:12px; outline:none; transition:border-color .15s; }}
.search-box:focus {{ border-color:var(--blue); box-shadow:0 0 0 3px rgba(10,102,194,.1); }}
.filter-bar {{ display:flex; gap:8px; flex-wrap:wrap; align-items:center; margin-bottom:14px; }}
.filter-tag {{ display:inline-flex; align-items:center; gap:6px; padding:5px 12px; border-radius:20px; font-size:12px; font-weight:600; background:var(--blue); color:white; animation:fadeIn .15s ease; }}
.filter-tag .remove {{ cursor:pointer; font-size:14px; opacity:.8; line-height:1; }}
.filter-tag .remove:hover {{ opacity:1; }}
.filter-add-btn {{ padding:5px 14px; border-radius:20px; font-size:12px; font-weight:600; border:1px dashed var(--blue); color:var(--blue); background:transparent; cursor:pointer; transition:all .15s; }}
.filter-add-btn:hover {{ background:var(--blue-light); }}
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
      <p>Demo Dashboard — Sample Data</p>
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
  <div class="section active" id="overview">
    <div class="stats-grid">
      <div class="stat-card"><div class="label">Connections</div><div class="value">{stats["total_connections"]:,}</div><div class="sub">Across {stats["unique_companies"]} companies</div></div>
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
            <div id="connFilterValueWrap"><label>Value</label><select id="connFilterValue"></select></div>
            <div id="connFilterTextWrap" style="display:none"><label>Contains</label><input type="text" id="connFilterText" placeholder="e.g. Engineer"></div>
            <button class="filter-apply-btn" id="connApplyFilter">Apply Filter</button>
          </div>
        </div>
      </div>
      <div class="result-count" id="connResultCount"></div>
      <div class="table-wrapper" id="connTableWrap"></div>
    </div>
  </div>

  <div class="section" id="companies">
    <div class="card"><h2>Top 20 Companies</h2><div class="chart-container" style="max-height:600px"><canvas id="companiesChart"></canvas></div></div>
    <div class="card"><h2>Company List</h2><div class="table-wrapper" id="companiesTableWrap"></div></div>
  </div>

  <div class="section" id="seniority">
    <div class="grid-2">
      <div class="card"><h2>Network by Seniority</h2><div class="chart-container"><canvas id="seniorityDonut"></canvas></div></div>
      <div class="card"><h2>Breakdown</h2><div class="table-wrapper" id="seniorityTableWrap"></div></div>
    </div>
    <div class="card"><h2>Top 20 Position Titles</h2><div class="chart-container" style="max-height:500px"><canvas id="positionsChart"></canvas></div></div>
  </div>

  <div class="section" id="growth">
    <div class="card"><h2>Cumulative Network Growth</h2><div class="chart-container" style="max-height:450px"><canvas id="growthLine"></canvas></div></div>
    <div class="grid-2">
      <div class="card"><h2>New Connections per Month</h2><div class="chart-container"><canvas id="growthMonthly"></canvas></div></div>
      <div class="card"><h2>Connections by Year</h2><div class="chart-container"><canvas id="growthYearly"></canvas></div></div>
    </div>
  </div>

  <div class="section" id="posts">
    <div class="stats-grid">
      <div class="stat-card"><div class="label">Total Posts</div><div class="value">{total_posts}</div></div>
      <div class="stat-card"><div class="label">Avg Words/Post</div><div class="value">{sum(p["wordCount"] for p in posts_list) // max(len(posts_list),1)}</div></div>
      <div class="stat-card"><div class="label">Your Comments</div><div class="value">{total_comments}</div><div class="sub">On all posts</div></div>
      <div class="stat-card"><div class="label">Reactions Given</div><div class="value">{total_reactions}</div></div>
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

  <div class="section" id="activity">
    <div class="card"><h2>Monthly Activity</h2><div class="chart-container" style="max-height:450px"><canvas id="activityLine"></canvas></div></div>
    <div class="grid-2">
      <div class="card"><h2>Reaction Types Given</h2><div class="chart-container"><canvas id="reactionsDonut"></canvas></div></div>
      <div class="card"><h2>Reaction Activity Over Time</h2><div class="chart-container"><canvas id="reactionsTimeline"></canvas></div></div>
    </div>
  </div>

  <div class="section" id="clusters">
    <div class="grid-2">
      <div class="card"><h2>Network Clusters (5+ connections)</h2><div class="chart-container"><canvas id="clustersPie"></canvas></div></div>
      <div class="card"><h2>Cluster Details</h2><div class="table-wrapper" id="clustersTableWrap"></div></div>
    </div>
  </div>

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
const allConnections = {json.dumps(connections[:500])};
const dormantD = {json.dumps(dormant_list[:100])};
const uniqueCompanies = {json.dumps(unique_companies)};
const uniqueSeniorities = {json.dumps(SENIORITIES)};
const uniqueYears = {json.dumps(unique_years)};
const totalConn = {total_conn};

document.querySelectorAll('nav a').forEach(a => {{
  a.addEventListener('click', e => {{
    e.preventDefault();
    document.querySelectorAll('nav a').forEach(x => x.classList.remove('active'));
    a.classList.add('active');
    document.querySelectorAll('.section').forEach(s => s.classList.remove('active'));
    document.getElementById(a.dataset.section).classList.add('active');
  }});
}});

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

new Chart(document.getElementById('overviewCompanies'), {{ type:'bar', data:{{ labels:companies.labels.slice(0,10), datasets:[{{ data:companies.values.slice(0,10), backgroundColor:blue, borderRadius:6, barPercentage:.7 }}] }}, options:{{ indexAxis:'y', plugins:{{ legend:{{ display:false }} }}, scales:{{ x:{{ grid:{{ display:false }} }} }} }} }});
new Chart(document.getElementById('overviewSeniority'), {{ type:'doughnut', data:{{ labels:seniority.labels, datasets:[{{ data:seniority.values, backgroundColor:palette.slice(0,8), borderWidth:0 }}] }}, options:{{ plugins:{{ legend:{{ position:'right' }} }}, cutout:'55%' }} }});
new Chart(document.getElementById('overviewGrowth'), {{ type:'line', data:{{ labels:growth.labels, datasets:[{{ label:'Cumulative', data:growth.cumulative, borderColor:blue, backgroundColor:'rgba(10,102,194,.08)', fill:true, tension:.3, pointRadius:0 }}] }}, options:{{ plugins:{{ legend:{{ display:false }} }}, scales:{{ x:{{ display:false }}, y:{{ grid:{{ color:'#f0f0f0' }} }} }} }} }});
new Chart(document.getElementById('overviewYearly'), {{ type:'bar', data:{{ labels:yearly.labels, datasets:[{{ data:yearly.values, backgroundColor:blue, borderRadius:6, barPercentage:.6 }}] }}, options:{{ plugins:{{ legend:{{ display:false }} }}, scales:{{ y:{{ grid:{{ color:'#f0f0f0' }} }} }} }} }});

new Chart(document.getElementById('companiesChart'), {{ type:'bar', data:{{ labels:companies.labels, datasets:[{{ data:companies.values, backgroundColor:blue, borderRadius:4, barPercentage:.7 }}] }}, options:{{ indexAxis:'y', plugins:{{ legend:{{ display:false }} }} }} }});
makeTable(['Company','Connections','%'], companies.labels.map((c,i) => [c, companies.values[i], (companies.values[i]/totalConn*100).toFixed(1)+'%']), 'companiesTableWrap');

new Chart(document.getElementById('seniorityDonut'), {{ type:'doughnut', data:{{ labels:seniority.labels, datasets:[{{ data:seniority.values, backgroundColor:palette.slice(0,8), borderWidth:0 }}] }}, options:{{ plugins:{{ legend:{{ position:'bottom' }} }}, cutout:'50%' }} }});
makeTable(['Level','Count','%'], seniority.labels.map((s,i) => [s, seniority.values[i], (seniority.values[i]/totalConn*100).toFixed(1)+'%']), 'seniorityTableWrap');
new Chart(document.getElementById('positionsChart'), {{ type:'bar', data:{{ labels:positionsTop.labels, datasets:[{{ data:positionsTop.values, backgroundColor:blue, borderRadius:4, barPercentage:.7 }}] }}, options:{{ indexAxis:'y', plugins:{{ legend:{{ display:false }} }} }} }});

new Chart(document.getElementById('growthLine'), {{ type:'line', data:{{ labels:growth.labels, datasets:[{{ label:'Cumulative', data:growth.cumulative, borderColor:blue, backgroundColor:'rgba(10,102,194,.06)', fill:true, tension:.3, pointRadius:0 }}] }}, options:{{ scales:{{ x:{{ ticks:{{ maxTicksLimit:20 }} }} }} }} }});
new Chart(document.getElementById('growthMonthly'), {{ type:'bar', data:{{ labels:growth.labels, datasets:[{{ label:'New', data:growth.new, backgroundColor:'rgba(10,102,194,.6)', borderRadius:2, barPercentage:1, categoryPercentage:1 }}] }}, options:{{ plugins:{{ legend:{{ display:false }} }}, scales:{{ x:{{ display:false }} }} }} }});
new Chart(document.getElementById('growthYearly'), {{ type:'bar', data:{{ labels:yearly.labels, datasets:[{{ data:yearly.values, backgroundColor:blue, borderRadius:6, barPercentage:.6 }}] }}, options:{{ plugins:{{ legend:{{ display:false }} }} }} }});

new Chart(document.getElementById('postsMonthly'), {{ type:'bar', data:{{ labels:postsMonthlyD.labels, datasets:[{{ data:postsMonthlyD.values, backgroundColor:blue, borderRadius:3, barPercentage:.8 }}] }}, options:{{ plugins:{{ legend:{{ display:false }} }}, scales:{{ x:{{ ticks:{{ maxTicksLimit:15 }} }} }} }} }});
new Chart(document.getElementById('postTypeChart'), {{ type:'doughnut', data:{{ labels:postTypeD.labels, datasets:[{{ data:postTypeD.values, backgroundColor:palette, borderWidth:0 }}] }}, options:{{ plugins:{{ legend:{{ position:'right' }} }}, cutout:'50%' }} }});
new Chart(document.getElementById('postDayChart'), {{ type:'bar', data:{{ labels:dayData.labels, datasets:[{{ data:dayData.values, backgroundColor:blue, borderRadius:6, barPercentage:.6 }}] }}, options:{{ plugins:{{ legend:{{ display:false }} }}, scales:{{ y:{{ beginAtZero:true }} }} }} }});
new Chart(document.getElementById('postHourChart'), {{ type:'bar', data:{{ labels:hourData.labels, datasets:[{{ data:hourData.values, backgroundColor:'#057642', borderRadius:6, barPercentage:.7 }}] }}, options:{{ plugins:{{ legend:{{ display:false }} }}, scales:{{ y:{{ beginAtZero:true }} }} }} }});
new Chart(document.getElementById('postWcChart'), {{ type:'bar', data:{{ labels:wordCountD.labels, datasets:[{{ data:wordCountD.values, backgroundColor:'#E7A33E', borderRadius:6, barPercentage:.6 }}] }}, options:{{ plugins:{{ legend:{{ display:false }} }}, scales:{{ y:{{ beginAtZero:true }} }} }} }});

let postTypeFilter = 'all';
const postTypes = [...new Set(allPosts.map(p => p.type))];
const pillsWrap = document.getElementById('postTypePills');
pillsWrap.innerHTML = '<span class="pill active" data-type="all">All</span>' + postTypes.map(t => '<span class="pill" data-type="'+t+'">'+t+'</span>').join('');
function renderPosts() {{
  const q = document.getElementById('postSearch').value.toLowerCase();
  let filtered = allPosts;
  if (postTypeFilter !== 'all') filtered = filtered.filter(p => p.type === postTypeFilter);
  if (q) filtered = filtered.filter(p => p.preview.toLowerCase().includes(q));
  document.getElementById('postResultCount').textContent = filtered.length + ' posts';
  const wrap = document.getElementById('postsList');
  if (filtered.length === 0) {{ wrap.innerHTML = '<p style="color:var(--text-muted);padding:20px">No posts match.</p>'; return; }}
  let html = '';
  filtered.forEach(p => {{
    const tb = {{'Media':'badge-purple','Link Share':'badge-blue','Long Text':'badge-green','Short Text':'badge-amber','Repost':'badge-gray'}}[p.type]||'badge-gray';
    html += '<div class="post-card"><div class="post-meta"><span class="date">'+p.date+' &middot; '+p.day+' '+p.hour+':00</span><span class="badge '+tb+'">'+p.type+'</span>';
    if (p.comments>0) html += '<span class="badge badge-green">'+p.comments+' comment'+(p.comments>1?'s':'')+'</span>';
    html += '</div>';
    if (p.preview) html += '<div class="post-preview">'+escHtml(p.preview)+'</div>';
    html += '<div class="post-stats"><span>'+p.wordCount+' words</span>';
    if (p.link) html += '<a href="'+p.link+'" target="_blank" class="post-link">View on LinkedIn &rarr;</a>';
    html += '</div></div>';
  }});
  wrap.innerHTML = html;
}}
pillsWrap.addEventListener('click', e => {{ const pill = e.target.closest('.pill'); if (!pill) return; pillsWrap.querySelectorAll('.pill').forEach(p => p.classList.remove('active')); pill.classList.add('active'); postTypeFilter = pill.dataset.type; renderPosts(); }});
document.getElementById('postSearch').addEventListener('input', renderPosts);
renderPosts();

new Chart(document.getElementById('activityLine'), {{ type:'line', data:{{ labels:activityD.labels, datasets:[ {{ label:'Posts', data:activityD.posts, borderColor:blue, tension:.3, pointRadius:1 }}, {{ label:'Comments', data:activityD.comments, borderColor:'#057642', tension:.3, pointRadius:1 }}, {{ label:'Reactions', data:activityD.reactions, borderColor:'#E7A33E', tension:.3, pointRadius:1 }} ] }}, options:{{ scales:{{ x:{{ ticks:{{ maxTicksLimit:20 }} }} }} }} }});
new Chart(document.getElementById('reactionsDonut'), {{ type:'doughnut', data:{{ labels:reactionsType.labels, datasets:[{{ data:reactionsType.values, backgroundColor:palette, borderWidth:0 }}] }}, options:{{ plugins:{{ legend:{{ position:'bottom' }} }}, cutout:'50%' }} }});
new Chart(document.getElementById('reactionsTimeline'), {{ type:'line', data:{{ labels:activityD.labels, datasets:[{{ label:'Reactions', data:activityD.reactions, borderColor:'#E7A33E', backgroundColor:'rgba(231,163,62,.1)', fill:true, tension:.3, pointRadius:0 }}] }}, options:{{ plugins:{{ legend:{{ display:false }} }}, scales:{{ x:{{ ticks:{{ maxTicksLimit:15 }} }} }} }} }});

new Chart(document.getElementById('clustersPie'), {{ type:'doughnut', data:{{ labels:clustersD.labels, datasets:[{{ data:clustersD.values, backgroundColor:palette.concat(palette), borderWidth:0 }}] }}, options:{{ plugins:{{ legend:{{ position:'right', labels:{{ font:{{ size:11 }} }} }} }}, cutout:'40%' }} }});
makeTable(['Company','Connections','%'], clustersD.labels.map((c,i) => [c, clustersD.values[i], (clustersD.values[i]/totalConn*100).toFixed(1)+'%']), 'clustersTableWrap');

let connFilters = [];
function updateFilterValueOptions() {{
  const type = document.getElementById('connFilterType').value;
  const valWrap = document.getElementById('connFilterValueWrap');
  const txtWrap = document.getElementById('connFilterTextWrap');
  const sel = document.getElementById('connFilterValue');
  if (type === 'position') {{ valWrap.style.display='none'; txtWrap.style.display='block'; }}
  else {{ valWrap.style.display='block'; txtWrap.style.display='none'; sel.innerHTML='';
    let opts = type==='seniority'?uniqueSeniorities:type==='company'?uniqueCompanies:uniqueYears.map(String);
    opts.forEach(o => {{ const op=document.createElement('option'); op.value=o; op.textContent=o; sel.appendChild(op); }});
  }}
}}
document.getElementById('connFilterType').addEventListener('change', updateFilterValueOptions);
updateFilterValueOptions();
document.getElementById('connAddFilterBtn').addEventListener('click', e => {{ e.stopPropagation(); document.getElementById('connFilterMenu').classList.toggle('open'); }});
document.addEventListener('click', e => {{ if (!e.target.closest('#connFilterDropdown')) document.getElementById('connFilterMenu').classList.remove('open'); }});
document.getElementById('connApplyFilter').addEventListener('click', () => {{
  const type = document.getElementById('connFilterType').value;
  let value = type==='position' ? document.getElementById('connFilterText').value.trim() : document.getElementById('connFilterValue').value;
  if (!value) return;
  if (connFilters.some(f => f.type===type && f.value===value)) return;
  connFilters.push({{ type, value }});
  document.getElementById('connFilterMenu').classList.remove('open');
  document.getElementById('connFilterText').value = '';
  renderConnFilters(); renderConnections();
}});
function renderConnFilters() {{
  const bar = document.getElementById('connFilterBar');
  bar.querySelectorAll('.filter-tag').forEach(t => t.remove());
  const dd = document.getElementById('connFilterDropdown');
  connFilters.forEach((f,i) => {{
    const tag = document.createElement('span'); tag.className='filter-tag';
    const lm = {{ seniority:'Seniority', company:'Company', year:'Year', position:'Position' }};
    tag.innerHTML = (lm[f.type]||f.type)+': '+f.value+' <span class="remove" data-idx="'+i+'">&times;</span>';
    bar.insertBefore(tag, dd);
  }});
  bar.querySelectorAll('.filter-tag .remove').forEach(btn => {{
    btn.addEventListener('click', e => {{ connFilters.splice(parseInt(e.target.dataset.idx),1); renderConnFilters(); renderConnections(); }});
  }});
}}
function renderConnections() {{
  const q = document.getElementById('connSearch').value.toLowerCase();
  let data = allConnections;
  connFilters.forEach(f => {{
    if (f.type==='seniority') data=data.filter(c=>c.seniority===f.value);
    else if (f.type==='company') data=data.filter(c=>c.company===f.value);
    else if (f.type==='year') data=data.filter(c=>c.year===parseInt(f.value));
    else if (f.type==='position') data=data.filter(c=>c.position.toLowerCase().includes(f.value.toLowerCase()));
  }});
  if (q) data=data.filter(c=>c.name.toLowerCase().includes(q)||c.company.toLowerCase().includes(q)||c.position.toLowerCase().includes(q));
  document.getElementById('connResultCount').textContent = data.length.toLocaleString()+' of '+totalConn.toLocaleString()+' connections';
  const show=data.slice(0,500);
  const wrap=document.getElementById('connTableWrap');
  let html='<table><thead><tr><th>Name</th><th>Company</th><th>Position</th><th>Seniority</th><th>Connected</th></tr></thead><tbody>';
  show.forEach(c=>{{ html+='<tr><td>'+escHtml(c.name)+'</td><td>'+escHtml(c.company)+'</td><td>'+escHtml(c.position)+'</td><td>'+badgeFor(c.seniority)+'</td><td>'+c.connected+'</td></tr>'; }});
  if(data.length>500) html+='<tr><td colspan="5" style="text-align:center;color:var(--text-muted);padding:12px">Showing 500 of '+data.length+'</td></tr>';
  html+='</tbody></table>';
  wrap.innerHTML=html;
}}
document.getElementById('connSearch').addEventListener('input', renderConnections);
renderConnections();

function renderDormant(q) {{
  let data=dormantD;
  if(q){{ const s=q.toLowerCase(); data=data.filter(c=>c.name.toLowerCase().includes(s)||c.company.toLowerCase().includes(s)||c.position.toLowerCase().includes(s)); }}
  const wrap=document.getElementById('dormantTableWrap');
  let html='<table><thead><tr><th>Name</th><th>Company</th><th>Position</th><th>Seniority</th><th>Connected</th></tr></thead><tbody>';
  data.forEach(c=>{{ html+='<tr><td>'+escHtml(c.name)+'</td><td>'+escHtml(c.company)+'</td><td>'+escHtml(c.position)+'</td><td>'+badgeFor(c.seniority)+'</td><td>'+c.connected+'</td></tr>'; }});
  html+='</tbody></table>';
  wrap.innerHTML=html;
}}
renderDormant('');
document.getElementById('dormantSearch').addEventListener('input', e => renderDormant(e.target.value));
</script>
</body>
</html>"""

with open("/Users/pavelaverin/Desktop/LinkedIn Skill/mock_dashboard.html", "w", encoding="utf-8") as f:
    f.write(html)

print("Mock dashboard saved to mock_dashboard.html")
