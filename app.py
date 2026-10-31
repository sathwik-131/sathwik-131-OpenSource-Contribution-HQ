import json
import re
import uuid
from pathlib import Path
from datetime import date

import pandas as pd
import plotly.express as px
import requests
import streamlit as st

st.set_page_config(
    page_title="OpenSource | Contribution HQ",
    page_icon="🏆",
    layout="wide",
    initial_sidebar_state="expanded",
)

DATA_FILE = Path("participants.json")
SAMPLE_FILE = Path("sample_data.json")
CONFIG_FILE = Path("hackathon_config.json")
GITHUB_API = "https://api.github.com"

POINTS = {"features": 10, "bug_fixes": 5, "documentation": 2, "tests": 4}
LABELS = {
    "features": "Features",
    "bug_fixes": "Bug fixes",
    "documentation": "Documentation",
    "tests": "Tests",
}
MEDALS = ["🥇", "🥈", "🥉"]
DEFAULT_CONFIG = {
    "name": "Open Source Contribution Hackathon",
    "description": "Build, contribute and create meaningful open-source impact.",
    "start_date": "2026-11-15",
    "end_date": "2026-11-16",
    "repository": "",
    "organization": "",
    "status": "Upcoming",
    "points": {
        "features": 10,
        "bug_fixes": 5,
        "documentation": 2,
        "tests": 4
    }
}


def load_config():
    if CONFIG_FILE.exists():
        try:
            saved = json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
            if isinstance(saved, dict):
                return {**DEFAULT_CONFIG, **saved}
        except (json.JSONDecodeError, OSError):
            st.error("Could not read hackathon_config.json.")

    return DEFAULT_CONFIG.copy()


def save_config(config):
    CONFIG_FILE.write_text(
        json.dumps(config, indent=4),
        encoding="utf-8"
    )

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Space+Grotesk:wght@500;600;700&display=swap');
.stApp {background:radial-gradient(ellipse at 15% 0%,#14243b 0%,#080d18 45%);color:#edf4ff}
html,body,[class*="css"]{font-family:'DM Sans',sans-serif}
h1,h2,h3{font-family:'Space Grotesk',sans-serif!important;letter-spacing:-.03em}
[data-testid="stSidebar"]{background:#0b1321;border-right:1px solid #223149}
[data-testid="stMetric"]{background:linear-gradient(145deg,#142238,#0f1929);border:1px solid #2a3d57;border-radius:16px;padding:17px 18px}
[data-testid="stMetricLabel"]{color:#9fb0c7!important}
[data-testid="stMetricValue"]{color:#f4f8ff!important;font-family:'Space Grotesk',sans-serif}
.hero{padding:26px 28px;border-radius:20px;margin:4px 0 22px;background:linear-gradient(110deg,rgba(25,48,72,.96),rgba(15,28,46,.94));border:1px solid #2b4560}
.eyebrow{color:#67e8c2;font-size:12px;font-weight:700;letter-spacing:.16em;text-transform:uppercase}
.hero h1{margin:7px 0 5px;font-size:34px;color:#f3f7ff}
.hero p{color:#a9bad0;margin:0;font-size:14px}
.section-note{color:#91a2b9;font-size:13px;margin-top:-8px}
.podium{background:linear-gradient(145deg,#17263a,#101827);border:1px solid #2c4059;border-radius:16px;padding:20px;text-align:center;min-height:155px}
.podium .medal{font-size:28px}.podium .name{font-family:'Space Grotesk';font-weight:700;font-size:19px;color:#f3f7ff}
.podium .score{color:#67e8c2;font-size:25px;font-weight:700;margin-top:6px}.podium .small{color:#91a2b9;font-size:12px}
hr{border-color:#26364d!important}
</style>
""", unsafe_allow_html=True)


def sample_participants():
    return [
        {
            "name": "Sathwik",
            "contributions": {"features": 3, "bug_fixes": 2, "documentation": 1, "tests": 2},
            "contribution_records": []
        },
        {
            "name": "Rahul",
            "contributions": {"features": 1, "bug_fixes": 4, "documentation": 2, "tests": 1},
            "contribution_records": []
        },
        {
            "name": "Arjun",
            "contributions": {"features": 2, "bug_fixes": 1, "documentation": 5, "tests": 3},
            "contribution_records": []
        },
    ]


def load_participants():
    source = DATA_FILE if DATA_FILE.exists() else SAMPLE_FILE

    if source.exists():
        try:
            raw = json.loads(source.read_text(encoding="utf-8"))

            if isinstance(raw, list):
                result = []

                for person in raw:
                    if isinstance(person, dict) and str(person.get("name", "")).strip():
                        c = person.get("contributions", {})
                        records = person.get("contribution_records", [])

                        result.append({
                            "name": str(person["name"]).strip(),
                            "contributions": {
                                k: max(0, int(c.get(k, 0))) for k in POINTS
                            },
                            "contribution_records": records if isinstance(records, list) else []
                        })

                return result

        except (json.JSONDecodeError, TypeError, ValueError):
            st.error(f"Could not read {source.name}; check its JSON format.")

    return sample_participants()

def save_participants():
    DATA_FILE.write_text(json.dumps(st.session_state.participants, indent=4), encoding="utf-8")


def score_for(c):
    active_points = st.session_state.get(
        "hackathon_config", {}
    ).get("points", POINTS)

    return sum(
        int(active_points.get(k, POINTS[k])) * int(c.get(k, 0))
        for k in POINTS
    )


def build_dataframe(people):
    rows = []
    for person in people:
        c = person["contributions"]
        rows.append({
            "Participant": person["name"],
            "Contributions": sum(int(c.get(k, 0)) for k in POINTS),
            "Features": int(c.get("features", 0)),
            "Bug fixes": int(c.get("bug_fixes", 0)),
            "Documentation": int(c.get("documentation", 0)),
            "Tests": int(c.get("tests", 0)),
            "Score": score_for(c),
        })
    df = pd.DataFrame(rows, columns=[
        "Participant", "Contributions", "Features", "Bug fixes",
        "Documentation", "Tests", "Score"
    ])
    if not df.empty:
        df = df.sort_values(["Score", "Contributions", "Participant"],
                            ascending=[False, False, True]).reset_index(drop=True)
        df.insert(0, "Rank", range(1, len(df) + 1))
    return df


def github_get(path, params=None):
    headers = {
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": "OpenSource-Contribution-HQ",
    }
    response = requests.get(
        f"{GITHUB_API}{path}", headers=headers, params=params, timeout=20
    )
    if response.status_code == 404:
        raise ValueError("Repository not found, or it is private. Check the owner/repository spelling.")
    if response.status_code == 403:
        remaining = response.headers.get("X-RateLimit-Remaining", "0")
        raise ValueError(f"GitHub API rate limit or access restriction (remaining: {remaining}). Try again later.")
    response.raise_for_status()
    return response.json()


def fetch_github_repository(owner, repo):
    repo_info = github_get(f"/repos/{owner}/{repo}")
    contributors = github_get(
        f"/repos/{owner}/{repo}/contributors",
        params={"per_page": 100, "anon": "false"},
    )
    commits = github_get(
        f"/repos/{owner}/{repo}/commits",
        params={"per_page": 100},
    )
    # Fetch the latest 100 pull requests across all states. GitHub returns
    # merged PRs with state="closed" and a non-null merged_at timestamp.
    pull_requests = github_get(
        f"/repos/{owner}/{repo}/pulls",
        params={"state": "all", "sort": "updated", "direction": "desc", "per_page": 100},
    )
    return repo_info, contributors, commits, pull_requests


if "participants" not in st.session_state:
    st.session_state.participants = load_participants()

if "github_result" not in st.session_state:
    st.session_state.github_result = None

if "hackathon_config" not in st.session_state:
    st.session_state.hackathon_config = load_config()

with st.sidebar:
    st.markdown("## ◈ OPEN SOURCE HQ")
    st.caption("CONTRIBUTION INTELLIGENCE")
    st.divider()
    page = st.radio(
        "WORKSPACE",
        ["Overview", "Organizer Dashboard", "Hackathon Configuration", "Leaderboard", "Participants", "Manage contributions", "Contribution History", "GitHub repository", "Scoring guide"],
    )
    st.divider()
    st.markdown("**PROJECT STATUS**")
    st.success("Local demo mode")
    st.caption("Local demo data is saved in participants.json.")
    if st.button("↻ Reload saved data", use_container_width=True):
        st.session_state.participants = load_participants()
        st.rerun()

participants = st.session_state.participants
df = build_dataframe(participants)
total_people = len(participants)
total_contributions = int(df["Contributions"].sum()) if not df.empty else 0
total_points = int(df["Score"].sum()) if not df.empty else 0
leader = df.iloc[0]["Participant"] if not df.empty else "—"

st.markdown("""
<div class="hero">
  <div class="eyebrow">OPEN SOURCE • COMMUNITY • IMPACT</div>
  <h1>Contribution HQ</h1>
  <p>A command centre for tracking contributors, exploring public GitHub repository activity and recognising open-source momentum.</p>
</div>
""", unsafe_allow_html=True)

if page == "Overview":
    config = st.session_state.hackathon_config

    st.title(config["name"])
    st.write(config["description"])

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("Event Status", config["status"])

    with col2:
        st.metric("Start Date", config["start_date"])

    with col3:
        st.metric("End Date", config["end_date"])

    if config.get("organization") or config.get("repository"):
        st.caption(
            f"GitHub Organization: {config['organization'] or 'Not configured'}"
        )
        if config.get("repository"):
            st.caption(f"Repository: {config['repository']}")

    st.divider()

    st.subheader("Workspace overview")
    st.markdown(
        '<div class="section-note">A snapshot of your local demo dataset.</div>',
        unsafe_allow_html=True
    )

    a, b, c, d = st.columns(4)
    a.metric("Contributors", total_people)
    b.metric("Contributions", total_contributions)
    c.metric("Points awarded", f"{total_points:,}")
    d.metric("Current leader", leader)

    st.divider()
    st.subheader("🏆 Leaders podium")

    if df.empty:
        st.info("No participants yet. Add someone from Participants.")
    else:
        cols = st.columns(3)

        for i, col in enumerate(cols):
            if i < min(3, len(df)):
                row = df.iloc[i]

                with col:
                    st.markdown(
                        f'<div class="podium"><div class="medal">{MEDALS[i]}</div>'
                        f'<div class="name">{row["Participant"]}</div>'
                        f'<div class="score">{row["Score"]} pts</div>'
                        f'<div class="small">{row["Contributions"]} recorded contributions</div></div>',
                        unsafe_allow_html=True,
                    )
            else:
                with col:
                    st.markdown(
                        '<div class="podium"><div class="medal">☆</div>'
                        '<div class="name">Open spot</div>'
                        '<div class="small">Keep contributing</div></div>',
                        unsafe_allow_html=True
                    )

    st.divider()

    left, right = st.columns([1.2, 1])

    with left:
        st.subheader("Score leaderboard")

        if not df.empty:
            st.dataframe(
                df[["Rank", "Participant", "Contributions", "Score"]],
                hide_index=True,
                width="stretch"
            )
        else:
            st.info("No leaderboard data yet.")

    with right:
        st.subheader("Contribution mix")

        if total_contributions:
            mix = pd.DataFrame({
                "Category": list(LABELS.values()),
                "Count": [
                    sum(p["contributions"].get(k, 0) for p in participants)
                    for k in POINTS
                ],
            })

            fig = px.pie(
                mix,
                names="Category",
                values="Count",
                hole=.66,
                color_discrete_sequence=[
                    "#67e8c2", "#6ea8fe", "#b69cff", "#ffbd69"
                ]
            )

            fig.update_layout(
                template="plotly_dark",
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                margin=dict(t=10, b=10, l=10, r=10),
                legend_title_text=""
            )

            st.plotly_chart(fig, width="stretch")
        else:
            st.info("Add contributions to see the chart.")
            
elif page == "Organizer Dashboard":
    st.subheader("🎯 Hackathon Organizer Dashboard")
    st.caption("A central overview of participant activity, contribution reviews and hackathon progress.")

    # Contribution statistics
    total_submissions = 0
    approved_count = 0
    pending_count = 0
    rejected_count = 0

    for person in participants:
        for record in person.get("contribution_records", []):
            total_submissions += 1

            status = record.get("status", "Pending")

            if status == "Approved":
                approved_count += 1
            elif status == "Pending":
                pending_count += 1
            elif status == "Rejected":
                rejected_count += 1

    # Main metrics
    st.markdown("### 📊 Hackathon Overview")

    col1, col2, col3, col4 = st.columns(4)

    col1.metric("Participants", total_people)
    col2.metric("Total submissions", total_submissions)
    col3.metric("Approved", approved_count)
    col4.metric("Pending reviews", pending_count)

    st.divider()

    # Points and activity
    st.markdown("### 🏆 Contribution Performance")

    col1, col2 = st.columns(2)

    with col1:
        st.metric("Total leaderboard points", total_points)
        st.metric("Approved contribution units", total_contributions)

    with col2:
        st.metric("Rejected submissions", rejected_count)

        approval_rate = (
            (approved_count / total_submissions) * 100
            if total_submissions else 0
        )

        st.metric("Approval rate", f"{approval_rate:.1f}%")

    st.divider()

    # Top contributors
    st.markdown("### 🥇 Top Contributors")

    if not df.empty:
        top_contributors = df.head(5)

        st.dataframe(
            top_contributors,
            hide_index=True,
            width="stretch"
        )

    st.divider()

    # Review status chart
    st.markdown("### 📈 Submission Review Status")

    status_df = pd.DataFrame({
        "Status": ["Approved", "Pending", "Rejected"],
        "Submissions": [
            approved_count,
            pending_count,
            rejected_count
        ]
    })

    status_chart = px.pie(
        status_df,
        names="Status",
        values="Submissions",
        hole=0.55,
        title="Contribution Approval Distribution",
        color="Status",
        color_discrete_map={
            "Approved": "#67e8c2",
            "Pending": "#f5c46b",
            "Rejected": "#ff6b81"
        }
    )

    status_chart.update_layout(
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)"
    )

    st.plotly_chart(status_chart, width="stretch")

    st.divider()

    # Pending review list
    st.markdown("### ⏳ Awaiting Organizer Review")

    if pending_count:
        for person in participants:
            for record in person.get("contribution_records", []):
                if record.get("status") == "Pending":
                    st.write(
                        f"**{person['name']}** — "
                        f"{LABELS.get(record.get('category'), 'Other')}"
                    )
                    st.caption(record.get("description", "No description"))
    else:
        st.success("All contribution submissions have been reviewed.")
        
elif page == "Hackathon Configuration":
    st.title("⚙️ Hackathon Configuration")
    st.write("Manage your event details, repositories and scoring rules.")

    config = st.session_state.hackathon_config
    points = config.get("points", POINTS)

    with st.form("hackathon_config_form"):

        st.subheader("Event Details")

        event_name = st.text_input(
            "Hackathon Name",
            value=config["name"]
        )

        description = st.text_area(
            "Description",
            value=config["description"]
        )

        col1, col2 = st.columns(2)

        with col1:
            start_date = st.date_input(
                "Start Date",
                value=date.fromisoformat(config["start_date"])
            )

        with col2:
            end_date = st.date_input(
                "End Date",
                value=date.fromisoformat(config["end_date"])
            )

        status = st.selectbox(
            "Event Status",
            ["Upcoming", "Live", "Completed"],
            index=["Upcoming", "Live", "Completed"].index(
                config["status"]
            )
        )

        st.divider()
        st.subheader("GitHub Settings")

        organization = st.text_input(
            "GitHub Organization",
            value=config["organization"]
        )

        repository = st.text_input(
            "GitHub Repository URL",
            value=config["repository"]
        )

        st.divider()
        st.subheader("Contribution Scoring")

        col1, col2 = st.columns(2)

        with col1:
            feature_points = st.number_input(
                "Features",
                min_value=0,
                value=int(points["features"])
            )

            bug_points = st.number_input(
                "Bug Fixes",
                min_value=0,
                value=int(points["bug_fixes"])
            )

        with col2:
            documentation_points = st.number_input(
                "Documentation",
                min_value=0,
                value=int(points["documentation"])
            )

            test_points = st.number_input(
                "Tests",
                min_value=0,
                value=int(points["tests"])
            )

        submitted = st.form_submit_button(
            "Save Hackathon Configuration",
            use_container_width=True
        )

    if submitted:
        if not event_name.strip():
            st.error("Hackathon name cannot be empty.")

        elif end_date < start_date:
            st.error("End date cannot be before start date.")

        else:
            updated_config = {
                "name": event_name.strip(),
                "description": description,
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "repository": repository.strip(),
                "organization": organization.strip(),
                "status": status,
                "points": {
                    "features": feature_points,
                    "bug_fixes": bug_points,
                    "documentation": documentation_points,
                    "tests": test_points
                }
            }

            save_config(updated_config)
            st.session_state.hackathon_config = updated_config

            st.success("Hackathon configuration saved successfully!")
            st.rerun()

elif page == "Leaderboard":
    st.subheader("🏅 Global leaderboard")
    st.markdown('<div class="section-note">Rankings use the transparent demo scoring rules.</div>', unsafe_allow_html=True)
    if df.empty:
        st.info("No participants have been added yet.")
    else:
        query = st.text_input("Search contributors", placeholder="Type a participant name...")
        view = df[df["Participant"].str.contains(query, case=False, na=False)] if query else df
        st.dataframe(view, hide_index=True, width="stretch")
        if not view.empty:
            chart = px.bar(view.sort_values("Score"), x="Score", y="Participant", orientation="h",
                           text="Score", color="Score", color_continuous_scale=["#285b70", "#67e8c2"])
            chart.update_layout(template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)",
                                plot_bgcolor="rgba(0,0,0,0)", coloraxis_showscale=False,
                                xaxis_title="Points", yaxis_title="", margin=dict(t=20, b=20))
            st.plotly_chart(chart, width="stretch")
        st.download_button("⬇ Export leaderboard as CSV",
                           data=df.to_csv(index=False).encode("utf-8"),
                           file_name="opensource_leaderboard.csv", mime="text/csv")

elif page == "Participants":
    st.subheader("👥 Participants")
    with st.expander("＋ Register a participant"):
        with st.form("add_participant", clear_on_submit=True):
            name = st.text_input("Participant name", placeholder="e.g. Priya")
            submit = st.form_submit_button("Add participant", type="primary")
            if submit:
                name = name.strip()
                if not name:
                    st.error("Please enter a name.")
                elif any(p["name"].casefold() == name.casefold() for p in participants):
                    st.warning("That participant is already registered.")
                else:
                    participants.append({"name": name, "contributions": {k: 0 for k in POINTS}})
                    save_participants()
                    st.success(f"{name} registered.")
                    st.rerun()
    if participants:
        cols = st.columns(3)
        for i, person in enumerate(participants):
            with cols[i % 3]:
                st.markdown(f"### {person['name']}")
                st.metric("Total score", score_for(person["contributions"]))
                st.caption(f"{sum(person['contributions'].values())} recorded contributions")
    else:
        st.info("No participants registered yet.")

elif page == "Manage contributions":
    st.subheader("＋ Submit a contribution")
    st.caption("Participants submit their work for organizer review. Only approved contributions affect the leaderboard.")

    if not participants:
        st.info("Register a participant first.")
    else:
        with st.form("submit_contribution", clear_on_submit=True):
            selected = st.selectbox(
                "Participant",
                [p["name"] for p in participants]
            )

            category = st.selectbox(
                "Contribution category",
                list(POINTS),
                format_func=lambda k: LABELS[k]
            )

            description = st.text_area(
                "Describe your contribution",
                placeholder="Explain what you implemented, fixed, documented, or tested..."
            )

            contribution_url = st.text_input(
                "GitHub PR / Commit URL",
                placeholder="https://github.com/owner/repository/pull/123"
            )

            submit = st.form_submit_button(
                "Submit for approval",
                type="primary"
            )

            if submit:
                if not description.strip():
                    st.error("Please describe your contribution.")
                elif not contribution_url.strip().startswith("https://github.com/"):
                    st.error("Please provide a valid GitHub URL.")
                else:
                    person = next(
                        p for p in participants if p["name"] == selected
                    )

                    person.setdefault("contribution_records", [])

                    person["contribution_records"].append({
                        "id": str(uuid.uuid4()),
                        "category": category,
                        "description": description.strip(),
                        "url": contribution_url.strip(),
                        "status": "Pending"
                    })

                    save_participants()
                    st.success("Contribution submitted for organizer approval!")
                    st.rerun()

    st.divider()

    st.subheader("📋 Contribution review")

    pending_records = []

    for person in participants:
        person.setdefault("contribution_records", [])

        for record in person["contribution_records"]:
            if record.get("status") == "Pending":
                pending_records.append((person, record))

    if not pending_records:
        st.info("No pending contributions to review.")
    else:
        st.metric("Pending submissions", len(pending_records))

        for person, record in pending_records:
            with st.container(border=True):
                st.markdown(f"**{person['name']}**")
                st.write(f"Category: {LABELS.get(record['category'], record['category'])}")
                st.write(record["description"])
                st.link_button("View GitHub contribution", record["url"])

                col1, col2 = st.columns(2)

                with col1:
                    if st.button(
                        "✅ Approve",
                        key=f"approve_{record['id']}",
                        type="primary"
                    ):
                        category = record["category"]

                        if category in POINTS:
                            person["contributions"][category] = (
                                int(person["contributions"].get(category, 0)) + 1
                            )
                            record["status"] = "Approved"
                            save_participants()
                            st.success("Contribution approved and leaderboard updated!")
                            st.rerun()

                with col2:
                    if st.button(
                        "❌ Reject",
                        key=f"reject_{record['id']}"
                    ):
                        record["status"] = "Rejected"
                        save_participants()
                        st.warning("Contribution rejected.")
                        st.rerun()

    st.divider()

    st.subheader("Scoring values")

    cols = st.columns(4)

    for col, (key, value) in zip(cols, POINTS.items()):
        col.metric(LABELS[key], f"{value} pts")
        
elif page == "Contribution History":
    st.subheader("📜 Contribution History")
    st.caption("Track every submitted contribution and its review status.")

    history_records = []

    for person in participants:
        for record in person.get("contribution_records", []):
            history_records.append({
                "Participant": person["name"],
                "Category": LABELS.get(
                    record.get("category"),
                    record.get("category", "Unknown")
                ),
                "Description": record.get("description", ""),
                "Status": record.get("status", "Pending"),
                "GitHub URL": record.get("url", ""),
                "Submission ID": record.get("id", "")
            })

    if not history_records:
        st.info("No contributions have been submitted yet.")
    else:
        history_df = pd.DataFrame(history_records)

        total = len(history_df)
        approved = (history_df["Status"] == "Approved").sum()
        pending = (history_df["Status"] == "Pending").sum()
        rejected = (history_df["Status"] == "Rejected").sum()

        col1, col2, col3, col4 = st.columns(4)

        col1.metric("Total submissions", total)
        col2.metric("Approved", int(approved))
        col3.metric("Pending", int(pending))
        col4.metric("Rejected", int(rejected))

        st.divider()

        selected_status = st.selectbox(
            "Filter by status",
            ["All", "Pending", "Approved", "Rejected"]
        )

        filtered_df = history_df.copy()

        if selected_status != "All":
            filtered_df = filtered_df[
                filtered_df["Status"] == selected_status
            ]

        st.dataframe(
            filtered_df.drop(columns=["Submission ID"]),
            hide_index=True,
            width="stretch",
            column_config={
                "GitHub URL": st.column_config.LinkColumn("GitHub Contribution")
            }
        )

        st.download_button(
            "⬇ Export contribution history",
            data=filtered_df.to_csv(index=False).encode("utf-8"),
            file_name="contribution_history.csv",
            mime="text/csv"
        )
        
elif page == "GitHub repository":
    st.subheader("🐙 Public GitHub repository explorer")
    st.markdown(
        "Enter a public repository as `owner/repository`. This page fetches repository details, "
        "GitHub's contributor statistics and up to the latest 100 commits using the public GitHub REST API."
    )
    st.info("No GitHub token is required for public repositories. Unauthenticated API requests are rate-limited. Private repositories are not supported in this version.")
    with st.form("github_lookup"):
        repo_input = st.text_input("Repository", placeholder="e.g. streamlit/streamlit")
        fetch = st.form_submit_button("Fetch GitHub activity", type="primary")
    if fetch:
        cleaned = repo_input.strip().strip("/")
        match = re.fullmatch(r"([A-Za-z0-9_.-]+)/([A-Za-z0-9_.-]+)", cleaned)
        if not match:
            st.error("Enter a repository in owner/repository format.")
        else:
            owner, repo = match.groups()
            with st.spinner(f"Fetching public activity for {owner}/{repo}..."):
                try:
                    info, contributors, commits, pull_requests = fetch_github_repository(owner, repo)
                    st.session_state.github_result = {
                        "info": info, "contributors": contributors, "commits": commits,
                        "pull_requests": pull_requests,
                        "full_name": f"{owner}/{repo}",
                    }
                except requests.Timeout:
                    st.error("GitHub did not respond in time. Please try again.")
                except requests.RequestException as exc:
                    st.error(f"GitHub API request failed: {exc}")
                except ValueError as exc:
                    st.error(str(exc))
    result = st.session_state.github_result
    if result:
        info = result["info"]
        contributors = result["contributors"]
        commits = result["commits"]
        pull_requests = result.get("pull_requests", [])
        st.divider()
        st.markdown(f"### [{info.get('full_name', result['full_name'])}]({info.get('html_url', '#')})")
        st.write(info.get("description") or "No repository description provided.")
        x1, x2, x3, x4 = st.columns(4)
        x1.metric("⭐ Stars", f"{info.get('stargazers_count', 0):,}")
        x2.metric("🍴 Forks", f"{info.get('forks_count', 0):,}")
        x3.metric("🐛 Open issues", f"{info.get('open_issues_count', 0):,}")
        x4.metric("Recent commits fetched", len(commits))
        st.caption(f"Default branch: {info.get('default_branch', 'unknown')} • Public repository • Data returned by GitHub API")
        st.divider()
        st.subheader("🔀 Pull request intelligence")
        st.caption("Latest 100 pull requests returned by GitHub, across open and closed states. A closed PR is counted as merged only when GitHub supplies a merged timestamp.")
        pr_rows = []
        for pr in pull_requests:
            merged = bool(pr.get("merged_at"))
            state = "Merged" if merged else pr.get("state", "unknown").title()
            user = pr.get("user") or {}
            pr_rows.append({
                "PR": f"#{pr.get('number', '')}",
                "Author": user.get("login", "Unknown"),
                "Title": pr.get("title", ""),
                "Status": state,
                "Created (UTC)": pr.get("created_at", ""),
                "Merged (UTC)": pr.get("merged_at") or "—",
                "Commits": pr.get("commits", 0),
                "Files changed": pr.get("changed_files", 0),
                "Additions": pr.get("additions", 0),
                "Deletions": pr.get("deletions", 0),
                "URL": pr.get("html_url", ""),
            })
        merged_count = sum(1 for row in pr_rows if row["Status"] == "Merged")
        open_count = sum(1 for row in pr_rows if row["Status"] == "Open")
        closed_count = sum(1 for row in pr_rows if row["Status"] == "Closed")
        p1, p2, p3, p4 = st.columns(4)
        p1.metric("PRs fetched", len(pr_rows))
        p2.metric("Merged", merged_count)
        p3.metric("Open", open_count)
        p4.metric("Closed without merge", closed_count)
        if pr_rows:
            pr_df = pd.DataFrame(pr_rows)
            status_filter = st.multiselect(
                "Filter pull requests by status",
                options=["Merged", "Open", "Closed"],
                default=["Merged", "Open", "Closed"],
            )
            filtered_prs = pr_df[pr_df["Status"].isin(status_filter)]
            st.dataframe(
                filtered_prs, hide_index=True, width="stretch",
                column_config={"URL": st.column_config.LinkColumn("Pull request")},
            )
            st.download_button(
                "⬇ Export pull request data as CSV",
                data=pr_df.to_csv(index=False).encode("utf-8"),
                file_name="github_pull_requests.csv", mime="text/csv",
            )
            st.markdown("**Pull requests by author**")
            author_summary = (pr_df.groupby("Author", as_index=False)
                             .agg(PRs=("PR", "count"), Merged=("Status", lambda s: int((s == "Merged").sum())),
                                  Commits=("Commits", "sum"), Files_changed=("Files changed", "sum"))
                             .sort_values(["Merged", "PRs"], ascending=False))
            st.dataframe(author_summary, hide_index=True, width="stretch")
        else:
            st.info("No pull requests were returned for this repository.")
        st.warning("PR counts, changed files and line totals describe activity, not contribution quality. Do not award hackathon points automatically from these numbers. Review relevance, correctness, duplication and usefulness before approving points.")
        st.divider()
        st.subheader("🏆 Top contributors")

        if contributors:
            contributor_rows = [{
                "GitHub user": c.get("login") or "Unknown",
                "Contributions (GitHub count)": c.get("contributions", 0),
                "Profile": c.get("html_url", ""),
            } for c in contributors]

            contributor_df = pd.DataFrame(contributor_rows).sort_values(
                "Contributions (GitHub count)", ascending=False
            )

            st.dataframe(
                contributor_df,
                hide_index=True,
                width="stretch",
                column_config={
                    "Profile": st.column_config.LinkColumn("GitHub Profile")
                }
            )

            chart_data = contributor_df.head(15).sort_values(
                "Contributions (GitHub count)", ascending=True
            )

            chart_height = max(280, len(chart_data) * 65)

            chart = px.bar(
                chart_data,
                x="Contributions (GitHub count)",
                y="GitHub user",
                orientation="h",
                text="Contributions (GitHub count)",
                color_discrete_sequence=["#4F9DFF"],
                hover_data=["GitHub user", "Contributions (GitHub count)"],
                title="Contribution Activity"
            )

            chart.update_traces(
                textposition="outside",
                marker_line_width=0,
                width=0.45
            )

            chart.update_layout(
                template="plotly_dark",
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                height=chart_height,
                showlegend=False,
                margin=dict(l=20, r=60, t=65, b=35),
                xaxis=dict(
                    title="Total Contributions",
                    showgrid=True,
                    gridcolor="rgba(255,255,255,0.08)",
                    range=[
                        0,
                        max(1, chart_data["Contributions (GitHub count)"].max()) * 1.25
                    ]
                ),
                yaxis=dict(
                    title="",
                    showgrid=False
                )
            )

            st.plotly_chart(chart, width="stretch")
        else:
            st.info("No contributor information available.")

        st.divider()

        # Latest GitHub commits
        st.subheader("📝 Latest commits fetched")

        commit_rows = []

        for item in commits:
            commit = item.get("commit", {})
            author = commit.get("author") or {}

            commit_rows.append({
                "SHA": item.get("sha", "")[:7],
                "Author": (item.get("author") or {}).get("login")
                    or author.get("name", "Unknown"),
                "Date (UTC)": author.get("date", ""),
                "Message": (commit.get("message", "").splitlines() or [""])[0],
                "Commit URL": item.get("html_url", ""),
            })

        if commit_rows:
            commit_df = pd.DataFrame(commit_rows)

            st.dataframe(
                commit_df,
                hide_index=True,
                width="stretch",
                column_config={
                    "Commit URL": st.column_config.LinkColumn("View Commit")
                }
            )

            st.download_button(
                "⬇ Download Commit History",
                data=commit_df.to_csv(index=False).encode("utf-8"),
                file_name="github_commits.csv",
                mime="text/csv",
                key="github_commit_history_download_v2"
            )
        else:
            st.info("No recent commits found for this repository.")

        st.caption(
            "Commit history is retrieved directly from the public GitHub API."
        )