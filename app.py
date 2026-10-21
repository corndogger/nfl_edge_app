import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

# -----------------------------------------------------------------------------
# 1. PAGE CONFIGURATION & TERMINAL CSS THEME (STRICT NO-EMOJI UI)
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="Football Edger",
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

/* ============================================================================
   1. PURE ST.MARKDOWN FLEXBOX TICKER CONTAINER (Requirement #1)
   Uses display: flex; overflow-x: auto; white-space: nowrap;
   ============================================================================ */
.nfl-ticker-flexbox-container {
    display: flex;
    flex-direction: row;
    flex-wrap: nowrap;
    overflow-x: auto;
    overflow-y: hidden;
    white-space: nowrap;
    gap: 10px;
    padding: 10px 10px 12px 10px;
    margin-bottom: 8px;
    background-color: #0B0E14;
    border: 1px solid #1E293B;
    border-radius: 10px;
    scrollbar-width: thin;
    scrollbar-color: #334155 #0B0E14;
    -webkit-overflow-scrolling: touch;
}
.nfl-ticker-flexbox-container::-webkit-scrollbar {
    height: 8px;
}
.nfl-ticker-flexbox-container::-webkit-scrollbar-track {
    background: #0B0E14;
    border-radius: 4px;
}
.nfl-ticker-flexbox-container::-webkit-scrollbar-thumb {
    background-color: #334155;
    border-radius: 4px;
}

/* ============================================================================
   2. STREAMLIT HORIZONTAL BLOCK TICKER OVERRIDE (Interactive Button Strip)
   Forces Streamlit's column row containing .nfl-ticker-marker into a single
   non-wrapping horizontal scroll strip with compact 196px game cards.
   ============================================================================ */
div[data-testid="stHorizontalBlock"]:has(.nfl-ticker-marker) {
    display: flex !important;
    flex-direction: row !important;
    flex-wrap: nowrap !important;
    overflow-x: auto !important;
    overflow-y: hidden !important;
    white-space: nowrap !important;
    gap: 10px !important;
    padding: 8px 8px 14px 8px !important;
    margin-bottom: 10px !important;
    background: #0B0E14 !important;
    border: 1px solid #1E293B !important;
    border-radius: 10px !important;
    scrollbar-width: thin;
    scrollbar-color: #334155 #0B0E14;
    -webkit-overflow-scrolling: touch;
}
div[data-testid="stHorizontalBlock"]:has(.nfl-ticker-marker)::-webkit-scrollbar {
    height: 8px;
}
div[data-testid="stHorizontalBlock"]:has(.nfl-ticker-marker)::-webkit-scrollbar-track {
    background: #0B0E14;
    border-radius: 4px;
}
div[data-testid="stHorizontalBlock"]:has(.nfl-ticker-marker)::-webkit-scrollbar-thumb {
    background-color: #334155;
    border-radius: 4px;
}
div[data-testid="stHorizontalBlock"]:has(.nfl-ticker-marker) > div[data-testid="stColumn"],
div[data-testid="stHorizontalBlock"]:has(.nfl-ticker-marker) > div[data-testid="column"] {
    flex: 0 0 196px !important;
    min-width: 196px !important;
    max-width: 196px !important;
    width: 196px !important;
    white-space: nowrap !important;
}

/* Individual Ticker Card Visuals */
.ticker-card {
    background-color: #131822;
    border: 1px solid #283246;
    border-top: 3px solid #3B475E;
    border-radius: 7px 7px 0 0;
    padding: 8px 10px;
    margin-bottom: -14px;
    white-space: nowrap;
    transition: all 0.14s ease-in-out;
}
.ticker-card-active {
    background: linear-gradient(180deg, #0F2920 0%, #121A26 100%);
    border: 1px solid #00FF87;
    border-top: 3px solid #00FF87;
    box-shadow: 0 0 14px rgba(0, 255, 135, 0.22);
    border-radius: 7px 7px 0 0;
    padding: 8px 10px;
    margin-bottom: -14px;
    white-space: nowrap;
}
.ticker-top-bar {
    display: flex;
    justify-content: space-between;
    align-items: center;
    font-size: 0.67rem;
    font-family: monospace;
    color: #94A3B8;
    margin-bottom: 5px;
    padding-bottom: 4px;
    border-bottom: 1px solid #1E293B;
    white-space: nowrap;
}
.ticker-matchup-header {
    font-family: monospace;
    font-size: 0.72rem;
    font-weight: 800;
    color: #CBD5E1;
    letter-spacing: 0.03em;
    margin-bottom: 5px;
    white-space: nowrap;
}
.ticker-slot-tag-tnf {
    background-color: rgba(255, 176, 32, 0.16);
    color: #FFB020;
    border: 1px solid #FFB020;
    padding: 0px 5px;
    border-radius: 3px;
    font-size: 0.63rem;
    font-weight: 800;
    font-family: monospace;
}
.ticker-slot-tag-snf {
    background-color: rgba(0, 255, 135, 0.15);
    color: #00FF87;
    border: 1px solid #00FF87;
    padding: 0px 5px;
    border-radius: 3px;
    font-size: 0.63rem;
    font-weight: 800;
    font-family: monospace;
}
.ticker-slot-tag-mnf {
    background-color: rgba(56, 189, 248, 0.16);
    color: #38BDF8;
    border: 1px solid #38BDF8;
    padding: 0px 5px;
    border-radius: 3px;
    font-size: 0.63rem;
    font-weight: 800;
    font-family: monospace;
}
.ticker-slot-tag-spc {
    background-color: rgba(192, 132, 252, 0.16);
    color: #C084FC;
    border: 1px solid #C084FC;
    padding: 0px 5px;
    border-radius: 3px;
    font-size: 0.63rem;
    font-weight: 800;
    font-family: monospace;
}
.ticker-team-row {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin: 3px 0;
    font-family: monospace;
    font-size: 0.84rem;
    font-weight: 700;
    color: #F8FAFC;
    white-space: nowrap;
}
.ticker-team-left {
    display: flex;
    align-items: center;
    gap: 6px;
    white-space: nowrap;
}
.ticker-score-win {
    font-family: monospace;
    font-size: 0.88rem;
    font-weight: 800;
    color: #00FF87;
}
.ticker-score {
    font-family: monospace;
    font-size: 0.86rem;
    font-weight: 700;
    color: #CBD5E1;
}
.ticker-score-muted {
    font-family: monospace;
    font-size: 0.75rem;
    color: #64748B;
}
.ticker-footer {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-top: 6px;
    padding-top: 4px;
    border-top: 1px dashed #263042;
    font-size: 0.66rem;
    font-family: monospace;
    color: #94A3B8;
    white-space: nowrap;
}

/* Style the action button docked seamlessly at the bottom of each ticker card */
div[data-testid="stHorizontalBlock"]:has(.nfl-ticker-marker) div[data-testid="stButton"] > button {
    border-radius: 0 0 7px 7px !important;
    font-family: monospace !important;
    font-size: 0.71rem !important;
    font-weight: 700 !important;
    height: 28px !important;
    min-height: 28px !important;
    padding: 0 8px !important;
    margin-top: 0 !important;
    white-space: nowrap !important;
}

/* High-Visibility Active Game Selection Banner */
.active-game-spotlight {
    background: linear-gradient(135deg, #0D1B2A 0%, #112233 55%, #0F1E19 100%);
    border: 2px solid #00FF87;
    box-shadow: 0 0 22px rgba(0, 255, 135, 0.18);
    border-radius: 12px;
    padding: 18px 22px;
    margin: 6px 0 16px 0;
    color: #F8FAFC;
}
.active-lock-pill {
    background-color: rgba(0, 255, 135, 0.18);
    color: #00FF87;
    border: 1px solid #00FF87;
    padding: 3px 10px;
    border-radius: 999px;
    font-size: 0.74rem;
    font-weight: 800;
    letter-spacing: 0.06em;
    font-family: monospace;
    display: inline-block;
    text-transform: uppercase;
}

/* Clean Dot-Indicator Unit Ranking & Status Badges */
.badge-elite {
    background-color: rgba(0, 255, 135, 0.14);
    color: #00FF87;
    border: 1px solid #00FF87;
    padding: 2px 8px;
    border-radius: 4px;
    font-size: 0.75rem;
    font-weight: 700;
    font-family: monospace;
    display: inline-block;
    margin: 2px 2px;
}
.badge-mid {
    background-color: rgba(148, 163, 184, 0.12);
    color: #94A3B8;
    border: 1px solid #475569;
    padding: 2px 8px;
    border-radius: 4px;
    font-size: 0.75rem;
    font-weight: 600;
    font-family: monospace;
    display: inline-block;
    margin: 2px 2px;
}
.badge-bad {
    background-color: rgba(220, 20, 60, 0.18);
    color: #FF4D6D;
    border: 1px solid #DC143C;
    padding: 2px 8px;
    border-radius: 4px;
    font-size: 0.75rem;
    font-weight: 700;
    font-family: monospace;
    display: inline-block;
    margin: 2px 2px;
}
.badge-amber {
    background-color: rgba(255, 176, 32, 0.15);
    color: #FFB020;
    border: 1px solid #FFB020;
    padding: 2px 8px;
    border-radius: 4px;
    font-size: 0.75rem;
    font-weight: 700;
    font-family: monospace;
    display: inline-block;
    margin: 2px 2px;
}
.badge-sage {
    background-color: rgba(110, 168, 150, 0.15);
    color: #7FD1B9;
    border: 1px solid #7FD1B9;
    padding: 2px 8px;
    border-radius: 4px;
    font-size: 0.75rem;
    font-weight: 600;
    font-family: monospace;
    display: inline-block;
    margin: 2px 2px;
}
.badge-hot {
    background-color: rgba(255, 107, 53, 0.18);
    color: #FF8C42;
    border: 1px solid #FF6B35;
    padding: 3px 9px;
    border-radius: 4px;
    font-size: 0.76rem;
    font-weight: 700;
    font-family: monospace;
    display: inline-block;
    margin: 2px 3px;
}
.badge-cold {
    background-color: rgba(56, 189, 248, 0.16);
    color: #38BDF8;
    border: 1px solid #0284C7;
    padding: 3px 9px;
    border-radius: 4px;
    font-size: 0.76rem;
    font-weight: 700;
    font-family: monospace;
    display: inline-block;
    margin: 2px 3px;
}
.team-pill {
    background-color: #1E293B;
    color: #F8FAFC;
    border: 1px solid #475569;
    padding: 3px 10px;
    border-radius: 999px;
    font-size: 0.85rem;
    font-weight: 700;
    font-family: monospace;
    display: inline-flex;
    align-items: center;
    gap: 6px;
    margin: 0 4px;
}
.team-pill-lg {
    background-color: #162234;
    color: #FFFFFF;
    border: 1px solid #3B82F6;
    padding: 6px 14px;
    border-radius: 10px;
    font-size: 1.3rem;
    font-weight: 800;
    font-family: monospace;
    display: inline-flex;
    align-items: center;
    gap: 10px;
    margin: 0 6px;
}
.metric-subtext {
    font-size: 0.82rem;
    color: #94A3B8;
    font-family: monospace;
}

/* Comparative Brief Pillars & Tactical Timeline */
.brief-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 12px;
    margin-bottom: 12px;
}
.unit-pillar {
    background-color: #151B26;
    border: 1px solid #263042;
    border-radius: 8px;
    padding: 12px 14px;
}
.unit-pillar-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    border-bottom: 1px solid #263042;
    padding-bottom: 8px;
    margin-bottom: 10px;
    font-weight: 700;
    font-size: 0.92rem;
    color: #F8FAFC;
}
.unit-tier-row {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 5px 0;
    font-size: 0.84rem;
    border-bottom: 1px dashed rgba(71, 85, 105, 0.35);
}
.unit-tier-label {
    color: #94A3B8;
    font-family: monospace;
    font-weight: 600;
    min-width: 58px;
}
.unit-lever-footer {
    margin-top: 9px;
    padding-top: 6px;
    font-size: 0.82rem;
    color: #E2E8F0;
    display: flex;
    justify-content: space-between;
    align-items: center;
}
.brief-context-strip {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 12px;
    background-color: #141A24;
    border: 1px solid #262D3D;
    border-radius: 8px;
    padding: 10px 14px;
}
.context-cell-title {
    font-size: 0.72rem;
    font-family: monospace;
    color: #94A3B8;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    margin-bottom: 4px;
}
.tactical-step {
    background-color: #151B26;
    border: 1px solid #263042;
    border-left: 3px solid #7FD1B9;
    border-radius: 6px;
    padding: 10px 14px;
    margin-bottom: 10px;
}
.tactical-step-last {
    background-color: #151B26;
    border: 1px solid #263042;
    border-left: 3px solid #FFB020;
    border-radius: 6px;
    padding: 10px 14px;
    margin-bottom: 0;
}
.tactical-phase-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 5px;
}
.tactical-phase-tag {
    font-size: 0.73rem;
    font-family: monospace;
    font-weight: 800;
    color: #7FD1B9;
    letter-spacing: 0.05em;
    text-transform: uppercase;
}
.tactical-body {
    font-size: 0.88rem;
    color: #F1F5F9;
    line-height: 1.45;
}

/* 1-on-1 CB vs WR Battle Cards */
.cb-wr-vs-row {
    display: flex;
    justify-content: space-between;
    align-items: center;
    background-color: #161D2A;
    border: 1px solid #283246;
    border-radius: 6px;
    padding: 8px 12px;
    margin: 8px 0;
}
</style>
""",
    unsafe_allow_html=True,
)

OFFENSE_POSITIONS = {"QB", "RB", "FB", "WR", "TE", "OL", "T", "OT", "LT", "RT", "G", "OG", "LG", "RG", "C"}
DEFENSE_POSITIONS = {"DL", "DE", "DT", "NT", "EDGE", "LB", "ILB", "OLB", "MLB", "DB", "CB", "S", "FS", "SS"}
SPECIAL_TEAMS_POSITIONS = {"K", "P", "LS"}


def render_html(html_str: str) -> None:
    """
    Safely renders custom HTML blocks in Streamlit by stripping leading line whitespace
    so Markdown's 4-space code-block parser never leaks raw <span> or <div> tags.
    """
    cleaned = "\n".join(line.lstrip() for line in html_str.strip().splitlines())
    st.markdown(cleaned, unsafe_allow_html=True)


def get_team_logo_url(team_abbr: str) -> str:
    """Maps NFL team abbreviations to ESPN CDN transparent team logos."""
    if not team_abbr or pd.isna(team_abbr):
        return ""
    clean = str(team_abbr).strip().upper()
    espn_map = {"LA": "lar", "LAR": "lar", "WAS": "wsh", "WSH": "wsh"}
    code = espn_map.get(clean, clean.lower())
    return f"https://a.espncdn.com/i/teamlogos/nfl/500/{code}.png"


def render_inline_logo(team_abbr: str, size: int = 20) -> str:
    """Renders an inline HTML <img> tag for a team logo next to headers and summaries."""
    logo = get_team_logo_url(team_abbr)
    return (
        f'<img src="{logo}" width="{size}" height="{size}" '
        f'style="vertical-align:middle; margin-right:5px;" onerror="this.style.display=\'none\'">'
    )


def render_team_pill(team_abbr: str, role_tag: str = "", large: bool = False) -> str:
    """Renders an inline HTML team pill with embedded logo and optional clean H/A tag."""
    logo = get_team_logo_url(team_abbr)
    cls = "team-pill-lg" if large else "team-pill"
    img_sz = 34 if large else 18
    role_html = (
        f'<span style="color:#94A3B8; font-size:0.75em; font-weight:600;">({role_tag})</span>'
        if role_tag
        else ""
    )
    return (
        f'<span class="{cls}">'
        f'<img src="{logo}" width="{img_sz}" height="{img_sz}" style="vertical-align:middle;" onerror="this.style.display=\'none\'">'
        f"{team_abbr} {role_html}</span>"
    )


def render_rank_badge(rank: int, prefix: str = "") -> str:
    """
    Renders standardized unit ranking tags using clean colored dot indicators:
    - Top 5 (1-5): ● ELITE [#X]
    - Bottom 10 (23-32): ● BAD [#X]
    - Middle Tier (6-22): ● MID [#X]
    """
    lbl = f"{prefix} " if prefix else ""
    if rank <= 5:
        return f'<span class="badge-elite">● {lbl}ELITE [#{rank}]</span>'
    if rank >= 23:
        return f'<span class="badge-bad">● {lbl}BAD [#{rank}]</span>'
    return f'<span class="badge-mid">● {lbl}MID [#{rank}]</span>'


def render_injury_badge(status: str) -> str:
    """Renders an HTML badge for official NFL injury report designations using clean dot indicators."""
    status_clean = str(status).strip().upper()
    if status_clean in ["OUT", "IR", "PUP", "SUSPENDED"]:
        return f'<span class="badge-bad">● [{status_clean}]</span>'
    if status_clean == "DOUBTFUL":
        return f'<span class="badge-bad">● [{status_clean}]</span>'
    if status_clean == "QUESTIONABLE":
        return f'<span class="badge-amber">● [{status_clean}]</span>'
    return f'<span class="badge-mid">● [{status_clean}]</span>'


def classify_primetime_code(row: pd.Series) -> str:
    """
    Detects compact broadcast tags for the NFL.com-style ticker (Requirement #2):
    Returns [TNF], [SNF], [MNF], [SPC], or empty string for standard Sunday daytime games.
    """
    weekday = str(row.get("weekday", "")).strip().lower()
    gameday = str(row.get("gameday", "")).strip()
    gametime = str(row.get("gametime", "")).strip()

    if not weekday and gameday:
        try:
            weekday = pd.to_datetime(gameday).day_name().lower()
        except Exception:
            weekday = ""

    hour = 13
    if ":" in gametime:
        try:
            hour = int(gametime.split(":")[0])
        except Exception:
            hour = 13

    if "thursday" in weekday:
        return "[TNF]"
    if "monday" in weekday:
        return "[MNF]"
    if "sunday" in weekday and hour >= 19:
        return "[SNF]"
    if "friday" in weekday or "saturday" in weekday or hour < 12:
        return "[SPC]"
    return ""


def render_slot_badge_html(slot_code: str) -> str:
    """Returns color-coded HTML badge for [TNF], [SNF], [MNF], or [SPC]."""
    if slot_code == "[TNF]":
        return '<span class="ticker-slot-tag-tnf">[TNF]</span>'
    if slot_code == "[SNF]":
        return '<span class="ticker-slot-tag-snf">[SNF]</span>'
    if slot_code == "[MNF]":
        return '<span class="ticker-slot-tag-mnf">[MNF]</span>'
    if slot_code == "[SPC]":
        return '<span class="ticker-slot-tag-spc">[SPC]</span>'
    return '<span class="ticker-score-muted">[SUN]</span>'


def select_game_callback(game_id: str, idx: int) -> None:
    """Updates st.session_state['selected_game'] when a ticker card is clicked."""
    st.session_state["selected_game"] = game_id
    st.session_state["selected_game_idx"] = idx


def render_nfl_horizontal_ticker(week_games: pd.DataFrame) -> None:
    """
    Renders the horizontally scrollable NFL.com-style weekly game strip at the top of the page.
    - Container Layout: Styled with CSS flexbox (`display: flex; overflow-x: auto; white-space: nowrap;`)
    - Card Content: Away vs. Home shorthand, live/final scores, and [TNF], [SNF], [MNF], or [SPC] tags.
    - State Interactivity: Clicking any game card updates st.session_state['selected_game'] and triggers st.rerun().
    """
    if week_games.empty:
        st.info("No games match the current filter criteria.")
        return

    current_selected_id = st.session_state.get("selected_game")
    cols = st.columns(len(week_games))

    for idx, (_, row) in enumerate(week_games.iterrows()):
        game_id = str(row["game_id"])
        is_selected = game_id == current_selected_id

        away_tm = str(row["away_team"]).strip().upper()
        home_tm = str(row["home_team"]).strip().upper()
        away_logo = get_team_logo_url(away_tm)
        home_logo = get_team_logo_url(home_tm)

        away_pts = row.get("away_score", np.nan)
        home_pts = row.get("home_score", np.nan)
        has_scores = pd.notna(away_pts) and pd.notna(home_pts)

        spread_v = row.get("home_spread", np.nan)
        total_v = row.get("total_line", np.nan)
        slot_code = str(row.get("broadcast_slot", ""))
        gametime_str = str(row.get("gametime", "TBD"))
        gameday_str = str(row.get("gameday", ""))[-5:] if pd.notna(row.get("gameday")) else ""

        if has_scores:
            a_int, h_int = int(away_pts), int(home_pts)
            a_cls = "ticker-score-win" if a_int > h_int else "ticker-score"
            h_cls = "ticker-score-win" if h_int > a_int else "ticker-score"
            a_score_html = f'<span class="{a_cls}">{a_int}</span>'
            h_score_html = f'<span class="{h_cls}">{h_int}</span>'
            status_text = "FINAL"
        else:
            a_score_html = '<span class="ticker-score-muted">--</span>'
            h_score_html = '<span class="ticker-score-muted">--</span>'
            status_text = f"{gameday_str} {gametime_str}".strip() or "UPCOMING"

        slot_html = render_slot_badge_html(slot_code)
        spread_lbl = f"{home_tm} {spread_v:+.1f}" if pd.notna(spread_v) else "Line TBD"
        ou_lbl = f"O/U {total_v:.1f}" if pd.notna(total_v) else ""
        card_cls = "ticker-card-active" if is_selected else "ticker-card"

        with cols[idx]:
            render_html(
                f"""
                <div class="nfl-ticker-marker {card_cls}">
                    <div class="ticker-top-bar">
                        <span>{status_text}</span>
                        {slot_html}
                    </div>
                    <div class="ticker-matchup-header">
                        {away_tm} vs. {home_tm}
                    </div>
                    <div class="ticker-team-row">
                        <span class="ticker-team-left">
                            <img src="{away_logo}" width="17" height="17" onerror="this.style.display='none'">
                            {away_tm} (A)
                        </span>
                        {a_score_html}
                    </div>
                    <div class="ticker-team-row">
                        <span class="ticker-team-left">
                            <img src="{home_logo}" width="17" height="17" onerror="this.style.display='none'">
                            {home_tm} (H)
                        </span>
                        {h_score_html}
                    </div>
                    <div class="ticker-footer">
                        <span>{spread_lbl}</span>
                        <span>{ou_lbl}</span>
                    </div>
                </div>
                """
            )
            btn_label = (
                f"● [ACTIVE: {away_tm} vs {home_tm}]"
                if is_selected
                else f"SELECT {away_tm} vs {home_tm}"
            )
            if st.button(
                btn_label,
                key=f"ticker_btn_{game_id}_{idx}",
                type="primary" if is_selected else "secondary",
                use_container_width=True,
            ):
                st.session_state["selected_game"] = game_id
                st.session_state["selected_game_idx"] = idx
                st.rerun()


def get_default_nfl_week_index(schedule_df: pd.DataFrame, available_weeks: list[int]) -> int:
    """
    Calculates the current active NFL week dynamically based on today's date
    or the first week with unplayed games so the app opens on the active slate.
    """
    if schedule_df.empty or not available_weeks:
        return 0

    today = pd.Timestamp.now().normalize()

    if "gameday" in schedule_df.columns:
        temp = schedule_df.copy()
        temp["parsed_date"] = pd.to_datetime(temp["gameday"], errors="coerce")
        valid_dates = temp.dropna(subset=["parsed_date", "week"])

        if not valid_dates.empty:
            upcoming = valid_dates[valid_dates["parsed_date"] >= (today - pd.Timedelta(days=1))]
            if not upcoming.empty:
                target_wk = int(upcoming.sort_values("parsed_date").iloc[0]["week"])
                if target_wk in available_weeks:
                    return available_weeks.index(target_wk)

            max_date = valid_dates["parsed_date"].max()
            if today > max_date:
                return len(available_weeks) - 1

    if "home_score" in schedule_df.columns:
        unplayed = schedule_df[schedule_df["home_score"].isna()]
        if not unplayed.empty:
            first_unplayed_wk = int(unplayed["week"].dropna().min())
            if first_unplayed_wk in available_weeks:
                return available_weeks.index(first_unplayed_wk)

    return 0


def evaluate_player_streak_badge(
    season_avg: float, l3_avg: float, is_negative_stat: bool = False
) -> tuple[str, str]:
    """
    Evaluates a player's Last 3 Games (L3) output against their season baseline
    using clean colored dot indicators.
    """
    diff = l3_avg - season_avg
    rel_pct = (diff / season_avg * 100.0) if season_avg > 0.25 else (diff * 100.0)

    if is_negative_stat:
        if diff >= 0.35:
            return (
                f'<span class="badge-bad">● [TURNOVER SPIKE: L3 {l3_avg:.2f}/g vs {season_avg:.2f} Avg]</span>',
                f"{diff:+.2f} vs Season Avg",
            )
        if diff <= -0.25:
            return (
                f'<span class="badge-elite">● [CLEAN POCKET: L3 {l3_avg:.2f}/g vs {season_avg:.2f} Avg]</span>',
                f"{diff:+.2f} vs Season Avg",
            )
        return (
            f'<span class="badge-mid">● [STEADY RATE: L3 {l3_avg:.2f}/g]</span>',
            f"{diff:+.2f} vs Season Avg",
        )

    if rel_pct >= 15.0 or (season_avg < 1.5 and diff >= 0.35):
        return (
            f'<span class="badge-hot">● [HOT STREAK: L3 Avg {l3_avg:.1f} vs {season_avg:.1f} Season]</span>',
            f"{diff:+.1f} L3 Surge ({rel_pct:+.0f}%)",
        )
    if rel_pct <= -15.0 or (season_avg < 1.5 and diff <= -0.35):
        return (
            f'<span class="badge-cold">● [COLD STREAK: L3 Avg {l3_avg:.1f} vs {season_avg:.1f} Season]</span>',
            f"{diff:+.1f} L3 Dip ({rel_pct:+.0f}%)",
        )
    return (
        f'<span class="badge-sage">● [STEADY FORM: L3 Avg {l3_avg:.1f} vs {season_avg:.1f} Season]</span>',
        f"{diff:+.1f} vs Season Avg",
    )


# -----------------------------------------------------------------------------
# 2. DATA INGESTION (PURE PANDAS READ_CSV + @ST.CACHE_DATA)
# -----------------------------------------------------------------------------
@st.cache_data(ttl=3600)
def load_master_games_csv() -> pd.DataFrame:
    """Loads the complete nflverse historical games.csv master file."""
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

    if not df.empty:
        if "game_id" not in df.columns:
            df["game_id"] = (
                df["season"].astype(str)
                + "_"
                + df["week"].astype(str)
                + "_"
                + df["away_team"].astype(str)
                + "_"
                + df["home_team"].astype(str)
            )
        df["broadcast_slot"] = df.apply(classify_primetime_code, axis=1)
        df["away_logo"] = df["away_team"].apply(get_team_logo_url)
        df["home_logo"] = df["home_team"].apply(get_team_logo_url)
        df["away_label"] = df["away_team"].astype(str) + " (A)"
        df["home_label"] = df["home_team"].astype(str) + " (H)"

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
# 3. ANALYTICS, 1-ON-1 CB vs WR MISMATCH, 5-YR H2H, ROSTER & BACKTEST ENGINES
# -----------------------------------------------------------------------------
def get_five_year_h2h_history(
    master_df: pd.DataFrame, away_tm: str, home_tm: str, current_season: int
) -> pd.DataFrame:
    """
    Filters the master nflverse schedule to the dedicated 5-year matchup window
    (current_season - 5 through current_season) between the selected teams.
    """
    if master_df.empty or "season" not in master_df.columns:
        return pd.DataFrame()

    min_season = current_season - 5
    h2h = master_df[
        (master_df["season"] >= min_season)
        & (master_df["season"] <= current_season)
        & (
            ((master_df["home_team"] == home_tm) & (master_df["away_team"] == away_tm))
            | ((master_df["home_team"] == away_tm) & (master_df["away_team"] == home_tm))
        )
        & master_df["home_score"].notna()
        & master_df["away_score"].notna()
    ].copy()

    if h2h.empty:
        return pd.DataFrame()

    h2h = h2h.sort_values(by=["season", "week"], ascending=[False, False])

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
    including Anytime TD, Receiving TDs, Interceptions (INT), and yardage/reception props.
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

    if "interceptions" not in sub.columns and "passing_interceptions" in sub.columns:
        sub["interceptions"] = sub["passing_interceptions"]

    stat_cols = [
        "passing_yards",
        "passing_tds",
        "interceptions",
        "completions",
        "attempts",
        "rushing_yards",
        "rushing_tds",
        "carries",
        "receiving_yards",
        "receiving_tds",
        "receptions",
        "targets",
        "receiving_air_yards",
        "special_teams_tds",
    ]
    for c in stat_cols:
        if c not in sub.columns:
            sub[c] = 0.0
        sub[c] = pd.to_numeric(sub[c], errors="coerce").fillna(0.0)

    sub["scrimmage_yards"] = sub["rushing_yards"] + sub["receiving_yards"]
    sub["anytime_td"] = sub["rushing_tds"] + sub["receiving_tds"] + sub["special_teams_tds"]
    sub["touches"] = sub["carries"] + sub["receptions"]
    sub["week"] = pd.to_numeric(sub.get("week", 1), errors="coerce").fillna(1).astype(int)
    sub["game_tag"] = "Wk " + sub["week"].astype(str) + " vs " + sub["opp_label"]

    return sub.sort_values(by=["week"])


def aggregate_team_skill_usage(player_df: pd.DataFrame, teams: list[str]) -> pd.DataFrame:
    """Aggregates seasonal player usage (Target Share, Rush Share, Air Yards, Touches, EPA) for selected teams."""
    if player_df.empty or "team" not in player_df.columns:
        return pd.DataFrame()

    sub = player_df[player_df["team"].isin(teams)].copy()
    if sub.empty:
        return pd.DataFrame()

    if "interceptions" not in sub.columns and "passing_interceptions" in sub.columns:
        sub["interceptions"] = sub["passing_interceptions"]

    for col in [
        "targets",
        "receptions",
        "receiving_yards",
        "receiving_tds",
        "receiving_air_yards",
        "receiving_epa",
        "carries",
        "rushing_yards",
        "rushing_tds",
        "rushing_epa",
        "passing_yards",
        "passing_tds",
        "interceptions",
        "passing_epa",
        "target_share",
        "air_yards_share",
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
            rec_tds=("receiving_tds", "sum"),
            air_yards=("receiving_air_yards", "sum"),
            rec_epa=("receiving_epa", "sum"),
            carries=("carries", "sum"),
            rush_yards=("rushing_yards", "sum"),
            rush_tds=("rushing_tds", "sum"),
            rush_epa=("rushing_epa", "sum"),
            pass_yards=("passing_yards", "sum"),
            pass_tds=("passing_tds", "sum"),
            ints=("interceptions", "sum"),
            pass_epa=("passing_epa", "sum"),
            avg_target_share=("target_share", "mean"),
            avg_air_share=("air_yards_share", "mean"),
        )
        .rename(columns={name_col: "player_name", pos_col: "position", id_col: "player_id"})
    )

    team_totals = grouped.groupby("team")[["targets", "carries", "air_yards"]].transform("sum")
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
    grouped["calc_air_share"] = np.where(
        team_totals["air_yards"] > 0,
        grouped["air_yards"] / team_totals["air_yards"],
        grouped["avg_air_share"],
    )
    grouped["touches"] = grouped["carries"] + grouped["receptions"]
    grouped["scrimmage_yards"] = grouped["rush_yards"] + grouped["rec_yards"]
    grouped["total_tds"] = grouped["rush_tds"] + grouped["rec_tds"]
    grouped["total_epa"] = grouped["rec_epa"] + grouped["rush_epa"] + grouped["pass_epa"]
    return grouped


def build_cb_wr_matchup_battles(
    usage_df: pd.DataFrame,
    player_df: pd.DataFrame,
    snaps_df: pd.DataFrame,
    inj_df: pd.DataFrame,
    eff_df: pd.DataFrame,
    off_tm: str,
    def_tm: str,
) -> list[dict]:
    """
    Automatically calculates and surfaces top 1-on-1 Wide Receiver vs. Cornerback
    individual battles for (off_tm WRs vs def_tm CBs).
    Factors in L4 receiving streaks, defensive pass EPA rank, and CB injuries.
    """
    if usage_df.empty:
        return []

    tm_wrs = usage_df[
        (usage_df["team"] == off_tm)
        & (usage_df["position"].astype(str).str.upper().isin(["WR"]))
    ].sort_values(by=["calc_target_share", "air_yards"], ascending=False)

    if len(tm_wrs) < 2:
        tm_wrs = usage_df[
            (usage_df["team"] == off_tm)
            & (usage_df["position"].astype(str).str.upper().isin(["WR", "TE"]))
        ].sort_values(by=["calc_target_share", "air_yards"], ascending=False)

    top_wrs = tm_wrs.head(3).copy()
    if top_wrs.empty:
        return []

    wr_streaks = {}
    if not player_df.empty and "team" in player_df.columns:
        p_sub = player_df[player_df["team"] == off_tm].copy()
        name_col = "player_display_name" if "player_display_name" in p_sub.columns else "player_name"
        if name_col in p_sub.columns and "receiving_yards" in p_sub.columns:
            p_sub["receiving_yards"] = pd.to_numeric(p_sub["receiving_yards"], errors="coerce").fillna(0.0)
            p_sub["week_num"] = pd.to_numeric(p_sub.get("week", 1), errors="coerce").fillna(1)
            for p_name, grp in p_sub.groupby(name_col):
                grp_sorted = grp.sort_values("week_num")
                s_avg = float(grp_sorted["receiving_yards"].mean())
                l4_avg = float(grp_sorted.tail(4)["receiving_yards"].mean())
                diff_yds = l4_avg - s_avg
                rel_pct = (diff_yds / s_avg * 100.0) if s_avg > 10.0 else 0.0
                if rel_pct >= 18.0 or diff_yds >= 15.0:
                    wr_streaks[str(p_name).strip().lower()] = ("HOT", l4_avg, s_avg, rel_pct)
                elif rel_pct <= -18.0 or diff_yds <= -15.0:
                    wr_streaks[str(p_name).strip().lower()] = ("COLD", l4_avg, s_avg, rel_pct)
                else:
                    wr_streaks[str(p_name).strip().lower()] = ("STEADY", l4_avg, s_avg, rel_pct)

    cb_roster = pd.DataFrame()
    if not snaps_df.empty and {"player", "team", "position", "defense_pct"}.issubset(snaps_df.columns):
        s_def = snaps_df[
            (snaps_df["team"] == def_tm)
            & (snaps_df["position"].astype(str).str.upper().isin(["CB", "DB", "FS", "SS", "S"]))
        ].copy()
        s_def["defense_pct"] = pd.to_numeric(s_def["defense_pct"], errors="coerce").fillna(0.0)
        s_def["pos_upper"] = s_def["position"].astype(str).str.upper().str.strip()
        s_def["is_cb"] = np.where(s_def["pos_upper"] == "CB", 1, 0)
        cb_roster = (
            s_def.groupby(["player", "pos_upper", "is_cb"], as_index=False)
            .agg(def_snap_share=("defense_pct", "mean"), games=("defense_pct", "count"))
            .sort_values(by=["is_cb", "def_snap_share"], ascending=[False, False])
        )
        cb_roster["clean_name"] = cb_roster["player"].astype(str).str.strip().str.lower()

    sec_inj_map = {}
    if not inj_df.empty and "team" in inj_df.columns:
        d_inj = inj_df[inj_df["team"] == def_tm].copy()
        for _, r_i in d_inj.iterrows():
            c_nm = str(r_i.get("player_display", "")).strip().lower()
            st_str = str(r_i.get("report_status", "")).strip().upper()
            inj_type = str(r_i.get("primary_injury", "Injury")).strip()
            sec_inj_map[c_nm] = (st_str, inj_type)

    active_cbs = []
    missing_starting_cbs = []

    if not cb_roster.empty:
        for _, cb_row in cb_roster.iterrows():
            c_nm = cb_row["clean_name"]
            snap_sh = float(cb_row["def_snap_share"])
            p_disp = cb_row["player"]
            pos_u = cb_row["pos_upper"]
            inj_status, inj_desc = sec_inj_map.get(c_nm, ("ACTIVE", ""))

            if inj_status in ["OUT", "IR", "PUP", "DOUBTFUL"] and snap_sh >= 0.50:
                missing_starting_cbs.append(
                    {
                        "name": p_disp,
                        "status": inj_status,
                        "snap_pct": snap_sh * 100.0,
                        "injury": inj_desc,
                    }
                )
            else:
                active_cbs.append(
                    {
                        "name": p_disp,
                        "pos": pos_u,
                        "snap_pct": snap_sh * 100.0,
                        "status": inj_status,
                        "injury": inj_desc,
                        "is_backup_elevated": snap_sh < 0.52,
                    }
                )

    while len(active_cbs) < 3:
        slot_num = len(active_cbs) + 1
        active_cbs.append(
            {
                "name": f"{def_tm} CB{slot_num} Rotation",
                "pos": "CB",
                "snap_pct": 55.0,
                "status": "ACTIVE",
                "injury": "",
                "is_backup_elevated": False,
            }
        )

    def_pass_rk = int(eff_df.loc[def_tm, "def_pass_epa_rank"]) if def_tm in eff_df.index else 16
    def_pass_epa = float(eff_df.loc[def_tm, "def_pass_epa"]) if def_tm in eff_df.index else 0.0

    alignments = ["Alpha Perimeter (X)", "Flanker / Field (Z)", "Slot / Motion (Y)"]
    battles = []

    for idx, (_, wr_row) in enumerate(top_wrs.iterrows()):
        cb_assigned = active_cbs[min(idx, len(active_cbs) - 1)]
        wr_name = wr_row["player_name"]
        wr_clean = str(wr_name).strip().lower()
        wr_tgt_sh = float(wr_row["calc_target_share"]) * 100.0
        wr_air_sh = float(wr_row["calc_air_share"]) * 100.0
        wr_epa = float(wr_row["rec_epa"])
        wr_games = max(1, int(wr_row["games"]))
        wr_ypg = float(wr_row["rec_yards"]) / wr_games

        streak_type, l4_val, s_val, rel_pct = wr_streaks.get(
            wr_clean, ("STEADY", wr_ypg, wr_ypg, 0.0)
        )

        score = 50.0
        if wr_tgt_sh >= 24.0:
            score += 14.0
        elif wr_tgt_sh >= 18.0:
            score += 8.0

        if def_pass_rk >= 25:
            score += 18.0
        elif def_pass_rk >= 20:
            score += 10.0
        elif def_pass_rk <= 5:
            score -= 16.0
        elif def_pass_rk <= 10:
            score -= 8.0

        if streak_type == "HOT":
            score += 10.0
        elif streak_type == "COLD":
            score -= 8.0

        cb_trigger_notes = []
        if missing_starting_cbs and idx < len(missing_starting_cbs):
            out_cb = missing_starting_cbs[idx]
            score += 18.0
            cb_trigger_notes.append(
                f"Primary {def_tm} starter {out_cb['name']} ({out_cb['snap_pct']:.0f}% snaps) is [{out_cb['status']}]; "
                f"{cb_assigned['name']} forced into elevated coverage assignment."
            )
        elif missing_starting_cbs:
            out_cb = missing_starting_cbs[0]
            score += 10.0
            cb_trigger_notes.append(
                f"Secondary rotation shifted due to {out_cb['name']} [{out_cb['status']}]."
            )

        if cb_assigned["status"] == "QUESTIONABLE":
            score += 9.0
            cb_trigger_notes.append(
                f"Assigned cover man {cb_assigned['name']} is [QUESTIONABLE] ({cb_assigned['injury']})."
            )
        elif cb_assigned["is_backup_elevated"]:
            score += 8.0
            cb_trigger_notes.append(
                f"Matched against sub-package/backup DB {cb_assigned['name']} ({cb_assigned['snap_pct']:.0f}% snap share)."
            )

        if score >= 74.0:
            tier_badge = '<span class="badge-elite">● [ELITE MISMATCH]</span>'
            tier_plain = "[ELITE MISMATCH]"
            card_style = "terminal-card-elite"
        elif score >= 61.0:
            tier_badge = '<span class="badge-sage">● [ADVANTAGE WR]</span>'
            tier_plain = "[ADVANTAGE WR]"
            card_style = "terminal-card"
        elif score <= 38.0:
            tier_badge = '<span class="badge-bad">● [CB LOCKDOWN SPOT]</span>'
            tier_plain = "[CB LOCKDOWN SPOT]"
            card_style = "terminal-card-vuln"
        else:
            tier_badge = '<span class="badge-mid">● [NEUTRAL BATTLE]</span>'
            tier_plain = "[NEUTRAL BATTLE]"
            card_style = "terminal-card"

        if streak_type == "HOT":
            wr_streak_badge = f'<span class="badge-hot">● [WR HOT L4: {l4_val:.1f} YPG ({rel_pct:+.0f}%)]</span>'
        elif streak_type == "COLD":
            wr_streak_badge = f'<span class="badge-cold">● [WR COLD L4: {l4_val:.1f} YPG ({rel_pct:+.0f}%)]</span>'
        else:
            wr_streak_badge = f'<span class="badge-mid">● [WR L4: {l4_val:.1f} YPG]</span>'

        if missing_starting_cbs and idx == 0:
            cb_status_badge = '<span class="badge-bad">● [BACKUP CB ELEVATED]</span>'
        elif cb_assigned["status"] == "QUESTIONABLE":
            cb_status_badge = '<span class="badge-amber">● [CB QUESTIONABLE]</span>'
        elif cb_assigned["is_backup_elevated"]:
            cb_status_badge = '<span class="badge-amber">● [ROTATIONAL DB]</span>'
        elif def_pass_rk <= 5:
            cb_status_badge = '<span class="badge-bad">● [SHUTDOWN COVERAGE]</span>'
        else:
            cb_status_badge = f'<span class="badge-mid">● [{cb_assigned["snap_pct"]:.0f}% DEF SNAPS]</span>'

        if not cb_trigger_notes:
            if score >= 70.0:
                cb_trigger_notes.append(
                    f"High-volume alpha target ({wr_tgt_sh:.1f}% share) attacking #{def_pass_rk} {def_tm} pass defense ({def_pass_epa:+.3f} EPA)."
                )
            elif score <= 38.0:
                cb_trigger_notes.append(
                    f"Shadowed by #{def_pass_rk} {def_tm} secondary allowing {def_pass_epa:+.3f} Pass EPA/play."
                )
            else:
                cb_trigger_notes.append(
                    f"Head-to-head perimeter battle vs {cb_assigned['name']} ({cb_assigned['snap_pct']:.0f}% snaps)."
                )

        battles.append(
            {
                "off_tm": off_tm,
                "def_tm": def_tm,
                "alignment": alignments[min(idx, 2)],
                "wr_name": wr_name,
                "wr_tgt_sh": wr_tgt_sh,
                "wr_air_sh": wr_air_sh,
                "wr_ypg": wr_ypg,
                "wr_l4_ypg": l4_val,
                "wr_epa": wr_epa,
                "wr_streak_badge": wr_streak_badge,
                "cb_name": cb_assigned["name"],
                "cb_pos": cb_assigned["pos"],
                "cb_snap_pct": cb_assigned["snap_pct"],
                "cb_status_badge": cb_status_badge,
                "def_pass_rk": def_pass_rk,
                "tier_badge": tier_badge,
                "tier_plain": tier_plain,
                "card_style": card_style,
                "mismatch_score": round(score, 1),
                "trigger_note": " ".join(cb_trigger_notes),
            }
        )

    return battles


def classify_unit_side(row: pd.Series) -> str:
    """Classifies a roster player into Offense, Defense, or Special Teams based on position and snap splits."""
    pos = str(row.get("position", "UNK")).strip().upper()
    if pos in OFFENSE_POSITIONS:
        return "Offense"
    if pos in DEFENSE_POSITIONS:
        return "Defense"
    if pos in SPECIAL_TEAMS_POSITIONS:
        return "Special Teams"

    off_s = float(row.get("off_snaps", 0.0))
    def_s = float(row.get("def_snaps", 0.0))
    if off_s > def_s and off_s > 0:
        return "Offense"
    if def_s > off_s and def_s > 0:
        return "Defense"
    if float(row.get("touches", 0.0)) > 0 or float(row.get("targets", 0.0)) > 0:
        return "Offense"
    return "Special Teams"


def build_roster_usage_table(
    snaps_df: pd.DataFrame, usage_df: pd.DataFrame, teams: list[str]
) -> pd.DataFrame:
    """
    Merges full active roster snap counts (offense/defense/ST snaps & snap %) with
    skill usage metrics (targets, touches, air yards, scrimmage yards, EPA) and unit side.
    """
    roster_base = pd.DataFrame()

    if not snaps_df.empty and {"player", "team"}.issubset(snaps_df.columns):
        s_sub = snaps_df[snaps_df["team"].isin(teams)].copy()
        for c in ["offense_snaps", "offense_pct", "defense_snaps", "defense_pct", "st_snaps", "st_pct"]:
            if c not in s_sub.columns:
                s_sub[c] = 0.0
            s_sub[c] = pd.to_numeric(s_sub[c], errors="coerce").fillna(0.0)

        if "position" not in s_sub.columns:
            s_sub["position"] = "UNK"

        s_sub["clean_name"] = s_sub["player"].astype(str).str.strip().str.lower()
        roster_base = (
            s_sub.groupby(["team", "clean_name", "player", "position"], as_index=False)
            .agg(
                games_active=("week", "nunique") if "week" in s_sub.columns else ("offense_snaps", "count"),
                off_snaps=("offense_snaps", "sum"),
                off_snap_pct=("offense_pct", "mean"),
                def_snaps=("defense_snaps", "sum"),
                def_snap_pct=("defense_pct", "mean"),
                st_snaps=("st_snaps", "sum"),
            )
            .rename(columns={"player": "player_name"})
        )
        roster_base["primary_snap_pct"] = roster_base[["off_snap_pct", "def_snap_pct"]].max(axis=1) * 100.0
        roster_base["total_snaps"] = roster_base["off_snaps"] + roster_base["def_snaps"]

    if not usage_df.empty:
        u_sub = usage_df[usage_df["team"].isin(teams)].copy()
        u_sub["clean_name"] = u_sub["player_name"].astype(str).str.strip().str.lower()

        if not roster_base.empty:
            merged = pd.merge(
                roster_base,
                u_sub[
                    [
                        "team",
                        "clean_name",
                        "player_name",
                        "position",
                        "games",
                        "targets",
                        "receptions",
                        "calc_target_share",
                        "air_yards",
                        "carries",
                        "touches",
                        "scrimmage_yards",
                        "pass_yards",
                        "total_tds",
                        "total_epa",
                    ]
                ],
                on=["team", "clean_name"],
                how="outer",
                suffixes=("_snap", "_stat"),
            )
            merged["player_name"] = merged["player_name_snap"].fillna(merged["player_name_stat"])
            merged["position"] = merged["position_snap"].fillna(merged["position_stat"]).fillna("UNK")
            merged["games_played"] = merged["games_active"].fillna(merged["games"]).fillna(1).astype(int)
        else:
            merged = u_sub.copy()
            merged["games_played"] = merged["games"].fillna(1).astype(int)
            merged["total_snaps"] = 0
            merged["off_snaps"] = 0
            merged["def_snaps"] = 0
            merged["primary_snap_pct"] = 0.0
    else:
        merged = roster_base.copy()
        if not merged.empty:
            merged["games_played"] = merged["games_active"].fillna(1).astype(int)

    if merged.empty:
        return pd.DataFrame()

    fill_zero_cols = [
        "total_snaps",
        "off_snaps",
        "def_snaps",
        "primary_snap_pct",
        "targets",
        "receptions",
        "calc_target_share",
        "air_yards",
        "carries",
        "touches",
        "scrimmage_yards",
        "pass_yards",
        "total_tds",
        "total_epa",
    ]
    for c in fill_zero_cols:
        if c not in merged.columns:
            merged[c] = 0.0
        merged[c] = pd.to_numeric(merged[c], errors="coerce").fillna(0.0)

    merged["position"] = merged["position"].astype(str).str.strip().str.upper()
    merged["unit_group"] = merged.apply(classify_unit_side, axis=1)
    merged["team_logo"] = merged["team"].apply(get_team_logo_url)
    merged["target_share_pct"] = (merged["calc_target_share"] * 100.0).round(1)
    merged["primary_snap_pct"] = merged["primary_snap_pct"].round(1)
    merged["total_epa"] = merged["total_epa"].round(2)

    return merged.sort_values(by=["primary_snap_pct", "touches", "targets"], ascending=False)


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

    roles, epa_penalties, impact_units, is_anchor_flags = [], [], [], []

    for _, row in team_inj.iterrows():
        pos = str(row.get("position", "UNK")).upper().strip()
        snap = float(row["snap_share"])
        tgt = float(row["calc_target_share"])
        status_str = str(row["report_status"]).upper().strip()

        is_anchor = (snap >= 0.65) or (tgt >= 0.18) or (pos == "QB" and snap >= 0.40)
        is_anchor_flags.append(bool(is_anchor))

        if is_anchor:
            if pos in ["T", "LT", "RT", "G", "C"]:
                roles.append("● [STARTING OL ANCHOR]")
            elif pos == "WR" or tgt >= 0.18:
                roles.append("● [PRIMARY TARGET / WR1]")
            elif pos in ["DE", "EDGE", "DT"]:
                roles.append("● [PRIMARY PASS RUSHER]")
            elif pos in ["CB", "S"]:
                roles.append("● [STARTING COVERAGE ANCHOR]")
            elif pos == "QB":
                roles.append("● [STARTING QUARTERBACK]")
            else:
                roles.append("● [KEY STARTING ANCHOR]")
        elif snap >= 0.35 or tgt >= 0.10:
            roles.append("● [ROTATIONAL CONTRIBUTOR]")
        else:
            roles.append("[DEPTH / SPECIAL TEAMS]")

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
    team_inj["is_anchor"] = is_anchor_flags
    team_inj["est_epa_penalty"] = epa_penalties
    team_inj["unit_side"] = impact_units
    team_inj["primary_injury"] = (
        team_inj["report_primary_injury"].fillna("Undisclosed")
        if "report_primary_injury" in team_inj.columns
        else "Undisclosed"
    )

    return team_inj.sort_values(by=["est_epa_penalty", "snap_share"], ascending=False)


def run_season_backtest(
    schedule_df: pd.DataFrame, eff_df: pd.DataFrame
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Grades all completed games in the selected season where extreme unit mismatches
    (● ELITE vs ● BAD) or rest edges occurred.
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

        # 1. ● ELITE (<=5) vs ● BAD (>=23) Pass Mismatch
        h_pass_elite_mm = (h_eff["off_pass_epa_rank"] <= 5) and (a_eff["def_pass_epa_rank"] >= 23)
        a_pass_elite_mm = (a_eff["off_pass_epa_rank"] <= 5) and (h_eff["def_pass_epa_rank"] >= 23)
        if h_pass_elite_mm != a_pass_elite_mm:
            backed = ht if h_pass_elite_mm else at
            su, ats, push = grade_side(backed)
            records.append(
                {
                    "Week": int(row["week"]),
                    "Matchup": f"{at} @ {ht}",
                    "Category": "● ELITE vs ● BAD Pass Unit",
                    "Backed Team": backed,
                    "Final Score": f"{at} {int(as_)} - {ht} {int(hs)}",
                    "Closing Spread": f"{ht} {-sp:+.1f}",
                    "SU Win": su,
                    "ATS Cover": ats,
                    "Push": push,
                }
            )

        # 2. ● ELITE (<=5) vs ● BAD (>=23) Rush Mismatch
        h_rush_elite_mm = (h_eff["off_rush_epa_rank"] <= 5) and (a_eff["def_rush_epa_rank"] >= 23)
        a_rush_elite_mm = (a_eff["off_rush_epa_rank"] <= 5) and (h_eff["def_rush_epa_rank"] >= 23)
        if h_rush_elite_mm != a_rush_elite_mm:
            backed = ht if h_rush_elite_mm else at
            su, ats, push = grade_side(backed)
            records.append(
                {
                    "Week": int(row["week"]),
                    "Matchup": f"{at} @ {ht}",
                    "Category": "● ELITE vs ● BAD Rush Unit",
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
                    "Category": "● Top-10 Off vs ● Bottom-10 Def",
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
                    "Category": "● Situational Rest Edge (3+ Days)",
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
                    "Category": "● Net EPA Model Edge (>=0.08/play)",
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


# -----------------------------------------------------------------------------
# 4. SIDEBAR CONTROLS & DYNAMIC CURRENT WEEK DEFAULT
# -----------------------------------------------------------------------------
st.sidebar.markdown("## Controls")

backtest_mode = st.sidebar.toggle(
    "Historical Backtest Mode",
    value=False,
    help="Switch between 2024, 2025, and 2026 seasons and grade historical ATS cover rates.",
)

if backtest_mode:
    selected_season = st.sidebar.selectbox("Select NFL Season", [2025, 2024, 2026], index=0)
else:
    selected_season = st.sidebar.selectbox("Select NFL Season", [2026, 2025, 2024], index=0)

with st.spinner(f"Loading {selected_season} nflverse CSV feeds..."):
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
default_week_idx = get_default_nfl_week_index(schedule_df, available_weeks)
selected_week = st.sidebar.selectbox(
    "Select NFL Week (Auto-Synced to Active Week)",
    available_weeks,
    index=default_week_idx,
)

all_teams = sorted(
    pd.concat([schedule_df["home_team"], schedule_df["away_team"]]).dropna().unique()
)
selected_team = st.sidebar.selectbox("Filter by Team (Optional)", ["All Teams"] + all_teams)

only_primetime = st.sidebar.checkbox("Filter Primetime Games Only", value=False)

st.sidebar.divider()
st.sidebar.markdown("### Unit Badge Legend")
render_html(
    f"{render_rank_badge(2)} Top 5 NFL Unit<br>"
    f"{render_rank_badge(14)} Ranks 6–22 Unit<br>"
    f"{render_rank_badge(28)} Bottom 10 Unit (23–32)"
)

st.sidebar.divider()
st.sidebar.markdown("### Active Feeds")
st.sidebar.caption(
    f"- **Season:** `{selected_season}` (Default Week `{available_weeks[default_week_idx]}`)\n"
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
if only_primetime and "broadcast_slot" in week_games.columns:
    week_games = week_games[week_games["broadcast_slot"] != ""].copy()

week_games = week_games.reset_index(drop=True)

if week_games.empty:
    st.warning("No games found for the selected filter combination.")
    st.stop()

# Synchronize st.session_state['selected_game'] (Requirement #3)
valid_game_ids = week_games["game_id"].astype(str).tolist()
if (
    "selected_game" not in st.session_state
    or st.session_state["selected_game"] not in valid_game_ids
):
    st.session_state["selected_game"] = valid_game_ids[0]
    st.session_state["selected_game_idx"] = 0
else:
    st.session_state["selected_game_idx"] = valid_game_ids.index(
        st.session_state["selected_game"]
    )

active_game = week_games.iloc[st.session_state["selected_game_idx"]]

# -----------------------------------------------------------------------------
# 5. PINNED TOP VIEW: HORIZONTAL SCROLLABLE NFL GAME TICKER (Reqs #1-#3)
# -----------------------------------------------------------------------------
mode_tag = (
    f'<span class="badge-amber">● [BACKTEST MODE: {selected_season}]</span>'
    if backtest_mode or selected_season < 2026
    else '<span class="badge-elite">● [LIVE 2026 SEASON]</span>'
)

st.title("Football Edger")
render_html(
    f"{mode_tag} "
    f"{render_rank_badge(1, 'Top-5')} "
    f"{render_rank_badge(12, 'Ranks 6-22')} "
    f"{render_rank_badge(28, 'Bottom-10')} "
    '<span class="badge-sage">● Scroll the horizontal game strip below and click any matchup card to load its analytics</span>'
)

ticker_head_col1, ticker_head_col2 = st.columns([1.4, 1])
with ticker_head_col1:
    st.subheader(f"{selected_season} Week {selected_week} — Weekly Game Ticker")
with ticker_head_col2:
    render_html(
        f'<div style="text-align:right; padding-top:10px;">'
        f'<span class="active-lock-pill">● SELECTED GAME: {st.session_state["selected_game"]}</span> '
        f'{render_team_pill(active_game["away_team"], "A")} '
        f'<span style="color:#94A3B8; font-weight:700;">@</span> '
        f'{render_team_pill(active_game["home_team"], "H")}'
        f"</div>"
    )

# Render Pinned Horizontal Scrollable Game Ticker (Replaces Old Schedule Table Entirely)
render_nfl_horizontal_ticker(week_games)

# -----------------------------------------------------------------------------
# 6. DETAIL VIEW: HIGH-PROMINENCE SELECTED MATCHUP SPOTLIGHT
# -----------------------------------------------------------------------------
if eff_df.empty:
    st.info("Efficiency data unavailable for this season.")
    st.stop()

away_tm = active_game["away_team"]
home_tm = active_game["home_team"]
spread_v = active_game.get("home_spread", np.nan)
total_v = active_game.get("total_line", np.nan)
rest_v = active_game.get("rest_edge_home", 0)
roof_str = str(active_game.get("roof", "outdoors")).capitalize()
stadium_str = active_game.get("stadium", "TBD")
slot_str = active_game.get("broadcast_slot", "")
away_pts = active_game.get("away_score", np.nan)
home_pts = active_game.get("home_score", np.nan)

spread_str = f"{home_tm} {spread_v:+.1f}" if pd.notna(spread_v) else "Spread TBD"
total_str = f"O/U {total_v:.1f}" if pd.notna(total_v) else "Total TBD"
final_score_badge = (
    f'<span class="badge-amber">● [FINAL: {away_tm} {int(away_pts)} - {home_tm} {int(home_pts)}]</span>'
    if pd.notna(away_pts) and pd.notna(home_pts)
    else ""
)
slot_badge = f'<span class="badge-amber">● {slot_str}</span>' if slot_str else ""

if pd.notna(rest_v) and rest_v > 0:
    rest_badge = f'<span class="badge-elite">● [REST EDGE: {home_tm} +{int(rest_v)}d]</span>'
elif pd.notna(rest_v) and rest_v < 0:
    rest_badge = f'<span class="badge-elite">● [REST EDGE: {away_tm} +{int(abs(rest_v))}d]</span>'
else:
    rest_badge = '<span class="badge-mid">● [EVEN REST: 0d]</span>'

a_eff = eff_df.loc[away_tm] if away_tm in eff_df.index else None
h_eff = eff_df.loc[home_tm] if home_tm in eff_df.index else None
usage_matchup = aggregate_team_skill_usage(player_df, [away_tm, home_tm])
inj_matchup = build_injury_impact_report(
    injuries_df, snaps_df, usage_matchup, [away_tm, home_tm], selected_week
)
h2h_5yr = get_five_year_h2h_history(master_games_df, away_tm, home_tm, selected_season)


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
a_def_badge = render_rank_badge(int(a_eff["def_epa_rank"]), f"{away_tm} Def") if a_eff is not None else ""
h_ovr_badge = render_rank_badge(int(h_eff["off_epa_rank"]), f"{home_tm} Off") if h_eff is not None else ""
h_def_badge = render_rank_badge(int(h_eff["def_epa_rank"]), f"{home_tm} Def") if h_eff is not None else ""

render_html(
    f"""
    <div class="active-game-spotlight">
        <div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:14px;">
            <div>
                <div style="margin-bottom:8px;">
                    <span class="active-lock-pill">● ACTIVE MATCHUP SELECTED ({st.session_state["selected_game_idx"] + 1} OF {len(week_games)})</span>
                    <span class="metric-subtext" style="margin-left:8px;">{selected_season} WEEK {selected_week} • {stadium_str} ({roof_str})</span>
                </div>
                <div style="display:flex; align-items:center; flex-wrap:wrap; gap:10px; margin:8px 0;">
                    {render_team_pill(away_tm, "A", large=True)}
                    <span style="font-size:1.35rem; font-weight:800; color:#64748B; font-family:monospace;">AT</span>
                    {render_team_pill(home_tm, "H", large=True)}
                </div>
                <div style="margin-top:8px;">
                    {a_ovr_badge} {a_def_badge}
                    <span style="color:#475569; margin:0 6px;">|</span>
                    {h_ovr_badge} {h_def_badge}
                </div>
            </div>
            <div style="display:flex; flex-direction:column; align-items:flex-end; gap:8px;">
                <div>{slot_badge} {final_score_badge}</div>
                <div>
                    <span class="badge-sage">[SPREAD: {spread_str}]</span>
                    <span class="badge-sage">[TOTAL: {total_str}]</span>
                    {rest_badge}
                </div>
            </div>
        </div>
    </div>
    """
)

# 6 Main Sub-Tabs (Strict No-Emoji Labels)
subtab_brief, subtab_players, subtab_trench, subtab_props, subtab_roster, subtab_backtest = st.tabs(
    [
        "Brief Summary & 5-Yr H2H",
        "Player Mismatches & Injuries",
        "Trench & Air Efficiency",
        "Player Prop Trend Explorer",
        "Team Roster & Usage Explorer",
        "Backtest Performance",
    ]
)

# =============================================================================
# SUB-TAB 1: BRIEF SUMMARY & TACTICAL GAME SCRIPT
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
            total_anchors_out = int(inj_matchup["is_anchor"].sum()) if not inj_matchup.empty else 0
            st.metric(
                "Flagged Starters on Report",
                f"{total_anchors_out} Anchors",
                delta=f"Away -{away_off_pen + away_def_pen:.2f} | Home -{home_off_pen + home_def_pen:.2f} EPA",
                delta_color="inverse" if total_anchors_out > 0 else "normal",
            )
        with k4:
            if not h2h_5yr.empty:
                h_wins = int((h2h_5yr["SU Winner"] == home_tm).sum())
                a_wins = int((h2h_5yr["SU Winner"] == away_tm).sum())
                last_res = h2h_5yr.iloc[0]["Matchup & Final"]
                st.metric(
                    f"5-Yr H2H ({selected_season - 5}–{selected_season})",
                    f"{home_tm} {h_wins} - {away_tm} {a_wins}",
                    delta=f"Last: {last_res}",
                    delta_color="off",
                )
            else:
                st.metric(
                    f"5-Yr H2H ({selected_season - 5}–{selected_season})",
                    "0 Meetings",
                    delta="No games in 5-yr window",
                    delta_color="off",
                )

        col_brief_left, col_brief_right = st.columns([1.2, 1])

        with col_brief_left:
            a_pass_rk, a_rush_rk = int(a_eff["off_pass_epa_rank"]), int(a_eff["off_rush_epa_rank"])
            h_pdef_rk, h_rdef_rk = int(h_eff["def_pass_epa_rank"]), int(h_eff["def_rush_epa_rank"])

            h_pass_rk, h_rush_rk = int(h_eff["off_pass_epa_rank"]), int(h_eff["off_rush_epa_rank"])
            a_pdef_rk, a_rdef_rk = int(a_eff["def_pass_epa_rank"]), int(a_eff["def_rush_epa_rank"])

            away_air_gap = h_pdef_rk - a_pass_rk
            away_grd_gap = h_rdef_rk - a_rush_rk
            if away_air_gap >= away_grd_gap:
                away_lever_tag = (
                    f'<span class="badge-elite">● [AIR EDGE: {away_air_gap:+d} RANK GAP]</span>'
                    if away_air_gap >= 6
                    else f'<span class="badge-sage">● [LEAN PASS: {a_eff["off_pass_epa"]:+.2f} EPA]</span>'
                )
            else:
                away_lever_tag = (
                    f'<span class="badge-elite">● [GROUND EDGE: {away_grd_gap:+d} RANK GAP]</span>'
                    if away_grd_gap >= 6
                    else f'<span class="badge-sage">● [LEAN RUSH: {a_eff["off_rush_epa"]:+.2f} EPA]</span>'
                )

            home_air_gap = a_pdef_rk - h_pass_rk
            home_grd_gap = a_rdef_rk - h_rush_rk
            if home_air_gap >= home_grd_gap:
                home_lever_tag = (
                    f'<span class="badge-elite">● [AIR EDGE: {home_air_gap:+d} RANK GAP]</span>'
                    if home_air_gap >= 6
                    else f'<span class="badge-sage">● [LEAN PASS: {h_eff["off_pass_epa"]:+.2f} EPA]</span>'
                )
            else:
                home_lever_tag = (
                    f'<span class="badge-elite">● [GROUND EDGE: {home_grd_gap:+d} RANK GAP]</span>'
                    if home_grd_gap >= 6
                    else f'<span class="badge-sage">● [LEAN RUSH: {h_eff["off_rush_epa"]:+.2f} EPA]</span>'
                )

            if pd.notna(rest_v) and abs(rest_v) >= 1:
                adv_rest_tm = home_tm if rest_v > 0 else away_tm
                rest_cell_html = (
                    f'{render_inline_logo(adv_rest_tm, 16)}<b>+{int(abs(rest_v))}d Rest Advantage</b> '
                    f'<span class="metric-subtext">• {roof_str}</span>'
                )
            else:
                rest_cell_html = (
                    f'<span class="badge-mid">● [EVEN REST: 0d]</span> '
                    f'<span class="metric-subtext">{stadium_str} ({roof_str})</span>'
                )

            if not inj_matchup.empty and int(inj_matchup["is_anchor"].sum()) > 0:
                top_inj = inj_matchup[inj_matchup["is_anchor"]].iloc[0]
                inj_cell_html = (
                    f'{render_inline_logo(top_inj["team"], 16)}<b>{top_inj["player_display"]}</b> '
                    f'({top_inj.get("position", "POS")}) {render_injury_badge(top_inj["report_status"])} '
                    f'<span style="color:#FF4D6D; font-family:monospace; font-weight:700;">-{top_inj["est_epa_penalty"]:.3f} EPA</span>'
                )
            else:
                inj_cell_html = '<span class="badge-elite">● [FULL STRENGTH]</span> <span class="metric-subtext">0 Anchor Absences</span>'

            render_html(
                f"""
                <div class="terminal-card-elite">
                    <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:12px;">
                        <h4 style="margin:0; color:#00FF87;">Brief Summary — Unit Tier Matrix</h4>
                        <span class="metric-subtext">Offense Tier [EPA] vs Opposing Defense Tier</span>
                    </div>
                    <div class="brief-grid">
                        <div class="unit-pillar">
                            <div class="unit-pillar-header">
                                <span>{render_inline_logo(away_tm, 20)}{away_tm} Possession (A)</span>
                                <span class="metric-subtext">vs {home_tm} Def</span>
                            </div>
                            <div class="unit-tier-row">
                                <span class="unit-tier-label">AIR</span>
                                <span>{render_rank_badge(a_pass_rk, "Off")} <span class="metric-subtext">({a_eff["off_pass_epa"]:+.2f})</span></span>
                                <span class="metric-subtext">vs</span>
                                <span>{render_rank_badge(h_pdef_rk, "Def")}</span>
                            </div>
                            <div class="unit-tier-row">
                                <span class="unit-tier-label">GROUND</span>
                                <span>{render_rank_badge(a_rush_rk, "Off")} <span class="metric-subtext">({a_eff["off_rush_epa"]:+.2f})</span></span>
                                <span class="metric-subtext">vs</span>
                                <span>{render_rank_badge(h_rdef_rk, "Def")}</span>
                            </div>
                            <div class="unit-lever-footer">
                                <span class="metric-subtext">Primary Lever</span>
                                {away_lever_tag}
                            </div>
                        </div>
                        <div class="unit-pillar">
                            <div class="unit-pillar-header">
                                <span>{render_inline_logo(home_tm, 20)}{home_tm} Possession (H)</span>
                                <span class="metric-subtext">vs {away_tm} Def</span>
                            </div>
                            <div class="unit-tier-row">
                                <span class="unit-tier-label">AIR</span>
                                <span>{render_rank_badge(h_pass_rk, "Off")} <span class="metric-subtext">({h_eff["off_pass_epa"]:+.2f})</span></span>
                                <span class="metric-subtext">vs</span>
                                <span>{render_rank_badge(a_pdef_rk, "Def")}</span>
                            </div>
                            <div class="unit-tier-row">
                                <span class="unit-tier-label">GROUND</span>
                                <span>{render_rank_badge(h_rush_rk, "Off")} <span class="metric-subtext">({h_eff["off_rush_epa"]:+.2f})</span></span>
                                <span class="metric-subtext">vs</span>
                                <span>{render_rank_badge(a_rdef_rk, "Def")}</span>
                            </div>
                            <div class="unit-lever-footer">
                                <span class="metric-subtext">Primary Lever</span>
                                {home_lever_tag}
                            </div>
                        </div>
                    </div>
                    <div class="brief-context-strip">
                        <div>
                            <div class="context-cell-title">Rest & Environment</div>
                            <div>{rest_cell_html}</div>
                        </div>
                        <div>
                            <div class="context-cell-title">Top Lineup Absence</div>
                            <div>{inj_cell_html}</div>
                        </div>
                    </div>
                </div>
                """
            )

        with col_brief_right:
            fav_team = home_tm if (pd.notna(spread_v) and spread_v <= 0) else away_tm
            dog_team = away_tm if fav_team == home_tm else home_tm
            fav_sr = (
                h_eff["off_sr"] * 100.0 if fav_team == home_tm else a_eff["off_sr"] * 100.0
            )
            dog_p_rk = (
                int(a_eff["off_pass_epa_rank"]) if dog_team == away_tm else int(h_eff["off_pass_epa_rank"])
            )
            fav_pdef_rk = (
                int(h_eff["def_pass_epa_rank"]) if fav_team == home_tm else int(a_eff["def_pass_epa_rank"])
            )

            if not usage_matchup.empty:
                top_w = usage_matchup.sort_values(by="calc_target_share", ascending=False).iloc[0]
                w_tm = top_w["team"]
                opp_tm = home_tm if w_tm == away_tm else away_tm
                opp_p_rk = int(eff_df.loc[opp_tm, "def_pass_epa_rank"])
                phase2_badge = f'<span class="badge-amber">● [{top_w["calc_target_share"]*100:.1f}% TARGET SHARE]</span>'
                phase2_body = (
                    f"{render_inline_logo(w_tm, 16)}<b>{top_w['player_name']}</b> ({top_w['position']}) "
                    f"featured vs {render_inline_logo(opp_tm, 16)}{render_rank_badge(opp_p_rk, 'Cov')} "
                    f"<span class='metric-subtext'>({int(top_w['targets'])} tgts, {int(top_w['air_yards'])} air yds)</span>"
                )
            else:
                phase2_badge = '<span class="badge-mid">● [BALANCED TARGETS]</span>'
                phase2_body = "Distributed progression reads across primary WRs and TEs."

            render_html(
                f"""
                <div class="terminal-card">
                    <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:12px;">
                        <h4 style="margin:0; color:#7FD1B9;">Game Script Flow — Tactical Timeline</h4>
                        <span class="metric-subtext">3-Phase Projection</span>
                    </div>
                    <div class="tactical-step">
                        <div class="tactical-phase-header">
                            <span class="tactical-phase-tag">PHASE 1 • OPENING SCRIPT & EARLY DOWNS TEMPO</span>
                            <span class="badge-elite">● [{model_lean_team} +{model_edge_mag:.3f} EPA]</span>
                        </div>
                        <div class="tactical-body">
                            {render_inline_logo(fav_team, 16)}<b>{fav_team}</b> dictates early tempo
                            (<b>{fav_sr:.1f}%</b> Success Rate) • Primary script lever: <b>{best_phase_val[0]}</b>
                            (<b>{best_phase_val[1]:+.3f}</b> net delta).
                        </div>
                    </div>
                    <div class="tactical-step">
                        <div class="tactical-phase-header">
                            <span class="tactical-phase-tag">PHASE 2 • FOCAL MISMATCH & TARGET SHARE FOCUS</span>
                            {phase2_badge}
                        </div>
                        <div class="tactical-body">
                            {phase2_body}
                        </div>
                    </div>
                    <div class="tactical-step-last">
                        <div class="tactical-phase-header">
                            <span class="tactical-phase-tag" style="color:#FFB020;">PHASE 3 • SECOND-HALF PIVOT & SCRIPT CONDITION</span>
                            <span class="badge-sage">● [IF {fav_team} LEADS +7]</span>
                        </div>
                        <div class="tactical-body">
                            {render_inline_logo(dog_team, 16)}<b>{dog_team}</b> forced into high-volume dropback script:
                            {render_rank_badge(dog_p_rk, "Pass Off")} vs
                            {render_inline_logo(fav_team, 16)}{render_rank_badge(fav_pdef_rk, "Pass Def")}.
                        </div>
                    </div>
                </div>
                """
            )

        render_html(
            f"<h4 style='margin:14px 0 8px 0;'>"
            f"{render_inline_logo(away_tm, 24)}{away_tm} vs {render_inline_logo(home_tm, 24)}{home_tm} — "
            f"5-Year Matchup History ({selected_season - 5}–{selected_season})</h4>"
        )
        if h2h_5yr.empty:
            st.info(
                f"No completed head-to-head matchups between {away_tm} and {home_tm} during the {selected_season - 5}–{selected_season} window."
            )
        else:
            avg_tot = h2h_5yr["Total Pts"].mean()
            h_su = int((h2h_5yr["SU Winner"] == home_tm).sum())
            a_su = int((h2h_5yr["SU Winner"] == away_tm).sum())

            render_html(
                f"""
                <div class="terminal-card" style="padding:12px; margin-bottom:12px;">
                    <span class="badge-sage">● [5-YR MEETINGS: {len(h2h_5yr)}]</span>
                    <span class="badge-elite">● [{home_tm} SU WINS: {h_su}]</span>
                    <span class="badge-elite">● [{away_tm} SU WINS: {a_su}]</span>
                    <span class="badge-amber">● [AVG COMBINED PTS: {avg_tot:.1f}]</span>
                </div>
                """
            )

            h2h_col_cards, h2h_col_table = st.columns([1, 1.6])
            with h2h_col_cards:
                for _, h_row in h2h_5yr.head(3).iterrows():
                    win_tm = h_row["SU Winner"]
                    badge_w = (
                        f'<span class="badge-elite">{render_inline_logo(win_tm, 14)}● [{win_tm} WON]</span>'
                        if win_tm != "TIE"
                        else '<span class="badge-mid">● [TIE]</span>'
                    )
                    render_html(
                        f"""
                        <div class="terminal-card" style="padding:12px; margin-bottom:8px;">
                            <div style="display:flex; justify-content:space-between; align-items:center;">
                                <b>{int(h_row['season'])} Wk {int(h_row['week'])} ({h_row.get('gameday', '')})</b>
                                {badge_w}
                            </div>
                            <div style="margin-top:6px; font-size:0.95rem;">
                                <b>{h_row['Matchup & Final']}</b>
                            </div>
                            <div class="metric-subtext" style="margin-top:4px;">
                                ATS: <b>{h_row['ATS Result']}</b> | Total Pts: <b>{h_row['Total Pts']}</b>
                            </div>
                        </div>
                        """
                    )

            with h2h_col_table:
                h2h_disp = h2h_5yr[
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
# SUB-TAB 2: PLAYER MISMATCHES & INJURIES (WITH DEDICATED CB vs WR SUB-TAB)
# =============================================================================
with subtab_players:
    pm_subtab_cbwr, pm_subtab_volume, pm_subtab_injuries = st.tabs(
        [
            "1-on-1 CB vs. WR Mismatches",
            "Skill-Player Volume vs. Unit Tiers",
            "Official Weekly Injury Report & EPA Drag",
        ]
    )

    with pm_subtab_cbwr:
        render_html(
            f"<h4 style='margin:0 0 4px 0;'>"
            f"{render_inline_logo(away_tm, 24)}1-on-1 Cornerback vs. Wide Receiver Mismatch Analyzer — "
            f"{away_tm} (A) vs {render_inline_logo(home_tm, 24)}{home_tm} (H)</h4>"
        )
        st.caption(
            "Automatically surfaces top individual WR1/WR2/Slot battles driven by opposing CB defensive snap shares, "
            "secondary injuries (backup CBs elevated into starting roles), and Last-4-Games (L4) hot/cold streaks."
        )

        away_cb_wr_battles = build_cb_wr_matchup_battles(
            usage_matchup, player_df, snaps_df, inj_matchup, eff_df, away_tm, home_tm
        )
        home_cb_wr_battles = build_cb_wr_matchup_battles(
            usage_matchup, player_df, snaps_df, inj_matchup, eff_df, home_tm, away_tm
        )
        all_battles = away_cb_wr_battles + home_cb_wr_battles

        if not all_battles:
            st.info("Insufficient wide receiver or cornerback snap data to project 1-on-1 battles.")
        else:
            elite_battles = [b for b in all_battles if b["mismatch_score"] >= 74.0]
            backup_triggers = [
                b
                for b in all_battles
                if "BACKUP" in b["cb_status_badge"] or "ROTATIONAL" in b["cb_status_badge"]
            ]
            hot_wrs = [b for b in all_battles if "WR HOT" in b["wr_streak_badge"]]
            top_battle = sorted(all_battles, key=lambda x: x["mismatch_score"], reverse=True)[0]

            c_k1, c_k2, c_k3, c_k4 = st.columns(4)
            c_k1.metric(
                "Top 1-on-1 Target Edge",
                f"{top_battle['wr_name']} ({top_battle['off_tm']})",
                delta=f"Index {top_battle['mismatch_score']:.0f}/100 vs {top_battle['cb_name']}",
            )
            c_k2.metric(
                "Flagged [ELITE MISMATCH] Spots",
                f"{len(elite_battles)} Battles",
                delta="Score >= 74/100 Threshold",
            )
            c_k3.metric(
                "Secondary Injury / Backup Triggers",
                f"{len(backup_triggers)} Matchups",
                delta="Backup or Rotational DB Targeted",
            )
            c_k4.metric(
                "Wideouts on L4 Hot Streak",
                f"{len(hot_wrs)} Receivers",
                delta=">= +18% L4 YPG vs Season",
            )

            cb_col1, cb_col2 = st.columns(2)

            for col_ui, (off_tm_i, def_tm_i, role_str, battle_list) in [
                (cb_col1, (away_tm, home_tm, "A", away_cb_wr_battles)),
                (cb_col2, (home_tm, away_tm, "H", home_cb_wr_battles)),
            ]:
                with col_ui:
                    render_html(
                        f'<div style="margin-bottom:10px;">'
                        f'{render_team_pill(off_tm_i, role_str)} <b>Wideouts vs</b> '
                        f'{render_team_pill(def_tm_i)} <b>Cornerbacks</b></div>'
                    )
                    for b in battle_list:
                        render_html(
                            f"""
                            <div class="{b['card_style']}">
                                <div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:6px;">
                                    <span class="metric-subtext">{b['alignment']} • Mismatch Index: <b>{b['mismatch_score']:.0f}/100</b></span>
                                    {b['tier_badge']}
                                </div>
                                <div class="cb-wr-vs-row">
                                    <div>
                                        {render_inline_logo(b['off_tm'], 18)}<b>{b['wr_name']}</b>
                                        <span class="badge-sage">[WR]</span><br>
                                        <span class="metric-subtext">
                                            Tgt Share: <b>{b['wr_tgt_sh']:.1f}%</b> | Air Share: <b>{b['wr_air_sh']:.1f}%</b> | <b>{b['wr_ypg']:.1f} YPG</b>
                                        </span>
                                    </div>
                                    <div style="font-family:monospace; font-weight:800; color:#64748B; padding:0 8px;">VS</div>
                                    <div style="text-align:right;">
                                        {render_inline_logo(b['def_tm'], 18)}<b>{b['cb_name']}</b>
                                        <span class="badge-mid">[{b['cb_pos']}]</span><br>
                                        <span class="metric-subtext">
                                            Def Snaps: <b>{b['cb_snap_pct']:.0f}%</b> | Pass Def: <b>#{b['def_pass_rk']} NFL</b>
                                        </span>
                                    </div>
                                </div>
                                <div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:4px; margin-bottom:6px;">
                                    {b['wr_streak_badge']}
                                    {b['cb_status_badge']}
                                </div>
                                <div class="metric-subtext" style="color:#CBD5E1;">
                                    <b>Trigger:</b> {b['trigger_note']}
                                </div>
                            </div>
                            """
                        )

            battle_table_df = pd.DataFrame(
                [
                    {
                        "Offense": b["off_tm"],
                        "Wide Receiver": b["wr_name"],
                        "Alignment": b["alignment"],
                        "Target %": round(b["wr_tgt_sh"], 1),
                        "Season YPG": round(b["wr_ypg"], 1),
                        "L4 YPG": round(b["wr_l4_ypg"], 1),
                        "Primary Coverage CB": f"{b['cb_name']} ({b['def_tm']})",
                        "CB Snap %": round(b["cb_snap_pct"], 0),
                        "Mismatch Index": b["mismatch_score"],
                        "Callout Tier": b["tier_plain"],
                    }
                    for b in sorted(all_battles, key=lambda x: x["mismatch_score"], reverse=True)
                ]
            )
            st.markdown("##### 1-on-1 CB vs. WR Mismatch Summary Matrix")
            st.dataframe(
                battle_table_df,
                width="stretch",
                hide_index=True,
                column_config={
                    "Target %": st.column_config.NumberColumn("Target %", format="%.1f%%"),
                    "Season YPG": st.column_config.NumberColumn("Season YPG", format="%.1f"),
                    "L4 YPG": st.column_config.NumberColumn("L4 YPG", format="%.1f"),
                    "CB Snap %": st.column_config.NumberColumn("CB Def Snaps", format="%.0f%%"),
                    "Mismatch Index": st.column_config.ProgressColumn(
                        "Mismatch Score", format="%.0f / 100", min_value=0, max_value=100
                    ),
                },
            )

    with pm_subtab_volume:
        render_html(
            f"<h4 style='margin:0 0 4px 0;'>"
            f"{render_inline_logo(away_tm, 22)}{render_inline_logo(home_tm, 22)}"
            f"Overall Skill-Player Volume vs. Unit Tiers ({away_tm} @ {home_tm})</h4>"
        )
        st.caption(
            "Primary offensive skill weapons (WR, RB, TE) cross-referenced against opposing Pass/Rush EPA defensive ranks."
        )

        if usage_matchup.empty or a_eff is None or h_eff is None:
            st.info("Player usage or team efficiency splits unavailable for this matchup.")
        else:
            p_col1, p_col2 = st.columns(2)

            for col_ui, (off_tm_i, def_tm_i, role_str) in [
                (p_col1, (away_tm, home_tm, "A")),
                (p_col2, (home_tm, away_tm, "H")),
            ]:
                with col_ui:
                    render_html(
                        f'<div style="margin-bottom:10px;">'
                        f'{render_team_pill(off_tm_i, role_str)} <b>Playmakers vs</b> '
                        f'{render_team_pill(def_tm_i)} <b>Defense</b></div>'
                    )
                    tm_weapons = usage_matchup[usage_matchup["team"] == off_tm_i].copy()
                    def_pass_rk = int(eff_df.loc[def_tm_i, "def_pass_epa_rank"])
                    def_rush_rk = int(eff_df.loc[def_tm_i, "def_rush_epa_rank"])

                    top_receivers = tm_weapons.sort_values(by="calc_target_share", ascending=False).head(3)
                    top_rusher = (
                        tm_weapons[tm_weapons["position"].isin(["RB", "FB", "QB"])]
                        .sort_values(by="calc_rush_share", ascending=False)
                        .head(1)
                    )
                    featured = pd.concat([top_receivers, top_rusher]).drop_duplicates(subset=["player_name"])

                    for _, w_row in featured.iterrows():
                        is_rec = w_row["calc_target_share"] >= w_row["calc_rush_share"]
                        opp_rk = def_pass_rk if is_rec else def_rush_rk
                        phase_str = f"{def_tm_i} Pass Def" if is_rec else f"{def_tm_i} Rush Def"
                        share_lbl = (
                            f"Target Share: <b>{w_row['calc_target_share']*100:.1f}%</b> ({int(w_row['targets'])} tgts, {int(w_row['air_yards'])} air yds)"
                            if is_rec
                            else f"Rush Share: <b>{w_row['calc_rush_share']*100:.1f}%</b> ({int(w_row['carries'])} att, {int(w_row['touches'])} touches)"
                        )

                        opp_unit_badge = render_rank_badge(opp_rk, f"vs {phase_str}")
                        box_cls = (
                            "terminal-card-elite"
                            if opp_rk >= 23
                            else ("terminal-card-vuln" if opp_rk <= 5 else "terminal-card")
                        )
                        pos_badge = str(w_row.get("position", "POS"))
                        scrim_yds = int(w_row["scrimmage_yards"])

                        render_html(
                            f"""
                            <div class="{box_cls}">
                                <div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap;">
                                    <div>
                                        {render_inline_logo(off_tm_i, 18)}<b>{w_row['player_name']}</b>
                                        <span class="badge-sage">[{pos_badge}]</span>
                                    </div>
                                    <div>{opp_unit_badge}</div>
                                </div>
                                <div class="metric-subtext" style="margin-top:6px;">
                                    {share_lbl} | Total EPA: <b>{w_row['total_epa']:+.1f}</b> |
                                    Scrimmage: <b>{scrim_yds} yds ({int(w_row['total_tds'])} TD)</b>
                                </div>
                            </div>
                            """
                        )

    with pm_subtab_injuries:
        render_html(
            f"<h4 style='margin:0 0 8px 0;'>"
            f"{render_inline_logo(away_tm, 22)}{render_inline_logo(home_tm, 22)}"
            f"Weekly Injuries & Missing Starter EPA Drag ({away_tm} @ {home_tm})</h4>"
        )

        if inj_matchup.empty:
            render_html(
                f"""
                <div class="terminal-card-elite">
                    <span class="badge-elite">● [CLEAN INJURY REPORT]</span>
                    <p style="margin:6px 0 0 0;" class="metric-subtext">
                        No active Out, Doubtful, or Questionable designations found for {away_tm} or {home_tm} in Week {selected_week}.
                    </p>
                </div>
                """
            )
        else:
            col_away_inj, col_home_inj = st.columns(2)

            for col_obj, (tm, role_str) in [(col_away_inj, (away_tm, "A")), (col_home_inj, (home_tm, "H"))]:
                with col_obj:
                    tm_inj = inj_matchup[inj_matchup["team"] == tm].copy()
                    total_off_drop = tm_inj[tm_inj["unit_side"] == "Offense"]["est_epa_penalty"].sum()
                    total_def_drop = tm_inj[tm_inj["unit_side"] == "Defense"]["est_epa_penalty"].sum()
                    anchor_count = int(tm_inj["is_anchor"].sum()) if not tm_inj.empty else 0

                    card_cls = "terminal-card-vuln" if anchor_count > 0 else "terminal-card"
                    badge_cls = "badge-bad" if anchor_count > 0 else "badge-mid"
                    render_html(
                        f"""
                        <div class="{card_cls}">
                            <div style="display:flex; justify-content:space-between; align-items:center;">
                                <h4 style="margin:0;">{render_inline_logo(tm, 22)}{tm} ({role_str}) Injury Impact</h4>
                                <span class="{badge_cls}">● [{anchor_count} ANCHORS FLAGGED]</span>
                            </div>
                            <p style="margin:8px 0 0 0;" class="metric-subtext">
                                Offense EPA Penalty: <b>{-total_off_drop:+.3f}/play</b> |
                                Defense EPA Penalty: <b>+{total_def_drop:.3f}/play allowed</b>
                            </p>
                        </div>
                        """
                    )

                    for _, r_inj in tm_inj.head(6).iterrows():
                        badge_html = render_injury_badge(r_inj["report_status"])
                        snap_pct = r_inj["snap_share"] * 100
                        tgt_pct = r_inj["calc_target_share"] * 100
                        pos_str = str(r_inj.get("position", "POS"))
                        render_html(
                            f"""
                            <div class="terminal-card" style="padding:12px; margin-bottom:8px;">
                                <div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap;">
                                    <div>
                                        {render_inline_logo(tm, 16)}<b>{r_inj['player_display']}</b>
                                        <span class="badge-sage">[{pos_str}]</span>
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

# =============================================================================
# SUB-TAB 3: TRENCH & AIR EFFICIENCY
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
                        "title": f"{render_inline_logo(o_tm, 20)}{o_tm} {phase} Offense Smash Spot (+{d_rk - o_rk} Rank Edge)",
                        "detail": f"{o_tm} generates {o_val:+.3f} EPA/play against a vulnerable {d_tm} defense allowing {d_val:+.3f} EPA/play.",
                    }
                )
            elif d_rk <= 5 and o_rk >= 23:
                mismatch_cards.append(
                    {
                        "style": "terminal-card-vuln",
                        "badges": f"{render_rank_badge(d_rk, f'{d_tm} {phase} Def')} vs {render_rank_badge(o_rk, f'{o_tm} {phase} Off')}",
                        "title": f"{render_inline_logo(d_tm, 20)}{d_tm} {phase} Defense Shutdown Spot (+{o_rk - d_rk} Rank Edge)",
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
            off_tm: str,
            def_tm: str,
            off_role: str,
            def_role: str,
            o_row: pd.Series,
            d_row: pd.Series,
            off_pen: float,
            def_pen: float,
        ):
            render_html(
                f"<h4 style='margin:12px 0 8px 0;'>"
                f"Possession Matchup: {render_team_pill(off_tm, off_role)} Offense vs "
                f"{render_team_pill(def_tm, def_role)} Defense</h4>"
            )
            c1, c2, c3 = st.columns(3)

            with c1:
                with st.container(border=True):
                    render_html(
                        f"<b>{render_inline_logo(off_tm, 16)}AIR EFFICIENCY ({off_tm} Pass vs {def_tm} Pass Def)</b><br>"
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
                        f"<b>{render_inline_logo(off_tm, 16)}TRENCH EFFICIENCY ({off_tm} Rush vs {def_tm} Rush Def)</b><br>"
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
                        f"<b>{render_inline_logo(off_tm, 16)}OVERALL & INJURY-ADJUSTED EPA</b><br>"
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

        render_possession_block(away_tm, home_tm, "A", "H", a_eff, h_eff, away_off_pen, home_def_pen)
        st.write("")
        render_possession_block(home_tm, away_tm, "H", "A", h_eff, a_eff, home_off_pen, away_def_pen)

# =============================================================================
# SUB-TAB 4: PLAYER PROP TREND EXPLORER
# =============================================================================
with subtab_props:
    render_html(
        f"<h4 style='margin:0 0 4px 0;'>"
        f"{render_inline_logo(away_tm, 22)}{render_inline_logo(home_tm, 22)}"
        f"Player Prop Trend Explorer ({away_tm} @ {home_tm})</h4>"
    )
    st.caption(
        f"Includes Anytime TD, Receiving TDs, Interceptions (INT), and yardage/reception props ({player_season} logs), "
        "plus automated Last-3-Games (L3) Hot/Cold streak detection."
    )

    prop_logs = prepare_matchup_player_prop_logs(player_df, [away_tm, home_tm])

    if prop_logs.empty:
        st.info(f"No weekly player game logs found for {away_tm} or {home_tm}.")
    else:
        prop_markets = {
            "Receiving Yards": ("receiving_yards", 54.5, 150.0, 1.0),
            "Receptions": ("receptions", 4.5, 15.0, 0.5),
            "Receiving TDs": ("receiving_tds", 0.5, 3.5, 0.5),
            "Targets": ("targets", 6.5, 18.0, 0.5),
            "Rushing Yards": ("rushing_yards", 59.5, 160.0, 1.0),
            "Rush Carries": ("carries", 13.5, 30.0, 0.5),
            "Anytime TD": ("anytime_td", 0.5, 3.5, 0.5),
            "Passing Yards": ("passing_yards", 234.5, 400.0, 1.0),
            "Passing TDs": ("passing_tds", 1.5, 5.5, 0.5),
            "Interceptions (INT)": ("interceptions", 0.5, 3.5, 0.5),
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

        p_log = pos_filtered_logs[
            (pos_filtered_logs["player_label"] == sel_player_name)
            & (pos_filtered_logs["team"] == sel_player_team)
        ].sort_values(by="week").copy()

        total_avail_games = len(p_log)
        is_td_or_int = stat_col_name in ["anytime_td", "receiving_tds", "interceptions"]

        if is_td_or_int:
            smart_default_threshold = 0.5
        else:
            player_median_val = (
                float(p_log[stat_col_name].median()) if total_avail_games > 0 else default_line
            )
            smart_default_threshold = (
                round(player_median_val * 2) / 2 if player_median_val > 0 else default_line
            )

        dynamic_max = float(max(max_line_cap, p_log[stat_col_name].max() * 1.25, 3.5))

        slider_col1, slider_col2 = st.columns(2)
        with slider_col1:
            prop_threshold = st.slider(
                f"Target Prop Threshold ({selected_market_label})",
                min_value=0.5,
                max_value=float(round(dynamic_max, 0) + 0.5),
                value=float(min(max(0.5, smart_default_threshold), dynamic_max)),
                step=float(step_val),
            )
        with slider_col2:
            if total_avail_games > 1:
                lookback_n = st.slider(
                    "Lookback Window (Last N Games)",
                    min_value=1,
                    max_value=total_avail_games,
                    value=min(10, total_avail_games),
                    step=1,
                )
            else:
                lookback_n = 1
                st.caption("Showing single available game log.")

        season_baseline_avg = float(p_log[stat_col_name].mean()) if total_avail_games > 0 else 0.0
        l3_avg = float(p_log.tail(3)[stat_col_name].mean()) if total_avail_games > 0 else 0.0
        streak_badge_html, streak_delta_str = evaluate_player_streak_badge(
            season_baseline_avg, l3_avg, is_negative_stat=(stat_col_name == "interceptions")
        )

        window_log = p_log.tail(lookback_n).copy()
        window_log["hit"] = window_log[stat_col_name] >= prop_threshold
        window_log["bar_color"] = np.where(window_log["hit"], "#00FF87", "#FF4D6D")
        window_log["result_label"] = np.where(window_log["hit"], "OVER (HIT)", "UNDER (MISS)")
        window_log["rolling_avg"] = window_log[stat_col_name].expanding().mean()

        hits_count = int(window_log["hit"].sum())
        sample_n = len(window_log)
        hit_rate_pct = (hits_count / sample_n * 100.0) if sample_n > 0 else 0.0
        avg_val = float(window_log[stat_col_name].mean())
        diff_vs_line = avg_val - prop_threshold

        opp_def_tm = home_tm if sel_player_team == away_tm else away_tm
        is_rush_prop = stat_col_name in ["rushing_yards", "carries"]
        opp_def_rk = (
            int(eff_df.loc[opp_def_tm, "def_rush_epa_rank"])
            if is_rush_prop
            else int(eff_df.loc[opp_def_tm, "def_pass_epa_rank"])
        )
        def_type_str = "Rush Def" if is_rush_prop else "Pass Def"

        pk1, pk2, pk3, pk4 = st.columns(4)
        pk1.metric(
            f"Hit Rate (Last {sample_n} Games)",
            f"{hit_rate_pct:.1f}% ({hits_count}/{sample_n})",
            delta="Strong Over Trend"
            if hit_rate_pct >= 60
            else ("Under Trend" if hit_rate_pct <= 40 else "Balanced Split"),
            delta_color="normal" if hit_rate_pct >= 55 else ("inverse" if hit_rate_pct < 45 else "off"),
        )
        pk2.metric(
            f"Window Avg ({selected_market_label})",
            f"{avg_val:.2f}" if is_td_or_int else f"{avg_val:.1f}",
            delta=f"{diff_vs_line:+.2f} vs Target ({prop_threshold})"
            if is_td_or_int
            else f"{diff_vs_line:+.1f} vs Target ({prop_threshold})",
            delta_color="normal" if diff_vs_line >= 0 else "inverse",
        )
        pk3.metric(
            "L3 Output vs Season Baseline",
            f"{l3_avg:.2f} L3 Avg" if is_td_or_int else f"{l3_avg:.1f} L3 Avg",
            delta=streak_delta_str,
            delta_color="normal"
            if (l3_avg >= season_baseline_avg and stat_col_name != "interceptions")
            else "inverse",
        )
        pk4.metric(
            f"Opposing {opp_def_tm} {def_type_str}",
            f"Rank #{opp_def_rk}",
            delta="Smash Spot (Bottom-10)"
            if opp_def_rk >= 23
            else ("Tough Draw (Top-5)" if opp_def_rk <= 5 else "Neutral Tier"),
            delta_color="normal" if opp_def_rk >= 23 else ("inverse" if opp_def_rk <= 5 else "off"),
        )

        opp_badge_html = render_rank_badge(opp_def_rk, f"{opp_def_tm} {def_type_str}")
        hit_badge_html = (
            f'<span class="badge-elite">● [{hits_count}/{sample_n} OVER ({hit_rate_pct:.0f}%)]</span>'
            if hit_rate_pct >= 60
            else (
                f'<span class="badge-bad">● [{hits_count}/{sample_n} OVER ({hit_rate_pct:.0f}%)]</span>'
                if hit_rate_pct <= 40
                else f'<span class="badge-mid">● [{hits_count}/{sample_n} OVER ({hit_rate_pct:.0f}%)]</span>'
            )
        )

        render_html(
            f"""
            <div class="terminal-card" style="padding:12px; margin-bottom:10px;">
                <div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:8px;">
                    <div>
                        {render_team_pill(sel_player_team)} <b>{sel_player_name}</b>
                        <span class="badge-sage">[{sel_player_pos}]</span>
                        {streak_badge_html}
                    </div>
                    <div>{hit_badge_html} {opp_badge_html}</div>
                </div>
            </div>
            """
        )

        fig_prop = go.Figure()

        fig_prop.add_trace(
            go.Bar(
                x=window_log["game_tag"],
                y=window_log[stat_col_name],
                marker_color=window_log["bar_color"],
                text=[
                    f"{v:.0f}" if (step_val >= 1 or is_td_or_int) else f"{v:.1f}"
                    for v in window_log[stat_col_name]
                ],
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

        fig_prop.add_hline(
            y=prop_threshold,
            line_width=2.5,
            line_dash="dash",
            line_color="#FFB020",
            annotation_text=f"Target Line: {prop_threshold} ({hit_rate_pct:.0f}% Hit Rate)",
            annotation_position="top left",
            annotation_font=dict(color="#FFB020", size=12),
        )

        y_upper = max(float(window_log[stat_col_name].max()), prop_threshold) * 1.25 + 1.0
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
            height=400,
            margin=dict(l=20, r=20, t=60, b=30),
        )

        st.plotly_chart(fig_prop, width="stretch")

        with st.expander(f"View {sel_player_name} Game-by-Game Log Table ({sample_n} Games)"):
            log_cols = [
                "week",
                "opp_label",
                stat_col_name,
                "result_label",
                "anytime_td",
                "receiving_tds",
                "interceptions",
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
                    "anytime_td": "Anytime TDs",
                    "receiving_tds": "Rec TDs",
                    "interceptions": "INTs",
                },
            )

# =============================================================================
# SUB-TAB 5: TEAM ROSTER & USAGE EXPLORER
# =============================================================================
with subtab_roster:
    render_html(
        f"<h4 style='margin:0 0 4px 0;'>"
        f"{render_inline_logo(away_tm, 22)}{away_tm} & {render_inline_logo(home_tm, 22)}{home_tm} — "
        f"Team Roster & Usage Explorer</h4>"
    )
    st.caption(
        "Filter by **All Offense**, **All Defense**, or **Special Teams** at once, or drill into specific positions "
        "to inspect Snap %, Total Snaps, Targets, Target Share, Touches, Air Yards, and Total EPA."
    )

    roster_table = build_roster_usage_table(snaps_df, usage_matchup, [away_tm, home_tm])

    if roster_table.empty:
        st.info("Active roster and snap usage data unavailable for the selected teams.")
    else:
        r_col1, r_col2, r_col3, r_col4 = st.columns([1.1, 1.3, 1.2, 1.1])
        with r_col1:
            roster_team_filter = st.radio(
                "1. Team Filter",
                options=[f"Both ({away_tm} & {home_tm})", away_tm, home_tm],
                horizontal=True,
            )
        with r_col2:
            unit_group_filter = st.radio(
                "2. Unit Group (One-Click Filter)",
                options=["All Roster", "All Offense", "All Defense", "Special Teams"],
                horizontal=True,
            )

        filtered_roster = roster_table.copy()
        if roster_team_filter in [away_tm, home_tm]:
            filtered_roster = filtered_roster[filtered_roster["team"] == roster_team_filter]

        if unit_group_filter == "All Offense":
            filtered_roster = filtered_roster[filtered_roster["unit_group"] == "Offense"]
        elif unit_group_filter == "All Defense":
            filtered_roster = filtered_roster[filtered_roster["unit_group"] == "Defense"]
        elif unit_group_filter == "Special Teams":
            filtered_roster = filtered_roster[filtered_roster["unit_group"] == "Special Teams"]

        with r_col3:
            avail_roster_pos = sorted(filtered_roster["position"].dropna().astype(str).unique().tolist())
            roster_pos_filter = st.multiselect(
                "3. Specific Positions (Optional)",
                options=avail_roster_pos,
                default=[],
                placeholder=f"All {unit_group_filter} Positions",
            )
        with r_col4:
            min_snap_slider = st.slider(
                "4. Min Snap Share %",
                min_value=0,
                max_value=90,
                value=10,
                step=5,
            )

        if roster_pos_filter:
            filtered_roster = filtered_roster[filtered_roster["position"].isin(roster_pos_filter)]
        filtered_roster = filtered_roster[filtered_roster["primary_snap_pct"] >= min_snap_slider]

        if not filtered_roster.empty:
            top_snap_p = filtered_roster.sort_values(by="primary_snap_pct", ascending=False).iloc[0]
            top_tgt_p = filtered_roster.sort_values(by="targets", ascending=False).iloc[0]
            top_touch_p = filtered_roster.sort_values(by="touches", ascending=False).iloc[0]
            top_air_p = filtered_roster.sort_values(by="air_yards", ascending=False).iloc[0]

            rk1, rk2, rk3, rk4 = st.columns(4)
            rk1.metric(
                f"{unit_group_filter} Snap Leader",
                f"{top_snap_p['player_name']} ({top_snap_p['team']})",
                delta=f"{top_snap_p['primary_snap_pct']:.1f}% Snaps ({int(top_snap_p['total_snaps'])} total)",
            )
            rk2.metric(
                "Target Leader",
                f"{top_tgt_p['player_name']} ({top_tgt_p['team']})",
                delta=f"{int(top_tgt_p['targets'])} Tgts ({top_tgt_p['target_share_pct']:.1f}% Share)",
            )
            rk3.metric(
                "Total Touches Leader",
                f"{top_touch_p['player_name']} ({top_touch_p['team']})",
                delta=f"{int(top_touch_p['touches'])} Touches ({int(top_touch_p['scrimmage_yards'])} Yds)",
            )
            rk4.metric(
                "Air Yards Leader",
                f"{top_air_p['player_name']} ({top_air_p['team']})",
                delta=f"{int(top_air_p['air_yards'])} Air Yards",
            )

        roster_disp_cols = [
            "team_logo",
            "team",
            "unit_group",
            "player_name",
            "position",
            "games_played",
            "primary_snap_pct",
            "total_snaps",
            "targets",
            "receptions",
            "target_share_pct",
            "air_yards",
            "carries",
            "touches",
            "scrimmage_yards",
            "total_tds",
            "total_epa",
        ]
        avail_r_cols = [c for c in roster_disp_cols if c in filtered_roster.columns]

        st.dataframe(
            filtered_roster[avail_r_cols],
            width="stretch",
            hide_index=True,
            column_config={
                "team_logo": st.column_config.ImageColumn("", width="small"),
                "team": "Team",
                "unit_group": "Unit",
                "player_name": "Player",
                "position": "Pos",
                "games_played": st.column_config.NumberColumn("Games", format="%d"),
                "primary_snap_pct": st.column_config.ProgressColumn(
                    "Snap Share %", format="%.1f%%", min_value=0, max_value=100
                ),
                "total_snaps": st.column_config.NumberColumn("Total Snaps", format="%d"),
                "targets": st.column_config.NumberColumn("Targets", format="%d"),
                "receptions": st.column_config.NumberColumn("Rec", format="%d"),
                "target_share_pct": st.column_config.ProgressColumn(
                    "Target Share %", format="%.1f%%", min_value=0, max_value=50
                ),
                "air_yards": st.column_config.NumberColumn("Air Yards", format="%d"),
                "carries": st.column_config.NumberColumn("Carries", format="%d"),
                "touches": st.column_config.NumberColumn("Touches", format="%d"),
                "scrimmage_yards": st.column_config.NumberColumn("Scrimmage Yds", format="%d"),
                "total_tds": st.column_config.NumberColumn("Total TDs", format="%d"),
                "total_epa": st.column_config.NumberColumn("Total EPA", format="%+.2f"),
            },
        )

# =============================================================================
# SUB-TAB 6: BACKTEST PERFORMANCE
# =============================================================================
with subtab_backtest:
    st.markdown(f"#### {selected_season} Season Historical Backtest & Edge Grading")
    st.caption(
        "Grades all completed games in the selected season where extreme unit mismatches (`● ELITE [#1-#5]` vs `● BAD [#23-#32]`), "
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

        st.markdown("##### Signal Performance Breakdown")
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

        with st.expander(f"Inspect Graded Game-by-Game Backtest Log ({len(bt_log)} Flagged Spots)"):
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