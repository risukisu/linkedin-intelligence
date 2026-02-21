"""
Shared LinkedIn data loading and processing module.
Used by both build_dashboard.py and query_linkedin.py.
"""

import pandas as pd
import os
import re
import glob
from urllib.parse import unquote


def find_export_dir(base_dir=None):
    """Auto-detect LinkedIn export directory."""
    if base_dir is None:
        base_dir = os.path.dirname(os.path.abspath(__file__))
    search_dirs = [base_dir, os.path.join(base_dir, "data exports")]
    patterns = ["Complete_LinkedInDataExport_*", "Basic_LinkedInDataExport_*"]
    candidates = []
    for d in search_dirs:
        for p in patterns:
            candidates.extend(glob.glob(os.path.join(d, p)))
    # Only keep directories (not zip files)
    candidates = [c for c in candidates if os.path.isdir(c)]
    if candidates:
        return max(candidates, key=os.path.getmtime)
    raise FileNotFoundError(
        "No LinkedIn export found. Place your LinkedInDataExport folder in the project directory or 'data exports' subfolder."
    )


def classify_seniority(position):
    """Classify a job title into a seniority level."""
    pos = str(position).lower()
    # Check director before C-Level because "cto" substring matches inside "director"
    if "director" in pos:
        return "Director"
    elif any(x in pos for x in ["ceo", "cto", "cfo", "coo", "cro", "chief", "founder", "co-founder", "owner", "partner"]):
        return "C-Level / Founder"
    elif any(x in pos for x in ["vp", "vice president"]):
        return "VP"
    elif any(x in pos for x in ["head of", "head "]):
        return "Head of"
    elif any(x in pos for x in ["manager", "lead", "team lead"]):
        return "Manager / Lead"
    elif any(x in pos for x in ["senior", "sr.", "sr "]):
        return "Senior IC"
    elif any(x in pos for x in ["junior", "jr.", "intern", "trainee", "associate"]):
        return "Junior / Associate"
    else:
        return "IC / Specialist"


def extract_urn(url):
    """Extract the LinkedIn URN ID from a share/activity URL."""
    if not isinstance(url, str):
        return None
    url = unquote(url)
    m = re.search(r'urn:li:(?:share|activity|ugcPost):(\d+)', url)
    return m.group(1) if m else None


def load_connections(export_dir):
    """Load and process Connections.csv with seniority classification."""
    path = os.path.join(export_dir, "Connections.csv")
    df = pd.read_csv(path, skiprows=2)
    df.columns = df.columns.str.strip()
    df["Connected On"] = pd.to_datetime(df["Connected On"], format="mixed", dayfirst=True, errors="coerce")
    for col in ["Company", "Position", "First Name", "Last Name"]:
        df[col] = df[col].fillna("Not Specified").str.strip()
    df["Full Name"] = df["First Name"] + " " + df["Last Name"]
    df["Seniority"] = df["Position"].apply(classify_seniority)
    return df


def load_shares(export_dir):
    """Load and process Shares.csv."""
    path = os.path.join(export_dir, "Shares.csv")
    if not os.path.exists(path):
        df = pd.DataFrame(columns=["Date", "ShareCommentary", "ShareLink", "SharedUrl", "MediaUrl", "Visibility"])
        df["Date"] = pd.to_datetime(df["Date"])
        return df
    df = pd.read_csv(path, on_bad_lines="skip", engine="python")
    df.columns = df.columns.str.strip()
    df["Date"] = pd.to_datetime(df["Date"], format="mixed", errors="coerce")
    return df


def load_comments(export_dir):
    """Load and process Comments.csv."""
    path = os.path.join(export_dir, "Comments.csv")
    if not os.path.exists(path):
        df = pd.DataFrame(columns=["Date", "Message", "Link"])
        df["Date"] = pd.to_datetime(df["Date"])
        return df
    df = pd.read_csv(path, on_bad_lines="skip", engine="python")
    df.columns = df.columns.str.strip()
    df["Date"] = pd.to_datetime(df["Date"], format="mixed", errors="coerce")
    return df


def load_reactions(export_dir):
    """Load and process Reactions.csv."""
    path = os.path.join(export_dir, "Reactions.csv")
    if not os.path.exists(path):
        df = pd.DataFrame(columns=["Date", "Type", "Link"])
        df["Date"] = pd.to_datetime(df["Date"])
        return df
    df = pd.read_csv(path, on_bad_lines="skip", engine="python")
    df.columns = df.columns.str.strip()
    df["Date"] = pd.to_datetime(df["Date"], format="mixed", errors="coerce")
    return df


def load_profile(export_dir):
    """Load Profile.csv for name and headline."""
    path = os.path.join(export_dir, "Profile.csv")
    if not os.path.exists(path):
        return None
    df = pd.read_csv(path)
    df.columns = df.columns.str.strip()
    return df


def enrich_posts(shares_df, comments_df):
    """Build enriched post list with type classification and comment counts."""
    shares_clean = shares_df.dropna(subset=["Date"]).copy()
    if "ShareLink" in shares_clean.columns:
        shares_clean["urn"] = shares_clean["ShareLink"].apply(extract_urn)
    else:
        shares_clean["urn"] = None

    comments_per_post = {}
    if "Link" in comments_df.columns:
        comments_df_copy = comments_df.copy()
        comments_df_copy["urn"] = comments_df_copy["Link"].apply(extract_urn)
        comments_per_post = comments_df_copy.groupby("urn").size().to_dict()

    posts_list = []
    for _, r in shares_clean.iterrows():
        commentary = str(r.get("ShareCommentary", "")) if pd.notna(r.get("ShareCommentary")) else ""
        commentary = commentary.replace('""', '"').strip().strip('"')
        word_count = len(commentary.split()) if commentary else 0
        urn = r.get("urn", "")
        link = r.get("ShareLink", "")
        shared_url = str(r.get("SharedUrl", "")) if pd.notna(r.get("SharedUrl")) else ""
        has_media = bool(str(r.get("MediaUrl", "")).strip()) if pd.notna(r.get("MediaUrl")) else False
        has_link = bool(shared_url.strip())
        visibility = str(r.get("Visibility", "")) if pd.notna(r.get("Visibility")) else ""

        if has_media:
            post_type = "Media"
        elif has_link:
            post_type = "Link Share"
        elif word_count > 100:
            post_type = "Long Text"
        elif word_count > 0:
            post_type = "Short Text"
        else:
            post_type = "Repost"

        comment_count = comments_per_post.get(urn, 0) if urn else 0

        posts_list.append({
            "date": r["Date"].strftime("%Y-%m-%d") if pd.notna(r["Date"]) else "",
            "day": r["Date"].strftime("%A") if pd.notna(r["Date"]) else "",
            "hour": int(r["Date"].hour) if pd.notna(r["Date"]) else 0,
            "content": commentary,
            "preview": commentary[:200] + ("..." if len(commentary) > 200 else ""),
            "wordCount": word_count,
            "type": post_type,
            "comments": comment_count,
            "link": link if isinstance(link, str) else "",
            "visibility": visibility,
        })

    return posts_list


def load_messages(export_dir):
    """Load and process messages.csv, grouped into conversations."""
    path = os.path.join(export_dir, "messages.csv")
    if not os.path.exists(path):
        return pd.DataFrame()
    df = pd.read_csv(path, on_bad_lines="skip", engine="python")
    df.columns = df.columns.str.strip()
    df["DATE"] = pd.to_datetime(df["DATE"], format="mixed", errors="coerce", utc=True)
    return df


def build_conversations(messages_df, owner_name="Pavel Averin"):
    """Group messages into conversations with metadata."""
    if messages_df.empty:
        return []

    convos = []
    for conv_id, msgs in messages_df.groupby("CONVERSATION ID"):
        msgs = msgs.sort_values("DATE", ascending=True)

        participants = set()
        for _, m in msgs.iterrows():
            fr = str(m.get("FROM", ""))
            to = str(m.get("TO", ""))
            if fr and fr != "nan":
                participants.add(fr)
            if to and to != "nan":
                participants.add(to)
        participants.discard(owner_name)
        other = ", ".join(sorted(participants)) if participants else "Unknown"

        last_msg = msgs.iloc[-1]
        last_from = str(last_msg.get("FROM", ""))
        last_date = last_msg["DATE"]

        content = str(last_msg.get("CONTENT", ""))
        # Strip HTML tags
        content = re.sub(r"<[^>]+>", " ", content)
        try:
            from html import unescape
            content = unescape(content)
        except Exception:
            pass
        content = re.sub(r"\s+", " ", content).strip()

        convos.append({
            "other": other,
            "msg_count": len(msgs),
            "last_date": last_date.strftime("%Y-%m-%d %H:%M") if pd.notna(last_date) else "",
            "last_from": last_from,
            "last_content": content[:500] + ("..." if len(content) > 500 else ""),
            "awaiting_your_reply": last_from != owner_name,
        })

    convos.sort(key=lambda x: x["last_date"], reverse=True)
    return convos


def load_all(export_dir):
    """Load all LinkedIn data. Returns dict with DataFrames and enriched posts."""
    conn_df = load_connections(export_dir)
    shares_df = load_shares(export_dir)
    comments_df = load_comments(export_dir)
    reactions_df = load_reactions(export_dir)
    messages_df = load_messages(export_dir)
    posts_list = enrich_posts(shares_df, comments_df)

    return {
        "connections": conn_df,
        "shares": shares_df,
        "comments": comments_df,
        "reactions": reactions_df,
        "messages": messages_df,
        "posts": posts_list,
    }
