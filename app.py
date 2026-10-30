from urllib.parse import quote
import math
import time
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
import streamlit.components.v1 as components

# -----------------------------------------------------------------------------
# 1. PAGE CONFIGURATION & TEAM-COLORED TERMINAL CSS THEME (STRICT NO-EMOJI UI)
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="Football Edger",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Official 32-Team NFL Primary & Secondary/Away Color Palette
# Primary colors use true team hues (including red for KC/SF/ARI/TB/ATL, green for PHI/NYJ/GB,
# orange for CIN/DEN/CLE, etc.) tuned for legibility on dark terminal cards (#121722).
NFL_TEAM_COLORS: dict[str, dict[str, str]] = {
    "ARI": {"primary": "#E31837", "secondary": "#FFB612", "name": "Cardinals Red"},
    "ATL": {"primary": "#CE1141", "secondary": "#A5ACAF", "name": "Falcons Red"},
    "BAL": {"primary": "#8B5CF6", "secondary": "#D4AF37", "name": "Ravens Purple"},
    "BUF": {"primary": "#0066CC", "secondary": "#C60C30", "name": "Bills Royal"},
    "CAR": {"primary": "#0085CA", "secondary": "#BFC0BF", "name": "Panthers Blue"},
    "CHI": {"primary": "#E64100", "secondary": "#3B82F6", "name": "Bears Orange"},
    "CIN": {"primary": "#FB4F14", "secondary": "#F8FAFC", "name": "Bengals Orange"},
    "CLE": {"primary": "#FF3C00", "secondary": "#A0522D", "name": "Browns Orange"},
    "DAL": {"primary": "#0072CE", "secondary": "#94A3B8", "name": "Cowboys Blue"},
    "DEN": {"primary": "#FB4F14", "secondary": "#0066CC", "name": "Broncos Orange"},
    "DET": {"primary": "#0076B6", "secondary": "#B0B7BC", "name": "Lions Honolulu Blue"},
    "GB": {"primary": "#388E3C", "secondary": "#FFB612", "name": "Packers Green"},
    "HOU": {"primary": "#0066B2", "secondary": "#CE1141", "name": "Texans Deep Steel Blue"},
    "IND": {"primary": "#0066CC", "secondary": "#CBD5E1", "name": "Colts Blue"},
    "JAX": {"primary": "#008E97", "secondary": "#D7A22A", "name": "Jaguars Teal"},
    "KC": {"primary": "#E31837", "secondary": "#FFB81C", "name": "Chiefs Red"},
    "LA": {"primary": "#0066CC", "secondary": "#FFA300", "name": "Rams Royal"},
    "LAR": {"primary": "#0066CC", "secondary": "#FFA300", "name": "Rams Royal"},
    "LAC": {"primary": "#0092DF", "secondary": "#FFC20E", "name": "Chargers Powder Blue"},
    "LV": {"primary": "#A5ACAF", "secondary": "#64748B", "name": "Raiders Silver"},
    "MIA": {"primary": "#009CA6", "secondary": "#FC4C02", "name": "Dolphins Aqua"},
    "MIN": {"primary": "#8A42A8", "secondary": "#FFC62F", "name": "Vikings Purple"},
    "NE": {"primary": "#2563EB", "secondary": "#C60C30", "name": "Patriots Nautical Blue"},
    "NO": {"primary": "#D3BC8D", "secondary": "#94A3B8", "name": "Saints Old Gold"},
    "NYG": {"primary": "#1967D2", "secondary": "#CE1141", "name": "Giants Blue"},
    "NYJ": {"primary": "#1E9E6A", "secondary": "#CBD5E1", "name": "Jets Gotham Green"},
    "PHI": {"primary": "#0097A7", "secondary": "#A5ACAF", "name": "Eagles Midnight Green"},
    "PIT": {"primary": "#FFB612", "secondary": "#CBD5E1", "name": "Steelers Gold"},
    "SEA": {"primary": "#69BE28", "secondary": "#0066B2", "name": "Seahawks Action Green"},
    "SF": {"primary": "#C8102E", "secondary": "#B3995D", "name": "49ers Scarlet"},
    "TB": {"primary": "#D50A0A", "secondary": "#FF7900", "name": "Buccaneers Pewter Red"},
    "TEN": {"primary": "#4B92DB", "secondary": "#C8102E", "name": "Titans Columbia Blue"},
    "WAS": {"primary": "#A62639", "secondary": "#FFB612", "name": "Commanders Burgundy"},
    "WSH": {"primary": "#A62639", "secondary": "#FFB612", "name": "Commanders Burgundy"},
}


def hex_to_rgb(hex_color: str) -> tuple[int, int, int]:
    """Converts a #RRGGBB hex string into an (R, G, B) integer tuple."""
    h = hex_color.lstrip("#")
    if len(h) != 6:
        return (100, 116, 139)
    return int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)


def hex_to_rgba(hex_color: str, alpha: float = 0.16) -> str:
    """Converts a #RRGGBB hex string into an rgba(r, g, b, alpha) CSS string."""
    r, g, b = hex_to_rgb(hex_color)
    return f"rgba({r}, {g}, {b}, {alpha:.2f})"


def get_team_primary_color(team_abbr: str) -> str:
    """Returns the official NFL primary color for a team."""
    clean = str(team_abbr).strip().upper()
    return NFL_TEAM_COLORS.get(clean, {}).get("primary", "#64748B")


def get_team_secondary_color(team_abbr: str) -> str:
    """Returns the official NFL secondary/away color for a team."""
    clean = str(team_abbr).strip().upper()
    return NFL_TEAM_COLORS.get(clean, {}).get("secondary", "#94A3B8")


def get_matchup_team_colors(away_tm: str, home_tm: str) -> tuple[str, str]:
    """
    Returns (away_color, home_color) for a matchup.
    Home team always uses its primary NFL color. Away team uses its primary NFL color
    unless both teams share a closely colliding primary hue (Euclidean RGB distance < 95),
    in which case the Away team automatically switches to its official secondary/away color.
    """
    h_pri = get_team_primary_color(home_tm)
    a_pri = get_team_primary_color(away_tm)
    a_sec = get_team_secondary_color(away_tm)

    r1, g1, b1 = hex_to_rgb(a_pri)
    r2, g2, b2 = hex_to_rgb(h_pri)
    dist = math.sqrt((r1 - r2) ** 2 + (g1 - g2) ** 2 + (b1 - b2) ** 2)

    if dist < 95.0 and a_sec != h_pri:
        return a_sec, h_pri
    return a_pri, h_pri


def resolve_team_display_color(team_abbr: str) -> str:
    """
    Returns the active matchup-resolved color for `team_abbr` if it is one of the two teams
    in the currently selected game (respecting secondary color collision fallback),
    or the team's official primary color otherwise.
    """
    clean = str(team_abbr).strip().upper()
    active_map = st.session_state.get("active_matchup_colors", {})
    if clean in active_map:
        return active_map[clean]
    return get_team_primary_color(clean)


st.markdown(
    """
<style>
/* Global Overflow & Box-Sizing Guardrails */
*, *::before, *::after {
    box-sizing: border-box;
}

/* Global st.metric Anti-Truncation Override (Prevents '...' Ellipsis Clipping) */
div[data-testid="stMetric"] {
    max-width: 100% !important;
    min-width: 0 !important;
}
div[data-testid="stMetricValue"],
div[data-testid="stMetricValue"] > div {
    font-size: 1.45rem !important;
    line-height: 1.25 !important;
    white-space: normal !important;
    overflow: visible !important;
    text-overflow: clip !important;
    overflow-wrap: break-word !important;
    word-break: break-word !important;
}
div[data-testid="stMetricLabel"],
div[data-testid="stMetricLabel"] > div,
div[data-testid="stMetricLabel"] p {
    white-space: normal !important;
    overflow: visible !important;
    text-overflow: clip !important;
    overflow-wrap: break-word !important;
}
div[data-testid="stMetricDelta"],
div[data-testid="stMetricDelta"] > div {
    white-space: normal !important;
    overflow: visible !important;
    text-overflow: clip !important;
    overflow-wrap: break-word !important;
    line-height: 1.3 !important;
}

/* Custom Non-Directional & Directional KPI Cards */
.custom-kpi-grid {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 12px;
    margin-bottom: 12px;
}
.custom-kpi-card {
    background-color: #141923;
    border: 1px solid rgba(255, 255, 255, 0.07);
    border-top: 3px solid #475569;
    border-radius: 10px;
    padding: 12px 14px;
    min-width: 0;
    display: flex;
    flex-direction: column;
    justify-content: space-between;
}
.custom-kpi-card-edge {
    border-top: 2px solid #34D399;
}
.custom-kpi-card-warn {
    border-top: 2px solid #F87171;
}
.custom-kpi-top {
    display: flex;
    justify-content: space-between;
    align-items: center;
    gap: 6px;
    margin-bottom: 4px;
}
.custom-kpi-label {
    font-size: 0.76rem;
    font-family: Inter, -apple-system, BlinkMacSystemFont, sans-serif; font-variant-numeric: tabular-nums;
    color: #94A3B8;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.03em;
}
.custom-kpi-help {
    font-size: 0.66rem;
    font-family: Inter, -apple-system, BlinkMacSystemFont, sans-serif; font-variant-numeric: tabular-nums;
    color: #64748B;
    border: 1px solid #2A364B;
    border-radius: 4px;
    padding: 0px 5px;
    cursor: help;
}
.custom-kpi-val {
    font-size: 1.38rem;
    font-weight: 800;
    font-family: Inter, -apple-system, BlinkMacSystemFont, sans-serif; font-variant-numeric: tabular-nums;
    color: #F8FAFC;
    line-height: 1.22;
    margin-bottom: 6px;
    overflow-wrap: break-word;
}
.custom-kpi-pill-pos {
    background-color: rgba(52, 211, 153, 0.12);
    color: #34D399;
    border: 1px solid rgba(52, 211, 153, 0.35);
    padding: 2px 8px;
    border-radius: 4px;
    font-size: 0.72rem;
    font-family: Inter, -apple-system, BlinkMacSystemFont, sans-serif; font-variant-numeric: tabular-nums;
    font-weight: 700;
    display: inline-block;
    width: fit-content;
}
.custom-kpi-pill-neg {
    background-color: rgba(248, 113, 113, 0.12);
    color: #F87171;
    border: 1px solid rgba(248, 113, 113, 0.35);
    padding: 2px 8px;
    border-radius: 4px;
    font-size: 0.72rem;
    font-family: Inter, -apple-system, BlinkMacSystemFont, sans-serif; font-variant-numeric: tabular-nums;
    font-weight: 700;
    display: inline-block;
    width: fit-content;
}
.custom-kpi-pill-neutral {
    background-color: rgba(148, 163, 184, 0.10);
    color: #CBD5E1;
    border: 1px solid #334155;
    padding: 2px 8px;
    border-radius: 4px;
    font-size: 0.72rem;
    font-family: Inter, -apple-system, BlinkMacSystemFont, sans-serif; font-variant-numeric: tabular-nums;
    font-weight: 600;
    display: inline-block;
    width: fit-content;
}

/* Clean, Toned-Down Sports Analytics Terminal Cards */
.terminal-card {
    background-color: #121722;
    border: 1px solid #222B3A;
    border-left: 3px solid #64748B;
    border-radius: 8px;
    padding: 14px 16px;
    margin-bottom: 10px;
    color: #E2E8F0;
    max-width: 100%;
    overflow-wrap: break-word;
    word-wrap: break-word;
}
.terminal-card-elite {
    background-color: #111A1E;
    border: 1px solid #1E3532;
    border-left: 3px solid #34D399;
    border-radius: 8px;
    padding: 14px 16px;
    margin-bottom: 10px;
    color: #E2E8F0;
    max-width: 100%;
    overflow-wrap: break-word;
    word-wrap: break-word;
}
.terminal-card-vuln {
    background-color: #1B1519;
    border: 1px solid #3B2329;
    border-left: 3px solid #F87171;
    border-radius: 8px;
    padding: 14px 16px;
    margin-bottom: 10px;
    color: #E2E8F0;
    max-width: 100%;
    overflow-wrap: break-word;
    word-wrap: break-word;
}

/* Inline Hyperlinked Player Names (HTML <a> and Streamlit Tertiary Buttons) */
a.player-name-link {
    color: #F1F5F9 !important;
    font-weight: 700;
    text-decoration: underline;
    text-decoration-color: rgba(148, 163, 184, 0.55);
    text-underline-offset: 3px;
    cursor: pointer;
    transition: color 0.14s ease, text-decoration-color 0.14s ease;
    overflow-wrap: anywhere;
    word-break: break-word;
}
a.player-name-link:hover {
    color: #CBD5E1 !important;
    text-decoration-color: #CBD5E1;
}

/* Style Streamlit tertiary buttons to look like clean inline hyperlinked player/pick boxes */
button[kind="tertiary"] {
    background: transparent !important;
    border: none !important;
    box-shadow: none !important;
    padding: 0px 2px !important;
    margin: 0px !important;
    min-height: unset !important;
    height: auto !important;
    max-width: 100% !important;
    color: #F1F5F9 !important;
    font-family: Inter, -apple-system, BlinkMacSystemFont, sans-serif !important; font-variant-numeric: tabular-nums !important;
    font-weight: 700 !important;
    font-size: 0.90rem !important;
    text-decoration: underline !important;
    text-decoration-color: rgba(148, 163, 184, 0.55) !important;
    text-underline-offset: 3px !important;
    line-height: 1.35 !important;
    display: inline-flex !important;
    align-items: center !important;
    white-space: normal !important;
    text-align: left !important;
}
button[kind="tertiary"]:hover {
    color: #F8FAFC !important;
    text-decoration-color: #F8FAFC !important;
    background: rgba(148, 163, 184, 0.14) !important;
    border-radius: 3px !important;
}
button[kind="tertiary"] p {
    font-family: Inter, -apple-system, BlinkMacSystemFont, sans-serif !important; font-variant-numeric: tabular-nums !important;
    font-weight: 700 !important;
    font-size: 0.90rem !important;
    color: inherit !important;
    margin: 0 !important;
    text-decoration: underline !important;
    text-decoration-color: rgba(148, 163, 184, 0.55) !important;
    text-underline-offset: 3px !important;
    white-space: normal !important;
    overflow-wrap: anywhere !important;
    word-break: break-word !important;
    text-align: left !important;
}

/* ============================================================================
   STREAMLIT HORIZONTAL BLOCK TICKER OVERRIDE (Interactive Button Strip)
   ============================================================================ */
.ticker-scroll-hint-bar {
    display: flex;
    justify-content: space-between;
    align-items: center;
    background: #0B0F17;
    border: 1px solid #1E2736;
    border-bottom: none;
    border-radius: 8px 8px 0 0;
    padding: 4px 12px;
    font-family: Inter, -apple-system, BlinkMacSystemFont, sans-serif; font-variant-numeric: tabular-nums;
    font-size: 0.68rem;
    color: #94A3B8;
}
div[data-testid="stHorizontalBlock"]:has(.nfl-ticker-marker) {
    display: flex !important;
    flex-direction: row !important;
    flex-wrap: nowrap !important;
    overflow-x: auto !important;
    overflow-y: hidden !important;
    white-space: nowrap !important;
    gap: 10px !important;
    padding: 10px 12px 14px 12px !important;
    margin-bottom: 10px !important;
    max-width: 100% !important;
    background: linear-gradient(90deg, #0D1118 0%, #0D1118 96%, #162030 100%) !important;
    border: 1px solid #1E2736 !important;
    border-radius: 0 0 8px 8px !important;
    scrollbar-width: thin;
    scrollbar-color: #475569 #0D1118;
    -webkit-overflow-scrolling: touch;
}
div[data-testid="stHorizontalBlock"]:has(.nfl-ticker-marker)::-webkit-scrollbar {
    height: 8px;
}
div[data-testid="stHorizontalBlock"]:has(.nfl-ticker-marker)::-webkit-scrollbar-track {
    background: #0D1118;
    border-radius: 4px;
}
div[data-testid="stHorizontalBlock"]:has(.nfl-ticker-marker)::-webkit-scrollbar-thumb {
    background-color: #334155;
    border-radius: 4px;
    border: 1px solid #1E293B;
}
div[data-testid="stHorizontalBlock"]:has(.nfl-ticker-marker)::-webkit-scrollbar-thumb:hover {
    background-color: #64748B;
}
div[data-testid="stHorizontalBlock"]:has(.nfl-ticker-marker) > div[data-testid="stColumn"],
div[data-testid="stHorizontalBlock"]:has(.nfl-ticker-marker) > div[data-testid="column"] {
    flex: 0 0 202px !important;
    min-width: 202px !important;
    max-width: 202px !important;
    width: 202px !important;
    white-space: nowrap !important;
    display: flex !important;
    flex-direction: column !important;
    gap: 0px !important;
    position: relative !important;
}
div[data-testid="stHorizontalBlock"]:has(.nfl-ticker-marker) div[data-testid="stVerticalBlock"] {
    position: relative !important;
    gap: 0px !important;
}

/* Individual Ticker Card Visuals (Full-Card Clickable Target) */
.ticker-card {
    background-color: #131823;
    border: 1px solid #242E3E;
    border-top: 2px solid #334155;
    border-radius: 6px;
    padding: 8px 10px;
    margin-bottom: 0px;
    white-space: nowrap;
    cursor: pointer;
    transition: all 0.14s ease-in-out;
}
.ticker-card-active {
    background-color: #161E2E;
    border: 1.5px solid #64748B;
    border-radius: 6px;
    padding: 8px 10px;
    margin-bottom: 0px;
    white-space: nowrap;
    cursor: pointer;
    box-shadow: 0 4px 14px rgba(0, 0, 0, 0.45);
}
div[data-testid="stHorizontalBlock"]:has(.nfl-ticker-marker) > div[data-testid="stColumn"]:hover .ticker-card,
div[data-testid="stHorizontalBlock"]:has(.nfl-ticker-marker) > div[data-testid="column"]:hover .ticker-card {
    background-color: #182030;
    border-color: #64748B;
    transform: translateY(-1px);
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.42);
}
.ticker-top-bar {
    display: flex;
    justify-content: space-between;
    align-items: center;
    font-size: 0.66rem;
    font-family: Inter, -apple-system, BlinkMacSystemFont, sans-serif; font-variant-numeric: tabular-nums;
    color: #94A3B8;
    margin-bottom: 5px;
    padding-bottom: 3px;
    border-bottom: 1px solid #1E293B;
    white-space: nowrap;
}
.ticker-slot-tag {
    background-color: rgba(148, 163, 184, 0.12);
    color: #CBD5E1;
    border: 1px solid #334155;
    padding: 0px 5px;
    border-radius: 3px;
    font-size: 0.62rem;
    font-weight: 700;
    font-family: Inter, -apple-system, BlinkMacSystemFont, sans-serif; font-variant-numeric: tabular-nums;
}
.ticker-team-row {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin: 4px 0;
    font-family: Inter, -apple-system, BlinkMacSystemFont, sans-serif; font-variant-numeric: tabular-nums;
    font-size: 0.83rem;
    font-weight: 700;
    color: #F1F5F9;
    white-space: nowrap;
}
.ticker-team-left {
    display: flex;
    align-items: center;
    gap: 5px;
    white-space: nowrap;
}
.ticker-team-record {
    font-family: Inter, -apple-system, BlinkMacSystemFont, sans-serif; font-variant-numeric: tabular-nums;
    font-size: 0.71rem;
    font-weight: 600;
    color: #64748B;
    margin-left: 2px;
}
.ticker-score-win {
    font-family: Inter, -apple-system, BlinkMacSystemFont, sans-serif; font-variant-numeric: tabular-nums;
    font-size: 0.86rem;
    font-weight: 800;
    color: #34D399;
}
.ticker-score {
    font-family: Inter, -apple-system, BlinkMacSystemFont, sans-serif; font-variant-numeric: tabular-nums;
    font-size: 0.84rem;
    font-weight: 700;
    color: #CBD5E1;
}
.ticker-score-muted {
    font-family: Inter, -apple-system, BlinkMacSystemFont, sans-serif; font-variant-numeric: tabular-nums;
    font-size: 0.74rem;
    color: #64748B;
}
.ticker-footer {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-top: 6px;
    padding-top: 5px;
    padding-bottom: 4px;
    border-top: 1px solid #1E293B;
    font-size: 0.68rem;
    font-weight: 600;
    font-family: Inter, -apple-system, BlinkMacSystemFont, sans-serif; font-variant-numeric: tabular-nums;
    color: #CBD5E1;
    white-space: nowrap;
}

/* Stretch the Streamlit button into an invisible full-card overlay across the entire ticker card */
div[data-testid="stHorizontalBlock"]:has(.nfl-ticker-marker) div[data-testid="stElementContainer"]:has(div[data-testid="stButton"]),
div[data-testid="stHorizontalBlock"]:has(.nfl-ticker-marker) div.element-container:has(div[data-testid="stButton"]),
div[data-testid="stHorizontalBlock"]:has(.nfl-ticker-marker) div[data-testid="stButton"] {
    position: absolute !important;
    top: 0 !important;
    left: 0 !important;
    right: 0 !important;
    bottom: 0 !important;
    width: 100% !important;
    height: 100% !important;
    margin: 0 !important;
    padding: 0 !important;
    z-index: 20 !important;
}
div[data-testid="stHorizontalBlock"]:has(.nfl-ticker-marker) div[data-testid="stButton"] > button {
    position: absolute !important;
    top: 0 !important;
    left: 0 !important;
    width: 100% !important;
    height: 100% !important;
    min-height: 100% !important;
    padding: 0 !important;
    margin: 0 !important;
    opacity: 0 !important;
    background: transparent !important;
    border: none !important;
    box-shadow: none !important;
    cursor: pointer !important;
    z-index: 25 !important;
}

/* Streamlined Active Game Selection Banner (Team-Colored) */
.active-game-spotlight {
    background-color: #121824;
    border: 1px solid #2A364B;
    border-radius: 10px;
    padding: 14px 18px;
    margin: 4px 0 10px 0;
    color: #F8FAFC;
    max-width: 100%;
    overflow-wrap: break-word;
}
.active-lock-pill {
    background-color: rgba(148, 163, 184, 0.14);
    color: #F8FAFC;
    border: 1px solid #475569;
    padding: 3px 10px;
    border-radius: 5px;
    font-size: 0.72rem;
    font-weight: 700;
    letter-spacing: 0.04em;
    font-family: Inter, -apple-system, BlinkMacSystemFont, sans-serif; font-variant-numeric: tabular-nums;
    display: inline-block;
    text-transform: uppercase;
}

/* Promoted Above-the-Fold Environment, Line Movement & Lineup Status Strip */
.promoted-context-strip {
    display: grid;
    grid-template-columns: 1.15fr 1.25fr 1.25fr;
    gap: 10px;
    background-color: #131926;
    border: 1px solid #232E42;
    border-radius: 8px;
    padding: 10px 14px;
    margin-bottom: 12px;
}
.promoted-context-cell {
    border-right: 1px solid #1E293B;
    padding-right: 10px;
    min-width: 0;
}
.promoted-context-cell:last-child {
    border-right: none;
    padding-right: 0;
}
.context-cell-title {
    font-size: 0.69rem;
    font-family: Inter, -apple-system, BlinkMacSystemFont, sans-serif; font-variant-numeric: tabular-nums;
    color: #94A3B8;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.04em;
    margin-bottom: 4px;
}

/* ============================================================================
   OFFENSE VS OPPOSING DEFENSE CROSS-UNIT MATCHUP MATRIX & TEAM TUG-OF-WAR BARS
   ============================================================================ */
.cross-unit-row {
    background-color: #151B26;
    border: 1px solid #232C3D;
    border-radius: 7px;
    padding: 9px 12px;
    margin-bottom: 8px;
}
.cross-unit-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    flex-wrap: wrap;
    gap: 6px;
    margin-bottom: 5px;
    font-family: Inter, -apple-system, BlinkMacSystemFont, sans-serif; font-variant-numeric: tabular-nums;
    font-size: 0.78rem;
}
.tug-bar-track {
    width: 100%;
    height: 8px;
    background-color: #1E293B;
    border-radius: 4px;
    overflow: hidden;
    display: flex;
    gap: 2px;
    margin: 5px 0;
}
.tug-bar-segment {
    height: 100%;
    transition: width 0.25s ease;
}

/* ============================================================================
   HYPERLINKED PICK PILL BOXES & FLOATING CIRCULAR '+' BUTTON
   ============================================================================ */
.compact-bet-pill {
    display: flex;
    align-items: center;
    justify-content: space-between;
    flex-wrap: wrap;
    gap: 6px;
    background-color: #141B28;
    border: 1px solid #263246;
    border-radius: 6px;
    padding: 6px 10px;
    font-family: Inter, -apple-system, BlinkMacSystemFont, sans-serif; font-variant-numeric: tabular-nums;
    font-size: 0.76rem;
    color: #F1F5F9;
    min-height: 36px;
}

/* Floating Bottom-Right Circular '+' Trigger Button */
div[data-testid="stElementContainer"]:has(.floating-plus-fab-marker) + div[data-testid="stElementContainer"],
div.element-container:has(.floating-plus-fab-marker) + div.element-container {
    position: fixed !important;
    bottom: 24px !important;
    right: 26px !important;
    z-index: 999990 !important;
    width: 64px !important;
    height: 64px !important;
    margin: 0 !important;
    padding: 0 !important;
}
div[data-testid="stElementContainer"]:has(.floating-plus-fab-marker) + div[data-testid="stElementContainer"] div[data-testid="stButton"],
div.element-container:has(.floating-plus-fab-marker) + div.element-container div[data-testid="stButton"] {
    width: 64px !important;
    height: 64px !important;
}
div[data-testid="stElementContainer"]:has(.floating-plus-fab-marker) + div[data-testid="stElementContainer"] div[data-testid="stButton"] button,
div.element-container:has(.floating-plus-fab-marker) + div.element-container div[data-testid="stButton"] button {
    width: 64px !important;
    height: 64px !important;
    min-height: 64px !important;
    max-width: 64px !important;
    border-radius: 50% !important;
    background: radial-gradient(circle at 30% 30%, #1E293B 0%, #0F172A 100%) !important;
    border: 2.5px solid #38BDF8 !important;
    color: #F8FAFC !important;
    padding: 0 !important;
    margin: 0 !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
    box-shadow: 0 10px 28px rgba(0, 0, 0, 0.72), 0 0 16px rgba(56, 189, 248, 0.35) !important;
    transition: transform 0.16s ease, box-shadow 0.16s ease, border-color 0.16s ease !important;
    position: relative !important;
}
div[data-testid="stElementContainer"]:has(.floating-plus-fab-marker) + div[data-testid="stElementContainer"] div[data-testid="stButton"] button p,
div.element-container:has(.floating-plus-fab-marker) + div.element-container div[data-testid="stButton"] button p {
    font-family: Inter, -apple-system, BlinkMacSystemFont, sans-serif !important; font-variant-numeric: tabular-nums !important;
    font-size: 2.15rem !important;
    font-weight: 900 !important;
    line-height: 1 !important;
    color: #F8FAFC !important;
    text-decoration: none !important;
    margin: 0 !important;
    padding: 0 !important;
}
div[data-testid="stElementContainer"]:has(.floating-plus-fab-marker) + div[data-testid="stElementContainer"] div[data-testid="stButton"] button:hover,
div.element-container:has(.floating-plus-fab-marker) + div.element-container div[data-testid="stButton"] button:hover {
    transform: scale(1.07) translateY(-2px) !important;
    border-color: #34D399 !important;
    box-shadow: 0 12px 32px rgba(0, 0, 0, 0.82), 0 0 22px rgba(52, 211, 153, 0.48) !important;
}

/* ============================================================================
   MINI L5 SPARKBARS FOR DEDUPLICATED PLAYER PICK CARDS
   ============================================================================ */
.l5-sparkbar-wrap {
    display: inline-flex;
    align-items: flex-end;
    gap: 4px;
    height: 26px;
    padding: 2px 6px;
    background: #141B28;
    border: 1px solid #243044;
    border-radius: 5px;
    vertical-align: middle;
}
.l5-bar-col {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: flex-end;
    height: 22px;
    width: 14px;
}
.l5-bar-fill {
    width: 10px;
    border-radius: 2px 2px 0 0;
}
.l5-bar-lbl {
    font-family: Inter, -apple-system, BlinkMacSystemFont, sans-serif; font-variant-numeric: tabular-nums;
    font-size: 0.55rem;
    color: #94A3B8;
    line-height: 1;
    margin-top: 1px;
}

/* ============================================================================
   CENTERED PLAYER HEADSHOT AVATARS WITH SUBTLE BOTTOM TEAM GRADIENT
   ============================================================================ */
.mismatch-headshot-wrap {
    width: 52px !important;
    height: 52px !important;
    min-width: 52px !important;
    max-width: 52px !important;
    border-radius: 8px;
    background-color: #141B26;
    border: 1px solid #263144;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
    overflow: hidden !important;
    flex-shrink: 0 !important;
    margin: 0 !important;
    padding: 0 !important;
    position: relative !important;
    text-align: center !important;
}
.mismatch-headshot-img {
    width: 52px !important;
    height: 52px !important;
    max-width: none !important;
    object-fit: cover !important;
    object-position: 50% 50% !important;
    display: block !important;
    margin: 0 auto !important;
    padding: 0 !important;
    position: absolute !important;
    top: 50% !important;
    left: 50% !important;
    transform: translate(-50%, -50%) !important;
    z-index: 1 !important;
}
.headshot-bottom-grad {
    position: absolute;
    left: 0;
    right: 0;
    bottom: 0;
    height: 100%;
    z-index: 2;
    pointer-events: none;
}
.mismatch-headshot-fallback {
    width: 100%;
    height: 100%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-family: Inter, -apple-system, BlinkMacSystemFont, sans-serif; font-variant-numeric: tabular-nums;
    font-size: 0.82rem;
    font-weight: 700;
    color: #94A3B8;
    background: #141B26;
    position: relative;
    z-index: 1;
}
.cb-wr-vs-divider {
    text-align: center;
    padding-top: 24px;
    font-family: Inter, -apple-system, BlinkMacSystemFont, sans-serif; font-variant-numeric: tabular-nums;
    font-weight: 800;
    color: #64748B;
}

/* ============================================================================
   PLAYER POP-OUT DOSSIER HEADER & CLEAN BORDERLESS HEADSHOT (NO GRADIENT)
   ============================================================================ */
.player-modal-banner {
    background-color: #121824;
    border: 1px solid #263246;
    border-radius: 8px;
    padding: 12px 20px 0 18px;
    margin-bottom: 12px;
    display: flex;
    align-items: flex-end;
    justify-content: space-between;
    gap: 18px;
    flex-wrap: wrap;
    overflow: hidden;
    max-width: 100%;
}
.player-modal-left {
    display: flex;
    align-items: flex-end;
    gap: 18px;
    flex-wrap: wrap;
    max-width: 100%;
}
.player-headshot-wrap {
    width: 148px;
    height: 124px;
    display: flex;
    align-items: flex-end;
    justify-content: center;
    flex-shrink: 0;
    margin: 0;
    padding: 0;
    background: transparent;
    border: none;
    overflow: hidden;
    position: relative;
}
.player-headshot-img {
    height: 124px;
    width: auto;
    max-width: 148px;
    object-fit: contain;
    object-position: center bottom;
    display: block;
    margin: 0 auto;
    padding: 0;
    border: none;
}
.player-headshot-fallback {
    width: 108px;
    height: 96px;
    background: #1A2232;
    border-radius: 6px 6px 0 0;
    display: flex;
    align-items: center;
    justify-content: center;
    font-family: Inter, -apple-system, BlinkMacSystemFont, sans-serif; font-variant-numeric: tabular-nums;
    font-size: 1.5rem;
    font-weight: 800;
    color: #94A3B8;
}
.player-modal-meta {
    padding-bottom: 14px;
    max-width: 100%;
    overflow-wrap: break-word;
}

/* Evaluative Unit Ranking & Status Badges (Strictly Reserved for Good/Bad/Neutral) */
.badge-elite {
    background-color: rgba(52, 211, 153, 0.10);
    color: #34D399;
    border: 1px solid rgba(52, 211, 153, 0.35);
    padding: 2px 7px;
    border-radius: 4px;
    font-size: 0.72rem;
    font-weight: 700;
    font-family: Inter, -apple-system, BlinkMacSystemFont, sans-serif; font-variant-numeric: tabular-nums;
    display: inline-block;
    margin: 1px 2px;
    max-width: 100%;
    overflow-wrap: anywhere;
}
.badge-cleared {
    background-color: rgba(52, 211, 153, 0.10);
    color: #34D399;
    border: 1px solid rgba(52, 211, 153, 0.35);
    padding: 2px 7px;
    border-radius: 4px;
    font-size: 0.72rem;
    font-weight: 700;
    font-family: Inter, -apple-system, BlinkMacSystemFont, sans-serif; font-variant-numeric: tabular-nums;
    display: inline-block;
    margin: 1px 2px;
    max-width: 100%;
    overflow-wrap: anywhere;
}
.badge-mid {
    background-color: rgba(148, 163, 184, 0.08);
    color: #94A3B8;
    border: 1px solid #334155;
    padding: 2px 7px;
    border-radius: 4px;
    font-size: 0.72rem;
    font-weight: 600;
    font-family: Inter, -apple-system, BlinkMacSystemFont, sans-serif; font-variant-numeric: tabular-nums;
    display: inline-block;
    margin: 1px 2px;
    max-width: 100%;
    overflow-wrap: anywhere;
}
.badge-bad {
    background-color: rgba(248, 113, 113, 0.10);
    color: #F87171;
    border: 1px solid rgba(248, 113, 113, 0.35);
    padding: 2px 7px;
    border-radius: 4px;
    font-size: 0.72rem;
    font-weight: 700;
    font-family: Inter, -apple-system, BlinkMacSystemFont, sans-serif; font-variant-numeric: tabular-nums;
    display: inline-block;
    margin: 1px 2px;
    max-width: 100%;
    overflow-wrap: anywhere;
}
.badge-amber {
    background-color: rgba(251, 191, 36, 0.10);
    color: #FBBF24;
    border: 1px solid rgba(251, 191, 36, 0.35);
    padding: 2px 7px;
    border-radius: 4px;
    font-size: 0.72rem;
    font-weight: 700;
    font-family: Inter, -apple-system, BlinkMacSystemFont, sans-serif; font-variant-numeric: tabular-nums;
    display: inline-block;
    margin: 1px 2px;
    max-width: 100%;
    overflow-wrap: anywhere;
}
.badge-sage {
    background-color: rgba(148, 163, 184, 0.12);
    color: #E2E8F0;
    border: 1px solid #475569;
    padding: 2px 7px;
    border-radius: 4px;
    font-size: 0.72rem;
    font-weight: 600;
    font-family: Inter, -apple-system, BlinkMacSystemFont, sans-serif; font-variant-numeric: tabular-nums;
    display: inline-block;
    margin: 1px 2px;
    max-width: 100%;
    overflow-wrap: anywhere;
}
.badge-hot {
    background-color: rgba(52, 211, 153, 0.12);
    color: #34D399;
    border: 1px solid rgba(52, 211, 153, 0.40);
    padding: 2px 7px;
    border-radius: 4px;
    font-size: 0.72rem;
    font-weight: 700;
    font-family: Inter, -apple-system, BlinkMacSystemFont, sans-serif; font-variant-numeric: tabular-nums;
    display: inline-block;
    margin: 1px 2px;
    max-width: 100%;
    overflow-wrap: anywhere;
}
.badge-cold {
    background-color: rgba(148, 163, 184, 0.10);
    color: #94A3B8;
    border: 1px solid #475569;
    padding: 2px 7px;
    border-radius: 4px;
    font-size: 0.72rem;
    font-weight: 600;
    font-family: Inter, -apple-system, BlinkMacSystemFont, sans-serif; font-variant-numeric: tabular-nums;
    display: inline-block;
    margin: 1px 2px;
    max-width: 100%;
    overflow-wrap: anywhere;
}
.team-pill {
    background-color: #18202F;
    color: #F1F5F9;
    border: 1px solid #2E3A4F;
    padding: 2px 9px;
    border-radius: 6px;
    font-size: 0.82rem;
    font-weight: 700;
    font-family: Inter, -apple-system, BlinkMacSystemFont, sans-serif; font-variant-numeric: tabular-nums;
    display: inline-flex;
    align-items: center;
    gap: 6px;
    margin: 0 3px;
}
.team-pill-lg {
    background-color: #161F2E;
    color: #F8FAFC;
    border: 1px solid #2E3D52;
    padding: 5px 12px;
    border-radius: 8px;
    font-size: 1.18rem;
    font-weight: 800;
    font-family: Inter, -apple-system, BlinkMacSystemFont, sans-serif; font-variant-numeric: tabular-nums;
    display: inline-flex;
    align-items: center;
    gap: 8px;
    margin: 0 4px;
}
.metric-subtext {
    font-size: 0.79rem;
    color: #94A3B8;
    font-family: Inter, -apple-system, BlinkMacSystemFont, sans-serif; font-variant-numeric: tabular-nums;
    overflow-wrap: break-word;
    word-break: break-word;
}

/* Team-Owned Unit Tier Matrix Pillars */
.brief-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 10px;
    margin-bottom: 10px;
}
.unit-pillar {
    background-color: #151B26;
    border: 1px solid #232C3D;
    border-radius: 7px;
    padding: 10px 12px;
    min-width: 0;
}
.unit-pillar-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    flex-wrap: wrap;
    gap: 4px;
    border-bottom: 1px solid #232C3D;
    padding-bottom: 6px;
    margin-bottom: 6px;
    font-weight: 700;
    font-size: 0.88rem;
    color: #F1F5F9;
}
.unit-section-tag {
    font-size: 0.66rem;
    font-family: Inter, -apple-system, BlinkMacSystemFont, sans-serif; font-variant-numeric: tabular-nums;
    font-weight: 700;
    color: #94A3B8;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    margin: 6px 0 2px 0;
}
.unit-tier-row {
    display: flex;
    justify-content: space-between;
    align-items: center;
    flex-wrap: wrap;
    gap: 4px;
    padding: 6px 0;
    font-size: 0.82rem;
    border-bottom: 1px solid rgba(255, 255, 255, 0.06);
}
.unit-tier-label {
    color: #CBD5E1;
    font-family: Inter, -apple-system, BlinkMacSystemFont, sans-serif; font-variant-numeric: tabular-nums;
    font-weight: 600;
    font-size: 0.76rem;
}
.unit-tier-right {
    display: flex;
    align-items: center;
    gap: 6px;
    flex-wrap: wrap;
}
.unit-epa-mini {
    font-family: Inter, -apple-system, BlinkMacSystemFont, sans-serif; font-variant-numeric: tabular-nums;
    font-size: 0.74rem;
    color: #94A3B8;
}
.unit-lever-footer {
    margin-top: 8px;
    padding-top: 4px;
    font-size: 0.78rem;
    color: #E2E8F0;
    display: flex;
    justify-content: space-between;
    align-items: center;
    flex-wrap: wrap;
    gap: 4px;
}

/* Compact Non-Clipping EPA Comparison Stat Grid (Unit EPA Tab) */
.epa-stat-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 8px;
    margin: 8px 0 6px 0;
}
.epa-stat-box {
    background-color: #151C28;
    border: 1px solid #232D3F;
    border-radius: 6px;
    padding: 8px 10px;
    min-width: 0;
}
.epa-stat-label {
    font-size: 0.73rem;
    font-family: Inter, -apple-system, BlinkMacSystemFont, sans-serif; font-variant-numeric: tabular-nums;
    color: #94A3B8;
    margin-bottom: 3px;
    white-space: normal;
    line-height: 1.25;
}
.epa-stat-num {
    font-size: 1.32rem;
    font-weight: 800;
    font-family: Inter, -apple-system, BlinkMacSystemFont, sans-serif; font-variant-numeric: tabular-nums;
    color: #F8FAFC;
    line-height: 1.2;
    margin-bottom: 5px;
    white-space: nowrap;
}

/* ============================================================================
   CUSTOM TEAM-COLORED DIVISIONAL STANDINGS & 5-YEAR H2H CARDS
   ============================================================================ */
.nfl-div-card {
    background: transparent;
    border: none;
    border-radius: 0;
    padding: 2px 0;
    margin-bottom: 12px;
    color: #E2E8F0;
    max-width: 100%;
    overflow-x: auto;
}
a.depth-chart-link-btn,
a.depth-chart-link-btn:visited {
    display: inline-flex;
    align-items: center;
    gap: 4px;
    font-family: Inter, -apple-system, BlinkMacSystemFont, sans-serif; font-variant-numeric: tabular-nums;
    font-size: 0.69rem;
    font-weight: 800;
    letter-spacing: 0.03em;
    padding: 2px 8px;
    border-radius: 4px;
    border: 1px solid #475569;
    background-color: rgba(148, 163, 184, 0.14);
    color: #F8FAFC !important;
    text-decoration: none !important;
    transition: all 0.14s ease-in-out;
}
a.depth-chart-link-btn:hover {
    filter: brightness(1.2);
    transform: translateY(-1px);
    box-shadow: 0 2px 6px rgba(0, 0, 0, 0.35);
}
.nfl-div-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    flex-wrap: wrap;
    gap: 8px;
    padding-bottom: 8px;
    margin-bottom: 8px;
    border-bottom: 1px solid #232D3F;
}
.nfl-div-title {
    font-family: Inter, -apple-system, BlinkMacSystemFont, sans-serif; font-variant-numeric: tabular-nums;
    font-size: 0.95rem;
    font-weight: 800;
    letter-spacing: 0.04em;
    color: #F8FAFC;
    text-transform: uppercase;
    display: flex;
    align-items: center;
    gap: 8px;
}
.div-team-strip {
    display: flex;
    flex-direction: column;
    gap: 5px;
    padding: 9px 11px;
    margin-bottom: 7px;
    border-radius: 7px;
    background-color: #151C28;
    border: 1px solid #232D3F;
    font-family: Inter, -apple-system, BlinkMacSystemFont, sans-serif; font-variant-numeric: tabular-nums;
}
.div-team-strip-top {
    display: flex;
    justify-content: space-between;
    align-items: center;
    flex-wrap: wrap;
    gap: 8px;
}
.div-team-strip-metrics {
    display: flex;
    align-items: center;
    justify-content: space-between;
    flex-wrap: wrap;
    gap: 8px;
    font-size: 0.73rem;
    color: #CBD5E1;
}
.nfl-rank-pill {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    width: 24px;
    height: 21px;
    border-radius: 4px;
    font-size: 0.72rem;
    font-weight: 800;
    background-color: #1A2333;
    color: #94A3B8;
    border: 1px solid #2B384E;
}
.nfl-rank-pill-1 {
    background-color: rgba(52, 211, 153, 0.14);
    color: #34D399;
    border: 1px solid rgba(52, 211, 153, 0.40);
}
.h2h-game-card {
    border-radius: 8px;
    padding: 10px 14px;
    margin-bottom: 8px;
    font-family: Inter, -apple-system, BlinkMacSystemFont, sans-serif; font-variant-numeric: tabular-nums;
    display: flex;
    flex-direction: column;
    gap: 6px;
}

/* Uniform Top-Level & Sub-Level Tabs Styling */
div[data-testid="stDataFrame"],
div[data-testid="stTable"],
.stPlotlyChart {
    max-width: 100% !important;
    overflow-x: auto !important;
    -webkit-overflow-scrolling: touch !important;
}
div[data-baseweb="tab-list"] {
    overflow-x: auto !important;
    overflow-y: hidden !important;
    flex-wrap: nowrap !important;
    white-space: nowrap !important;
    scrollbar-width: thin;
    -webkit-overflow-scrolling: touch;
    gap: 6px !important;
    background-color: #0E131D !important;
    padding: 6px 8px !important;
    border-radius: 8px !important;
    border: 1px solid #1E293B !important;
}
button[data-baseweb="tab"] {
    flex-shrink: 0 !important;
    white-space: nowrap !important;
    font-family: Inter, -apple-system, BlinkMacSystemFont, sans-serif !important; font-variant-numeric: tabular-nums !important;
    font-weight: 700 !important;
    font-size: 0.84rem !important;
    padding: 8px 16px !important;
    border-radius: 6px !important;
}

/* ============================================================================
   MOBILE & TABLET RESPONSIVE MEDIA QUERIES (MAX-WIDTH: 768PX & 480PX)
   ============================================================================ */
/* Flat Modern Card Containers */
div[data-testid="stVerticalBlockBorderWrapper"] {
    background-color: #141923 !important;
    border: 1px solid rgba(255, 255, 255, 0.08) !important;
    border-radius: 10px !important;
    padding: 12px 14px !important;
}

@media (max-width: 768px) {
    .stApp, .main {
        max-width: 100vw !important;
        overflow-x: hidden !important;
    }
    .block-container {
        padding-left: 0.45rem !important;
        padding-right: 0.45rem !important;
        padding-top: 0.85rem !important;
        padding-bottom: 4.5rem !important;
        max-width: 100vw !important;
        width: 100vw !important;
    }
    div[data-testid="stVerticalBlockBorderWrapper"] {
        padding: 10px 11px !important;
        border-radius: 10px !important;
        margin-bottom: 6px !important;
        width: 100% !important;
    }
    div[data-testid="stHorizontalBlock"]:not(:has(.nfl-ticker-marker)):not(:has(.compact-bet-pill)) {
        flex-direction: column !important;
        flex-wrap: nowrap !important;
        gap: 0.5rem !important;
        width: 100% !important;
    }
    div[data-testid="stHorizontalBlock"]:not(:has(.nfl-ticker-marker)):not(:has(.compact-bet-pill)) > div[data-testid="stColumn"],
    div[data-testid="stHorizontalBlock"]:not(:has(.nfl-ticker-marker)):not(:has(.compact-bet-pill)) > div[data-testid="column"] {
        width: 100% !important;
        min-width: 100% !important;
        max-width: 100% !important;
        flex: 1 1 100% !important;
    }
    div[data-testid="stHorizontalBlock"]:has(.nfl-ticker-marker) {
        flex-direction: row !important;
        flex-wrap: nowrap !important;
        overflow-x: auto !important;
        gap: 8px !important;
        padding: 8px 6px 10px 6px !important;
        margin-left: -2px !important;
        margin-right: -2px !important;
    }
    div[data-testid="stHorizontalBlock"]:has(.nfl-ticker-marker) > div[data-testid="stColumn"],
    div[data-testid="stHorizontalBlock"]:has(.nfl-ticker-marker) > div[data-testid="column"] {
        flex: 0 0 168px !important;
        min-width: 168px !important;
        max-width: 168px !important;
        width: 168px !important;
    }
    .brief-grid,
    .promoted-context-strip {
        grid-template-columns: 1fr !important;
        gap: 8px !important;
    }
    .custom-kpi-grid {
        grid-template-columns: 1fr !important;
        gap: 8px !important;
    }
    .custom-kpi-card {
        padding: 12px 14px !important;
        border-radius: 10px !important;
        width: 100% !important;
    }
    .custom-kpi-val {
        font-size: 1.24rem !important;
    }
    .cross-unit-row,
    .div-team-strip,
    .h2h-game-card,
    .terminal-card,
    .terminal-card-elite,
    .terminal-card-vuln {
        width: 100% !important;
        padding: 11px 12px !important;
        border-radius: 10px !important;
        margin-bottom: 8px !important;
    }
    div[data-baseweb="tab-list"] {
        gap: 4px !important;
        padding: 5px 6px !important;
        border-radius: 10px !important;
        width: 100% !important;
    }
    button[data-baseweb="tab"] {
        font-size: 0.80rem !important;
        padding: 8px 12px !important;
        border-radius: 7px !important;
    }
    div[data-testid="stButton"] > button {
        min-height: 42px !important;
    }
    .epa-stat-num {
        font-size: 1.12rem !important;
    }
    .epa-stat-box {
        padding: 8px 10px !important;
    }
    .active-game-spotlight {
        padding: 12px 12px !important;
        border-radius: 10px !important;
    }
    .team-pill-lg {
        font-size: 1.0rem !important;
        padding: 4px 10px !important;
        margin: 2px 2px !important;
    }
    .team-pill {
        font-size: 0.78rem !important;
        padding: 2px 8px !important;
    }
    .cb-wr-vs-divider {
        padding: 4px 0 !important;
        margin: 2px 0 !important;
        text-align: left !important;
        font-size: 0.75rem !important;
        border-top: 1px solid rgba(255, 255, 255, 0.06);
        border-bottom: 1px solid rgba(255, 255, 255, 0.06);
    }
}

@media (max-width: 480px) {
    .custom-kpi-grid {
        grid-template-columns: 1fr !important;
    }
}
</style>
""",
    unsafe_allow_html=True,
)

# Zero-reload JavaScript interceptor for any inline <a class="player-name-link"> tags
components.html(
    """
    <script>
    (function() {
        const parentDoc = window.parent.document;
        if (!parentDoc._playerLinkListenerAttached) {
            parentDoc._playerLinkListenerAttached = true;
            parentDoc.addEventListener('click', function(e) {
                const link = e.target.closest('a.player-name-link');
                if (link && link.getAttribute('href')) {
                    e.preventDefault();
                    e.stopPropagation();
                    const href = link.getAttribute('href');
                    const url = new URL(href, window.parent.location.origin + window.parent.location.pathname);
                    window.parent.history.pushState({}, '', url.toString());
                    window.parent.dispatchEvent(new PopStateEvent('popstate'));
                }
            }, true);
        }
    })();
    </script>
    """,
    height=0,
    width=0,
)

OFFENSE_POSITIONS = {"QB", "RB", "FB", "WR", "TE", "OL", "T", "OT", "LT", "RT", "G", "OG", "LG", "RG", "C"}
DEFENSE_POSITIONS = {"DL", "DE", "DT", "NT", "EDGE", "LB", "ILB", "OLB", "MLB", "DB", "CB", "S", "FS", "SS"}
SPECIAL_TEAMS_POSITIONS = {"K", "P", "LS"}

UNAVAILABLE_DESIGNATIONS = {"OUT", "DOUBTFUL", "IR", "PUP", "SUSPENDED", "NFI"}
UNCONFIRMED_NON_FULL_PRACTICE_DESIGNATIONS = {
    "UNSPECIFIED (DNP)",
    "UNSPECIFIED (LP)",
    "UNCONFIRMED (DNP)",
    "UNCONFIRMED (LP)",
}
CB_WR_REMOVED_DESIGNATIONS = UNAVAILABLE_DESIGNATIONS | UNCONFIRMED_NON_FULL_PRACTICE_DESIGNATIONS

ACTIVE_INJURY_DESIGNATIONS = {
    "OUT",
    "DOUBTFUL",
    "QUESTIONABLE",
    "IR",
    "PUP",
    "SUSPENDED",
    "NFI",
    "UNSPECIFIED (DNP)",
    "UNSPECIFIED (LP)",
}
CLEARED_DESIGNATIONS = {
    "ACTIVE",
    "CLEARED",
    "ACTIVE / CLEARED",
    "ACTIVE / CLEAN REPORT",
    "FULL STRENGTH",
    "GOOD TO GO",
    "PROBABLE",
    "AVAILABLE",
    "UNSPECIFIED (FP)",
}

# Official NFL 8-Division Structure & Full Team Names (NFL.com Standard)
NFL_DIVISIONS: dict[str, list[str]] = {
    "AFC East": ["BUF", "MIA", "NE", "NYJ"],
    "AFC North": ["BAL", "CIN", "CLE", "PIT"],
    "AFC South": ["HOU", "IND", "JAX", "TEN"],
    "AFC West": ["DEN", "KC", "LAC", "LV"],
    "NFC East": ["DAL", "NYG", "PHI", "WAS"],
    "NFC North": ["CHI", "DET", "GB", "MIN"],
    "NFC South": ["ATL", "CAR", "NO", "TB"],
    "NFC West": ["ARI", "LAR", "SEA", "SF"],
}

NFL_TEAM_NAMES: dict[str, str] = {
    "ARI": "Cardinals",
    "ATL": "Falcons",
    "BAL": "Ravens",
    "BUF": "Bills",
    "CAR": "Panthers",
    "CHI": "Bears",
    "CIN": "Bengals",
    "CLE": "Browns",
    "DAL": "Cowboys",
    "DEN": "Broncos",
    "DET": "Lions",
    "GB": "Packers",
    "HOU": "Texans",
    "IND": "Colts",
    "JAX": "Jaguars",
    "KC": "Chiefs",
    "LA": "Rams",
    "LAR": "Rams",
    "LAC": "Chargers",
    "LV": "Raiders",
    "MIA": "Dolphins",
    "MIN": "Vikings",
    "NE": "Patriots",
    "NO": "Saints",
    "NYG": "Giants",
    "NYJ": "Jets",
    "PHI": "Eagles",
    "PIT": "Steelers",
    "SEA": "Seahawks",
    "SF": "49ers",
    "TB": "Buccaneers",
    "TEN": "Titans",
    "WAS": "Commanders",
    "WSH": "Commanders",
}

TEAM_TO_DIVISION: dict[str, str] = {}
TEAM_TO_CONFERENCE: dict[str, str] = {}
for _div_name, _div_teams in NFL_DIVISIONS.items():
    _conf = _div_name.split()[0]
    for _tm in _div_teams:
        TEAM_TO_DIVISION[_tm] = _div_name
        TEAM_TO_CONFERENCE[_tm] = _conf
TEAM_TO_DIVISION["LA"] = "NFC West"
TEAM_TO_CONFERENCE["LA"] = "NFC"
TEAM_TO_DIVISION["WSH"] = "NFC East"
TEAM_TO_CONFERENCE["WSH"] = "NFC"

# Official 32-Team NFL Franchise Depth Chart URLs (Opens in New Browser Tab)
NFL_OFFICIAL_DEPTH_CHART_URLS: dict[str, str] = {
    "ARI": "https://www.azcardinals.com/team/depth-chart",
    "ATL": "https://www.atlantafalcons.com/team/depth-chart",
    "BAL": "https://www.baltimoreravens.com/team/depth-chart",
    "BUF": "https://www.buffalobills.com/team/depth-chart",
    "CAR": "https://www.panthers.com/team/depth-chart",
    "CHI": "https://www.chicagobears.com/team/depth-chart",
    "CIN": "https://www.bengals.com/team/depth-chart",
    "CLE": "https://www.clevelandbrowns.com/team/depth-chart",
    "DAL": "https://www.dallascowboys.com/team/depth-chart",
    "DEN": "https://www.denverbroncos.com/team/depth-chart",
    "DET": "https://www.detroitlions.com/team/depth-chart",
    "GB": "https://www.packers.com/team/depth-chart",
    "HOU": "https://www.houstontexans.com/team/depth-chart",
    "IND": "https://www.colts.com/team/depth-chart",
    "JAX": "https://www.jaguars.com/team/depth-chart",
    "KC": "https://www.chiefs.com/team/depth-chart",
    "LA": "https://www.therams.com/team/depth-chart",
    "LAR": "https://www.therams.com/team/depth-chart",
    "LAC": "https://www.chargers.com/team/depth-chart",
    "LV": "https://www.raiders.com/team/depth-chart",
    "MIA": "https://www.miamidolphins.com/team/depth-chart",
    "MIN": "https://www.vikings.com/team/depth-chart",
    "NE": "https://www.patriots.com/team/depth-chart",
    "NO": "https://www.neworleanssaints.com/team/depth-chart",
    "NYG": "https://www.giants.com/team/depth-chart",
    "NYJ": "https://www.newyorkjets.com/team/depth-chart",
    "PHI": "https://www.philadelphiaeagles.com/team/depth-chart",
    "PIT": "https://www.steelers.com/team/depth-chart",
    "SEA": "https://www.seahawks.com/team/depth-chart",
    "SF": "https://www.49ers.com/team/depth-chart",
    "TB": "https://www.buccaneers.com/team/depth-chart",
    "TEN": "https://www.tennesseetitans.com/team/depth-chart",
    "WAS": "https://www.commanders.com/team/depth-chart",
    "WSH": "https://www.commanders.com/team/depth-chart",
}


def get_team_depth_chart_url(team_abbr: str) -> str:
    """Returns the official NFL franchise depth chart URL for a given team."""
    clean = str(team_abbr).strip().upper()
    return NFL_OFFICIAL_DEPTH_CHART_URLS.get(clean, "https://www.nfl.com/teams/")


def normalize_guard_position(
    pos_val: str,
    depth_pos_val: str = "",
    player_name: str = "",
    team_abbr: str = "",
    slot_idx: int | None = None,
) -> str:
    """
    Ensures offensive guards are labeled specifically as LG or RG rather than generic G / OG.
    Uses official depth_chart_position when available, and deterministically assigns LG / RG otherwise.
    """
    pos = str(pos_val or "").strip().upper()
    d_pos = str(depth_pos_val or "").strip().upper()
    if d_pos in ("LG", "RG"):
        return d_pos
    if pos in ("LG", "RG"):
        return pos
    if pos in ("G", "OG") or d_pos in ("G", "OG"):
        if slot_idx is not None:
            return "LG" if (slot_idx % 2 == 0) else "RG"
        seed_str = f"{str(team_abbr).strip().upper()}|{str(player_name).strip().lower()}"
        h_val = sum((i + 1) * ord(ch) for i, ch in enumerate(seed_str))
        return "LG" if (h_val % 2 == 0) else "RG"
    return pos


def normalize_dataframe_guard_positions(
    df: pd.DataFrame,
    pos_col: str = "position",
    name_col: str = "player_name",
) -> pd.DataFrame:
    """
    Normalizes any generic G / OG positions in a DataFrame into specific LG or RG designations,
    respecting depth_chart_position first and alternating LG/RG across guards on each team.
    """
    if df.empty or pos_col not in df.columns:
        return df
    df = df.copy()
    raw_pos = df[pos_col].fillna("").astype(str).str.strip().str.upper()
    depth_col = "depth_chart_position" if "depth_chart_position" in df.columns else None
    if depth_col:
        d_series = df[depth_col].fillna("").astype(str).str.strip().str.upper()
        raw_pos = np.where(
            raw_pos.isin(["G", "OG", "OL"]) & d_series.isin(["LG", "RG"]),
            d_series,
            raw_pos,
        )
        raw_pos = pd.Series(raw_pos, index=df.index)

    guard_mask = raw_pos.isin(["G", "OG"])
    if guard_mask.any():
        actual_name_col = name_col if name_col in df.columns else (
            "full_name" if "full_name" in df.columns else (
                "player" if "player" in df.columns else (
                    "player_display" if "player_display" in df.columns else None
                )
            )
        )
        team_col = "team" if "team" in df.columns else None
        team_guard_map: dict[tuple[str, str], str] = {}
        team_counters: dict[str, int] = {}
        new_pos_list = list(raw_pos)
        for idx_i, is_g in enumerate(guard_mask):
            if not is_g:
                continue
            row_i = df.iloc[idx_i]
            tm_i = str(row_i[team_col]).strip().upper() if team_col else "NFL"
            nm_i = str(row_i[actual_name_col]).strip().lower() if actual_name_col else str(idx_i)
            key_i = (tm_i, nm_i)
            if key_i not in team_guard_map:
                cnt = team_counters.get(tm_i, 0)
                team_guard_map[key_i] = "LG" if (cnt % 2 == 0) else "RG"
                team_counters[tm_i] = cnt + 1
            new_pos_list[idx_i] = team_guard_map[key_i]
        df[pos_col] = new_pos_list
    else:
        df[pos_col] = raw_pos
    return df
if "injury_refresh_token" not in st.session_state:
    st.session_state["injury_refresh_token"] = 0
if "bet_slip" not in st.session_state:
    st.session_state["bet_slip"] = []
if "default_odds_american" not in st.session_state:
    st.session_state["default_odds_american"] = -110
if "kelly_fraction_mult" not in st.session_state:
    st.session_state["kelly_fraction_mult"] = 0.25
if "top_workspace_section" not in st.session_state:
    st.session_state["top_workspace_section"] = "Current Matchup"
if "open_props_slip_modal" not in st.session_state:
    st.session_state["open_props_slip_modal"] = False
if "active_pick_focus" not in st.session_state:
    st.session_state["active_pick_focus"] = None

PROP_MARKETS = {
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


def render_html(html_str: str) -> None:
    """
    Safely renders custom HTML blocks in Streamlit by stripping leading line whitespace
    so Markdown's 4-space code-block parser never leaks raw <span> or <div> tags.
    """
    cleaned = "\n".join(line.lstrip() for line in html_str.strip().splitlines())
    st.markdown(cleaned, unsafe_allow_html=True)


# -----------------------------------------------------------------------------
# ANALYTICS HELPERS: ODDS, KELLY CRITERION, FAIR SPREAD, SPARKBARS, BET SLIP
# -----------------------------------------------------------------------------
def american_odds_to_decimal_and_prob(american_odds: int) -> tuple[float, float]:
    """Converts American odds (e.g. -110, +115) into (decimal_odds, breakeven_prob)."""
    if american_odds < 0:
        dec = 1.0 + (100.0 / abs(float(american_odds)))
        imp = abs(float(american_odds)) / (abs(float(american_odds)) + 100.0)
    else:
        dec = 1.0 + (float(american_odds) / 100.0)
        imp = 100.0 / (float(american_odds) + 100.0)
    return dec, imp


def prob_to_fair_american_odds(prob: float) -> int:
    """Converts a win probability (0..1) into fair no-vig American odds."""
    p = float(np.clip(prob, 0.02, 0.98))
    if p >= 0.5:
        return int(round(-100.0 * p / (1.0 - p)))
    return int(round(100.0 * (1.0 - p) / p))


def compute_ev_and_kelly(
    win_prob: float,
    american_odds: int = -110,
    kelly_fraction: float = 0.25,
) -> tuple[float, float]:
    """
    Computes Expected Value percentage (+EV%) and recommended stake in units
    using fractional Kelly Criterion (assuming 1 unit = 1% bankroll standard).
    """
    dec_odds, _ = american_odds_to_decimal_and_prob(american_odds)
    b = dec_odds - 1.0
    p = float(np.clip(win_prob, 0.01, 0.99))
    q = 1.0 - p
    ev_pct = ((p * b) - q) * 100.0
    raw_kelly = ((b * p) - q) / b if b > 0 else 0.0
    kelly_units = max(0.0, raw_kelly * kelly_fraction * 100.0)
    return round(ev_pct, 1), round(min(kelly_units, 5.0), 2)


def make_pick_id(season: int, week: int, matchup: str, category: str, selection: str) -> str:
    """Builds a deterministic unique pick_id for Bet Slip deduplication and toggling."""
    return f"{season}_W{week}_{matchup}_{category}_{selection}"


def is_pick_in_bet_slip(pick_id: str) -> bool:
    """Checks if a pick_id is currently tracked in st.session_state['bet_slip']."""
    return any(item.get("pick_id") == pick_id for item in st.session_state.get("bet_slip", []))


def toggle_pick_in_bet_slip(
    season: int,
    week: int,
    matchup: str,
    category: str,
    selection: str,
    market_line: str,
    model_proj: str,
    american_odds: int,
    edge_score: float,
    ev_pct: float,
    kelly_units: float,
    team_abbr: str = "",
    outcome_status: str = "PENDING",
) -> bool:
    """
    Toggles a bet in st.session_state['bet_slip'].
    Returns True if added, False if removed.
    """
    pick_id = make_pick_id(season, week, matchup, category, selection)
    existing_list = st.session_state.get("bet_slip", [])
    for idx, existing in enumerate(existing_list):
        if existing.get("pick_id") == pick_id:
            existing_list.pop(idx)
            st.session_state["bet_slip"] = existing_list
            return False

    st.session_state["bet_slip"].append(
        {
            "pick_id": pick_id,
            "Season": season,
            "Week": week,
            "Matchup": matchup,
            "Team": team_abbr,
            "Market Type": category,
            "Selection": selection,
            "Book Line": market_line,
            "Model Projection": model_proj,
            "Odds": f"{int(american_odds):+d}",
            "Edge Score": round(edge_score, 1),
            "EV %": round(ev_pct, 1),
            "Kelly Stake (u)": round(kelly_units, 2),
            "Result": outcome_status,
        }
    )
    return True


def trigger_props_slip_popup(
    focus_category: str = "",
    focus_selection: str = "",
    focus_team: str = "",
    focus_player: str = "",
) -> None:
    """Opens the unified Underdog-style Matchup Picks, Prop Explorer & Bet Slip modal."""
    st.session_state["active_pick_focus"] = {
        "category": focus_category,
        "selection": focus_selection,
        "team": focus_team,
        "player": focus_player,
    }
    st.session_state["open_player_modal"] = False
    st.session_state["open_props_slip_modal"] = True


def render_compact_bet_action_row(
    key_prefix: str,
    season: int,
    week: int,
    matchup: str,
    category: str,
    selection: str,
    market_line: str,
    model_proj: str,
    american_odds: int,
    edge_score: float,
    ev_pct: float,
    kelly_units: float,
    team_abbr: str = "",
    team_color_override: str = "",
    pill_label_html: str = "",
    open_matchup_modal_on_click: bool = False,
    focus_player: str = "",
    button_text_override: str = "",
) -> None:
    """
    Renders a clean, single-line hyperlinked pick button displaying ONLY the line
    (e.g., 'OVER 94.5 Rec Yds' or 'UNDER 94.5 Rec Yds' or 'GB -3.5') without word-salad
    player names, projections, EV%, or Kelly text cluttering the button.
    """
    pick_id = make_pick_id(season, week, matchup, category, selection)
    already_tracked = is_pick_in_bet_slip(pick_id)

    accent_hex = (
        team_color_override
        if team_color_override
        else (resolve_team_display_color(team_abbr) if team_abbr else "#38BDF8")
    )
    border_hex = "#34D399" if already_tracked else accent_hex
    bg_rgba = hex_to_rgba(border_hex, 0.20 if not already_tracked else 0.32)
    hover_rgba = hex_to_rgba(border_hex, 0.38)
    border_rgba = hex_to_rgba(border_hex, 0.80)

    clean_line_text = button_text_override.strip() if button_text_override else selection.strip()
    btn_label = f"✓ {clean_line_text}" if already_tracked else clean_line_text

    safe_cls = "pick-link-" + "".join(
        ch if ch.isalnum() else "-" for ch in f"{key_prefix}_{pick_id}"
    ).lower()

    render_html(
        f"""
        <style>
        div[data-testid="stElementContainer"]:has(.{safe_cls}) + div[data-testid="stElementContainer"] div[data-testid="stButton"] button,
        div.element-container:has(.{safe_cls}) + div.element-container div[data-testid="stButton"] button {{
            background-color: {bg_rgba} !important;
            border: 1.5px solid {border_rgba} !important;
            border-left: 4px solid {border_hex} !important;
            border-radius: 6px !important;
            padding: 6px 12px !important;
            min-height: 36px !important;
            height: auto !important;
            width: 100% !important;
            color: #F8FAFC !important;
            text-decoration: none !important;
            box-shadow: 0 2px 6px rgba(0, 0, 0, 0.28) !important;
            justify-content: center !important;
            text-align: center !important;
        }}
        div[data-testid="stElementContainer"]:has(.{safe_cls}) + div[data-testid="stElementContainer"] div[data-testid="stButton"] button p,
        div.element-container:has(.{safe_cls}) + div.element-container div[data-testid="stButton"] button p {{
            color: #F8FAFC !important;
            font-family: Inter, -apple-system, BlinkMacSystemFont, sans-serif !important; font-variant-numeric: tabular-nums !important;
            font-weight: 800 !important;
            font-size: 0.85rem !important;
            text-decoration: none !important;
            line-height: 1.25 !important;
            text-align: center !important;
        }}
        div[data-testid="stElementContainer"]:has(.{safe_cls}) + div[data-testid="stElementContainer"] div[data-testid="stButton"] button:hover,
        div.element-container:has(.{safe_cls}) + div.element-container div[data-testid="stButton"] button:hover {{
            background-color: {hover_rgba} !important;
            border-color: {border_hex} !important;
            color: #FFFFFF !important;
        }}
        </style>
        <span class="{safe_cls}" style="display:none;"></span>
        """
    )

    help_text = (
        f"Click to open Matchup Picks & Props board for {selection} ({matchup})"
        if open_matchup_modal_on_click
        else (
            f"Remove {selection} ({matchup}) from Bet Slip"
            if already_tracked
            else f"Add {selection} ({matchup} • {model_proj} • {ev_pct:+.1f}% EV • {kelly_units:.2f}u) to Bet Slip"
        )
    )

    if st.button(
        btn_label,
        key=f"pick_link_btn_{key_prefix}_{pick_id}",
        type="tertiary",
        help=help_text,
        use_container_width=True,
    ):
        if open_matchup_modal_on_click:
            trigger_props_slip_popup(
                focus_category=category,
                focus_selection=selection,
                focus_team=team_abbr,
                focus_player=focus_player,
            )
            st.rerun()
        else:
            added = toggle_pick_in_bet_slip(
                season=season,
                week=week,
                matchup=matchup,
                category=category,
                selection=selection,
                market_line=market_line,
                model_proj=model_proj,
                american_odds=american_odds,
                edge_score=edge_score,
                ev_pct=ev_pct,
                kelly_units=kelly_units,
                team_abbr=team_abbr,
            )
            if added:
                st.toast(f"Added {selection} ({matchup}) to Bet Slip")
            else:
                st.toast(f"Removed {selection} from Bet Slip")


def compute_model_fair_line_and_totals(
    a_eff: pd.Series,
    h_eff: pd.Series,
    away_off_pen: float,
    away_def_pen: float,
    home_off_pen: float,
    home_def_pen: float,
    away_tm: str,
    home_tm: str,
    market_home_spread: float = np.nan,
    market_total: float = np.nan,
    rest_edge_home: float = 0.0,
    roof_str: str = "Outdoors",
    wind_mph: float = 0.0,
    temp_f: float = 65.0,
) -> dict:
    """
    Translates team offensive/defensive EPA/play and active injury penalties into:
    - Model Fair Home Spread (negative = Home favored, positive = Away favored)
    - Spread Value Edge (points vs market spread)
    - Implied Away Score, Implied Home Score, and Model Fair Total
    - Model Win Probabilities (Away % and Home %)
    """
    adj_away_off = float(a_eff["off_epa"]) - away_off_pen
    adj_away_def = float(a_eff["def_epa"]) + away_def_pen
    adj_home_off = float(h_eff["off_epa"]) - home_off_pen
    adj_home_def = float(h_eff["def_epa"]) + home_def_pen

    away_expected_epa_per_play = (adj_away_off + adj_home_def) / 2.0
    home_expected_epa_per_play = (adj_home_off + adj_away_def) / 2.0

    plays_per_team = 63.0
    base_ppg = 22.2

    env_total_adj = 0.0
    if roof_str.lower() in ["dome", "closed"]:
        env_total_adj += 1.4
    if pd.notna(wind_mph) and wind_mph >= 15.0:
        env_total_adj -= min(4.5, (wind_mph - 12.0) * 0.35)
    if pd.notna(temp_f) and temp_f <= 32.0:
        env_total_adj -= 1.0

    rest_pts_home = float(np.clip(rest_edge_home * 0.35, -2.1, 2.1)) if pd.notna(rest_edge_home) else 0.0
    hfa_pts = 1.65

    raw_away_pts = base_ppg + (away_expected_epa_per_play * plays_per_team) - (hfa_pts / 2.0) - (rest_pts_home / 2.0) + (env_total_adj / 2.0)
    raw_home_pts = base_ppg + (home_expected_epa_per_play * plays_per_team) + (hfa_pts / 2.0) + (rest_pts_home / 2.0) + (env_total_adj / 2.0)

    away_proj_pts = float(np.clip(round(raw_away_pts, 1), 10.0, 42.0))
    home_proj_pts = float(np.clip(round(raw_home_pts, 1), 10.0, 42.0))

    fair_home_spread = round(away_proj_pts - home_proj_pts, 1)
    fair_total = round(away_proj_pts + home_proj_pts, 1)

    expected_home_margin = home_proj_pts - away_proj_pts
    home_win_prob = 0.5 * (1.0 + math.erf(expected_home_margin / (13.45 * math.sqrt(2.0))))
    home_win_prob = float(np.clip(home_win_prob, 0.05, 0.95))
    away_win_prob = 1.0 - home_win_prob

    if fair_home_spread < 0:
        fair_spread_str = f"{home_tm} {fair_home_spread:+.1f}"
    elif fair_home_spread > 0:
        fair_spread_str = f"{away_tm} {-fair_home_spread:+.1f}"
    else:
        fair_spread_str = "PK (Even)"

    spread_edge_pts = 0.0
    backed_spread_team = home_tm if fair_home_spread <= 0 else away_tm
    backed_spread_line_str = fair_spread_str
    spread_cover_prob = 0.524

    if pd.notna(market_home_spread):
        home_val_pts = float(market_home_spread) - fair_home_spread
        if home_val_pts >= 0:
            backed_spread_team = home_tm
            spread_edge_pts = round(home_val_pts, 1)
            backed_spread_line_str = f"{home_tm} {market_home_spread:+.1f}"
        else:
            backed_spread_team = away_tm
            spread_edge_pts = round(abs(home_val_pts), 1)
            backed_spread_line_str = f"{away_tm} {-market_home_spread:+.1f}"

        spread_cover_prob = 0.5 * (1.0 + math.erf(spread_edge_pts / (13.45 * math.sqrt(2.0))))
        spread_cover_prob = float(np.clip(spread_cover_prob, 0.50, 0.78))

    total_edge_pts = 0.0
    total_lean_dir = "OVER"
    total_hit_prob = 0.524
    if pd.notna(market_total):
        total_diff = fair_total - float(market_total)
        total_edge_pts = round(abs(total_diff), 1)
        total_lean_dir = "OVER" if total_diff >= 0 else "UNDER"
        total_hit_prob = 0.5 * (1.0 + math.erf(total_edge_pts / (13.8 * math.sqrt(2.0))))
        total_hit_prob = float(np.clip(total_hit_prob, 0.50, 0.76))

    return {
        "away_proj_pts": away_proj_pts,
        "home_proj_pts": home_proj_pts,
        "fair_home_spread": fair_home_spread,
        "fair_spread_str": fair_spread_str,
        "fair_total": fair_total,
        "backed_spread_team": backed_spread_team,
        "backed_spread_line_str": backed_spread_line_str,
        "spread_edge_pts": spread_edge_pts,
        "spread_cover_prob": spread_cover_prob,
        "total_lean_dir": total_lean_dir,
        "total_edge_pts": total_edge_pts,
        "total_hit_prob": total_hit_prob,
        "away_win_prob": round(away_win_prob * 100.0, 1),
        "home_win_prob": round(home_win_prob * 100.0, 1),
        "away_win_prob_raw": away_win_prob,
        "home_win_prob_raw": home_win_prob,
    }


def render_l5_sparkbars_html(values: list[float], line_val: float) -> str:
    """Renders a compact 5-game mini vertical sparkbar strip colored by hit/miss vs line."""
    if not values:
        return '<span class="badge-mid">No L5 Logs</span>'
    last5 = values[-5:]
    max_v = max(max(last5), line_val, 1.0)
    cols_html = []
    for v in last5:
        hit = v >= line_val
        color = "#34D399" if hit else "#F87171"
        h_px = max(4, int(round((v / max_v) * 14)))
        v_str = f"{v:.0f}" if v >= 10 or v == int(v) else f"{v:.1f}"
        cols_html.append(
            f'<div class="l5-bar-col" title="Output: {v_str} (Line: {line_val})">'
            f'<div class="l5-bar-fill" style="height:{h_px}px; background:{color};"></div>'
            f'<span class="l5-bar-lbl">{v_str}</span>'
            f"</div>"
        )
    return f'<div class="l5-sparkbar-wrap" title="Last {len(last5)} Games vs {line_val} Line">{"".join(cols_html)}</div>'


def estimate_line_movement_and_splits(
    game_row: pd.Series,
    model_projection: dict,
    away_tm: str,
    home_tm: str,
) -> dict:
    """
    Computes opening-to-current spread/total movement and moneyline implied probabilities
    from schedule data and model-vs-market differentials.
    """
    cur_sp = game_row.get("home_spread", np.nan)
    cur_tot = game_row.get("total_line", np.nan)
    away_ml = game_row.get("away_moneyline", np.nan)
    home_ml = game_row.get("home_moneyline", np.nan)

    fair_sp = model_projection.get("fair_home_spread", 0.0)
    if pd.notna(cur_sp):
        raw_drift = np.clip((cur_sp - fair_sp) * 0.35, -1.5, 1.5)
        open_sp = round((float(cur_sp) + raw_drift) * 2.0) / 2.0
        sp_move = float(cur_sp) - open_sp
        if open_sp <= 0:
            open_sp_str = f"{home_tm} {open_sp:+.1f}"
            open_fav_tm = home_tm
        else:
            open_sp_str = f"{away_tm} {-open_sp:+.1f}"
            open_fav_tm = away_tm

        if float(cur_sp) <= 0:
            cur_sp_str = f"{home_tm} {float(cur_sp):+.1f}"
            cur_fav_tm = home_tm
        else:
            cur_sp_str = f"{away_tm} {-float(cur_sp):+.1f}"
            cur_fav_tm = away_tm

        if sp_move < -0.2:
            move_tag = f"Steam toward {home_tm} ({sp_move:+.1f} pts)"
        elif sp_move > 0.2:
            move_tag = f"Steam toward {away_tm} ({-sp_move:+.1f} pts)"
        else:
            move_tag = "Anchored on Key Number"
    else:
        open_sp_str = "TBD"
        cur_sp_str = "TBD"
        open_fav_tm = home_tm
        cur_fav_tm = home_tm
        move_tag = "Line Pending"

    if pd.notna(cur_tot):
        fair_tot = model_projection.get("fair_total", float(cur_tot))
        tot_drift = np.clip((float(cur_tot) - fair_tot) * 0.3, -1.5, 1.5)
        open_tot = round((float(cur_tot) + tot_drift) * 2.0) / 2.0
        open_tot_str = f"{open_tot:.1f}"
        cur_tot_str = f"{float(cur_tot):.1f}"
    else:
        open_tot_str = "TBD"
        cur_tot_str = "TBD"

    if pd.notna(away_ml) and pd.notna(home_ml):
        away_ml_int = int(away_ml)
        home_ml_int = int(home_ml)
        _, a_imp = american_odds_to_decimal_and_prob(away_ml_int)
        _, h_imp = american_odds_to_decimal_and_prob(home_ml_int)
        vig_sum = a_imp + h_imp
        mkt_away_prob = round((a_imp / vig_sum) * 100.0, 1) if vig_sum > 0 else 50.0
        mkt_home_prob = round(100.0 - mkt_away_prob, 1)
        ml_str = f"{away_tm} {away_ml_int:+d} | {home_tm} {home_ml_int:+d}"
    else:
        mkt_home_prob = round(50.0 - (float(cur_sp) * 2.8 if pd.notna(cur_sp) else 0.0), 1)
        mkt_home_prob = float(np.clip(mkt_home_prob, 8.0, 92.0))
        mkt_away_prob = round(100.0 - mkt_home_prob, 1)
        away_ml_int = prob_to_fair_american_odds(min(0.95, (mkt_away_prob / 100.0) * 1.022))
        home_ml_int = prob_to_fair_american_odds(min(0.95, (mkt_home_prob / 100.0) * 1.022))
        ml_str = f"{away_tm} {away_ml_int:+d} | {home_tm} {home_ml_int:+d}"

    return {
        "open_sp_str": open_sp_str,
        "cur_sp_str": cur_sp_str,
        "open_fav_tm": open_fav_tm,
        "cur_fav_tm": cur_fav_tm,
        "move_tag": move_tag,
        "open_tot_str": open_tot_str,
        "cur_tot_str": cur_tot_str,
        "ml_str": ml_str,
        "away_ml_int": away_ml_int,
        "home_ml_int": home_ml_int,
        "mkt_away_prob": mkt_away_prob,
        "mkt_home_prob": mkt_home_prob,
    }


def trigger_player_popup(
    player_name: str,
    team_abbr: str = "",
    position: str = "",
) -> None:
    """Sets st.session_state['active_player'] and opens the player pop-out modal."""
    clean_p = str(player_name).strip()
    if not clean_p or "Rotation" in clean_p:
        return
    st.session_state["active_player"] = {
        "name": clean_p,
        "team": str(team_abbr).strip().upper(),
        "position": str(position).strip().upper(),
    }
    st.session_state["open_props_slip_modal"] = False
    st.session_state["open_player_modal"] = True


def render_player_link(player_name: str, team_abbr: str = "", pos: str = "") -> str:
    """Renders a clean inline hyperlinked player name inside HTML cards."""
    clean_p = str(player_name).strip()
    if not clean_p or "Rotation" in clean_p:
        return f"<b>{clean_p}</b>"
    active_gid = str(st.session_state.get("selected_game", ""))
    href = (
        f"?inspect_player={quote(clean_p)}"
        f"&inspect_team={quote(str(team_abbr).strip().upper())}"
        f"&inspect_pos={quote(str(pos).strip().upper())}"
        f"&game_id={quote(active_gid)}"
    )
    return f'<a class="player-name-link" href="{href}" target="_self">{clean_p}</a>'


def render_inline_player_trigger(
    player_name: str,
    team_abbr: str,
    pos: str,
    key_suffix: str,
    extra_label: str = "",
    color_override: str = "",
) -> None:
    """
    Renders a team-colored interactive player pill button that opens the Player Dossier modal.
    Uses a leaf-scoped sibling CSS selector so each player is strictly highlighted in their own team's color.
    """
    clean_p = str(player_name).strip()
    tm_clean = str(team_abbr).strip().upper()
    tm_hex = color_override if color_override else resolve_team_display_color(tm_clean)
    if not clean_p or "Rotation" in clean_p:
        render_html(
            f'<span style="display:inline-block; background:{hex_to_rgba(tm_hex, 0.16)}; border:1px solid {hex_to_rgba(tm_hex, 0.55)}; border-left:3px solid {tm_hex}; border-radius:6px; padding:3px 9px; font-family:Inter, -apple-system, BlinkMacSystemFont, sans-serif; font-variant-numeric:tabular-nums; font-size:0.84rem; font-weight:700; color:#F8FAFC;">'
            f"{clean_p} {extra_label}</span>"
        )
        return
    disp_text = f"{clean_p} {extra_label}".strip()
    safe_plr_cls = "plr-trig-" + "".join(ch if ch.isalnum() else "-" for ch in f"{key_suffix}_{clean_p}_{tm_clean}").lower()
    bg_rgba = hex_to_rgba(tm_hex, 0.18)
    hover_rgba = hex_to_rgba(tm_hex, 0.34)
    border_rgba = hex_to_rgba(tm_hex, 0.70)
    render_html(
        f"""
        <style>
        div[data-testid="stElementContainer"]:has(.{safe_plr_cls}) + div[data-testid="stElementContainer"] div[data-testid="stButton"] button,
        div.element-container:has(.{safe_plr_cls}) + div.element-container div[data-testid="stButton"] button {{
            background-color: {bg_rgba} !important;
            border: 1.5px solid {border_rgba} !important;
            border-left: 4px solid {tm_hex} !important;
            border-radius: 6px !important;
            padding: 4px 10px !important;
            min-height: 32px !important;
            height: auto !important;
            color: #F8FAFC !important;
            text-decoration: none !important;
            box-shadow: 0 1px 4px rgba(0, 0, 0, 0.25) !important;
        }}
        div[data-testid="stElementContainer"]:has(.{safe_plr_cls}) + div[data-testid="stElementContainer"] div[data-testid="stButton"] button p,
        div.element-container:has(.{safe_plr_cls}) + div.element-container div[data-testid="stButton"] button p {{
            text-decoration: none !important;
            color: #F8FAFC !important;
            font-family: Inter, -apple-system, BlinkMacSystemFont, sans-serif !important; font-variant-numeric: tabular-nums !important;
            font-weight: 700 !important;
            font-size: 0.85rem !important;
        }}
        div[data-testid="stElementContainer"]:has(.{safe_plr_cls}) + div[data-testid="stElementContainer"] div[data-testid="stButton"] button:hover,
        div.element-container:has(.{safe_plr_cls}) + div.element-container div[data-testid="stButton"] button:hover {{
            background-color: {hover_rgba} !important;
            border-color: {tm_hex} !important;
            color: #FFFFFF !important;
        }}
        </style>
        <span class="{safe_plr_cls}" style="display:none;"></span>
        """
    )
    if st.button(
        disp_text,
        key=f"inline_plr_{key_suffix}_{clean_p}_{tm_clean}",
        type="tertiary",
    ):
        trigger_player_popup(clean_p, tm_clean, pos)
        st.rerun()


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


def render_team_pill(
    team_abbr: str,
    role_tag: str = "",
    large: bool = False,
    color_override: str = "",
) -> str:
    """
    Renders an inline HTML team pill accented with the team's official NFL color
    (or an explicit matchup contrast override) and embedded logo.
    """
    logo = get_team_logo_url(team_abbr)
    cls = "team-pill-lg" if large else "team-pill"
    img_sz = 28 if large else 17
    tm_hex = color_override if color_override else resolve_team_display_color(team_abbr)
    bg_rgba = hex_to_rgba(tm_hex, 0.16)
    border_rgba = hex_to_rgba(tm_hex, 0.55)
    role_html = (
        f'<span style="color:#CBD5E1; font-size:0.75em; font-weight:600;">({role_tag})</span>'
        if role_tag
        else ""
    )
    return (
        f'<span class="{cls}" style="background:{bg_rgba}; border:1px solid {border_rgba}; border-left:4px solid {tm_hex};">'
        f'<img src="{logo}" width="{img_sz}" height="{img_sz}" style="vertical-align:middle;" onerror="this.style.display=\'none\'">'
        f"{team_abbr} {role_html}</span>"
    )


def render_rank_badge(rank: int, prefix: str = "") -> str:
    """
    Renders concise, flat unit ranking pills without bracket clutter:
    - Top 10 (1-10): Green (#X)
    - Bottom 10 (23-32): Red (#X)
    - Middle (11-22): Neutral (#X)
    """
    lbl = f"{prefix} " if prefix else ""
    if rank <= 10:
        return f'<span class="badge-elite">{lbl}#{rank}</span>'
    if rank >= 23:
        return f'<span class="badge-bad">{lbl}#{rank}</span>'
    return f'<span class="badge-mid">{lbl}#{rank}</span>'


def is_active_unresolved_injury(status_str: str) -> bool:
    """Returns True ONLY when a player's status is an active, unresolved injury designation."""
    if not status_str or pd.isna(status_str):
        return False
    s_clean = str(status_str).strip().upper()
    if s_clean in CLEARED_DESIGNATIONS or "CLEARED" in s_clean or "PLAYED" in s_clean:
        return False
    return s_clean in ACTIVE_INJURY_DESIGNATIONS


def is_unavailable_injury(status_str: str) -> bool:
    """Returns True ONLY when a player is ruled out or doubtful."""
    if not status_str or pd.isna(status_str):
        return False
    s_clean = str(status_str).strip().upper()
    if s_clean in CLEARED_DESIGNATIONS or "CLEARED" in s_clean or "PLAYED" in s_clean:
        return False
    return s_clean in UNAVAILABLE_DESIGNATIONS


def is_excluded_from_cb_wr_matchup(status_str: str, practice_status: str = "") -> bool:
    """
    Determines whether a player should be removed from the 1-on-1 CB vs. WR matchups:
    - Players ruled Out, Doubtful, IR, PUP, Suspended, or NFI are removed (True).
    - Players who are unconfirmed and DNP or LP are removed (True).
    - Players who logged Full Practice ('FP') remain in CB vs. WR matchups (False).
    """
    s_clean = "" if pd.isna(status_str) else str(status_str).strip().upper()
    p_clean = "" if pd.isna(practice_status) else str(practice_status).strip().upper()

    if not s_clean:
        if "FULL" in p_clean or p_clean == "FP":
            return False
        if "DID NOT" in p_clean or "DNP" in p_clean or "LIMITED" in p_clean or p_clean == "LP":
            return True
        return False

    if s_clean in CLEARED_DESIGNATIONS or "CLEARED" in s_clean or "PLAYED" in s_clean or "FP" in s_clean:
        return False

    if s_clean in CB_WR_REMOVED_DESIGNATIONS:
        return True

    if s_clean in {"UNSPECIFIED", "UNCONFIRMED"}:
        if "FULL" in p_clean or p_clean == "FP":
            return False
        return True

    return False


def extract_combined_injury_name(row: pd.Series) -> str:
    """Combines primary and secondary injury columns across report and practice feeds."""
    rep_p = str(row.get("report_primary_injury", "")).strip() if pd.notna(row.get("report_primary_injury")) else ""
    prac_p = str(row.get("practice_primary_injury", "")).strip() if pd.notna(row.get("practice_primary_injury")) else ""
    rep_s = str(row.get("report_secondary_injury", "")).strip() if pd.notna(row.get("report_secondary_injury")) else ""
    prac_s = str(row.get("practice_secondary_injury", "")).strip() if pd.notna(row.get("practice_secondary_injury")) else ""

    if rep_p.lower() in ["nan", "none", ""]:
        rep_p = ""
    if prac_p.lower() in ["nan", "none", ""]:
        prac_p = ""
    if rep_s.lower() in ["nan", "none", ""]:
        rep_s = ""
    if prac_s.lower() in ["nan", "none", ""]:
        prac_s = ""

    primary = rep_p or prac_p
    secondary = rep_s or prac_s

    if primary and secondary and secondary.lower() not in primary.lower():
        return f"{primary} / {secondary}"
    if primary:
        return primary
    return "Unspecified Injury"


def normalize_injury_designation(
    raw_status: str,
    practice_status: str = "",
) -> str:
    """Normalizes raw nflverse injury designations and practice participation."""
    if pd.isna(raw_status):
        s_clean = ""
    else:
        s_clean = str(raw_status).strip().upper()
        if s_clean in ["NAN", "NONE", "NULL", "--", "-", "UNSPECIFIED", "UNCONFIRMED"]:
            s_clean = ""

    p_clean = "" if pd.isna(practice_status) else str(practice_status).strip().upper()
    if p_clean in ["NAN", "NONE", "NULL", "--", "-"]:
        p_clean = ""

    if s_clean in ["ACTIVE", "CLEARED", "ACTIVE / CLEARED", "PROBABLE", "AVAILABLE", "GOOD TO GO"]:
        return "ACTIVE / CLEARED"
    if s_clean in ["OUT", "IR", "INJURED RESERVE", "PUP", "SUSPENDED", "NFI", "RESERVE"]:
        return "IR" if "IR" in s_clean or "RESERVE" in s_clean else s_clean
    if "DOUBT" in s_clean:
        return "DOUBTFUL"
    if "QUEST" in s_clean:
        return "QUESTIONABLE"

    if not s_clean:
        if "FULL" in p_clean or p_clean == "FP":
            return "UNSPECIFIED (FP)"
        if "LIMITED" in p_clean or p_clean == "LP":
            return "UNSPECIFIED (LP)"
        if "DID NOT" in p_clean or "DNP" in p_clean or not p_clean:
            return "UNSPECIFIED (DNP)"
        return "UNSPECIFIED (LP)"

    return s_clean


def render_injury_badge(status: str) -> str:
    """Renders a concise flat badge for official NFL injury report designations."""
    status_clean = str(status).strip().upper()
    if status_clean == "UNSPECIFIED (DNP)":
        return '<span class="badge-bad">DNP</span>'
    if status_clean == "UNSPECIFIED (LP)":
        return '<span class="badge-amber">LP</span>'
    if status_clean == "UNSPECIFIED (FP)":
        return '<span class="badge-elite">FP</span>'
    if status_clean in CLEARED_DESIGNATIONS or "CLEARED" in status_clean or "PLAYED" in status_clean:
        return '<span class="badge-elite">Cleared</span>'
    if status_clean in ["OUT", "IR", "PUP", "SUSPENDED", "NFI"]:
        return f'<span class="badge-bad">{status_clean.title() if len(status_clean) > 3 else status_clean}</span>'
    if status_clean == "DOUBTFUL":
        return '<span class="badge-bad">Doubtful</span>'
    if status_clean == "QUESTIONABLE":
        return '<span class="badge-amber">Questionable</span>'
    return f'<span class="badge-mid">{status_clean.title()}</span>'


def render_practice_badge(practice_status: str) -> str:
    """Renders a compact flat tag for weekly practice participation (FP, LP, DNP)."""
    if pd.isna(practice_status) or not str(practice_status).strip():
        return ""
    p_clean = str(practice_status).strip().upper()
    if p_clean in ["NAN", "NONE", "NULL", "UNSPECIFIED", "N/A"]:
        return ""
    if "FULL" in p_clean or p_clean == "FP":
        return '<span class="badge-elite">FP</span>'
    if "LIMITED" in p_clean or p_clean == "LP":
        return '<span class="badge-amber">LP</span>'
    if "DID NOT" in p_clean or "DNP" in p_clean:
        return '<span class="badge-bad">DNP</span>'
    return f'<span class="badge-mid">{p_clean}</span>'


def classify_primetime_code(row: pd.Series) -> str:
    """Detects compact broadcast tags (TNF, SNF, MNF, SPC)."""
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
        return "TNF"
    if "monday" in weekday:
        return "MNF"
    if "sunday" in weekday and hour >= 19:
        return "SNF"
    if "friday" in weekday or "saturday" in weekday or hour < 12:
        return "SPC"
    return ""


def render_slot_badge_html(slot_code: str) -> str:
    """Returns a clean, uniform slate badge for broadcast slots."""
    clean_slot = str(slot_code).strip("[]")
    if clean_slot in ["TNF", "SNF", "MNF", "SPC"]:
        return f'<span class="ticker-slot-tag">{clean_slot}</span>'
    return '<span class="ticker-score-muted">SUN</span>'


def normalize_team_code(team_abbr: str) -> str:
    """Normalizes team abbreviations to standard nflverse / NFL.com keys."""
    clean = str(team_abbr).strip().upper()
    if clean == "LA":
        return "LAR"
    if clean == "WSH":
        return "WAS"
    return clean


def get_team_division(team_abbr: str) -> str:
    """Returns the NFL division name for a given team abbreviation."""
    clean = normalize_team_code(team_abbr)
    return TEAM_TO_DIVISION.get(clean, "NFL Division")


def compute_team_records(
    schedule_df: pd.DataFrame, through_week: int | None = None
) -> dict[str, str]:
    """Dynamically computes each NFL team's season record up through the selected week."""
    records: dict[str, list[int]] = {}
    if schedule_df.empty:
        return {}

    for col in ["home_team", "away_team"]:
        if col in schedule_df.columns:
            for tm in schedule_df[col].dropna().unique():
                clean_tm = str(tm).strip().upper()
                if clean_tm not in records:
                    records[clean_tm] = [0, 0, 0]

    sub = schedule_df.copy()
    if through_week is not None and "week" in sub.columns:
        sub = sub[pd.to_numeric(sub["week"], errors="coerce").fillna(999) <= through_week]

    if {"home_score", "away_score"}.issubset(sub.columns):
        completed = sub[sub["home_score"].notna() & sub["away_score"].notna()]
        for _, r in completed.iterrows():
            ht = str(r["home_team"]).strip().upper()
            at = str(r["away_team"]).strip().upper()
            hs = float(r["home_score"])
            as_ = float(r["away_score"])

            if ht not in records:
                records[ht] = [0, 0, 0]
            if at not in records:
                records[at] = [0, 0, 0]

            if hs > as_:
                records[ht][0] += 1
                records[at][1] += 1
            elif as_ > hs:
                records[at][0] += 1
                records[ht][1] += 1
            else:
                records[ht][2] += 1
                records[at][2] += 1

    formatted: dict[str, str] = {}
    for tm, (w, l, t) in records.items():
        formatted[tm] = f"{w}-{l}-{t}" if t > 0 else f"{w}-{l}"

    return formatted


def compute_nfl_division_standings(
    schedule_df: pd.DataFrame, through_week: int | None = None
) -> dict[str, pd.DataFrame]:
    """Computes full NFL.com-style Divisional Standings across all 8 NFL divisions."""
    stats: dict[str, dict] = {}
    for div_name, div_teams in NFL_DIVISIONS.items():
        conf = div_name.split()[0]
        for tm in div_teams:
            stats[tm] = {
                "team": tm,
                "team_name": NFL_TEAM_NAMES.get(tm, tm),
                "division": div_name,
                "conference": conf,
                "w": 0,
                "l": 0,
                "t": 0,
                "pf": 0,
                "pa": 0,
                "home_w": 0,
                "home_l": 0,
                "home_t": 0,
                "road_w": 0,
                "road_l": 0,
                "road_t": 0,
                "div_w": 0,
                "div_l": 0,
                "div_t": 0,
                "conf_w": 0,
                "conf_l": 0,
                "conf_t": 0,
                "results_seq": [],
            }

    if not schedule_df.empty and {"home_team", "away_team", "home_score", "away_score"}.issubset(schedule_df.columns):
        sub = schedule_df.copy()
        if "game_type" in sub.columns:
            reg_sub = sub[sub["game_type"].astype(str).str.upper() == "REG"]
            if not reg_sub.empty:
                sub = reg_sub
        if through_week is not None and "week" in sub.columns:
            sub = sub[pd.to_numeric(sub["week"], errors="coerce").fillna(999) <= through_week]

        completed = sub[sub["home_score"].notna() & sub["away_score"].notna()].copy()
        if "week" in completed.columns:
            completed["week_num"] = pd.to_numeric(completed["week"], errors="coerce").fillna(1)
            completed = completed.sort_values(by=["week_num"])

        for _, r in completed.iterrows():
            ht = normalize_team_code(r["home_team"])
            at = normalize_team_code(r["away_team"])
            if ht not in stats or at not in stats:
                continue

            hs = int(round(float(r["home_score"])))
            as_ = int(round(float(r["away_score"])))

            stats[ht]["pf"] += hs
            stats[ht]["pa"] += as_
            stats[at]["pf"] += as_
            stats[at]["pa"] += hs

            same_div = stats[ht]["division"] == stats[at]["division"]
            same_conf = stats[ht]["conference"] == stats[at]["conference"]

            if hs > as_:
                stats[ht]["w"] += 1
                stats[ht]["home_w"] += 1
                stats[ht]["results_seq"].append("W")

                stats[at]["l"] += 1
                stats[at]["road_l"] += 1
                stats[at]["results_seq"].append("L")

                if same_div:
                    stats[ht]["div_w"] += 1
                    stats[at]["div_l"] += 1
                if same_conf:
                    stats[ht]["conf_w"] += 1
                    stats[at]["conf_l"] += 1
            elif as_ > hs:
                stats[at]["w"] += 1
                stats[at]["road_w"] += 1
                stats[at]["results_seq"].append("W")

                stats[ht]["l"] += 1
                stats[ht]["home_l"] += 1
                stats[ht]["results_seq"].append("L")

                if same_div:
                    stats[at]["div_w"] += 1
                    stats[ht]["div_l"] += 1
                if same_conf:
                    stats[at]["conf_w"] += 1
                    stats[ht]["conf_l"] += 1
            else:
                stats[ht]["t"] += 1
                stats[ht]["home_t"] += 1
                stats[ht]["results_seq"].append("T")

                stats[at]["t"] += 1
                stats[at]["road_t"] += 1
                stats[at]["results_seq"].append("T")

                if same_div:
                    stats[ht]["div_t"] += 1
                    stats[at]["div_t"] += 1
                if same_conf:
                    stats[ht]["conf_t"] += 1
                    stats[at]["conf_t"] += 1

    def _fmt_rec(w: int, l: int, t: int) -> str:
        return f"{w}-{l}-{t}" if t > 0 else f"{w}-{l}"

    def _fmt_pct(pct_val: float) -> str:
        if pct_val >= 0.9995:
            return "1.000"
        return f"{pct_val:.3f}"[1:]

    def _calc_streak(seq: list[str]) -> str:
        if not seq:
            return "-"
        last_res = seq[-1]
        cnt = 0
        for item in reversed(seq):
            if item == last_res:
                cnt += 1
            else:
                break
        return f"{last_res}{cnt}"

    def _calc_l5(seq: list[str]) -> str:
        last5 = seq[-5:]
        w5 = sum(1 for x in last5 if x == "W")
        l5 = sum(1 for x in last5 if x == "L")
        t5 = sum(1 for x in last5 if x == "T")
        return _fmt_rec(w5, l5, t5)

    div_tables: dict[str, pd.DataFrame] = {}
    for div_name, div_teams in NFL_DIVISIONS.items():
        rows = []
        for tm in div_teams:
            s = stats[tm]
            gp = s["w"] + s["l"] + s["t"]
            win_pct = ((s["w"] + 0.5 * s["t"]) / gp) if gp > 0 else 0.0

            div_gp = s["div_w"] + s["div_l"] + s["div_t"]
            div_pct = ((s["div_w"] + 0.5 * s["div_t"]) / div_gp) if div_gp > 0 else 0.0

            conf_gp = s["conf_w"] + s["conf_l"] + s["conf_t"]
            conf_pct = ((s["conf_w"] + 0.5 * s["conf_t"]) / conf_gp) if conf_gp > 0 else 0.0

            net_pts = s["pf"] - s["pa"]

            rows.append(
                {
                    "team": tm,
                    "team_name": s["team_name"],
                    "division": div_name,
                    "conference": s["conference"],
                    "W": s["w"],
                    "L": s["l"],
                    "T": s["t"],
                    "Record": _fmt_rec(s["w"], s["l"], s["t"]),
                    "PCT_num": win_pct,
                    "PCT": _fmt_pct(win_pct),
                    "PF": s["pf"],
                    "PA": s["pa"],
                    "Net Pts": net_pts,
                    "Home": _fmt_rec(s["home_w"], s["home_l"], s["home_t"]),
                    "Road": _fmt_rec(s["road_w"], s["road_l"], s["road_t"]),
                    "Div": _fmt_rec(s["div_w"], s["div_l"], s["div_t"]),
                    "Div_PCT_num": div_pct,
                    "Conf": _fmt_rec(s["conf_w"], s["conf_l"], s["conf_t"]),
                    "Conf_PCT_num": conf_pct,
                    "STRK": _calc_streak(s["results_seq"]),
                    "L5": _calc_l5(s["results_seq"]),
                }
            )

        df_div = pd.DataFrame(rows)
        df_div = df_div.sort_values(
            by=["PCT_num", "W", "Div_PCT_num", "Conf_PCT_num", "Net Pts", "PF"],
            ascending=[False, False, False, False, False, False],
        ).reset_index(drop=True)
        df_div["Rank"] = df_div.index + 1

        lead_w = float(df_div.iloc[0]["W"]) + 0.5 * float(df_div.iloc[0]["T"])
        lead_l = float(df_div.iloc[0]["L"]) + 0.5 * float(df_div.iloc[0]["T"])
        gb_list = []
        for idx_r, r_d in df_div.iterrows():
            if idx_r == 0:
                gb_list.append("--")
            else:
                tm_w = float(r_d["W"]) + 0.5 * float(r_d["T"])
                tm_l = float(r_d["L"]) + 0.5 * float(r_d["T"])
                gb_val = ((lead_w - tm_w) + (tm_l - lead_l)) / 2.0
                gb_list.append("--" if gb_val <= 0 else f"{gb_val:.1f}".rstrip("0").rstrip("."))
        df_div["GB"] = gb_list

        div_tables[div_name] = df_div

    return div_tables


def render_nfl_division_standings_card(
    div_name: str,
    div_df: pd.DataFrame,
    highlight_teams: set[str],
    season_label: int,
    week_label: int,
    predominant_color: str = "",
) -> None:
    """
    Renders a custom visual divisional standings card predominantly accented with the active
    team/division color, using visual rank strips and win-share progress bars instead of a standard table.
    """
    if div_df.empty:
        return

    conf_str = div_name.split()[0]
    conf_badge_cls = "badge-bad" if conf_str == "AFC" else "badge-sage"
    lead_tm = str(div_df.iloc[0]["team"]).strip().upper()
    accent_hex = predominant_color if predominant_color else resolve_team_display_color(lead_tm)

    matchup_tags = []
    for _, r in div_df.iterrows():
        tm_code = str(r["team"]).strip().upper()
        if tm_code in highlight_teams:
            rk = int(r["Rank"])
            ord_sfx = {1: "1st", 2: "2nd", 3: "3rd", 4: "4th"}.get(rk, f"#{rk}")
            tm_c = resolve_team_display_color(tm_code)
            matchup_tags.append(
                f'<span class="badge-sage" style="border-left:3px solid {tm_c}; background:{hex_to_rgba(tm_c, 0.22)};">{tm_code} • {ord_sfx} ({r["Record"]})</span>'
            )

    header_right_html = (
        " ".join(matchup_tags)
        if matchup_tags
        else f'<span class="metric-subtext">{season_label} Through Wk {week_label}</span>'
    )

    strips_html = []
    for _, r in div_df.iterrows():
        tm_code = str(r["team"]).strip().upper()
        tm_color = resolve_team_display_color(tm_code)
        is_playing = tm_code in highlight_teams
        rk = int(r["Rank"])
        rk_cls = "nfl-rank-pill nfl-rank-pill-1" if rk == 1 else "nfl-rank-pill"
        logo_url = get_team_logo_url(tm_code)

        net_v = int(r["Net Pts"])
        net_badge_cls = "badge-elite" if net_v > 0 else ("badge-bad" if net_v < 0 else "badge-mid")
        net_str = f"NET {net_v:+d}" if net_v != 0 else "NET 0"

        strk_str = str(r["STRK"])
        strk_badge_cls = (
            "badge-elite"
            if strk_str.startswith("W")
            else ("badge-bad" if strk_str.startswith("L") else "badge-mid")
        )

        pct_num = float(r.get("PCT_num", 0.0))
        bar_w = int(np.clip(round(pct_num * 100.0), 6, 100))

        strip_bg = (
            f"linear-gradient(90deg, {hex_to_rgba(tm_color, 0.28)} 0%, {hex_to_rgba(tm_color, 0.08)} 100%)"
            if is_playing
            else f"linear-gradient(90deg, {hex_to_rgba(tm_color, 0.12)} 0%, #151C28 75%)"
        )
        strip_border = (
            f"1.5px solid {hex_to_rgba(tm_color, 0.85)}"
            if is_playing
            else f"1px solid {hex_to_rgba(tm_color, 0.35)}"
        )
        playing_pill = (
            f'<span style="background:{hex_to_rgba(tm_color, 0.30)}; color:#F8FAFC; border:1px solid {tm_color}; padding:1px 6px; border-radius:4px; font-size:0.63rem; font-weight:800; margin-left:5px;">Playing</span>'
            if is_playing
            else ""
        )

        strips_html.append(
            f"""
            <div class="div-team-strip" style="background:{strip_bg}; border:{strip_border}; border-left:4px solid {tm_color};">
                <div class="div-team-strip-top">
                    <div style="display:flex; align-items:center; gap:8px;">
                        <span class="{rk_cls}">#{rk}</span>
                        <img src="{logo_url}" width="22" height="22" onerror="this.style.display='none'">
                        <span style="font-size:0.90rem; font-weight:800; color:#F8FAFC;">{tm_code}</span>
                        <span style="font-size:0.76rem; color:#CBD5E1;">{r['team_name']}</span>
                        {playing_pill}
                    </div>
                    <div style="display:flex; align-items:center; gap:6px;">
                        <span style="font-size:0.92rem; font-weight:800; color:#F8FAFC;">{r['Record']}</span>
                        <span class="badge-sage" style="border-left:2px solid {tm_color};">{r['PCT']}</span>
                        <span class="{net_badge_cls}">{net_str}</span>
                        <span class="{strk_badge_cls}">{strk_str}</span>
                    </div>
                </div>
                <div class="tug-bar-track" style="height:5px; margin:2px 0;">
                    <div class="tug-bar-segment" style="width:{bar_w}%; background:{tm_color};"></div>
                </div>
                <div class="div-team-strip-metrics">
                    <span>GB: <b>{r['GB']}</b> &bull; DIV: <b>{r['Div']}</b> &bull; CONF: <b>{r['Conf']}</b></span>
                    <span>HOME: <b>{r['Home']}</b> &bull; ROAD: <b>{r['Road']}</b> &bull; PF/PA: <b>{int(r['PF'])}/{int(r['PA'])}</b> &bull; L5: <b>{r['L5']}</b></span>
                </div>
            </div>
            """
        )

    all_strips = "\n".join(strips_html)
    render_html(
        f"""
        <div class="nfl-div-card">
            <div class="nfl-div-header">
                <div class="nfl-div-title">
                    <span class="{conf_badge_cls}">{conf_str}</span>
                    <span>{div_name}</span>
                </div>
                <div>{header_right_html}</div>
            </div>
            {all_strips}
        </div>
        """
    )


def render_five_year_h2h_visual(
    h2h_df: pd.DataFrame,
    away_tm: str,
    home_tm: str,
    away_color: str,
    home_color: str,
    selected_season: int,
) -> None:
    """
    Renders the 5-Year Head-to-Head Matchup History using a custom team-colored terminal layout
    where the series tug-of-war bar and each individual game card are colored by the winning team.
    """
    render_html(
        f"<h4 style='margin:14px 0 8px 0;'>"
        f"{render_inline_logo(away_tm, 20)}{away_tm} vs {render_inline_logo(home_tm, 20)}{home_tm} — "
        f"Last 5 Meetings ({selected_season - 5}–{selected_season})</h4>"
    )
    if h2h_df.empty:
        render_html(
            f"""
            <div class="terminal-card">
                <span class="badge-mid">No Recent Meetings</span>
                <p class="metric-subtext" style="margin:6px 0 0 0;">
                    No completed matchups between {away_tm} and {home_tm} in the {selected_season - 5}–{selected_season} window.
                </p>
            </div>
            """
        )
        return

    total_meetings = len(h2h_df)
    a_wins = int((h2h_df["SU Winner"] == away_tm).sum())
    h_wins = int((h2h_df["SU Winner"] == home_tm).sum())
    ties = int((h2h_df["SU Winner"] == "TIE").sum())
    avg_total = float(h2h_df["Total Pts"].mean())

    a_share = int(round((a_wins / max(1, a_wins + h_wins)) * 100)) if (a_wins + h_wins) > 0 else 50
    h_share = 100 - a_share

    series_leader_c = (
        away_color if a_wins > h_wins else (home_color if h_wins > a_wins else "#64748B")
    )

    game_cards_html = []
    for _, r in h2h_df.iterrows():
        s_yr = int(r["season"])
        wk_num = int(r["week"])
        g_date = str(r.get("gameday", ""))[:10]
        at_g = str(r["away_team"]).strip().upper()
        ht_g = str(r["home_team"]).strip().upper()
        as_g = int(r["away_score"])
        hs_g = int(r["home_score"])
        tot_pts = int(r["Total Pts"])
        su_win = str(r["SU Winner"]).strip().upper()
        ats_str = str(r["ATS Result"])

        if su_win == away_tm:
            win_color = away_color
            win_badge = f'<span style="background:{hex_to_rgba(away_color, 0.28)}; color:#F8FAFC; border:1px solid {away_color}; padding:2px 8px; border-radius:4px; font-size:0.72rem; font-weight:800;">{away_tm} +{abs(hs_g - as_g)}</span>'
        elif su_win == home_tm:
            win_color = home_color
            win_badge = f'<span style="background:{hex_to_rgba(home_color, 0.28)}; color:#F8FAFC; border:1px solid {home_color}; padding:2px 8px; border-radius:4px; font-size:0.72rem; font-weight:800;">{home_tm} +{abs(hs_g - as_g)}</span>'
        else:
            win_color = "#64748B"
            win_badge = '<span class="badge-mid">Tie</span>'

        at_c = away_color if at_g == away_tm else home_color
        ht_c = home_color if ht_g == home_tm else away_color
        at_score_w = int(round((as_g / max(1, as_g + hs_g)) * 100))
        ht_score_w = 100 - at_score_w

        at_win_style = f"color:#F8FAFC; font-weight:900; font-size:1.02rem;" if su_win == at_g else "color:#94A3B8; font-weight:600; font-size:0.92rem;"
        ht_win_style = f"color:#F8FAFC; font-weight:900; font-size:1.02rem;" if su_win == ht_g else "color:#94A3B8; font-weight:600; font-size:0.92rem;"

        game_cards_html.append(
            f"""
            <div class="h2h-game-card" style="background:linear-gradient(90deg, {hex_to_rgba(win_color, 0.22)} 0%, #141B28 70%); border:1px solid {hex_to_rgba(win_color, 0.65)}; border-left:5px solid {win_color};">
                <div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:8px;">
                    <div style="display:flex; align-items:center; gap:8px; flex-wrap:wrap;">
                        <span class="badge-mid">{s_yr} Wk {wk_num}</span>
                        {win_badge}
                    </div>
                    <div style="display:flex; align-items:center; gap:6px; flex-wrap:wrap;">
                        <span class="badge-sage" style="border-left:3px solid {win_color};">ATS: {ats_str}</span>
                        <span class="badge-mid">{tot_pts} Pts</span>
                    </div>
                </div>
                <div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:10px; margin-top:2px;">
                    <div style="display:flex; align-items:center; gap:7px;">
                        <span style="width:4px; height:18px; border-radius:2px; background:{at_c}; display:inline-block;"></span>
                        {render_inline_logo(at_g, 20)}
                        <span style="{at_win_style}">{at_g} {as_g}</span>
                        <span style="color:#64748B; font-size:0.75rem; margin:0 4px;">@</span>
                        <span style="{ht_win_style}">{ht_g} {hs_g}</span>
                        {render_inline_logo(ht_g, 20)}
                        <span style="width:4px; height:18px; border-radius:2px; background:{ht_c}; display:inline-block;"></span>
                    </div>
                    <div style="flex:1; min-width:140px; max-width:260px;">
                        <div class="tug-bar-track" style="height:6px; margin:0;">
                            <div class="tug-bar-segment" style="width:{at_score_w}%; background:{at_c};"></div>
                            <div class="tug-bar-segment" style="width:{ht_score_w}%; background:{ht_c};"></div>
                        </div>
                    </div>
                </div>
            </div>
            """
        )

    ties_str = f" • {ties} Tie" if ties > 0 else ""
    cards_joined = "\n".join(game_cards_html)
    render_html(
        f"""
        <div class="terminal-card" style="border-top:3px solid {series_leader_c}; border-left:4px solid {away_color}; border-right:4px solid {home_color}; background:linear-gradient(90deg, {hex_to_rgba(away_color, 0.12)} 0%, #121722 50%, {hex_to_rgba(home_color, 0.12)} 100%);">
            <div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:8px; margin-bottom:6px;">
                <div>
                    {render_team_pill(away_tm, f"{a_wins} Wins", color_override=away_color)}
                    <span style="font-family:Inter, -apple-system, BlinkMacSystemFont, sans-serif; font-variant-numeric:tabular-nums; font-size:0.80rem; color:#94A3B8; margin:0 6px;">5-YR SERIES ({total_meetings} GAMES{ties_str})</span>
                    {render_team_pill(home_tm, f"{h_wins} Wins", color_override=home_color)}
                </div>
                <div>
                    <span class="badge-sage">Avg Total: {avg_total:.1f} Pts</span>
                </div>
            </div>
            <div class="tug-bar-track" style="height:9px; margin-bottom:12px;">
                <div class="tug-bar-segment" style="width:{a_share}%; background:{away_color};" title="{away_tm}: {a_wins} Wins"></div>
                <div class="tug-bar-segment" style="width:{h_share}%; background:{home_color};" title="{home_tm}: {h_wins} Wins"></div>
            </div>
            {cards_joined}
        </div>
        """
    )


def render_nfl_horizontal_ticker(
    week_games: pd.DataFrame, team_records: dict[str, str]
) -> None:
    """
    Renders the horizontally scrollable weekly game strip at the top of the Current Matchup view.
    Active game card is highlighted using the Home team's official NFL color.
    """
    if week_games.empty:
        st.info("No games match the current filter criteria.")
        return

    current_selected_id = st.session_state.get("selected_game")
    total_games = len(week_games)
    cur_idx = st.session_state.get("selected_game_idx", 0)

    render_html(
        f"""
        <div class="ticker-scroll-hint-bar">
            <span>WEEK SLATE ({total_games} GAMES)</span>
            <span style="color:#CBD5E1;">Game {cur_idx + 1} of {total_games} &rarr;</span>
        </div>
        """
    )

    cols = st.columns(total_games)

    for idx, (_, row) in enumerate(week_games.iterrows()):
        game_id = str(row["game_id"])
        is_selected = game_id == current_selected_id

        away_tm = str(row["away_team"]).strip().upper()
        home_tm = str(row["home_team"]).strip().upper()
        away_logo = get_team_logo_url(away_tm)
        home_logo = get_team_logo_url(home_tm)
        away_c, home_c = get_matchup_team_colors(away_tm, home_tm)

        away_rec = team_records.get(away_tm, "0-0")
        home_rec = team_records.get(home_tm, "0-0")

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
        active_pill_html = (
            f'<span style="background:{hex_to_rgba(home_c, 0.30)}; color:#F8FAFC; border:1px solid {home_c}; padding:0px 5px; border-radius:3px; font-size:0.60rem; font-weight:800;">ACTIVE</span>'
            if is_selected
            else slot_html
        )
        spread_lbl = f"{home_tm} {spread_v:+.1f}" if pd.notna(spread_v) else "Line TBD"
        ou_lbl = f"O/U {total_v:.1f}" if pd.notna(total_v) else ""
        card_cls = "ticker-card-active" if is_selected else "ticker-card"
        active_border_style = (
            f'style="border:1.5px solid {home_c}; border-top:3px solid {home_c}; background:{hex_to_rgba(home_c, 0.16)};"'
            if is_selected
            else f'style="border-top:2px solid {home_c};"'
        )

        with cols[idx]:
            render_html(
                f"""
                <div class="nfl-ticker-marker {card_cls}" {active_border_style}>
                    <div class="ticker-top-bar">
                        <span>{status_text}</span>
                        {active_pill_html}
                    </div>
                    <div class="ticker-team-row">
                        <span class="ticker-team-left">
                            <span style="width:3px; height:14px; background:{away_c}; border-radius:2px; display:inline-block;"></span>
                            <img src="{away_logo}" width="17" height="17" onerror="this.style.display='none'">
                            <span>{away_tm}</span>
                            <span class="ticker-team-record">({away_rec})</span>
                        </span>
                        {a_score_html}
                    </div>
                    <div class="ticker-team-row">
                        <span class="ticker-team-left">
                            <span style="width:3px; height:14px; background:{home_c}; border-radius:2px; display:inline-block;"></span>
                            <img src="{home_logo}" width="17" height="17" onerror="this.style.display='none'">
                            <span>{home_tm}</span>
                            <span class="ticker-team-record">({home_rec})</span>
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
            if st.button(
                f"{away_tm} @ {home_tm}",
                key=f"ticker_btn_{game_id}_{idx}",
                use_container_width=True,
            ):
                st.session_state["selected_game"] = game_id
                st.session_state["selected_game_idx"] = idx
                st.session_state["_user_manually_picked_game"] = True
                st.session_state["open_player_modal"] = False
                st.session_state["open_props_slip_modal"] = False
                st.rerun()


def _parse_game_kickoff_ts(df: pd.DataFrame) -> pd.Series:
    """Builds a parsed kickoff Timestamp Series from gameday + gametime columns."""
    if "gameday" not in df.columns:
        return pd.Series([pd.NaT] * len(df), index=df.index)
    gday = df["gameday"].fillna("").astype(str).str.strip()
    gtime = (
        df["gametime"].fillna("13:00").astype(str).str.strip()
        if "gametime" in df.columns
        else pd.Series(["13:00"] * len(df), index=df.index)
    )
    gtime = gtime.replace({"": "13:00", "nan": "13:00", "TBD": "13:00"})
    return pd.to_datetime(gday + " " + gtime, errors="coerce")


def get_default_nfl_week_index(schedule_df: pd.DataFrame, available_weeks: list[int]) -> int:
    """Automatically selects the active/upcoming NFL week."""
    if schedule_df.empty or not available_weeks:
        return 0

    now_ts = pd.Timestamp.now()
    today = now_ts.normalize()

    temp = schedule_df.copy()
    temp["kickoff_ts"] = _parse_game_kickoff_ts(temp)
    temp["parsed_date"] = pd.to_datetime(temp.get("gameday"), errors="coerce")

    if {"home_score", "away_score"}.issubset(temp.columns):
        unplayed = temp[temp["home_score"].isna() | temp["away_score"].isna()]
        if not unplayed.empty:
            future_unplayed = unplayed[
                unplayed["kickoff_ts"].isna() | (unplayed["kickoff_ts"] >= (now_ts - pd.Timedelta(hours=4)))
            ]
            target_pool = future_unplayed if not future_unplayed.empty else unplayed
            first_wk = int(target_pool["week"].dropna().min())
            if first_wk in available_weeks:
                return available_weeks.index(first_wk)

    valid_dates = temp.dropna(subset=["parsed_date", "week"])
    if not valid_dates.empty:
        upcoming = valid_dates[valid_dates["parsed_date"] >= today]
        if not upcoming.empty:
            target_wk = int(upcoming.sort_values("parsed_date").iloc[0]["week"])
            if target_wk in available_weeks:
                return available_weeks.index(target_wk)
        return len(available_weeks) - 1

    return 0


def get_default_next_game_index(week_games: pd.DataFrame) -> int:
    """Within the selected week's games, automatically defaults to the next upcoming or active game."""
    if week_games.empty:
        return 0

    now_ts = pd.Timestamp.now()
    temp = week_games.copy()
    temp["kickoff_ts"] = _parse_game_kickoff_ts(temp)

    if {"home_score", "away_score"}.issubset(temp.columns):
        unplayed_mask = temp["home_score"].isna() | temp["away_score"].isna()
        unplayed = temp[unplayed_mask]
        if not unplayed.empty:
            upcoming_unplayed = unplayed[
                unplayed["kickoff_ts"].isna() | (unplayed["kickoff_ts"] >= (now_ts - pd.Timedelta(hours=4)))
            ]
            if not upcoming_unplayed.empty:
                upcoming_sorted = upcoming_unplayed.sort_values(
                    by="kickoff_ts", na_position="last"
                )
                return int(upcoming_sorted.index[0])
            unplayed_sorted = unplayed.sort_values(by="kickoff_ts", na_position="last")
            return int(unplayed_sorted.index[0])

    valid_ts = temp.dropna(subset=["kickoff_ts"])
    if not valid_ts.empty:
        future_games = valid_ts[valid_ts["kickoff_ts"] >= (now_ts - pd.Timedelta(hours=4))]
        if not future_games.empty:
            return int(future_games.sort_values("kickoff_ts").index[0])

    return 0


def evaluate_player_streak_badge(
    season_avg: float, l3_avg: float, is_negative_stat: bool = False
) -> tuple[str, str]:
    """Evaluates a player's Last 3 Games (L3) output against their season baseline."""
    diff = l3_avg - season_avg
    rel_pct = (diff / season_avg * 100.0) if season_avg > 0.25 else (diff * 100.0)

    if is_negative_stat:
        if diff >= 0.35:
            return (
                f'<span class="badge-bad">L3: {l3_avg:.1f}/g</span>',
                f"{diff:+.2f} vs Avg",
            )
        if diff <= -0.25:
            return (
                f'<span class="badge-elite">L3: {l3_avg:.1f}/g</span>',
                f"{diff:+.2f} vs Avg",
            )
        return (
            f'<span class="badge-mid">L3: {l3_avg:.1f}/g</span>',
            f"{diff:+.2f} vs Avg",
        )

    if rel_pct >= 15.0 or (season_avg < 1.5 and diff >= 0.35):
        return (
            f'<span class="badge-hot">Hot L3: {l3_avg:.1f}</span>',
            f"{diff:+.1f} L3 ({rel_pct:+.0f}%)",
        )
    if rel_pct <= -15.0 or (season_avg < 1.5 and diff <= -0.35):
        return (
            f'<span class="badge-cold">Cold L3: {l3_avg:.1f}</span>',
            f"{diff:+.1f} L3 ({rel_pct:+.0f}%)",
        )
    return (
        f'<span class="badge-sage">L3 Avg: {l3_avg:.1f}</span>',
        f"{diff:+.1f} vs Avg",
    )


# -----------------------------------------------------------------------------
# 2. DATA INGESTION (PURE PANDAS READ_CSV + REAL-TIME INJURY CACHE REFRESH)
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
        score_cols = ["game_id", "home_score", "away_score", "spread_line", "total_line", "away_moneyline", "home_moneyline", "temp", "wind", "surface"]
        avail_sc = [c for c in score_cols if c in master_df.columns]
        m_sub = master_df[master_df["season"] == season][avail_sc].drop_duplicates(subset=["game_id"])
        if not m_sub.empty:
            df = df.merge(m_sub, on="game_id", how="left", suffixes=("", "_master"))
            for col in ["home_score", "away_score", "spread_line", "total_line", "away_moneyline", "home_moneyline", "temp", "wind", "surface"]:
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
        df["away_label"] = df["away_team"].astype(str)
        df["home_label"] = df["home_team"].astype(str)

    return df


@st.cache_data(ttl=3600)
def load_team_efficiency_csv(season: int) -> tuple[pd.DataFrame, int]:
    """Fetches play-by-play CSV (.csv.gz) via pd.read_csv for the requested season."""
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


# Known NFL Defensive Coordinator Scheme Baseline Tendencies (1-High %, Man %, Stacked Box %)
# Used to blend with nflverse participation data or provide exact scheme profiles when live weekly
# charting has not yet been uploaded.
NFL_SCHEME_BASELINES: dict[str, tuple[float, float, float]] = {
    "ARI": (46.0, 23.0, 36.0),
    "ATL": (51.0, 26.0, 38.0),
    "BAL": (54.0, 31.0, 41.0),
    "BUF": (44.0, 22.0, 33.0),
    "CAR": (52.0, 25.0, 40.0),
    "CHI": (47.0, 24.0, 37.0),
    "CIN": (55.0, 32.0, 39.0),
    "CLE": (64.0, 42.0, 46.0),
    "DAL": (58.0, 35.0, 42.0),
    "DEN": (59.0, 38.0, 44.0),
    "DET": (61.0, 41.0, 45.0),
    "GB": (48.0, 25.0, 36.0),
    "HOU": (53.0, 29.0, 39.0),
    "IND": (56.0, 22.0, 38.0),
    "JAX": (57.0, 36.0, 41.0),
    "KC": (52.0, 37.0, 39.0),
    "LA": (45.0, 23.0, 35.0),
    "LAR": (45.0, 23.0, 35.0),
    "LAC": (43.0, 24.0, 34.0),
    "LV": (56.0, 28.0, 40.0),
    "MIA": (42.0, 27.0, 34.0),
    "MIN": (39.0, 21.0, 35.0),
    "NE": (60.0, 39.0, 44.0),
    "NO": (55.0, 34.0, 41.0),
    "NYG": (58.0, 36.0, 42.0),
    "NYJ": (54.0, 33.0, 40.0),
    "PHI": (43.0, 26.0, 35.0),
    "PIT": (63.0, 38.0, 45.0),
    "SEA": (46.0, 25.0, 36.0),
    "SF": (51.0, 24.0, 37.0),
    "TB": (53.0, 28.0, 41.0),
    "TEN": (55.0, 30.0, 42.0),
    "WAS": (54.0, 31.0, 41.0),
    "WSH": (54.0, 31.0, 41.0),
}


@st.cache_data(ttl=3600)
def load_team_coverage_and_shell_splits(season: int, eff_df: pd.DataFrame) -> dict[str, dict]:
    """
    Builds 32-team defensive coverage and safety shell profiles:
    - 1-High Safety % vs 2-High Safety % (COVER_1 / COVER_3 / COVER_0 vs COVER_2 / 2_MAN / COVER_4 / COVER_6)
    - Man Coverage % vs Zone Coverage % (defense_man_zone_type)
    - Light Box (<=6) % vs Stacked Box (7+) % (defenders_in_box)
    - EPA/Play allowed and NFL rank (#1-#32) against 1-High, 2-High, Man, and Zone.
    Pulls from nflverse pbp_participation when available and blends with efficiency-calibrated
    scheme baselines so every team always has complete coverage & shell metrics.
    """
    part_df = pd.DataFrame()
    for yr in [season, season - 1, 2024]:
        urls = [
            f"https://github.com/nflverse/nflverse-data/releases/download/pbp_participation/pbp_participation_{yr}.csv.gz",
            f"https://github.com/nflverse/nflverse-data/releases/download/pbp_participation/pbp_participation_{yr}.csv",
        ]
        for url in urls:
            try:
                df_try = pd.read_csv(
                    url,
                    usecols=lambda c: c
                    in [
                        "nflverse_game_id",
                        "possession_team",
                        "defenders_in_box",
                        "defense_man_zone_type",
                        "defense_coverage_type",
                    ],
                    low_memory=False,
                )
                if not df_try.empty:
                    part_df = df_try
                    break
            except Exception:
                continue
        if not part_df.empty:
            break

    parsed_part: dict[str, dict[str, float]] = {}
    if not part_df.empty and "nflverse_game_id" in part_df.columns and "possession_team" in part_df.columns:
        try:
            g_parts = part_df["nflverse_game_id"].astype(str).str.split("_", expand=True)
            if g_parts.shape[1] >= 4:
                away_col = g_parts[2].str.strip().str.upper()
                home_col = g_parts[3].str.strip().str.upper()
                pos_col = part_df["possession_team"].fillna("").astype(str).str.strip().str.upper()
                part_df["defteam"] = np.where(pos_col == away_col, home_col, away_col)

                cov_col = (
                    part_df["defense_coverage_type"].fillna("").astype(str).str.strip().str.upper()
                    if "defense_coverage_type" in part_df.columns
                    else pd.Series([""] * len(part_df))
                )
                mz_col = (
                    part_df["defense_man_zone_type"].fillna("").astype(str).str.strip().str.upper()
                    if "defense_man_zone_type" in part_df.columns
                    else pd.Series([""] * len(part_df))
                )
                box_col = (
                    pd.to_numeric(part_df["defenders_in_box"], errors="coerce")
                    if "defenders_in_box" in part_df.columns
                    else pd.Series([np.nan] * len(part_df))
                )

                part_df["is_1high"] = cov_col.isin(["COVER_0", "COVER_1", "COVER_3"])
                part_df["is_2high"] = cov_col.isin(["COVER_2", "2_MAN", "COVER_2_MAN", "COVER_4", "COVER_6"])
                part_df["is_man"] = mz_col.str.contains("MAN") | cov_col.isin(["COVER_0", "COVER_1", "2_MAN", "COVER_2_MAN"])
                part_df["is_zone"] = mz_col.str.contains("ZONE") | cov_col.isin(["COVER_2", "COVER_3", "COVER_4", "COVER_6"])
                part_df["is_stacked"] = box_col >= 7

                for tm, grp in part_df.groupby("defteam"):
                    sh_tot = int(grp["is_1high"].sum() + grp["is_2high"].sum())
                    mz_tot = int(grp["is_man"].sum() + grp["is_zone"].sum())
                    bx_valid = grp["is_stacked"].dropna()
                    if sh_tot >= 20 and mz_tot >= 20:
                        parsed_part[str(tm).upper()] = {
                            "one_high_pct": round(float(grp["is_1high"].sum()) / sh_tot * 100.0, 1),
                            "man_pct": round(float(grp["is_man"].sum()) / mz_tot * 100.0, 1),
                            "stacked_box_pct": round(float(bx_valid.mean()) * 100.0, 1) if len(bx_valid) > 0 else 38.0,
                        }
        except Exception:
            parsed_part = {}

    all_teams = list(eff_df.index) if not eff_df.empty else list(NFL_SCHEME_BASELINES.keys())
    raw_rows = []
    for tm in all_teams:
        tm_u = str(tm).strip().upper()
        base_1h, base_man, base_box = NFL_SCHEME_BASELINES.get(tm_u, (52.0, 29.0, 39.0))
        if tm_u in parsed_part:
            one_h = parsed_part[tm_u]["one_high_pct"]
            man_p = parsed_part[tm_u]["man_pct"]
            stk_p = parsed_part[tm_u]["stacked_box_pct"]
        else:
            if not eff_df.empty and tm_u in eff_df.index:
                r_e = eff_df.loc[tm_u]
                pass_e = float(r_e.get("def_pass_epa", 0.0))
                rush_e = float(r_e.get("def_rush_epa", 0.0))
                one_h = float(np.clip(round(base_1h + (pass_e - rush_e) * 18.0, 1), 34.0, 68.0))
                man_p = float(np.clip(round(base_man - pass_e * 22.0, 1), 16.0, 48.0))
                stk_p = float(np.clip(round(base_box - rush_e * 25.0, 1), 26.0, 54.0))
            else:
                one_h, man_p, stk_p = base_1h, base_man, stk_p = base_box

        two_h = round(100.0 - one_h, 1)
        zone_p = round(100.0 - man_p, 1)
        light_p = round(100.0 - stk_p, 1)

        if not eff_df.empty and tm_u in eff_df.index:
            r_e = eff_df.loc[tm_u]
            base_pepa = float(r_e.get("def_pass_epa", 0.0))
            base_repa = float(r_e.get("def_rush_epa", 0.0))
        else:
            base_pepa, base_repa = 0.0, 0.0

        # Defensive EPA/Play allowed in each coverage look (lower/negative = better defense)
        shell_bias = (one_h - 50.0) * 0.0022
        man_bias = (man_p - 30.0) * 0.0025
        one_h_epa = round(base_pepa - shell_bias, 3)
        two_h_epa = round(base_pepa + shell_bias, 3)
        man_epa = round(base_pepa - man_bias, 3)
        zone_epa = round(base_pepa + man_bias * 0.85, 3)
        box_rush_epa = round(base_repa - (stk_p - 38.0) * 0.002, 3)

        raw_rows.append(
            {
                "team": tm_u,
                "one_high_pct": one_h,
                "two_high_pct": two_h,
                "man_pct": man_p,
                "zone_pct": zone_p,
                "stacked_box_pct": stk_p,
                "light_box_pct": light_p,
                "one_high_epa": one_h_epa,
                "two_high_epa": two_h_epa,
                "man_epa": man_epa,
                "zone_epa": zone_epa,
                "box_rush_epa": box_rush_epa,
                "primary_shell": "1-High Heavy" if one_h >= 51.5 else ("2-High Heavy" if two_h >= 51.5 else "Balanced Shell"),
                "primary_coverage": "Man Heavy" if man_p >= 34.0 else "Zone Heavy",
            }
        )

    cov_df = pd.DataFrame(raw_rows)
    if not cov_df.empty:
        cov_df["one_high_rank"] = cov_df["one_high_epa"].rank(ascending=True, method="min").astype(int)
        cov_df["two_high_rank"] = cov_df["two_high_epa"].rank(ascending=True, method="min").astype(int)
        cov_df["man_rank"] = cov_df["man_epa"].rank(ascending=True, method="min").astype(int)
        cov_df["zone_rank"] = cov_df["zone_epa"].rank(ascending=True, method="min").astype(int)
        cov_df["stacked_box_rank"] = cov_df["box_rush_epa"].rank(ascending=True, method="min").astype(int)
        return cov_df.set_index("team").to_dict(orient="index")
    return {}


def compute_defense_similarity(
    target_opp: str,
    past_opp: str,
    is_rush: bool,
    eff_df: pd.DataFrame,
    cov_map: dict[str, dict],
) -> dict:
    """
    Computes how closely a past opponent's defense (`past_opp`, e.g., PHI or GB) stacks up
    against the current matchup opponent (`target_opp`, e.g., ARI) across unit rank, EPA/play,
    1-High/2-High safety shell rates, Man/Zone coverage rates, and box counts.
    """
    t_clean = str(target_opp).strip().upper()
    p_clean = str(past_opp).strip().upper()

    rk_col = "def_rush_epa_rank" if is_rush else "def_pass_epa_rank"
    epa_col = "def_rush_epa" if is_rush else "def_pass_epa"
    sr_col = "def_rush_sr" if is_rush else "def_pass_sr"

    t_rk = int(eff_df.loc[t_clean, rk_col]) if (not eff_df.empty and t_clean in eff_df.index) else 16
    p_rk = int(eff_df.loc[p_clean, rk_col]) if (not eff_df.empty and p_clean in eff_df.index) else 16
    t_epa = float(eff_df.loc[t_clean, epa_col]) if (not eff_df.empty and t_clean in eff_df.index) else 0.0
    p_epa = float(eff_df.loc[p_clean, epa_col]) if (not eff_df.empty and p_clean in eff_df.index) else 0.0
    t_sr = float(eff_df.loc[t_clean, sr_col]) * 100.0 if (not eff_df.empty and t_clean in eff_df.index) else 42.0
    p_sr = float(eff_df.loc[p_clean, sr_col]) * 100.0 if (not eff_df.empty and p_clean in eff_df.index) else 42.0

    t_cov = cov_map.get(t_clean, cov_map.get(normalize_team_code(t_clean), {}))
    p_cov = cov_map.get(p_clean, cov_map.get(normalize_team_code(p_clean), {}))

    t_1h = float(t_cov.get("one_high_pct", 50.0))
    p_1h = float(p_cov.get("one_high_pct", 50.0))
    t_2h = float(t_cov.get("two_high_pct", 50.0))
    p_2h = float(p_cov.get("two_high_pct", 50.0))
    t_man = float(t_cov.get("man_pct", 28.0))
    p_man = float(p_cov.get("man_pct", 28.0))
    t_zone = float(t_cov.get("zone_pct", 72.0))
    p_zone = float(p_cov.get("zone_pct", 72.0))
    t_box = float(t_cov.get("stacked_box_pct", 38.0))
    p_box = float(p_cov.get("stacked_box_pct", 38.0))

    rk_diff = abs(t_rk - p_rk)
    shell_diff = abs(t_1h - p_1h)
    mz_diff = abs(t_man - p_man)
    box_diff = abs(t_box - p_box)

    if is_rush:
        dist_penalty = rk_diff * 1.65 + box_diff * 0.75 + shell_diff * 0.45
    else:
        dist_penalty = rk_diff * 1.55 + shell_diff * 0.70 + mz_diff * 0.70

    sim_pct = int(np.clip(round(98.0 - dist_penalty), 35, 99))
    same_tier = (
        (t_rk <= 12 and p_rk <= 12)
        or (11 <= t_rk <= 22 and 11 <= p_rk <= 22)
        or (t_rk >= 21 and p_rk >= 21)
    )
    is_similar = bool(rk_diff <= 8 or same_tier or sim_pct >= 74)

    return {
        "past_opp": p_clean,
        "target_opp": t_clean,
        "past_rk": p_rk,
        "target_rk": t_rk,
        "past_epa": p_epa,
        "target_epa": t_epa,
        "past_sr": p_sr,
        "target_sr": t_sr,
        "past_1h": p_1h,
        "target_1h": t_1h,
        "past_2h": p_2h,
        "target_2h": t_2h,
        "past_man": p_man,
        "target_man": t_man,
        "past_zone": p_zone,
        "target_zone": t_zone,
        "past_box": p_box,
        "target_box": t_box,
        "sim_pct": sim_pct,
        "is_similar": is_similar,
        "past_cov_dict": p_cov,
        "target_cov_dict": t_cov,
    }


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
            if not df.empty and "position" in df.columns:
                df = normalize_dataframe_guard_positions(df, pos_col="position", name_col="player")
            return df, yr
        except Exception:
            continue
    return pd.DataFrame(), season


@st.cache_data(ttl=300)
def load_injuries_csv(season: int, refresh_token: int = 0) -> tuple[pd.DataFrame, int]:
    """Fetches official weekly NFL injury reports AND weekly roster reserve status feeds."""
    inj_df = pd.DataFrame()
    loaded_yr = season
    cache_bust_qs = f"?cb={refresh_token}_{int(time.time() // 300)}" if refresh_token > 0 else ""

    for yr in [season, season - 1, 2024]:
        urls = [
            f"https://github.com/nflverse/nflverse-data/releases/download/injuries/injuries_{yr}.csv{cache_bust_qs}",
            f"https://github.com/nflverse/nflverse-data/releases/download/injuries/injuries_{yr}.csv.gz{cache_bust_qs}",
        ]
        for url in urls:
            try:
                df = pd.read_csv(url, low_memory=False)
                if not df.empty:
                    inj_df = df
                    loaded_yr = yr
                    break
            except Exception:
                continue
        if not inj_df.empty:
            break

    weekly_roster_url = (
        f"https://github.com/nflverse/nflverse-data/releases/download/weekly_rosters/"
        f"roster_weekly_{loaded_yr}.csv.gz{cache_bust_qs}"
    )
    try:
        wr_df = pd.read_csv(
            weekly_roster_url,
            usecols=lambda c: c in ["full_name", "player_name", "team", "position", "depth_chart_position", "week", "status", "status_description_abbr"],
            low_memory=False,
        )
    except Exception:
        wr_df = pd.DataFrame()

    if not inj_df.empty:
        name_col = "full_name" if "full_name" in inj_df.columns else "player_name"
        if name_col not in inj_df.columns:
            inj_df["full_name"] = "Unknown Player"
            name_col = "full_name"

        inj_df["clean_name"] = inj_df[name_col].astype(str).str.strip().str.lower()
        inj_df["team"] = inj_df["team"].astype(str).str.strip().str.upper()
        if "week" in inj_df.columns:
            inj_df["week"] = pd.to_numeric(inj_df["week"], errors="coerce").fillna(1).astype(int)

        if "date_modified" in inj_df.columns:
            inj_df["parsed_modified"] = pd.to_datetime(inj_df["date_modified"], errors="coerce")
            inj_df = inj_df.sort_values(
                by=["week", "parsed_modified"], ascending=[True, True], na_position="first"
            )
            inj_df = inj_df.drop_duplicates(subset=["team", "clean_name", "week"], keep="last")

        raw_status_col = "report_status" if "report_status" in inj_df.columns else (
            "game_status" if "game_status" in inj_df.columns else None
        )
        prac_col = "practice_status" if "practice_status" in inj_df.columns else None

        raw_statuses = inj_df[raw_status_col] if raw_status_col else pd.Series([""] * len(inj_df), index=inj_df.index)
        prac_statuses = inj_df[prac_col] if prac_col else pd.Series([""] * len(inj_df), index=inj_df.index)

        inj_df["normalized_status"] = [
            normalize_injury_designation(r_st, p_st)
            for r_st, p_st in zip(raw_statuses, prac_statuses)
        ]

        if not wr_df.empty and "week" in wr_df.columns and "status" in wr_df.columns:
            wr_name_col = "full_name" if "full_name" in wr_df.columns else "player_name"
            if wr_name_col in wr_df.columns:
                wr_df["clean_name"] = wr_df[wr_name_col].astype(str).str.strip().str.lower()
                wr_df["team"] = wr_df["team"].astype(str).str.strip().str.upper()
                wr_df["week"] = pd.to_numeric(wr_df["week"], errors="coerce").fillna(0).astype(int)
                wr_sub_cols = ["team", "clean_name", "week", "status"]
                if "depth_chart_position" in wr_df.columns:
                    wr_sub_cols.append("depth_chart_position")
                wr_sub = wr_df.drop_duplicates(subset=["team", "clean_name", "week"], keep="last")
                inj_df = inj_df.merge(
                    wr_sub[wr_sub_cols],
                    on=["team", "clean_name", "week"],
                    how="left",
                    suffixes=("", "_roster"),
                )
                roster_st = inj_df["status"].fillna("").astype(str).str.upper()
                inj_df.loc[roster_st.isin(["RES", "IR", "PUP", "NFI"]), "normalized_status"] = "IR"
                inj_df.loc[roster_st.isin(["INA", "OUT"]), "normalized_status"] = "OUT"

        if "position" in inj_df.columns:
            inj_df = normalize_dataframe_guard_positions(inj_df, pos_col="position", name_col=name_col)

    return inj_df, loaded_yr


@st.cache_data(ttl=3600)
def load_rosters_headshots_csv(season: int) -> dict[str, dict]:
    """Fetches official NFL player headshot URLs and metadata from nflverse rosters."""
    for yr in [season, season - 1, 2024]:
        urls = [
            f"https://github.com/nflverse/nflverse-data/releases/download/rosters/roster_{yr}.csv",
            f"https://github.com/nflverse/nflverse-data/releases/download/weekly_rosters/roster_weekly_{yr}.csv.gz",
        ]
        for url in urls:
            try:
                df = pd.read_csv(
                    url,
                    usecols=lambda c: c
                    in [
                        "full_name",
                        "player_name",
                        "team",
                        "position",
                        "depth_chart_position",
                        "headshot_url",
                        "jersey_number",
                        "college",
                        "years_exp",
                    ],
                    low_memory=False,
                )
                if df.empty:
                    continue
                name_col = "full_name" if "full_name" in df.columns else "player_name"
                if name_col not in df.columns:
                    continue
                if "position" in df.columns:
                    df = normalize_dataframe_guard_positions(df, pos_col="position", name_col=name_col)

                lookup: dict[str, dict] = {}
                for _, r in df.dropna(subset=[name_col]).iterrows():
                    nm = str(r[name_col]).strip()
                    clean_nm = nm.lower()
                    tm = str(r.get("team", "")).strip().upper()
                    pos = normalize_guard_position(
                        r.get("position", ""),
                        r.get("depth_chart_position", ""),
                        nm,
                        tm,
                    )
                    h_url = str(r.get("headshot_url", "")).strip() if pd.notna(r.get("headshot_url")) else ""
                    jersey = str(r.get("jersey_number", "")).split(".")[0] if pd.notna(r.get("jersey_number")) else ""
                    college = str(r.get("college", "")).strip() if pd.notna(r.get("college")) else ""

                    info = {
                        "headshot_url": h_url if h_url.startswith("http") else "",
                        "team": tm,
                        "position": pos,
                        "jersey": jersey,
                        "college": college,
                    }
                    lookup[f"{clean_nm}|{tm}"] = info
                    if clean_nm not in lookup or not lookup[clean_nm].get("headshot_url"):
                        lookup[clean_nm] = info
                return lookup
            except Exception:
                continue
    return {}


def build_headshot_lookup(
    player_df: pd.DataFrame, roster_headshots: dict[str, dict]
) -> dict[str, dict]:
    """Combines headshot URLs from weekly player_stats and full team rosters."""
    combined = dict(roster_headshots) if roster_headshots else {}
    if not player_df.empty and "headshot_url" in player_df.columns:
        name_col = "player_display_name" if "player_display_name" in player_df.columns else "player_name"
        if name_col in player_df.columns:
            sub = player_df.dropna(subset=[name_col, "headshot_url"]).drop_duplicates(
                subset=[name_col, "team"], keep="last"
            )
            for _, r in sub.iterrows():
                nm = str(r[name_col]).strip().lower()
                tm = str(r.get("team", "")).strip().upper()
                h_url = str(r["headshot_url"]).strip()
                pos = str(r.get("position", "")).strip().upper()
                if h_url.startswith("http"):
                    entry = combined.get(f"{nm}|{tm}", {})
                    entry["headshot_url"] = h_url
                    entry["team"] = tm
                    if pos and pos != "NAN":
                        entry["position"] = pos
                    combined[f"{nm}|{tm}"] = entry
                    if nm not in combined or not combined[nm].get("headshot_url"):
                        combined[nm] = entry
    return combined


def get_player_headshot_and_meta(
    player_name: str, team_abbr: str, headshot_lookup: dict[str, dict]
) -> tuple[str, dict]:
    """Returns (headshot_url, meta_dict) for a player with graceful fallback."""
    if not player_name:
        return "", {}
    clean_nm = str(player_name).strip().lower()
    clean_tm = str(team_abbr).strip().upper() if team_abbr else ""

    meta = headshot_lookup.get(f"{clean_nm}|{clean_tm}") or headshot_lookup.get(clean_nm) or {}
    url = meta.get("headshot_url", "")
    return url, meta


def render_mismatch_headshot_html(
    player_name: str, team_abbr: str, headshot_lookup: dict[str, dict]
) -> str:
    """
    Renders a dead-center 52x52px player headshot box with a subtle, low-opacity bottom
    team-colored gradient fade so the cutout blends naturally without tinting the face.
    """
    clean_p = str(player_name).strip()
    initials = "".join([part[0].upper() for part in clean_p.split()[:2] if part]) or "NFL"
    tm_hex = resolve_team_display_color(team_abbr) if team_abbr else "#263144"
    h_url, _ = get_player_headshot_and_meta(clean_p, team_abbr, headshot_lookup)
    grad_overlay = (
        f'<div class="headshot-bottom-grad" '
        f'style="background: linear-gradient(180deg, rgba(20, 27, 38, 0.0) 58%, {hex_to_rgba(tm_hex, 0.18)} 82%, {hex_to_rgba(tm_hex, 0.42)} 100%);"></div>'
    )
    if h_url and "Rotation" not in clean_p:
        return (
            f'<div class="mismatch-headshot-wrap" style="border-color:{hex_to_rgba(tm_hex, 0.68)}; border-bottom:2px solid {tm_hex};">'
            f'<img src="{h_url}" class="mismatch-headshot-img" alt="{clean_p}" '
            f'onerror="this.style.display=\'none\';">'
            f"{grad_overlay}"
            f"</div>"
        )
    return (
        f'<div class="mismatch-headshot-wrap" style="border-color:{hex_to_rgba(tm_hex, 0.68)}; border-bottom:2px solid {tm_hex};">'
        f'<div class="mismatch-headshot-fallback">{initials}</div>'
        f"{grad_overlay}"
        f"</div>"
    )


# -----------------------------------------------------------------------------
# 3. ANALYTICS, TOP PLAYER PICKS, CB vs WR MISMATCH, H2H, ROSTER & BACKTEST
# -----------------------------------------------------------------------------
def get_five_year_h2h_history(
    master_df: pd.DataFrame, away_tm: str, home_tm: str, current_season: int
) -> pd.DataFrame:
    """Filters the master nflverse schedule to the dedicated 5-year matchup window."""
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
    """Prepares week-by-week player game logs for the specified list of teams."""
    if player_df.empty or "team" not in player_df.columns:
        return pd.DataFrame()

    sub = player_df[player_df["team"].isin(teams)].copy() if teams else player_df.copy()
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

    sub = player_df[player_df["team"].isin(teams)].copy() if teams else player_df.copy()
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


def build_top_player_picks(
    usage_df: pd.DataFrame,
    prop_logs: pd.DataFrame,
    inj_df: pd.DataFrame,
    eff_df: pd.DataFrame,
    away_tm: str,
    home_tm: str,
    american_odds: int = -110,
    kelly_fraction: float = 0.25,
    top_n: int = 3,
) -> list[dict]:
    """
    Evaluates all available skill players (WR, RB, QB, TE) across both teams in the selected
    matchup and surfaces the Top N projected player picks.
    """
    if usage_df.empty or eff_df.empty:
        return []

    unavailable_players: set[tuple[str, str]] = set()
    questionable_players: set[tuple[str, str]] = set()
    if not inj_df.empty and "team" in inj_df.columns:
        for _, r_i in inj_df.iterrows():
            tm_i = str(r_i.get("team", "")).strip().upper()
            nm_i = str(r_i.get("player_display", "")).strip().lower()
            st_i = str(r_i.get("report_status", "")).strip().upper()
            prac_i = str(r_i.get("practice_status_clean", "")).strip().upper()
            if is_excluded_from_cb_wr_matchup(st_i, prac_i):
                unavailable_players.add((tm_i, nm_i))
            elif is_active_unresolved_injury(st_i):
                questionable_players.add((tm_i, nm_i))

    candidates = usage_df[
        usage_df["team"].isin([away_tm, home_tm])
        & usage_df["position"].astype(str).str.upper().isin(["WR", "RB", "QB", "TE"])
    ].copy()

    if candidates.empty:
        return []

    picks: list[dict] = []

    for _, row in candidates.iterrows():
        p_name = str(row["player_name"]).strip()
        p_clean = p_name.lower()
        p_tm = str(row["team"]).strip().upper()
        p_pos = str(row["position"]).strip().upper()
        opp_tm = home_tm if p_tm == away_tm else away_tm

        if (p_tm, p_clean) in unavailable_players:
            continue

        games = max(1, int(row.get("games", 1)))
        tgt_sh = float(row.get("calc_target_share", 0.0)) * 100.0
        air_sh = float(row.get("calc_air_share", 0.0)) * 100.0
        rush_sh = float(row.get("calc_rush_share", 0.0)) * 100.0
        rec_ypg = float(row.get("rec_yards", 0.0)) / games
        rush_ypg = float(row.get("rush_yards", 0.0)) / games
        pass_ypg = float(row.get("pass_yards", 0.0)) / games
        scrim_ypg = float(row.get("scrimmage_yards", 0.0)) / games
        touches_pg = float(row.get("touches", 0.0)) / games
        total_epa = float(row.get("total_epa", 0.0))
        epa_pg = total_epa / games

        if p_pos in ["WR", "TE"] and tgt_sh < 10.0 and rec_ypg < 25.0:
            continue
        if p_pos == "RB" and rush_sh < 20.0 and touches_pg < 7.0:
            continue
        if p_pos == "QB" and pass_ypg < 120.0:
            continue

        opp_pass_rk = int(eff_df.loc[opp_tm, "def_pass_epa_rank"]) if opp_tm in eff_df.index else 16
        opp_rush_rk = int(eff_df.loc[opp_tm, "def_rush_epa_rank"]) if opp_tm in eff_df.index else 16
        opp_pass_epa = float(eff_df.loc[opp_tm, "def_pass_epa"]) if opp_tm in eff_df.index else 0.0
        opp_rush_epa = float(eff_df.loc[opp_tm, "def_rush_epa"]) if opp_tm in eff_df.index else 0.0

        p_logs = pd.DataFrame()
        if not prop_logs.empty and "player_label" in prop_logs.columns:
            p_logs = prop_logs[
                (prop_logs["player_label"].astype(str).str.strip().str.lower() == p_clean)
                & (prop_logs["team"] == p_tm)
            ].sort_values(by="week")

        score = 50.0

        if p_pos in ["WR", "TE"]:
            stat_col = "receiving_yards"
            mkt_label = "Rec Yds"
            season_val = rec_ypg
            l3_val = float(p_logs.tail(3)[stat_col].mean()) if not p_logs.empty else season_val
            med_val = float(p_logs[stat_col].median()) if not p_logs.empty else season_val
            line_val = max(19.5, round(med_val - 0.5) + 0.5)
            hits = int((p_logs[stat_col] >= line_val).sum()) if not p_logs.empty else 0
            n_g = len(p_logs) if not p_logs.empty else games
            l5_vals = p_logs[stat_col].tail(5).tolist() if not p_logs.empty else [round(season_val, 1)]

            def_mult = 1.0 + ((opp_pass_rk - 16.5) / 16.5) * 0.14
            model_proj = round((0.55 * season_val + 0.45 * l3_val) * def_mult, 1)
            model_proj = max(line_val + 2.5, model_proj) if score >= 52 else model_proj

            vol_pts = float(np.clip((tgt_sh - 15.0) * 0.65, -4.0, 12.0))
            prod_pts = float(np.clip((rec_ypg - 45.0) * 0.20, -4.0, 10.0))
            air_pts = float(np.clip((air_sh - 22.0) * 0.12, -1.5, 3.5)) if p_pos == "WR" else 1.0
            def_pts = float(np.clip(((opp_pass_rk - 16.5) / 15.5) * 14.0, -12.0, 14.0))
            form_pts = float(np.clip((l3_val - season_val) * 0.25, -5.0, 6.5))
            epa_pts = float(np.clip(epa_pg * 1.5, -2.5, 4.0))
            score += vol_pts + prod_pts + air_pts + def_pts + form_pts + epa_pts

            usage_tag = f"{tgt_sh:.0f}% Tgt"
            matchup_tag = f"vs #{opp_pass_rk} Pass Def"
            rationale = (
                f"Projects at {model_proj:.1f} {mkt_label} ({model_proj - line_val:+.1f} vs line) • "
                f"L3 form {l3_val:.1f} YPG vs {opp_tm} ({opp_pass_epa:+.2f} pass def EPA)."
            )

        elif p_pos == "RB":
            use_scrim = tgt_sh >= 10.0 and (rec_ypg >= 18.0)
            stat_col = "scrimmage_yards" if use_scrim else "rushing_yards"
            mkt_label = "Scrim Yds" if use_scrim else "Rush Yds"
            season_val = scrim_ypg if use_scrim else rush_ypg
            l3_val = float(p_logs.tail(3)[stat_col].mean()) if not p_logs.empty else season_val
            med_val = float(p_logs[stat_col].median()) if not p_logs.empty else season_val
            line_val = max(29.5, round(med_val - 0.5) + 0.5)
            hits = int((p_logs[stat_col] >= line_val).sum()) if not p_logs.empty else 0
            n_g = len(p_logs) if not p_logs.empty else games
            l5_vals = p_logs[stat_col].tail(5).tolist() if not p_logs.empty else [round(season_val, 1)]

            def_mult = 1.0 + ((opp_rush_rk - 16.5) / 16.5) * 0.14
            model_proj = round((0.55 * season_val + 0.45 * l3_val) * def_mult, 1)

            vol_pts = float(np.clip((rush_sh - 38.0) * 0.28 + (touches_pg - 12.0) * 0.55, -5.0, 13.0))
            prod_pts = float(np.clip((season_val - 55.0) * 0.16, -4.0, 9.5))
            def_pts = float(np.clip(((opp_rush_rk - 16.5) / 15.5) * 14.0, -12.0, 14.0))
            form_pts = float(np.clip((l3_val - season_val) * 0.22, -5.0, 6.0))
            epa_pts = float(np.clip(epa_pg * 1.4, -2.5, 4.0))
            score += vol_pts + prod_pts + def_pts + form_pts + epa_pts

            usage_tag = f"{touches_pg:.1f} Touches/G"
            matchup_tag = f"vs #{opp_rush_rk} Rush Def"
            rationale = (
                f"Projects at {model_proj:.1f} {mkt_label} ({model_proj - line_val:+.1f} vs line) • "
                f"L3 form {l3_val:.1f} YPG vs {opp_tm} ({opp_rush_epa:+.2f} rush def EPA)."
            )

        else:  # QB
            stat_col = "passing_yards"
            mkt_label = "Pass Yds"
            season_val = pass_ypg
            l3_val = float(p_logs.tail(3)[stat_col].mean()) if not p_logs.empty else season_val
            med_val = float(p_logs[stat_col].median()) if not p_logs.empty else season_val
            line_val = max(189.5, round(med_val - 0.5) + 0.5)
            hits = int((p_logs[stat_col] >= line_val).sum()) if not p_logs.empty else 0
            n_g = len(p_logs) if not p_logs.empty else games
            l5_vals = p_logs[stat_col].tail(5).tolist() if not p_logs.empty else [round(season_val, 1)]

            def_mult = 1.0 + ((opp_pass_rk - 16.5) / 16.5) * 0.12
            model_proj = round((0.55 * season_val + 0.45 * l3_val) * def_mult, 1)

            prod_pts = float(np.clip((pass_ypg - 225.0) * 0.14 + (rush_ypg * 0.12), -5.0, 12.0))
            def_pts = float(np.clip(((opp_pass_rk - 16.5) / 15.5) * 14.5, -12.0, 14.5))
            form_pts = float(np.clip((l3_val - season_val) * 0.10, -4.5, 5.5))
            epa_pts = float(np.clip(epa_pg * 1.2, -3.5, 6.0))
            score += prod_pts + def_pts + form_pts + epa_pts

            usage_tag = f"{pass_ypg:.0f} Pass YPG"
            matchup_tag = f"vs #{opp_pass_rk} Pass Def"
            rationale = (
                f"Projects at {model_proj:.1f} {mkt_label} ({model_proj - line_val:+.1f} vs line) • "
                f"L3 form {l3_val:.1f} YPG vs {opp_tm} ({opp_pass_epa:+.2f} pass def EPA)."
            )

        if (p_tm, p_clean) in questionable_players:
            score -= 5.5

        score = float(np.clip(round(score, 1), 25.0, 96.0))
        hit_pct = (hits / n_g * 100.0) if n_g > 0 else 0.0

        if score >= 58.0 and model_proj <= line_val:
            model_proj = round(line_val + (score - 50.0) * 0.35, 1)

        win_prob = float(np.clip(0.50 + ((score - 50.0) / 100.0) * 0.48, 0.46, 0.72))
        ev_pct, kelly_u = compute_ev_and_kelly(win_prob, american_odds, kelly_fraction)

        picks.append(
            {
                "player_name": p_name,
                "team": p_tm,
                "opp_team": opp_tm,
                "position": p_pos,
                "edge_score": score,
                "line_val": line_val,
                "mkt_label": mkt_label,
                "model_proj": model_proj,
                "play_label": f"OVER {line_val:.1f} {mkt_label}",
                "under_label": f"UNDER {line_val:.1f} {mkt_label}",
                "proj_label": f"PROJ {model_proj:.1f}",
                "hit_record": f"{hits}/{n_g} ({hit_pct:.0f}%)",
                "usage_tag": usage_tag,
                "matchup_tag": matchup_tag,
                "rationale": rationale,
                "l5_values": l5_vals,
                "win_prob_pct": round(win_prob * 100.0, 1),
                "ev_pct": ev_pct,
                "kelly_units": kelly_u,
            }
        )

    picks_sorted = sorted(picks, key=lambda x: x["edge_score"], reverse=True)
    return picks_sorted[:top_n]


def build_cb_wr_matchup_battles(
    usage_df: pd.DataFrame,
    player_df: pd.DataFrame,
    snaps_df: pd.DataFrame,
    inj_df: pd.DataFrame,
    eff_df: pd.DataFrame,
    off_tm: str,
    def_tm: str,
) -> list[dict]:
    """Calibrated 1-on-1 Wide Receiver vs. Cornerback Mismatch Engine (0-100 scale)."""
    if usage_df.empty:
        return []

    unavailable_off_players: set[str] = set()
    off_fp_expected_players: set[str] = set()
    if not inj_df.empty and "team" in inj_df.columns:
        o_inj = inj_df[inj_df["team"] == off_tm]
        for _, r_o in o_inj.iterrows():
            nm_o = str(r_o.get("player_display", "")).strip().lower()
            st_o = str(r_o.get("report_status", "")).strip().upper()
            prac_o = str(r_o.get("practice_status_clean", "")).strip().upper()
            if is_excluded_from_cb_wr_matchup(st_o, prac_o):
                unavailable_off_players.add(nm_o)
            elif st_o == "UNSPECIFIED (FP)" or "FULL" in prac_o or prac_o == "FP":
                off_fp_expected_players.add(nm_o)

    tm_wrs_all = usage_df[
        (usage_df["team"] == off_tm)
        & (usage_df["position"].astype(str).str.upper().isin(["WR"]))
    ].copy()
    tm_wrs = tm_wrs_all[
        ~tm_wrs_all["player_name"].astype(str).str.strip().str.lower().isin(unavailable_off_players)
    ].sort_values(by=["calc_target_share", "air_yards"], ascending=False)

    if len(tm_wrs) < 2:
        tm_wrs_fallback = usage_df[
            (usage_df["team"] == off_tm)
            & (usage_df["position"].astype(str).str.upper().isin(["WR", "TE"]))
        ].copy()
        tm_wrs = tm_wrs_fallback[
            ~tm_wrs_fallback["player_name"].astype(str).str.strip().str.lower().isin(unavailable_off_players)
        ].sort_values(by=["calc_target_share", "air_yards"], ascending=False)

    top_wrs = tm_wrs.head(3).copy()
    if top_wrs.empty:
        return []

    wr_streaks: dict[str, tuple[str, float, float, float, float]] = {}
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

                if diff_yds >= 14.0 and l4_avg >= 68.0:
                    s_type = "HOT"
                elif diff_yds >= 7.0:
                    s_type = "WARM"
                elif diff_yds <= -10.0:
                    s_type = "COLD"
                else:
                    s_type = "STEADY"
                wr_streaks[str(p_name).strip().lower()] = (s_type, l4_avg, s_avg, rel_pct, diff_yds)

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

    sec_inj_map: dict[str, tuple[str, str, str]] = {}
    if not inj_df.empty and "team" in inj_df.columns:
        d_inj = inj_df[inj_df["team"] == def_tm].copy()
        for _, r_i in d_inj.iterrows():
            c_nm = str(r_i.get("player_display", "")).strip().lower()
            st_str = str(r_i.get("report_status", "")).strip().upper()
            prac_str = str(r_i.get("practice_status_clean", "")).strip().upper()
            inj_type = str(r_i.get("primary_injury", "")).strip()
            sec_inj_map[c_nm] = (st_str, prac_str, inj_type)

    active_cbs = []
    missing_starting_cbs = []

    if not cb_roster.empty:
        for _, cb_row in cb_roster.iterrows():
            c_nm = cb_row["clean_name"]
            snap_sh = float(cb_row["def_snap_share"])
            p_disp = cb_row["player"]
            pos_u = cb_row["pos_upper"]
            raw_inj_status, raw_prac_status, inj_desc = sec_inj_map.get(c_nm, ("ACTIVE", "", ""))

            if is_excluded_from_cb_wr_matchup(raw_inj_status, raw_prac_status):
                if snap_sh >= 0.50:
                    missing_starting_cbs.append(
                        {
                            "name": p_disp,
                            "status": raw_inj_status,
                            "snap_pct": snap_sh * 100.0,
                            "injury": inj_desc,
                        }
                    )
            else:
                if is_active_unresolved_injury(raw_inj_status):
                    resolved_status = raw_inj_status
                elif raw_inj_status == "UNSPECIFIED (FP)" or (
                    c_nm in sec_inj_map and ("FULL" in raw_prac_status or raw_prac_status == "FP")
                ):
                    resolved_status = "UNSPECIFIED (FP)"
                elif raw_inj_status in CLEARED_DESIGNATIONS and c_nm in sec_inj_map:
                    resolved_status = "ACTIVE / CLEARED"
                else:
                    resolved_status = "ACTIVE"
                active_cbs.append(
                    {
                        "name": p_disp,
                        "pos": pos_u,
                        "snap_pct": snap_sh * 100.0,
                        "status": resolved_status,
                        "injury": inj_desc if is_active_unresolved_injury(resolved_status) else "",
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
            }
        )

    def_pass_rk = int(eff_df.loc[def_tm, "def_pass_epa_rank"]) if def_tm in eff_df.index else 16
    def_pass_epa = float(eff_df.loc[def_tm, "def_pass_epa"]) if def_tm in eff_df.index else 0.0

    alignments = ["WR1 vs CB1", "WR2 vs CB2", "Slot vs Nickel"]
    battles = []

    for idx, (_, wr_row) in enumerate(top_wrs.iterrows()):
        cb_assigned = active_cbs[min(idx, len(active_cbs) - 1)]
        wr_name = wr_row["player_name"]
        wr_clean = str(wr_name).strip().lower()
        wr_tgt_sh_frac = float(wr_row["calc_target_share"])
        wr_air_sh_frac = float(wr_row["calc_air_share"])
        wr_tgt_sh = wr_tgt_sh_frac * 100.0
        wr_air_sh = wr_air_sh_frac * 100.0
        wr_epa = float(wr_row["rec_epa"])
        wr_games = max(1, int(wr_row["games"]))
        wr_ypg = float(wr_row["rec_yards"]) / wr_games
        wr_is_fp_expected = wr_clean in off_fp_expected_players

        streak_type, l4_val, s_val, rel_pct, diff_yds = wr_streaks.get(
            wr_clean, ("STEADY", wr_ypg, wr_ypg, 0.0, 0.0)
        )

        score = 50.0

        tgt_pts = float(np.clip((wr_tgt_sh_frac - 0.16) * 48.0, -6.0, 10.0))
        ypg_pts = float(np.clip((wr_ypg - 55.0) * 0.18, -7.0, 9.0))
        air_pts = float(np.clip((wr_air_sh_frac - 0.26) * 15.0, -2.5, 3.5))
        wr_talent_pts = float(np.clip(tgt_pts + ypg_pts + air_pts, -12.0, 18.0))
        score += wr_talent_pts

        def_unit_pts = float(np.clip(((def_pass_rk - 16.5) / 15.5) * 13.0, -13.0, 13.0))
        score += def_unit_pts

        cb_snap_pct = float(cb_assigned["snap_pct"])
        cb_has_active_inj = is_active_unresolved_injury(cb_assigned["status"])
        if not missing_starting_cbs and not cb_has_active_inj and cb_snap_pct >= 85.0:
            score -= 1.5

        form_pts = float(np.clip(diff_yds * 0.30, -8.0, 8.0))
        score += form_pts

        rationale_clauses = []
        has_injury_or_backup_trigger = False

        if missing_starting_cbs and idx < len(missing_starting_cbs):
            out_cb = missing_starting_cbs[idx]
            score += 12.0
            has_injury_or_backup_trigger = True
            rationale_clauses.append(
                f"Starter {out_cb['name']} [{out_cb['status']}] • {cb_assigned['name']} ({cb_assigned['snap_pct']:.0f}% snaps) elevated."
            )
        elif missing_starting_cbs:
            out_cb = missing_starting_cbs[0]
            score += 7.0
            has_injury_or_backup_trigger = True
            rationale_clauses.append(
                f"Rotation shift ({out_cb['name']} [{out_cb['status']}]) • {cb_assigned['name']} draws coverage."
            )

        if cb_has_active_inj:
            score += 6.5 if "DNP" in cb_assigned["status"] or cb_assigned["status"] == "QUESTIONABLE" else 4.0
            has_injury_or_backup_trigger = True
            inj_detail = f" ({cb_assigned['injury']})" if cb_assigned.get("injury") else ""
            rationale_clauses.append(
                f"{cb_assigned['name']} [{cb_assigned['status']}]{inj_detail} • Gameday limitation risk."
            )

        if not missing_starting_cbs and not cb_has_active_inj and cb_snap_pct < 68.0:
            score += 4.5
            has_injury_or_backup_trigger = True
            rationale_clauses.append(
                f"Rotational CB ({cb_snap_pct:.0f}% snaps) • Exploitable perimeter cushion."
            )

        score = float(np.clip(round(score, 1), 15.0, 96.0))

        has_elite_catalyst = (
            (def_pass_rk >= 25)
            or has_injury_or_backup_trigger
            or (wr_ypg >= 75.0)
            or (l4_val >= 80.0)
        )
        if score >= 75.0 and not has_elite_catalyst:
            score = 72.5

        if score >= 75.0:
            tier_badge = '<span class="badge-elite">WR Edge</span>'
            tier_plain = "WR Edge"
            card_style = "terminal-card-elite"
        elif score >= 60.0:
            tier_badge = '<span class="badge-sage">Slight WR Edge</span>'
            tier_plain = "Slight WR Edge"
            card_style = "terminal-card"
        elif score <= 40.0:
            tier_badge = '<span class="badge-bad">CB Edge</span>'
            tier_plain = "CB Edge"
            card_style = "terminal-card-vuln"
        else:
            tier_badge = '<span class="badge-mid">Even</span>'
            tier_plain = "Even"
            card_style = "terminal-card"

        if streak_type == "HOT":
            wr_streak_badge = f'<span class="badge-hot">Hot L4: {l4_val:.1f} YPG</span>'
        elif streak_type == "WARM":
            wr_streak_badge = f'<span class="badge-amber">L4: {l4_val:.1f} YPG</span>'
        elif streak_type == "COLD":
            wr_streak_badge = f'<span class="badge-cold">Cold L4: {l4_val:.1f} YPG</span>'
        else:
            wr_streak_badge = f'<span class="badge-mid">L4: {l4_val:.1f} YPG</span>'

        if missing_starting_cbs and idx < len(missing_starting_cbs):
            cb_status_badge = '<span class="badge-bad">Backup CB</span>'
        elif cb_has_active_inj:
            cb_status_badge = f'<span class="badge-amber">{cb_assigned["status"].title()}</span>'
        elif def_pass_rk <= 5:
            cb_status_badge = '<span class="badge-bad">Top-5 Pass Def</span>'
        else:
            cb_status_badge = f'<span class="badge-mid">{cb_assigned["snap_pct"]:.0f}% Snaps</span>'

        if not rationale_clauses:
            clr_prefix = (
                "Full practice (expected to play) • "
                if (cb_assigned["status"] in ["ACTIVE / CLEARED", "UNSPECIFIED (FP)"] or wr_is_fp_expected)
                else ""
            )
            if score >= 75.0:
                rationale_clauses.append(
                    f"{clr_prefix}Alpha volume ({wr_tgt_sh:.1f}% tgt, {wr_ypg:.1f} YPG) vs #{def_pass_rk} {def_tm} pass def ({def_pass_epa:+.3f} EPA)."
                )
            elif score >= 60.0:
                rationale_clauses.append(
                    f"{clr_prefix}Volume edge ({wr_tgt_sh:.1f}% tgt, {l4_val:.1f} L4 YPG) vs #{def_pass_rk} {def_tm} pass def ({def_pass_epa:+.3f} EPA)."
                )
            elif score <= 40.0:
                rationale_clauses.append(
                    f"{clr_prefix}#{def_pass_rk} {def_tm} pass def ({def_pass_epa:+.3f} EPA) & {cb_assigned['name']} project to cap {wr_name}."
                )
            else:
                rationale_clauses.append(
                    f"{clr_prefix}Balanced battle ({wr_tgt_sh:.1f}% tgt) vs #{def_pass_rk} {def_tm} pass def ({def_pass_epa:+.3f} EPA)."
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
                "has_injury_trigger": has_injury_or_backup_trigger,
                "def_pass_rk": def_pass_rk,
                "tier_badge": tier_badge,
                "tier_plain": tier_plain,
                "card_style": card_style,
                "mismatch_score": score,
                "trigger_note": " ".join(rationale_clauses),
            }
        )

    return battles


def classify_unit_side(row: pd.Series) -> str:
    """Classifies a roster player into Offense, Defense, or Special Teams."""
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
    snaps_df: pd.DataFrame,
    usage_df: pd.DataFrame,
    teams: list[str],
    inj_matchup: pd.DataFrame | None = None,
) -> pd.DataFrame:
    """Merges full active roster snap counts with skill usage metrics and health status."""
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
                        "calc_rush_share",
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
        "calc_rush_share",
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
    merged = normalize_dataframe_guard_positions(merged, pos_col="position", name_col="player_name")
    merged["unit_group"] = merged.apply(classify_unit_side, axis=1)
    merged["team_logo"] = merged["team"].apply(get_team_logo_url)
    merged["target_share_pct"] = (merged["calc_target_share"] * 100.0).round(1)
    merged["rush_share_pct"] = (merged["calc_rush_share"] * 100.0).round(1)
    merged["primary_snap_pct"] = merged["primary_snap_pct"].round(1)
    merged["total_epa"] = merged["total_epa"].round(2)

    status_map: dict[tuple[str, str], str] = {}
    if inj_matchup is not None and not inj_matchup.empty and "clean_name" in inj_matchup.columns:
        for _, r_inj in inj_matchup.iterrows():
            tm_k = str(r_inj.get("team", "")).strip().upper()
            nm_k = str(r_inj.get("clean_name", "")).strip().lower()
            st_v = str(r_inj.get("report_status", "ACTIVE / CLEARED")).strip().upper()
            inj_v = str(r_inj.get("primary_injury", "")).strip()
            suffix = f" ({inj_v})" if inj_v and inj_v not in ["Undisclosed", "Unspecified Injury"] else ""
            status_map[(tm_k, nm_k)] = f"[{st_v}]{suffix}"

    merged["health_status"] = [
        status_map.get((str(r["team"]).strip().upper(), str(r["clean_name"]).strip().lower()), "[ACTIVE]")
        for _, r in merged.iterrows()
    ]

    return merged.sort_values(by=["primary_snap_pct", "touches", "targets"], ascending=False)


def build_injury_impact_report(
    injuries_df: pd.DataFrame,
    snaps_df: pd.DataFrame,
    usage_df: pd.DataFrame,
    teams: list[str],
    selected_week: int,
    game_is_completed: bool = False,
    snaps_season_matches: bool = False,
) -> pd.DataFrame:
    """Cross-references official weekly injury designations and mid-week practice participation."""
    if injuries_df.empty or "team" not in injuries_df.columns:
        return pd.DataFrame()

    team_inj = injuries_df[injuries_df["team"].isin(teams)].copy()
    if team_inj.empty:
        return pd.DataFrame()

    if "week" in team_inj.columns:
        team_inj["week"] = pd.to_numeric(team_inj["week"], errors="coerce").fillna(1).astype(int)
        if selected_week in team_inj["week"].values:
            team_inj = team_inj[team_inj["week"] == selected_week].copy()
        else:
            prior_weeks = team_inj[team_inj["week"] <= selected_week]
            if not prior_weeks.empty:
                latest_wk = int(prior_weeks["week"].max())
                team_inj = prior_weeks[prior_weeks["week"] == latest_wk].copy()
            else:
                latest_wk = int(team_inj["week"].max())
                team_inj = team_inj[team_inj["week"] == latest_wk].copy()

    if team_inj.empty:
        return pd.DataFrame()

    played_in_selected_week: set[tuple[str, str]] = set()
    if (
        game_is_completed
        and snaps_season_matches
        and not snaps_df.empty
        and {"player", "team", "week"}.issubset(snaps_df.columns)
    ):
        s_wk = snaps_df[
            (snaps_df["team"].isin(teams))
            & (pd.to_numeric(snaps_df["week"], errors="coerce") == selected_week)
        ].copy()
        for _, s_r in s_wk.iterrows():
            off_s = float(pd.to_numeric(s_r.get("offense_snaps", 0), errors="coerce") or 0)
            def_s = float(pd.to_numeric(s_r.get("defense_snaps", 0), errors="coerce") or 0)
            st_s = float(pd.to_numeric(s_r.get("st_snaps", 0), errors="coerce") or 0)
            if (off_s + def_s + st_s) > 0:
                played_in_selected_week.add(
                    (str(s_r["team"]).strip().upper(), str(s_r["player"]).strip().lower())
                )

    name_col = "full_name" if "full_name" in team_inj.columns else "player_name"
    team_inj["clean_name"] = team_inj[name_col].astype(str).str.strip().str.lower()
    team_inj["player_display"] = team_inj[name_col].astype(str).str.strip()
    if "position" in team_inj.columns:
        team_inj = normalize_dataframe_guard_positions(team_inj, pos_col="position", name_col="player_display")

    raw_status_col = "report_status" if "report_status" in team_inj.columns else (
        "game_status" if "game_status" in team_inj.columns else None
    )
    prac_col = "practice_status" if "practice_status" in team_inj.columns else None

    r_vals = team_inj[raw_status_col] if raw_status_col else pd.Series([""] * len(team_inj), index=team_inj.index)
    p_vals = team_inj[prac_col] if prac_col else pd.Series([""] * len(team_inj), index=team_inj.index)
    norm_list = [normalize_injury_designation(r_v, p_v) for r_v, p_v in zip(r_vals, p_vals)]

    team_inj["report_status"] = norm_list
    team_inj["practice_status_clean"] = (
        team_inj[prac_col].fillna("Unspecified").astype(str).str.strip()
        if prac_col
        else "N/A"
    )
    team_inj["combined_injury_desc"] = team_inj.apply(extract_combined_injury_name, axis=1)

    updated_statuses = []
    status_notes = []
    for _, r_inj in team_inj.iterrows():
        tm_u = str(r_inj["team"]).strip().upper()
        nm_l = str(r_inj["clean_name"]).strip().lower()
        cur_st = str(r_inj["report_status"]).strip().upper()

        if (tm_u, nm_l) in played_in_selected_week:
            updated_statuses.append("ACTIVE / CLEARED")
            status_notes.append(f"Confirmed Active on Field (Wk {selected_week} Snaps Logged)")
        else:
            updated_statuses.append(cur_st)
            status_notes.append(
                "Full Practice Participant (Expected to Play)"
                if not is_active_unresolved_injury(cur_st)
                else "Official NFL Injury / Practice Report"
            )

    team_inj["report_status"] = updated_statuses
    team_inj["status_source_note"] = status_notes

    valid_statuses = list(ACTIVE_INJURY_DESIGNATIONS | CLEARED_DESIGNATIONS)
    team_inj = team_inj[
        team_inj["report_status"].astype(str).str.upper().str.strip().isin(valid_statuses)
    ].copy()

    if team_inj.empty:
        return pd.DataFrame()

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
        "OG": 0.022,
        "LG": 0.022,
        "RG": 0.022,
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
        "SUSPENDED": 1.0,
        "NFI": 1.0,
        "DOUBTFUL": 0.75,
        "QUESTIONABLE": 0.35,
        "UNSPECIFIED (DNP)": 0.45,
        "UNSPECIFIED (LP)": 0.22,
    }

    roles, epa_penalties, impact_units, is_anchor_flags, is_cleared_flags = [], [], [], [], []

    for _, row in team_inj.iterrows():
        pos = str(row.get("position", "UNK")).upper().strip()
        snap = float(row["snap_share"])
        tgt = float(row["calc_target_share"])
        status_str = str(row["report_status"]).upper().strip()

        has_active_injury = is_active_unresolved_injury(status_str)
        is_cleared = not has_active_injury
        is_cleared_flags.append(is_cleared)

        is_key_player = (snap >= 0.65) or (tgt >= 0.18) or (pos == "QB" and snap >= 0.40)
        is_anchor = bool(is_key_player and has_active_injury)
        is_anchor_flags.append(is_anchor)

        if is_cleared:
            roles.append("Full Practice")
            penalty = 0.0
        else:
            if is_key_player:
                if pos in ["T", "LT", "RT", "G", "OG", "LG", "RG", "C"]:
                    roles.append("Starting OL")
                elif pos == "WR" or tgt >= 0.18:
                    roles.append("Primary Target")
                elif pos in ["DE", "EDGE", "DT"]:
                    roles.append("Pass Rusher")
                elif pos in ["CB", "S"]:
                    roles.append("Starting DB")
                elif pos == "QB":
                    roles.append("Starting QB")
                else:
                    roles.append("Starter")
            elif snap >= 0.35 or tgt >= 0.10:
                roles.append("Rotation")
            else:
                roles.append("Depth")

            base_w = pos_weights.get(pos, 0.015)
            usage_boost = 1.35 if tgt >= 0.20 else (1.15 if snap >= 0.75 else 0.75)
            prob_miss = status_prob_missing.get(status_str, 0.0)
            penalty = round(base_w * snap * usage_boost * prob_miss, 3)

        epa_penalties.append(penalty)

        if pos in ["QB", "WR", "TE", "T", "LT", "RT", "G", "OG", "LG", "RG", "C", "RB"]:
            impact_units.append("Offense")
        else:
            impact_units.append("Defense")

    team_inj["role_tier"] = roles
    team_inj["is_anchor"] = is_anchor_flags
    team_inj["is_cleared"] = is_cleared_flags
    team_inj["est_epa_penalty"] = epa_penalties
    team_inj["unit_side"] = impact_units
    team_inj["primary_injury"] = (
        team_inj["combined_injury_desc"]
        if "combined_injury_desc" in team_inj.columns
        else "Unspecified Injury"
    )

    return team_inj.sort_values(
        by=["is_cleared", "est_epa_penalty", "snap_share"],
        ascending=[True, False, False],
    )


def build_slate_best_bets_leaderboard(
    week_games: pd.DataFrame,
    eff_df: pd.DataFrame,
    player_df: pd.DataFrame,
    snaps_df: pd.DataFrame,
    injuries_df: pd.DataFrame,
    selected_season: int,
    selected_week: int,
    american_odds: int = -110,
    kelly_fraction: float = 0.25,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Scans EVERY game in the current week's slate and builds two league-wide leaderboards:
    1. Top Spread & Total Edges across the entire week
    2. Top Player Prop Plays across the entire week
    """
    if week_games.empty or eff_df.empty:
        return pd.DataFrame(), pd.DataFrame()

    game_edges_rows = []
    prop_edges_rows = []

    all_week_teams = sorted(
        pd.concat([week_games["away_team"], week_games["home_team"]]).dropna().unique().tolist()
    )
    all_usage = aggregate_team_skill_usage(player_df, all_week_teams)
    all_prop_logs = prepare_matchup_player_prop_logs(player_df, all_week_teams)

    for _, g_row in week_games.iterrows():
        at = str(g_row["away_team"]).strip().upper()
        ht = str(g_row["home_team"]).strip().upper()
        gid = str(g_row["game_id"])
        if at not in eff_df.index or ht not in eff_df.index:
            continue

        a_e = eff_df.loc[at]
        h_e = eff_df.loc[ht]

        g_inj = build_injury_impact_report(
            injuries_df,
            snaps_df,
            all_usage[all_usage["team"].isin([at, ht])] if not all_usage.empty else pd.DataFrame(),
            [at, ht],
            selected_week,
            game_is_completed=bool(pd.notna(g_row.get("away_score")) and pd.notna(g_row.get("home_score"))),
        )

        def _pen(tm_c: str, side_c: str) -> float:
            if g_inj.empty:
                return 0.0
            s_c = g_inj[(g_inj["team"] == tm_c) & (g_inj["unit_side"] == side_c) & (~g_inj["is_cleared"])]
            return float(s_c["est_epa_penalty"].sum()) if not s_c.empty else 0.0

        a_off_p, a_def_p = _pen(at, "Offense"), _pen(at, "Defense")
        h_off_p, h_def_p = _pen(ht, "Offense"), _pen(ht, "Defense")

        mkt_sp = g_row.get("home_spread", np.nan)
        mkt_tot = g_row.get("total_line", np.nan)
        rest_e = g_row.get("rest_edge_home", 0.0)
        roof_s = str(g_row.get("roof", "outdoors"))
        wind_v = float(g_row.get("wind", 0.0)) if pd.notna(g_row.get("wind")) else 0.0
        temp_v = float(g_row.get("temp", 65.0)) if pd.notna(g_row.get("temp")) else 65.0

        proj = compute_model_fair_line_and_totals(
            a_e, h_e, a_off_p, a_def_p, h_off_p, h_def_p, at, ht, mkt_sp, mkt_tot, rest_e, roof_s, wind_v, temp_v
        )

        sp_ev, sp_kelly = compute_ev_and_kelly(proj["spread_cover_prob"], american_odds, kelly_fraction)
        tot_ev, tot_kelly = compute_ev_and_kelly(proj["total_hit_prob"], american_odds, kelly_fraction)

        sp_edge_score = float(np.clip(50.0 + proj["spread_edge_pts"] * 7.5, 35.0, 96.0))
        tot_edge_score = float(np.clip(50.0 + proj["total_edge_pts"] * 6.5, 35.0, 94.0))

        game_edges_rows.append(
            {
                "game_id": gid,
                "Matchup": f"{at} @ {ht}",
                "Backed Team": proj["backed_spread_team"],
                "Market Type": "Spread",
                "Best Bet": proj["backed_spread_line_str"],
                "Market Line": f"{ht} {mkt_sp:+.1f}" if pd.notna(mkt_sp) else "TBD",
                "Model Fair Line": proj["fair_spread_str"],
                "Implied Score": f"{at} {proj['away_proj_pts']:.1f} - {ht} {proj['home_proj_pts']:.1f}",
                "Value Edge (Pts)": proj["spread_edge_pts"],
                "Edge Score": round(sp_edge_score, 1),
                "Win Prob %": round(proj["spread_cover_prob"] * 100.0, 1),
                "EV %": sp_ev,
                "Kelly Units": sp_kelly,
            }
        )

        if pd.notna(mkt_tot):
            game_edges_rows.append(
                {
                    "game_id": gid,
                    "Matchup": f"{at} @ {ht}",
                    "Backed Team": ht,
                    "Market Type": "Total (O/U)",
                    "Best Bet": f"{proj['total_lean_dir']} {float(mkt_tot):.1f}",
                    "Market Line": f"O/U {float(mkt_tot):.1f}",
                    "Model Fair Line": f"Proj Total {proj['fair_total']:.1f}",
                    "Implied Score": f"{at} {proj['away_proj_pts']:.1f} - {ht} {proj['home_proj_pts']:.1f}",
                    "Value Edge (Pts)": proj["total_edge_pts"],
                    "Edge Score": round(tot_edge_score, 1),
                    "Win Prob %": round(proj["total_hit_prob"] * 100.0, 1),
                    "EV %": tot_ev,
                    "Kelly Units": tot_kelly,
                }
            )

        g_picks = build_top_player_picks(
            all_usage[all_usage["team"].isin([at, ht])] if not all_usage.empty else pd.DataFrame(),
            all_prop_logs[all_prop_logs["team"].isin([at, ht])] if not all_prop_logs.empty else pd.DataFrame(),
            g_inj,
            eff_df,
            at,
            ht,
            american_odds=american_odds,
            kelly_fraction=kelly_fraction,
            top_n=3,
        )
        for pk in g_picks:
            prop_edges_rows.append(
                {
                    "game_id": gid,
                    "Matchup": f"{at} @ {ht}",
                    "Player": pk["player_name"],
                    "Team": pk["team"],
                    "Pos": pk["position"],
                    "Prop Play": pk["play_label"],
                    "Book Line": pk["line_val"],
                    "Model Proj": pk["model_proj"],
                    "Proj Delta": round(pk["model_proj"] - pk["line_val"], 1),
                    "Season Hit Rate": pk["hit_record"],
                    "Edge Score": pk["edge_score"],
                    "Win Prob %": pk["win_prob_pct"],
                    "EV %": pk["ev_pct"],
                    "Kelly Units": pk["kelly_units"],
                    "Rationale": pk["rationale"],
                    "l5_values": pk["l5_values"],
                    "mkt_label": pk["mkt_label"],
                }
            )

    game_edges_df = (
        pd.DataFrame(game_edges_rows).sort_values(by=["Edge Score", "Value Edge (Pts)"], ascending=False).reset_index(drop=True)
        if game_edges_rows
        else pd.DataFrame()
    )
    prop_edges_df = (
        pd.DataFrame(prop_edges_rows).sort_values(by=["Edge Score", "EV %"], ascending=False).reset_index(drop=True)
        if prop_edges_rows
        else pd.DataFrame()
    )
    return game_edges_df, prop_edges_df


def get_player_season_injury_history(
    injuries_df: pd.DataFrame,
    snaps_df: pd.DataFrame,
    player_name: str,
    team_abbr: str = "",
    selected_week: int | None = None,
) -> pd.DataFrame:
    """Extracts a player's week-by-week historical injury log across the entire season."""
    clean_nm = str(player_name).strip().lower()
    clean_tm = str(team_abbr).strip().upper()

    if injuries_df.empty:
        p_inj = pd.DataFrame()
    else:
        name_col = "full_name" if "full_name" in injuries_df.columns else "player_name"
        if "clean_name" not in injuries_df.columns and name_col in injuries_df.columns:
            injuries_df = injuries_df.copy()
            injuries_df["clean_name"] = injuries_df[name_col].astype(str).str.strip().str.lower()

        p_inj = injuries_df[injuries_df["clean_name"] == clean_nm].copy()
        if clean_tm and not p_inj.empty and "team" in p_inj.columns:
            if (p_inj["team"].astype(str).str.upper() == clean_tm).any():
                p_inj = p_inj[p_inj["team"].astype(str).str.upper() == clean_tm].copy()

    snap_by_week: dict[int, tuple[int, float]] = {}
    if not snaps_df.empty and "player" in snaps_df.columns and "week" in snaps_df.columns:
        p_sn = snaps_df[snaps_df["player"].astype(str).str.strip().str.lower() == clean_nm].copy()
        if clean_tm and not p_sn.empty and "team" in p_sn.columns:
            if (p_sn["team"].astype(str).str.upper() == clean_tm).any():
                p_sn = p_sn[p_sn["team"].astype(str).str.upper() == clean_tm]
        for _, s_r in p_sn.iterrows():
            wk_i = int(pd.to_numeric(s_r.get("week", 0), errors="coerce") or 0)
            off_s = int(pd.to_numeric(s_r.get("offense_snaps", 0), errors="coerce") or 0)
            def_s = int(pd.to_numeric(s_r.get("defense_snaps", 0), errors="coerce") or 0)
            st_s = int(pd.to_numeric(s_r.get("st_snaps", 0), errors="coerce") or 0)
            off_pct = float(pd.to_numeric(s_r.get("offense_pct", 0.0), errors="coerce") or 0.0)
            def_pct = float(pd.to_numeric(s_r.get("defense_pct", 0.0), errors="coerce") or 0.0)
            snap_by_week[wk_i] = (off_s + def_s + st_s, max(off_pct, def_pct) * 100.0)

    rows = []
    if not p_inj.empty and "week" in p_inj.columns:
        p_inj["week"] = pd.to_numeric(p_inj["week"], errors="coerce").fillna(1).astype(int)
        p_inj = p_inj.sort_values(by="week", ascending=False)

        raw_col = "report_status" if "report_status" in p_inj.columns else (
            "game_status" if "game_status" in p_inj.columns else None
        )
        prac_col = "practice_status" if "practice_status" in p_inj.columns else None

        for _, r in p_inj.iterrows():
            wk = int(r["week"])
            tm_r = str(r.get("team", clean_tm)).strip().upper()
            raw_st = str(r.get(raw_col, "")).strip() if raw_col and pd.notna(r.get(raw_col)) else ""
            prac_st = str(r.get(prac_col, "")).strip() if prac_col and pd.notna(r.get(prac_col)) else "N/A"
            norm_st = (
                str(r["normalized_status"]).strip().upper()
                if "normalized_status" in r and pd.notna(r["normalized_status"])
                else normalize_injury_designation(raw_st, prac_st)
            )

            injury_ailment = extract_combined_injury_name(r)

            tot_snaps, snap_pct = snap_by_week.get(wk, (0, 0.0))
            if selected_week is not None and wk < selected_week and tot_snaps > 0:
                gameday_outcome = f"ACTIVE ({tot_snaps} Snaps / {snap_pct:.0f}%)"
                if norm_st in ["QUESTIONABLE", "DOUBTFUL", "UNSPECIFIED (DNP)", "UNSPECIFIED (LP)"]:
                    norm_st = f"{norm_st} -> PLAYED"
            elif norm_st in ["OUT", "IR", "PUP", "SUSPENDED", "NFI"]:
                gameday_outcome = "DID NOT PLAY (INACTIVE)"
            elif not is_active_unresolved_injury(norm_st):
                gameday_outcome = "FULL PRACTICE / EXPECTED TO PLAY"
            else:
                gameday_outcome = "ON INJURY REPORT"

            mod_date = (
                str(r.get("date_modified", ""))[:10]
                if "date_modified" in r and pd.notna(r.get("date_modified"))
                else "Weekly Report"
            )

            rows.append(
                {
                    "Week": wk,
                    "Team": tm_r,
                    "Injury / Ailment": injury_ailment,
                    "Practice Participation": prac_st if prac_st and prac_st.lower() != "nan" else "N/A",
                    "Report Designation": norm_st,
                    "Gameday Participation": gameday_outcome,
                    "Updated": mod_date,
                }
            )

    return pd.DataFrame(rows)


def run_season_backtest(
    schedule_df: pd.DataFrame, eff_df: pd.DataFrame
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Grades all completed games in the selected season where extreme unit mismatches occurred."""
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

        h_pass_elite_mm = (h_eff["off_pass_epa_rank"] <= 5) and (a_eff["def_pass_epa_rank"] >= 23)
        a_pass_elite_mm = (a_eff["off_pass_epa_rank"] <= 5) and (h_eff["def_pass_epa_rank"] >= 23)
        if h_pass_elite_mm != a_pass_elite_mm:
            backed = ht if h_pass_elite_mm else at
            su, ats, push = grade_side(backed)
            records.append(
                {
                    "Week": int(row["week"]),
                    "Matchup": f"{at} @ {ht}",
                    "Category": "ELITE vs BAD Pass Unit",
                    "Backed Team": backed,
                    "Final Score": f"{at} {int(as_)} - {ht} {int(hs)}",
                    "Closing Spread": f"{ht} {-sp:+.1f}",
                    "SU Win": su,
                    "ATS Cover": ats,
                    "Push": push,
                }
            )

        h_rush_elite_mm = (h_eff["off_rush_epa_rank"] <= 5) and (a_eff["def_rush_epa_rank"] >= 23)
        a_rush_elite_mm = (a_eff["off_rush_epa_rank"] <= 5) and (h_eff["def_rush_epa_rank"] >= 23)
        if h_rush_elite_mm != a_rush_elite_mm:
            backed = ht if h_rush_elite_mm else at
            su, ats, push = grade_side(backed)
            records.append(
                {
                    "Week": int(row["week"]),
                    "Matchup": f"{at} @ {ht}",
                    "Category": "ELITE vs BAD Rush Unit",
                    "Backed Team": backed,
                    "Final Score": f"{at} {int(as_)} - {ht} {int(hs)}",
                    "Closing Spread": f"{ht} {-sp:+.1f}",
                    "SU Win": su,
                    "ATS Cover": ats,
                    "Push": push,
                }
            )

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
                    "Category": "Top-10 Off vs Bottom-10 Def",
                    "Backed Team": backed,
                    "Final Score": f"{at} {int(as_)} - {ht} {int(hs)}",
                    "Closing Spread": f"{ht} {-sp:+.1f}",
                    "SU Win": su,
                    "ATS Cover": ats,
                    "Push": push,
                }
            )

        rest_diff = row.get("rest_edge_home", 0)
        if pd.notna(rest_diff) and abs(rest_diff) >= 3:
            backed = ht if rest_diff > 0 else at
            su, ats, push = grade_side(backed)
            records.append(
                {
                    "Week": int(row["week"]),
                    "Matchup": f"{at} @ {ht}",
                    "Category": "Situational Rest Edge (3+ Days)",
                    "Backed Team": backed,
                    "Final Score": f"{at} {int(as_)} - {ht} {int(hs)}",
                    "Closing Spread": f"{ht} {-sp:+.1f}",
                    "SU Win": su,
                    "ATS Cover": ats,
                    "Push": push,
                }
            )

        net_home_epa = (h_eff["off_epa"] - a_eff["def_epa"]) - (a_eff["off_epa"] - h_eff["def_epa"])
        if abs(net_home_epa) >= 0.08:
            backed = ht if net_home_epa > 0 else at
            su, ats, push = grade_side(backed)
            records.append(
                {
                    "Week": int(row["week"]),
                    "Matchup": f"{at} @ {ht}",
                    "Category": "Net EPA Model Edge (>=0.08/play)",
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
# 4. INTERACTIVE POP-OUT MODALS (PLAYER DOSSIER & UNDERDOG-STYLE PROPS / BET SLIP)
# -----------------------------------------------------------------------------
if "inspect_player" in st.query_params:
    qp_name = st.query_params.get("inspect_player", "")
    qp_team = st.query_params.get("inspect_team", "")
    qp_pos = st.query_params.get("inspect_pos", "")
    qp_gid = st.query_params.get("game_id", "")
    if qp_gid:
        st.session_state["selected_game"] = qp_gid
    st.query_params.clear()
    if qp_name:
        trigger_player_popup(qp_name, qp_team, qp_pos)


def _fragment_decorator(func):
    """Wraps modal content functions in st.fragment when supported so interactions never refresh the page behind the pop-out."""
    if hasattr(st, "fragment"):
        return st.fragment(func)
    return func


@_fragment_decorator
def render_player_popup_contents(
    active_info: dict,
    roster_table: pd.DataFrame,
    prop_logs: pd.DataFrame,
    snaps_df: pd.DataFrame,
    inj_matchup: pd.DataFrame,
    injuries_full_df: pd.DataFrame,
    eff_df: pd.DataFrame,
    headshot_lookup: dict[str, dict],
    away_tm: str,
    home_tm: str,
    stat_season: int,
    inj_season: int,
    selected_week: int,
) -> None:
    """
    Renders the player pop-out dossier with a clean borderless headshot (no gradient overlay),
    season stats summary, interactive Props explorer, weekly game logs, and current + past season injuries.
    """
    p_name = str(active_info.get("name", "")).strip()
    p_team = str(active_info.get("team", "")).strip().upper()
    p_pos = str(active_info.get("position", "")).strip().upper()
    clean_nm = p_name.lower()

    r_match = pd.DataFrame()
    if not roster_table.empty and "player_name" in roster_table.columns:
        r_match = roster_table[
            roster_table["player_name"].astype(str).str.strip().str.lower() == clean_nm
        ]
        if p_team and not r_match.empty and (r_match["team"] == p_team).any():
            r_match = r_match[r_match["team"] == p_team]

    if not r_match.empty:
        r_row = r_match.iloc[0]
        if not p_team:
            p_team = str(r_row.get("team", "")).strip().upper()
        if not p_pos or p_pos == "UNK":
            p_pos = str(r_row.get("position", "UNK")).strip().upper()
        unit_side = str(r_row.get("unit_group", "Offense"))
    else:
        r_row = None
        unit_side = "Defense" if p_pos in DEFENSE_POSITIONS else "Offense"

    headshot_url, meta_info = get_player_headshot_and_meta(p_name, p_team, headshot_lookup)
    if not p_team and meta_info.get("team"):
        p_team = meta_info["team"]
    if (not p_pos or p_pos == "UNK") and meta_info.get("position"):
        p_pos = meta_info["position"]

    p_tm_color = resolve_team_display_color(p_team) if p_team else "#475569"
    initials = "".join([part[0].upper() for part in p_name.split()[:2] if part]) or "NFL"
    jersey_num = meta_info.get("jersey", "")
    college_str = meta_info.get("college", "")
    jersey_tag = f"#{jersey_num} • " if jersey_num else ""
    college_tag = f" • {college_str}" if college_str else ""

    if headshot_url:
        headshot_html = (
            f'<div class="player-headshot-wrap">'
            f'<img src="{headshot_url}" class="player-headshot-img" '
            f'alt="{p_name}" '
            f'onerror="this.style.display=\'none\';">'
            f"</div>"
        )
    else:
        headshot_html = (
            f'<div class="player-headshot-wrap">'
            f'<div class="player-headshot-fallback">{initials}</div>'
            f"</div>"
        )

    p_pos = normalize_guard_position(p_pos, "", p_name, p_team)
    player_inj_history = get_player_season_injury_history(
        injuries_full_df,
        snaps_df,
        p_name,
        p_team,
        selected_week=selected_week,
    )

    current_status_str = "ACTIVE / CLEAN REPORT"
    current_prac_badge = ""
    if not inj_matchup.empty and "player_display" in inj_matchup.columns:
        i_sub = inj_matchup[
            inj_matchup["player_display"].astype(str).str.strip().str.lower() == clean_nm
        ]
        if not i_sub.empty:
            i_row = i_sub.iloc[0]
            current_status_str = str(i_row["report_status"]).strip().upper()
            prim_inj_val = str(i_row.get("primary_injury", "")).strip()
            prac_val = str(i_row.get("practice_status_clean", "")).strip()
            current_prac_badge = render_practice_badge(prac_val) if prac_val and prac_val != "N/A" else ""
            if not is_active_unresolved_injury(current_status_str):
                inj_badge_html = (
                    f'{render_injury_badge(current_status_str)} '
                    f'<span class="badge-mid">{prim_inj_val}</span> '
                    f'<span class="badge-sage">0.00 EPA</span> '
                    f'{current_prac_badge}'
                )
            else:
                inj_badge_html = (
                    f'{render_injury_badge(current_status_str)} '
                    f'<span class="badge-bad">{prim_inj_val}</span> '
                    f'{current_prac_badge}'
                )
        else:
            inj_badge_html = '<span class="badge-elite">Active</span>'
    else:
        inj_badge_html = '<span class="badge-elite">Active</span>'

    opp_tm = home_tm if p_team == away_tm else away_tm
    render_html(
        f"""
        <div class="player-modal-banner" style="border-left: 5px solid {p_tm_color}; background: #121824;">
            <div class="player-modal-left">
                {headshot_html}
                <div class="player-modal-meta">
                    <div style="display:flex; align-items:center; flex-wrap:wrap; gap:6px;">
                        <span style="font-size:1.35rem; font-weight:800; color:#F8FAFC; font-family:Inter, -apple-system, BlinkMacSystemFont, sans-serif; font-variant-numeric:tabular-nums;">
                            {p_name}
                        </span>
                        {render_team_pill(p_team) if p_team else ""}
                        <span class="badge-sage">{p_pos or "NFL"}</span>
                        <span class="badge-mid">{unit_side}</span>
                    </div>
                    <div class="metric-subtext" style="margin-top:4px;">
                        {jersey_tag}{stat_season} Season • vs {opp_tm}{college_tag}
                    </div>
                    <div style="margin-top:6px;">
                        {inj_badge_html}
                    </div>
                </div>
            </div>
        </div>
        """
    )

    # Always show Season Stats Summary right at the top of the player pop-out
    if r_row is not None:
        s_games = int(r_row.get("games_played", 1))
        s_snap_pct = float(r_row.get("primary_snap_pct", 0.0))
        s_tot_snaps = int(r_row.get("total_snaps", 0))
        s_tgt_sh = float(r_row.get("target_share_pct", 0.0))
        s_rush_sh = float(r_row.get("rush_share_pct", 0.0))
        s_tgts = int(r_row.get("targets", 0))
        s_touches = int(r_row.get("touches", 0))
        s_scrim = int(r_row.get("scrimmage_yards", 0))
        s_pass = int(r_row.get("pass_yards", 0))
        s_tds = int(r_row.get("total_tds", 0))
        s_epa = float(r_row.get("total_epa", 0.0))

        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Season Games Active", f"{s_games} GP", delta=f"{s_tot_snaps} Snaps", delta_color="off")
        m2.metric("Snap Share", f"{s_snap_pct:.1f}%", delta=f"{unit_side}", delta_color="off")
        if p_pos == "QB":
            m3.metric("Passing Yards", f"{s_pass} Yds", delta=f"{s_scrim} Rush Yds", delta_color="off")
        elif unit_side == "Defense":
            def_s = int(r_row.get("def_snaps", s_tot_snaps))
            st_s = int(r_row.get("st_snaps", 0))
            m3.metric("Defensive Snaps", f"{def_s}", delta=f"{st_s} ST Snaps", delta_color="off")
        else:
            m3.metric(
                "Volume Share",
                f"{s_tgt_sh:.1f}% Tgt",
                delta=f"{s_rush_sh:.1f}% Rush ({s_tgts} Tgts)",
                delta_color="off",
            )
        m4.metric(
            "Scrimmage & EPA",
            f"{s_scrim} Yds ({s_tds} TD)",
            delta=f"{s_epa:+.2f} EPA ({s_touches} Touches)",
            delta_color="normal" if s_epa >= 0 else "inverse",
        )

    hist_count = len(player_inj_history)
    tab_props, tab_stats, tab_inj_hist = st.tabs(
        [
            "Props",
            "Game Logs",
            f"Injuries ({hist_count})" if hist_count > 0 else "Injuries",
        ]
    )

    p_logs = pd.DataFrame()
    if not prop_logs.empty and "player_label" in prop_logs.columns:
        p_logs = prop_logs[
            prop_logs["player_label"].astype(str).str.strip().str.lower() == clean_nm
        ].sort_values(by="week")

    p_snaps = pd.DataFrame()
    if not snaps_df.empty and "player" in snaps_df.columns:
        p_snaps = snaps_df[
            snaps_df["player"].astype(str).str.strip().str.lower() == clean_nm
        ].copy()
        if p_team and not p_snaps.empty and "team" in p_snaps.columns:
            if (p_snaps["team"] == p_team).any():
                p_snaps = p_snaps[p_snaps["team"] == p_team]
        if "week" in p_snaps.columns:
            p_snaps["week"] = pd.to_numeric(p_snaps["week"], errors="coerce").fillna(1).astype(int)
            p_snaps = p_snaps.sort_values(by="week")

    with tab_props:
        if p_logs.empty:
            st.info(f"No skill prop logs recorded for {p_name} ({p_pos}).")
        else:
            default_mkt = "Receiving Yards"
            if p_pos == "QB":
                default_mkt = "Passing Yards"
            elif p_pos in ["RB", "FB"]:
                default_mkt = "Rushing Yards"

            market_keys = list(PROP_MARKETS.keys())
            default_idx = market_keys.index(default_mkt) if default_mkt in market_keys else 0

            cov_map_modal = load_team_coverage_and_shell_splits(stat_season, eff_df)

            mc1, mc2, mc3 = st.columns([1.15, 1.25, 1.25])
            with mc1:
                sel_mkt = st.selectbox(
                    "Prop Market",
                    options=market_keys,
                    index=default_idx,
                    key=f"modal_prop_mkt_{clean_nm}",
                )
            stat_col, def_l, max_cap, stp = PROP_MARKETS[sel_mkt]
            is_td_int = stat_col in ["anytime_td", "receiving_tds", "interceptions"]
            is_rush = stat_col in ["rushing_yards", "carries"]
            def_unit_lbl = "Rush Def" if is_rush else "Pass Def"

            opp_def_rk = 16
            if not eff_df.empty and opp_tm in eff_df.index:
                opp_def_rk = int(
                    eff_df.loc[opp_tm, "def_rush_epa_rank" if is_rush else "def_pass_epa_rank"]
                )

            med_val = float(p_logs[stat_col].median()) if len(p_logs) > 0 else def_l
            smart_line = 0.5 if is_td_int else (round(med_val * 2) / 2 if med_val > 0 else def_l)
            dyn_max = float(max(max_cap, p_logs[stat_col].max() * 1.25, 3.5))

            with mc2:
                modal_line = st.slider(
                    f"Line ({sel_mkt})",
                    min_value=0.5,
                    max_value=float(round(dyn_max, 0) + 0.5),
                    value=float(min(max(0.5, smart_line), dyn_max)),
                    step=float(stp),
                    key=f"modal_prop_line_{clean_nm}_{stat_col}",
                )
            with mc3:
                sim_filter_mode = st.selectbox(
                    "Opponent Filter",
                    options=[
                        "All Past Games",
                        f"Similar Defenses to {opp_tm} (#{opp_def_rk} {def_unit_lbl})",
                    ],
                    index=0,
                    key=f"modal_sim_def_filter_{clean_nm}_{stat_col}",
                )

            # Enrich each past game with opponent defense rank, similarity score, and coverage splits
            p_logs_all = p_logs.copy().reset_index(drop=True)
            sim_details_list = []
            chart_x_labels = []
            is_sim_flags = []
            for _, r_lg in p_logs_all.iterrows():
                past_opp_code = str(r_lg.get("opp_label", "OPP")).strip().upper()
                sim_info = compute_defense_similarity(
                    opp_tm, past_opp_code, is_rush, eff_df, cov_map_modal
                )
                sim_details_list.append(sim_info)
                is_sim_flags.append(sim_info["is_similar"])
                chart_x_labels.append(f"Wk {int(r_lg['week'])} vs {past_opp_code} (#{sim_info['past_rk']})")

            p_logs_all["chart_label"] = chart_x_labels
            p_logs_all["is_similar_def"] = is_sim_flags
            p_logs_all["sim_info"] = sim_details_list

            if sim_filter_mode.startswith("Similar Defenses") and any(is_sim_flags):
                p_logs_chart = p_logs_all[p_logs_all["is_similar_def"]].copy().reset_index(drop=True)
            else:
                p_logs_chart = p_logs_all.copy().reset_index(drop=True)

            s_avg = float(p_logs_all[stat_col].mean())
            l3_avg = float(p_logs_all.tail(3)[stat_col].mean())
            sim_sub_df = p_logs_all[p_logs_all["is_similar_def"]]
            sim_avg = float(sim_sub_df[stat_col].mean()) if not sim_sub_df.empty else s_avg
            streak_badge, streak_delta = evaluate_player_streak_badge(
                s_avg, l3_avg, is_negative_stat=(stat_col == "interceptions")
            )

            p_logs_chart["hit"] = p_logs_chart[stat_col] >= modal_line
            p_logs_chart["bar_color"] = np.where(p_logs_chart["hit"], "#34D399", "#F87171")
            p_logs_chart["bar_line_color"] = np.where(p_logs_chart["is_similar_def"], "#38BDF8", "rgba(0,0,0,0)")
            p_logs_chart["bar_line_width"] = np.where(p_logs_chart["is_similar_def"], 2.0, 0.0)
            p_logs_chart["rolling_avg"] = p_logs_chart[stat_col].expanding().mean()

            hits_n = int(p_logs_chart["hit"].sum())
            tot_n = len(p_logs_chart)
            hit_pct = (hits_n / tot_n * 100.0) if tot_n > 0 else 0.0

            def_mult_m = 1.0 + ((opp_def_rk - 16.5) / 16.5) * 0.12
            modal_proj = round((0.55 * s_avg + 0.45 * l3_avg) * def_mult_m, 2 if is_td_int else 1)
            modal_dir = "OVER" if modal_proj >= modal_line else "UNDER"
            modal_wp = float(np.clip(0.50 + abs(modal_proj - modal_line) / max(2.0, s_avg * 0.65) * 0.22, 0.51, 0.74))
            modal_ev, modal_kelly = compute_ev_and_kelly(
                modal_wp,
                int(st.session_state.get("default_odds_american", -110)),
                float(st.session_state.get("kelly_fraction_mult", 0.25)),
            )
            modal_conf = round(50.0 + (modal_wp - 0.50) * 140.0, 1)

            pk1, pk2, pk3 = st.columns(3)
            pk1.metric(
                f"Hit Rate (vs {modal_line})",
                f"{hit_pct:.1f}% ({hits_n}/{tot_n})",
                delta="Over Trend" if hit_pct >= 55 else "Under Trend",
                delta_color="normal" if hit_pct >= 55 else "inverse",
            )
            pk2.metric(
                "L3 Form vs Season",
                f"{l3_avg:.2f} L3" if is_td_int else f"{l3_avg:.1f} L3",
                delta=streak_delta,
            )
            pk3.metric(
                f"vs {opp_tm} {def_unit_lbl}",
                f"Rank #{opp_def_rk}",
                delta=f"Avg vs Similar Defs: {sim_avg:.1f}" if not is_td_int else ("Favorable" if opp_def_rk >= 23 else "Neutral"),
                delta_color="normal" if opp_def_rk >= 23 else ("inverse" if opp_def_rk <= 8 else "off"),
            )

            render_compact_bet_action_row(
                key_prefix=f"modal_plr_pick_{clean_nm}_{stat_col}",
                season=stat_season,
                week=selected_week,
                matchup=f"{away_tm} @ {home_tm}",
                category=f"Player Prop ({sel_mkt})",
                selection=f"{p_name} {modal_dir} {modal_line} {sel_mkt}",
                market_line=f"{modal_line}",
                model_proj=f"Proj {modal_proj}",
                american_odds=int(st.session_state.get("default_odds_american", -110)),
                edge_score=modal_conf,
                ev_pct=modal_ev,
                kelly_units=modal_kelly,
                team_abbr=p_team,
                team_color_override=p_tm_color,
                button_text_override=f"{modal_dir} {modal_line} {sel_mkt}",
            )

            sim_count_badge = f'<span class="badge-sage">{int(sum(is_sim_flags))} Similar Def Matchups (Blue Border)</span>'
            render_html(
                f'<div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:6px; margin:4px 0 6px 0;">'
                f'<div>{streak_badge} {sim_count_badge}</div>'
                f'<span class="metric-subtext">Click any game bar below to compare that defense to {opp_tm}</span>'
                f"</div>"
            )

            fig_m = go.Figure()
            fig_m.add_trace(
                go.Bar(
                    x=p_logs_chart["chart_label"],
                    y=p_logs_chart[stat_col],
                    marker=dict(
                        color=p_logs_chart["bar_color"],
                        line=dict(
                            color=p_logs_chart["bar_line_color"],
                            width=p_logs_chart["bar_line_width"],
                        ),
                    ),
                    text=[
                        f"{v:.0f}" if (stp >= 1 or is_td_int) else f"{v:.1f}"
                        for v in p_logs_chart[stat_col]
                    ],
                    textposition="outside",
                    name=sel_mkt,
                )
            )
            fig_m.add_trace(
                go.Scatter(
                    x=p_logs_chart["chart_label"],
                    y=p_logs_chart["rolling_avg"],
                    mode="lines+markers",
                    line=dict(color=p_tm_color, width=2, dash="dot"),
                    name="Cumulative Avg",
                )
            )
            fig_m.add_hline(
                y=modal_line,
                line_width=2,
                line_dash="dash",
                line_color="#FBBF24",
                annotation_text=f"Line: {modal_line} ({hit_pct:.0f}% Hit)",
                annotation_position="top left",
                annotation_font=dict(color="#FBBF24", size=11),
            )
            y_max = max(float(p_logs_chart[stat_col].max()), modal_line) * 1.28 + 1.0
            fig_m.update_layout(
                dragmode=False,
                paper_bgcolor="#141923",
                plot_bgcolor="#141923",
                font=dict(color="#E2E8F0"),
                xaxis=dict(title="Week & Opponent (Defense Rank)", gridcolor="#222B3A", fixedrange=True),
                yaxis=dict(title=sel_mkt, range=[0, y_max], gridcolor="#222B3A", fixedrange=True),
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                height=300,
                margin=dict(l=16, r=16, t=32, b=24),
            )
            chart_sel_event = st.plotly_chart(
                fig_m,
                width="stretch",
                key=f"modal_plotly_{clean_nm}_{stat_col}_{sim_filter_mode}",
                on_select="rerun",
                selection_mode="points",
                config={"displayModeBar": False, "scrollZoom": False},
            )

            # Determine which past game is selected (via bar click or fallback selector)
            chart_labels_list = p_logs_chart["chart_label"].tolist()
            default_bar_idx = len(chart_labels_list) - 1
            if chart_sel_event and getattr(chart_sel_event, "selection", None):
                pts_sel = chart_sel_event.selection.get("points", [])
                if pts_sel:
                    pt_idx = pts_sel[0].get("point_index", pts_sel[0].get("pointNumber", default_bar_idx))
                    if isinstance(pt_idx, int) and 0 <= pt_idx < len(chart_labels_list):
                        default_bar_idx = pt_idx

            sel_game_lbl = st.selectbox(
                f"Compare Past Game Defense vs {opp_tm} (Or Click Any Bar on Chart Above)",
                options=chart_labels_list,
                index=default_bar_idx,
                key=f"modal_past_game_cmp_{clean_nm}_{stat_col}_{default_bar_idx}",
            )
            sel_game_row = p_logs_chart[p_logs_chart["chart_label"] == sel_game_lbl].iloc[0]
            sel_sim = sel_game_row["sim_info"]
            past_opp_tm = sel_sim["past_opp"]
            past_opp_c = get_team_primary_color(past_opp_tm)
            cur_opp_c = resolve_team_display_color(opp_tm)
            recorded_val = float(sel_game_row[stat_col])
            recorded_str = f"{recorded_val:.0f}" if (stp >= 1 or is_td_int) else f"{recorded_val:.1f}"
            hit_in_game = recorded_val >= modal_line

            # Side-by-side: (Left) Past Defense vs Current Opponent Defense Comparison
            # (Right) Defensive Coverage Shell (1-High vs 2-High & Man vs Zone) Breakdown
            cmp_col_l, cmp_col_r = st.columns(2)
            with cmp_col_l:
                sim_badge_cls = "badge-elite" if sel_sim["is_similar"] else "badge-mid"
                sim_badge_txt = f"{sel_sim['sim_pct']}% Match to {opp_tm}"
                res_badge_cls = "badge-elite" if hit_in_game else "badge-bad"
                res_badge_txt = f"{recorded_str} {sel_mkt} ({'Hit Over' if hit_in_game else 'Under'})"

                p_1h_bar = int(np.clip(round(sel_sim["past_1h"]), 10, 90))
                t_1h_bar = int(np.clip(round(sel_sim["target_1h"]), 10, 90))
                p_man_bar = int(np.clip(round(sel_sim["past_man"]), 10, 90))
                t_man_bar = int(np.clip(round(sel_sim["target_man"]), 10, 90))

                render_html(
                    f"""
                    <div class="terminal-card" style="border-left: 4px solid {past_opp_c}; border-right: 4px solid {cur_opp_c}; background:#141923;">
                        <div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:6px; margin-bottom:8px;">
                            <div style="font-weight:800; font-size:0.92rem; color:#F8FAFC;">
                                {render_inline_logo(past_opp_tm, 18)}{past_opp_tm} Defense vs {render_inline_logo(opp_tm, 18)}{opp_tm} Defense
                            </div>
                            <div>
                                <span class="{res_badge_cls}">{res_badge_txt}</span>
                                <span class="{sim_badge_cls}">{sim_badge_txt}</span>
                            </div>
                        </div>
                        <div class="unit-tier-row">
                            <span class="unit-tier-label">{def_unit_lbl} Rank & EPA</span>
                            <span class="unit-tier-right">
                                <b style="color:{past_opp_c};">{past_opp_tm} #{sel_sim['past_rk']}</b> <span class="unit-epa-mini">({sel_sim['past_epa']:+.2f})</span>
                                <span style="color:#64748B;">vs</span>
                                <b style="color:{cur_opp_c};">{opp_tm} #{sel_sim['target_rk']}</b> <span class="unit-epa-mini">({sel_sim['target_epa']:+.2f})</span>
                            </span>
                        </div>
                        <div class="unit-tier-row">
                            <span class="unit-tier-label">Success Rate Allowed</span>
                            <span class="unit-tier-right">
                                <b style="color:{past_opp_c};">{past_opp_tm} {sel_sim['past_sr']:.1f}%</b>
                                <span style="color:#64748B;">vs</span>
                                <b style="color:{cur_opp_c};">{opp_tm} {sel_sim['target_sr']:.1f}%</b>
                            </span>
                        </div>
                        <div class="unit-tier-row">
                            <span class="unit-tier-label">Safety Shell (1-High / 2-High)</span>
                            <span class="unit-tier-right">
                                <b style="color:{past_opp_c};">{past_opp_tm} {p_1h_bar}% / {100 - p_1h_bar}%</b>
                                <span style="color:#64748B;">vs</span>
                                <b style="color:{cur_opp_c};">{opp_tm} {t_1h_bar}% / {100 - t_1h_bar}%</b>
                            </span>
                        </div>
                        <div class="unit-tier-row">
                            <span class="unit-tier-label">Coverage (Man / Zone)</span>
                            <span class="unit-tier-right">
                                <b style="color:{past_opp_c};">{past_opp_tm} {p_man_bar}% / {100 - p_man_bar}%</b>
                                <span style="color:#64748B;">vs</span>
                                <b style="color:{cur_opp_c};">{opp_tm} {t_man_bar}% / {100 - t_man_bar}%</b>
                            </span>
                        </div>
                        <div class="unit-tier-row" style="border-bottom:none;">
                            <span class="unit-tier-label">Stacked Box (7+ Defenders)</span>
                            <span class="unit-tier-right">
                                <b style="color:{past_opp_c};">{past_opp_tm} {sel_sim['past_box']:.0f}%</b>
                                <span style="color:#64748B;">vs</span>
                                <b style="color:{cur_opp_c};">{opp_tm} {sel_sim['target_box']:.0f}%</b>
                            </span>
                        </div>
                    </div>
                    """
                )

            with cmp_col_r:
                t_cov_d = sel_sim["target_cov_dict"]
                t_1h_rk = int(t_cov_d.get("one_high_rank", 16))
                t_2h_rk = int(t_cov_d.get("two_high_rank", 16))
                t_man_rk = int(t_cov_d.get("man_rank", 16))
                t_zn_rk = int(t_cov_d.get("zone_rank", 16))
                prim_shell_str = str(t_cov_d.get("primary_shell", "Balanced Shell"))
                prim_cov_str = str(t_cov_d.get("primary_coverage", "Zone Heavy"))

                # Player performance vs 1-High / 2-High & Man / Zone based on past opponent scheme profiles
                one_h_games = [
                    float(r_g[stat_col])
                    for _, r_g in p_logs_all.iterrows()
                    if r_g["sim_info"]["past_1h"] >= 51.0
                ]
                two_h_games = [
                    float(r_g[stat_col])
                    for _, r_g in p_logs_all.iterrows()
                    if r_g["sim_info"]["past_1h"] < 51.0
                ]
                man_games = [
                    float(r_g[stat_col])
                    for _, r_g in p_logs_all.iterrows()
                    if r_g["sim_info"]["past_man"] >= 31.0
                ]
                zone_games = [
                    float(r_g[stat_col])
                    for _, r_g in p_logs_all.iterrows()
                    if r_g["sim_info"]["past_man"] < 31.0
                ]

                p_1h_avg = float(np.mean(one_h_games)) if one_h_games else round(s_avg * (0.94 if is_rush else 1.06), 1)
                p_2h_avg = float(np.mean(two_h_games)) if two_h_games else round(s_avg * (1.08 if is_rush else 0.95), 1)
                p_man_avg = float(np.mean(man_games)) if man_games else round(s_avg * 1.05, 1)
                p_zn_avg = float(np.mean(zone_games)) if zone_games else round(s_avg * 0.98, 1)

                render_html(
                    f"""
                    <div class="terminal-card" style="border-left: 4px solid {p_tm_color}; border-right: 4px solid {cur_opp_c}; background:#141923;">
                        <div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:6px; margin-bottom:8px;">
                            <div style="font-weight:800; font-size:0.92rem; color:#F8FAFC;">
                                {render_inline_logo(opp_tm, 18)}{opp_tm} Coverage Tendencies & {p_name} Splits
                            </div>
                            <div>
                                <span class="badge-sage">{prim_shell_str}</span>
                                <span class="badge-mid">{prim_cov_str}</span>
                            </div>
                        </div>
                        <div class="unit-tier-row">
                            <span class="unit-tier-label">1-High Safety ({sel_sim['target_1h']:.0f}% Snaps)</span>
                            <span class="unit-tier-right">
                                <span class="unit-epa-mini">{opp_tm} Def #{t_1h_rk}</span>
                                <span class="badge-elite">{p_name}: {p_1h_avg:.1f}/g</span>
                            </span>
                        </div>
                        <div class="unit-tier-row">
                            <span class="unit-tier-label">2-High Safety ({sel_sim['target_2h']:.0f}% Snaps)</span>
                            <span class="unit-tier-right">
                                <span class="unit-epa-mini">{opp_tm} Def #{t_2h_rk}</span>
                                <span class="badge-elite">{p_name}: {p_2h_avg:.1f}/g</span>
                            </span>
                        </div>
                        <div class="unit-tier-row">
                            <span class="unit-tier-label">Man Coverage ({sel_sim['target_man']:.0f}% Snaps)</span>
                            <span class="unit-tier-right">
                                <span class="unit-epa-mini">{opp_tm} Def #{t_man_rk}</span>
                                <span class="badge-sage">{p_name}: {p_man_avg:.1f}/g</span>
                            </span>
                        </div>
                        <div class="unit-tier-row" style="border-bottom:none;">
                            <span class="unit-tier-label">Zone Coverage ({sel_sim['target_zone']:.0f}% Snaps)</span>
                            <span class="unit-tier-right">
                                <span class="unit-epa-mini">{opp_tm} Def #{t_zn_rk}</span>
                                <span class="badge-sage">{p_name}: {p_zn_avg:.1f}/g</span>
                            </span>
                        </div>
                        <div class="tug-bar-track" style="height:6px; margin-top:6px;">
                            <div class="tug-bar-segment" style="width:{int(sel_sim['target_1h'])}%; background:{cur_opp_c};" title="1-High: {sel_sim['target_1h']:.0f}%"></div>
                            <div class="tug-bar-segment" style="width:{100 - int(sel_sim['target_1h'])}%; background:#38BDF8;" title="2-High: {sel_sim['target_2h']:.0f}%"></div>
                        </div>
                        <div style="display:flex; justify-content:space-between; font-size:0.70rem; color:#94A3B8; margin-top:2px;">
                            <span>{opp_tm} 1-High: {sel_sim['target_1h']:.0f}%</span>
                            <span>{opp_tm} 2-High: {sel_sim['target_2h']:.0f}% (Light Box: {100.0 - sel_sim['target_box']:.0f}%)</span>
                        </div>
                    </div>
                    """
                )

    with tab_stats:
        if not p_logs.empty:
            st.markdown(f"##### {stat_season} Weekly Game Logs ({len(p_logs)} Games)")
            log_disp_cols = [
                "week",
                "opp_label",
                "targets",
                "receptions",
                "receiving_yards",
                "receiving_tds",
                "carries",
                "rushing_yards",
                "rushing_tds",
                "scrimmage_yards",
                "anytime_td",
                "passing_yards",
                "passing_tds",
                "interceptions",
            ]
            avail_c = [c for c in log_disp_cols if c in p_logs.columns]
            st.dataframe(
                p_logs[avail_c].sort_values(by="week", ascending=False),
                width="stretch",
                hide_index=True,
            )

        if not p_snaps.empty:
            st.markdown(f"##### {stat_season} Snap Participation Log")
            snap_copy = p_snaps.copy()
            for pct_c in ["offense_pct", "defense_pct", "st_pct"]:
                if pct_c in snap_copy.columns:
                    snap_copy[pct_c] = (pd.to_numeric(snap_copy[pct_c], errors="coerce").fillna(0.0) * 100.0).round(1)
            snap_cols = [
                c
                for c in ["week", "opponent", "offense_snaps", "offense_pct", "defense_snaps", "defense_pct", "st_snaps", "st_pct"]
                if c in snap_copy.columns
            ]
            st.dataframe(
                snap_copy[snap_cols].sort_values(by="week", ascending=False),
                width="stretch",
                hide_index=True,
            )

        if p_logs.empty and p_snaps.empty:
            st.info(f"No weekly stat or snap logs recorded for {p_name} in {stat_season}.")

    with tab_inj_hist:
        if player_inj_history.empty:
            render_html(
                f"""
                <div class="terminal-card-elite" style="margin-top:8px;">
                    <span class="badge-elite">Clean {inj_season} Injury Log</span>
                    <p class="metric-subtext" style="margin:6px 0 0 0;">
                        {p_name} ({p_team} {p_pos}) has no weekly injury report entries in {inj_season}.
                    </p>
                </div>
                """
            )
        else:
            st.dataframe(
                player_inj_history,
                width="stretch",
                hide_index=True,
            )


@_fragment_decorator
def render_underdog_props_and_betslip_modal(
    selected_season: int,
    selected_week: int,
    away_tm: str,
    home_tm: str,
    away_color: str,
    home_color: str,
    spread_v: float,
    total_v: float,
    model_proj_dict: dict,
    line_move_dict: dict,
    usage_matchup: pd.DataFrame,
    prop_logs_matchup: pd.DataFrame,
    inj_matchup: pd.DataFrame,
    eff_df: pd.DataFrame,
    headshot_lookup: dict[str, dict],
    default_odds: int,
    kelly_mult: float,
) -> None:
    """
    Renders the dedicated Underdog-style Matchup Picks & Bet Slip pop-out modal.
    - Clean, high-contrast line callouts with concise buttons ('OVER 94.5 Rec Yds', 'UNDER 94.5 Rec Yds').
    - Selectable player name pills inside every prop card so clicking a player opens their Player Dossier directly.
    """
    slip_items = st.session_state.get("bet_slip", [])
    slip_count = len(slip_items)
    total_kelly_staked = sum(float(item.get("Kelly Stake (u)", 0.0)) for item in slip_items)
    focus_info = st.session_state.get("active_pick_focus") or {}
    focus_sel = str(focus_info.get("selection", "")).strip()

    focus_banner_html = (
        f'<span class="badge-elite">Selected: {focus_sel}</span>'
        if focus_sel
        else f'<span class="badge-sage">Odds {default_odds:+d} • {kelly_mult:.2f}x Kelly</span>'
    )

    render_html(
        f"""
        <div class="active-game-spotlight" style="padding:10px 14px; margin:0 0 10px 0; border-left:4px solid {away_color}; border-right:4px solid {home_color}; background:linear-gradient(90deg, {hex_to_rgba(away_color, 0.16)} 0%, #121824 50%, {hex_to_rgba(home_color, 0.16)} 100%);">
            <div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:8px;">
                <div style="display:flex; align-items:center; gap:8px; flex-wrap:wrap;">
                    {render_team_pill(away_tm, "Away", color_override=away_color)}
                    <span style="font-family:Inter, -apple-system, BlinkMacSystemFont, sans-serif; font-variant-numeric:tabular-nums; font-weight:800; color:#94A3B8;">@</span>
                    {render_team_pill(home_tm, "Home", color_override=home_color)}
                    <span class="metric-subtext">Matchup Picks & Prop Board</span>
                </div>
                <div>
                    {focus_banner_html}
                    <span class="badge-elite">{slip_count} Picks • {total_kelly_staked:.2f}u</span>
                </div>
            </div>
        </div>
        """
    )

    tab_matchup_board, tab_bet_slip = st.tabs(
        [
            "Picks & Props",
            f"Bet Slip ({slip_count})" if slip_count > 0 else "Bet Slip",
        ]
    )

    with tab_matchup_board:
        # ---------------------------------------------------------------------
        # 1. CURRENT MATCHUP TEAM PICKS (SPREAD, MONEYLINE, TOTAL OVER/UNDER)
        # ---------------------------------------------------------------------
        render_html(
            f"""
            <div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:6px; margin-bottom:6px;">
                <h4 style="margin:0; color:#F8FAFC;">Team Picks ({away_tm} @ {home_tm})</h4>
                <span class="metric-subtext">Tap any Spread, Moneyline, or Total line to toggle in your Bet Slip</span>
            </div>
            """
        )

        matchup_str = f"{away_tm} @ {home_tm}"
        fair_sp_str = model_proj_dict.get("fair_spread_str", "PK")
        fair_tot_val = model_proj_dict.get("fair_total", 44.5)
        backed_sp_tm = model_proj_dict.get("backed_spread_team", home_tm)
        sp_cov_p = float(model_proj_dict.get("spread_cover_prob", 0.524))
        away_sp_prob = sp_cov_p if backed_sp_tm == away_tm else (1.0 - sp_cov_p)
        home_sp_prob = sp_cov_p if backed_sp_tm == home_tm else (1.0 - sp_cov_p)

        away_sp_line = f"{away_tm} {-float(spread_v):+.1f}" if pd.notna(spread_v) else f"{away_tm} PK"
        home_sp_line = f"{home_tm} {float(spread_v):+.1f}" if pd.notna(spread_v) else f"{home_tm} PK"
        away_sp_ev, away_sp_k = compute_ev_and_kelly(away_sp_prob, default_odds, kelly_mult)
        home_sp_ev, home_sp_k = compute_ev_and_kelly(home_sp_prob, default_odds, kelly_mult)

        away_ml_odds = int(line_move_dict.get("away_ml_int", -110))
        home_ml_odds = int(line_move_dict.get("home_ml_int", -110))
        away_wp_raw = float(model_proj_dict.get("away_win_prob_raw", 0.50))
        home_wp_raw = float(model_proj_dict.get("home_win_prob_raw", 0.50))
        away_ml_ev, away_ml_k = compute_ev_and_kelly(away_wp_raw, away_ml_odds, kelly_mult)
        home_ml_ev, home_ml_k = compute_ev_and_kelly(home_wp_raw, home_ml_odds, kelly_mult)

        tot_line_num = float(total_v) if pd.notna(total_v) else fair_tot_val
        tot_lean = model_proj_dict.get("total_lean_dir", "OVER")
        tot_hit_p = float(model_proj_dict.get("total_hit_prob", 0.524))
        over_prob = tot_hit_p if tot_lean == "OVER" else (1.0 - tot_hit_p)
        under_prob = tot_hit_p if tot_lean == "UNDER" else (1.0 - tot_hit_p)
        over_ev, over_k = compute_ev_and_kelly(over_prob, default_odds, kelly_mult)
        under_ev, under_k = compute_ev_and_kelly(under_prob, default_odds, kelly_mult)

        tm_c1, tm_c2, tm_c3 = st.columns(3)
        with tm_c1:
            with st.container(border=True):
                render_html(
                    f'<div class="context-cell-title" style="margin-bottom:6px;">Point Spread (Fair: <b style="color:#F8FAFC;">{fair_sp_str}</b>)</div>'
                )
                render_compact_bet_action_row(
                    key_prefix="ud_sp_away",
                    season=selected_season,
                    week=selected_week,
                    matchup=matchup_str,
                    category="Spread",
                    selection=away_sp_line,
                    market_line=away_sp_line,
                    model_proj=f"Fair {fair_sp_str}",
                    american_odds=default_odds,
                    edge_score=round(away_sp_prob * 100.0, 1),
                    ev_pct=away_sp_ev,
                    kelly_units=away_sp_k,
                    team_abbr=away_tm,
                    team_color_override=away_color,
                    button_text_override=away_sp_line,
                )
                render_compact_bet_action_row(
                    key_prefix="ud_sp_home",
                    season=selected_season,
                    week=selected_week,
                    matchup=matchup_str,
                    category="Spread",
                    selection=home_sp_line,
                    market_line=home_sp_line,
                    model_proj=f"Fair {fair_sp_str}",
                    american_odds=default_odds,
                    edge_score=round(home_sp_prob * 100.0, 1),
                    ev_pct=home_sp_ev,
                    kelly_units=home_sp_k,
                    team_abbr=home_tm,
                    team_color_override=home_color,
                    button_text_override=home_sp_line,
                )

        with tm_c2:
            with st.container(border=True):
                render_html(
                    f'<div class="context-cell-title" style="margin-bottom:6px;">Moneyline (<b style="color:{away_color};">{away_tm} {away_wp_raw*100:.0f}%</b> | <b style="color:{home_color};">{home_tm} {home_wp_raw*100:.0f}%</b>)</div>'
                )
                render_compact_bet_action_row(
                    key_prefix="ud_ml_away",
                    season=selected_season,
                    week=selected_week,
                    matchup=matchup_str,
                    category="Moneyline",
                    selection=f"{away_tm} ML ({away_ml_odds:+d})",
                    market_line=f"{away_ml_odds:+d}",
                    model_proj=f"Win {away_wp_raw*100:.1f}%",
                    american_odds=away_ml_odds,
                    edge_score=round(away_wp_raw * 100.0, 1),
                    ev_pct=away_ml_ev,
                    kelly_units=away_ml_k,
                    team_abbr=away_tm,
                    team_color_override=away_color,
                    button_text_override=f"{away_tm} ML ({away_ml_odds:+d})",
                )
                render_compact_bet_action_row(
                    key_prefix="ud_ml_home",
                    season=selected_season,
                    week=selected_week,
                    matchup=matchup_str,
                    category="Moneyline",
                    selection=f"{home_tm} ML ({home_ml_odds:+d})",
                    market_line=f"{home_ml_odds:+d}",
                    model_proj=f"Win {home_wp_raw*100:.1f}%",
                    american_odds=home_ml_odds,
                    edge_score=round(home_wp_raw * 100.0, 1),
                    ev_pct=home_ml_ev,
                    kelly_units=home_ml_k,
                    team_abbr=home_tm,
                    team_color_override=home_color,
                    button_text_override=f"{home_tm} ML ({home_ml_odds:+d})",
                )

        with tm_c3:
            with st.container(border=True):
                render_html(
                    f'<div class="context-cell-title" style="margin-bottom:6px;">Game Total (Model Proj: <b style="color:#F8FAFC;">{fair_tot_val:.1f} Pts</b>)</div>'
                )
                render_compact_bet_action_row(
                    key_prefix="ud_tot_over",
                    season=selected_season,
                    week=selected_week,
                    matchup=matchup_str,
                    category="Total (O/U)",
                    selection=f"OVER {tot_line_num:.1f} Total Pts",
                    market_line=f"O/U {tot_line_num:.1f}",
                    model_proj=f"Proj {fair_tot_val:.1f}",
                    american_odds=default_odds,
                    edge_score=round(over_prob * 100.0, 1),
                    ev_pct=over_ev,
                    kelly_units=over_k,
                    team_abbr=away_tm,
                    team_color_override="#34D399",
                    button_text_override=f"OVER {tot_line_num:.1f}",
                )
                render_compact_bet_action_row(
                    key_prefix="ud_tot_under",
                    season=selected_season,
                    week=selected_week,
                    matchup=matchup_str,
                    category="Total (O/U)",
                    selection=f"UNDER {tot_line_num:.1f} Total Pts",
                    market_line=f"O/U {tot_line_num:.1f}",
                    model_proj=f"Proj {fair_tot_val:.1f}",
                    american_odds=default_odds,
                    edge_score=round(under_prob * 100.0, 1),
                    ev_pct=under_ev,
                    kelly_units=under_k,
                    team_abbr=home_tm,
                    team_color_override="#38BDF8",
                    button_text_override=f"UNDER {tot_line_num:.1f}",
                )

        # ---------------------------------------------------------------------
        # 2. BEST & MOST POPULAR PLAYER PICKS (CLEAN SCANNABLE LINES + CLICKABLE PLAYERS)
        # ---------------------------------------------------------------------
        render_html(
            f"""
            <div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:6px; margin:12px 0 6px 0;">
                <h4 style="margin:0; color:#F8FAFC;">Player Props ({away_tm} @ {home_tm})</h4>
                <span class="metric-subtext">Click Player Name for Dossier • Tap OVER or UNDER to add to Bet Slip</span>
            </div>
            """
        )

        popular_picks = build_top_player_picks(
            usage_matchup,
            prop_logs_matchup,
            inj_matchup,
            eff_df,
            away_tm,
            home_tm,
            american_odds=default_odds,
            kelly_fraction=kelly_mult,
            top_n=8,
        )

        if not popular_picks:
            st.info("No player prop projections available for this matchup.")
        else:
            pop_cols = st.columns(2)
            for idx_p, pk in enumerate(popular_picks):
                p_tm_c = resolve_team_display_color(pk["team"])
                p_pic_html = render_mismatch_headshot_html(
                    pk["player_name"], pk["team"], headshot_lookup
                )
                spark_html = render_l5_sparkbars_html(pk["l5_values"], pk["line_val"])
                under_wp = max(0.28, 1.0 - (pk["win_prob_pct"] / 100.0))
                under_ev, under_k = compute_ev_and_kelly(under_wp, default_odds, kelly_mult)

                with pop_cols[idx_p % 2]:
                    with st.container(border=True):
                        # Selectable Player Name Trigger at the top of each Prop Card
                        hdr_l, hdr_r = st.columns([1.45, 0.95])
                        with hdr_l:
                            render_inline_player_trigger(
                                pk["player_name"],
                                pk["team"],
                                pk["position"],
                                f"ud_pop_plr_{idx_p}",
                                f"{pk['team']} {pk['position']}",
                            )
                        with hdr_r:
                            render_html(
                                f'<div style="text-align:right; padding-top:2px;">'
                                f'<span class="badge-elite">Proj {pk["model_proj"]:.1f}</span>'
                                f"</div>"
                            )

                        # Prominent, At-a-Glance Prop Line Callout + Centered Avatar + L5 Sparkbar
                        render_html(
                            f"""
                            <div style="display:flex; align-items:center; justify-content:space-between; gap:10px; border-left:4px solid {p_tm_c}; padding-left:8px; margin:4px 0 8px 0;">
                                <div style="display:flex; align-items:center; gap:10px;">
                                    {p_pic_html}
                                    <div>
                                        <div style="font-family:Inter, -apple-system, BlinkMacSystemFont, sans-serif; font-variant-numeric:tabular-nums; font-size:1.06rem; font-weight:900; color:#FBBF24; line-height:1.2;">
                                            {pk['line_val']:.1f} {pk['mkt_label']}
                                        </div>
                                        <div class="metric-subtext" style="font-size:0.74rem; color:#CBD5E1; margin-top:2px;">
                                            Model: <b>{pk['model_proj']:.1f}</b> &bull; Hit: <b>{pk['hit_record']}</b>
                                        </div>
                                    </div>
                                </div>
                                <div style="text-align:right;">
                                    <span class="metric-subtext" style="font-size:0.60rem;">L5 VS {pk['line_val']}</span><br>
                                    {spark_html}
                                </div>
                            </div>
                            """
                        )

                        # Clean OVER / UNDER Buttons (Only the Line Text!)
                        btn_o_col, btn_u_col = st.columns(2)
                        with btn_o_col:
                            render_compact_bet_action_row(
                                key_prefix=f"ud_pop_over_{idx_p}",
                                season=selected_season,
                                week=selected_week,
                                matchup=matchup_str,
                                category=f"Player Prop ({pk['position']})",
                                selection=f"{pk['player_name']} {pk['play_label']}",
                                market_line=f"{pk['line_val']} {pk['mkt_label']}",
                                model_proj=f"Proj {pk['model_proj']:.1f}",
                                american_odds=default_odds,
                                edge_score=pk["edge_score"],
                                ev_pct=pk["ev_pct"],
                                kelly_units=pk["kelly_units"],
                                team_abbr=pk["team"],
                                team_color_override=p_tm_c,
                                button_text_override=pk["play_label"],
                            )
                        with btn_u_col:
                            render_compact_bet_action_row(
                                key_prefix=f"ud_pop_under_{idx_p}",
                                season=selected_season,
                                week=selected_week,
                                matchup=matchup_str,
                                category=f"Player Prop ({pk['position']})",
                                selection=f"{pk['player_name']} {pk['under_label']}",
                                market_line=f"{pk['line_val']} {pk['mkt_label']}",
                                model_proj=f"Proj {pk['model_proj']:.1f}",
                                american_odds=default_odds,
                                edge_score=round(100.0 - pk["edge_score"], 1),
                                ev_pct=under_ev,
                                kelly_units=under_k,
                                team_abbr=pk["team"],
                                team_color_override="#64748B",
                                button_text_override=pk["under_label"],
                            )

        # Custom Prop Explorer inside the pop-out modal
        with st.expander("Custom Matchup Player Prop Builder (Any Player & Alt Line)", expanded=False):
            if not prop_logs_matchup.empty:
                r_sum = (
                    prop_logs_matchup.groupby(["player_label", "team", "pos_clean"], as_index=False)
                    .agg(scrim=("scrimmage_yards", "sum"), pass_y=("passing_yards", "sum"))
                )
                r_sum["score"] = r_sum["scrim"] + r_sum["pass_y"] * 0.4
                r_sum = r_sum.sort_values(by="score", ascending=False)
                r_sum["opt"] = r_sum["player_label"] + " (" + r_sum["team"] + " - " + r_sum["pos_clean"] + ")"

                cc1, cc2, cc3 = st.columns([1.3, 1.2, 1.2])
                with cc1:
                    c_plr_opt = st.selectbox("Select Player", r_sum["opt"].tolist(), key="ud_cust_plr")
                c_row = r_sum[r_sum["opt"] == c_plr_opt].iloc[0]
                c_nm, c_tm, c_pos = c_row["player_label"], c_row["team"], c_row["pos_clean"]
                c_color = resolve_team_display_color(c_tm)
                with cc2:
                    c_mkt = st.selectbox("Market", list(PROP_MARKETS.keys()), key="ud_cust_mkt")
                c_scol, c_defl, c_maxc, c_stp = PROP_MARKETS[c_mkt]
                c_plogs = prop_logs_matchup[
                    (prop_logs_matchup["player_label"] == c_nm) & (prop_logs_matchup["team"] == c_tm)
                ].sort_values(by="week")
                c_med = float(c_plogs[c_scol].median()) if not c_plogs.empty else c_defl
                with cc3:
                    c_line = st.slider(
                        "Alt Line",
                        min_value=0.5,
                        max_value=float(max(c_maxc, c_med * 1.6, 5.5)),
                        value=float(max(0.5, round(c_med * 2) / 2)),
                        step=float(c_stp),
                        key=f"ud_cust_line_{c_nm}_{c_scol}",
                    )
                c_avg = float(c_plogs[c_scol].mean()) if not c_plogs.empty else c_line
                c_dir = "OVER" if c_avg >= c_line else "UNDER"
                c_ev, c_k = compute_ev_and_kelly(0.56, default_odds, kelly_mult)
                render_compact_bet_action_row(
                    key_prefix=f"ud_cust_{c_nm}_{c_scol}",
                    season=selected_season,
                    week=selected_week,
                    matchup=matchup_str,
                    category=f"Custom Prop ({c_mkt})",
                    selection=f"{c_nm} {c_dir} {c_line} {c_mkt}",
                    market_line=f"{c_line}",
                    model_proj=f"Season Avg {c_avg:.1f}",
                    american_odds=default_odds,
                    edge_score=64.0,
                    ev_pct=c_ev,
                    kelly_units=c_k,
                    team_abbr=c_tm,
                    team_color_override=c_color,
                    button_text_override=f"{c_dir} {c_line} {c_mkt}",
                )

    with tab_bet_slip:
        slip_items_now = st.session_state.get("bet_slip", [])
        n_now = len(slip_items_now)
        tot_u_now = sum(float(x.get("Kelly Stake (u)", 0.0)) for x in slip_items_now)
        avg_ev_now = (
            float(np.mean([float(x.get("EV %", 0.0)) for x in slip_items_now]))
            if n_now > 0
            else 0.0
        )

        sk1, sk2, sk3 = st.columns(3)
        sk1.metric("Tracked Picks", f"{n_now} Selections")
        sk2.metric("Combined Kelly Stake", f"{tot_u_now:.2f} Units")
        sk3.metric("Average Expected Value", f"{avg_ev_now:+.1f}% EV")

        if not slip_items_now:
            st.info(
                "Your Bet Slip is currently empty. Switch to the **Matchup Picks & Player Props** tab above to add team lines or player props."
            )
        else:
            for s_idx, item in enumerate(list(slip_items_now)):
                tm_code = str(item.get("Team", "")).strip().upper()
                tm_hex = resolve_team_display_color(tm_code) if tm_code else "#38BDF8"
                row_l, row_r = st.columns([5.2, 0.8])
                with row_l:
                    render_html(
                        f"""
                        <div style="background:{hex_to_rgba(tm_hex, 0.16)}; border:1px solid {hex_to_rgba(tm_hex, 0.55)}; border-left:4px solid {tm_hex}; border-radius:6px; padding:7px 10px; margin-bottom:5px; font-family:Inter, -apple-system, BlinkMacSystemFont, sans-serif; font-variant-numeric:tabular-nums; font-size:0.78rem;">
                            <div>{render_inline_logo(tm_code, 15) if tm_code else ""}<b>{item['Selection']}</b> <span style="color:#94A3B8;">({item['Matchup']} • {item['Market Type']})</span></div>
                            <div style="color:#CBD5E1; margin-top:2px;">{item['Model Projection']} • Odds <b>{item['Odds']}</b> • <span style="color:#34D399; font-weight:700;">{item['EV %']:+.1f}% EV</span> • <b>{item['Kelly Stake (u)']:.2f}u Kelly</b></div>
                        </div>
                        """
                    )
                with row_r:
                    if st.button(
                        "✕",
                        key=f"modal_rm_slip_{s_idx}_{item['pick_id']}",
                        help=f"Remove {item['Selection']}",
                        use_container_width=True,
                    ):
                        st.session_state["bet_slip"].pop(s_idx)
                        st.rerun(scope="fragment") if "fragment" in st.rerun.__doc__.lower() else None

            slip_df_export = pd.DataFrame(slip_items_now).drop(columns=["pick_id"], errors="ignore")
            b_dl, b_clr = st.columns(2)
            with b_dl:
                st.download_button(
                    label="Export Bet Slip (.csv)",
                    data=slip_df_export.to_csv(index=False).encode("utf-8"),
                    file_name=f"football_edger_bet_slip_{selected_season}_wk{selected_week}.csv",
                    mime="text/csv",
                    type="primary",
                    use_container_width=True,
                    key="modal_dl_csv_btn",
                )
            with b_clr:
                if st.button("Clear All Picks", use_container_width=True, key="modal_clear_all_btn"):
                    st.session_state["bet_slip"] = []
                    st.toast("Cleared all picks from Bet Slip")


# -----------------------------------------------------------------------------
# 5. SIDEBAR CONTROLS, ODDS/KELLY SETTINGS & FEED SYNC
# -----------------------------------------------------------------------------
st.sidebar.markdown("## Controls")

backtest_mode = st.sidebar.toggle(
    "Historical Backtest Mode",
    value=False,
    help="Switch between 2024, 2025, and 2026 seasons and grade historical ATS cover rates.",
)

if backtest_mode:
    selected_season = st.sidebar.selectbox("Season", [2025, 2024, 2026], index=0)
else:
    selected_season = st.sidebar.selectbox("Season", [2026, 2025, 2024], index=0)

with st.spinner(f"Loading {selected_season} nflverse feeds..."):
    master_games_df = load_master_games_csv()
    schedule_df = load_season_schedule(selected_season)
    eff_df, eff_season = load_team_efficiency_csv(selected_season)
    player_df, player_season = load_player_stats_csv(selected_season)
    snaps_df, snaps_season = load_snap_counts_csv(selected_season)
    injuries_df, inj_season = load_injuries_csv(
        selected_season, st.session_state["injury_refresh_token"]
    )
    roster_headshots_raw = load_rosters_headshots_csv(player_season)
    headshot_lookup = build_headshot_lookup(player_df, roster_headshots_raw)

if schedule_df.empty:
    st.error("Could not load NFL schedule CSV from nflverse.")
    st.stop()

available_weeks = sorted(schedule_df["week"].dropna().astype(int).unique())
default_week_idx = get_default_nfl_week_index(schedule_df, available_weeks)
selected_week = st.sidebar.selectbox(
    "Week (Auto-Synced)",
    available_weeks,
    index=default_week_idx,
)

all_teams = sorted(
    pd.concat([schedule_df["home_team"], schedule_df["away_team"]]).dropna().unique()
)
selected_team = st.sidebar.selectbox("Team Filter", ["All Teams"] + all_teams)
only_primetime = st.sidebar.checkbox("Primetime Only", value=False)

st.sidebar.divider()
st.sidebar.markdown("### Odds & Kelly Sizing")
odds_choice = st.sidebar.selectbox(
    "Default Market Odds (Vig)",
    options=[-105, -110, -115, -120, -125, +100, +105],
    index=1,
    format_func=lambda x: f"{x:+d} ({american_odds_to_decimal_and_prob(x)[1]*100:.1f}% Breakeven)",
)
st.session_state["default_odds_american"] = int(odds_choice)

kelly_choice = st.sidebar.selectbox(
    "Kelly Stake Multiplier",
    options=[
        ("Quarter-Kelly (0.25x • Conservative)", 0.25),
        ("Half-Kelly (0.50x • Balanced)", 0.50),
        ("Full-Kelly (1.00x • Aggressive)", 1.00),
    ],
    index=0,
    format_func=lambda x: x[0],
)
st.session_state["kelly_fraction_mult"] = float(kelly_choice[1])

st.sidebar.divider()
st.sidebar.markdown("### Live Injury Feed Sync")
if st.sidebar.button(
    "Refresh Injury Feed",
    use_container_width=True,
):
    st.session_state["injury_refresh_token"] += 1
    load_injuries_csv.clear()
    st.rerun()

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

valid_game_ids = week_games["game_id"].astype(str).tolist()
filter_sig = f"{selected_season}_{selected_week}_{selected_team}_{only_primetime}"
next_game_idx = get_default_next_game_index(week_games)

if (
    "selected_game" not in st.session_state
    or st.session_state["selected_game"] not in valid_game_ids
    or st.session_state.get("_last_week_filter_sig") != filter_sig
):
    st.session_state["_last_week_filter_sig"] = filter_sig
    st.session_state["selected_game_idx"] = next_game_idx
    st.session_state["selected_game"] = valid_game_ids[next_game_idx]
else:
    st.session_state["selected_game_idx"] = valid_game_ids.index(
        st.session_state["selected_game"]
    )

active_game = week_games.iloc[st.session_state["selected_game_idx"]]
away_tm = str(active_game["away_team"]).strip().upper()
home_tm = str(active_game["home_team"]).strip().upper()
away_color, home_color = get_matchup_team_colors(away_tm, home_tm)
st.session_state["active_matchup_colors"] = {
    away_tm: away_color,
    home_tm: home_color,
    normalize_team_code(away_tm): away_color,
    normalize_team_code(home_tm): home_color,
}

team_records_map = compute_team_records(schedule_df, through_week=selected_week)
division_standings_map = compute_nfl_division_standings(schedule_df, through_week=selected_week)

# -----------------------------------------------------------------------------
# 6. PINNED TOP BAR & DISTINCT WORKSPACE SWITCHER (CURRENT MATCHUP VS LEAGUE HUB)
# -----------------------------------------------------------------------------
top_hdr_left, top_hdr_mid, top_hdr_right = st.columns([1.25, 1.35, 0.90])
with top_hdr_left:
    st.markdown(f"### Football Edger — {selected_season} Week {selected_week}")
with top_hdr_mid:
    workspace_options = [
        "Matchup",
        "League Hub",
    ]
    cur_ws_idx = 1 if st.session_state.get("top_workspace_section") == "NFL League Hub" else 0
    chosen_ws = st.radio(
        "Primary Workspace",
        options=workspace_options,
        index=cur_ws_idx,
        horizontal=True,
        label_visibility="collapsed",
        key="primary_workspace_radio",
    )
    is_league_hub = chosen_ws == "League Hub"
    st.session_state["top_workspace_section"] = "NFL League Hub" if is_league_hub else "Current Matchup"
with top_hdr_right:
    if not is_league_hub:
        nav_prev_col, nav_next_col = st.columns(2)
        cur_g_idx = int(st.session_state["selected_game_idx"])
        with nav_prev_col:
            if st.button(
                "Prev Game",
                disabled=(cur_g_idx <= 0),
                use_container_width=True,
                key="top_prev_game_btn",
            ):
                new_idx = max(0, cur_g_idx - 1)
                st.session_state["selected_game_idx"] = new_idx
                st.session_state["selected_game"] = valid_game_ids[new_idx]
                st.session_state["open_player_modal"] = False
                st.session_state["open_props_slip_modal"] = False
                st.rerun()
        with nav_next_col:
            if st.button(
                "Next Game",
                disabled=(cur_g_idx >= len(valid_game_ids) - 1),
                use_container_width=True,
                key="top_next_game_btn",
            ):
                new_idx = min(len(valid_game_ids) - 1, cur_g_idx + 1)
                st.session_state["selected_game_idx"] = new_idx
                st.session_state["selected_game"] = valid_game_ids[new_idx]
                st.session_state["open_player_modal"] = False
                st.session_state["open_props_slip_modal"] = False
                st.rerun()
    else:
        render_html(
            f'<div style="text-align:right; padding-top:6px;">'
            f'<span class="active-lock-pill" style="border-color:#38BDF8;">LEAGUE SLATE: {len(week_games)} GAMES</span>'
            f"</div>"
        )

if eff_df.empty:
    st.info("Efficiency data unavailable for this season.")
    st.stop()

# Shared Matchup Context Calculations (Fast single-game scope)
away_norm = normalize_team_code(away_tm)
home_norm = normalize_team_code(home_tm)
away_div_name = get_team_division(away_norm)
home_div_name = get_team_division(home_norm)

spread_v = active_game.get("home_spread", np.nan)
total_v = active_game.get("total_line", np.nan)
rest_v = active_game.get("rest_edge_home", 0)
roof_str = str(active_game.get("roof", "outdoors")).capitalize()
surface_str = str(active_game.get("surface", "Grass")).capitalize() if pd.notna(active_game.get("surface")) else "Grass"
temp_val = float(active_game.get("temp", 65.0)) if pd.notna(active_game.get("temp")) else np.nan
wind_val = float(active_game.get("wind", 0.0)) if pd.notna(active_game.get("wind")) else np.nan
stadium_str = active_game.get("stadium", "TBD")
slot_str = active_game.get("broadcast_slot", "")
away_pts = active_game.get("away_score", np.nan)
home_pts = active_game.get("home_score", np.nan)
active_game_is_completed = bool(pd.notna(away_pts) and pd.notna(home_pts))

spread_str = f"{home_tm} {spread_v:+.1f}" if pd.notna(spread_v) else "Spread TBD"
total_str = f"O/U {total_v:.1f}" if pd.notna(total_v) else "Total TBD"
final_score_badge = (
    f'<span class="badge-amber">Final: {away_tm} {int(away_pts)} - {home_tm} {int(home_pts)}</span>'
    if active_game_is_completed
    else '<span class="badge-sage">Upcoming</span>'
)
slot_badge = f'<span class="badge-mid">{slot_str}</span>' if slot_str else ""

if pd.notna(rest_v) and rest_v > 0:
    rest_badge = f'<span class="badge-elite">{home_tm} +{int(rest_v)}d Rest</span>'
elif pd.notna(rest_v) and rest_v < 0:
    rest_badge = f'<span class="badge-elite">{away_tm} +{int(abs(rest_v))}d Rest</span>'
else:
    rest_badge = '<span class="badge-mid">Even Rest</span>'

a_eff = eff_df.loc[away_tm] if away_tm in eff_df.index else None
h_eff = eff_df.loc[home_tm] if home_tm in eff_df.index else None
usage_matchup = aggregate_team_skill_usage(player_df, [away_tm, home_tm])

inj_matchup = build_injury_impact_report(
    injuries_df,
    snaps_df,
    usage_matchup,
    [away_tm, home_tm],
    selected_week,
    game_is_completed=active_game_is_completed,
    snaps_season_matches=(snaps_season == selected_season and snaps_season == inj_season),
)
h2h_5yr = get_five_year_h2h_history(master_games_df, away_tm, home_tm, selected_season)
roster_matchup_table = build_roster_usage_table(
    snaps_df, usage_matchup, [away_tm, home_tm], inj_matchup
)
prop_logs_matchup = prepare_matchup_player_prop_logs(player_df, [away_tm, home_tm])


def get_unit_penalty_from_df(inj_df_src: pd.DataFrame, tm: str, side: str) -> float:
    """Strictly sums unit EPA penalties ONLY for active unresolved injury designations."""
    if inj_df_src.empty:
        return 0.0
    sub = inj_df_src[
        (inj_df_src["team"] == tm)
        & (inj_df_src["unit_side"] == side)
        & (~inj_df_src["is_cleared"])
        & (inj_df_src["report_status"].apply(is_active_unresolved_injury))
    ]
    if sub.empty:
        return 0.0
    return float(sub["est_epa_penalty"].sum())


away_off_pen = get_unit_penalty_from_df(inj_matchup, away_tm, "Offense")
away_def_pen = get_unit_penalty_from_df(inj_matchup, away_tm, "Defense")
home_off_pen = get_unit_penalty_from_df(inj_matchup, home_tm, "Offense")
home_def_pen = get_unit_penalty_from_df(inj_matchup, home_tm, "Defense")

model_proj_dict = (
    compute_model_fair_line_and_totals(
        a_eff,
        h_eff,
        away_off_pen,
        away_def_pen,
        home_off_pen,
        home_def_pen,
        away_tm,
        home_tm,
        spread_v,
        total_v,
        rest_v,
        roof_str,
        wind_val if pd.notna(wind_val) else 0.0,
        temp_val if pd.notna(temp_val) else 65.0,
    )
    if (a_eff is not None and h_eff is not None)
    else {}
)

line_move_dict = estimate_line_movement_and_splits(
    active_game, model_proj_dict, away_tm, home_tm
)

default_odds = int(st.session_state["default_odds_american"])
kelly_mult = float(st.session_state["kelly_fraction_mult"])

# =============================================================================
# WORKSPACE 1: CURRENT MATCHUP (ALL ACTIVE GAME TABS IN ONE UNIFORM HUB)
# =============================================================================
if not is_league_hub:
    render_nfl_horizontal_ticker(week_games, team_records_map)

    away_rec_str = team_records_map.get(away_tm, "0-0")
    home_rec_str = team_records_map.get(home_tm, "0-0")

    proj_score_pill = (
        f'<span class="badge-elite">Proj: {away_tm} {model_proj_dict["away_proj_pts"]:.1f}, {home_tm} {model_proj_dict["home_proj_pts"]:.1f}</span>'
        if model_proj_dict
        else ""
    )
    game_state_pill = (
        f'<span class="badge-amber">Final: {away_tm} {int(away_pts)} - {home_tm} {int(home_pts)}</span>'
        if active_game_is_completed
        else f'<span class="badge-sage">{spread_str} • {total_str}</span>'
    )
    weather_short = f"{roof_str} • {surface_str}"
    if pd.notna(temp_val) and roof_str.lower() not in ["dome", "closed"]:
        weather_short += f" • {int(temp_val)}°F"

    render_html(
        f"""
        <div class="active-game-spotlight" style="border-left: 4px solid {away_color}; border-right: 4px solid {home_color}; background: #141923;">
            <div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:10px;">
                <div style="display:flex; align-items:center; flex-wrap:wrap; gap:8px;">
                    {render_team_pill(away_tm, away_rec_str, large=True, color_override=away_color)}
                    <span style="font-size:0.95rem; font-weight:700; color:#64748B;">@</span>
                    {render_team_pill(home_tm, home_rec_str, large=True, color_override=home_color)}
                    <span class="metric-subtext" style="margin-left:4px;">{stadium_str} ({weather_short})</span>
                </div>
                <div style="display:flex; align-items:center; flex-wrap:wrap; gap:6px;">
                    {game_state_pill}
                    {proj_score_pill}
                </div>
            </div>
        </div>
        """
    )

    # CONCISE 1-2 WORD GAME TABS
    (
        game_tab_overview,
        game_tab_mismatches,
        game_tab_injuries,
        game_tab_epa,
        game_tab_props_rosters,
    ) = st.tabs(
        [
            "Overview",
            "Matchups",
            "Injuries",
            "Team Stats",
            "Props & Depth",
        ]
    )

    # -------------------------------------------------------------------------
    # CURRENT GAME TAB 1: OVERVIEW (FLAT MODERN, CONCISE TAGS, SCROLL-FIRST)
    # -------------------------------------------------------------------------
    with game_tab_overview:
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

            best_phase_val = max(
                [
                    (f"{away_tm} Pass Offense", away_pass_edge, away_color),
                    (f"{away_tm} Rush Offense", away_rush_edge, away_color),
                    (f"{home_tm} Pass Offense", home_pass_edge, home_color),
                    (f"{home_tm} Rush Offense", home_rush_edge, home_color),
                ],
                key=lambda x: x[1],
            )

            total_flagged_inj = (
                int((~inj_matchup["is_cleared"]).sum())
                if not inj_matchup.empty and "is_cleared" in inj_matchup.columns
                else 0
            )
            cleared_count = (
                int(inj_matchup["is_cleared"].sum())
                if not inj_matchup.empty and "is_cleared" in inj_matchup.columns
                else 0
            )

            sp_edge_pts = model_proj_dict.get("spread_edge_pts", 0.0)
            backed_line_str = model_proj_dict.get("backed_spread_line_str", f"{model_lean_team} Edge")
            backed_tm_code = model_proj_dict.get("backed_spread_team", model_lean_team)
            backed_tm_color = home_color if backed_tm_code == home_tm else away_color
            fair_home_sp = float(model_proj_dict.get("fair_home_spread", 0.0))
            if fair_home_sp < 0:
                proj_margin_plain = f"Model: {home_tm} by {abs(fair_home_sp):.1f}"
            elif fair_home_sp > 0:
                proj_margin_plain = f"Model: {away_tm} by {abs(fair_home_sp):.1f}"
            else:
                proj_margin_plain = "Model: Even"

            open_fav_c = home_color if line_move_dict.get("open_fav_tm", home_tm) == home_tm else away_color
            cur_fav_c = home_color if line_move_dict.get("cur_fav_tm", home_tm) == home_tm else away_color
            inj_pill_cls = "custom-kpi-pill-neg" if total_flagged_inj > 0 else "custom-kpi-pill-pos"

            render_html(
                f"""
                <div class="custom-kpi-grid">
                    <div class="custom-kpi-card" style="border-top: 3px solid {backed_tm_color};">
                        <div class="custom-kpi-top">
                            <span class="custom-kpi-label">Model Pick</span>
                        </div>
                        <div class="custom-kpi-val">{render_inline_logo(backed_tm_code, 20)}{backed_line_str}</div>
                        <span class="custom-kpi-pill-pos">{proj_margin_plain} (+{sp_edge_pts:.1f} pt edge)</span>
                    </div>
                    <div class="custom-kpi-card" style="border-top: 3px solid {home_color};">
                        <div class="custom-kpi-top">
                            <span class="custom-kpi-label">Win Probability</span>
                        </div>
                        <div class="custom-kpi-val">
                            <span style="color:{away_color};">{away_tm} {model_proj_dict['away_win_prob']:.0f}%</span>
                            <span style="color:#64748B; font-size:0.95rem;"> • </span>
                            <span style="color:{home_color};">{home_tm} {model_proj_dict['home_win_prob']:.0f}%</span>
                        </div>
                        <span class="badge-mid">Open <b style="color:{open_fav_c};">{line_move_dict['open_sp_str']}</b> &rarr; Now <b style="color:{cur_fav_c};">{line_move_dict['cur_sp_str']}</b></span>
                    </div>
                    <div class="custom-kpi-card" style="border-top: 3px solid {best_phase_val[2]};">
                        <div class="custom-kpi-top">
                            <span class="custom-kpi-label">Key Advantage</span>
                        </div>
                        <div class="custom-kpi-val">{best_phase_val[0]}</div>
                        <span class="custom-kpi-pill-pos">{best_phase_val[1]:+.2f} EPA/Play Edge</span>
                    </div>
                    <div class="custom-kpi-card {'custom-kpi-card-warn' if total_flagged_inj > 0 else 'custom-kpi-card-edge'}">
                        <div class="custom-kpi-top">
                            <span class="custom-kpi-label">Injury Status</span>
                        </div>
                        <div class="custom-kpi-val">{total_flagged_inj} Flagged • {cleared_count} Cleared</div>
                        <span class="{inj_pill_cls}">{away_tm} -{away_off_pen + away_def_pen:.2f} EPA • {home_tm} -{home_off_pen + home_def_pen:.2f} EPA</span>
                    </div>
                </div>
                """
            )

            # HYPERLINKED TEAM PICK BOXES (SPREAD, TOTAL O/U & MONEYLINE; OPENS MATCHUP PICKS POP-OUT ON CLICK)
            q_bet1, q_bet2, q_bet3 = st.columns(3)
            sp_ev_v, sp_kelly_v = compute_ev_and_kelly(model_proj_dict["spread_cover_prob"], default_odds, kelly_mult)
            tot_ev_v, tot_kelly_v = compute_ev_and_kelly(model_proj_dict["total_hit_prob"], default_odds, kelly_mult)

            ov_away_ml_odds = int(line_move_dict.get("away_ml_int", -110))
            ov_home_ml_odds = int(line_move_dict.get("home_ml_int", -110))
            ov_away_wp = float(model_proj_dict.get("away_win_prob_raw", 0.50))
            ov_home_wp = float(model_proj_dict.get("home_win_prob_raw", 0.50))
            ov_away_ml_ev, ov_away_ml_k = compute_ev_and_kelly(ov_away_wp, ov_away_ml_odds, kelly_mult)
            ov_home_ml_ev, ov_home_ml_k = compute_ev_and_kelly(ov_home_wp, ov_home_ml_odds, kelly_mult)

            if ov_away_ml_ev > ov_home_ml_ev or (ov_away_ml_ev == ov_home_ml_ev and ov_away_wp > ov_home_wp):
                ml_pick_tm = away_tm
                ml_pick_color = away_color
                ml_pick_odds = ov_away_ml_odds
                ml_pick_wp = ov_away_wp
                ml_pick_ev = ov_away_ml_ev
                ml_pick_kelly = ov_away_ml_k
            else:
                ml_pick_tm = home_tm
                ml_pick_color = home_color
                ml_pick_odds = ov_home_ml_odds
                ml_pick_wp = ov_home_wp
                ml_pick_ev = ov_home_ml_ev
                ml_pick_kelly = ov_home_ml_k
            ml_pick_lbl = f"{ml_pick_tm} ML ({ml_pick_odds:+d})"

            with q_bet1:
                render_compact_bet_action_row(
                    key_prefix=f"ov_sp_{active_game['game_id']}",
                    season=selected_season,
                    week=selected_week,
                    matchup=f"{away_tm} @ {home_tm}",
                    category="Spread",
                    selection=model_proj_dict["backed_spread_line_str"],
                    market_line=spread_str,
                    model_proj=f"Fair {model_proj_dict['fair_spread_str']}",
                    american_odds=default_odds,
                    edge_score=50.0 + model_proj_dict["spread_edge_pts"] * 7.5,
                    ev_pct=sp_ev_v,
                    kelly_units=sp_kelly_v,
                    team_abbr=backed_tm_code,
                    team_color_override=backed_tm_color,
                    open_matchup_modal_on_click=True,
                    button_text_override=model_proj_dict["backed_spread_line_str"],
                )
            with q_bet2:
                if pd.notna(total_v):
                    tot_pick_lbl = f"{model_proj_dict['total_lean_dir']} {float(total_v):.1f}"
                    render_compact_bet_action_row(
                        key_prefix=f"ov_tot_{active_game['game_id']}",
                        season=selected_season,
                        week=selected_week,
                        matchup=f"{away_tm} @ {home_tm}",
                        category="Total (O/U)",
                        selection=f"{tot_pick_lbl} Total Pts",
                        market_line=f"O/U {float(total_v):.1f}",
                        model_proj=f"Proj {model_proj_dict['fair_total']:.1f}",
                        american_odds=default_odds,
                        edge_score=50.0 + model_proj_dict["total_edge_pts"] * 6.5,
                        ev_pct=tot_ev_v,
                        kelly_units=tot_kelly_v,
                        team_abbr=home_tm,
                        team_color_override=home_color,
                        open_matchup_modal_on_click=True,
                        button_text_override=f"{tot_pick_lbl} Total Pts",
                    )
            with q_bet3:
                render_compact_bet_action_row(
                    key_prefix=f"ov_ml_{active_game['game_id']}",
                    season=selected_season,
                    week=selected_week,
                    matchup=f"{away_tm} @ {home_tm}",
                    category="Moneyline",
                    selection=ml_pick_lbl,
                    market_line=f"{ml_pick_odds:+d}",
                    model_proj=f"Win {ml_pick_wp*100:.1f}%",
                    american_odds=ml_pick_odds,
                    edge_score=round(ml_pick_wp * 100.0, 1),
                    ev_pct=ml_pick_ev,
                    kelly_units=ml_pick_kelly,
                    team_abbr=ml_pick_tm,
                    team_color_override=ml_pick_color,
                    open_matchup_modal_on_click=True,
                    button_text_override=ml_pick_lbl,
                )

            col_brief_left, col_brief_right = st.columns([1.15, 1.05])

            # 3. TEAM-COLORED UNIT TIER MATRIX (AWAY COLOR VS HOME COLOR)
            with col_brief_left:
                a_pass_rk, a_rush_rk = int(a_eff["off_pass_epa_rank"]), int(a_eff["off_rush_epa_rank"])
                a_pdef_rk, a_rdef_rk = int(a_eff["def_pass_epa_rank"]), int(a_eff["def_rush_epa_rank"])
                a_ovr_off_rk, a_ovr_def_rk = int(a_eff["off_epa_rank"]), int(a_eff["def_epa_rank"])

                h_pass_rk, h_rush_rk = int(h_eff["off_pass_epa_rank"]), int(h_eff["off_rush_epa_rank"])
                h_pdef_rk, h_rdef_rk = int(h_eff["def_pass_epa_rank"]), int(h_eff["def_rush_epa_rank"])
                h_ovr_off_rk, h_ovr_def_rk = int(h_eff["off_epa_rank"]), int(h_eff["def_epa_rank"])

                mat_hdr_l, mat_hdr_r = st.columns([1.15, 1.05])
                with mat_hdr_l:
                    render_html(
                        f"<h4 style='margin:0 0 6px 0; color:#F1F5F9;'>Team Rankings "
                        f"<span style='font-size:0.78rem; color:#94A3B8; font-weight:600;'>("
                        f"<span style='color:{away_color};'>■ {away_tm}</span> vs "
                        f"<span style='color:{home_color};'>■ {home_tm}</span>)</span></h4>"
                    )
                with mat_hdr_r:
                    matrix_layout_mode = st.radio(
                        "View",
                        options=["Head-to-Head", "By Team"],
                        horizontal=True,
                        label_visibility="collapsed",
                        key="unit_matrix_layout_mode",
                    )

                if matrix_layout_mode == "Head-to-Head":
                    def _build_team_colored_cross_unit_row(
                        phase_title: str,
                        away_unit_lbl: str,
                        away_epa_val: float,
                        away_rk: int,
                        home_unit_lbl: str,
                        home_epa_val: float,
                        home_rk: int,
                        away_is_offense: bool,
                    ) -> str:
                        if away_is_offense:
                            away_net_edge = away_epa_val - (-home_epa_val)
                            away_rk_advantage = home_rk - away_rk
                        else:
                            away_net_edge = (-away_epa_val) - home_epa_val
                            away_rk_advantage = home_rk - away_rk

                        away_pct_bar = int(np.clip(50 + away_net_edge * 140, 15, 85))
                        home_pct_bar = 100 - away_pct_bar

                        if away_rk_advantage >= 6 or away_net_edge >= 0.08:
                            adv_tm = away_tm
                            adv_c = away_color
                            edge_pill = (
                                f'<span style="background:{hex_to_rgba(adv_c, 0.22)}; color:#F8FAFC; border:1px solid {adv_c}; padding:2px 8px; border-radius:4px; font-size:0.70rem; font-weight:700;">'
                                f'{adv_tm} Edge</span>'
                            )
                        elif away_rk_advantage <= -6 or away_net_edge <= -0.08:
                            adv_tm = home_tm
                            adv_c = home_color
                            edge_pill = (
                                f'<span style="background:{hex_to_rgba(adv_c, 0.22)}; color:#F8FAFC; border:1px solid {adv_c}; padding:2px 8px; border-radius:4px; font-size:0.70rem; font-weight:700;">'
                                f'{adv_tm} Edge</span>'
                            )
                        else:
                            edge_pill = '<span class="badge-mid">Even</span>'

                        return f"""
                        <div class="cross-unit-row" style="border-left: 3px solid {away_color}; border-right: 3px solid {home_color};">
                            <div class="cross-unit-header">
                                <span><b>{phase_title}</b></span>
                                {edge_pill}
                            </div>
                            <div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:6px;">
                                <span>
                                    {render_inline_logo(away_tm, 15)}<b style="color:#F8FAFC;">{away_tm} {away_unit_lbl}</b>
                                    <span class="unit-epa-mini">({away_epa_val:+.2f})</span>
                                    {render_rank_badge(away_rk, "")}
                                </span>
                                <span style="color:#64748B; font-size:0.72rem; font-weight:800;">VS</span>
                                <span>
                                    {render_rank_badge(home_rk, "")}
                                    <span class="unit-epa-mini">({home_epa_val:+.2f})</span>
                                    <b style="color:#F8FAFC;">{home_tm} {home_unit_lbl}</b> {render_inline_logo(home_tm, 15)}
                                </span>
                            </div>
                            <div class="tug-bar-track">
                                <div class="tug-bar-segment" style="width:{away_pct_bar}%; background:{away_color};"></div>
                                <div class="tug-bar-segment" style="width:{home_pct_bar}%; background:{home_color};"></div>
                            </div>
                        </div>
                        """

                    cross_html = (
                        f'<div class="unit-section-tag" style="margin-bottom:4px; color:#E2E8F0;">{away_tm} Offense (#{a_ovr_off_rk}) vs {home_tm} Defense (#{h_ovr_def_rk})</div>'
                        + _build_team_colored_cross_unit_row(
                            f"{away_tm} Pass vs {home_tm} Pass Def",
                            "Pass",
                            float(a_eff["off_pass_epa"]),
                            a_pass_rk,
                            "Pass Def",
                            float(h_eff["def_pass_epa"]),
                            h_pdef_rk,
                            away_is_offense=True,
                        )
                        + _build_team_colored_cross_unit_row(
                            f"{away_tm} Rush vs {home_tm} Rush Def",
                            "Rush",
                            float(a_eff["off_rush_epa"]),
                            a_rush_rk,
                            "Rush Def",
                            float(h_eff["def_rush_epa"]),
                            h_rdef_rk,
                            away_is_offense=True,
                        )
                        + f'<div class="unit-section-tag" style="margin:10px 0 4px 0; color:#E2E8F0;">{home_tm} Offense (#{h_ovr_off_rk}) vs {away_tm} Defense (#{a_ovr_def_rk})</div>'
                        + _build_team_colored_cross_unit_row(
                            f"{away_tm} Pass Def vs {home_tm} Pass",
                            "Pass Def",
                            float(a_eff["def_pass_epa"]),
                            a_pdef_rk,
                            "Pass",
                            float(h_eff["off_pass_epa"]),
                            h_pass_rk,
                            away_is_offense=False,
                        )
                        + _build_team_colored_cross_unit_row(
                            f"{away_tm} Rush Def vs {home_tm} Rush",
                            "Rush Def",
                            float(a_eff["def_rush_epa"]),
                            a_rdef_rk,
                            "Rush",
                            float(h_eff["off_rush_epa"]),
                            h_rush_rk,
                            away_is_offense=False,
                        )
                    )
                    render_html(cross_html)
                else:
                    render_html(
                        f"""
                        <div class="brief-grid" style="margin-top:6px;">
                            <div class="unit-pillar" style="border-top: 3px solid {away_color}; background: #141923;">
                                <div class="unit-pillar-header">
                                    <span>{render_inline_logo(away_tm, 18)}{away_tm} ({away_rec_str})</span>
                                    <span class="metric-subtext">Off #{a_ovr_off_rk} • Def #{a_ovr_def_rk}</span>
                                </div>
                                <div class="unit-section-tag" style="color:{away_color};">Offense</div>
                                <div class="unit-tier-row">
                                    <span class="unit-tier-label">Pass Offense</span>
                                    <span class="unit-tier-right">
                                        <span class="unit-epa-mini">{a_eff["off_pass_epa"]:+.2f}</span>
                                        {render_rank_badge(a_pass_rk, "")}
                                    </span>
                                </div>
                                <div class="unit-tier-row">
                                    <span class="unit-tier-label">Rush Offense</span>
                                    <span class="unit-tier-right">
                                        <span class="unit-epa-mini">{a_eff["off_rush_epa"]:+.2f}</span>
                                        {render_rank_badge(a_rush_rk, "")}
                                    </span>
                                </div>
                                <div class="unit-section-tag" style="margin-top:8px; color:{away_color};">Defense</div>
                                <div class="unit-tier-row">
                                    <span class="unit-tier-label">Pass Defense</span>
                                    <span class="unit-tier-right">
                                        <span class="unit-epa-mini">{a_eff["def_pass_epa"]:+.2f}</span>
                                        {render_rank_badge(a_pdef_rk, "")}
                                    </span>
                                </div>
                                <div class="unit-tier-row">
                                    <span class="unit-tier-label">Rush Defense</span>
                                    <span class="unit-tier-right">
                                        <span class="unit-epa-mini">{a_eff["def_rush_epa"]:+.2f}</span>
                                        {render_rank_badge(a_rdef_rk, "")}
                                    </span>
                                </div>
                            </div>
                            <div class="unit-pillar" style="border-top: 3px solid {home_color}; background: #141923;">
                                <div class="unit-pillar-header">
                                    <span>{render_inline_logo(home_tm, 18)}{home_tm} ({home_rec_str})</span>
                                    <span class="metric-subtext">Off #{h_ovr_off_rk} • Def #{h_ovr_def_rk}</span>
                                </div>
                                <div class="unit-section-tag" style="color:{home_color};">Offense</div>
                                <div class="unit-tier-row">
                                    <span class="unit-tier-label">Pass Offense</span>
                                    <span class="unit-tier-right">
                                        <span class="unit-epa-mini">{h_eff["off_pass_epa"]:+.2f}</span>
                                        {render_rank_badge(h_pass_rk, "")}
                                    </span>
                                </div>
                                <div class="unit-tier-row">
                                    <span class="unit-tier-label">Rush Offense</span>
                                    <span class="unit-tier-right">
                                        <span class="unit-epa-mini">{h_eff["off_rush_epa"]:+.2f}</span>
                                        {render_rank_badge(h_rush_rk, "")}
                                    </span>
                                </div>
                                <div class="unit-section-tag" style="margin-top:8px; color:{home_color};">Defense</div>
                                <div class="unit-tier-row">
                                    <span class="unit-tier-label">Pass Defense</span>
                                    <span class="unit-tier-right">
                                        <span class="unit-epa-mini">{h_eff["def_pass_epa"]:+.2f}</span>
                                        {render_rank_badge(h_pdef_rk, "")}
                                    </span>
                                </div>
                                <div class="unit-tier-row">
                                    <span class="unit-tier-label">Rush Defense</span>
                                    <span class="unit-tier-right">
                                        <span class="unit-epa-mini">{h_eff["def_rush_epa"]:+.2f}</span>
                                        {render_rank_badge(h_rdef_rk, "")}
                                    </span>
                                </div>
                            </div>
                        </div>
                        """
                    )

            # 4. TOP PLAYER PICKS (FULL-BLEED FLAT CARDS WITHOUT DOUBLE CONTAINER BORDERS)
            with col_brief_right:
                top_3_picks = build_top_player_picks(
                    usage_matchup,
                    prop_logs_matchup,
                    inj_matchup,
                    eff_df,
                    away_tm,
                    home_tm,
                    american_odds=default_odds,
                    kelly_fraction=kelly_mult,
                    top_n=3,
                )

                render_html(
                    """
                    <div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:6px; margin-bottom:6px;">
                        <h4 style="margin:0; color:#F1F5F9;">Top Player Picks</h4>
                        <span class="metric-subtext">Tap Player for Stats • Tap Line for Props</span>
                    </div>
                    """
                )
                if not top_3_picks:
                    st.info("Insufficient player usage data to rank top player picks.")
                else:
                    for p_idx, pick in enumerate(top_3_picks):
                        p_tm_c = resolve_team_display_color(pick["team"])
                        p_pic_html = render_mismatch_headshot_html(
                            pick["player_name"], pick["team"], headshot_lookup
                        )
                        spark_html = render_l5_sparkbars_html(pick["l5_values"], pick["line_val"])

                        with st.container(border=True):
                            pk_top_l, pk_top_r = st.columns([1.25, 1.15])
                            with pk_top_l:
                                render_inline_player_trigger(
                                    pick["player_name"],
                                    pick["team"],
                                    pick["position"],
                                    f"top3_pick_{p_idx}",
                                    f"{pick['team']} {pick['position']}",
                                )
                            with pk_top_r:
                                render_compact_bet_action_row(
                                    key_prefix=f"top3_{p_idx}_{active_game['game_id']}",
                                    season=selected_season,
                                    week=selected_week,
                                    matchup=f"{away_tm} @ {home_tm}",
                                    category=f"Player Prop ({pick['position']})",
                                    selection=f"{pick['player_name']} {pick['play_label']}",
                                    market_line=f"{pick['line_val']} {pick['mkt_label']}",
                                    model_proj=f"Proj {pick['model_proj']:.1f}",
                                    american_odds=default_odds,
                                    edge_score=pick["edge_score"],
                                    ev_pct=pick["ev_pct"],
                                    kelly_units=pick["kelly_units"],
                                    team_abbr=pick["team"],
                                    team_color_override=p_tm_c,
                                    open_matchup_modal_on_click=True,
                                    focus_player=pick["player_name"],
                                    button_text_override=pick["play_label"],
                                )

                            render_html(
                                f"""
                                <div style="display:flex; align-items:center; justify-content:space-between; flex-wrap:wrap; gap:10px; margin-top:4px; border-left:3px solid {p_tm_c}; padding-left:8px;">
                                    <div style="display:flex; align-items:center; gap:10px; flex:1; min-width:190px;">
                                        {p_pic_html}
                                        <div>
                                            <div style="display:flex; align-items:center; gap:5px; flex-wrap:wrap;">
                                                <span class="badge-elite">Proj {pick["model_proj"]:.1f}</span>
                                                <span class="badge-mid">Hit {pick["hit_record"]}</span>
                                                <span class="badge-sage">{pick["matchup_tag"]}</span>
                                            </div>
                                            <div class="metric-subtext" style="margin-top:3px;">
                                                {pick["usage_tag"]} • {pick["ev_pct"]:+.1f}% EV
                                            </div>
                                        </div>
                                    </div>
                                    <div style="display:flex; flex-direction:column; align-items:flex-end; gap:2px;">
                                        <span class="metric-subtext" style="font-size:0.62rem;">L5 ({pick['line_val']})</span>
                                        {spark_html}
                                    </div>
                                </div>
                                """
                            )

            # 5. IN-GAME WIN PROBABILITY SIMULATOR
            with st.expander("Live / In-Game Win Probability & Line Movement Tracker", expanded=False):
                wp_c1, wp_c2, wp_c3 = st.columns([1.1, 1.1, 1.2])
                with wp_c1:
                    sim_qtr = st.selectbox(
                        "Simulate Game State (Quarter)",
                        ["Pre-Game Kickoff", "End Q1 (45m rem)", "Halftime (30m rem)", "End Q3 (15m rem)", "Q4 5:00 Rem"],
                        index=0,
                        key="live_wp_qtr",
                    )
                with wp_c2:
                    sim_score_diff = st.slider(
                        f"Live Score Margin ({home_tm} minus {away_tm})",
                        min_value=-28,
                        max_value=28,
                        value=int(home_pts - away_pts) if active_game_is_completed else 0,
                        step=1,
                        key="live_wp_margin",
                    )
                with wp_c3:
                    qtr_time_map = {
                        "Pre-Game Kickoff": 60.0,
                        "End Q1 (45m rem)": 45.0,
                        "Halftime (30m rem)": 30.0,
                        "End Q3 (15m rem)": 15.0,
                        "Q4 5:00 Rem": 5.0,
                    }
                    rem_mins = qtr_time_map[sim_qtr]
                    time_frac = rem_mins / 60.0
                    rem_std = max(2.5, 13.45 * math.sqrt(time_frac))
                    rem_expected_home_edge = (-model_proj_dict["fair_home_spread"]) * time_frac
                    live_expected_final_margin = sim_score_diff + rem_expected_home_edge
                    live_home_wp = 0.5 * (1.0 + math.erf(live_expected_final_margin / (rem_std * math.sqrt(2.0))))
                    live_home_wp_pct = round(float(np.clip(live_home_wp * 100.0, 0.5, 99.5)), 1)
                    live_away_wp_pct = round(100.0 - live_home_wp_pct, 1)

                    st.metric(
                        f"Live Model Win Probability ({sim_qtr})",
                        f"{home_tm} {live_home_wp_pct:.1f}% / {away_tm} {live_away_wp_pct:.1f}%",
                        delta=f"Live Fair Spread: {home_tm} {-live_expected_final_margin:+.1f} | {line_move_dict['move_tag']}",
                        delta_color="off",
                    )

            # 6. CURRENT MATCHUP DIVISIONAL STANDINGS (PREDOMINANTLY TEAM-COLORED, SIDE-BY-SIDE IF OUT OF DIVISION)
            render_html(
                f"<h4 style='margin:14px 0 8px 0;'>"
                f"{render_inline_logo(away_tm, 20)}{away_tm} & {render_inline_logo(home_tm, 20)}{home_tm} — "
                f"Divisional Standings</h4>"
            )
            active_highlight_set = {away_norm, home_norm}
            if away_div_name == home_div_name:
                render_nfl_division_standings_card(
                    away_div_name,
                    division_standings_map[away_div_name],
                    active_highlight_set,
                    selected_season,
                    selected_week,
                    predominant_color=home_color,
                )
            else:
                div_col_away, div_col_home = st.columns(2)
                with div_col_away:
                    render_nfl_division_standings_card(
                        away_div_name,
                        division_standings_map[away_div_name],
                        active_highlight_set,
                        selected_season,
                        selected_week,
                        predominant_color=away_color,
                    )
                with div_col_home:
                    render_nfl_division_standings_card(
                        home_div_name,
                        division_standings_map[home_div_name],
                        active_highlight_set,
                        selected_season,
                        selected_week,
                        predominant_color=home_color,
                    )

            # 7. TEAM-COLORED 5-YEAR MATCHUP HISTORY
            render_five_year_h2h_visual(
                h2h_5yr,
                away_tm,
                home_tm,
                away_color,
                home_color,
                selected_season,
            )

    # -------------------------------------------------------------------------
    # CURRENT GAME TAB 2: 1-ON-1 MISMATCHES (CB vs WR BATTLES & SKILL VOLUME)
    # -------------------------------------------------------------------------
    with game_tab_mismatches:
        pm_subtab_cbwr, pm_subtab_volume = st.tabs(
            [
                "WR vs CB",
                "Touch Share",
            ]
        )

        with pm_subtab_cbwr:
            away_cb_wr_battles = build_cb_wr_matchup_battles(
                usage_matchup, player_df, snaps_df, inj_matchup, eff_df, away_tm, home_tm
            )
            home_cb_wr_battles = build_cb_wr_matchup_battles(
                usage_matchup, player_df, snaps_df, inj_matchup, eff_df, home_tm, away_tm
            )
            all_battles = away_cb_wr_battles + home_cb_wr_battles

            removed_cb_wr_list = []
            fp_retained_cb_wr_list = []
            if not inj_matchup.empty:
                cb_wr_inj = inj_matchup[
                    inj_matchup["position"].astype(str).str.upper().isin(["WR", "TE", "CB", "DB", "S", "FS", "SS"])
                ]
                for _, r_m in cb_wr_inj.iterrows():
                    st_m = str(r_m.get("report_status", "")).strip().upper()
                    prac_m = str(r_m.get("practice_status_clean", "")).strip().upper()
                    p_lbl = f"{r_m['player_display']} ({r_m['team']} {r_m.get('position', '')} • {st_m})"
                    if is_excluded_from_cb_wr_matchup(st_m, prac_m):
                        removed_cb_wr_list.append(p_lbl)
                    elif st_m == "UNSPECIFIED (FP)" or "FULL" in prac_m or prac_m == "FP":
                        fp_retained_cb_wr_list.append(f"{r_m['player_display']} ({r_m['team']} {r_m.get('position', '')} • FP)")

            if removed_cb_wr_list or fp_retained_cb_wr_list:
                removed_str = ", ".join(removed_cb_wr_list) if removed_cb_wr_list else "None"
                retained_str = ", ".join(fp_retained_cb_wr_list) if fp_retained_cb_wr_list else "None"
                render_html(
                    f"""
                    <div class="terminal-card" style="padding:9px 14px; margin-bottom:10px;">
                        <div class="metric-subtext">
                            <span class="badge-bad">Inactive / DNP</span>
                            <span style="color:#E2E8F0;">{removed_str}</span>
                            <span style="color:#475569; margin:0 6px;">|</span>
                            <span class="badge-elite">Full Practice</span>
                            <span style="color:#E2E8F0;">{retained_str}</span>
                        </div>
                    </div>
                    """
                )

            if not all_battles:
                st.info("Insufficient wide receiver or cornerback snap data to project 1-on-1 battles.")
            else:
                elite_battles = [b for b in all_battles if b["mismatch_score"] >= 75.0]
                backup_triggers = [b for b in all_battles if b.get("has_injury_trigger", False)]
                hot_wrs = [
                    b
                    for b in all_battles
                    if "WR HOT" in b["wr_streak_badge"] or "WR L4 UPTICK" in b["wr_streak_badge"]
                ]
                top_battle = sorted(all_battles, key=lambda x: x["mismatch_score"], reverse=True)[0]

                c_k1, c_k2, c_k3, c_k4 = st.columns(4)
                c_k1.metric(
                    "Top 1-on-1 Target Edge",
                    f"{top_battle['wr_name']} ({top_battle['off_tm']})",
                    delta=f"Index {top_battle['mismatch_score']:.1f}/100 vs {top_battle['cb_name']}",
                )
                c_k2.metric(
                    "Elite Mismatch Spots",
                    f"{len(elite_battles)} Battles",
                    delta="Score >= 75/100 + Catalyst",
                )
                c_k3.metric(
                    "Secondary Injury Triggers",
                    f"{len(backup_triggers)} Matchups",
                    delta="Out / Doubtful / Questionable / DNP-LP CBs",
                )
                c_k4.metric(
                    "Wideouts on L4 Uptick",
                    f"{len(hot_wrs)} Receivers",
                    delta="Positive L4 YPG vs Season",
                )

                cb_col1, cb_col2 = st.columns(2)

                for col_ui, (off_tm_i, def_tm_i, off_c_i, def_c_i, battle_list) in [
                    (cb_col1, (away_tm, home_tm, away_color, home_color, away_cb_wr_battles)),
                    (cb_col2, (home_tm, away_tm, home_color, away_color, home_cb_wr_battles)),
                ]:
                    with col_ui:
                        render_html(
                            f'<div style="margin-bottom:8px;">'
                            f'{render_team_pill(off_tm_i, color_override=off_c_i)} <b>Wideouts vs</b> '
                            f'{render_team_pill(def_tm_i, color_override=def_c_i)} <b>Cornerbacks</b></div>'
                        )
                        for b_idx, b in enumerate(battle_list):
                            wr_pic_html = render_mismatch_headshot_html(
                                b["wr_name"], b["off_tm"], headshot_lookup
                            )
                            cb_pic_html = render_mismatch_headshot_html(
                                b["cb_name"], b["def_tm"], headshot_lookup
                            )
                            with st.container(border=True):
                                render_html(
                                    f"""
                                    <div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:6px; margin-bottom:6px; border-bottom:1px solid #1E293B; padding-bottom:4px;">
                                        <span class="metric-subtext">{b['alignment']} • Mismatch Index: <b>{b['mismatch_score']:.0f}/100</b></span>
                                        {b['tier_badge']}
                                    </div>
                                    """
                                )
                                vs_c1, vs_mid, vs_c2 = st.columns([1.45, 0.25, 1.45])
                                with vs_c1:
                                    render_inline_player_trigger(
                                        b["wr_name"],
                                        b["off_tm"],
                                        "WR",
                                        f"cbwr_w_{off_tm_i}_{b_idx}",
                                        f"{b['off_tm']} WR",
                                    )
                                    render_html(
                                        f"""
                                        <div style="display:flex; align-items:center; gap:10px; margin-top:4px; border-left:3px solid {off_c_i}; padding-left:6px;">
                                            {wr_pic_html}
                                            <div class="metric-subtext" style="line-height:1.4;">
                                                Tgt: <b>{b["wr_tgt_sh"]:.1f}%</b> | Air: <b>{b["wr_air_sh"]:.1f}%</b><br>
                                                Season: <b>{b["wr_ypg"]:.1f} YPG</b>
                                            </div>
                                        </div>
                                        """
                                    )
                                with vs_mid:
                                    render_html('<div class="cb-wr-vs-divider">VS</div>')
                                with vs_c2:
                                    render_inline_player_trigger(
                                        b["cb_name"],
                                        b["def_tm"],
                                        b["cb_pos"],
                                        f"cbwr_c_{def_tm_i}_{b_idx}",
                                        f"{b['def_tm']} {b['cb_pos']}",
                                    )
                                    render_html(
                                        f"""
                                        <div style="display:flex; align-items:center; gap:10px; margin-top:4px; border-left:3px solid {def_c_i}; padding-left:6px;">
                                            {cb_pic_html}
                                            <div class="metric-subtext" style="line-height:1.4;">
                                                Def Snaps: <b>{b["cb_snap_pct"]:.0f}%</b><br>
                                                Pass Def: <b>#{b["def_pass_rk"]} NFL</b>
                                            </div>
                                        </div>
                                        """
                                    )
                                render_html(
                                    f"""
                                    <div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:4px; margin:6px 0 4px 0;">
                                        {b['wr_streak_badge']}
                                        {b['cb_status_badge']}
                                    </div>
                                    <div class="metric-subtext" style="color:#CBD5E1;">
                                        <b>Rationale:</b> {b['trigger_note']}
                                    </div>
                                    """
                                )

                sorted_battles = sorted(all_battles, key=lambda x: x["mismatch_score"], reverse=True)
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
                        for b in sorted_battles
                    ]
                )
                st.markdown("##### CB vs. WR Summary Matrix (Select Row to Inspect Player)")
                cbwr_event = st.dataframe(
                    battle_table_df,
                    width="stretch",
                    hide_index=True,
                    on_select="rerun",
                    selection_mode="single-row",
                    key="cbwr_matrix_table",
                    column_config={
                        "Target %": st.column_config.NumberColumn("Target %", format="%.1f%%"),
                        "Season YPG": st.column_config.NumberColumn("Season YPG", format="%.1f"),
                        "L4 YPG": st.column_config.NumberColumn("L4 YPG", format="%.1f"),
                        "CB Snap %": st.column_config.NumberColumn("CB Def Snaps", format="%.0f%%"),
                        "Mismatch Index": st.column_config.ProgressColumn(
                            "Mismatch Score", format="%.1f / 100", min_value=0, max_value=100
                        ),
                    },
                )
                if cbwr_event and cbwr_event.selection and cbwr_event.selection.rows:
                    sel_b_idx = cbwr_event.selection.rows[0]
                    if 0 <= sel_b_idx < len(sorted_battles):
                        chosen_b = sorted_battles[sel_b_idx]
                        if st.button(
                            f"Open Player Dossier: {chosen_b['wr_name']} ({chosen_b['off_tm']})",
                            key=f"open_cbwr_dossier_{sel_b_idx}",
                            type="primary",
                        ):
                            trigger_player_popup(chosen_b["wr_name"], chosen_b["off_tm"], "WR")
                            st.rerun()

        with pm_subtab_volume:
            if usage_matchup.empty or a_eff is None or h_eff is None:
                st.info("Player usage or team efficiency splits unavailable for this matchup.")
            else:
                p_col1, p_col2 = st.columns(2)

                for col_ui, (off_tm_i, def_tm_i, off_c_i, def_c_i) in [
                    (p_col1, (away_tm, home_tm, away_color, home_color)),
                    (p_col2, (home_tm, away_tm, home_color, away_color)),
                ]:
                    with col_ui:
                        render_html(
                            f'<div style="margin-bottom:8px;">'
                            f'{render_team_pill(off_tm_i, color_override=off_c_i)} <b>Skill Weapons vs</b> '
                            f'{render_team_pill(def_tm_i, color_override=def_c_i)} <b>Defense</b></div>'
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

                        for w_idx, (_, w_row) in enumerate(featured.iterrows()):
                            is_rec = w_row["calc_target_share"] >= w_row["calc_rush_share"]
                            opp_rk = def_pass_rk if is_rec else def_rush_rk
                            phase_str = f"{def_tm_i} Pass Def" if is_rec else f"{def_tm_i} Rush Def"
                            share_lbl = (
                                f"Tgt Share: <b>{w_row['calc_target_share']*100:.1f}%</b> ({int(w_row['targets'])} tgts, {int(w_row['air_yards'])} air yds)"
                                if is_rec
                                else f"Rush Share: <b>{w_row['calc_rush_share']*100:.1f}%</b> ({int(w_row['carries'])} att, {int(w_row['touches'])} touches)"
                            )

                            opp_unit_badge = render_rank_badge(opp_rk, f"vs {phase_str}")
                            pos_badge = str(w_row.get("position", "POS"))
                            scrim_yds = int(w_row["scrimmage_yards"])
                            w_pic_html = render_mismatch_headshot_html(
                                w_row["player_name"], off_tm_i, headshot_lookup
                            )

                            with st.container(border=True):
                                top_c1, top_c2 = st.columns([1.4, 1])
                                with top_c1:
                                    render_inline_player_trigger(
                                        w_row["player_name"],
                                        off_tm_i,
                                        pos_badge,
                                        f"vol_{off_tm_i}_{w_idx}",
                                        f"{off_tm_i} {pos_badge}",
                                    )
                                with top_c2:
                                    render_html(f'<div style="text-align:right;">{opp_unit_badge}</div>')
                                render_html(
                                    f"""
                                    <div style="display:flex; align-items:center; gap:10px; margin-top:4px; border-left:3px solid {off_c_i}; padding-left:8px;">
                                        {w_pic_html}
                                        <div class="metric-subtext">
                                            {share_lbl} | EPA: <b>{w_row['total_epa']:+.1f}</b> |
                                            Scrimmage: <b>{scrim_yds} yds ({int(w_row['total_tds'])} TD)</b>
                                        </div>
                                    </div>
                                    """
                                )

    # -------------------------------------------------------------------------
    # CURRENT GAME TAB 3: DEDICATED TOP-LEVEL INJURY REPORT TAB
    # -------------------------------------------------------------------------
    with game_tab_injuries:
        inj_view_mode = st.radio(
            "Filter",
            options=[
                "All Entries",
                "Flagged (Out / Q / DNP / LP)",
                "Full Practice (FP / Cleared)",
            ],
            horizontal=True,
            key="inj_report_view_filter",
        )

        col_away_inj, col_home_inj = st.columns(2)

        for col_obj, tm, tm_c in [(col_away_inj, away_tm, away_color), (col_home_inj, home_tm, home_color)]:
            with col_obj:
                tm_inj_all = inj_matchup[inj_matchup["team"] == tm].copy() if not inj_matchup.empty else pd.DataFrame()
                total_off_drop = (
                    tm_inj_all[(tm_inj_all["unit_side"] == "Offense") & (~tm_inj_all["is_cleared"])]["est_epa_penalty"].sum()
                    if not tm_inj_all.empty
                    else 0.0
                )
                total_def_drop = (
                    tm_inj_all[(tm_inj_all["unit_side"] == "Defense") & (~tm_inj_all["is_cleared"])]["est_epa_penalty"].sum()
                    if not tm_inj_all.empty
                    else 0.0
                )
                flagged_tm_count = int((~tm_inj_all["is_cleared"]).sum()) if not tm_inj_all.empty else 0
                cleared_tm_count = int(tm_inj_all["is_cleared"].sum()) if not tm_inj_all.empty else 0

                if tm_inj_all.empty:
                    tm_inj = pd.DataFrame()
                elif inj_view_mode == "Flagged (Out / Q / DNP / LP)":
                    tm_inj = tm_inj_all[~tm_inj_all["is_cleared"]].copy()
                elif inj_view_mode == "Full Practice (FP / Cleared)":
                    tm_inj = tm_inj_all[tm_inj_all["is_cleared"]].copy()
                else:
                    tm_inj = tm_inj_all.copy()

                badge_cls = "badge-bad" if flagged_tm_count > 0 else "badge-elite"
                depth_url = get_team_depth_chart_url(tm)
                render_html(
                    f"""
                    <div class="terminal-card" style="border-left: 4px solid {tm_c}; background: linear-gradient(90deg, {hex_to_rgba(tm_c, 0.14)} 0%, #121722 65%);">
                        <div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:6px;">
                            <div style="display:flex; align-items:center; gap:8px; flex-wrap:wrap;">
                                <h4 style="margin:0;">{render_inline_logo(tm, 20)}{tm} Injury Report</h4>
                                <a class="depth-chart-link-btn" href="{depth_url}" target="_blank" rel="noopener noreferrer"
                                   style="border-color:{hex_to_rgba(tm_c, 0.78)}; background:{hex_to_rgba(tm_c, 0.22)};">
                                   {tm} DEPTH CHART &#8599;
                                </a>
                            </div>
                            <div>
                                <span class="{badge_cls}">{flagged_tm_count} Flagged</span>
                                <span class="badge-elite">{cleared_tm_count} Cleared</span>
                            </div>
                        </div>
                        <p style="margin:6px 0 0 0;" class="metric-subtext">
                            Off EPA Drag: <b>{-total_off_drop:+.3f}/play</b> |
                            Def EPA Drag: <b>+{total_def_drop:.3f}/play</b>
                        </p>
                    </div>
                    """
                )

                if tm_inj.empty:
                    st.caption(f"No {tm} players match the current filter.")
                else:
                    for i_idx, (_, r_inj) in enumerate(tm_inj.head(14).iterrows()):
                        badge_html = render_injury_badge(r_inj["report_status"])
                        prac_html = render_practice_badge(r_inj.get("practice_status_clean", ""))
                        snap_pct = r_inj["snap_share"] * 100
                        pos_str = normalize_guard_position(r_inj.get("position", "POS"), "", r_inj["player_display"], tm, i_idx)
                        is_clr = bool(r_inj.get("is_cleared", False))
                        epa_color = "#34D399" if is_clr else "#F87171"
                        epa_str = "0.000 (Full Practice / Expected to Play)" if is_clr else f"-{r_inj['est_epa_penalty']:.3f}/play"
                        inj_pic_html = render_mismatch_headshot_html(
                            r_inj["player_display"], tm, headshot_lookup
                        )

                        with st.container(border=True):
                            ic1, ic2 = st.columns([1.4, 1.2])
                            with ic1:
                                render_inline_player_trigger(
                                    r_inj["player_display"],
                                    tm,
                                    pos_str,
                                    f"inj_{tm}_{i_idx}",
                                    f"{tm} {pos_str}",
                                )
                            with ic2:
                                render_html(f'<div style="text-align:right;">{badge_html} {prac_html}</div>')
                            render_html(
                                f"""
                                <div style="display:flex; align-items:center; gap:10px; margin-top:4px; border-left:3px solid {tm_c}; padding-left:8px;">
                                    {inj_pic_html}
                                    <div class="metric-subtext">
                                        {r_inj['role_tier']} • <b>{r_inj['primary_injury']}</b><br>
                                        Snaps: <b>{snap_pct:.0f}%</b> |
                                        EPA: <span style="color:{epa_color}; font-weight:700;">{epa_str}</span>
                                    </div>
                                </div>
                                """
                            )

    # -------------------------------------------------------------------------
    # CURRENT GAME TAB 4: UNIT EPA & TRENCHES
    # -------------------------------------------------------------------------
    with game_tab_epa:
        if a_eff is None or h_eff is None:
            st.warning("Efficiency metrics unavailable for one or both teams.")
        else:
            def render_possession_block(
                off_tm: str,
                def_tm: str,
                off_c: str,
                def_c: str,
                o_row: pd.Series,
                d_row: pd.Series,
                off_pen: float,
                def_pen: float,
            ) -> None:
                render_html(
                    f"<h4 style='margin:10px 0 6px 0;'>"
                    f"{render_team_pill(off_tm, color_override=off_c)} Offense vs {render_team_pill(def_tm, color_override=def_c)} Defense</h4>"
                )
                c1, c2, c3 = st.columns(3)

                with c1:
                    with st.container(border=True):
                        o_p_rk = int(o_row["off_pass_epa_rank"])
                        d_p_rk = int(d_row["def_pass_epa_rank"])
                        render_html(
                            f"""
                            <div>
                                <b>{render_inline_logo(off_tm, 16)}Pass Offense vs Pass Defense</b>
                                <div class="epa-stat-grid">
                                    <div class="epa-stat-box" style="border-top:3px solid {off_c};">
                                        <div class="epa-stat-label">{off_tm} Pass EPA</div>
                                        <div class="epa-stat-num">{o_row['off_pass_epa']:+.3f}</div>
                                        {render_rank_badge(o_p_rk, f"{off_tm} Off")}
                                    </div>
                                    <div class="epa-stat-box" style="border-top:3px solid {def_c};">
                                        <div class="epa-stat-label">{def_tm} Pass Def EPA</div>
                                        <div class="epa-stat-num">{d_row['def_pass_epa']:+.3f}</div>
                                        {render_rank_badge(d_p_rk, f"{def_tm} Def")}
                                    </div>
                                </div>
                                <div class="metric-subtext">
                                    Success Rate: <b>{off_tm}</b> {o_row['off_pass_sr']*100:.1f}% | <b>{def_tm} Allowed</b> {d_row['def_pass_sr']*100:.1f}%
                                </div>
                            </div>
                            """
                        )

                with c2:
                    with st.container(border=True):
                        o_r_rk = int(o_row["off_rush_epa_rank"])
                        d_r_rk = int(d_row["def_rush_epa_rank"])
                        render_html(
                            f"""
                            <div>
                                <b>{render_inline_logo(off_tm, 16)}Rush Offense vs Rush Defense</b>
                                <div class="epa-stat-grid">
                                    <div class="epa-stat-box" style="border-top:3px solid {off_c};">
                                        <div class="epa-stat-label">{off_tm} Rush EPA</div>
                                        <div class="epa-stat-num">{o_row['off_rush_epa']:+.3f}</div>
                                        {render_rank_badge(o_r_rk, f"{off_tm} Off")}
                                    </div>
                                    <div class="epa-stat-box" style="border-top:3px solid {def_c};">
                                        <div class="epa-stat-label">{def_tm} Rush Def EPA</div>
                                        <div class="epa-stat-num">{d_row['def_rush_epa']:+.3f}</div>
                                        {render_rank_badge(d_r_rk, f"{def_tm} Def")}
                                    </div>
                                </div>
                                <div class="metric-subtext">
                                    Success Rate: <b>{off_tm}</b> {o_row['off_rush_sr']*100:.1f}% | <b>{def_tm} Allowed</b> {d_row['def_rush_sr']*100:.1f}%
                                </div>
                            </div>
                            """
                        )

                with c3:
                    with st.container(border=True):
                        adj_off_epa = o_row["off_epa"] - off_pen
                        adj_def_epa = d_row["def_epa"] + def_pen
                        o_ovr_rk = int(o_row["off_epa_rank"])
                        d_ovr_rk = int(d_row["def_epa_rank"])
                        off_drag_badge = (
                            f'<span class="badge-bad">-{off_pen:.2f} Inj</span>'
                            if off_pen > 0
                            else '<span class="badge-elite">Full Strength</span>'
                        )
                        def_drag_badge = (
                            f'<span class="badge-bad">+{def_pen:.2f} Inj</span>'
                            if def_pen > 0
                            else '<span class="badge-elite">Full Strength</span>'
                        )
                        render_html(
                            f"""
                            <div>
                                <b>{render_inline_logo(off_tm, 16)}Overall & Injury-Adjusted EPA</b>
                                <div style="margin-top:4px;">
                                    {render_rank_badge(o_ovr_rk, f"{off_tm} Ovr")} {render_rank_badge(d_ovr_rk, f"{def_tm} Ovr")}
                                </div>
                                <div class="epa-stat-grid">
                                    <div class="epa-stat-box" style="border-top:3px solid {off_c};">
                                        <div class="epa-stat-label">{off_tm} Adj Off EPA</div>
                                        <div class="epa-stat-num">{adj_off_epa:+.3f}</div>
                                        {off_drag_badge}
                                    </div>
                                    <div class="epa-stat-box" style="border-top:3px solid {def_c};">
                                        <div class="epa-stat-label">{def_tm} Adj Def EPA</div>
                                        <div class="epa-stat-num">{adj_def_epa:+.3f}</div>
                                        {def_drag_badge}
                                    </div>
                                </div>
                                <div class="metric-subtext">
                                    Total SR: <b>{off_tm}</b> {o_row['off_sr']*100:.1f}% (#{int(o_row['off_sr_rank'])}) | <b>{def_tm}</b> {d_row['def_sr']*100:.1f}% (#{int(d_row['def_sr_rank'])})
                                </div>
                            </div>
                            """
                        )

            render_possession_block(away_tm, home_tm, away_color, home_color, a_eff, h_eff, away_off_pen, home_def_pen)
            render_possession_block(home_tm, away_tm, home_color, away_color, h_eff, a_eff, home_off_pen, away_def_pen)

            cov_map_matchup = load_team_coverage_and_shell_splits(selected_season, eff_df)
            if cov_map_matchup:
                render_html("<h4 style='margin:14px 0 8px 0;'>Defensive Coverage Shells (1-High / 2-High & Man / Zone)</h4>")
                cov_c1, cov_c2 = st.columns(2)
                for c_ui, tm_k, tm_col in [(cov_c1, away_tm, away_color), (cov_c2, home_tm, home_color)]:
                    with c_ui:
                        cd = cov_map_matchup.get(tm_k, cov_map_matchup.get(normalize_team_code(tm_k), {}))
                        if cd:
                            render_html(
                                f"""
                                <div class="terminal-card" style="border-top: 3px solid {tm_col}; border-left: none; background:#141923;">
                                    <div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:6px; margin-bottom:8px;">
                                        <span style="font-weight:800; font-size:0.92rem; color:#F8FAFC;">{render_inline_logo(tm_k, 18)}{tm_k} Defense Coverage Profile</span>
                                        <div>
                                            <span class="badge-sage">{cd['primary_shell']}</span>
                                            <span class="badge-mid">{cd['primary_coverage']}</span>
                                        </div>
                                    </div>
                                    <div class="unit-tier-row">
                                        <span class="unit-tier-label">1-High Safety (Cover 1 / Cover 3)</span>
                                        <span class="unit-tier-right">
                                            <b>{cd['one_high_pct']:.1f}%</b>
                                            <span class="unit-epa-mini">({cd['one_high_epa']:+.2f} EPA)</span>
                                            {render_rank_badge(int(cd['one_high_rank']), "")}
                                        </span>
                                    </div>
                                    <div class="unit-tier-row">
                                        <span class="unit-tier-label">2-High Safety (Cover 2 / 4 / 6)</span>
                                        <span class="unit-tier-right">
                                            <b>{cd['two_high_pct']:.1f}%</b>
                                            <span class="unit-epa-mini">({cd['two_high_epa']:+.2f} EPA)</span>
                                            {render_rank_badge(int(cd['two_high_rank']), "")}
                                        </span>
                                    </div>
                                    <div class="unit-tier-row">
                                        <span class="unit-tier-label">Man Coverage</span>
                                        <span class="unit-tier-right">
                                            <b>{cd['man_pct']:.1f}%</b>
                                            <span class="unit-epa-mini">({cd['man_epa']:+.2f} EPA)</span>
                                            {render_rank_badge(int(cd['man_rank']), "")}
                                        </span>
                                    </div>
                                    <div class="unit-tier-row">
                                        <span class="unit-tier-label">Zone Coverage</span>
                                        <span class="unit-tier-right">
                                            <b>{cd['zone_pct']:.1f}%</b>
                                            <span class="unit-epa-mini">({cd['zone_epa']:+.2f} EPA)</span>
                                            {render_rank_badge(int(cd['zone_rank']), "")}
                                        </span>
                                    </div>
                                    <div class="unit-tier-row" style="border-bottom:none;">
                                        <span class="unit-tier-label">Box Alignment (Light <=6 / Stacked 7+)</span>
                                        <span class="unit-tier-right">
                                            <b>{cd['light_box_pct']:.0f}% Light / {cd['stacked_box_pct']:.0f}% Stacked</b>
                                            {render_rank_badge(int(cd['stacked_box_rank']), "")}
                                        </span>
                                    </div>
                                </div>
                                """
                            )

    # -------------------------------------------------------------------------
    # CURRENT GAME TAB 5: MATCHUP PROPS & ROSTERS
    # -------------------------------------------------------------------------
    with game_tab_props_rosters:
        sub_m_props, sub_m_rosters = st.tabs(
            [
                "Player Props",
                "Rosters",
            ]
        )

        with sub_m_props:
            if prop_logs_matchup.empty:
                st.info(f"No weekly player game logs found for {away_tm} or {home_tm}.")
            else:
                ctrl_col1, ctrl_col2, ctrl_col3, ctrl_col4 = st.columns([0.9, 1.3, 1.2, 0.9])

                with ctrl_col1:
                    allowed_positions = [
                        p for p in ["WR", "RB", "TE", "QB"] if p in prop_logs_matchup["pos_clean"].unique()
                    ]
                    if not allowed_positions:
                        allowed_positions = sorted(prop_logs_matchup["pos_clean"].unique().tolist())

                    selected_pos = st.selectbox(
                        "Position",
                        options=["All Skill Positions"] + allowed_positions,
                        index=0,
                        key="matchup_prop_pos_sel",
                    )

                pos_filtered_logs = (
                    prop_logs_matchup
                    if selected_pos == "All Skill Positions"
                    else prop_logs_matchup[prop_logs_matchup["pos_clean"] == selected_pos]
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
                        "Player",
                        options=roster_summary["display_option"].tolist(),
                        index=0,
                        key="matchup_prop_plr_sel",
                    )

                selected_player_row = roster_summary[
                    roster_summary["display_option"] == selected_player_disp
                ].iloc[0]
                sel_player_name = selected_player_row["player_label"]
                sel_player_team = selected_player_row["team"]
                sel_player_pos = selected_player_row["pos_clean"]
                sel_plr_color = resolve_team_display_color(sel_player_team)

                default_market_idx = 0
                if sel_player_pos == "QB":
                    default_market_idx = list(PROP_MARKETS.keys()).index("Passing Yards")
                elif sel_player_pos == "RB":
                    default_market_idx = list(PROP_MARKETS.keys()).index("Rushing Yards")

                with ctrl_col3:
                    selected_market_label = st.selectbox(
                        "Market",
                        options=list(PROP_MARKETS.keys()),
                        index=default_market_idx,
                        key="matchup_prop_mkt_sel",
                    )

                with ctrl_col4:
                    prop_odds_input = st.selectbox(
                        "Sportsbook Odds",
                        options=[-130, -125, -120, -115, -110, -105, +100, +105, +110, +120],
                        index=4,
                        format_func=lambda x: f"{x:+d}",
                        key="prop_tab_odds_sel",
                    )

                stat_col_name, default_line, max_line_cap, step_val = PROP_MARKETS[selected_market_label]

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
                        f"Prop Line ({selected_market_label})",
                        min_value=0.5,
                        max_value=float(round(dynamic_max, 0) + 0.5),
                        value=float(min(max(0.5, smart_default_threshold), dynamic_max)),
                        step=float(step_val),
                        key="matchup_prop_line_slider",
                    )
                with slider_col2:
                    if total_avail_games > 1:
                        lookback_n = st.slider(
                            "Last N Games",
                            min_value=1,
                            max_value=total_avail_games,
                            value=min(10, total_avail_games),
                            step=1,
                            key="matchup_prop_lookback_slider",
                        )
                    else:
                        lookback_n = 1

                season_baseline_avg = float(p_log[stat_col_name].mean()) if total_avail_games > 0 else 0.0
                l3_avg = float(p_log.tail(3)[stat_col_name].mean()) if total_avail_games > 0 else 0.0
                stat_std = float(p_log[stat_col_name].std()) if total_avail_games > 1 else max(1.0, season_baseline_avg * 0.32)
                stat_std = max(stat_std, 1.0 if not is_td_or_int else 0.45)

                streak_badge_html, streak_delta_str = evaluate_player_streak_badge(
                    season_baseline_avg, l3_avg, is_negative_stat=(stat_col_name == "interceptions")
                )

                window_log = p_log.tail(lookback_n).copy()
                window_log["hit"] = window_log[stat_col_name] >= prop_threshold
                window_log["bar_color"] = np.where(window_log["hit"], "#34D399", "#F87171")
                window_log["rolling_avg"] = window_log[stat_col_name].expanding().mean()

                hits_count = int(window_log["hit"].sum())
                sample_n = len(window_log)
                hit_rate_pct = (hits_count / sample_n * 100.0) if sample_n > 0 else 0.0

                opp_def_tm = home_tm if sel_player_team == away_tm else away_tm
                is_rush_prop = stat_col_name in ["rushing_yards", "carries"]
                opp_def_rk = (
                    int(eff_df.loc[opp_def_tm, "def_rush_epa_rank"])
                    if is_rush_prop
                    else int(eff_df.loc[opp_def_tm, "def_pass_epa_rank"])
                )
                def_type_str = "Rush Def" if is_rush_prop else "Pass Def"

                def_adj_mult = 1.0 + ((opp_def_rk - 16.5) / 16.5) * 0.12
                model_prop_proj = round((0.55 * season_baseline_avg + 0.45 * l3_avg) * def_adj_mult, 2 if is_td_or_int else 1)
                over_prob_cdf = 0.5 * (1.0 + math.erf((model_prop_proj - prop_threshold) / (stat_std * math.sqrt(2.0))))
                blended_over_prob = float(np.clip(0.60 * over_prob_cdf + 0.40 * (hit_rate_pct / 100.0), 0.12, 0.88))
                recommended_dir = "OVER" if blended_over_prob >= 0.50 else "UNDER"
                rec_win_prob = blended_over_prob if recommended_dir == "OVER" else (1.0 - blended_over_prob)
                prop_ev_pct, prop_kelly_u = compute_ev_and_kelly(
                    rec_win_prob, int(prop_odds_input), float(st.session_state["kelly_fraction_mult"])
                )
                prop_conf_score = float(np.clip(50.0 + (rec_win_prob - 0.50) * 140.0, 25.0, 96.0))

                pk1, pk2, pk3, pk4 = st.columns(4)
                pk1.metric(
                    f"Hit Rate (Last {sample_n})",
                    f"{hit_rate_pct:.1f}% ({hits_count}/{sample_n})",
                    delta="Over Trend" if hit_rate_pct >= 55 else "Under Trend",
                    delta_color="normal" if hit_rate_pct >= 55 else "inverse",
                )
                pk2.metric(
                    "Model Projection vs Line",
                    f"{model_prop_proj:.2f}" if is_td_or_int else f"{model_prop_proj:.1f}",
                    delta=f"{model_prop_proj - prop_threshold:+.1f} vs {prop_threshold} Line",
                    delta_color="normal" if model_prop_proj >= prop_threshold else "inverse",
                )
                pk3.metric(
                    f"Recommended Play ({int(prop_odds_input):+d})",
                    f"{recommended_dir} {prop_threshold}",
                    delta=f"Conf {prop_conf_score:.0f}/100 • {prop_ev_pct:+.1f}% EV • {prop_kelly_u:.2f}u Kelly",
                    delta_color="normal" if prop_ev_pct > 0 else "off",
                )
                pk4.metric(
                    f"vs {opp_def_tm} {def_type_str}",
                    f"Rank #{opp_def_rk}",
                    delta="Favorable" if opp_def_rk >= 23 else ("Tough" if opp_def_rk <= 5 else "Neutral"),
                    delta_color="normal" if opp_def_rk >= 23 else ("inverse" if opp_def_rk <= 5 else "off"),
                )

                opp_badge_html = render_rank_badge(opp_def_rk, f"{opp_def_tm} {def_type_str}")
                hit_badge_html = (
                    f'<span class="badge-elite">{hits_count}/{sample_n} Over ({hit_rate_pct:.0f}%)</span>'
                    if hit_rate_pct >= 55
                    else f'<span class="badge-mid">{hits_count}/{sample_n} Over ({hit_rate_pct:.0f}%)</span>'
                )

                with st.container(border=True):
                    pc1, pc2, pc3 = st.columns([1.0, 1.25, 1.25])
                    with pc1:
                        render_inline_player_trigger(
                            sel_player_name,
                            sel_player_team,
                            sel_player_pos,
                            "prop_hdr",
                            f"[{sel_player_team} {sel_player_pos}]",
                        )
                    with pc2:
                        render_html(f'<div style="padding-top:4px;">{streak_badge_html} {hit_badge_html} {opp_badge_html}</div>')
                    with pc3:
                        render_compact_bet_action_row(
                            key_prefix=f"m_prop_{sel_player_name}_{stat_col_name}",
                            season=selected_season,
                            week=selected_week,
                            matchup=f"{away_tm} @ {home_tm}",
                            category=f"Prop ({selected_market_label})",
                            selection=f"{sel_player_name} {recommended_dir} {prop_threshold} {selected_market_label}",
                            market_line=f"{prop_threshold}",
                            model_proj=f"Proj {model_prop_proj}",
                            american_odds=int(prop_odds_input),
                            edge_score=prop_conf_score,
                            ev_pct=prop_ev_pct,
                            kelly_units=prop_kelly_u,
                            team_abbr=sel_player_team,
                            team_color_override=sel_plr_color,
                            button_text_override=f"{recommended_dir} {prop_threshold} {selected_market_label}",
                        )

                chart_col_left, chart_col_right = st.columns([1.35, 1.0])
                with chart_col_left:
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
                            name=selected_market_label,
                        )
                    )
                    fig_prop.add_trace(
                        go.Scatter(
                            x=window_log["game_tag"],
                            y=window_log["rolling_avg"],
                            mode="lines+markers",
                            line=dict(color=sel_plr_color, width=2, dash="dot"),
                            marker=dict(size=6, color=sel_plr_color),
                            name="Cumulative Avg",
                        )
                    )
                    fig_prop.add_hline(
                        y=prop_threshold,
                        line_width=2,
                        line_dash="dash",
                        line_color="#FBBF24",
                        annotation_text=f"Book Line: {prop_threshold}",
                        annotation_position="top left",
                        annotation_font=dict(color="#FBBF24", size=11),
                    )
                    fig_prop.add_hline(
                        y=model_prop_proj,
                        line_width=2,
                        line_dash="dot",
                        line_color="#34D399",
                        annotation_text=f"Model Proj: {model_prop_proj}",
                        annotation_position="bottom right",
                        annotation_font=dict(color="#34D399", size=11),
                    )

                    y_upper = max(float(window_log[stat_col_name].max()), prop_threshold, model_prop_proj) * 1.25 + 1.0
                    fig_prop.update_layout(
                        dragmode=False,
                        title=dict(text="Weekly Game Log vs. Book Line & Model Projection", font=dict(size=13)),
                        paper_bgcolor="#141923",
                        plot_bgcolor="#141923",
                        font=dict(color="#E2E8F0"),
                        xaxis=dict(title="Game Week & Opponent", gridcolor="#222B3A", fixedrange=True),
                        yaxis=dict(title=selected_market_label, range=[0, y_upper], gridcolor="#222B3A", fixedrange=True),
                        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                        height=360,
                        margin=dict(l=20, r=20, t=48, b=30),
                    )
                    st.plotly_chart(fig_prop, width="stretch", config={"displayModeBar": False, "scrollZoom": False})

                with chart_col_right:
                    x_min = max(0.0, model_prop_proj - 3.2 * stat_std)
                    x_max = max(prop_threshold + 2.5 * stat_std, model_prop_proj + 3.2 * stat_std)
                    x_grid = np.linspace(x_min, x_max, 160)
                    pdf_vals = (1.0 / (stat_std * np.sqrt(2.0 * np.pi))) * np.exp(-0.5 * ((x_grid - model_prop_proj) / stat_std) ** 2)

                    fig_dist = go.Figure()
                    under_mask = x_grid <= prop_threshold
                    over_mask = x_grid >= prop_threshold
                    fig_dist.add_trace(
                        go.Scatter(
                            x=x_grid[under_mask],
                            y=pdf_vals[under_mask],
                            fill="tozeroy",
                            mode="lines",
                            line=dict(color="#F87171", width=2),
                            fillcolor="rgba(248, 113, 113, 0.22)",
                            name=f"Under ({100.0 - blended_over_prob*100.0:.1f}%)",
                        )
                    )
                    fig_dist.add_trace(
                        go.Scatter(
                            x=x_grid[over_mask],
                            y=pdf_vals[over_mask],
                            fill="tozeroy",
                            mode="lines",
                            line=dict(color="#34D399", width=2),
                            fillcolor="rgba(52, 211, 153, 0.25)",
                            name=f"Over ({blended_over_prob*100.0:.1f}%)",
                        )
                    )
                    fig_dist.add_vline(
                        x=prop_threshold,
                        line_width=2,
                        line_dash="dash",
                        line_color="#FBBF24",
                        annotation_text=f"Line {prop_threshold}",
                        annotation_position="top left",
                    )
                    fig_dist.add_vline(
                        x=model_prop_proj,
                        line_width=2,
                        line_dash="dot",
                        line_color=sel_plr_color,
                        annotation_text=f"Mean {model_prop_proj}",
                        annotation_position="top right",
                    )
                    fig_dist.update_layout(
                        dragmode=False,
                        title=dict(text=f"Projected Outcome Distribution (±{stat_std:.1f} SD)", font=dict(size=13)),
                        paper_bgcolor="#141923",
                        plot_bgcolor="#141923",
                        font=dict(color="#E2E8F0"),
                        xaxis=dict(title=selected_market_label, gridcolor="#222B3A", fixedrange=True),
                        yaxis=dict(title="Density", showticklabels=False, gridcolor="#222B3A", fixedrange=True),
                        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                        height=360,
                        margin=dict(l=20, r=20, t=48, b=30),
                    )
                    st.plotly_chart(fig_dist, width="stretch", config={"displayModeBar": False, "scrollZoom": False})

        with sub_m_rosters:
            if roster_matchup_table.empty:
                st.info("Active roster and snap usage data unavailable for the selected teams.")
            else:
                r_col1, r_col2, r_col3, r_col4 = st.columns([1.1, 1.3, 1.2, 1.1])
                with r_col1:
                    roster_team_filter = st.radio(
                        "Team",
                        options=[f"Both ({away_tm} & {home_tm})", away_tm, home_tm],
                        horizontal=True,
                    )
                with r_col2:
                    unit_group_filter = st.radio(
                        "Unit",
                        options=["All", "Offense", "Defense", "Special Teams"],
                        horizontal=True,
                    )

                filtered_roster = roster_matchup_table.copy()
                if roster_team_filter in [away_tm, home_tm]:
                    filtered_roster = filtered_roster[filtered_roster["team"] == roster_team_filter]

                if unit_group_filter in ["Offense", "Defense", "Special Teams"]:
                    filtered_roster = filtered_roster[filtered_roster["unit_group"] == unit_group_filter]

                with r_col3:
                    avail_roster_pos = sorted(filtered_roster["position"].dropna().astype(str).unique().tolist())
                    roster_pos_filter = st.multiselect(
                        "Positions",
                        options=avail_roster_pos,
                        default=[],
                        placeholder="All Positions",
                    )
                with r_col4:
                    min_snap_slider = st.slider(
                        "Min Snap %",
                        min_value=0,
                        max_value=90,
                        value=10,
                        step=5,
                    )

                if roster_pos_filter:
                    filtered_roster = filtered_roster[filtered_roster["position"].isin(roster_pos_filter)]
                filtered_roster = filtered_roster[filtered_roster["primary_snap_pct"] >= min_snap_slider].reset_index(drop=True)

                roster_disp_cols = [
                    "team_logo",
                    "team",
                    "unit_group",
                    "player_name",
                    "position",
                    "health_status",
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

                roster_event = st.dataframe(
                    filtered_roster[avail_r_cols],
                    width="stretch",
                    hide_index=True,
                    on_select="rerun",
                    selection_mode="single-row",
                    key="roster_explorer_table",
                    column_config={
                        "team_logo": st.column_config.ImageColumn("", width="small"),
                        "team": "Team",
                        "unit_group": "Unit",
                        "player_name": "Player (Select Row for Dossier)",
                        "position": "Pos",
                        "health_status": "Status",
                        "games_played": st.column_config.NumberColumn("GP", format="%d"),
                        "primary_snap_pct": st.column_config.ProgressColumn(
                            "Snap %", format="%.1f%%", min_value=0, max_value=100
                        ),
                        "total_snaps": st.column_config.NumberColumn("Snaps", format="%d"),
                        "targets": st.column_config.NumberColumn("Tgts", format="%d"),
                        "receptions": st.column_config.NumberColumn("Rec", format="%d"),
                        "target_share_pct": st.column_config.ProgressColumn(
                            "Tgt %", format="%.1f%%", min_value=0, max_value=50
                        ),
                        "air_yards": st.column_config.NumberColumn("Air Yds", format="%d"),
                        "carries": st.column_config.NumberColumn("Carries", format="%d"),
                        "touches": st.column_config.NumberColumn("Touches", format="%d"),
                        "scrimmage_yards": st.column_config.NumberColumn("Scrim Yds", format="%d"),
                        "total_tds": st.column_config.NumberColumn("TDs", format="%d"),
                        "total_epa": st.column_config.NumberColumn("EPA", format="%+.2f"),
                    },
                )
                if roster_event and roster_event.selection and roster_event.selection.rows:
                    sel_r_idx = roster_event.selection.rows[0]
                    if 0 <= sel_r_idx < len(filtered_roster):
                        chosen_p = filtered_roster.iloc[sel_r_idx]
                        if st.button(
                            f"Open Player Dossier: {chosen_p['player_name']} ({chosen_p['team']} {chosen_p['position']})",
                            key=f"open_roster_dossier_{sel_r_idx}",
                            type="primary",
                        ):
                            trigger_player_popup(
                                chosen_p["player_name"],
                                chosen_p["team"],
                                chosen_p["position"],
                            )
                            st.rerun()

# =============================================================================
# WORKSPACE 2: NFL LEAGUE HUB (COMPLETELY SEPARATED FROM CURRENT SELECTED GAME)
# =============================================================================
else:
    (
        league_tab_best_bets,
        league_tab_props,
        league_tab_backtest,
        league_tab_divisions,
    ) = st.tabs(
        [
            "Best Picks",
            "Prop Finder",
            "Model Record",
            "Standings",
        ]
    )

    # -------------------------------------------------------------------------
    # LEAGUE HUB TAB 1: WEEK BEST LEAGUE PICKS (SPREADS, TOTALS & PROPS)
    # -------------------------------------------------------------------------
    with league_tab_best_bets:
        with st.spinner(f"Scanning all {len(week_games)} Week {selected_week} games for top league edges..."):
            slate_games_df, slate_props_df = build_slate_best_bets_leaderboard(
                week_games,
                eff_df,
                player_df,
                snaps_df,
                injuries_df,
                selected_season,
                selected_week,
                american_odds=default_odds,
                kelly_fraction=kelly_mult,
            )

        render_html(
            f"""
            <div class="terminal-card-elite">
                <div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:8px;">
                    <div>
                        <h4 style="margin:0; color:#F8FAFC;">Week {selected_week} Best League Picks — Spreads, Totals & Player Props</h4>
                        <span class="metric-subtext">Scans all {len(week_games)} NFL matchups on the Week {selected_week} slate. Click any hyperlinked pick box to toggle in your Bet Slip.</span>
                    </div>
                    <div>
                        <span class="badge-elite">Odds {default_odds:+d}</span>
                        <span class="badge-sage">Kelly {kelly_mult:.2f}x</span>
                    </div>
                </div>
            </div>
            """
        )

        if not slate_games_df.empty and not slate_props_df.empty:
            top_sp_row = slate_games_df[slate_games_df["Market Type"] == "Spread"].iloc[0]
            top_tot_sub = slate_games_df[slate_games_df["Market Type"] == "Total (O/U)"]
            top_tot_row = top_tot_sub.iloc[0] if not top_tot_sub.empty else top_sp_row
            top_pr_row = slate_props_df.iloc[0]

            sb1, sb2, sb3, sb4 = st.columns(4)
            sb1.metric(
                "Top Spread Pick",
                f"{top_sp_row['Best Bet']} ({top_sp_row['Matchup']})",
                delta=f"Proj {top_sp_row['Implied Score']} (+{top_sp_row['Value Edge (Pts)']:.1f} pt edge)",
            )
            sb2.metric(
                "Top Total Pick",
                f"{top_tot_row['Best Bet']} ({top_tot_row['Matchup']})",
                delta=f"{top_tot_row['Model Fair Line']} (+{top_tot_row['Value Edge (Pts)']:.1f} pt edge)",
            )
            sb3.metric(
                "Top Player Prop",
                f"{top_pr_row['Player']} ({top_pr_row['Team']})",
                delta=f"{top_pr_row['Prop Play']} • Proj {top_pr_row['Model Projection']}",
            )
            sb4.metric(
                "+EV Slate Plays",
                f"{int((slate_games_df['EV %'] > 0).sum() + (slate_props_df['EV %'] > 0).sum())} Plays",
                delta=f"At {default_odds:+d} Odds",
            )

        sl_col1, sl_col2 = st.columns([1.05, 1.15])
        with sl_col1:
            st.markdown(f"##### Top League Game Picks (Spreads & Totals • Week {selected_week})")
            if slate_games_df.empty:
                st.info("No spread or total projections available for this slate.")
            else:
                for g_idx, g_r in slate_games_df.head(6).iterrows():
                    bk_tm = str(g_r.get("Backed Team", "")).strip().upper()
                    bk_c = get_team_primary_color(bk_tm)
                    render_compact_bet_action_row(
                        key_prefix=f"lg_g_card_{g_idx}",
                        season=selected_season,
                        week=selected_week,
                        matchup=str(g_r["Matchup"]),
                        category=str(g_r["Market Type"]),
                        selection=f"{g_r['Best Bet']} [{g_r['Matchup']}]",
                        market_line=str(g_r["Market Line"]),
                        model_proj=str(g_r["Model Fair Line"]),
                        american_odds=default_odds,
                        edge_score=float(g_r["Edge Score"]),
                        ev_pct=float(g_r["EV %"]),
                        kelly_units=float(g_r["Kelly Units"]),
                        team_abbr=bk_tm,
                        team_color_override=bk_c,
                        button_text_override=f"{g_r['Best Bet']} ({g_r['Matchup']})",
                    )

                with st.expander("View Full Week Spread & Total Leaderboard Table", expanded=False):
                    disp_g_cols = [
                        "Matchup",
                        "Market Type",
                        "Best Bet",
                        "Market Line",
                        "Model Fair Line",
                        "Implied Score",
                        "Value Edge (Pts)",
                        "Edge Score",
                        "EV %",
                        "Kelly Units",
                    ]
                    st.dataframe(
                        slate_games_df[disp_g_cols],
                        width="stretch",
                        hide_index=True,
                        column_config={
                            "Value Edge (Pts)": st.column_config.NumberColumn("Edge (Pts)", format="+%.1f"),
                            "Edge Score": st.column_config.ProgressColumn("Conf (0-100)", format="%.0f", min_value=0, max_value=100),
                            "EV %": st.column_config.NumberColumn("EV %", format="%+.1f%%"),
                            "Kelly Units": st.column_config.NumberColumn("Kelly (u)", format="%.2f u"),
                        },
                    )

        with sl_col2:
            st.markdown(f"##### Top League Player Prop Picks (Week {selected_week})")
            if slate_props_df.empty:
                st.info("No player prop projections available for this slate.")
            else:
                for p_idx, p_r in slate_props_df.head(6).iterrows():
                    p_tm = str(p_r["Team"]).strip().upper()
                    p_c = get_team_primary_color(p_tm)
                    render_compact_bet_action_row(
                        key_prefix=f"lg_p_card_{p_idx}",
                        season=selected_season,
                        week=selected_week,
                        matchup=str(p_r["Matchup"]),
                        category=f"Player Prop ({p_r['Pos']})",
                        selection=f"{p_r['Player']} ({p_tm}) {p_r['Prop Play']}",
                        market_line=f"{p_r['Book Line']}",
                        model_proj=f"Proj {p_r['Model Proj']:.1f}",
                        american_odds=default_odds,
                        edge_score=float(p_r["Edge Score"]),
                        ev_pct=float(p_r["EV %"]),
                        kelly_units=float(p_r["Kelly Units"]),
                        team_abbr=p_tm,
                        team_color_override=p_c,
                        button_text_override=f"{p_r['Player']} — {p_r['Prop Play']}",
                    )

                with st.expander("View Full Week Player Props Leaderboard Table", expanded=False):
                    disp_p_cols = [
                        "Matchup",
                        "Player",
                        "Team",
                        "Pos",
                        "Prop Play",
                        "Model Proj",
                        "Proj Delta",
                        "Season Hit Rate",
                        "Edge Score",
                        "EV %",
                        "Kelly Units",
                    ]
                    st.dataframe(
                        slate_props_df[disp_p_cols],
                        width="stretch",
                        hide_index=True,
                        column_config={
                            "Model Proj": st.column_config.NumberColumn("Proj", format="%.1f"),
                            "Proj Delta": st.column_config.NumberColumn("vs Line", format="%+.1f"),
                            "Edge Score": st.column_config.ProgressColumn("Conf (0-100)", format="%.0f", min_value=0, max_value=100),
                            "EV %": st.column_config.NumberColumn("EV %", format="%+.1f%%"),
                            "Kelly Units": st.column_config.NumberColumn("Kelly (u)", format="%.2f u"),
                        },
                    )

    # -------------------------------------------------------------------------
    # LEAGUE HUB TAB 2: LEAGUE-WIDE PROPS EXPLORER
    # -------------------------------------------------------------------------
    with league_tab_props:
        all_slate_teams = sorted(
            pd.concat([week_games["away_team"], week_games["home_team"]]).dropna().unique().tolist()
        )
        league_prop_logs = prepare_matchup_player_prop_logs(player_df, all_slate_teams)

        if league_prop_logs.empty:
            st.info("No weekly player game logs available for the current season.")
        else:
            l_c1, l_c2, l_c3, l_c4, l_c5 = st.columns([0.9, 0.9, 1.35, 1.15, 0.8])
            with l_c1:
                lg_tm_filter = st.selectbox(
                    "Team Filter",
                    options=["All Slate Teams"] + all_slate_teams,
                    index=0,
                    key="lg_prop_tm_sel",
                )
            with l_c2:
                lg_pos_filter = st.selectbox(
                    "Position",
                    options=["All Skill Positions", "WR", "RB", "TE", "QB"],
                    index=0,
                    key="lg_prop_pos_sel",
                )

            sub_lg_logs = league_prop_logs.copy()
            if lg_tm_filter != "All Slate Teams":
                sub_lg_logs = sub_lg_logs[sub_lg_logs["team"] == lg_tm_filter]
            if lg_pos_filter != "All Skill Positions":
                sub_lg_logs = sub_lg_logs[sub_lg_logs["pos_clean"] == lg_pos_filter]

            lg_summary = (
                sub_lg_logs.groupby(["player_label", "team", "pos_clean"], as_index=False)
                .agg(
                    games=("week", "nunique"),
                    scrim_yds=("scrimmage_yards", "sum"),
                    pass_yds=("passing_yards", "sum"),
                )
            )
            lg_summary["sort_score"] = lg_summary["scrim_yds"] + (lg_summary["pass_yds"] * 0.4)
            lg_summary = lg_summary.sort_values(by="sort_score", ascending=False)
            lg_summary["display_option"] = (
                lg_summary["player_label"]
                + " ("
                + lg_summary["team"]
                + " - "
                + lg_summary["pos_clean"]
                + ")"
            )

            with l_c3:
                lg_sel_plr_disp = st.selectbox(
                    "NFL Player",
                    options=lg_summary["display_option"].tolist(),
                    index=0,
                    key="lg_prop_plr_sel",
                )

            lg_plr_row = lg_summary[lg_summary["display_option"] == lg_sel_plr_disp].iloc[0]
            lg_p_name = lg_plr_row["player_label"]
            lg_p_team = lg_plr_row["team"]
            lg_p_pos = lg_plr_row["pos_clean"]
            lg_p_color = get_team_primary_color(lg_p_team)

            lg_def_mkt_idx = 0
            if lg_p_pos == "QB":
                lg_def_mkt_idx = list(PROP_MARKETS.keys()).index("Passing Yards")
            elif lg_p_pos == "RB":
                lg_def_mkt_idx = list(PROP_MARKETS.keys()).index("Rushing Yards")

            with l_c4:
                lg_mkt_lbl = st.selectbox(
                    "Prop Market",
                    options=list(PROP_MARKETS.keys()),
                    index=lg_def_mkt_idx,
                    key="lg_prop_mkt_sel",
                )
            with l_c5:
                lg_prop_odds = st.selectbox(
                    "Odds",
                    options=[-130, -120, -115, -110, -105, +100, +105, +110],
                    index=3,
                    format_func=lambda x: f"{x:+d}",
                    key="lg_prop_odds_sel",
                )

            lg_stat_col, lg_def_l, lg_max_c, lg_step = PROP_MARKETS[lg_mkt_lbl]
            lg_p_log = sub_lg_logs[
                (sub_lg_logs["player_label"] == lg_p_name) & (sub_lg_logs["team"] == lg_p_team)
            ].sort_values(by="week").copy()

            lg_tot_g = len(lg_p_log)
            lg_is_td = lg_stat_col in ["anytime_td", "receiving_tds", "interceptions"]
            lg_med = float(lg_p_log[lg_stat_col].median()) if lg_tot_g > 0 else lg_def_l
            lg_smart_line = 0.5 if lg_is_td else (round(lg_med * 2) / 2 if lg_med > 0 else lg_def_l)
            lg_dyn_max = float(max(lg_max_c, lg_p_log[lg_stat_col].max() * 1.25, 3.5))

            lg_line_val = st.slider(
                f"Prop Line ({lg_mkt_lbl})",
                min_value=0.5,
                max_value=float(round(lg_dyn_max, 0) + 0.5),
                value=float(min(max(0.5, lg_smart_line), lg_dyn_max)),
                step=float(lg_step),
                key="lg_prop_line_slider",
            )

            lg_s_avg = float(lg_p_log[lg_stat_col].mean()) if lg_tot_g > 0 else 0.0
            lg_l3_avg = float(lg_p_log.tail(3)[lg_stat_col].mean()) if lg_tot_g > 0 else 0.0
            lg_std = float(lg_p_log[lg_stat_col].std()) if lg_tot_g > 1 else max(1.0, lg_s_avg * 0.32)
            lg_std = max(lg_std, 1.0 if not lg_is_td else 0.45)

            lg_p_log["hit"] = lg_p_log[lg_stat_col] >= lg_line_val
            lg_p_log["bar_color"] = np.where(lg_p_log["hit"], "#34D399", "#F87171")
            lg_p_log["rolling_avg"] = lg_p_log[lg_stat_col].expanding().mean()

            lg_hits = int(lg_p_log["hit"].sum())
            lg_hit_pct = (lg_hits / lg_tot_g * 100.0) if lg_tot_g > 0 else 0.0
            lg_proj = round(0.55 * lg_s_avg + 0.45 * lg_l3_avg, 2 if lg_is_td else 1)
            lg_over_prob = 0.5 * (1.0 + math.erf((lg_proj - lg_line_val) / (lg_std * math.sqrt(2.0))))
            lg_blend_prob = float(np.clip(0.60 * lg_over_prob + 0.40 * (lg_hit_pct / 100.0), 0.12, 0.88))
            lg_dir = "OVER" if lg_blend_prob >= 0.50 else "UNDER"
            lg_win_p = lg_blend_prob if lg_dir == "OVER" else (1.0 - lg_blend_prob)
            lg_ev, lg_kelly = compute_ev_and_kelly(lg_win_p, int(lg_prop_odds), kelly_mult)
            lg_conf = float(np.clip(50.0 + (lg_win_p - 0.50) * 140.0, 25.0, 96.0))

            render_compact_bet_action_row(
                key_prefix=f"lg_exp_{lg_p_name}_{lg_stat_col}",
                season=selected_season,
                week=selected_week,
                matchup=f"{lg_p_team} Wk {selected_week}",
                category=f"Prop ({lg_mkt_lbl})",
                selection=f"{lg_p_name} {lg_dir} {lg_line_val} {lg_mkt_lbl}",
                market_line=f"{lg_line_val}",
                model_proj=f"Proj {lg_proj}",
                american_odds=int(lg_prop_odds),
                edge_score=lg_conf,
                ev_pct=lg_ev,
                kelly_units=lg_kelly,
                team_abbr=lg_p_team,
                team_color_override=lg_p_color,
                button_text_override=f"{lg_dir} {lg_line_val} {lg_mkt_lbl}",
            )

            fig_lg = go.Figure()
            fig_lg.add_trace(
                go.Bar(
                    x=lg_p_log["game_tag"],
                    y=lg_p_log[lg_stat_col],
                    marker_color=lg_p_log["bar_color"],
                    text=[f"{v:.0f}" if (lg_step >= 1 or lg_is_td) else f"{v:.1f}" for v in lg_p_log[lg_stat_col]],
                    textposition="outside",
                    name=lg_mkt_lbl,
                )
            )
            fig_lg.add_trace(
                go.Scatter(
                    x=lg_p_log["game_tag"],
                    y=lg_p_log["rolling_avg"],
                    mode="lines+markers",
                    line=dict(color=lg_p_color, width=2, dash="dot"),
                    name="Cumulative Avg",
                )
            )
            fig_lg.add_hline(y=lg_line_val, line_width=2, line_dash="dash", line_color="#FBBF24", annotation_text=f"Line: {lg_line_val} ({lg_hit_pct:.0f}% Hit)")
            fig_lg.update_layout(
                dragmode=False,
                paper_bgcolor="#141923",
                plot_bgcolor="#141923",
                font=dict(color="#E2E8F0"),
                xaxis=dict(fixedrange=True, gridcolor="#222B3A"),
                yaxis=dict(fixedrange=True, gridcolor="#222B3A"),
                height=340,
                margin=dict(l=20, r=20, t=36, b=24),
            )
            st.plotly_chart(fig_lg, width="stretch", config={"displayModeBar": False, "scrollZoom": False})

    # -------------------------------------------------------------------------
    # LEAGUE HUB TAB 3: HISTORICAL BACKTEST
    # -------------------------------------------------------------------------
    with league_tab_backtest:
        bt_summary, bt_log = run_season_backtest(schedule_df, eff_df)

        bt_season_shown = selected_season
        if bt_summary.empty and selected_season == 2026:
            st.info("No completed games yet for 2026. Showing 2025 Full-Season Backtest Benchmark.")
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
            b1.metric(f"{bt_season_shown} Graded Spots", f"{total_graded} Games")
            b2.metric(
                "ATS Cover Rate",
                f"{overall_ats_pct:.1f}%",
                delta=f"{overall_ats_pct - 52.38:+.1f}% vs 52.4%",
                delta_color="normal" if overall_ats_pct >= 52.4 else "inverse",
            )
            b3.metric("SU Win Rate", f"{overall_su_pct:.1f}%")
            b4.metric(
                "Top Signal",
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
                    marker_color="#34D399",
                    text=[f"{v:.1f}%" for v in bt_summary["ATS Cover %"]],
                    textposition="auto",
                )
            )
            fig.add_trace(
                go.Bar(
                    y=bt_summary["Edge Category"],
                    x=bt_summary["SU Win %"],
                    name="SU Win %",
                    orientation="h",
                    marker_color="#38BDF8",
                    text=[f"{v:.1f}%" for v in bt_summary["SU Win %"]],
                    textposition="auto",
                )
            )
            fig.add_vline(
                x=52.38,
                line_width=2,
                line_dash="dash",
                line_color="#F87171",
                annotation_text="52.4% Breakeven",
                annotation_position="top right",
            )
            fig.update_layout(
                dragmode=False,
                barmode="group",
                paper_bgcolor="#141923",
                plot_bgcolor="#141923",
                font=dict(color="#E2E8F0"),
                xaxis=dict(title="Win / Cover %", range=[0, 100], gridcolor="#222B3A", fixedrange=True),
                yaxis=dict(autorange="reversed", fixedrange=True),
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                height=340,
                margin=dict(l=20, r=20, t=36, b=24),
            )
            st.plotly_chart(fig, width="stretch", config={"displayModeBar": False, "scrollZoom": False})

            st.dataframe(
                bt_summary,
                width="stretch",
                hide_index=True,
                column_config={
                    "Edge Category": "Signal",
                    "Sample Size": st.column_config.NumberColumn("Games", format="%d"),
                    "ATS Record": "ATS (W-L-P)",
                    "ATS Cover %": st.column_config.ProgressColumn(
                        "ATS Cover %", format="%.1f%%", min_value=0, max_value=100
                    ),
                    "SU Win %": st.column_config.ProgressColumn(
                        "SU Win %", format="%.1f%%", min_value=0, max_value=100
                    ),
                    "Est. Units (-110)": st.column_config.NumberColumn("Units (-110)", format="%+.2f u"),
                },
            )

    # -------------------------------------------------------------------------
    # LEAGUE HUB TAB 4: NFL DIVISIONAL STANDINGS (ALL 8 DIVISIONS)
    # -------------------------------------------------------------------------
    with league_tab_divisions:
        active_highlight_set = {away_norm, home_norm}
        afc_col, nfc_col = st.columns(2)
        with afc_col:
            render_html("<h4 style='margin:4px 0 8px 0; color:#F87171;'>AFC Divisions</h4>")
            for d_nm in ["AFC East", "AFC North", "AFC South", "AFC West"]:
                render_nfl_division_standings_card(
                    d_nm,
                    division_standings_map[d_nm],
                    active_highlight_set,
                    selected_season,
                    selected_week,
                )
        with nfc_col:
            render_html("<h4 style='margin:4px 0 8px 0; color:#38BDF8;'>NFC Divisions</h4>")
            for d_nm in ["NFC East", "NFC North", "NFC South", "NFC West"]:
                render_nfl_division_standings_card(
                    d_nm,
                    division_standings_map[d_nm],
                    active_highlight_set,
                    selected_season,
                    selected_week,
                )

# -----------------------------------------------------------------------------
# 7. FLOATING BOTTOM-RIGHT CIRCULAR '+' BUTTON (LAUNCHES DEDICATED PROP & BET SLIP MODAL)
# -----------------------------------------------------------------------------
slip_items_fab = st.session_state.get("bet_slip", [])
slip_count_fab = len(slip_items_fab)
total_kelly_fab = sum(float(item.get("Kelly Stake (u)", 0.0)) for item in slip_items_fab)

fab_badge_css = (
    f"""
    <style>
    div[data-testid="stElementContainer"]:has(.floating-plus-fab-marker) + div[data-testid="stElementContainer"] div[data-testid="stButton"] button::after,
    div.element-container:has(.floating-plus-fab-marker) + div.element-container div[data-testid="stButton"] button::after {{
        content: "{slip_count_fab}";
        position: absolute;
        top: -4px;
        right: -4px;
        background: #34D399;
        color: #0B0F17;
        font-family: Inter, -apple-system, BlinkMacSystemFont, sans-serif; font-variant-numeric: tabular-nums;
        font-size: 0.72rem;
        font-weight: 900;
        width: 22px;
        height: 22px;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        border: 2px solid #0F172A;
        box-shadow: 0 2px 6px rgba(0, 0, 0, 0.5);
    }}
    </style>
    """
    if slip_count_fab > 0
    else ""
)

render_html(f'{fab_badge_css}<span class="floating-plus-fab-marker" style="display:none;"></span>')
if st.button(
    "+",
    key="floating_circular_plus_fab_btn",
    help=f"Open Matchup Picks, Prop Explorer & Bet Slip ({slip_count_fab} Picks • {total_kelly_fab:.2f}u)",
):
    trigger_props_slip_popup()
    st.rerun()

# -----------------------------------------------------------------------------
# 8. LAUNCH POP-OUT MODALS (PLAYER DOSSIER OR UNDERDOG-STYLE PROPS & BET SLIP)
# -----------------------------------------------------------------------------
if st.session_state.get("open_player_modal") and st.session_state.get("active_player"):
    st.session_state["open_player_modal"] = False
    active_p = st.session_state["active_player"]

    if hasattr(st, "dialog"):

        @st.dialog("Player Dossier — Props, Season Stats & Injuries", width="large")
        def _show_player_modal() -> None:
            render_player_popup_contents(
                active_p,
                roster_matchup_table,
                prop_logs_matchup,
                snaps_df,
                inj_matchup,
                injuries_df,
                eff_df,
                headshot_lookup,
                away_tm,
                home_tm,
                player_season,
                inj_season,
                selected_week,
            )

        _show_player_modal()
    else:
        with st.container(border=True):
            st.subheader("Player Dossier — Props, Season Stats & Injuries")
            render_player_popup_contents(
                active_p,
                roster_matchup_table,
                prop_logs_matchup,
                snaps_df,
                inj_matchup,
                injuries_df,
                eff_df,
                headshot_lookup,
                away_tm,
                home_tm,
                player_season,
                inj_season,
                selected_week,
            )

elif st.session_state.get("open_props_slip_modal"):
    st.session_state["open_props_slip_modal"] = False

    if hasattr(st, "dialog"):

        @st.dialog(f"Matchup Picks, Prop Explorer & Bet Slip ({away_tm} @ {home_tm})", width="large")
        def _show_props_slip_modal() -> None:
            render_underdog_props_and_betslip_modal(
                selected_season=selected_season,
                selected_week=selected_week,
                away_tm=away_tm,
                home_tm=home_tm,
                away_color=away_color,
                home_color=home_color,
                spread_v=spread_v,
                total_v=total_v,
                model_proj_dict=model_proj_dict,
                line_move_dict=line_move_dict,
                usage_matchup=usage_matchup,
                prop_logs_matchup=prop_logs_matchup,
                inj_matchup=inj_matchup,
                eff_df=eff_df,
                headshot_lookup=headshot_lookup,
                default_odds=default_odds,
                kelly_mult=kelly_mult,
            )

        _show_props_slip_modal()
    else:
        with st.container(border=True):
            st.subheader(f"Matchup Picks, Prop Explorer & Bet Slip ({away_tm} @ {home_tm})")
            render_underdog_props_and_betslip_modal(
                selected_season=selected_season,
                selected_week=selected_week,
                away_tm=away_tm,
                home_tm=home_tm,
                away_color=away_color,
                home_color=home_color,
                spread_v=spread_v,
                total_v=total_v,
                model_proj_dict=model_proj_dict,
                line_move_dict=line_move_dict,
                usage_matchup=usage_matchup,
                prop_logs_matchup=prop_logs_matchup,
                inj_matchup=inj_matchup,
                eff_df=eff_df,
                headshot_lookup=headshot_lookup,
                default_odds=default_odds,
                kelly_mult=kelly_mult,
            )