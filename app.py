import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
import streamlit.components.v1 as components

# -----------------------------------------------------------------------------
# 1. PAGE CONFIGURATION & TERMINAL CSS THEME
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="NFL Edge Finder Terminal",
    page_icon="🏈",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
<style>
/* Master-Detail Terminal Cards */
.terminal-card {
    background-color: #12161F;
    border: 1px solid #262D3D;
    border-left: 4px solid #4A90E2;
    border-radius: 8px;
    padding: 16px;
    margin-bottom: 12px;
    color: #E2E8F0;
}
.terminal-card-elite {
    background-color: #0F1E19;
    border: 1px solid #1E4635;
    border-left: 4px solid #00FF87;
    border-radius: 8px;
    padding: 16px;
    margin-bottom: 12px;
    color: #E2E8F0;
}
.terminal-card-vuln {
    background-color: #211316;
    border: 1px solid #4A2026;
    border-left: 4px solid #DC143C;
    border-radius: 8px;
    padding: 16px;
    margin-bottom: 12px;
    color: #E2E8F0;
}

/* Refined Unit Ranking Badges */
.badge-elite {
    background-color: rgba(0, 255, 135, 0.14);
    color: #00FF87;
    border: 1px solid #00FF87;
    padding: 2px 8px;
    border-radius: 4px;
    font-size: 0.78rem;
    font-weight: 700;
    font-family: monospace;
    display: inline-block;
    margin: 2px 3px;
}
.badge-mid {
    background-color: rgba(148, 163, 184, 0.12);
    color: #94A3B8;
    border: 1px solid #475569;
    padding: 2px 8px;
    border-radius: 4px;
    font-size: 0.78rem;
    font-weight: 600;
    font-family: monospace;
    display: inline-block;
    margin: 2px 3px;
}
.badge-bad {
    background-color: rgba(220, 20, 60, 0.18);
    color: #FF4D6D;
    border: 1px solid #DC143C;
    padding: 2px 8px;
    border-radius: 4px;
    font-size: 0.78rem;
    font-weight: 700;
    font-family: monospace;
    display: inline-block;
    margin: 2px 3px;
}

/* Supplemental Status & Context Badges */
.badge-amber {
    background-color: rgba(255, 176, 32, 0.15);
    color: #FFB020;
    border: 1px solid #FFB020;
    padding: 2px 8px;
    border-radius: 4px;
    font-size: 0.78rem;
    font-weight: 700;
    font-family: monospace;
    display: inline-block;
    margin: 2px 3px;
}
.badge-sage {
    background-color: rgba(110, 168, 150, 0.15);
    color: #7FD1B9;
    border: 1px solid #7FD1B9;
    padding: 2px 8px;
    border-radius: 4px;
    font-size: 0.78rem;
    font-weight: 600;
    font-family: monospace;
    display: inline-block;
    margin: 2px 3px;
}
.metric-subtext {
    font-size: 0.82rem;
    color: #94A3B8;
    font-family: monospace;
}
.brief-bullet {
    font-size: 0.95rem;
    line-height: 1.65;
    margin-bottom: 10px;
    color: #F1F5F9;
}
</style>
""",
    unsafe_allow_html=True,
)


def render_html(html_str: str) -> None:
    """
    Safely renders custom HTML blocks in Streamlit by stripping leading line whitespace
    so Markdown's 4-space code-block parser never leaks raw <span> or <div> tags.
    """
    cleaned = "\n".join(line.lstrip() for line in html_str.strip().splitlines())
    st.markdown(cleaned, unsafe_allow_html=True)


def render_rank_badge(rank: int, prefix: str = "") -> str:
    """
    Renders standardized unit ranking tags:
    - Top 5 (1-5): ⚡ ELITE [#X]
    - Bottom 10 (23-32): 🚨 BAD [#X]
    - Middle Tier (6-22): 📊 MID [#X]
    """
    lbl = f"{prefix} " if prefix else ""
    if rank <= 5:
        return f'<span class="badge-elite">{lbl}⚡ ELITE [#{rank}]</span>'
    if rank >= 23:
        return f'<span class="badge-bad">{lbl}🚨 BAD [#{rank}]</span>'
    return f'<span class="badge-mid">{lbl}📊 MID [#{rank}]</span>'


def render_injury_badge(status: str) -> str:
    """Renders an HTML badge for official NFL injury report designations."""
    status_clean = str(status).strip().upper()
    if status_clean in ["OUT", "IR", "PUP", "SUSPENDED"]:
        return f'<span class="badge-bad">🚨 {status_clean}</span>'
    if status_clean == "DOUBTFUL":
        return f'<span class="badge-bad">⚠️ {status_clean}</span>'
    if status_clean == "QUESTIONABLE":
        return f'<span class="badge-amber">❓ {status_clean}</span>'
    return f'<span class="badge-mid">{status_clean}</span>'


# -----------------------------------------------------------------------------
# 2. DATA INGESTION (PURE PANDAS READ_CSV + @ST.CACHE_DATA)
# -----------------------------------------------------------------------------
@st.cache_data(ttl=3600)
def load_master_games_csv() -> pd.DataFrame:
    """
    Loads the complete nflverse historical games.csv master file for multi-year
    backtesting and head-to-head matchup history lookups.
    """
    master_url = "https://github.com/nflverse/nflverse-data/releases/download/schedules/games.csv"
    try:
        df = pd.read_csv(master_url, low_memory=False)
    except Exception:
        return pd.DataFrame()

    if {"home_rest", "away_rest"}.issubset(df.columns):
        df["rest_edge_home"] = df["home_rest"] - df["away_rest"]
    if "spread_line" in df.columns:
        df["home_spread"] = df["spread_line"] * -1

    return df


@st.cache_data(ttl=3600)
def load_season_schedule(season: int) -> pd.DataFrame:
    """Fetches a specific season schedule with fallback to the master games dataset."""
    master_df = load_master_games_csv()
    season_url = f"https://github.com/nflverse/nflverse-data/releases/download/schedules/schedule_{season}.csv"

    df = pd.DataFrame()
    try:
        df = pd.read_csv(season_url, low_memory=False)
        if {"home_rest", "away_rest"}.issubset(df.columns):
            df["rest_edge_home"] = df["home_rest"] - df["away_rest"]
        if "spread_line" in df.columns:
            df["home_spread"] = df["spread_line"] * -1
    except Exception:
        pass

    if df.empty and not master_df.empty and "season" in master_df.columns:
        df = master_df[master_df["season"] == season].copy()
    elif not df.empty and not master_df.empty and "game_id" in df.columns and "game_id" in master_df.columns:
        score_cols = ["game_id", "home_score", "away_score", "spread_line", "total_line"]
        avail_sc = [c for c in score_cols if c in master_df.columns]
        m_sub = master_df[master_df["season"] == season][avail_sc].drop_duplicates(subset=["game_id"])
        if not m_sub.empty:
            df = df.merge(m_sub, on="game_id", how="left", suffixes=("", "_master"))
            for col in ["home_score", "away_score", "spread_line", "total_line"]:
                if f"{col}_master" in df.columns:
                    df[col] = df[col].fillna(df[f"{col}_master"])
            if "spread_line" in df.columns:
                df["home_spread"] = df["spread_line"] * -1

    return df


@st.cache_data(ttl=3600)
def load_team_efficiency_csv(season: int) -> tuple[pd.DataFrame, int]:
    """
    Fetches play-by-play CSV (.csv.gz) via pd.read_csv for the requested season
    to compute team offensive and defensive Pass EPA, Rush EPA, Success Rate, and Ranks.
    """
    use_cols = ["posteam", "defteam", "epa", "success", "play_type", "pass", "rush"]

    for yr in [season, season - 1, 2024]:
        pbp_url = f"https://github.com/nflverse/nflverse-data/releases/download/pbp/play_by_play_{yr}.csv.gz"
        try:
            pbp = pd.read_csv(
                pbp_url,
                compression="gzip",
                usecols=lambda c: c in use_cols,
                low_memory=False,
            )
            loaded_yr = yr
            break
        except Exception:
            continue
    else:
        return pd.DataFrame(), season

    valid = pbp[
        pbp["play_type"].isin(["pass", "run"])
        & pbp["epa"].notna()
        & pbp["posteam"].notna()
        & pbp["defteam"].notna()
    ].copy()

    off_all = (
        valid.groupby("posteam")
        .agg(off_epa=("epa", "mean"), off_sr=("success", "mean"))
        .reset_index()
        .rename(columns={"posteam": "team"})
    )
    off_pass = (
        valid[valid["pass"] == 1]
        .groupby("posteam")
        .agg(off_pass_epa=("epa", "mean"), off_pass_sr=("success", "mean"))
        .reset_index()
        .rename(columns={"posteam": "team"})
    )
    off_rush = (
        valid[valid["rush"] == 1]
        .groupby("posteam")
        .agg(off_rush_epa=("epa", "mean"), off_rush_sr=("success", "mean"))
        .reset_index()
        .rename(columns={"posteam": "team"})
    )

    def_all = (
        valid.groupby("defteam")
        .agg(def_epa=("epa", "mean"), def_sr=("success", "mean"))
        .reset_index()
        .rename(columns={"defteam": "team"})
    )
    def_pass = (
        valid[valid["pass"] == 1]
        .groupby("defteam")
        .agg(def_pass_epa=("epa", "mean"), def_pass_sr=("success", "mean"))
        .reset_index()
        .rename(columns={"defteam": "team"})
    )
    def_rush = (
        valid[valid["rush"] == 1]
        .groupby("defteam")
        .agg(def_rush_epa=("epa", "mean"), def_rush_sr=("success", "mean"))
        .reset_index()
        .rename(columns={"defteam": "team"})
    )

    eff = (
        off_all.merge(off_pass, on="team")
        .merge(off_rush, on="team")
        .merge(def_all, on="team")
        .merge(def_pass, on="team")
        .merge(def_rush, on="team")
    )

    for col in ["off_epa", "off_sr", "off_pass_epa", "off_pass_sr", "off_rush_epa", "off_rush_sr"]:
        eff[f"{col}_rank"] = eff[col].rank(ascending=False, method="min").astype(int)

    for col in ["def_epa", "def_sr", "def_pass_epa", "def_pass_sr", "def_rush_epa", "def_rush_sr"]:
        eff[f"{col}_rank"] = eff[col].rank(ascending=True, method="min").astype(int)

    return eff.set_index("team"), loaded_yr


@st.cache_data(ttl=3600)
def load_player_stats_csv(season: int) -> tuple[pd.DataFrame, int]:
    """Fetches weekly player offensive/receiving/rushing stats via pd.read_csv."""
    for yr in [season, season - 1, 2024]:
        urls = [
            f"https://github.com/nflverse/nflverse-data/releases/download/stats_player/stats_player_week_{yr}.csv.gz",
            f"https://github.com/nflverse/nflverse-data/releases/download/player_stats/player_stats_{yr}.csv.gz",
            f"https://github.com/nflverse/nflverse-data/releases/download/player_stats/player_stats_{yr}.csv",
        ]
        for url in urls:
            try:
                df = pd.read_csv(url, low_memory=False)
                if "recent_team" in df.columns and "team" not in df.columns:
                    df["team"] = df["recent_team"]
                return df, yr
            except Exception:
                continue
    return pd.DataFrame(), season


@st.cache_data(ttl=3600)
def load_snap_counts_csv(season: int) -> tuple[pd.DataFrame, int]:
    """Fetches player snap percentages via pd.read_csv to identify starting anchors."""
    for yr in [season, season - 1, 2024]:
        url = f"https://github.com/nflverse/nflverse-data/releases/download/snap_counts/snap_counts_{yr}.csv"
        try:
            df = pd.read_csv(url, low_memory=False)
            return df, yr
        except Exception:
            continue
    return pd.DataFrame(), season


@st.cache_data(ttl=3600)
def load_injuries_csv(season: int) -> tuple[pd.DataFrame, int]:
    """Fetches official weekly NFL injury reports via pd.read_csv."""
    for yr in [season, season - 1, 2024]:
        urls = [
            f"https://github.com/nflverse/nflverse-data/releases/download/injuries/injuries_{yr}.csv",
            f"https://github.com/nflverse/nflverse-data/releases/download/injuries/injuries_{yr}.csv.gz",
        ]
        for url in urls:
            try:
                df = pd.read_csv(url, low_memory=False)
                return df, yr
            except Exception:
                continue
    return pd.DataFrame(), season


# -----------------------------------------------------------------------------
# 3. ANALYTICS, HEAD-TO-HEAD HISTORY, PROP LOGS & BACKTEST ENGINES
# -----------------------------------------------------------------------------
def get_head_to_head_history(
    master_df: pd.DataFrame, away_tm: str, home_tm: str, limit: int = 8
) -> pd.DataFrame:
    """
    Looks up past completed matchups between away_tm and home_tm across historical
    nflverse schedule data and computes winners, margins, and ATS cover results.
    """
    if master_df.empty:
        return pd.DataFrame()

    h2h = master_df[
        (
            ((master_df["home_team"] == home_tm) & (master_df["away_team"] == away_tm))
            | ((master_df["home_team"] == away_tm) & (master_df["away_team"] == home_tm))
        )
        & master_df["home_score"].notna()
        & master_df["away_score"].notna()
    ].copy()

    if h2h.empty:
        return pd.DataFrame()

    h2h = h2h.sort_values(by=["season", "week"], ascending=[False, False]).head(limit)

    winners, scores, ats_results = [], [], []
    for _, r in h2h.iterrows():
        hs, as_ = int(r["home_score"]), int(r["away_score"])
        ht, at = r["home_team"], r["away_team"]
        margin = hs - as_

        if margin > 0:
            winners.append(ht)
        elif margin < 0:
            winners.append(at)
        else:
            winners.append("TIE")

        scores.append(f"{at} {as_} @ {ht} {hs}")

        sp = r.get("spread_line", np.nan)
        if pd.notna(sp):
            if margin > sp:
                ats_results.append(f"{ht} Covered ({-sp:+.1f})")
            elif margin < sp:
                ats_results.append(f"{at} Covered ({sp:+.1f})")
            else:
                ats_results.append("Push")
        else:
            ats_results.append("N/A")

    h2h["Matchup & Final"] = scores
    h2h["SU Winner"] = winners
    h2h["ATS Result"] = ats_results
    h2h["Total Pts"] = h2h["home_score"].astype(int) + h2h["away_score"].astype(int)

    return h2h


def prepare_matchup_player_prop_logs(player_df: pd.DataFrame, teams: list[str]) -> pd.DataFrame:
    """
    Prepares week-by-week player game logs for the selected matchup teams,
    standardizing prop columns (Passing, Rushing, Receiving, Scrimmage) for the Prop Explorer.
    """
    if player_df.empty or "team" not in player_df.columns:
        return pd.DataFrame()

    sub = player_df[player_df["team"].isin(teams)].copy()
    if sub.empty:
        return pd.DataFrame()

    name_col = "player_display_name" if "player_display_name" in sub.columns else "player_name"
    pos_col = "position" if "position" in sub.columns else "position_group"
    opp_col = "opponent_team" if "opponent_team" in sub.columns else None

    sub["player_label"] = sub[name_col].astype(str).str.strip()
    sub["pos_clean"] = sub[pos_col].fillna("UNK").astype(str).str.upper().str.strip()
    sub["opp_label"] = sub[opp_col].fillna("OPP").astype(str) if opp_col else "OPP"

    stat_cols = [
        "passing_yards",
        "passing_tds",
        "completions",
        "attempts",
        "rushing_yards",
        "rushing_tds",
        "carries",
        "receiving_yards",
        "receiving_tds",
        "receptions",
        "targets",
    ]
    for c in stat_cols:
        if c not in sub.columns:
            sub[c] = 0.0
        sub[c] = pd.to_numeric(sub[c], errors="coerce").fillna(0.0)

    sub["scrimmage_yards"] = sub["rushing_yards"] + sub["receiving_yards"]
    sub["total_tds"] = sub["rushing_tds"] + sub["receiving_tds"]
    sub["week"] = pd.to_numeric(sub.get("week", 1), errors="coerce").fillna(1).astype(int)
    sub["game_tag"] = "Wk " + sub["week"].astype(str) + " vs " + sub["opp_label"]

    return sub.sort_values(by=["week"])


def run_season_backtest(
    schedule_df: pd.DataFrame, eff_df: pd.DataFrame
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Grades all completed games in the selected season where extreme unit mismatches
    (⚡ ELITE vs 🚨 BAD) or rest edges occurred, returning a summary by category
    and a game-by-game graded log.
    """
    if schedule_df.empty or eff_df.empty:
        return pd.DataFrame(), pd.DataFrame()

    completed = schedule_df[
        schedule_df["home_score"].notna()
        & schedule_df["away_score"].notna()
        & schedule_df["spread_line"].notna()
    ].copy()

    if completed.empty:
        return pd.DataFrame(), pd.DataFrame()

    records = []

    for _, row in completed.iterrows():
        ht, at = row["home_team"], row["away_team"]
        if ht not in eff_df.index or at not in eff_df.index:
            continue

        h_eff = eff_df.loc[ht]
        a_eff = eff_df.loc[at]

        hs, as_ = float(row["home_score"]), float(row["away_score"])
        sp = float(row["spread_line"])
        home_margin = hs - as_

        def grade_side(backed_team: str) -> tuple[bool, bool, bool]:
            is_home = backed_team == ht
            su_win = (home_margin > 0) if is_home else (home_margin < 0)
            is_push = home_margin == sp
            ats_win = (home_margin > sp) if is_home else (home_margin < sp)
            return su_win, ats_win, is_push

        # 1. ⚡ ELITE (<=5) vs 🚨 BAD (>=23) Pass Mismatch
        h_pass_elite_mm = (h_eff["off_pass_epa_rank"] <= 5) and (a_eff["def_pass_epa_rank"] >= 23)
        a_pass_elite_mm = (a_eff["off_pass_epa_rank"] <= 5) and (h_eff["def_pass_epa_rank"] >= 23)
        if h_pass_elite_mm != a_pass_elite_mm:
            backed = ht if h_pass_elite_mm else at
            su, ats, push = grade_side(backed)
            records.append(
                {
                    "Week": int(row["week"]),
                    "Matchup": f"{at} @ {ht}",
                    "Category": "⚡ ELITE vs 🚨 BAD Pass Unit",
                    "Backed Team": backed,
                    "Final Score": f"{at} {int(as_)} - {ht} {int(hs)}",
                    "Closing Spread": f"{ht} {-sp:+.1f}",
                    "SU Win": su,
                    "ATS Cover": ats,
                    "Push": push,
                }
            )

        # 2. ⚡ ELITE (<=5) vs 🚨 BAD (>=23) Rush Mismatch
        h_rush_elite_mm = (h_eff["off_rush_epa_rank"] <= 5) and (a_eff["def_rush_epa_rank"] >= 23)
        a_rush_elite_mm = (a_eff["off_rush_epa_rank"] <= 5) and (h_eff["def_rush_epa_rank"] >= 23)
        if h_rush_elite_mm != a_rush_elite_mm:
            backed = ht if h_rush_elite_mm else at
            su, ats, push = grade_side(backed)
            records.append(
                {
                    "Week": int(row["week"]),
                    "Matchup": f"{at} @ {ht}",
                    "Category": "⚡ ELITE vs 🚨 BAD Rush Unit",
                    "Backed Team": backed,
                    "Final Score": f"{at} {int(as_)} - {ht} {int(hs)}",
                    "Closing Spread": f"{ht} {-sp:+.1f}",
                    "SU Win": su,
                    "ATS Cover": ats,
                    "Push": push,
                }
            )

        # 3. Top-10 Offense vs Bottom-10 Defense (Any Phase)
        h_top10_mm = ((h_eff["off_pass_epa_rank"] <= 10) and (a_eff["def_pass_epa_rank"] >= 23)) or (
            (h_eff["off_rush_epa_rank"] <= 10) and (a_eff["def_rush_epa_rank"] >= 23)
        )
        a_top10_mm = ((a_eff["off_pass_epa_rank"] <= 10) and (h_eff["def_pass_epa_rank"] >= 23)) or (
            (a_eff["off_rush_epa_rank"] <= 10) and (h_eff["def_rush_epa_rank"] >= 23)
        )
        if h_top10_mm != a_top10_mm:
            backed = ht if h_top10_mm else at
            su, ats, push = grade_side(backed)
            records.append(
                {
                    "Week": int(row["week"]),
                    "Matchup": f"{at} @ {ht}",
                    "Category": "🔥 Top-10 Off vs 🚨 Bottom-10 Def",
                    "Backed Team": backed,
                    "Final Score": f"{at} {int(as_)} - {ht} {int(hs)}",
                    "Closing Spread": f"{ht} {-sp:+.1f}",
                    "SU Win": su,
                    "ATS Cover": ats,
                    "Push": push,
                }
            )

        # 4. Situational Rest Edge (3+ Days)
        rest_diff = row.get("rest_edge_home", 0)
        if pd.notna(rest_diff) and abs(rest_diff) >= 3:
            backed = ht if rest_diff > 0 else at
            su, ats, push = grade_side(backed)
            records.append(
                {
                    "Week": int(row["week"]),
                    "Matchup": f"{at} @ {ht}",
                    "Category": "🔋 Situational Rest Edge (3+ Days)",
                    "Backed Team": backed,
                    "Final Score": f"{at} {int(as_)} - {ht} {int(hs)}",
                    "Closing Spread": f"{ht} {-sp:+.1f}",
                    "SU Win": su,
                    "ATS Cover": ats,
                    "Push": push,
                }
            )

        # 5. High-Conviction Net EPA Model Edge (>= 0.08 EPA/play differential)
        net_home_epa = (h_eff["off_epa"] - a_eff["def_epa"]) - (a_eff["off_epa"] - h_eff["def_epa"])
        if abs(net_home_epa) >= 0.08:
            backed = ht if net_home_epa > 0 else at
            su, ats, push = grade_side(backed)
            records.append(
                {
                    "Week": int(row["week"]),
                    "Matchup": f"{at} @ {ht}",
                    "Category": "📊 Net EPA Model Edge (>=0.08/play)",
                    "Backed Team": backed,
                    "Final Score": f"{at} {int(as_)} - {ht} {int(hs)}",
                    "Closing Spread": f"{ht} {-sp:+.1f}",
                    "SU Win": su,
                    "ATS Cover": ats,
                    "Push": push,
                }
            )

    log_df = pd.DataFrame(records)
    if log_df.empty:
        return pd.DataFrame(), pd.DataFrame()

    summary_rows = []
    for cat, grp in log_df.groupby("Category", sort=False):
        non_push = grp[~grp["Push"]]
        games_n = len(grp)
        ats_w = int(non_push["ATS Cover"].sum())
        ats_l = int(len(non_push) - ats_w)
        ats_p = int(grp["Push"].sum())
        ats_pct = (ats_w / len(non_push) * 100.0) if len(non_push) > 0 else 0.0

        su_w = int(grp["SU Win"].sum())
        su_pct = (su_w / games_n * 100.0) if games_n > 0 else 0.0

        roi_units = (ats_w * 0.9091) - ats_l
        summary_rows.append(
            {
                "Edge Category": cat,
                "Sample Size": games_n,
                "ATS Record": f"{ats_w}-{ats_l}-{ats_p}",
                "ATS Cover %": round(ats_pct, 1),
                "SU Win %": round(su_pct, 1),
                "Est. Units (-110)": round(roi_units, 2),
            }
        )

    summary_df = pd.DataFrame(summary_rows)
    return summary_df, log_df


def aggregate_team_skill_usage(player_df: pd.DataFrame, teams: list[str]) -> pd.DataFrame:
    """Aggregates seasonal player usage (Target Share, Rush Share, Total EPA) for selected teams."""
    if player_df.empty or "team" not in player_df.columns:
        return pd.DataFrame()

    sub = player_df[player_df["team"].isin(teams)].copy()
    if sub.empty:
        return pd.DataFrame()

    for col in [
        "targets",
        "receptions",
        "receiving_yards",
        "receiving_epa",
        "carries",
        "rushing_yards",
        "rushing_epa",
        "passing_yards",
        "passing_epa",
        "target_share",
    ]:
        if col not in sub.columns:
            sub[col] = 0.0
        sub[col] = pd.to_numeric(sub[col], errors="coerce").fillna(0.0)

    name_col = "player_display_name" if "player_display_name" in sub.columns else "player_name"
    id_col = "player_id" if "player_id" in sub.columns else name_col
    pos_col = "position" if "position" in sub.columns else "position_group"

    grouped = (
        sub.groupby([id_col, name_col, "team", pos_col], as_index=False)
        .agg(
            games=("week", "nunique"),
            targets=("targets", "sum"),
            receptions=("receptions", "sum"),
            rec_yards=("receiving_yards", "sum"),
            rec_epa=("receiving_epa", "sum"),
            carries=("carries", "sum"),
            rush_yards=("rushing_yards", "sum"),
            rush_epa=("rushing_epa", "sum"),
            pass_yards=("passing_yards", "sum"),
            pass_epa=("passing_epa", "sum"),
            avg_target_share=("target_share", "mean"),
        )
        .rename(columns={name_col: "player_name", pos_col: "position", id_col: "player_id"})
    )

    team_totals = grouped.groupby("team")[["targets", "carries"]].transform("sum")
    grouped["calc_target_share"] = np.where(
        team_totals["targets"] > 0,
        grouped["targets"] / team_totals["targets"],
        grouped["avg_target_share"],
    )
    grouped["calc_rush_share"] = np.where(
        team_totals["carries"] > 0,
        grouped["carries"] / team_totals["carries"],
        0.0,
    )
    grouped["total_epa"] = grouped["rec_epa"] + grouped["rush_epa"] + grouped["pass_epa"]
    return grouped


def build_injury_impact_report(
    injuries_df: pd.DataFrame,
    snaps_df: pd.DataFrame,
    usage_df: pd.DataFrame,
    teams: list[str],
    selected_week: int,
) -> pd.DataFrame:
    """
    Cross-references official weekly injury designations (Out, Doubtful, Questionable)
    with snap counts and target shares to flag missing starters and estimate EPA impact.
    """
    if injuries_df.empty or "team" not in injuries_df.columns:
        return pd.DataFrame()

    team_inj = injuries_df[injuries_df["team"].isin(teams)].copy()
    if team_inj.empty:
        return pd.DataFrame()

    if "week" in team_inj.columns:
        if selected_week in team_inj["week"].values:
            team_inj = team_inj[team_inj["week"] == selected_week].copy()
        else:
            latest_wk = team_inj["week"].max()
            team_inj = team_inj[team_inj["week"] == latest_wk].copy()

    status_col = "report_status" if "report_status" in team_inj.columns else "game_status"
    team_inj["report_status"] = (
        team_inj[status_col].fillna("Questionable") if status_col in team_inj.columns else "Questionable"
    )

    valid_statuses = ["OUT", "DOUBTFUL", "QUESTIONABLE", "IR", "PUP"]
    team_inj = team_inj[
        team_inj["report_status"].astype(str).str.upper().str.strip().isin(valid_statuses)
    ].copy()

    if team_inj.empty:
        return pd.DataFrame()

    name_col = "full_name" if "full_name" in team_inj.columns else "player_name"
    team_inj["clean_name"] = team_inj[name_col].astype(str).str.strip().str.lower()

    if not snaps_df.empty and {"player", "team", "offense_pct", "defense_pct"}.issubset(snaps_df.columns):
        snaps_sub = snaps_df[snaps_df["team"].isin(teams)].copy()
        snaps_sub["clean_name"] = snaps_sub["player"].astype(str).str.strip().str.lower()
        snaps_agg = (
            snaps_sub.groupby(["team", "clean_name"], as_index=False)
            .agg(off_snap_pct=("offense_pct", "mean"), def_snap_pct=("defense_pct", "mean"))
        )
        snaps_agg["snap_share"] = snaps_agg[["off_snap_pct", "def_snap_pct"]].max(axis=1)
        team_inj = team_inj.merge(
            snaps_agg[["team", "clean_name", "snap_share"]], on=["team", "clean_name"], how="left"
        )
    else:
        team_inj["snap_share"] = np.nan

    if not usage_df.empty:
        usage_sub = usage_df.copy()
        usage_sub["clean_name"] = usage_sub["player_name"].astype(str).str.strip().str.lower()
        team_inj = team_inj.merge(
            usage_sub[["team", "clean_name", "calc_target_share", "calc_rush_share", "total_epa"]],
            on=["team", "clean_name"],
            how="left",
        )
    else:
        team_inj["calc_target_share"] = 0.0
        team_inj["calc_rush_share"] = 0.0
        team_inj["total_epa"] = 0.0

    team_inj["snap_share"] = team_inj["snap_share"].fillna(0.45)
    team_inj["calc_target_share"] = team_inj["calc_target_share"].fillna(0.0)
    team_inj["calc_rush_share"] = team_inj["calc_rush_share"].fillna(0.0)
    team_inj["total_epa"] = team_inj["total_epa"].fillna(0.0)

    pos_weights = {
        "QB": 0.110,
        "T": 0.038,
        "LT": 0.042,
        "RT": 0.032,
        "G": 0.022,
        "C": 0.025,
        "WR": 0.035,
        "TE": 0.020,
        "RB": 0.018,
        "DE": 0.035,
        "EDGE": 0.038,
        "DT": 0.026,
        "LB": 0.022,
        "CB": 0.034,
        "S": 0.024,
    }
    status_prob_missing = {
        "OUT": 1.0,
        "IR": 1.0,
        "PUP": 1.0,
        "DOUBTFUL": 0.75,
        "QUESTIONABLE": 0.35,
    }

    roles, epa_penalties, impact_units = [], [], []

    for _, row in team_inj.iterrows():
        pos = str(row.get("position", "UNK")).upper().strip()
        snap = float(row["snap_share"])
        tgt = float(row["calc_target_share"])
        status_str = str(row["report_status"]).upper().strip()

        is_anchor = (snap >= 0.65) or (tgt >= 0.18) or (pos == "QB" and snap >= 0.40)
        if is_anchor:
            if pos in ["T", "LT", "RT", "G", "C"]:
                roles.append("🔥 Starting OL Anchor")
            elif pos == "WR" or tgt >= 0.18:
                roles.append("🔥 Primary Target / WR1")
            elif pos in ["DE", "EDGE", "DT"]:
                roles.append("🔥 Primary Pass Rusher / Trench")
            elif pos in ["CB", "S"]:
                roles.append("🔥 Starting Coverage Anchor")
            elif pos == "QB":
                roles.append("🔥 Starting Quarterback")
            else:
                roles.append("🔥 Key Starting Anchor")
        elif snap >= 0.35 or tgt >= 0.10:
            roles.append("⚡ Rotational Contributor")
        else:
            roles.append("Depth / Special Teams")

        base_w = pos_weights.get(pos, 0.015)
        usage_boost = 1.35 if tgt >= 0.20 else (1.15 if snap >= 0.75 else 0.75)
        prob_miss = status_prob_missing.get(status_str, 0.25)
        penalty = round(base_w * snap * usage_boost * prob_miss, 3)
        epa_penalties.append(penalty)

        if pos in ["QB", "WR", "TE", "T", "LT", "RT", "G", "C", "RB"]:
            impact_units.append("Offense")
        else:
            impact_units.append("Defense")

    team_inj["player_display"] = team_inj[name_col]
    team_inj["role_tier"] = roles
    team_inj["est_epa_penalty"] = epa_penalties
    team_inj["unit_side"] = impact_units
    team_inj["primary_injury"] = (
        team_inj["report_primary_injury"].fillna("Undisclosed")
        if "report_primary_injury" in team_inj.columns
        else "Undisclosed"
    )

    return team_inj.sort_values(by=["est_epa_penalty", "snap_share"], ascending=False)


# -----------------------------------------------------------------------------
# 4. SIDEBAR CONTROLS & HISTORICAL BACKTEST MODE
# -----------------------------------------------------------------------------
st.sidebar.markdown("## 🎛️ Terminal Controls")

backtest_mode = st.sidebar.toggle(
    "🕰️ Historical Backtest Mode",
    value=False,
    help="Enable to switch between 2024, 2025, and 2026 seasons and grade historical ATS cover rates.",
)

if backtest_mode:
    selected_season = st.sidebar.selectbox("Select NFL Season", [2025, 2024, 2026], index=0)
else:
    selected_season = st.sidebar.selectbox("Select NFL Season", [2026, 2025, 2024], index=0)

with st.spinner(f"Loading {selected_season} nflverse CSV feeds (Schedules, PBP, Usage, Snaps, Injuries)..."):
    master_games_df = load_master_games_csv()
    schedule_df = load_season_schedule(selected_season)
    eff_df, eff_season = load_team_efficiency_csv(selected_season)
    player_df, player_season = load_player_stats_csv(selected_season)
    snaps_df, snaps_season = load_snap_counts_csv(selected_season)
    injuries_df, inj_season = load_injuries_csv(selected_season)

if schedule_df.empty:
    st.error("Could not load NFL schedule CSV from nflverse. Please verify your internet connection.")
    st.stop()

available_weeks = sorted(schedule_df["week"].dropna().astype(int).unique())
selected_week = st.sidebar.selectbox("Select NFL Week", available_weeks, index=0)

all_teams = sorted(
    pd.concat([schedule_df["home_team"], schedule_df["away_team"]]).dropna().unique()
)
selected_team = st.sidebar.selectbox("Filter by Team (Optional)", ["All Teams"] + all_teams)

st.sidebar.divider()
st.sidebar.markdown("### 🏷️ Unit Badge Legend")
st.sidebar.markdown(
    f"{render_rank_badge(2)} Top 5 NFL Unit<br>"
    f"{render_rank_badge(14)} Ranks 6–22 Unit<br>"
    f"{render_rank_badge(28)} Bottom 10 Unit (23–32)",
    unsafe_allow_html=True,
)

st.sidebar.divider()
st.sidebar.markdown("### 📡 Active nflverse Feeds")
st.sidebar.caption(
    f"- **Active Season:** `{selected_season}`\n"
    f"- **Efficiency PBP:** `{eff_season} CSV.gz`\n"
    f"- **Player Usage:** `{player_season} CSV`\n"
    f"- **Snap Counts:** `{snaps_season} CSV`\n"
    f"- **Injury Report:** `{inj_season} CSV`"
)

week_games = schedule_df[schedule_df["week"] == selected_week].copy()
if selected_team != "All Teams":
    week_games = week_games[
        (week_games["home_team"] == selected_team) | (week_games["away_team"] == selected_team)
    ].copy()
week_games = week_games.reset_index(drop=True)

if "selected_game_idx" not in st.session_state:
    st.session_state.selected_game_idx = 0
if "trigger_scroll" not in st.session_state:
    st.session_state.trigger_scroll = False
if st.session_state.selected_game_idx >= len(week_games):
    st.session_state.selected_game_idx = 0

# -----------------------------------------------------------------------------
# 5. MASTER VIEW: PERMANENT TOP WEEKLY SCHEDULE TABLE
# -----------------------------------------------------------------------------
mode_tag = (
    f'<span class="badge-amber">🕰️ HISTORICAL BACKTEST ACTIVE ({selected_season})</span>'
    if backtest_mode or selected_season < 2026
    else '<span class="badge-elite">⚡ LIVE 2026 SEASON ACTIVE</span>'
)

st.title(f"🏈 {selected_season} NFL Matchup Edge Finder & Prop Terminal")
render_html(
    f"{mode_tag} "
    f"{render_rank_badge(1, 'Top-5')} "
    f"{render_rank_badge(12, 'Ranks 6-22')} "
    f"{render_rank_badge(28, 'Bottom-10')} "
    '<span class="badge-sage">Click any schedule row below to dynamically populate the matchup workspace</span>'
)

st.subheader(f"📅 {selected_season} Week {selected_week} Master Schedule & Rest Slate")
st.caption("👆 **Click any row in the table** to immediately update and scroll to the Matchup Deep-Dive below.")

display_cols = [
    "gameday",
    "gametime",
    "away_team",
    "away_score",
    "home_team",
    "home_score",
    "home_spread",
    "total_line",
    "away_moneyline",
    "home_moneyline",
    "rest_edge_home",
    "roof",
    "stadium",
]
avail_cols = [c for c in display_cols if c in week_games.columns]

selection_event = st.dataframe(
    week_games[avail_cols],
    width="stretch",
    hide_index=True,
    on_select="rerun",
    selection_mode="single-row",
    column_config={
        "gameday": "Date",
        "gametime": "Time (ET)",
        "away_team": "Away",
        "away_score": "Away Pts",
        "home_team": "Home",
        "home_score": "Home Pts",
        "home_spread": st.column_config.NumberColumn("Home Spread", format="%+.1f"),
        "total_line": st.column_config.NumberColumn("Over/Under", format="%.1f"),
        "away_moneyline": "Away ML",
        "home_moneyline": "Home ML",
        "rest_edge_home": st.column_config.NumberColumn(
            "Home Rest Edge",
            format="%+d days",
            help="Home rest days minus Away rest days.",
        ),
        "roof": "Roof",
        "stadium": "Stadium",
    },
)

if selection_event.selection.rows:
    clicked_idx = selection_event.selection.rows[0]
    if clicked_idx != st.session_state.selected_game_idx:
        st.session_state.selected_game_idx = clicked_idx
        st.session_state.trigger_scroll = True
        st.rerun()

# -----------------------------------------------------------------------------
# 6. DETAIL VIEW: SELECTED MATCHUP WORKSPACE & SUB-TABS
# -----------------------------------------------------------------------------
st.divider()
render_html('<div id="matchup-detail-anchor"></div>')

if st.session_state.trigger_scroll:
    components.html(
        """
        <script>
            const anchor = window.parent.document.getElementById('matchup-detail-anchor');
            if (anchor) {
                anchor.scrollIntoView({ behavior: 'smooth', block: 'start' });
            }
        </script>
        """,
        height=0,
    )
    st.session_state.trigger_scroll = False

active_game = week_games.iloc[st.session_state.selected_game_idx] if not week_games.empty else None

if active_game is None or eff_df.empty:
    st.info("Select a valid matchup above to launch the deep-dive analysis.")
    st.stop()

away_tm = active_game["away_team"]
home_tm = active_game["home_team"]
spread_v = active_game.get("home_spread", np.nan)
total_v = active_game.get("total_line", np.nan)
rest_v = active_game.get("rest_edge_home", 0)
roof_str = str(active_game.get("roof", "outdoors")).capitalize()
stadium_str = active_game.get("stadium", "TBD")
away_pts = active_game.get("away_score", np.nan)
home_pts = active_game.get("home_score", np.nan)

spread_str = f"{home_tm} {spread_v:+.1f}" if pd.notna(spread_v) else "Spread TBD"
total_str = f"O/U {total_v:.1f}" if pd.notna(total_v) else "Total TBD"
final_score_badge = (
    f'<span class="badge-amber">🏁 FINAL: {away_tm} {int(away_pts)} - {home_tm} {int(home_pts)}</span>'
    if pd.notna(away_pts) and pd.notna(home_pts)
    else ""
)

if pd.notna(rest_v) and rest_v > 0:
    rest_badge = f'<span class="badge-elite">⚡ REST EDGE: {home_tm} +{int(rest_v)}d</span>'
elif pd.notna(rest_v) and rest_v < 0:
    rest_badge = f'<span class="badge-elite">⚡ REST EDGE: {away_tm} +{int(abs(rest_v))}d</span>'
else:
    rest_badge = '<span class="badge-mid">📊 EVEN REST [0d]</span>'

# Pre-compute shared matchup datasets
a_eff = eff_df.loc[away_tm] if away_tm in eff_df.index else None
h_eff = eff_df.loc[home_tm] if home_tm in eff_df.index else None
usage_matchup = aggregate_team_skill_usage(player_df, [away_tm, home_tm])
inj_matchup = build_injury_impact_report(
    injuries_df, snaps_df, usage_matchup, [away_tm, home_tm], selected_week
)
h2h_history = get_head_to_head_history(master_games_df, away_tm, home_tm, limit=8)


def get_unit_penalty(tm: str, side: str) -> float:
    if inj_matchup.empty:
        return 0.0
    sub = inj_matchup[(inj_matchup["team"] == tm) & (inj_matchup["unit_side"] == side)]
    return float(sub["est_epa_penalty"].sum())


away_off_pen = get_unit_penalty(away_tm, "Offense")
away_def_pen = get_unit_penalty(away_tm, "Defense")
home_off_pen = get_unit_penalty(home_tm, "Offense")
home_def_pen = get_unit_penalty(home_tm, "Defense")

a_ovr_badge = render_rank_badge(int(a_eff["off_epa_rank"]), f"{away_tm} Off") if a_eff is not None else ""
h_ovr_badge = render_rank_badge(int(h_eff["off_epa_rank"]), f"{home_tm} Off") if h_eff is not None else ""

# Requirement #1: Clean HTML rendering via render_html() so <span class="badge-sage"> never leaks
render_html(
    f"""
    <div class="terminal-card">
        <div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:12px;">
            <div>
                <span class="metric-subtext">ACTIVE MATCHUP DRILL-DOWN • {selected_season} WEEK {selected_week} • {stadium_str} ({roof_str})</span>
                <h2 style="margin:4px 0 6px 0; color:#F8FAFC;">{away_tm} @ {home_tm}</h2>
                <div>{a_ovr_badge} {h_ovr_badge}</div>
            </div>
            <div style="display:flex; gap:6px; align-items:center; flex-wrap:wrap;">
                {final_score_badge}
                <span class="badge-sage">📌 {spread_str}</span>
                <span class="badge-sage">🎯 {total_str}</span>
                {rest_badge}
            </div>
        </div>
    </div>
    """
)

# 5 Sub-Tabs including the new Player Prop Trend Explorer Tab (Requirement #2)
subtab_brief, subtab_trench, subtab_injuries, subtab_props, subtab_backtest = st.tabs(
    [
        "⚡ Edge Summary Brief & H2H",
        "📊 Trench & Air Efficiency",
        "🚑 Player Mismatches & Injuries",
        "🎯 Player Prop Trend Explorer",
        "📈 Backtest Performance",
    ]
)

# =============================================================================
# SUB-TAB 1: ⚡ EDGE SUMMARY BRIEF & PREVIOUS MATCHUPS PANEL
# =============================================================================
with subtab_brief:
    if a_eff is None or h_eff is None:
        st.warning("Team efficiency data unavailable for this matchup.")
    else:
        away_pass_edge = a_eff["off_pass_epa"] - h_eff["def_pass_epa"]
        away_rush_edge = a_eff["off_rush_epa"] - h_eff["def_rush_epa"]
        home_pass_edge = h_eff["off_pass_epa"] - a_eff["def_pass_epa"]
        home_rush_edge = h_eff["off_rush_epa"] - a_eff["def_rush_epa"]

        net_away_score = (a_eff["off_epa"] - away_off_pen) - (h_eff["def_epa"] + home_def_pen)
        net_home_score = (h_eff["off_epa"] - home_off_pen) - (a_eff["def_epa"] + away_def_pen)
        model_lean_team = home_tm if net_home_score >= net_away_score else away_tm
        model_edge_mag = abs(net_home_score - net_away_score)

        k1, k2, k3, k4 = st.columns(4)
        with k1:
            st.metric(
                "Efficiency Model Lean",
                f"{model_lean_team} Edge",
                delta=f"+{model_edge_mag:.3f} Net EPA/Play",
                delta_color="normal",
            )
        with k2:
            best_phase_val = max(
                [
                    (f"{away_tm} Pass", away_pass_edge),
                    (f"{away_tm} Rush", away_rush_edge),
                    (f"{home_tm} Pass", home_pass_edge),
                    (f"{home_tm} Rush", home_rush_edge),
                ],
                key=lambda x: x[1],
            )
            st.metric(
                "Primary Schematic Lever",
                best_phase_val[0],
                delta=f"{best_phase_val[1]:+.3f} Matchup Delta",
                delta_color="normal",
            )
        with k3:
            total_anchors_out = (
                len(inj_matchup[inj_matchup["role_tier"].str.contains("🔥")])
                if not inj_matchup.empty
                else 0
            )
            st.metric(
                "Flagged Starters on Report",
                f"{total_anchors_out} Anchors",
                delta=f"Away -{away_off_pen + away_def_pen:.2f} | Home -{home_off_pen + home_def_pen:.2f} EPA",
                delta_color="inverse" if total_anchors_out > 0 else "normal",
            )
        with k4:
            if not h2h_history.empty:
                h_wins = int((h2h_history["SU Winner"] == home_tm).sum())
                a_wins = int((h2h_history["SU Winner"] == away_tm).sum())
                last_res = h2h_history.iloc[0]["Matchup & Final"]
                st.metric(
                    f"Recent H2H ({len(h2h_history)} Games)",
                    f"{home_tm} {h_wins} - {away_tm} {a_wins}",
                    delta=f"Last: {last_res}",
                    delta_color="off",
                )
            else:
                st.metric("Recent H2H Series", "No Recent Games", delta="N/A", delta_color="off")

        col_brief_left, col_brief_right = st.columns([1.15, 1])

        with col_brief_left:
            a_pass_rk, a_rush_rk = int(a_eff["off_pass_epa_rank"]), int(a_eff["off_rush_epa_rank"])
            h_pdef_rk, h_rdef_rk = int(h_eff["def_pass_epa_rank"]), int(h_eff["def_rush_epa_rank"])

            h_pass_rk, h_rush_rk = int(h_eff["off_pass_epa_rank"]), int(h_eff["off_rush_epa_rank"])
            a_pdef_rk, a_rdef_rk = int(a_eff["def_pass_epa_rank"]), int(a_eff["def_rush_epa_rank"])

            if (h_pdef_rk - a_pass_rk) >= (h_rdef_rk - a_rush_rk):
                away_plan_html = (
                    f"🎯 <b>{away_tm} Air Attack Funnel:</b> <b>{away_tm}</b> Pass Offense "
                    f"{render_rank_badge(a_pass_rk)} (<b>{a_eff['off_pass_epa']:+.3f} EPA</b>) attacks "
                    f"<b>{home_tm}</b> Pass Defense {render_rank_badge(h_pdef_rk)} — expect early dropbacks "
                    f"and high-volume intermediate targeting."
                )
            else:
                away_plan_html = (
                    f"🚜 <b>{away_tm} Ground Control:</b> <b>{away_tm}</b> Rush Offense "
                    f"{render_rank_badge(a_rush_rk)} (<b>{a_eff['off_rush_epa']:+.3f} EPA</b>) presses "
                    f"<b>{home_tm}</b> Run Front {render_rank_badge(h_rdef_rk)} — sets up early-down "
                    f"efficiency and high-percentage play-action."
                )

            if (a_pdef_rk - h_pass_rk) >= (a_rdef_rk - h_rush_rk):
                home_plan_html = (
                    f"🚀 <b>{home_tm} Passing Ceiling:</b> <b>{home_tm}</b> Pass Offense "
                    f"{render_rank_badge(h_pass_rk)} (<b>{h_eff['off_pass_epa']:+.3f} EPA</b>) squares off with "
                    f"<b>{away_tm}</b> Coverage {render_rank_badge(a_pdef_rk)} — elevated explosive-play "
                    f"probability through the air."
                )
            else:
                home_plan_html = (
                    f"🔨 <b>{home_tm} Trench Dominance:</b> <b>{home_tm}</b> Rush Offense "
                    f"{render_rank_badge(h_rush_rk)} (<b>{h_eff['off_rush_epa']:+.3f} EPA</b>) leans on "
                    f"<b>{away_tm}</b> Rush Defense {render_rank_badge(a_rdef_rk)} to control clock and "
                    f"stay ahead of the chains."
                )

            if pd.notna(rest_v) and abs(rest_v) >= 2:
                adv_rest_tm = home_tm if rest_v > 0 else away_tm
                sit_bullet_html = (
                    f"🔋 <b>Situational Preparation Edge:</b> <b>{adv_rest_tm}</b> enters with a "
                    f'<span class="badge-elite">+{int(abs(rest_v))} DAY REST EDGE</span>, '
                    f"boosting 4th-quarter pass-rush and trench stamina."
                )
            else:
                sit_bullet_html = (
                    f"🏟️ <b>Situational Parity:</b> Both teams enter on even rest inside "
                    f"<b>{stadium_str}</b> ({roof_str}), making red-zone execution the primary swing factor."
                )

            if not inj_matchup.empty and len(inj_matchup[inj_matchup["role_tier"].str.contains("🔥")]) > 0:
                top_inj = inj_matchup.iloc[0]
                inj_bullet_html = (
                    f"🚑 <b>Critical Cluster Absence:</b> <b>{top_inj['team']}</b> starter "
                    f"<b>{top_inj['player_display']}</b> ({top_inj.get('position', 'POS')}) is listed "
                    f"{render_injury_badge(top_inj['report_status'])}, shaving "
                    f"<b>-{top_inj['est_epa_penalty']:.3f} EPA/play</b> off their {top_inj['unit_side'].lower()} unit."
                )
            else:
                inj_bullet_html = (
                    '💚 <b>Clean Starting Lineups:</b> <span class="badge-elite">FULL STRENGTH</span> '
                    "Neither team has a flagged anchor starter absence on the active weekly report."
                )

            render_html(
                f"""
                <div class="terminal-card-elite">
                    <h4 style="margin:0 0 12px 0; color:#00FF87;">⚡ Executive Edge Summary Brief</h4>
                    <div class="brief-bullet">{away_plan_html}</div>
                    <div class="brief-bullet">{home_plan_html}</div>
                    <div class="brief-bullet">{sit_bullet_html}</div>
                    <div class="brief-bullet">{inj_bullet_html}</div>
                </div>
                """
            )

        with col_brief_right:
            fav_team = home_tm if (pd.notna(spread_v) and spread_v <= 0) else away_tm
            dog_team = away_tm if fav_team == home_tm else home_tm

            weapon_callout_html = "Balanced skill distribution expected across primary receivers and backs."
            if not usage_matchup.empty:
                top_w = usage_matchup.sort_values(by="calc_target_share", ascending=False).iloc[0]
                w_tm = top_w["team"]
                opp_tm = home_tm if w_tm == away_tm else away_tm
                opp_p_rk = int(eff_df.loc[opp_tm, "def_pass_epa_rank"])
                weapon_callout_html = (
                    f"<b>{top_w['player_name']}</b> ({w_tm} {top_w['position']}) commands a "
                    f"<b>{top_w['calc_target_share']*100:.1f}% target share</b> against "
                    f"<b>{opp_tm}</b> Pass Defense {render_rank_badge(opp_p_rk)}."
                )

            render_html(
                f"""
                <div class="terminal-card">
                    <h4 style="margin:0 0 12px 0; color:#7FD1B9;">🎬 Projected Game Script & Flow</h4>
                    <div class="brief-bullet">
                        1️⃣ <b>Opening Quarters:</b> <b>{model_lean_team}</b> holds a
                        <span class="badge-elite">+{model_edge_mag:.3f} NET EPA/PLAY</span> schematic cushion.
                        Expect <b>{fav_team}</b> to script early-down concepts attacking the weakest opposing defensive tier.
                    </div>
                    <div class="brief-bullet">
                        2️⃣ <b>Focal Point Matchup:</b> {weapon_callout_html}
                    </div>
                    <div class="brief-bullet">
                        3️⃣ <b>2nd-Half Pivot:</b> If <b>{fav_team}</b> builds a single-score cushion,
                        <b>{dog_team}</b> is forced into predictable dropback mode — testing pass protection against opposing edge rushers.
                    </div>
                </div>
                """
            )

        st.markdown(f"#### 🏛️ Previous Head-to-Head Matchups ({away_tm} vs {home_tm})")
        if h2h_history.empty:
            st.info(f"No completed historical matchups found between {away_tm} and {home_tm} in the dataset.")
        else:
            h2h_col_cards, h2h_col_table = st.columns([1, 1.6])

            with h2h_col_cards:
                for _, h_row in h2h_history.head(3).iterrows():
                    win_tm = h_row["SU Winner"]
                    badge_w = (
                        f'<span class="badge-elite">🏆 {win_tm} WON</span>'
                        if win_tm != "TIE"
                        else '<span class="badge-mid">TIE</span>'
                    )
                    render_html(
                        f"""
                        <div class="terminal-card" style="padding:12px; margin-bottom:8px;">
                            <div style="display:flex; justify-content:space-between; align-items:center;">
                                <b>{int(h_row['season'])} Week {int(h_row['week'])} ({h_row.get('gameday', '')})</b>
                                {badge_w}
                            </div>
                            <div style="margin-top:6px; font-size:0.95rem;">
                                <b>{h_row['Matchup & Final']}</b>
                            </div>
                            <div class="metric-subtext" style="margin-top:4px;">
                                ATS: <b>{h_row['ATS Result']}</b> | Total Points: <b>{h_row['Total Pts']}</b>
                            </div>
                        </div>
                        """
                    )

            with h2h_col_table:
                h2h_disp = h2h_history[
                    ["season", "week", "gameday", "Matchup & Final", "SU Winner", "ATS Result", "Total Pts"]
                ].copy()
                st.dataframe(
                    h2h_disp,
                    width="stretch",
                    hide_index=True,
                    column_config={
                        "season": st.column_config.NumberColumn("Season", format="%d"),
                        "week": st.column_config.NumberColumn("Week", format="%d"),
                        "gameday": "Date",
                        "Matchup & Final": "Score",
                        "SU Winner": "Winner",
                        "ATS Result": "Spread Outcome",
                        "Total Pts": "Combined Pts",
                    },
                )

# =============================================================================
# SUB-TAB 2: 📊 TRENCH & AIR EFFICIENCY
# =============================================================================
with subtab_trench:
    if a_eff is None or h_eff is None:
        st.warning("Efficiency metrics unavailable for one or both teams.")
    else:
        mismatch_cards = []
        unit_pairs = [
            (away_tm, home_tm, "Pass", a_eff["off_pass_epa"], int(a_eff["off_pass_epa_rank"]), h_eff["def_pass_epa"], int(h_eff["def_pass_epa_rank"])),
            (away_tm, home_tm, "Rush", a_eff["off_rush_epa"], int(a_eff["off_rush_epa_rank"]), h_eff["def_rush_epa"], int(h_eff["def_rush_epa_rank"])),
            (home_tm, away_tm, "Pass", h_eff["off_pass_epa"], int(h_eff["off_pass_epa_rank"]), a_eff["def_pass_epa"], int(a_eff["def_pass_epa_rank"])),
            (home_tm, away_tm, "Rush", h_eff["off_rush_epa"], int(h_eff["off_rush_epa_rank"]), a_eff["def_rush_epa"], int(a_eff["def_rush_epa_rank"])),
        ]

        for o_tm, d_tm, phase, o_val, o_rk, d_val, d_rk in unit_pairs:
            if o_rk <= 10 and d_rk >= 23:
                mismatch_cards.append(
                    {
                        "style": "terminal-card-elite",
                        "badges": f"{render_rank_badge(o_rk, f'{o_tm} {phase} Off')} vs {render_rank_badge(d_rk, f'{d_tm} {phase} Def')}",
                        "title": f"🔥 {o_tm} {phase} Offense Smash Spot (+{d_rk - o_rk} Rank Edge)",
                        "detail": f"{o_tm} generates {o_val:+.3f} EPA/play against a vulnerable {d_tm} defense allowing {d_val:+.3f} EPA/play.",
                    }
                )
            elif d_rk <= 5 and o_rk >= 23:
                mismatch_cards.append(
                    {
                        "style": "terminal-card-vuln",
                        "badges": f"{render_rank_badge(d_rk, f'{d_tm} {phase} Def')} vs {render_rank_badge(o_rk, f'{o_tm} {phase} Off')}",
                        "title": f"🛡️ {d_tm} {phase} Defense Shutdown Spot (+{o_rk - d_rk} Rank Edge)",
                        "detail": f"Elite {d_tm} unit ({d_val:+.3f} EPA allowed) clamps down on struggling {o_tm} {phase.lower()} attack ({o_val:+.3f} EPA).",
                    }
                )

        if mismatch_cards:
            m_cols = st.columns(len(mismatch_cards))
            for i, card in enumerate(mismatch_cards):
                with m_cols[i]:
                    render_html(
                        f"""
                        <div class="{card['style']}">
                            <div>{card['badges']}</div>
                            <h4 style="margin:8px 0 4px 0;">{card['title']}</h4>
                            <span class="metric-subtext">{card['detail']}</span>
                        </div>
                        """
                    )

        def render_possession_block(
            off_tm: str, def_tm: str, o_row: pd.Series, d_row: pd.Series, off_pen: float, def_pen: float
        ):
            st.markdown(f"#### 🏈 When **{off_tm}** Has the Ball (**{off_tm} Offense** vs **{def_tm} Defense**)")
            c1, c2, c3 = st.columns(3)

            with c1:
                with st.container(border=True):
                    render_html(
                        f"<b>AIR EFFICIENCY ({off_tm} Pass vs {def_tm} Pass Def)</b><br>"
                        f"{render_rank_badge(int(o_row['off_pass_epa_rank']), f'{off_tm} Off')} "
                        f"{render_rank_badge(int(d_row['def_pass_epa_rank']), f'{def_tm} Def')}"
                    )
                    m_a, m_b = st.columns(2)
                    m_a.metric(
                        f"{off_tm} Pass EPA",
                        f"{o_row['off_pass_epa']:+.3f}",
                        delta=f"Rank #{int(o_row['off_pass_epa_rank'])}",
                        delta_color="normal" if o_row["off_pass_epa_rank"] <= 16 else "inverse",
                    )
                    m_b.metric(
                        f"{def_tm} Pass EPA Allowed",
                        f"{d_row['def_pass_epa']:+.3f}",
                        delta=f"Rank #{int(d_row['def_pass_epa_rank'])}",
                        delta_color="normal" if d_row["def_pass_epa_rank"] <= 16 else "inverse",
                    )
                    st.caption(
                        f"Pass Success Rate: **{off_tm}** {o_row['off_pass_sr']*100:.1f}% "
                        f"| **{def_tm} Allowed** {d_row['def_pass_sr']*100:.1f}%"
                    )

            with c2:
                with st.container(border=True):
                    render_html(
                        f"<b>TRENCH EFFICIENCY ({off_tm} Rush vs {def_tm} Rush Def)</b><br>"
                        f"{render_rank_badge(int(o_row['off_rush_epa_rank']), f'{off_tm} Off')} "
                        f"{render_rank_badge(int(d_row['def_rush_epa_rank']), f'{def_tm} Def')}"
                    )
                    m_a, m_b = st.columns(2)
                    m_a.metric(
                        f"{off_tm} Rush EPA",
                        f"{o_row['off_rush_epa']:+.3f}",
                        delta=f"Rank #{int(o_row['off_rush_epa_rank'])}",
                        delta_color="normal" if o_row["off_rush_epa_rank"] <= 16 else "inverse",
                    )
                    m_b.metric(
                        f"{def_tm} Rush EPA Allowed",
                        f"{d_row['def_rush_epa']:+.3f}",
                        delta=f"Rank #{int(d_row['def_rush_epa_rank'])}",
                        delta_color="normal" if d_row["def_rush_epa_rank"] <= 16 else "inverse",
                    )
                    st.caption(
                        f"Rush Success Rate: **{off_tm}** {o_row['off_rush_sr']*100:.1f}% "
                        f"| **{def_tm} Allowed** {d_row['def_rush_sr']*100:.1f}%"
                    )

            with c3:
                with st.container(border=True):
                    adj_off_epa = o_row["off_epa"] - off_pen
                    adj_def_epa = d_row["def_epa"] + def_pen
                    render_html(
                        f"<b>OVERALL & INJURY-ADJUSTED EPA</b><br>"
                        f"{render_rank_badge(int(o_row['off_epa_rank']), f'{off_tm} Ovr')} "
                        f"{render_rank_badge(int(d_row['def_epa_rank']), f'{def_tm} Ovr')}"
                    )
                    m_a, m_b = st.columns(2)
                    m_a.metric(
                        f"{off_tm} Adj Off EPA",
                        f"{adj_off_epa:+.3f}",
                        delta=f"{-off_pen:+.3f} Inj Drag" if off_pen > 0 else "Full Strength",
                        delta_color="normal" if off_pen == 0 else "inverse",
                    )
                    m_b.metric(
                        f"{def_tm} Adj Def EPA",
                        f"{adj_def_epa:+.3f}",
                        delta=f"+{def_pen:.3f} Inj Drag" if def_pen > 0 else "Full Strength",
                        delta_color="normal" if def_pen == 0 else "inverse",
                    )
                    st.caption(
                        f"Total Success Rate: **{off_tm}** {o_row['off_sr']*100:.1f}% (#{int(o_row['off_sr_rank'])}) "
                        f"| **{def_tm}** {d_row['def_sr']*100:.1f}% (#{int(d_row['def_sr_rank'])})"
                    )

        render_possession_block(away_tm, home_tm, a_eff, h_eff, away_off_pen, home_def_pen)
        st.write("")
        render_possession_block(home_tm, away_tm, h_eff, a_eff, home_off_pen, away_def_pen)

# =============================================================================
# SUB-TAB 3: 🚑 PLAYER MISMATCHES & INJURIES
# =============================================================================
with subtab_injuries:
    st.markdown(f"#### 🚑 Official Weekly Injury Report & Anchor Impact ({away_tm} @ {home_tm})")

    if inj_matchup.empty:
        render_html(
            f"""
            <div class="terminal-card-elite">
                <span class="badge-elite">⚡ CLEAN INJURY REPORT</span>
                <p style="margin:6px 0 0 0;" class="metric-subtext">
                    No active Out, Doubtful, or Questionable designations found for {away_tm} or {home_tm} in Week {selected_week}.
                </p>
            </div>
            """
        )
    else:
        col_away_inj, col_home_inj = st.columns(2)

        for col_obj, tm in [(col_away_inj, away_tm), (col_home_inj, home_tm)]:
            with col_obj:
                tm_inj = inj_matchup[inj_matchup["team"] == tm].copy()
                total_off_drop = tm_inj[tm_inj["unit_side"] == "Offense"]["est_epa_penalty"].sum()
                total_def_drop = tm_inj[tm_inj["unit_side"] == "Defense"]["est_epa_penalty"].sum()
                anchor_count = len(tm_inj[tm_inj["role_tier"].str.contains("🔥")])

                card_cls = "terminal-card-vuln" if anchor_count > 0 else "terminal-card"
                badge_cls = "badge-bad" if anchor_count > 0 else "badge-mid"
                render_html(
                    f"""
                    <div class="{card_cls}">
                        <div style="display:flex; justify-content:space-between; align-items:center;">
                            <h4 style="margin:0;">{tm} Missing Starters & Drag</h4>
                            <span class="{badge_cls}">🚨 {anchor_count} Anchors Flagged</span>
                        </div>
                        <p style="margin:8px 0 0 0;" class="metric-subtext">
                            Offense EPA Penalty: <b>{-total_off_drop:+.3f}/play</b> |
                            Defense EPA Penalty: <b>+{total_def_drop:.3f}/play allowed</b>
                        </p>
                    </div>
                    """
                )

                for _, r_inj in tm_inj.head(5).iterrows():
                    badge_html = render_injury_badge(r_inj["report_status"])
                    snap_pct = r_inj["snap_share"] * 100
                    tgt_pct = r_inj["calc_target_share"] * 100
                    pos_str = str(r_inj.get("position", "POS"))
                    render_html(
                        f"""
                        <div class="terminal-card" style="padding:12px; margin-bottom:8px;">
                            <div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap;">
                                <div>
                                    <b>{r_inj['player_display']}</b>
                                    <span class="badge-sage">{pos_str}</span>
                                    <span class="metric-subtext">{r_inj['role_tier']}</span>
                                </div>
                                <div>{badge_html}</div>
                            </div>
                            <div class="metric-subtext" style="margin-top:6px;">
                                Injury: <b>{r_inj['primary_injury']}</b> |
                                Snaps: <b>{snap_pct:.0f}%</b> |
                                Target Share: <b>{tgt_pct:.1f}%</b> |
                                EPA Impact: <span style="color:#FF4D6D; font-weight:700;">-{r_inj['est_epa_penalty']:.3f}/play</span>
                            </div>
                        </div>
                        """
                    )

    st.divider()
    st.markdown("#### 🎯 Skill-Player Volume vs Opposing Unit Rank")

    if usage_matchup.empty or a_eff is None or h_eff is None:
        st.info("Player usage or team efficiency splits unavailable for this matchup.")
    else:
        p_col1, p_col2 = st.columns(2)

        for col_ui, (off_tm, def_tm) in [(p_col1, (away_tm, home_tm)), (p_col2, (home_tm, away_tm))]:
            with col_ui:
                st.markdown(f"##### ⚡ {off_tm} Primary Weapons vs {def_tm} Defense")
                tm_weapons = usage_matchup[usage_matchup["team"] == off_tm].copy()
                def_pass_rk = int(eff_df.loc[def_tm, "def_pass_epa_rank"])
                def_rush_rk = int(eff_df.loc[def_tm, "def_rush_epa_rank"])

                top_receivers = tm_weapons.sort_values(by="calc_target_share", ascending=False).head(2)
                top_rusher = (
                    tm_weapons[tm_weapons["position"].isin(["RB", "FB", "QB"])]
                    .sort_values(by="calc_rush_share", ascending=False)
                    .head(1)
                )
                featured = pd.concat([top_receivers, top_rusher]).drop_duplicates(subset=["player_name"])

                for _, w_row in featured.iterrows():
                    is_rec = w_row["calc_target_share"] >= w_row["calc_rush_share"]
                    opp_rk = def_pass_rk if is_rec else def_rush_rk
                    phase_str = f"{def_tm} Pass Def" if is_rec else f"{def_tm} Rush Def"
                    share_lbl = (
                        f"Target Share: {w_row['calc_target_share']*100:.1f}% ({int(w_row['targets'])} tgts)"
                        if is_rec
                        else f"Rush Share: {w_row['calc_rush_share']*100:.1f}% ({int(w_row['carries'])} att)"
                    )

                    opp_unit_badge = render_rank_badge(opp_rk, f"vs {phase_str}")
                    box_cls = (
                        "terminal-card-elite"
                        if opp_rk >= 23
                        else ("terminal-card-vuln" if opp_rk <= 5 else "terminal-card")
                    )
                    pos_badge = str(w_row.get("position", "POS"))
                    scrim_yds = int(w_row["rec_yards"] + w_row["rush_yards"])

                    render_html(
                        f"""
                        <div class="{box_cls}">
                            <div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap;">
                                <div>
                                    <b>{w_row['player_name']}</b>
                                    <span class="badge-sage">{pos_badge}</span>
                                </div>
                                <div>{opp_unit_badge}</div>
                            </div>
                            <div class="metric-subtext" style="margin-top:6px;">
                                {share_lbl} | Season Total EPA: <b>{w_row['total_epa']:+.1f}</b> |
                                Scrimmage Yds: <b>{scrim_yds} yds</b>
                            </div>
                        </div>
                        """
                    )

# =============================================================================
# SUB-TAB 4: 🎯 PLAYER PROP TREND EXPLORER (Requirement #2)
# =============================================================================
with subtab_props:
    st.markdown(f"#### 🎯 Player Prop Trend Explorer ({away_tm} @ {home_tm})")
    st.caption(
        f"Filter active skill players from **{away_tm}** and **{home_tm}** ({player_season} game logs), "
        "adjust your target prop line and lookback window, and inspect conditional green/red hit rates."
    )

    prop_logs = prepare_matchup_player_prop_logs(player_df, [away_tm, home_tm])

    if prop_logs.empty:
        st.info(f"No weekly player game logs found for {away_tm} or {home_tm}.")
    else:
        # Prop Market Mapping
        prop_markets = {
            "Receiving Yards": ("receiving_yards", 54.5, 150.0, 1.0),
            "Receptions": ("receptions", 4.5, 15.0, 0.5),
            "Targets": ("targets", 6.5, 18.0, 0.5),
            "Rushing Yards": ("rushing_yards", 59.5, 160.0, 1.0),
            "Rush Carries": ("carries", 13.5, 30.0, 0.5),
            "Passing Yards": ("passing_yards", 234.5, 400.0, 1.0),
            "Passing TDs": ("passing_tds", 1.5, 5.5, 0.5),
            "Pass Completions": ("completions", 20.5, 38.0, 0.5),
            "Scrimmage Yards (Rush + Rec)": ("scrimmage_yards", 74.5, 180.0, 1.0),
        }

        ctrl_col1, ctrl_col2, ctrl_col3 = st.columns([1, 1.4, 1.3])

        with ctrl_col1:
            allowed_positions = [
                p for p in ["WR", "RB", "TE", "QB"] if p in prop_logs["pos_clean"].unique()
            ]
            if not allowed_positions:
                allowed_positions = sorted(prop_logs["pos_clean"].unique().tolist())

            selected_pos = st.selectbox(
                "1. Filter Position",
                options=["All Skill Positions"] + allowed_positions,
                index=0,
            )

        # Filter active roster by position and rank by total involvement so starters appear at top
        pos_filtered_logs = (
            prop_logs
            if selected_pos == "All Skill Positions"
            else prop_logs[prop_logs["pos_clean"] == selected_pos]
        )

        roster_summary = (
            pos_filtered_logs.groupby(["player_label", "team", "pos_clean"], as_index=False)
            .agg(
                games=("week", "nunique"),
                scrim_yds=("scrimmage_yards", "sum"),
                pass_yds=("passing_yards", "sum"),
            )
        )
        roster_summary["sort_score"] = roster_summary["scrim_yds"] + (roster_summary["pass_yds"] * 0.4)
        roster_summary = roster_summary.sort_values(by="sort_score", ascending=False)
        roster_summary["display_option"] = (
            roster_summary["player_label"]
            + " ("
            + roster_summary["team"]
            + " - "
            + roster_summary["pos_clean"]
            + ")"
        )

        with ctrl_col2:
            selected_player_disp = st.selectbox(
                "2. Select Active Matchup Player",
                options=roster_summary["display_option"].tolist(),
                index=0,
            )

        selected_player_row = roster_summary[
            roster_summary["display_option"] == selected_player_disp
        ].iloc[0]
        sel_player_name = selected_player_row["player_label"]
        sel_player_team = selected_player_row["team"]
        sel_player_pos = selected_player_row["pos_clean"]

        # Smart default market based on player position
        default_market_idx = 0
        if sel_player_pos == "QB":
            default_market_idx = list(prop_markets.keys()).index("Passing Yards")
        elif sel_player_pos == "RB":
            default_market_idx = list(prop_markets.keys()).index("Rushing Yards")

        with ctrl_col3:
            selected_market_label = st.selectbox(
                "3. Select Prop Market",
                options=list(prop_markets.keys()),
                index=default_market_idx,
            )

        stat_col_name, default_line, max_line_cap, step_val = prop_markets[selected_market_label]

        # Extract the selected player's chronological game log
        p_log = pos_filtered_logs[
            (pos_filtered_logs["player_label"] == sel_player_name)
            & (pos_filtered_logs["team"] == sel_player_team)
        ].sort_values(by="week").copy()

        total_avail_games = len(p_log)
        player_median_val = float(p_log[stat_col_name].median()) if total_avail_games > 0 else default_line
        smart_default_threshold = round(player_median_val * 2) / 2 if player_median_val > 0 else default_line
        dynamic_max = float(max(max_line_cap, p_log[stat_col_name].max() * 1.25, 10.0))

        slider_col1, slider_col2 = st.columns(2)
        with slider_col1:
            prop_threshold = st.slider(
                f"🎯 Target Prop Threshold ({selected_market_label})",
                min_value=0.5,
                max_value=float(round(dynamic_max, 0) + 0.5),
                value=float(min(max(0.5, smart_default_threshold), dynamic_max)),
                step=float(step_val),
            )
        with slider_col2:
            if total_avail_games > 1:
                lookback_n = st.slider(
                    "🗓️ Lookback Window (Last N Games)",
                    min_value=1,
                    max_value=total_avail_games,
                    value=min(10, total_avail_games),
                    step=1,
                )
            else:
                lookback_n = 1
                st.caption("Showing single available game log.")

        # Apply lookback window
        window_log = p_log.tail(lookback_n).copy()
        window_log["hit"] = window_log[stat_col_name] >= prop_threshold
        window_log["bar_color"] = np.where(window_log["hit"], "#00FF87", "#FF4D6D")
        window_log["result_label"] = np.where(window_log["hit"], "OVER (HIT)", "UNDER (MISS)")
        window_log["rolling_avg"] = window_log[stat_col_name].expanding().mean()

        hits_count = int(window_log["hit"].sum())
        sample_n = len(window_log)
        hit_rate_pct = (hits_count / sample_n * 100.0) if sample_n > 0 else 0.0
        avg_val = float(window_log[stat_col_name].mean())
        median_val = float(window_log[stat_col_name].median())
        diff_vs_line = avg_val - prop_threshold

        # Determine opposing defense rank for context badge
        opp_def_tm = home_tm if sel_player_team == away_tm else away_tm
        is_rush_prop = stat_col_name in ["rushing_yards", "carries"]
        opp_def_rk = (
            int(eff_df.loc[opp_def_tm, "def_rush_epa_rank"])
            if is_rush_prop
            else int(eff_df.loc[opp_def_tm, "def_pass_epa_rank"])
        )
        def_type_str = "Rush Def" if is_rush_prop else "Pass Def"

        # KPI Summary Row
        pk1, pk2, pk3, pk4 = st.columns(4)
        pk1.metric(
            f"Hit Rate (Last {sample_n} Games)",
            f"{hit_rate_pct:.1f}% ({hits_count}/{sample_n})",
            delta="Strong Over Trend" if hit_rate_pct >= 60 else ("Under Trend" if hit_rate_pct <= 40 else "Balanced Split"),
            delta_color="normal" if hit_rate_pct >= 55 else ("inverse" if hit_rate_pct < 45 else "off"),
        )
        pk2.metric(
            f"Window Average ({selected_market_label})",
            f"{avg_val:.1f}",
            delta=f"{diff_vs_line:+.1f} vs Target ({prop_threshold})",
            delta_color="normal" if diff_vs_line >= 0 else "inverse",
        )
        pk3.metric(
            "Window Median / Floor-Ceiling",
            f"{median_val:.1f} Med",
            delta=f"Min: {window_log[stat_col_name].min():.0f} | Max: {window_log[stat_col_name].max():.0f}",
            delta_color="off",
        )
        pk4.metric(
            f"Opposing {opp_def_tm} {def_type_str}",
            f"Rank #{opp_def_rk}",
            delta="Smash Spot (Bottom-10)" if opp_def_rk >= 23 else ("Tough Draw (Top-5)" if opp_def_rk <= 5 else "Neutral Tier"),
            delta_color="normal" if opp_def_rk >= 23 else ("inverse" if opp_def_rk <= 5 else "off"),
        )

        # Conditional Hit-Rate Plotly Bar Chart
        fig_prop = go.Figure()

        fig_prop.add_trace(
            go.Bar(
                x=window_log["game_tag"],
                y=window_log[stat_col_name],
                marker_color=window_log["bar_color"],
                text=[f"{v:.0f}" if step_val >= 1 else f"{v:.1f}" for v in window_log[stat_col_name]],
                textposition="outside",
                customdata=np.stack((window_log["result_label"], window_log["opp_label"]), axis=-1),
                hovertemplate=(
                    "<b>%{x}</b><br>"
                    f"{selected_market_label}: <b>%{{y}}</b><br>"
                    "Outcome: <b>%{customdata[0]}</b><extra></extra>"
                ),
                name=selected_market_label,
            )
        )

        fig_prop.add_trace(
            go.Scatter(
                x=window_log["game_tag"],
                y=window_log["rolling_avg"],
                mode="lines+markers",
                line=dict(color="#4A90E2", width=2, dash="dot"),
                marker=dict(size=6, color="#4A90E2"),
                name="Cumulative Avg",
            )
        )

        # Horizontal Target Line Overlay
        fig_prop.add_hline(
            y=prop_threshold,
            line_width=2.5,
            line_dash="dash",
            line_color="#FFB020",
            annotation_text=f"Target Line: {prop_threshold} ({hit_rate_pct:.0f}% Hit Rate)",
            annotation_position="top left",
            annotation_font=dict(color="#FFB020", size=12),
        )

        y_upper = max(float(window_log[stat_col_name].max()), prop_threshold) * 1.22 + 2.0
        fig_prop.update_layout(
            title=(
                f"{sel_player_name} ({sel_player_team} {sel_player_pos}) — {selected_market_label} "
                f"(Last {sample_n} Games vs {prop_threshold} Line)"
            ),
            paper_bgcolor="#12161F",
            plot_bgcolor="#12161F",
            font=dict(color="#E2E8F0"),
            xaxis=dict(title="Game Week & Opponent", gridcolor="#262D3D"),
            yaxis=dict(title=selected_market_label, range=[0, y_upper], gridcolor="#262D3D"),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            height=410,
            margin=dict(l=20, r=20, t=60, b=30),
        )

        st.plotly_chart(fig_prop, width="stretch")

        # Matchup Context Banner below Chart
        opp_badge_html = render_rank_badge(opp_def_rk, f"{opp_def_tm} {def_type_str}")
        hit_badge_html = (
            f'<span class="badge-elite">⚡ {hits_count}/{sample_n} OVER ({hit_rate_pct:.0f}%)</span>'
            if hit_rate_pct >= 60
            else (
                f'<span class="badge-bad">🚨 {hits_count}/{sample_n} OVER ({hit_rate_pct:.0f}%)</span>'
                if hit_rate_pct <= 40
                else f'<span class="badge-mid">📊 {hits_count}/{sample_n} OVER ({hit_rate_pct:.0f}%)</span>'
            )
        )

        render_html(
            f"""
            <div class="terminal-card">
                <div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:8px;">
                    <div>
                        <b>{sel_player_name}</b> <span class="badge-sage">{sel_player_team} • {sel_player_pos}</span>
                        <span class="metric-subtext">Prop Line: <b>{prop_threshold} {selected_market_label}</b></span>
                    </div>
                    <div>{hit_badge_html} {opp_badge_html}</div>
                </div>
            </div>
            """
        )

        with st.expander(f"📋 View {sel_player_name} Game-by-Game Log Table ({sample_n} Games)"):
            log_cols = [
                "week",
                "opp_label",
                stat_col_name,
                "result_label",
                "targets",
                "receptions",
                "receiving_yards",
                "carries",
                "rushing_yards",
                "passing_yards",
            ]
            avail_log_cols = list(dict.fromkeys([c for c in log_cols if c in window_log.columns]))
            st.dataframe(
                window_log[avail_log_cols].sort_values(by="week", ascending=False),
                width="stretch",
                hide_index=True,
                column_config={
                    "week": st.column_config.NumberColumn("Week", format="%d"),
                    "opp_label": "Opponent",
                    stat_col_name: st.column_config.NumberColumn(selected_market_label, format="%.1f"),
                    "result_label": f"vs {prop_threshold} Line",
                },
            )

# =============================================================================
# SUB-TAB 5: 📈 BACKTEST PERFORMANCE
# =============================================================================
with subtab_backtest:
    st.markdown(f"#### 📈 {selected_season} Season Historical Backtest & Edge Grading")
    st.caption(
        "Grades all completed games in the selected season where extreme unit mismatches (`⚡ ELITE [#1-#5]` vs `🚨 BAD [#23-#32]`), "
        "situational rest edges (`3+ days`), or high-conviction Net EPA edges occurred."
    )

    bt_summary, bt_log = run_season_backtest(schedule_df, eff_df)

    bt_season_shown = selected_season
    if bt_summary.empty and selected_season == 2026:
        st.info(
            "No completed games with final scores found yet for the selected 2026 slate. "
            "Displaying graded **2025 Full-Season Backtest Benchmark** below (toggle Historical Backtest Mode in the sidebar to inspect 2024 or 2025 schedules directly)."
        )
        sched_2025 = load_season_schedule(2025)
        eff_2025, _ = load_team_efficiency_csv(2025)
        bt_summary, bt_log = run_season_backtest(sched_2025, eff_2025)
        bt_season_shown = 2025

    if bt_summary.empty:
        st.warning("Insufficient completed game data to compute backtest metrics.")
    else:
        total_graded = int(bt_log.shape[0])
        non_push_all = bt_log[~bt_log["Push"]]
        overall_ats_pct = (
            non_push_all["ATS Cover"].mean() * 100.0 if not non_push_all.empty else 0.0
        )
        overall_su_pct = bt_log["SU Win"].mean() * 100.0 if not bt_log.empty else 0.0
        best_cat_row = bt_summary.sort_values(by="ATS Cover %", ascending=False).iloc[0]

        b1, b2, b3, b4 = st.columns(4)
        b1.metric(
            f"{bt_season_shown} Graded Edge Spots",
            f"{total_graded} Games",
            delta="Verified nflverse Lines",
        )
        b2.metric(
            "Aggregate ATS Cover Rate",
            f"{overall_ats_pct:.1f}%",
            delta=f"{overall_ats_pct - 52.38:+.1f}% vs Breakeven (52.4%)",
            delta_color="normal" if overall_ats_pct >= 52.4 else "inverse",
        )
        b3.metric(
            "Aggregate Straight-Up Win %",
            f"{overall_su_pct:.1f}%",
            delta="Outright Winner Rate",
        )
        b4.metric(
            "Top Performing Signal",
            f"{best_cat_row['ATS Cover %']:.1f}% ATS",
            delta=best_cat_row["Edge Category"],
        )

        fig = go.Figure()
        fig.add_trace(
            go.Bar(
                y=bt_summary["Edge Category"],
                x=bt_summary["ATS Cover %"],
                name="ATS Cover %",
                orientation="h",
                marker_color="#00FF87",
                text=[f"{v:.1f}%" for v in bt_summary["ATS Cover %"]],
                textposition="auto",
            )
        )
        fig.add_trace(
            go.Bar(
                y=bt_summary["Edge Category"],
                x=bt_summary["SU Win %"],
                name="Straight-Up Win %",
                orientation="h",
                marker_color="#4A90E2",
                text=[f"{v:.1f}%" for v in bt_summary["SU Win %"]],
                textposition="auto",
            )
        )
        fig.add_vline(
            x=52.38,
            line_width=2,
            line_dash="dash",
            line_color="#FF4D6D",
            annotation_text="52.4% ATS Breakeven (-110)",
            annotation_position="top right",
        )
        fig.update_layout(
            title=f"{bt_season_shown} Historical Cover & Win Rates by Mismatch Signal",
            barmode="group",
            paper_bgcolor="#12161F",
            plot_bgcolor="#12161F",
            font=dict(color="#E2E8F0"),
            xaxis=dict(title="Win / Cover Percentage (%)", range=[0, 100], gridcolor="#262D3D"),
            yaxis=dict(autorange="reversed"),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            height=380,
            margin=dict(l=20, r=20, t=60, b=30),
        )
        st.plotly_chart(fig, width="stretch")

        st.markdown("##### 📊 Signal Performance Breakdown")
        st.dataframe(
            bt_summary,
            width="stretch",
            hide_index=True,
            column_config={
                "Edge Category": "Mismatch / Edge Signal",
                "Sample Size": st.column_config.NumberColumn("Games Flagged", format="%d"),
                "ATS Record": "ATS Record (W-L-P)",
                "ATS Cover %": st.column_config.ProgressColumn(
                    "ATS Cover %", format="%.1f%%", min_value=0, max_value=100
                ),
                "SU Win %": st.column_config.ProgressColumn(
                    "SU Win %", format="%.1f%%", min_value=0, max_value=100
                ),
                "Est. Units (-110)": st.column_config.NumberColumn("Net Units (-110)", format="%+.2f u"),
            },
        )

        with st.expander(f"🔎 Inspect Graded Game-by-Game Backtest Log ({len(bt_log)} Flagged Spots)"):
            cat_filter = st.selectbox(
                "Filter Log by Signal Type",
                ["All Signals"] + list(bt_summary["Edge Category"].unique()),
            )
            filtered_log = (
                bt_log if cat_filter == "All Signals" else bt_log[bt_log["Category"] == cat_filter]
            )
            st.dataframe(
                filtered_log,
                width="stretch",
                hide_index=True,
                column_config={
                    "Week": st.column_config.NumberColumn("Week", format="%d"),
                    "SU Win": st.column_config.CheckboxColumn("SU Win"),
                    "ATS Cover": st.column_config.CheckboxColumn("ATS Cover"),
                    "Push": st.column_config.CheckboxColumn("Push"),
                },
            )