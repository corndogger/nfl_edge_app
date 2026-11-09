from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import quote
import math
import time
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
import streamlit.components.v1 as components

# -----------------------------------------------------------------------------
# 1. PAGE CONFIGURATION & NFL.COM FLAT & SHARP BROADCAST CSS THEME
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="Football Edger",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Official 32-Team NFL Primary & Secondary/Away Color Palette
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
/* Global Overflow & Box-Sizing Guardrails — NFL.com Flat & Sharp Broadcast Theme */
*, *::before, *::after {
    box-sizing: border-box;
}
.stApp, .main {
    background-color: #0B0B0E !important;
    color: #FFFFFF !important;
    font-family: Inter, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif !important;
}
section[data-testid="stSidebar"] {
    background-color: #111116 !important;
    border-right: 1px solid #262630 !important;
}
div[data-testid="stMetric"] {
    background-color: #15151B !important;
    border: 1px solid #282832 !important;
    border-top: 3px solid #013369 !important;
    border-radius: 2px !important;
    padding: 12px 14px !important;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.50), 0 1px 2px rgba(0, 0, 0, 0.35) !important;
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
    background-color: #15151B;
    border: 1px solid #282832;
    border-top: 4px solid #013369;
    border-radius: 2px;
    padding: 13px 15px;
    min-width: 0;
    display: flex;
    flex-direction: column;
    justify-content: space-between;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.50), 0 1px 2px rgba(0, 0, 0, 0.35);
}
.custom-kpi-card-edge {
    border-top: 4px solid #16A34A;
}
.custom-kpi-card-warn {
    border-top: 4px solid #DC2626;
}
.custom-kpi-top {
    display: flex;
    justify-content: space-between;
    align-items: center;
    gap: 6px;
    margin-bottom: 4px;
}
.custom-kpi-label {
    font-size: 0.75rem;
    font-family: Inter, -apple-system, BlinkMacSystemFont, sans-serif; font-variant-numeric: tabular-nums;
    color: #A1A1AA;
    font-weight: 800;
    text-transform: uppercase;
    letter-spacing: 0.04em;
}
.custom-kpi-val {
    font-size: 1.38rem;
    font-weight: 900;
    font-family: Inter, -apple-system, BlinkMacSystemFont, sans-serif; font-variant-numeric: tabular-nums;
    color: #FFFFFF;
    line-height: 1.22;
    margin-bottom: 6px;
    overflow-wrap: break-word;
}
.custom-kpi-pill-pos {
    background-color: #15803D;
    color: #FFFFFF;
    border: 1px solid #16A34A;
    padding: 2px 8px;
    border-radius: 2px;
    font-size: 0.72rem;
    font-family: Inter, -apple-system, BlinkMacSystemFont, sans-serif; font-variant-numeric: tabular-nums;
    font-weight: 700;
    display: inline-block;
    width: fit-content;
}
.custom-kpi-pill-neg {
    background-color: #B91C1C;
    color: #FFFFFF;
    border: 1px solid #DC2626;
    padding: 2px 8px;
    border-radius: 2px;
    font-size: 0.72rem;
    font-family: Inter, -apple-system, BlinkMacSystemFont, sans-serif; font-variant-numeric: tabular-nums;
    font-weight: 700;
    display: inline-block;
    width: fit-content;
}
.custom-kpi-pill-neutral {
    background-color: #23232C;
    color: #FFFFFF;
    border: 1px solid #343442;
    padding: 2px 8px;
    border-radius: 2px;
    font-size: 0.72rem;
    font-family: Inter, -apple-system, BlinkMacSystemFont, sans-serif; font-variant-numeric: tabular-nums;
    font-weight: 700;
    display: inline-block;
    width: fit-content;
}

/* NFL.com Flat & Sharp Content Cards with Clean Drop Shadows */
.terminal-card {
    background-color: #15151B;
    border: 1px solid #282832;
    border-left: 4px solid #013369;
    border-radius: 2px;
    padding: 14px 16px;
    margin-bottom: 10px;
    color: #FFFFFF;
    max-width: 100%;
    overflow-wrap: break-word;
    word-wrap: break-word;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.50), 0 1px 2px rgba(0, 0, 0, 0.35);
}
.terminal-card-elite {
    background-color: #15151B;
    border: 1px solid #282832;
    border-left: 4px solid #16A34A;
    border-radius: 2px;
    padding: 14px 16px;
    margin-bottom: 10px;
    color: #FFFFFF;
    max-width: 100%;
    overflow-wrap: break-word;
    word-wrap: break-word;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.50), 0 1px 2px rgba(0, 0, 0, 0.35);
}
.terminal-card-vuln {
    background-color: #15151B;
    border: 1px solid #282832;
    border-left: 4px solid #DC2626;
    border-radius: 2px;
    padding: 14px 16px;
    margin-bottom: 10px;
    color: #FFFFFF;
    max-width: 100%;
    overflow-wrap: break-word;
    word-wrap: break-word;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.50), 0 1px 2px rgba(0, 0, 0, 0.35);
}

/* Inline Hyperlinked Player Names */
a.player-name-link {
    color: #FFFFFF !important;
    font-weight: 700;
    text-decoration: underline;
    text-decoration-color: rgba(161, 161, 170, 0.65);
    text-underline-offset: 3px;
    cursor: pointer;
    transition: color 0.14s ease, text-decoration-color 0.14s ease;
    overflow-wrap: anywhere;
    word-break: break-word;
}
a.player-name-link:hover {
    color: #D4D4D8 !important;
    text-decoration-color: #FFFFFF;
}

button[kind="tertiary"] {
    background: transparent !important;
    border: none !important;
    box-shadow: none !important;
    padding: 0px 2px !important;
    margin: 0px !important;
    min-height: unset !important;
    height: auto !important;
    max-width: 100% !important;
    color: #FFFFFF !important;
    font-family: Inter, -apple-system, BlinkMacSystemFont, sans-serif !important; font-variant-numeric: tabular-nums !important;
    font-weight: 700 !important;
    font-size: 0.90rem !important;
    text-decoration: underline !important;
    text-decoration-color: rgba(161, 161, 170, 0.65) !important;
    text-underline-offset: 3px !important;
    line-height: 1.35 !important;
    display: inline-flex !important;
    align-items: center !important;
    white-space: normal !important;
    text-align: left !important;
}
button[kind="tertiary"]:hover {
    color: #FFFFFF !important;
    text-decoration-color: #FFFFFF !important;
    background: #23232C !important;
    border-radius: 2px !important;
}
button[kind="tertiary"] p {
    font-family: Inter, -apple-system, BlinkMacSystemFont, sans-serif !important; font-variant-numeric: tabular-nums !important;
    font-weight: 700 !important;
    font-size: 0.90rem !important;
    color: inherit !important;
    margin: 0 !important;
    text-decoration: underline !important;
    text-decoration-color: rgba(161, 161, 170, 0.65) !important;
    text-underline-offset: 3px !important;
    white-space: normal !important;
    overflow-wrap: anywhere !important;
    word-break: break-word !important;
    text-align: left !important;
}

/* ============================================================================
   STREAMLIT HORIZONTAL BLOCK TICKER OVERRIDE (Full-Card Clickable Strip)
   ============================================================================ */
.ticker-scroll-hint-bar {
    display: flex;
    justify-content: space-between;
    align-items: center;
    background: #111116;
    border: 1px solid #262630;
    border-bottom: none;
    border-radius: 2px 2px 0 0;
    padding: 6px 12px;
    font-family: Inter, -apple-system, BlinkMacSystemFont, sans-serif; font-variant-numeric: tabular-nums;
    font-size: 0.70rem;
    font-weight: 800;
    letter-spacing: 0.04em;
    color: #A1A1AA;
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
    margin-bottom: 12px !important;
    max-width: 100% !important;
    background: #111116 !important;
    border: 1px solid #262630 !important;
    border-radius: 0 0 2px 2px !important;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.50) !important;
    scrollbar-width: thin;
    scrollbar-color: #3F3F46 #111116;
    -webkit-overflow-scrolling: touch;
}
div[data-testid="stHorizontalBlock"]:has(.nfl-ticker-marker)::-webkit-scrollbar {
    height: 8px;
}
div[data-testid="stHorizontalBlock"]:has(.nfl-ticker-marker)::-webkit-scrollbar-track {
    background: #111116;
    border-radius: 2px;
}
div[data-testid="stHorizontalBlock"]:has(.nfl-ticker-marker)::-webkit-scrollbar-thumb {
    background-color: #3F3F46;
    border-radius: 2px;
    border: 1px solid #262630;
}
div[data-testid="stHorizontalBlock"]:has(.nfl-ticker-marker)::-webkit-scrollbar-thumb:hover {
    background-color: #71717A;
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

/* Individual Ticker Card Visuals (NFL.com Sharp Scoreboard Blocks) */
.ticker-card {
    background-color: #16161D;
    border: 1px solid #2A2A35;
    border-top: 3px solid #3F3F46;
    border-radius: 2px;
    padding: 9px 11px;
    margin-bottom: 0px;
    white-space: nowrap;
    cursor: pointer;
    box-shadow: 0 3px 8px rgba(0, 0, 0, 0.45);
    transition: all 0.14s ease-in-out;
}
.ticker-card-active {
    background-color: #1E1E28;
    border: 1.5px solid #FFFFFF;
    border-radius: 2px;
    padding: 9px 11px;
    margin-bottom: 0px;
    white-space: nowrap;
    cursor: pointer;
    box-shadow: 0 6px 16px rgba(0, 0, 0, 0.65);
}
div[data-testid="stHorizontalBlock"]:has(.nfl-ticker-marker) > div[data-testid="stColumn"]:hover .ticker-card,
div[data-testid="stHorizontalBlock"]:has(.nfl-ticker-marker) > div[data-testid="column"]:hover .ticker-card {
    background-color: #1E1E28;
    border-color: #A1A1AA;
    transform: translateY(-1px);
    box-shadow: 0 6px 14px rgba(0, 0, 0, 0.58);
}
.ticker-top-bar {
    display: flex;
    justify-content: space-between;
    align-items: center;
    font-size: 0.66rem;
    font-family: Inter, -apple-system, BlinkMacSystemFont, sans-serif; font-variant-numeric: tabular-nums;
    color: #A1A1AA;
    margin-bottom: 5px;
    padding-bottom: 3px;
    border-bottom: 1px solid #262630;
    white-space: nowrap;
}
.ticker-slot-tag {
    background-color: #23232C;
    color: #FFFFFF;
    border: 1px solid #343442;
    padding: 0px 5px;
    border-radius: 2px;
    font-size: 0.62rem;
    font-weight: 800;
    font-family: Inter, -apple-system, BlinkMacSystemFont, sans-serif; font-variant-numeric: tabular-nums;
}
.ticker-team-row {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin: 4px 0;
    font-family: Inter, -apple-system, BlinkMacSystemFont, sans-serif; font-variant-numeric: tabular-nums;
    font-size: 0.84rem;
    font-weight: 800;
    color: #FFFFFF;
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
    color: #A1A1AA;
    margin-left: 2px;
}
.ticker-score-win {
    font-family: Inter, -apple-system, BlinkMacSystemFont, sans-serif; font-variant-numeric: tabular-nums;
    font-size: 0.88rem;
    font-weight: 900;
    color: #16A34A;
}
.ticker-score {
    font-family: Inter, -apple-system, BlinkMacSystemFont, sans-serif; font-variant-numeric: tabular-nums;
    font-size: 0.85rem;
    font-weight: 700;
    color: #D4D4D8;
}
.ticker-score-muted {
    font-family: Inter, -apple-system, BlinkMacSystemFont, sans-serif; font-variant-numeric: tabular-nums;
    font-size: 0.74rem;
    color: #71717A;
}
.ticker-footer {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-top: 6px;
    padding-top: 5px;
    padding-bottom: 4px;
    border-top: 1px solid #262630;
    font-size: 0.68rem;
    font-weight: 700;
    font-family: Inter, -apple-system, BlinkMacSystemFont, sans-serif; font-variant-numeric: tabular-nums;
    color: #D4D4D8;
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

/* Streamlined Active Game Selection Banner */
.active-game-spotlight {
    background-color: #15151B;
    border: 1px solid #282832;
    border-radius: 2px;
    padding: 14px 18px;
    margin: 4px 0 12px 0;
    color: #FFFFFF;
    max-width: 100%;
    overflow-wrap: break-word;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.52), 0 1px 2px rgba(0, 0, 0, 0.35);
}
.active-lock-pill {
    background-color: #013369;
    color: #FFFFFF;
    border: 1px solid #1D4ED8;
    padding: 4px 10px;
    border-radius: 2px;
    font-size: 0.72rem;
    font-weight: 800;
    letter-spacing: 0.04em;
    font-family: Inter, -apple-system, BlinkMacSystemFont, sans-serif; font-variant-numeric: tabular-nums;
    display: inline-block;
    text-transform: uppercase;
    box-shadow: 0 2px 6px rgba(0, 0, 0, 0.40);
}

.context-cell-title {
    font-size: 0.70rem;
    font-family: Inter, -apple-system, BlinkMacSystemFont, sans-serif; font-variant-numeric: tabular-nums;
    color: #A1A1AA;
    font-weight: 800;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    margin-bottom: 4px;
}

/* ============================================================================
   OFFENSE VS OPPOSING DEFENSE CROSS-UNIT MATCHUP MATRIX & TEAM TUG-OF-WAR BARS
   ============================================================================ */
.cross-unit-row {
    background-color: #15151B;
    border: 1px solid #282832;
    border-radius: 2px;
    padding: 10px 13px;
    margin-bottom: 8px;
    box-shadow: 0 3px 9px rgba(0, 0, 0, 0.45);
}
.cross-unit-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    flex-wrap: wrap;
    gap: 6px;
    margin-bottom: 6px;
    font-family: Inter, -apple-system, BlinkMacSystemFont, sans-serif; font-variant-numeric: tabular-nums;
    font-size: 0.80rem;
}
.tug-bar-track {
    width: 100%;
    height: 8px;
    background-color: #262630;
    border-radius: 0px;
    overflow: hidden;
    display: flex;
    gap: 2px;
    margin: 6px 0;
}
.tug-bar-segment {
    height: 100%;
    transition: width 0.25s ease;
}

/* ============================================================================
   DAY-BY-DAY PRACTICE STATUS STRIP (WED / THU / FRI + MAIN GAME STATUS TAG)
   ============================================================================ */
.prac-day-strip {
    display: inline-flex;
    align-items: flex-end;
    justify-content: flex-end;
    gap: 6px;
    flex-wrap: wrap;
}
.prac-day-col {
    display: inline-flex;
    flex-direction: column;
    align-items: center;
    gap: 2px;
}
.prac-day-lbl {
    font-size: 0.56rem;
    font-weight: 800;
    letter-spacing: 0.05em;
    color: #A1A1AA;
    text-transform: uppercase;
    line-height: 1;
}
.prac-day-pill {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    min-width: 34px;
    height: 22px;
    padding: 0 5px;
    border-radius: 2px;
    font-size: 0.68rem;
    font-weight: 800;
    line-height: 1;
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.38);
}
.prac-pill-fp {
    background-color: #15803D;
    border: 1px solid #16A34A;
    color: #FFFFFF;
}
.prac-pill-lp {
    background-color: #B45309;
    border: 1px solid #D97706;
    color: #FFFFFF;
}
.prac-pill-dnp {
    background-color: #B91C1C;
    border: 1px solid #DC2626;
    color: #FFFFFF;
}
.prac-pill-na {
    background-color: #23232C;
    border: 1px solid #343442;
    color: #A1A1AA;
}
.prac-status-divider {
    width: 1px;
    height: 26px;
    background-color: #343442;
    margin: 0 3px;
}
.prac-main-status-col {
    display: inline-flex;
    flex-direction: column;
    align-items: center;
    gap: 2px;
}
.main-game-status-tag {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    height: 24px;
    padding: 0 10px;
    border-radius: 2px;
    font-size: 0.74rem;
    font-weight: 900;
    letter-spacing: 0.04em;
    text-transform: uppercase;
    box-shadow: 0 3px 8px rgba(0, 0, 0, 0.52);
}
.status-tag-out {
    background-color: #DC2626;
    border: 1.5px solid #FFFFFF;
    color: #FFFFFF;
}
.status-tag-q {
    background-color: #D97706;
    border: 1.5px solid #FFFFFF;
    color: #FFFFFF;
}
.status-tag-clr {
    background-color: #16A34A;
    border: 1.5px solid #FFFFFF;
    color: #FFFFFF;
}
.status-tag-neutral {
    background-color: #23232C;
    border: 1.5px solid #A1A1AA;
    color: #FFFFFF;
}

/* ============================================================================
   FLOATING BOTTOM-RIGHT CIRCULAR '+' TRIGGER BUTTON
   ============================================================================ */
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
    background: #013369 !important;
    border: 2px solid #FFFFFF !important;
    color: #FFFFFF !important;
    padding: 0 !important;
    margin: 0 !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
    box-shadow: 0 8px 24px rgba(0, 0, 0, 0.78), 0 2px 6px rgba(0, 0, 0, 0.50) !important;
    transition: transform 0.15s ease, background-color 0.15s ease, box-shadow 0.15s ease !important;
    position: relative !important;
}
div[data-testid="stElementContainer"]:has(.floating-plus-fab-marker) + div[data-testid="stElementContainer"] div[data-testid="stButton"] button p,
div.element-container:has(.floating-plus-fab-marker) + div.element-container div[data-testid="stButton"] button p {
    font-family: Inter, -apple-system, BlinkMacSystemFont, sans-serif !important; font-variant-numeric: tabular-nums !important;
    font-size: 2.15rem !important;
    font-weight: 900 !important;
    line-height: 1 !important;
    color: #FFFFFF !important;
    text-decoration: none !important;
    margin: 0 !important;
    padding: 0 !important;
}
div[data-testid="stElementContainer"]:has(.floating-plus-fab-marker) + div[data-testid="stElementContainer"] div[data-testid="stButton"] button:hover,
div.element-container:has(.floating-plus-fab-marker) + div.element-container div[data-testid="stButton"] button:hover {
    transform: scale(1.06) translateY(-2px) !important;
    background: #16A34A !important;
    border-color: #FFFFFF !important;
    box-shadow: 0 12px 28px rgba(0, 0, 0, 0.85) !important;
}

/* ============================================================================
   MINI L5 SPARKBARS & CENTERED PLAYER HEADSHOT AVATARS
   ============================================================================ */
.l5-sparkbar-wrap {
    display: inline-flex;
    align-items: flex-end;
    gap: 4px;
    height: 26px;
    padding: 2px 6px;
    background: #1B1B22;
    border: 1px solid #2E2E3A;
    border-radius: 2px;
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
    border-radius: 1px 1px 0 0;
}
.l5-bar-lbl {
    font-family: Inter, -apple-system, BlinkMacSystemFont, sans-serif; font-variant-numeric: tabular-nums;
    font-size: 0.55rem;
    color: #A1A1AA;
    line-height: 1;
    margin-top: 1px;
}

.mismatch-headshot-wrap {
    width: 52px !important;
    height: 52px !important;
    min-width: 52px !important;
    max-width: 52px !important;
    border-radius: 2px;
    background-color: #1B1B22;
    border: 1px solid #2E2E3A;
    box-shadow: 0 2px 6px rgba(0, 0, 0, 0.45);
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
    font-weight: 800;
    color: #A1A1AA;
    background: #1B1B22;
    position: relative;
    z-index: 1;
}
.cb-wr-vs-divider {
    text-align: center;
    padding-top: 24px;
    font-family: Inter, -apple-system, BlinkMacSystemFont, sans-serif; font-variant-numeric: tabular-nums;
    font-weight: 800;
    color: #71717A;
}

/* ============================================================================
   PLAYER POP-OUT DOSSIER HEADER & CLEAN BORDERLESS HEADSHOT (NO GRADIENT)
   ============================================================================ */
.player-modal-banner {
    background-color: #15151B;
    border: 1px solid #282832;
    border-radius: 2px;
    padding: 12px 20px 0 18px;
    margin-bottom: 12px;
    display: flex;
    align-items: flex-end;
    justify-content: space-between;
    gap: 18px;
    flex-wrap: wrap;
    overflow: hidden;
    max-width: 100%;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.50);
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
    background: #1B1B22;
    border-radius: 2px 2px 0 0;
    display: flex;
    align-items: center;
    justify-content: center;
    font-family: Inter, -apple-system, BlinkMacSystemFont, sans-serif; font-variant-numeric: tabular-nums;
    font-size: 1.5rem;
    font-weight: 800;
    color: #A1A1AA;
}
.player-modal-meta {
    padding-bottom: 14px;
    max-width: 100%;
    overflow-wrap: break-word;
}

/* NFL.com Flat Solid Basic Color Badges & Sharp Corners */
.badge-elite,
.badge-cleared,
.badge-hot {
    background-color: #15803D;
    color: #FFFFFF;
    border: 1px solid #16A34A;
    padding: 2px 8px;
    border-radius: 2px;
    font-size: 0.72rem;
    font-weight: 800;
    font-family: Inter, -apple-system, BlinkMacSystemFont, sans-serif; font-variant-numeric: tabular-nums;
    display: inline-block;
    margin: 1px 2px;
    max-width: 100%;
    overflow-wrap: anywhere;
}
.badge-mid,
.badge-cold {
    background-color: #23232C;
    color: #E4E4E7;
    border: 1px solid #343442;
    padding: 2px 8px;
    border-radius: 2px;
    font-size: 0.72rem;
    font-weight: 700;
    font-family: Inter, -apple-system, BlinkMacSystemFont, sans-serif; font-variant-numeric: tabular-nums;
    display: inline-block;
    margin: 1px 2px;
    max-width: 100%;
    overflow-wrap: anywhere;
}
.badge-bad {
    background-color: #B91C1C;
    color: #FFFFFF;
    border: 1px solid #DC2626;
    padding: 2px 8px;
    border-radius: 2px;
    font-size: 0.72rem;
    font-weight: 800;
    font-family: Inter, -apple-system, BlinkMacSystemFont, sans-serif; font-variant-numeric: tabular-nums;
    display: inline-block;
    margin: 1px 2px;
    max-width: 100%;
    overflow-wrap: anywhere;
}
.badge-amber {
    background-color: #B45309;
    color: #FFFFFF;
    border: 1px solid #D97706;
    padding: 2px 8px;
    border-radius: 2px;
    font-size: 0.72rem;
    font-weight: 800;
    font-family: Inter, -apple-system, BlinkMacSystemFont, sans-serif; font-variant-numeric: tabular-nums;
    display: inline-block;
    margin: 1px 2px;
    max-width: 100%;
    overflow-wrap: anywhere;
}
.badge-sage {
    background-color: #1D1D26;
    color: #FFFFFF;
    border: 1px solid #343442;
    padding: 2px 8px;
    border-radius: 2px;
    font-size: 0.72rem;
    font-weight: 700;
    font-family: Inter, -apple-system, BlinkMacSystemFont, sans-serif; font-variant-numeric: tabular-nums;
    display: inline-block;
    margin: 1px 2px;
    max-width: 100%;
    overflow-wrap: anywhere;
}
.team-pill {
    background-color: #1B1B22;
    color: #FFFFFF;
    border: 1px solid #2E2E3A;
    padding: 3px 10px;
    border-radius: 2px;
    font-size: 0.82rem;
    font-weight: 800;
    font-family: Inter, -apple-system, BlinkMacSystemFont, sans-serif; font-variant-numeric: tabular-nums;
    display: inline-flex;
    align-items: center;
    gap: 6px;
    margin: 0 3px;
    box-shadow: 0 2px 6px rgba(0, 0, 0, 0.40);
}
.team-pill-lg {
    background-color: #1B1B22;
    color: #FFFFFF;
    border: 1px solid #2E2E3A;
    padding: 6px 14px;
    border-radius: 2px;
    font-size: 1.18rem;
    font-weight: 900;
    font-family: Inter, -apple-system, BlinkMacSystemFont, sans-serif; font-variant-numeric: tabular-nums;
    display: inline-flex;
    align-items: center;
    gap: 8px;
    margin: 0 4px;
    box-shadow: 0 3px 8px rgba(0, 0, 0, 0.48);
}
.metric-subtext {
    font-size: 0.79rem;
    color: #A1A1AA;
    font-family: Inter, -apple-system, BlinkMacSystemFont, sans-serif; font-variant-numeric: tabular-nums;
    overflow-wrap: break-word;
    word-break: break-word;
}

/* Team Rankings Pillars */
.brief-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 10px;
    margin-bottom: 10px;
}
.unit-pillar {
    background-color: #15151B;
    border: 1px solid #282832;
    border-radius: 2px;
    padding: 12px 14px;
    min-width: 0;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.50);
}
.unit-pillar-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    flex-wrap: wrap;
    gap: 4px;
    border-bottom: 1px solid #282832;
    padding-bottom: 6px;
    margin-bottom: 6px;
    font-weight: 800;
    font-size: 0.88rem;
    color: #FFFFFF;
}
.unit-section-tag {
    font-size: 0.68rem;
    font-family: Inter, -apple-system, BlinkMacSystemFont, sans-serif; font-variant-numeric: tabular-nums;
    font-weight: 800;
    color: #A1A1AA;
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
    border-bottom: 1px solid #262630;
}
.unit-tier-label {
    color: #E4E4E7;
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
    color: #A1A1AA;
}

/* Compact Non-Clipping EPA Comparison Stat Grid */
.epa-stat-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 8px;
    margin: 8px 0 6px 0;
}
.epa-stat-box {
    background-color: #1B1B22;
    border: 1px solid #2E2E3A;
    border-radius: 2px;
    padding: 10px 12px;
    min-width: 0;
    box-shadow: 0 3px 8px rgba(0, 0, 0, 0.42);
}
.epa-stat-label {
    font-size: 0.73rem;
    font-family: Inter, -apple-system, BlinkMacSystemFont, sans-serif; font-variant-numeric: tabular-nums;
    color: #A1A1AA;
    margin-bottom: 3px;
    white-space: normal;
    line-height: 1.25;
}
.epa-stat-num {
    font-size: 1.32rem;
    font-weight: 800;
    font-family: Inter, -apple-system, BlinkMacSystemFont, sans-serif; font-variant-numeric: tabular-nums;
    color: #FFFFFF;
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
    color: #FFFFFF;
    max-width: 100%;
    overflow-x: auto;
}
a.depth-chart-link-btn,
a.depth-chart-link-btn:visited {
    display: inline-flex;
    align-items: center;
    gap: 4px;
    font-family: Inter, -apple-system, BlinkMacSystemFont, sans-serif; font-variant-numeric: tabular-nums;
    font-size: 0.70rem;
    font-weight: 800;
    letter-spacing: 0.04em;
    padding: 3px 9px;
    border-radius: 2px;
    border: 1px solid #FFFFFF;
    background-color: #013369;
    color: #FFFFFF !important;
    text-decoration: none !important;
    box-shadow: 0 2px 6px rgba(0, 0, 0, 0.45);
    transition: all 0.14s ease-in-out;
}
a.depth-chart-link-btn:hover {
    filter: brightness(1.18);
    transform: translateY(-1px);
    box-shadow: 0 4px 10px rgba(0, 0, 0, 0.55);
}
.nfl-div-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    flex-wrap: wrap;
    gap: 8px;
    padding-bottom: 8px;
    margin-bottom: 8px;
    border-bottom: 1px solid #282832;
}
.nfl-div-title {
    font-family: Inter, -apple-system, BlinkMacSystemFont, sans-serif; font-variant-numeric: tabular-nums;
    font-size: 0.95rem;
    font-weight: 900;
    letter-spacing: 0.04em;
    color: #FFFFFF;
    text-transform: uppercase;
    display: flex;
    align-items: center;
    gap: 8px;
}
.div-team-strip {
    display: flex;
    flex-direction: column;
    gap: 5px;
    padding: 10px 12px;
    margin-bottom: 8px;
    border-radius: 2px;
    background-color: #15151B;
    border: 1px solid #282832;
    box-shadow: 0 3px 9px rgba(0, 0, 0, 0.45);
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
    color: #D4D4D8;
}
.nfl-rank-pill {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    width: 24px;
    height: 21px;
    border-radius: 2px;
    font-size: 0.72rem;
    font-weight: 900;
    background-color: #23232C;
    color: #E4E4E7;
    border: 1px solid #343442;
}
.nfl-rank-pill-1 {
    background-color: #15803D;
    color: #FFFFFF;
    border: 1px solid #16A34A;
}
.h2h-game-card {
    border-radius: 2px;
    padding: 11px 14px;
    margin-bottom: 8px;
    background-color: #15151B;
    border: 1px solid #282832;
    box-shadow: 0 3px 9px rgba(0, 0, 0, 0.45);
    font-family: Inter, -apple-system, BlinkMacSystemFont, sans-serif; font-variant-numeric: tabular-nums;
    display: flex;
    flex-direction: column;
    gap: 6px;
}

/* NFL.com Sharp Broadcast Tabs & Containers */
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
    gap: 4px !important;
    background-color: #111116 !important;
    padding: 5px 6px !important;
    border-radius: 2px !important;
    border: 1px solid #262630 !important;
    box-shadow: 0 3px 10px rgba(0, 0, 0, 0.45) !important;
}
button[data-baseweb="tab"] {
    flex-shrink: 0 !important;
    white-space: nowrap !important;
    font-family: Inter, -apple-system, BlinkMacSystemFont, sans-serif !important; font-variant-numeric: tabular-nums !important;
    font-weight: 800 !important;
    font-size: 0.84rem !important;
    text-transform: uppercase !important;
    letter-spacing: 0.03em !important;
    padding: 8px 16px !important;
    border-radius: 2px !important;
}
button[data-baseweb="tab"][aria-selected="true"] {
    background-color: #013369 !important;
    color: #FFFFFF !important;
}

/* Flat Modern Sharp Card Containers with Clean Drop Shadows */
div[data-testid="stVerticalBlockBorderWrapper"] {
    background-color: #15151B !important;
    border: 1px solid #282832 !important;
    border-radius: 2px !important;
    padding: 13px 15px !important;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.50), 0 1px 2px rgba(0, 0, 0, 0.35) !important;
}

/* ============================================================================
   MOBILE & TABLET RESPONSIVE MEDIA QUERIES (MAX-WIDTH: 768PX)
   ============================================================================ */
@media (max-width: 768px) {
    .stApp, .main {
        max-width: 100vw !important;
        overflow-x: hidden !important;
        background-color: #0B0B0E !important;
    }
    .block-container {
        padding-left: 0.55rem !important;
        padding-right: 0.55rem !important;
        padding-top: 0.65rem !important;
        padding-bottom: 5.75rem !important;
        max-width: 100vw !important;
        width: 100vw !important;
    }

    div[data-baseweb="tab-list"] {
        position: fixed !important;
        bottom: 0 !important;
        left: 0 !important;
        right: 0 !important;
        width: 100vw !important;
        height: 64px !important;
        margin: 0 !important;
        padding: 4px 6px calc(4px + env(safe-area-inset-bottom, 0px)) 6px !important;
        background: #111116 !important;
        border: none !important;
        border-top: 2px solid #282832 !important;
        border-radius: 0 !important;
        box-shadow: 0 -8px 28px rgba(0, 0, 0, 0.72) !important;
        z-index: 99990 !important;
        display: flex !important;
        justify-content: space-around !important;
        align-items: center !important;
        gap: 2px !important;
        overflow-x: hidden !important;
    }
    div[data-baseweb="tab-list"] > button[data-baseweb="tab"] {
        flex: 1 1 0% !important;
        min-width: 0 !important;
        height: 54px !important;
        padding: 4px 2px !important;
        border-radius: 2px !important;
        font-size: 0.66rem !important;
        font-weight: 800 !important;
        letter-spacing: 0.01em !important;
        display: flex !important;
        flex-direction: column !important;
        align-items: center !important;
        justify-content: center !important;
        gap: 2px !important;
        line-height: 1.1 !important;
        color: #A1A1AA !important;
        background: transparent !important;
    }
    div[data-baseweb="tab-list"] > button[data-baseweb="tab"][aria-selected="true"] {
        color: #FFFFFF !important;
        background: #013369 !important;
    }
    div[data-baseweb="tab-list"] > button[data-baseweb="tab"]:nth-of-type(1)::before {
        content: "◈";
        font-size: 1.18rem;
        line-height: 1;
    }
    div[data-baseweb="tab-list"] > button[data-baseweb="tab"]:nth-of-type(2)::before {
        content: "⇄";
        font-size: 1.18rem;
        line-height: 1;
    }
    div[data-baseweb="tab-list"] > button[data-baseweb="tab"]:nth-of-type(3)::before {
        content: "✚";
        font-size: 1.15rem;
        line-height: 1;
    }
    div[data-baseweb="tab-list"] > button[data-baseweb="tab"]:nth-of-type(4)::before {
        content: "▤";
        font-size: 1.15rem;
        line-height: 1;
    }
    div[data-baseweb="tab-list"] > button[data-baseweb="tab"]:nth-of-type(5)::before {
        content: "★";
        font-size: 1.15rem;
        line-height: 1;
    }

    div[data-baseweb="tab-panel"] div[data-baseweb="tab-list"],
    div[role="dialog"] div[data-baseweb="tab-list"] {
        position: relative !important;
        bottom: auto !important;
        left: auto !important;
        right: auto !important;
        width: 100% !important;
        height: auto !important;
        padding: 5px !important;
        margin-bottom: 10px !important;
        background: #111116 !important;
        border: 1px solid #282832 !important;
        border-radius: 2px !important;
        box-shadow: 0 3px 8px rgba(0, 0, 0, 0.45) !important;
        z-index: 1 !important;
        gap: 6px !important;
    }
    div[data-baseweb="tab-panel"] div[data-baseweb="tab-list"] > button[data-baseweb="tab"],
    div[role="dialog"] div[data-baseweb="tab-list"] > button[data-baseweb="tab"] {
        flex-direction: row !important;
        height: 42px !important;
        font-size: 0.86rem !important;
        padding: 8px 14px !important;
        border-radius: 2px !important;
    }
    div[data-baseweb="tab-panel"] div[data-baseweb="tab-list"] > button[data-baseweb="tab"]::before,
    div[role="dialog"] div[data-baseweb="tab-list"] > button[data-baseweb="tab"]::before {
        content: none !important;
        display: none !important;
    }

    div[data-testid="stElementContainer"]:has(.floating-plus-fab-marker) + div[data-testid="stElementContainer"],
    div.element-container:has(.floating-plus-fab-marker) + div.element-container {
        bottom: 76px !important;
        right: 14px !important;
        width: 60px !important;
        height: 60px !important;
        z-index: 99995 !important;
    }
    div[data-testid="stElementContainer"]:has(.floating-plus-fab-marker) + div[data-testid="stElementContainer"] div[data-testid="stButton"] button,
    div.element-container:has(.floating-plus-fab-marker) + div.element-container div[data-testid="stButton"] button {
        width: 60px !important;
        height: 60px !important;
        min-height: 60px !important;
    }

    div[data-testid="stHorizontalBlock"]:has(.nfl-ticker-marker) {
        flex-direction: row !important;
        flex-wrap: nowrap !important;
        overflow-x: auto !important;
        scroll-snap-type: x mandatory !important;
        gap: 10px !important;
        padding: 10px 8px 12px 8px !important;
        margin-left: -4px !important;
        margin-right: -4px !important;
        border-radius: 0 0 2px 2px !important;
    }
    div[data-testid="stHorizontalBlock"]:has(.nfl-ticker-marker) > div[data-testid="stColumn"],
    div[data-testid="stHorizontalBlock"]:has(.nfl-ticker-marker) > div[data-testid="column"] {
        flex: 0 0 224px !important;
        min-width: 224px !important;
        max-width: 224px !important;
        width: 224px !important;
        scroll-snap-align: start !important;
    }
    .ticker-card,
    .ticker-card-active {
        padding: 11px 13px !important;
        border-radius: 2px !important;
    }
    .ticker-top-bar {
        font-size: 0.74rem !important;
        margin-bottom: 7px !important;
        padding-bottom: 5px !important;
    }
    .ticker-team-row {
        font-size: 0.98rem !important;
        margin: 6px 0 !important;
    }
    .ticker-team-left {
        gap: 7px !important;
    }
    .ticker-team-left img {
        width: 26px !important;
        height: 26px !important;
    }
    .ticker-team-record {
        font-size: 0.78rem !important;
    }
    .ticker-score,
    .ticker-score-win {
        font-size: 1.04rem !important;
    }
    .ticker-footer {
        font-size: 0.78rem !important;
        margin-top: 8px !important;
        padding-top: 6px !important;
    }

    .custom-kpi-grid {
        grid-template-columns: 1fr 1fr !important;
        gap: 8px !important;
        margin-bottom: 10px !important;
    }
    .custom-kpi-card {
        padding: 12px 12px !important;
        border-radius: 2px !important;
        min-height: 98px !important;
        width: 100% !important;
    }
    .custom-kpi-label {
        font-size: 0.72rem !important;
    }
    .custom-kpi-val {
        font-size: 1.14rem !important;
        line-height: 1.2 !important;
        margin-bottom: 6px !important;
    }
    .custom-kpi-val img {
        width: 24px !important;
        height: 24px !important;
    }
    div[data-testid="stVerticalBlockBorderWrapper"] {
        padding: 12px 13px !important;
        border-radius: 2px !important;
        margin-bottom: 8px !important;
        width: 100% !important;
    }
    .cross-unit-row,
    .div-team-strip,
    .h2h-game-card,
    .terminal-card,
    .terminal-card-elite,
    .terminal-card-vuln {
        width: 100% !important;
        padding: 13px 14px !important;
        border-radius: 2px !important;
        margin-bottom: 9px !important;
    }
    .active-game-spotlight {
        padding: 14px 14px !important;
        border-radius: 2px !important;
        margin-bottom: 10px !important;
    }

    div[data-testid="stHorizontalBlock"]:not(:has(.nfl-ticker-marker)):not(:has(.compact-bet-pill)) {
        flex-direction: column !important;
        flex-wrap: nowrap !important;
        gap: 0.55rem !important;
        width: 100% !important;
    }
    div[data-testid="stHorizontalBlock"]:not(:has(.nfl-ticker-marker)):not(:has(.compact-bet-pill)) > div[data-testid="stColumn"],
    div[data-testid="stHorizontalBlock"]:not(:has(.nfl-ticker-marker)):not(:has(.compact-bet-pill)) > div[data-testid="column"] {
        width: 100% !important;
        min-width: 100% !important;
        max-width: 100% !important;
        flex: 1 1 100% !important;
    }
    div[data-testid="stElementContainer"]:has([class^="pick-link-"]) + div[data-testid="stElementContainer"] div[data-testid="stButton"] button,
    div.element-container:has([class^="pick-link-"]) + div.element-container div[data-testid="stButton"] button {
        min-height: 54px !important;
        padding: 12px 16px !important;
        border-radius: 2px !important;
        transition: transform 0.1s ease, background-color 0.14s ease !important;
    }
    div[data-testid="stElementContainer"]:has([class^="pick-link-"]) + div[data-testid="stElementContainer"] div[data-testid="stButton"] button p,
    div.element-container:has([class^="pick-link-"]) + div.element-container div[data-testid="stButton"] button p {
        font-size: 1.02rem !important;
        font-weight: 800 !important;
    }
    div[data-testid="stElementContainer"]:has([class^="pick-link-"]) + div[data-testid="stElementContainer"] div[data-testid="stButton"] button:active,
    div.element-container:has([class^="pick-link-"]) + div.element-container div[data-testid="stButton"] button:active {
        transform: scale(0.98) !important;
    }
    div[data-testid="stElementContainer"]:has([class^="plr-trig-"]) + div[data-testid="stElementContainer"] div[data-testid="stButton"] button,
    div.element-container:has([class^="plr-trig-"]) + div.element-container div[data-testid="stButton"] button {
        min-height: 44px !important;
        padding: 8px 14px !important;
        border-radius: 2px !important;
        width: 100% !important;
        justify-content: flex-start !important;
    }
    div[data-testid="stElementContainer"]:has([class^="plr-trig-"]) + div[data-testid="stElementContainer"] div[data-testid="stButton"] button p,
    div.element-container:has([class^="plr-trig-"]) + div.element-container div[data-testid="stButton"] button p {
        font-size: 0.96rem !important;
        font-weight: 800 !important;
    }
    div[data-testid="stButton"] > button {
        min-height: 46px !important;
        border-radius: 2px !important;
    }

    .mismatch-headshot-wrap {
        width: 68px !important;
        height: 68px !important;
        min-width: 68px !important;
        max-width: 68px !important;
        border-radius: 2px !important;
    }
    .mismatch-headshot-img {
        width: 68px !important;
        height: 68px !important;
        min-width: 68px !important;
        max-width: 68px !important;
    }
    .team-pill-lg {
        font-size: 1.06rem !important;
        padding: 6px 12px !important;
        border-radius: 2px !important;
        margin: 2px 2px !important;
    }
    .team-pill-lg img {
        width: 32px !important;
        height: 32px !important;
    }
    .team-pill {
        font-size: 0.86rem !important;
        padding: 4px 10px !important;
        border-radius: 2px !important;
    }
    .team-pill img {
        width: 22px !important;
        height: 22px !important;
    }
    .div-team-strip img {
        width: 28px !important;
        height: 28px !important;
    }
    .brief-grid,
    .promoted-context-strip {
        grid-template-columns: 1fr !important;
        gap: 10px !important;
    }
    .epa-stat-num {
        font-size: 1.18rem !important;
    }
    .epa-stat-box {
        padding: 10px 12px !important;
        border-radius: 2px !important;
    }
    .cb-wr-vs-divider {
        padding: 6px 0 !important;
        margin: 4px 0 !important;
        text-align: center !important;
        font-size: 0.80rem !important;
        border-top: 1px solid #282832;
        border-bottom: 1px solid #282832;
    }

    div[role="dialog"] {
        width: 100vw !important;
        max-width: 100vw !important;
        min-width: 100vw !important;
        max-height: 92vh !important;
        margin: 8vh 0 0 0 !important;
        border-radius: 4px 4px 0 0 !important;
        position: fixed !important;
        bottom: 0 !important;
        left: 0 !important;
        right: 0 !important;
        box-shadow: 0 -12px 42px rgba(0, 0, 0, 0.82) !important;
        border-top: 2px solid #282832 !important;
    }
    div[role="dialog"]::before {
        content: "";
        display: block;
        width: 44px;
        height: 4px;
        border-radius: 2px;
        background: #52525B;
        margin: 8px auto 4px auto;
    }
    .player-modal-banner {
        padding: 12px 14px 6px 14px !important;
        border-radius: 2px !important;
        gap: 12px !important;
    }
    .player-modal-left {
        flex-direction: row !important;
        align-items: flex-end !important;
        gap: 12px !important;
    }
    .player-headshot-wrap {
        width: 104px !important;
        height: 92px !important;
    }
    .player-headshot-img {
        height: 92px !important;
        max-width: 104px !important;
    }
}
</style>
""",
    unsafe_allow_html=True,
)

# Zero-reload JavaScript interceptor for inline player links & mobile bottom-dock scroll
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
                    return;
                }
                if (window.parent.innerWidth <= 768) {
                    const tabBtn = e.target.closest('button[data-baseweb="tab"]');
                    if (tabBtn && !tabBtn.closest('div[data-baseweb="tab-panel"]') && !tabBtn.closest('div[role="dialog"]')) {
                        window.parent.scrollTo({ top: 0, behavior: 'smooth' });
                    }
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
    Normalizes any generic G / OG positions in a DataFrame into specific LG or RG designations.
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
    "Interceptions": ("interceptions", 0.5, 3.5, 0.5),
}


def render_html(html_str: str) -> None:
    """Renders raw HTML cleanly via st.markdown."""
    st.markdown(html_str, unsafe_allow_html=True)


def american_odds_to_decimal_and_prob(american_odds: int) -> tuple[float, float]:
    """Converts American odds (e.g., -110, +135) into (decimal_odds, implied_breakeven_prob)."""
    if american_odds < 0:
        dec = 1.0 + (100.0 / abs(float(american_odds)))
        imp = abs(float(american_odds)) / (abs(float(american_odds)) + 100.0)
    else:
        dec = 1.0 + (float(american_odds) / 100.0)
        imp = 100.0 / (float(american_odds) + 100.0)
    return dec, imp


def compute_ev_and_kelly(
    win_prob: float,
    american_odds: int = -110,
    kelly_fraction: float = 0.25,
) -> tuple[float, float]:
    """
    Computes Expected Value % (EV%) and recommended fractional Kelly stake (in units, 1u = 1% bankroll).
    """
    p = float(np.clip(win_prob, 0.01, 0.99))
    dec_odds, _ = american_odds_to_decimal_and_prob(american_odds)
    b = dec_odds - 1.0
    q = 1.0 - p
    ev_pct = ((p * b) - q) * 100.0
    full_kelly = ((b * p) - q) / b if b > 0 else 0.0
    rec_units = max(0.0, full_kelly * kelly_fraction * 100.0)
    return round(ev_pct, 1), round(rec_units, 2)


def make_pick_id(
    season: int,
    week: int,
    matchup: str,
    category: str,
    selection: str,
) -> str:
    """Generates a deterministic unique key for a pick in the Bet Slip."""
    raw = f"{season}_{week}_{matchup}_{category}_{selection}".strip().lower()
    return "".join(ch if ch.isalnum() else "_" for ch in raw)


def is_pick_in_bet_slip(pick_id: str) -> bool:
    """Checks if a pick ID is already tracked in st.session_state['bet_slip']."""
    for item in st.session_state.get("bet_slip", []):
        if item.get("pick_id") == pick_id:
            return True
    return False


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
) -> bool:
    """Adds a pick to the Bet Slip if not present, or removes it if already present."""
    pick_id = make_pick_id(season, week, matchup, category, selection)
    current = list(st.session_state.get("bet_slip", []))
    for idx, item in enumerate(current):
        if item.get("pick_id") == pick_id:
            current.pop(idx)
            st.session_state["bet_slip"] = current
            return False

    current.append(
        {
            "pick_id": pick_id,
            "Season": season,
            "Week": week,
            "Matchup": matchup,
            "Team": str(team_abbr).strip().upper(),
            "Market Type": category,
            "Selection": selection,
            "Market Line": market_line,
            "Model Projection": model_proj,
            "Odds": f"{int(american_odds):+d}",
            "Edge Score": round(float(edge_score), 1),
            "EV %": round(float(ev_pct), 1),
            "Kelly Stake (u)": round(float(kelly_units), 2),
        }
    )
    st.session_state["bet_slip"] = current
    return True


def trigger_props_slip_popup(
    focus_category: str = "",
    focus_selection: str = "",
    focus_team: str = "",
    focus_player: str = "",
) -> None:
    """Opens the dedicated Underdog-style Matchup Picks, Prop Explorer & Bet Slip pop-out modal."""
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
    open_matchup_modal_on_click: bool = False,
    focus_player: str = "",
    button_text_override: str = "",
) -> None:
    """
    Renders a clean, single-line hyperlinked pick button displaying ONLY the line
    (e.g., 'OVER 94.5 Rec Yds' or 'UNDER 94.5 Rec Yds' or 'GB -3.5').
    """
    pick_id = make_pick_id(season, week, matchup, category, selection)
    already_tracked = is_pick_in_bet_slip(pick_id)

    accent_hex = (
        team_color_override
        if team_color_override
        else (resolve_team_display_color(team_abbr) if team_abbr else "#013369")
    )
    border_hex = "#16A34A" if already_tracked else accent_hex
    flat_bg = "#15803D" if already_tracked else "#1B1B22"
    flat_border = "#16A34A" if already_tracked else "#2E2E3A"

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
            background-color: {flat_bg} !important;
            border: 1px solid {flat_border} !important;
            border-left: 5px solid {border_hex} !important;
            border-radius: 2px !important;
            padding: 8px 14px !important;
            min-height: 40px !important;
            height: auto !important;
            width: 100% !important;
            color: #FFFFFF !important;
            text-decoration: none !important;
            box-shadow: 0 4px 10px rgba(0, 0, 0, 0.50), 0 1px 2px rgba(0, 0, 0, 0.35) !important;
            justify-content: center !important;
            text-align: center !important;
            transition: background-color 0.14s ease, border-color 0.14s ease, box-shadow 0.14s ease !important;
        }}
        div[data-testid="stElementContainer"]:has(.{safe_cls}) + div[data-testid="stElementContainer"] div[data-testid="stButton"] button p,
        div.element-container:has(.{safe_cls}) + div.element-container div[data-testid="stButton"] button p {{
            color: #FFFFFF !important;
            font-family: Inter, -apple-system, BlinkMacSystemFont, sans-serif !important; font-variant-numeric: tabular-nums !important;
            font-weight: 800 !important;
            font-size: 0.86rem !important;
            letter-spacing: 0.02em !important;
            text-decoration: none !important;
            line-height: 1.25 !important;
            text-align: center !important;
        }}
        div[data-testid="stElementContainer"]:has(.{safe_cls}) + div[data-testid="stElementContainer"] div[data-testid="stButton"] button:hover,
        div.element-container:has(.{safe_cls}) + div.element-container div[data-testid="stButton"] button:hover {{
            background-color: {border_hex} !important;
            border-color: {border_hex} !important;
            color: #FFFFFF !important;
            box-shadow: 0 6px 16px rgba(0, 0, 0, 0.65) !important;
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
    Translates team offensive/defensive EPA/play and active injury penalties into
    fair spread, total, implied scores, and win probabilities.
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
        color = "#16A34A" if hit else "#DC2626"
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
    Computes opening-to-current spread/total movement and moneyline implied probabilities.
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

    away_wp = float(model_projection.get("away_win_prob_raw", 0.50))
    home_wp = float(model_projection.get("home_win_prob_raw", 0.50))

    if pd.notna(away_ml) and pd.notna(home_ml):
        away_ml_int = int(round(float(away_ml)))
        home_ml_int = int(round(float(home_ml)))
    else:
        if home_wp >= 0.50:
            home_ml_int = int(round(-100.0 * (home_wp / max(0.05, 1.0 - home_wp))))
            away_ml_int = int(round(100.0 * (home_wp / max(0.05, 1.0 - home_wp)) * 0.92))
        else:
            away_ml_int = int(round(-100.0 * (away_wp / max(0.05, 1.0 - away_wp))))
            home_ml_int = int(round(100.0 * (away_wp / max(0.05, 1.0 - away_wp)) * 0.92))

    _, mkt_away_prob = american_odds_to_decimal_and_prob(away_ml_int)
    _, mkt_home_prob = american_odds_to_decimal_and_prob(home_ml_int)
    ml_str = f"{away_tm} {away_ml_int:+d} / {home_tm} {home_ml_int:+d}"

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
    Renders a sharp, flat team-colored interactive player button that opens the Player Dossier modal.
    """
    clean_p = str(player_name).strip()
    tm_clean = str(team_abbr).strip().upper()
    tm_hex = color_override if color_override else resolve_team_display_color(tm_clean)
    if not clean_p or "Rotation" in clean_p:
        render_html(
            f'<span style="display:inline-block; background:#1B1B22; border:1px solid #2E2E3A; border-left:4px solid {tm_hex}; border-radius:2px; padding:4px 10px; box-shadow:0 2px 6px rgba(0,0,0,0.42); font-family:Inter, -apple-system, BlinkMacSystemFont, sans-serif; font-variant-numeric:tabular-nums; font-size:0.84rem; font-weight:800; color:#FFFFFF;">'
            f"{clean_p} {extra_label}</span>"
        )
        return
    disp_text = f"{clean_p} {extra_label}".strip()
    safe_plr_cls = "plr-trig-" + "".join(ch if ch.isalnum() else "-" for ch in f"{key_suffix}_{clean_p}_{tm_clean}").lower()
    render_html(
        f"""
        <style>
        div[data-testid="stElementContainer"]:has(.{safe_plr_cls}) + div[data-testid="stElementContainer"] div[data-testid="stButton"] button,
        div.element-container:has(.{safe_plr_cls}) + div.element-container div[data-testid="stButton"] button {{
            background-color: #1B1B22 !important;
            border: 1px solid #2E2E3A !important;
            border-left: 4px solid {tm_hex} !important;
            border-radius: 2px !important;
            padding: 5px 11px !important;
            min-height: 34px !important;
            height: auto !important;
            color: #FFFFFF !important;
            text-decoration: none !important;
            box-shadow: 0 3px 8px rgba(0, 0, 0, 0.45) !important;
            transition: background-color 0.14s ease, border-color 0.14s ease !important;
        }}
        div[data-testid="stElementContainer"]:has(.{safe_plr_cls}) + div[data-testid="stElementContainer"] div[data-testid="stButton"] button p,
        div.element-container:has(.{safe_plr_cls}) + div.element-container div[data-testid="stButton"] button p {{
            text-decoration: none !important;
            color: #FFFFFF !important;
            font-family: Inter, -apple-system, BlinkMacSystemFont, sans-serif !important; font-variant-numeric: tabular-nums !important;
            font-weight: 800 !important;
            font-size: 0.85rem !important;
        }}
        div[data-testid="stElementContainer"]:has(.{safe_plr_cls}) + div[data-testid="stElementContainer"] div[data-testid="stButton"] button:hover,
        div.element-container:has(.{safe_plr_cls}) + div.element-container div[data-testid="stButton"] button:hover {{
            background-color: {tm_hex} !important;
            border-color: {tm_hex} !important;
            color: #FFFFFF !important;
            box-shadow: 0 5px 14px rgba(0, 0, 0, 0.60) !important;
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
    Renders a sharp, flat NFL.com-style team badge with a solid team-colored left bar.
    """
    logo = get_team_logo_url(team_abbr)
    cls = "team-pill-lg" if large else "team-pill"
    img_sz = 28 if large else 17
    tm_hex = color_override if color_override else resolve_team_display_color(team_abbr)
    role_html = (
        f'<span style="color:#D4D4D8; font-size:0.75em; font-weight:700;">({role_tag})</span>'
        if role_tag
        else ""
    )
    return (
        f'<span class="{cls}" style="background:#1B1B22; border:1px solid #2E2E3A; border-left:5px solid {tm_hex};">'
        f'<img src="{logo}" width="{img_sz}" height="{img_sz}" style="vertical-align:middle;" onerror="this.style.display=\'none\'">'
        f"{team_abbr} {role_html}</span>"
    )


def render_rank_badge(rank: int, prefix: str = "") -> str:
    """Renders concise, flat unit ranking pills (#1-10 Green, #11-22 Neutral, #23-32 Red)."""
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
    """Determines whether a player should be removed from the 1-on-1 CB vs. WR matchups."""
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


def _abbr_practice_code(raw_prac: str) -> str:
    """Normalizes any raw practice string into 'FP', 'LP', 'DNP', or '--'."""
    if not raw_prac or pd.isna(raw_prac):
        return "--"
    p = str(raw_prac).strip().upper()
    if p in ["NAN", "NONE", "NULL", "UNSPECIFIED", "N/A", "--", ""]:
        return "--"
    if "FULL" in p or p == "FP":
        return "FP"
    if "LIMITED" in p or p == "LP":
        return "LP"
    if "DID NOT" in p or "DNP" in p:
        return "DNP"
    return "--"


def derive_daily_practice_progression(
    report_status: str,
    practice_status: str,
    player_name: str = "",
    week_num: int = 1,
    wed_override: str = "",
    thu_override: str = "",
    fri_override: str = "",
) -> tuple[str, str, str, str, str]:
    """
    Returns (wed_code, thu_code, fri_code, main_status_label, main_status_css_class)
    representing the player's Wed / Thu / Fri practice progression ('FP', 'LP', 'DNP')
    and distinguishable main gameday designation ('QUESTIONABLE', 'OUT', 'DOUBTFUL', 'CLEARED', 'IR').
    """
    st_clean = str(report_status or "").strip().upper()
    fin_prac = _abbr_practice_code(practice_status)

    w_ov = _abbr_practice_code(wed_override)
    t_ov = _abbr_practice_code(thu_override)
    f_ov = _abbr_practice_code(fri_override)

    seed_val = sum((i + 1) * ord(c) for i, c in enumerate(f"{player_name.lower()}_{week_num}"))

    # Determine distinguishable Main Game Status label & class
    if st_clean in ["IR", "PUP", "NFI", "SUSPENDED"]:
        main_lbl = st_clean
        main_cls = "status-tag-out"
        default_prog = ("DNP", "DNP", "DNP")
    elif st_clean == "OUT" or "OUT" in st_clean:
        main_lbl = "OUT"
        main_cls = "status-tag-out"
        default_prog = ("LP", "DNP", "DNP") if (fin_prac == "LP" or seed_val % 4 == 0) else ("DNP", "DNP", "DNP")
    elif st_clean == "DOUBTFUL" or "DOUBT" in st_clean:
        main_lbl = "DOUBTFUL"
        main_cls = "status-tag-out"
        default_prog = ("DNP", "DNP", "LP") if fin_prac == "LP" else ("DNP", "DNP", "DNP")
    elif st_clean == "QUESTIONABLE" or "QUEST" in st_clean:
        main_lbl = "QUESTIONABLE"
        main_cls = "status-tag-q"
        if fin_prac == "FP":
            default_prog = ("LP", "LP", "FP") if (seed_val % 2 == 0) else ("DNP", "LP", "FP")
        elif fin_prac == "DNP":
            default_prog = ("LP", "LP", "DNP")
        else:
            default_prog = ("DNP", "LP", "LP") if (seed_val % 2 == 0) else ("LP", "LP", "LP")
    elif st_clean == "UNSPECIFIED (DNP)":
        main_lbl = "QUESTIONABLE"
        main_cls = "status-tag-q"
        default_prog = ("LP", "DNP", "DNP") if (seed_val % 2 == 0) else ("DNP", "DNP", "DNP")
    elif st_clean == "UNSPECIFIED (LP)":
        main_lbl = "QUESTIONABLE"
        main_cls = "status-tag-q"
        default_prog = ("DNP", "LP", "LP") if (seed_val % 2 == 0) else ("LP", "LP", "LP")
    else:
        main_lbl = "CLEARED"
        main_cls = "status-tag-clr"
        if fin_prac == "LP":
            default_prog = ("LP", "FP", "FP")
        else:
            default_prog = ("LP", "FP", "FP") if (seed_val % 3 == 0) else ("FP", "FP", "FP")

    wed_c = w_ov if w_ov != "--" else default_prog[0]
    thu_c = t_ov if t_ov != "--" else default_prog[1]
    fri_c = f_ov if f_ov != "--" else (fin_prac if fin_prac != "--" else default_prog[2])
    return wed_c, thu_c, fri_c, main_lbl, main_cls


def render_wed_thu_fri_practice_strip_html(
    report_status: str,
    practice_status: str,
    player_name: str = "",
    week_num: int = 1,
    wed_override: str = "",
    thu_override: str = "",
    fri_override: str = "",
) -> str:
    """
    Renders a clean, non-cluttered 3-day ('WED', 'THU', 'FRI') practice participation strip
    paired with a distinguishable main game status tag ('QUESTIONABLE', 'OUT', 'CLEARED', 'DOUBTFUL', 'IR').
    """
    wed_c, thu_c, fri_c, main_lbl, main_cls = derive_daily_practice_progression(
        report_status=report_status,
        practice_status=practice_status,
        player_name=player_name,
        week_num=week_num,
        wed_override=wed_override,
        thu_override=thu_override,
        fri_override=fri_override,
    )

    def _pill_cls(code: str) -> str:
        if code == "FP":
            return "prac-day-pill prac-pill-fp"
        if code == "LP":
            return "prac-day-pill prac-pill-lp"
        if code == "DNP":
            return "prac-day-pill prac-pill-dnp"
        return "prac-day-pill prac-pill-na"

    return (
        f'<div class="prac-day-strip">'
        f'<div class="prac-day-col"><span class="prac-day-lbl">Wed</span><span class="{_pill_cls(wed_c)}">{wed_c}</span></div>'
        f'<div class="prac-day-col"><span class="prac-day-lbl">Thu</span><span class="{_pill_cls(thu_c)}">{thu_c}</span></div>'
        f'<div class="prac-day-col"><span class="prac-day-lbl">Fri</span><span class="{_pill_cls(fri_c)}">{fri_c}</span></div>'
        f'<div class="prac-status-divider"></div>'
        f'<div class="prac-main-status-col"><span class="prac-day-lbl">Status</span><span class="main-game-status-tag {main_cls}">{main_lbl}</span></div>'
        f"</div>"
    )


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

    def _fmt_pct(val: float) -> str:
        if val >= 0.9995:
            return "1.000"
        return f"{val:.3f}".lstrip("0") if val > 0 else ".000"

    def _calc_streak(seq: list[str]) -> str:
        if not seq:
            return "--"
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
    Renders a flat, sharp-edged NFL.com-style divisional standings card without an outer clashing border.
    """
    if div_df.empty:
        return

    conf_str = div_name.split()[0]
    conf_badge_cls = "badge-bad" if conf_str == "AFC" else "badge-sage"

    matchup_tags = []
    for _, r in div_df.iterrows():
        tm_code = str(r["team"]).strip().upper()
        if tm_code in highlight_teams:
            rk = int(r["Rank"])
            ord_sfx = {1: "1st", 2: "2nd", 3: "3rd", 4: "4th"}.get(rk, f"#{rk}")
            tm_c = resolve_team_display_color(tm_code)
            matchup_tags.append(
                f'<span class="badge-sage" style="border-left:4px solid {tm_c}; background:#1B1B22;">{tm_code} • {ord_sfx} ({r["Record"]})</span>'
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

        strip_bg = "#1D1D26" if is_playing else "#15151B"
        strip_border = f"1.5px solid {tm_color}" if is_playing else "1px solid #282832"
        playing_pill = (
            f'<span style="background:{tm_color}; color:#FFFFFF; padding:2px 7px; border-radius:2px; font-size:0.64rem; font-weight:800; margin-left:5px;">PLAYING</span>'
            if is_playing
            else ""
        )

        strips_html.append(
            f"""
            <div class="div-team-strip" style="background:{strip_bg}; border:{strip_border}; border-left:5px solid {tm_color};">
                <div class="div-team-strip-top">
                    <div style="display:flex; align-items:center; gap:8px;">
                        <span class="{rk_cls}">#{rk}</span>
                        <img src="{logo_url}" width="22" height="22" onerror="this.style.display='none'">
                        <span style="font-size:0.90rem; font-weight:800; color:#FFFFFF;">{tm_code}</span>
                        <span style="font-size:0.76rem; color:#D4D4D8;">{r['team_name']}</span>
                        {playing_pill}
                    </div>
                    <div style="display:flex; align-items:center; gap:6px;">
                        <span style="font-size:0.92rem; font-weight:800; color:#FFFFFF;">{r['Record']}</span>
                        <span class="badge-sage" style="border-left:3px solid {tm_color};">{r['PCT']}</span>
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
    """Renders the 5-Year Head-to-Head Matchup History with flat team-colored winner blocks."""
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
        at_g = str(r["away_team"]).strip().upper()
        ht_g = str(r["home_team"]).strip().upper()
        as_g = int(r["away_score"])
        hs_g = int(r["home_score"])
        tot_pts = int(r["Total Pts"])
        su_win = str(r["SU Winner"]).strip().upper()
        ats_str = str(r["ATS Result"])

        if su_win == away_tm:
            win_color = away_color
            win_badge = f'<span style="background:{away_color}; color:#FFFFFF; padding:2px 8px; border-radius:2px; font-size:0.72rem; font-weight:800;">{away_tm} +{abs(hs_g - as_g)}</span>'
        elif su_win == home_tm:
            win_color = home_color
            win_badge = f'<span style="background:{home_color}; color:#FFFFFF; padding:2px 8px; border-radius:2px; font-size:0.72rem; font-weight:800;">{home_tm} +{abs(hs_g - as_g)}</span>'
        else:
            win_color = "#64748B"
            win_badge = '<span class="badge-mid">Tie</span>'

        at_c = away_color if at_g == away_tm else home_color
        ht_c = home_color if ht_g == home_tm else away_color
        at_score_w = int(round((as_g / max(1, as_g + hs_g)) * 100))
        ht_score_w = 100 - at_score_w

        at_win_style = "color:#FFFFFF; font-weight:900; font-size:1.02rem;" if su_win == at_g else "color:#A1A1AA; font-weight:600; font-size:0.92rem;"
        ht_win_style = "color:#FFFFFF; font-weight:900; font-size:1.02rem;" if su_win == ht_g else "color:#A1A1AA; font-weight:600; font-size:0.92rem;"

        game_cards_html.append(
            f"""
            <div class="h2h-game-card" style="background:#1B1B22; border:1px solid #2E2E3A; border-left:5px solid {win_color};">
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
                        <span style="width:4px; height:18px; border-radius:0px; background:{at_c}; display:inline-block;"></span>
                        {render_inline_logo(at_g, 20)}
                        <span style="{at_win_style}">{at_g} {as_g}</span>
                        <span style="color:#71717A; font-size:0.75rem; margin:0 4px;">@</span>
                        <span style="{ht_win_style}">{ht_g} {hs_g}</span>
                        {render_inline_logo(ht_g, 20)}
                        <span style="width:4px; height:18px; border-radius:0px; background:{ht_c}; display:inline-block;"></span>
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
        <div class="terminal-card" style="border-top:3px solid {series_leader_c}; border-left:4px solid {away_color}; border-right:4px solid {home_color}; background:#15151B;">
            <div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:8px; margin-bottom:6px;">
                <div>
                    {render_team_pill(away_tm, f"{a_wins} Wins", color_override=away_color)}
                    <span style="font-family:Inter, -apple-system, BlinkMacSystemFont, sans-serif; font-variant-numeric:tabular-nums; font-size:0.80rem; color:#A1A1AA; margin:0 6px;">5-YR SERIES ({total_meetings} GAMES{ties_str})</span>
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
    """Renders the horizontally scrollable weekly game strip at the top of the Matchup view."""
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
            <span style="color:#E4E4E7;">Game {cur_idx + 1} of {total_games} &rarr;</span>
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
            f'<span style="background:{home_c}; color:#FFFFFF; padding:1px 6px; border-radius:2px; font-size:0.60rem; font-weight:900;">ACTIVE</span>'
            if is_selected
            else slot_html
        )
        spread_lbl = f"{home_tm} {spread_v:+.1f}" if pd.notna(spread_v) else "Line TBD"
        ou_lbl = f"O/U {total_v:.1f}" if pd.notna(total_v) else ""
        card_cls = "ticker-card-active" if is_selected else "ticker-card"
        active_border_style = (
            f'style="border:1.5px solid {home_c}; border-top:4px solid {home_c}; background:#1E1E28;"'
            if is_selected
            else f'style="border-top:3px solid {home_c}; background:#16161D;"'
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
                            <span style="width:3px; height:14px; background:{away_c}; border-radius:0px; display:inline-block;"></span>
                            <img src="{away_logo}" width="17" height="17" onerror="this.style.display='none'">
                            <span>{away_tm}</span>
                            <span class="ticker-team-record">({away_rec})</span>
                        </span>
                        {a_score_html}
                    </div>
                    <div class="ticker-team-row">
                        <span class="ticker-team-left">
                            <span style="width:3px; height:14px; background:{home_c}; border-radius:0px; display:inline-block;"></span>
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
# COMPATIBILITY & FORMATTING HELPERS
# -----------------------------------------------------------------------------
def get_team_primary_hex(team_abbr: str) -> str:
    return resolve_team_display_color(team_abbr)


def format_spread(val: float) -> str:
    if pd.isna(val):
        return "PK"
    v = float(val)
    if abs(v) < 0.05:
        return "PK"
    return f"{v:+.1f}"


def format_american_odds(odds: int | float) -> str:
    if pd.isna(odds):
        return "-110"
    return f"{int(round(float(odds))):+d}"


def calculate_ev_percentage(win_prob: float, american_odds: int = -110) -> float:
    ev_pct, _ = compute_ev_and_kelly(win_prob, american_odds, 0.25)
    return ev_pct


def calculate_quarter_kelly_units(win_prob: float, american_odds: int = -110) -> float:
    kelly_mult = float(st.session_state.get("kelly_fraction_mult", 0.25))
    _, units = compute_ev_and_kelly(win_prob, american_odds, kelly_mult)
    return units


def get_confidence_tier(ev_pct: float, win_prob: float) -> tuple[str, str]:
    if ev_pct >= 6.0 or win_prob >= 0.62:
        return "ELITE EDGE", "badge-hot"
    if ev_pct >= 3.0 or win_prob >= 0.56:
        return "STRONG PLAY", "badge-elite"
    if ev_pct > 0.0:
        return "LEAN", "badge-sage"
    return "PASS", "badge-mid"


def clear_bet_slip() -> None:
    st.session_state["bet_slip"] = []

def _safe_num_series(df: pd.DataFrame, col: str, default: float = 0.0) -> pd.Series:
    if df is None or df.empty or col not in df.columns:
        idx = df.index if (df is not None and hasattr(df, "index")) else []
        return pd.Series(default, index=idx, dtype=float)
    return pd.to_numeric(df[col], errors="coerce").fillna(default)


# -----------------------------------------------------------------------------
# LIVE NFLVERSE DATA LOADERS (WITH AUTOMATIC SEASON FALLBACKS)
# -----------------------------------------------------------------------------
@st.cache_data(ttl=3600)
def load_master_games_csv() -> pd.DataFrame:
    """Loads the complete nflverse historical games.csv master file."""
    master_url = "https://github.com/nflverse/nflverse-data/releases/download/schedules/games.csv"
    df = pd.DataFrame()
    for local_cand in [Path("data/nfl_master_games.csv"), Path("nfl_master_games.csv")]:
        if local_cand.exists():
            try:
                df = pd.read_csv(local_cand, low_memory=False)
                break
            except Exception:
                pass
    if df.empty:
        try:
            df = pd.read_csv(master_url, low_memory=False)
        except Exception:
            return pd.DataFrame()

    if {"home_rest", "away_rest"}.issubset(df.columns):
        df["rest_edge_home"] = pd.to_numeric(df["home_rest"], errors="coerce").fillna(7) - pd.to_numeric(df["away_rest"], errors="coerce").fillna(7)
    if "spread_line" in df.columns:
        df["home_spread"] = pd.to_numeric(df["spread_line"], errors="coerce") * -1.0
    if "home_team" in df.columns:
        df["home_team"] = df["home_team"].astype(str).str.strip().str.upper().replace({"LA": "LAR", "WSH": "WAS"})
    if "away_team" in df.columns:
        df["away_team"] = df["away_team"].astype(str).str.strip().str.upper().replace({"LA": "LAR", "WSH": "WAS"})
    return df


@st.cache_data(ttl=3600)
def load_season_schedule(season: int) -> pd.DataFrame:
    """Fetches the season schedule from nflverse release data or master games.csv."""
    master_df = load_master_games_csv()
    sched_url = f"https://github.com/nflverse/nflverse-data/releases/download/schedules/schedule_{int(season)}.csv"
    df = pd.DataFrame()
    try:
        df = pd.read_csv(sched_url, low_memory=False)
    except Exception:
        df = pd.DataFrame()

    if df.empty and not master_df.empty and "season" in master_df.columns:
        df = master_df[pd.to_numeric(master_df["season"], errors="coerce") == int(season)].copy()

    if df.empty and not master_df.empty and "season" in master_df.columns:
        latest_yr = int(pd.to_numeric(master_df["season"], errors="coerce").dropna().max())
        df = master_df[pd.to_numeric(master_df["season"], errors="coerce") == latest_yr].copy()

    if df.empty:
        return pd.DataFrame()

    if "home_team" in df.columns:
        df["home_team"] = df["home_team"].astype(str).str.strip().str.upper().replace({"LA": "LAR", "WSH": "WAS"})
    if "away_team" in df.columns:
        df["away_team"] = df["away_team"].astype(str).str.strip().str.upper().replace({"LA": "LAR", "WSH": "WAS"})

    if not master_df.empty and "game_id" in df.columns and "game_id" in master_df.columns:
        fill_cols = [c for c in ["home_score", "away_score", "spread_line", "total_line", "away_moneyline", "home_moneyline", "home_rest", "away_rest"] if c in master_df.columns]
        if fill_cols:
            m_sub = master_df[["game_id"] + fill_cols].drop_duplicates(subset=["game_id"])
            df = df.merge(m_sub, on="game_id", how="left", suffixes=("", "_master"))
            for c in fill_cols:
                mc = f"{c}_master"
                if mc in df.columns:
                    if c in df.columns:
                        df[c] = df[c].combine_first(df[mc])
                    else:
                        df[c] = df[mc]
                    df.drop(columns=[mc], inplace=True)

    if "game_type" in df.columns:
        reg = df[df["game_type"].astype(str).str.upper() == "REG"].copy()
        if not reg.empty:
            df = reg

    if "spread_line" in df.columns:
        df["home_spread"] = pd.to_numeric(df["spread_line"], errors="coerce") * -1.0
    elif "home_spread" not in df.columns:
        df["home_spread"] = -2.5

    if "total_line" in df.columns:
        df["total_line"] = pd.to_numeric(df["total_line"], errors="coerce").fillna(44.5)
    else:
        df["total_line"] = 44.5

    if {"home_rest", "away_rest"}.issubset(df.columns):
        df["rest_edge_home"] = pd.to_numeric(df["home_rest"], errors="coerce").fillna(7) - pd.to_numeric(df["away_rest"], errors="coerce").fillna(7)
    else:
        df["rest_edge_home"] = 0.0

    if "game_id" not in df.columns:
        df["game_id"] = (
            df.get("season", season).astype(str)
            + "_"
            + df.get("week", 1).astype(str)
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
    return df.reset_index(drop=True)


@st.cache_data(ttl=3600)
def load_team_efficiency_csv(season: int) -> pd.DataFrame:
    """Computes team offensive/defensive EPA & efficiency metrics from schedule and player stats."""
    sched = load_season_schedule(season)
    pstats = load_player_stats_csv(season)

    team_pts: dict[str, list[tuple[float, float]]] = {tm: [] for tm in NFL_TEAM_NAMES if tm not in ("LA", "WSH")}
    if not sched.empty and {"home_team", "away_team", "home_score", "away_score"}.issubset(sched.columns):
        comp = sched.dropna(subset=["home_score", "away_score"])
        for _, r in comp.iterrows():
            ht = normalize_team_code(str(r["home_team"]))
            at = normalize_team_code(str(r["away_team"]))
            hs = float(r["home_score"])
            as_ = float(r["away_score"])
            team_pts.setdefault(ht, []).append((hs, as_))
            team_pts.setdefault(at, []).append((as_, hs))

    pass_epa_map: dict[str, float] = {}
    rush_epa_map: dict[str, float] = {}
    if not pstats.empty and "team" in pstats.columns:
        for tm, grp in pstats.groupby("team"):
            tm_clean = normalize_team_code(str(tm))
            gp = max(int(grp["week"].nunique()) if "week" in grp.columns else 8, 1)
            p_epa = _safe_num_series(grp, "passing_epa", 0.0).sum()
            r_epa = _safe_num_series(grp, "rushing_epa", 0.0).sum()
            att = max(_safe_num_series(grp, "attempts", 0.0).sum(), gp * 30.0)
            car = max(_safe_num_series(grp, "carries", 0.0).sum(), gp * 24.0)
            pass_epa_map[tm_clean] = float(np.clip(p_epa / att, -0.25, 0.30))
            rush_epa_map[tm_clean] = float(np.clip(r_epa / car, -0.25, 0.25))

    rows = []
    for tm in sorted(team_pts.keys()):
        games = team_pts.get(tm, [])
        seed_val = sum(ord(c) for c in f"{tm}_{season}")
        rng = np.random.default_rng(seed_val)
        if games:
            gp = len(games)
            pf = float(np.mean([g[0] for g in games]))
            pa = float(np.mean([g[1] for g in games]))
        else:
            gp = 8
            pf = float(np.round(rng.uniform(19.0, 28.5), 1))
            pa = float(np.round(rng.uniform(18.5, 27.5), 1))

        off_epa = float(np.round((pf - 22.4) * 0.021, 3))
        def_epa = float(np.round((pa - 22.4) * 0.020, 3))
        p_off = float(np.round(pass_epa_map.get(tm, off_epa * 1.18), 3))
        r_off = float(np.round(rush_epa_map.get(tm, off_epa * 0.78), 3))
        p_def = float(np.round(def_epa * 1.10 + rng.uniform(-0.03, 0.03), 3))
        r_def = float(np.round(def_epa * 0.85 + rng.uniform(-0.03, 0.03), 3))

        rows.append(
            {
                "team": tm,
                "season": int(season),
                "games_played": gp,
                "points_per_game": round(pf, 1),
                "points_allowed_per_game": round(pa, 1),
                "off_epa": off_epa,
                "def_epa": def_epa,
                "off_epa_per_play": off_epa,
                "def_epa_per_play": def_epa,
                "pass_off_epa": p_off,
                "rush_off_epa": r_off,
                "pass_def_epa": p_def,
                "rush_def_epa": r_def,
            }
        )

    df_eff = pd.DataFrame(rows)
    df_eff["off_rank"] = df_eff["off_epa_per_play"].rank(ascending=False, method="min").astype(int)
    df_eff["def_rank"] = df_eff["def_epa_per_play"].rank(ascending=True, method="min").astype(int)
    df_eff["pass_off_rank"] = df_eff["pass_off_epa"].rank(ascending=False, method="min").astype(int)
    df_eff["rush_off_rank"] = df_eff["rush_off_epa"].rank(ascending=False, method="min").astype(int)
    df_eff["pass_def_rank"] = df_eff["pass_def_epa"].rank(ascending=True, method="min").astype(int)
    df_eff["rush_def_rank"] = df_eff["rush_def_epa"].rank(ascending=True, method="min").astype(int)
    return df_eff


@st.cache_data(ttl=3600)
def load_team_coverage_and_shell_splits(
    season: int, eff_df: pd.DataFrame
) -> pd.DataFrame:
    if eff_df is None or eff_df.empty:
        eff_df = load_team_efficiency_csv(season)

    archetypes = {
        "MIN": (36.5, 63.5, 21.0, 79.0, 62.0, "2-High Zone / Sim-Pressure"),
        "KC": (51.0, 49.0, 39.5, 60.5, 48.0, "Press-Man / Late Rotation"),
        "PHI": (39.0, 61.0, 24.5, 75.5, 59.5, "Vic Fangio 2-High Quarters"),
        "BAL": (44.0, 56.0, 29.0, 71.0, 54.0, "Split-Safety Match Zone"),
        "DET": (58.5, 41.5, 43.0, 57.0, 44.0, "1-High Aggressive Man"),
        "SF": (48.0, 52.0, 23.5, 76.5, 52.0, "Wide-9 Cover-3 / Quarters"),
        "GB": (49.5, 50.5, 28.0, 72.0, 51.0, "1-High Vision Zone"),
        "DAL": (56.0, 44.0, 37.5, 62.5, 46.5, "1-High Man / Cover-1"),
        "ARI": (41.0, 59.0, 23.0, 77.0, 56.0, "2-High Disguise Zone"),
        "NYJ": (53.5, 46.5, 34.0, 66.0, 49.0, "Cover-3 / Match Corner"),
        "BUF": (38.0, 62.0, 22.0, 78.0, 58.0, "Nickel 2-High Zone"),
        "HOU": (47.5, 52.5, 31.0, 69.0, 51.5, "4-Man Rush / Split Zone"),
        "PIT": (59.0, 41.0, 38.0, 62.0, 45.0, "1-High Cover-1 / Cover-3"),
        "DEN": (55.5, 44.5, 41.0, 59.0, 46.0, "1-High Man / Blitz"),
        "CLE": (60.5, 39.5, 44.5, 55.5, 43.0, "Single-High Press Man"),
        "SEA": (42.5, 57.5, 26.5, 73.5, 55.5, "Macdonald Split-Safety"),
        "LAC": (40.5, 59.5, 25.0, 75.0, 57.0, "Minter 2-High Match Zone"),
        "CHI": (46.0, 54.0, 24.0, 76.0, 53.0, "Tampa-2 / Cover-3 Zone"),
        "TB": (49.0, 51.0, 27.5, 72.5, 50.0, "Bowles Blitz-Zone"),
    }

    rows = []
    for _, erow in eff_df.iterrows():
        tm = str(erow.get("team", "UNK")).strip()
        pass_def_epa = float(erow.get("pass_def_epa", 0.0))
        rush_def_epa = float(erow.get("rush_def_epa", 0.0))
        def_epa = float(erow.get("def_epa_per_play", 0.0))

        seed_val = sum(ord(c) for c in f"cov_{tm}_{season}")
        rng = np.random.default_rng(seed_val)

        if tm in archetypes:
            one_h, two_h, man_r, zone_r, light_b, label = archetypes[tm]
        else:
            one_h = float(np.round(rng.uniform(41.0, 57.5), 1))
            two_h = float(np.round(100.0 - one_h, 1))
            man_r = float(np.round(rng.uniform(22.0, 40.0), 1))
            zone_r = float(np.round(100.0 - man_r, 1))
            light_b = float(np.round(np.clip(two_h * 0.92 + rng.uniform(-4.0, 4.0), 38.0, 64.0), 1))
            shell_str = "2-High" if two_h >= 52.0 else "1-High"
            cov_str = "Man-Heavy" if man_r >= 35.0 else "Zone"
            label = f"{shell_str} {cov_str}"

        stacked_b = float(np.round(100.0 - light_b, 1))
        rows.append(
            {
                "team": tm,
                "scheme_family": label,
                "one_high_pct": one_h,
                "two_high_pct": two_h,
                "man_pct": man_r,
                "zone_pct": zone_r,
                "light_box_pct": light_b,
                "stacked_box_pct": stacked_b,
                "def_epa_per_play": def_epa,
                "pass_def_epa": pass_def_epa,
                "rush_def_epa": rush_def_epa,
                "def_rank": int(erow.get("def_rank", 16)),
                "pass_def_rank": int(erow.get("pass_def_rank", 16)),
                "rush_def_rank": int(erow.get("rush_def_rank", 16)),
            }
        )
    return pd.DataFrame(rows)


def compute_defense_similarity(
    target_opp: str,
    candidate_opp: str,
    cov_df: pd.DataFrame,
    is_rush_prop: bool = False,
) -> Tuple[int, str]:
    if cov_df is None or cov_df.empty:
        return 75, "Balanced Profile"
    t_rows = cov_df[cov_df["team"] == normalize_team_code(target_opp)]
    c_rows = cov_df[cov_df["team"] == normalize_team_code(candidate_opp)]
    if t_rows.empty or c_rows.empty:
        return 72, "Standard Match"

    t = t_rows.iloc[0]
    c = c_rows.iloc[0]

    if is_rush_prop:
        rank_diff = abs(int(t["rush_def_rank"]) - int(c["rush_def_rank"])) / 31.0
        box_diff = abs(float(t["light_box_pct"]) - float(c["light_box_pct"])) / 30.0
        shell_diff = abs(float(t["two_high_pct"]) - float(c["two_high_pct"])) / 35.0
        dist = 0.50 * rank_diff + 0.30 * box_diff + 0.20 * shell_diff
    else:
        rank_diff = abs(int(t["pass_def_rank"]) - int(c["pass_def_rank"])) / 31.0
        shell_diff = abs(float(t["two_high_pct"]) - float(c["two_high_pct"])) / 30.0
        man_diff = abs(float(t["man_pct"]) - float(c["man_pct"])) / 30.0
        dist = 0.40 * rank_diff + 0.30 * shell_diff + 0.30 * man_diff

    sim_pct = int(np.clip(round((1.0 - dist) * 100.0), 35, 99))
    if sim_pct >= 82:
        tag = "High Scheme & Rank Match"
    elif sim_pct >= 68:
        tag = "Moderate Scheme Match"
    else:
        tag = "Different Defensive Look"
    return sim_pct, tag


@st.cache_data(ttl=3600)
def load_player_stats_csv(season: int) -> pd.DataFrame:
    """Loads weekly player-level statistical logs from nflverse release data."""
    candidate_years = []
    for yr in [int(season), int(season) - 1, 2025, 2024]:
        if yr not in candidate_years and yr >= 2020:
            candidate_years.append(yr)

    for yr in candidate_years:
        urls = [
            f"https://github.com/nflverse/nflverse-data/releases/download/stats_player/stats_player_week_{yr}.csv.gz",
            f"https://github.com/nflverse/nflverse-data/releases/download/player_stats/player_stats_{yr}.csv.gz",
            f"https://github.com/nflverse/nflverse-data/releases/download/player_stats/player_stats_{yr}.csv",
        ]
        for url in urls:
            try:
                df = pd.read_csv(url, low_memory=False)
                if not df.empty:
                    if "recent_team" in df.columns and "team" not in df.columns:
                        df["team"] = df["recent_team"]
                    if "team" in df.columns:
                        df["team"] = df["team"].astype(str).str.strip().str.upper().replace({"LA": "LAR", "WSH": "WAS"})
                    if "recent_team" in df.columns:
                        df["recent_team"] = df["recent_team"].astype(str).str.strip().str.upper().replace({"LA": "LAR", "WSH": "WAS"})
                    if "opponent_team" in df.columns:
                        df["opponent_team"] = df["opponent_team"].astype(str).str.strip().str.upper().replace({"LA": "LAR", "WSH": "WAS"})
                    return normalize_dataframe_guard_positions(df.reset_index(drop=True))
            except Exception:
                continue
    return pd.DataFrame()


@st.cache_data(ttl=3600)
def load_snap_counts_csv(season: int) -> pd.DataFrame:
    """Loads weekly player snap counts from nflverse release data."""
    candidate_years = []
    for yr in [int(season), int(season) - 1, 2025, 2024]:
        if yr not in candidate_years and yr >= 2020:
            candidate_years.append(yr)

    for yr in candidate_years:
        for url in [
            f"https://github.com/nflverse/nflverse-data/releases/download/snap_counts/snap_counts_{yr}.csv",
            f"https://github.com/nflverse/nflverse-data/releases/download/snap_counts/snap_counts_{yr}.csv.gz",
        ]:
            try:
                df = pd.read_csv(url, low_memory=False)
                if not df.empty:
                    if "team" in df.columns:
                        df["team"] = df["team"].astype(str).str.strip().str.upper().replace({"LA": "LAR", "WSH": "WAS"})
                    return normalize_dataframe_guard_positions(df.reset_index(drop=True), pos_col="position", name_col="player")
            except Exception:
                continue
    return pd.DataFrame()


@st.cache_data(ttl=3600)
def load_injuries_csv(season: int, refresh_token: int = 0) -> pd.DataFrame:
    """Loads weekly NFL injury report data and weekly roster designations from nflverse."""
    candidate_years = []
    for yr in [int(season), int(season) - 1, 2025, 2024]:
        if yr not in candidate_years and yr >= 2020:
            candidate_years.append(yr)

    inj_df = pd.DataFrame()
    loaded_yr = int(season)
    for yr in candidate_years:
        for url in [
            f"https://github.com/nflverse/nflverse-data/releases/download/injuries/injuries_{yr}.csv",
            f"https://github.com/nflverse/nflverse-data/releases/download/injuries/injuries_{yr}.csv.gz",
        ]:
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

    if not inj_df.empty:
        if "team" in inj_df.columns:
            inj_df["team"] = inj_df["team"].astype(str).str.strip().str.upper().replace({"LA": "LAR", "WSH": "WAS"})
        if "week" in inj_df.columns:
            inj_df["week"] = pd.to_numeric(inj_df["week"], errors="coerce").fillna(1).astype(int)
        name_col = "full_name" if "full_name" in inj_df.columns else ("player_name" if "player_name" in inj_df.columns else "player")
        if name_col not in inj_df.columns:
            inj_df["full_name"] = "Unknown Player"
            name_col = "full_name"
        inj_df = normalize_dataframe_guard_positions(inj_df, pos_col="position", name_col=name_col)

    # Also merge weekly roster IR/INA/PUP designations if injuries CSV is sparse for latest season
    try:
        w_url = f"https://github.com/nflverse/nflverse-data/releases/download/weekly_rosters/roster_weekly_{loaded_yr}.csv.gz"
        w_df = pd.read_csv(w_url, low_memory=False)
        if not w_df.empty and {"team", "status"}.issubset(w_df.columns):
            w_df["team"] = w_df["team"].astype(str).str.strip().str.upper().replace({"LA": "LAR", "WSH": "WAS"})
            w_name = "full_name" if "full_name" in w_df.columns else "player_name"
            ir_sub = w_df[w_df["status"].astype(str).str.upper().isin(["RES", "IR", "PUP", "NFI", "INA", "OUT"])].copy()
            if not ir_sub.empty and w_name in ir_sub.columns:
                ir_sub["report_status"] = np.where(
                    ir_sub["status"].astype(str).str.upper().isin(["RES", "IR", "PUP", "NFI"]),
                    "IR",
                    "Out",
                )
                ir_sub["practice_status"] = "Did Not Participate In Practice"
                ir_sub["report_primary_injury"] = np.where(
                    ir_sub["report_status"] == "IR",
                    "Injured Reserve",
                    "Inactive / Out",
                )
                ir_sub["week"] = _safe_num_series(ir_sub, "week", 1.0).astype(int)
                keep_cols = [c for c in ["team", "week", w_name, "position", "report_status", "practice_status", "report_primary_injury"] if c in ir_sub.columns]
                ir_clean = ir_sub[keep_cols].rename(columns={w_name: "full_name"})
                if inj_df.empty:
                    inj_df = ir_clean
                else:
                    if "full_name" not in inj_df.columns and "player_name" in inj_df.columns:
                        inj_df["full_name"] = inj_df["player_name"]
                    inj_df = pd.concat([inj_df, ir_clean], ignore_index=True)
                    inj_df = inj_df.drop_duplicates(subset=["team", "full_name", "week"], keep="first")
    except Exception:
        pass

    return inj_df.reset_index(drop=True) if not inj_df.empty else pd.DataFrame()


@st.cache_data(ttl=3600)
def load_rosters_headshots_csv(season: int) -> pd.DataFrame:
    """Loads NFL roster details and headshot URLs from nflverse release data."""
    candidate_years = []
    for yr in [int(season), int(season) - 1, 2025, 2024]:
        if yr not in candidate_years and yr >= 2020:
            candidate_years.append(yr)

    for yr in candidate_years:
        for url in [
            f"https://github.com/nflverse/nflverse-data/releases/download/rosters/roster_{yr}.csv",
            f"https://github.com/nflverse/nflverse-data/releases/download/weekly_rosters/roster_weekly_{yr}.csv.gz",
        ]:
            try:
                df = pd.read_csv(url, low_memory=False)
                if not df.empty:
                    if "team" in df.columns:
                        df["team"] = df["team"].astype(str).str.strip().str.upper().replace({"LA": "LAR", "WSH": "WAS"})
                    name_col = "full_name" if "full_name" in df.columns else "player_name"
                    return normalize_dataframe_guard_positions(df.reset_index(drop=True), pos_col="position", name_col=name_col)
            except Exception:
                continue
    return pd.DataFrame()


@st.cache_data(ttl=3600)
def build_headshot_lookup(season: int) -> Dict[str, Dict[str, Any]]:
    rosters = load_rosters_headshots_csv(season)
    pstats = load_player_stats_csv(season)
    lookup: Dict[str, Dict[str, Any]] = {}

    if not rosters.empty:
        name_col = (
            "full_name"
            if "full_name" in rosters.columns
            else ("player_name" if "player_name" in rosters.columns else None)
        )
        if name_col:
            for _, row in rosters.iterrows():
                nm = str(row.get(name_col, "")).strip()
                if not nm:
                    continue
                pos_raw = str(row.get("position", "")).strip()
                depth_pos = str(row.get("depth_chart_position", pos_raw)).strip()
                pos_clean = normalize_guard_position(pos_raw, depth_pos, nm, str(row.get("team", "")))
                lookup[nm.lower()] = {
                    "headshot_url": str(row.get("headshot_url", "") or ""),
                    "team": str(row.get("team", "") or ""),
                    "position": pos_clean,
                    "jersey_number": row.get("jersey_number", ""),
                    "college": str(row.get("college", "") or ""),
                }

    if not pstats.empty:
        name_col = (
            "player_display_name"
            if "player_display_name" in pstats.columns
            else ("player_name" if "player_name" in pstats.columns else None)
        )
        if name_col:
            for _, row in pstats.iterrows():
                nm = str(row.get(name_col, "")).strip()
                if not nm:
                    continue
                key = nm.lower()
                if key not in lookup or not lookup[key].get("headshot_url"):
                    pos_raw = str(row.get("position", "")).strip()
                    tm_r = str(row.get("recent_team", row.get("team", "")) or "")
                    pos_clean = normalize_guard_position(pos_raw, "", nm, tm_r)
                    lookup[key] = {
                        "headshot_url": str(row.get("headshot_url", "") or ""),
                        "team": tm_r,
                        "position": pos_clean,
                        "jersey_number": row.get("jersey_number", ""),
                        "college": str(row.get("college", "") or ""),
                    }
    return lookup


def get_player_headshot_and_meta(
    player_name: str,
    team_abbr: str,
    position: str,
    headshot_lookup: Dict[str, Dict[str, Any]],
) -> Dict[str, Any]:
    key = str(player_name or "").strip().lower()
    found = headshot_lookup.get(key, {})
    url = str(found.get("headshot_url", "") or "").strip()
    if not url or url.lower() in ("nan", "none") or not url.startswith("http"):
        url = "https://static.www.nfl.com/image/private/f_auto,q_auto/league/mdrlzgankqabpbx39c1g"
    pos_final = normalize_guard_position(
        position or found.get("position", "NFL"), "", player_name, team_abbr
    )
    return {
        "headshot_url": url,
        "team": team_abbr or found.get("team", "NFL"),
        "position": pos_final,
        "jersey_number": found.get("jersey_number", ""),
        "college": found.get("college", ""),
    }


def render_mismatch_headshot_html(
    player_name: str,
    team_abbr: str,
    position: str,
    headshot_lookup: Dict[str, Dict[str, Any]],
) -> str:
    meta = get_player_headshot_and_meta(
        player_name, team_abbr, position, headshot_lookup
    )
    hex_col = resolve_team_display_color(team_abbr)
    r, g, b = hex_to_rgb(hex_col)
    bg_grad = (
        f"linear-gradient(180deg, rgba(16,16,22,0.95) 0%, "
        f"rgba({r},{g},{b},0.18) 60%, rgba({r},{g},{b},0.42) 100%)"
    )
    img_url = meta["headshot_url"]
    return (
        f'<img src="{img_url}" class="mismatch-headshot-img" '
        f'style="background:{bg_grad};border-color:{hex_col}88;" '
        f'alt="{player_name}" onerror="this.style.display=\'none\'" />'
    )


def get_five_year_h2h_history(
    master_df: pd.DataFrame, away_team: str, home_team: str, max_season: int
) -> pd.DataFrame:
    """Returns a DataFrame formatted for render_five_year_h2h_visual."""
    if master_df.empty:
        return pd.DataFrame()
    min_season = int(max_season) - 5
    at_norm = normalize_team_code(away_team)
    ht_norm = normalize_team_code(home_team)
    sub = master_df[
        (pd.to_numeric(master_df["season"], errors="coerce") >= min_season)
        & (pd.to_numeric(master_df["season"], errors="coerce") <= int(max_season))
        & (
            ((master_df["away_team"] == at_norm) & (master_df["home_team"] == ht_norm))
            | ((master_df["away_team"] == ht_norm) & (master_df["home_team"] == at_norm))
        )
    ].copy()
    sub = sub.dropna(subset=["away_score", "home_score"])
    if sub.empty:
        return pd.DataFrame()

    sub = sub.sort_values(by=["season", "week"], ascending=[False, False]).head(8).copy()
    sub["away_score"] = pd.to_numeric(sub["away_score"], errors="coerce").fillna(0).astype(int)
    sub["home_score"] = pd.to_numeric(sub["home_score"], errors="coerce").fillna(0).astype(int)
    sub["Total Pts"] = sub["away_score"] + sub["home_score"]

    su_winners = []
    ats_results = []
    for _, r in sub.iterrows():
        g_aw = str(r["away_team"]).strip().upper()
        g_hm = str(r["home_team"]).strip().upper()
        a_sc = int(r["away_score"])
        h_sc = int(r["home_score"])
        if a_sc > h_sc:
            su_winners.append(g_aw)
        elif h_sc > a_sc:
            su_winners.append(g_hm)
        else:
            su_winners.append("TIE")

        h_sp = r.get("home_spread", np.nan)
        if pd.notna(h_sp):
            margin = (h_sc - a_sc) + float(h_sp)
            if margin > 0:
                ats_results.append(f"{g_hm} Covered ({float(h_sp):+.1f})")
            elif margin < 0:
                ats_results.append(f"{g_aw} Covered ({-float(h_sp):+.1f})")
            else:
                ats_results.append("Push")
        else:
            ats_results.append("N/A")

    sub["SU Winner"] = su_winners
    sub["ATS Result"] = ats_results
    return sub.reset_index(drop=True)


def prepare_matchup_player_prop_logs(
    pstats_df: pd.DataFrame, away_team: str, home_team: str, max_week: int
) -> pd.DataFrame:
    if pstats_df.empty:
        return pd.DataFrame()
    team_col = "team" if "team" in pstats_df.columns else "recent_team"
    if team_col not in pstats_df.columns:
        return pd.DataFrame()
    at_norm = normalize_team_code(away_team)
    ht_norm = normalize_team_code(home_team)
    sub = pstats_df[pstats_df[team_col].isin([at_norm, ht_norm])].copy()
    if "week" in sub.columns:
        w_filtered = sub[pd.to_numeric(sub["week"], errors="coerce") <= int(max_week)]
        if not w_filtered.empty:
            sub = w_filtered
    return normalize_dataframe_guard_positions(sub.reset_index(drop=True))


def aggregate_team_skill_usage(
    prop_logs: pd.DataFrame, team_abbr: str
) -> pd.DataFrame:
    if prop_logs.empty:
        return pd.DataFrame()
    team_col = "team" if "team" in prop_logs.columns else "recent_team"
    tm_norm = normalize_team_code(team_abbr)
    sub = prop_logs[prop_logs[team_col] == tm_norm].copy()
    if sub.empty:
        return pd.DataFrame()

    name_col = (
        "player_display_name"
        if "player_display_name" in sub.columns
        else "player_name"
    )
    for col in [
        "targets",
        "receptions",
        "receiving_yards",
        "receiving_tds",
        "carries",
        "rushing_yards",
        "rushing_tds",
        "passing_yards",
        "passing_tds",
    ]:
        if col not in sub.columns:
            sub[col] = 0.0
        sub[col] = pd.to_numeric(sub[col], errors="coerce").fillna(0.0)

    grp = (
        sub.groupby([name_col, "position"], as_index=False)
        .agg(
            games=("week", "nunique"),
            targets=("targets", "sum"),
            receptions=("receptions", "sum"),
            rec_yards=("receiving_yards", "sum"),
            rec_tds=("receiving_tds", "sum"),
            carries=("carries", "sum"),
            rush_yards=("rushing_yards", "sum"),
            rush_tds=("rushing_tds", "sum"),
            pass_yards=("passing_yards", "sum"),
            pass_tds=("passing_tds", "sum"),
        )
        .rename(columns={name_col: "Player", "position": "Pos"})
    )
    grp["Pos"] = grp.apply(
        lambda r: normalize_guard_position(r["Pos"], "", r["Player"], tm_norm), axis=1
    )
    tot_tgts = max(float(grp["targets"].sum()), 1.0)
    tot_car = max(float(grp["carries"].sum()), 1.0)
    grp["Target Share %"] = (grp["targets"] / tot_tgts * 100.0).round(1)
    grp["Rush Share %"] = (grp["carries"] / tot_car * 100.0).round(1)
    grp["Rec Yds/G"] = (grp["rec_yards"] / grp["games"].clip(lower=1)).round(1)
    grp["Rush Yds/G"] = (grp["rush_yards"] / grp["games"].clip(lower=1)).round(1)
    grp["Total TD"] = (grp["rec_tds"] + grp["rush_tds"]).astype(int)
    grp["Touches/G"] = (
        (grp["receptions"] + grp["carries"]) / grp["games"].clip(lower=1)
    ).round(1)
    return grp.sort_values(
        by=["Touches/G", "Rec Yds/G"], ascending=False
    ).reset_index(drop=True)


def build_top_player_picks(
    prop_logs: pd.DataFrame,
    away_team: str,
    home_team: str,
    away_eff: pd.Series,
    home_eff: pd.Series,
    headshot_lookup: Dict[str, Dict[str, Any]],
) -> List[Dict[str, Any]]:
    if prop_logs.empty:
        return []
    team_col = "team" if "team" in prop_logs.columns else "recent_team"
    name_col = (
        "player_display_name"
        if "player_display_name" in prop_logs.columns
        else "player_name"
    )
    at_norm = normalize_team_code(away_team)
    ht_norm = normalize_team_code(home_team)
    odds_val = int(st.session_state.get("default_odds_american", -110))
    kelly_mult = float(st.session_state.get("kelly_fraction_mult", 0.25))

    picks: List[Dict[str, Any]] = []
    for (p_name, pos, tm), grp in prop_logs.groupby([name_col, "position", team_col]):
        if len(grp) < 2:
            continue
        grp = grp.sort_values("week")
        opp_tm = ht_norm if tm == at_norm else at_norm
        opp_eff = home_eff if tm == at_norm else away_eff

        if pos == "QB":
            stat_col = "passing_yards"
            market_lbl = "Pass Yds"
            def_rank = int(opp_eff.get("pass_def_rank", 16))
        elif pos == "RB":
            stat_col = "rushing_yards"
            market_lbl = "Rush Yds"
            def_rank = int(opp_eff.get("rush_def_rank", 16))
        elif pos in ("WR", "TE"):
            stat_col = "receiving_yards"
            market_lbl = "Rec Yds"
            def_rank = int(opp_eff.get("pass_def_rank", 16))
        else:
            continue

        if stat_col not in grp.columns:
            continue
        vals = pd.to_numeric(grp[stat_col], errors="coerce").fillna(0.0)
        season_avg = float(vals.mean())
        if (pos == "QB" and season_avg < 130) or (pos != "QB" and season_avg < 22):
            continue

        l3_avg = float(vals.tail(3).mean())
        line_val = float(np.floor(season_avg * 0.92) + 0.5)
        hits = int((vals > line_val).sum())
        gp = len(vals)
        hit_rate = hits / max(gp, 1)

        def_adj = (def_rank - 16.5) * (0.85 if pos == "QB" else 0.35)
        proj = float(np.round(0.55 * l3_avg + 0.45 * season_avg + def_adj, 1))
        diff = proj - line_val
        side = "OVER" if diff >= 0 else "UNDER"
        win_prob = float(
            np.clip(
                0.52 + abs(diff) / max(line_val, 15.0) * 0.35 + (hit_rate - 0.5) * 0.18,
                0.51,
                0.76,
            )
        )
        ev_pct, kelly_u = compute_ev_and_kelly(win_prob, odds_val, kelly_mult)
        tier_lbl, tier_cls = get_confidence_tier(ev_pct, win_prob)
        meta = get_player_headshot_and_meta(str(p_name), str(tm), str(pos), headshot_lookup)

        picks.append(
            {
                "player": str(p_name),
                "team": str(tm),
                "opp": opp_tm,
                "pos": str(pos),
                "market": market_lbl,
                "line": line_val,
                "proj": proj,
                "edge_score": round(abs(diff), 1),
                "season_avg": round(season_avg, 1),
                "l3_avg": round(l3_avg, 1),
                "hit_str": f"{hits}/{gp} ({hit_rate*100:.0f}%)",
                "side": side,
                "def_rank": def_rank,
                "win_prob": win_prob,
                "ev_pct": ev_pct,
                "kelly_u": kelly_u,
                "tier_lbl": tier_lbl,
                "tier_cls": tier_cls,
                "headshot_url": meta["headshot_url"],
            }
        )

    picks.sort(key=lambda x: x["ev_pct"], reverse=True)
    return picks[:8]


def build_cb_wr_matchup_battles(
    prop_logs: pd.DataFrame,
    rosters_df: pd.DataFrame,
    away_team: str,
    home_team: str,
    away_eff: pd.Series,
    home_eff: pd.Series,
    headshot_lookup: Dict[str, Dict[str, Any]],
) -> List[Dict[str, Any]]:
    battles: List[Dict[str, Any]] = []
    if prop_logs.empty:
        return battles

    team_col = "team" if "team" in prop_logs.columns else "recent_team"
    name_col = (
        "player_display_name"
        if "player_display_name" in prop_logs.columns
        else "player_name"
    )
    at_norm = normalize_team_code(away_team)
    ht_norm = normalize_team_code(home_team)

    for off_team, def_team, def_eff in [
        (at_norm, ht_norm, home_eff),
        (ht_norm, at_norm, away_eff),
    ]:
        wrs = prop_logs[
            (prop_logs[team_col] == off_team)
            & (prop_logs["position"].isin(["WR", "TE"]))
        ].copy()
        if wrs.empty:
            continue
        wr_agg = (
            wrs.groupby([name_col, "position"], as_index=False)
            .agg(
                gp=("week", "nunique"),
                tgts=("targets", "sum"),
                rec=("receptions", "sum"),
                yds=("receiving_yards", "sum"),
                tds=("receiving_tds", "sum"),
            )
            .sort_values(by=["yds", "tgts"], ascending=False)
            .head(3)
        )

        cbs: List[str] = []
        if not rosters_df.empty and "team" in rosters_df.columns:
            r_name = "full_name" if "full_name" in rosters_df.columns else "player_name"
            cb_rows = rosters_df[
                (rosters_df["team"] == def_team)
                & (rosters_df["position"].isin(["CB", "DB", "SAF", "S"]))
            ]
            if not cb_rows.empty and r_name in cb_rows.columns:
                cbs = cb_rows[r_name].dropna().astype(str).unique().tolist()[:3]
        while len(cbs) < 3:
            cbs.append(f"{def_team} CB{len(cbs)+1}")

        pass_def_rk = int(def_eff.get("pass_def_rank", 16))
        for idx, (_, wr_row) in enumerate(wr_agg.iterrows()):
            wr_name = str(wr_row[name_col])
            wr_pos = str(wr_row["position"])
            gp = max(int(wr_row["gp"]), 1)
            ypg = float(wr_row["yds"]) / gp
            tpg = float(wr_row["tgts"]) / gp
            cb_name = cbs[min(idx, len(cbs) - 1)]
            edge_score = float(np.round((ypg - 48.0) * 0.35 + (pass_def_rk - 16.5) * 0.95, 1))
            if edge_score >= 4.0:
                adv_lbl = f"{off_team} WR Edge (+{edge_score:.1f})"
                adv_cls = "badge-hot"
            elif edge_score <= -4.0:
                adv_lbl = f"{def_team} Coverage Edge ({edge_score:.1f})"
                adv_cls = "badge-cold"
            else:
                adv_lbl = "Neutral Matchup"
                adv_cls = "badge-mid"

            battles.append(
                {
                    "off_team": off_team,
                    "def_team": def_team,
                    "slot_label": f"WR{idx+1} vs CB{idx+1}" if wr_pos == "WR" else "TE1 vs Nickel/S",
                    "wr_name": wr_name,
                    "wr_pos": wr_pos,
                    "wr_ypg": round(ypg, 1),
                    "wr_tpg": round(tpg, 1),
                    "cb_name": cb_name,
                    "pass_def_rank": pass_def_rk,
                    "edge_score": edge_score,
                    "adv_lbl": adv_lbl,
                    "adv_cls": adv_cls,
                }
            )
    return battles


def classify_unit_side(pos: str) -> str:
    p = str(pos or "").upper().strip()
    if p in ("QB", "RB", "FB", "WR", "TE", "OL", "OT", "LT", "RT", "LG", "RG", "G", "C", "T"):
        return "Offense"
    if p in ("K", "P", "LS"):
        return "Special Teams"
    return "Defense"


def build_roster_usage_table(
    snaps_df: pd.DataFrame,
    pstats_df: pd.DataFrame,
    inj_df: pd.DataFrame,
    team_abbr: str,
    max_week: int,
) -> pd.DataFrame:
    if snaps_df.empty:
        return pd.DataFrame()
    tm_norm = normalize_team_code(team_abbr)
    sub = snaps_df[snaps_df["team"] == tm_norm].copy()
    if "week" in sub.columns:
        w_sub = sub[pd.to_numeric(sub["week"], errors="coerce") <= int(max_week)]
        if not w_sub.empty:
            sub = w_sub
    if sub.empty:
        return pd.DataFrame()

    p_col = "player" if "player" in sub.columns else "player_name"
    for c in ["offense_snaps", "offense_pct", "defense_snaps", "defense_pct"]:
        if c not in sub.columns:
            sub[c] = 0.0
        sub[c] = pd.to_numeric(sub[c], errors="coerce").fillna(0.0)

    sub["total_snaps"] = sub["offense_snaps"] + sub["defense_snaps"]
    sub["snap_pct"] = np.where(
        sub["offense_pct"] >= sub["defense_pct"],
        sub["offense_pct"],
        sub["defense_pct"],
    )
    if sub["snap_pct"].max() <= 1.05:
        sub["snap_pct"] = sub["snap_pct"] * 100.0

    agg = (
        sub.groupby([p_col, "position"], as_index=False)
        .agg(
            GP=("week", "nunique"),
            Snaps=("total_snaps", "sum"),
            Snap_Pct=("snap_pct", "mean"),
        )
        .rename(columns={p_col: "Player", "position": "Pos"})
    )
    agg["Pos"] = agg.apply(
        lambda r: normalize_guard_position(r["Pos"], "", r["Player"], tm_norm), axis=1
    )
    agg["Side"] = agg["Pos"].apply(classify_unit_side)
    agg["Snap %"] = agg["Snap_Pct"].round(1)
    agg["Snaps"] = agg["Snaps"].astype(int)
    return (
        agg[["Player", "Pos", "Side", "GP", "Snaps", "Snap %"]]
        .sort_values(by=["Snap %", "Snaps"], ascending=False)
        .reset_index(drop=True)
    )


def build_injury_impact_report(
    inj_df: pd.DataFrame,
    snaps_df: pd.DataFrame,
    rosters_df: pd.DataFrame,
    team_abbr: str,
    week_num: int,
    headshot_lookup: Dict[str, Dict[str, Any]],
) -> List[Dict[str, Any]]:
    if inj_df.empty or "team" not in inj_df.columns:
        return []
    tm_norm = normalize_team_code(team_abbr)
    sub = inj_df[
        (inj_df["team"] == tm_norm) & (pd.to_numeric(inj_df["week"], errors="coerce") == int(week_num))
    ].copy()
    if sub.empty:
        avail_weeks = pd.to_numeric(inj_df[inj_df["team"] == tm_norm]["week"], errors="coerce").dropna()
        if not avail_weeks.empty:
            target_wk = int(avail_weeks[avail_weeks <= int(week_num)].max()) if (avail_weeks <= int(week_num)).any() else int(avail_weeks.max())
            sub = inj_df[(inj_df["team"] == tm_norm) & (pd.to_numeric(inj_df["week"], errors="coerce") == target_wk)].copy()
    if sub.empty:
        return []

    name_col = (
        "full_name"
        if "full_name" in sub.columns
        else ("player_name" if "player_name" in sub.columns else "player")
    )

    snap_map: Dict[str, float] = {}
    if not snaps_df.empty and "team" in snaps_df.columns:
        s_sub = snaps_df[snaps_df["team"] == tm_norm].copy()
        if not s_sub.empty:
            sp_col = "player" if "player" in s_sub.columns else "player_name"
            for c in ["offense_pct", "defense_pct"]:
                if c not in s_sub.columns:
                    s_sub[c] = 0.0
                s_sub[c] = pd.to_numeric(s_sub[c], errors="coerce").fillna(0.0)
            s_sub["pct"] = np.maximum(s_sub["offense_pct"], s_sub["defense_pct"])
            if s_sub["pct"].max() <= 1.05:
                s_sub["pct"] = s_sub["pct"] * 100.0
            for nm, grp in s_sub.groupby(sp_col):
                snap_map[str(nm).strip().lower()] = float(grp["pct"].mean())

    items: List[Dict[str, Any]] = []
    seen_players = set()
    for _, row in sub.iterrows():
        p_name = str(row.get(name_col, "")).strip()
        if not p_name or p_name.lower() in seen_players:
            continue
        seen_players.add(p_name.lower())

        pos_raw = str(row.get("position", "NFL")).strip()
        pos = normalize_guard_position(pos_raw, "", p_name, tm_norm)
        rep_status = str(row.get("report_status", row.get("game_status", "")) or "").strip()
        prac_status = str(row.get("practice_status", "") or "").strip()
        prim_inj = extract_combined_injury_name(row)
        if not prim_inj or prim_inj.lower() in ("nan", "none", "undisclosed"):
            prim_inj = str(row.get("report_primary_injury", row.get("primary_injury", "")) or "Undisclosed / Rest").strip()

        snap_pct = round(snap_map.get(p_name.lower(), 35.0), 1)
        wed_p, thu_p, fri_p, main_tag, main_cls = derive_daily_practice_progression(
            rep_status, prac_status, p_name, int(week_num)
        )
        strip_html = render_wed_thu_fri_practice_strip_html(
            rep_status, prac_status, p_name, int(week_num)
        )
        meta = get_player_headshot_and_meta(p_name, tm_norm, pos, headshot_lookup)

        severity_order = {
            "OUT": 0,
            "IR": 1,
            "DOUBTFUL": 2,
            "QUESTIONABLE": 3,
            "CLEARED": 4,
        }.get(main_tag, 3)

        items.append(
            {
                "player": p_name,
                "pos": pos,
                "side": classify_unit_side(pos),
                "injury": prim_inj,
                "report_status": rep_status,
                "practice_status": prac_status,
                "wed": wed_p,
                "thu": thu_p,
                "fri": fri_p,
                "main_tag": main_tag,
                "main_cls": main_cls,
                "strip_html": strip_html,
                "snap_pct": snap_pct,
                "headshot_url": meta["headshot_url"],
                "severity_order": severity_order,
            }
        )

    items.sort(key=lambda x: (x["severity_order"], -x["snap_pct"]))
    return items


def compute_team_injury_penalties(
    inj_items: List[Dict[str, Any]]
) -> tuple[float, float]:
    """Computes offensive and defensive EPA/play penalties from active team injury report items."""
    off_pen = 0.0
    def_pen = 0.0
    for item in inj_items:
        tag = item.get("main_tag", "CLEARED")
        if tag == "CLEARED":
            continue
        mult = 1.0 if tag in ("OUT", "IR") else (0.75 if tag == "DOUBTFUL" else 0.35)
        snap_weight = float(item.get("snap_pct", 30.0)) / 100.0
        pos = str(item.get("pos", "")).upper()
        pos_w = 0.045 if pos == "QB" else (0.018 if pos in ("LT", "RT", "WR", "CB", "EDGE", "DE") else 0.012)
        if item.get("side") == "Offense":
            off_pen += mult * snap_weight * pos_w
        elif item.get("side") == "Defense":
            def_pen += mult * snap_weight * pos_w
    return round(min(off_pen, 0.085), 4), round(min(def_pen, 0.085), 4)


def get_player_season_injury_history(
    inj_df: pd.DataFrame,
    snaps_df: pd.DataFrame,
    player_name: str,
    team_abbr: str,
) -> List[Dict[str, Any]]:
    if inj_df.empty:
        return []
    name_col = (
        "full_name"
        if "full_name" in inj_df.columns
        else ("player_name" if "player_name" in inj_df.columns else "player")
    )
    sub = inj_df[
        inj_df[name_col].astype(str).str.strip().str.lower() == player_name.strip().lower()
    ].copy()
    if sub.empty:
        return []

    snap_by_wk: Dict[int, Tuple[int, float]] = {}
    if not snaps_df.empty:
        sp_col = "player" if "player" in snaps_df.columns else "player_name"
        s_sub = snaps_df[
            snaps_df[sp_col].astype(str).str.strip().str.lower()
            == player_name.strip().lower()
        ].copy()
        for _, srow in s_sub.iterrows():
            wk = int(pd.to_numeric(srow.get("week", 0), errors="coerce") or 0)
            osn = float(pd.to_numeric(srow.get("offense_snaps", 0), errors="coerce") or 0)
            dsn = float(pd.to_numeric(srow.get("defense_snaps", 0), errors="coerce") or 0)
            opct = float(pd.to_numeric(srow.get("offense_pct", 0), errors="coerce") or 0)
            dpct = float(pd.to_numeric(srow.get("defense_pct", 0), errors="coerce") or 0)
            pct = max(opct, dpct)
            if pct <= 1.05:
                pct *= 100.0
            snap_by_wk[wk] = (int(osn + dsn), round(pct, 1))

    sub = sub.sort_values("week", ascending=False)
    records: List[Dict[str, Any]] = []
    for _, row in sub.iterrows():
        wk = int(pd.to_numeric(row.get("week", 1), errors="coerce") or 1)
        rep_st = str(row.get("report_status", row.get("game_status", "")) or "").strip()
        prac_st = str(row.get("practice_status", "") or "").strip()
        inj_body = extract_combined_injury_name(row)
        if not inj_body or inj_body.lower() in ("nan", "none"):
            inj_body = "Rest / Coach Decision"

        wed_p, thu_p, fri_p, main_tag, main_cls = derive_daily_practice_progression(
            rep_st, prac_st, player_name, wk
        )
        strip_html = render_wed_thu_fri_practice_strip_html(
            rep_st, prac_st, player_name, wk
        )
        snaps_cnt, snap_pct = snap_by_wk.get(wk, (0, 0.0))
        if snaps_cnt > 0:
            snaps_str = f"{snaps_cnt} Snaps ({snap_pct:.0f}%)"
            outcome_str = "Played"
        elif main_tag in ("OUT", "IR", "DOUBTFUL"):
            snaps_str = "0 Snaps (DNP)"
            outcome_str = "Inactive / Missed"
        else:
            snaps_str = "Active / Pending"
            outcome_str = "Active"

        records.append(
            {
                "week": wk,
                "injury": inj_body,
                "wed": wed_p,
                "thu": thu_p,
                "fri": fri_p,
                "main_tag": main_tag,
                "main_cls": main_cls,
                "strip_html": strip_html,
                "snaps_str": snaps_str,
                "outcome_str": outcome_str,
            }
        )
    return records


def build_slate_best_bets_leaderboard(
    sched_df: pd.DataFrame, eff_df: pd.DataFrame
) -> pd.DataFrame:
    if sched_df.empty or eff_df.empty:
        return pd.DataFrame()
    eff_map = {str(r["team"]): r for _, r in eff_df.iterrows() if "team" in r}
    odds_val = int(st.session_state.get("default_odds_american", -110))
    kelly_mult = float(st.session_state.get("kelly_fraction_mult", 0.25))
    rows = []
    for _, g in sched_df.iterrows():
        aw = normalize_team_code(str(g.get("away_team", "")))
        hm = normalize_team_code(str(g.get("home_team", "")))
        wk = int(pd.to_numeric(g.get("week", 1), errors="coerce") or 1)
        if aw not in eff_map or hm not in eff_map:
            continue
        mod = compute_model_fair_line_and_totals(
            a_eff=eff_map[aw],
            h_eff=eff_map[hm],
            away_off_pen=0.0,
            away_def_pen=0.0,
            home_off_pen=0.0,
            home_def_pen=0.0,
            away_tm=aw,
            home_tm=hm,
            market_home_spread=g.get("home_spread", np.nan),
            market_total=g.get("total_line", np.nan),
            rest_edge_home=float(g.get("rest_edge_home", 0.0) or 0.0),
            roof_str=str(g.get("roof", "Outdoors") or "Outdoors"),
        )
        ev_sp, kelly_sp = compute_ev_and_kelly(mod["spread_cover_prob"], odds_val, kelly_mult)
        tier_lbl, _ = get_confidence_tier(ev_sp, mod["spread_cover_prob"])
        rows.append(
            {
                "Week": wk,
                "Matchup": f"{aw} @ {hm}",
                "Market": "Spread",
                "Best Pick": mod["backed_spread_line_str"],
                "Model Fair Line": mod["fair_spread_str"],
                "Edge": f"{mod['spread_edge_pts']:.1f} pts",
                "Win Prob": f"{mod['spread_cover_prob']*100:.1f}%",
                "EV %": ev_sp,
                "Kelly": f"{kelly_sp:.2f}u",
                "Tier": tier_lbl,
            }
        )
    df_out = pd.DataFrame(rows)
    if not df_out.empty:
        df_out = df_out.sort_values(by="EV %", ascending=False).reset_index(drop=True)
    return df_out


def run_season_backtest(
    sched_df: pd.DataFrame, eff_df: pd.DataFrame
) -> Dict[str, Any]:
    if sched_df.empty or eff_df.empty:
        return {"wins": 0, "losses": 0, "win_pct": 0.0, "roi": 0.0, "units": 0.0, "df": pd.DataFrame()}
    completed = sched_df.dropna(subset=["away_score", "home_score"]).copy()
    if completed.empty:
        return {"wins": 0, "losses": 0, "win_pct": 0.0, "roi": 0.0, "units": 0.0, "df": pd.DataFrame()}

    eff_map = {str(r["team"]): r for _, r in eff_df.iterrows()}
    wins = 0
    losses = 0
    units = 0.0
    log_rows = []
    for _, g in completed.iterrows():
        aw = normalize_team_code(str(g.get("away_team", "")))
        hm = normalize_team_code(str(g.get("home_team", "")))
        if aw not in eff_map or hm not in eff_map:
            continue
        mod = compute_model_fair_line_and_totals(
            a_eff=eff_map[aw],
            h_eff=eff_map[hm],
            away_off_pen=0.0,
            away_def_pen=0.0,
            home_off_pen=0.0,
            home_def_pen=0.0,
            away_tm=aw,
            home_tm=hm,
            market_home_spread=g.get("home_spread", np.nan),
            market_total=g.get("total_line", np.nan),
            rest_edge_home=float(g.get("rest_edge_home", 0.0) or 0.0),
            roof_str=str(g.get("roof", "Outdoors") or "Outdoors"),
        )
        if mod["spread_edge_pts"] < 1.5 or pd.isna(g.get("home_spread", np.nan)):
            continue
        a_sc = float(g.get("away_score", 0))
        h_sc = float(g.get("home_score", 0))
        actual_margin = h_sc - a_sc
        home_line = float(g.get("home_spread", 0.0))
        covered_home = (actual_margin + home_line) > 0
        pick_home = mod["backed_spread_team"] == hm
        won = (pick_home and covered_home) or (not pick_home and not covered_home)
        if won:
            wins += 1
            units += 0.91
        else:
            losses += 1
            units -= 1.0
        log_rows.append(
            {
                "Week": int(pd.to_numeric(g.get("week", 1), errors="coerce") or 1),
                "Game": f"{aw} @ {hm}",
                "Score": f"{int(a_sc)}-{int(h_sc)}",
                "Model Pick": mod["backed_spread_line_str"],
                "Edge": f"{mod['spread_edge_pts']:.1f} pts",
                "Result": "WIN" if won else "LOSS",
                "Net Units": "+0.91u" if won else "-1.00u",
            }
        )
    tot = max(wins + losses, 1)
    roi = round(units / tot * 100.0, 1)
    return {
        "wins": wins,
        "losses": losses,
        "win_pct": round(wins / tot * 100.0, 1),
        "units": round(units, 2),
        "roi": roi,
        "df": pd.DataFrame(log_rows),
    }


# -----------------------------------------------------------------------------
# PLAYER DOSSIER & PROP EXPLORER MODALS
# -----------------------------------------------------------------------------
def render_player_popup_contents(
    player_name: str,
    team_abbr: str,
    opp_team: str,
    season: int,
    week_num: int,
    pstats_df: pd.DataFrame,
    snaps_df: pd.DataFrame,
    inj_df: pd.DataFrame,
    eff_df: pd.DataFrame,
    headshot_lookup: Dict[str, Dict[str, Any]],
) -> None:
    tm_norm = normalize_team_code(team_abbr)
    opp_norm = normalize_team_code(opp_team)
    meta = get_player_headshot_and_meta(
        player_name, tm_norm, "", headshot_lookup
    )
    pos = normalize_guard_position(meta["position"], "", player_name, tm_norm)
    side = classify_unit_side(pos)
    jersey = meta.get("jersey_number", "")
    college = meta.get("college", "") or "NFL"
    jersey_str = f"#{int(float(jersey))} · " if str(jersey).replace(".", "").isdigit() else ""

    inj_hist = get_player_season_injury_history(
        inj_df, snaps_df, player_name, tm_norm
    )
    latest_inj = inj_hist[0] if inj_hist else None

    if latest_inj:
        status_strip_html = (
            f'<div style="margin-top:8px;">{latest_inj["strip_html"]}</div>'
        )
    else:
        status_strip_html = (
            '<div style="margin-top:8px;">'
            '<span class="main-game-status-tag main-status-cleared">'
            'ACTIVE / CLEARED</span></div>'
        )

    st.markdown(
        f"""
        <div class="player-modal-banner">
            <div class="player-headshot-wrap">
                <img src="{meta['headshot_url']}" class="player-headshot-img" alt="{player_name}" onerror="this.style.display='none'" />
            </div>
            <div style="flex:1;min-width:220px;">
                <div style="display:flex;align-items:center;gap:8px;flex-wrap:wrap;">
                    <span style="font-family:'Plus Jakarta Sans',sans-serif;font-size:1.35rem;font-weight:900;color:#FFFFFF;text-transform:uppercase;">
                        {player_name}
                    </span>
                    {render_team_pill(tm_norm)}
                    <span class="badge-mid">{pos}</span>
                    <span class="badge-sage">{side}</span>
                </div>
                <div style="font-size:0.80rem;color:#A1A1AA;margin-top:3px;font-weight:600;">
                    {jersey_str}{season} Season · vs {opp_norm} · {college}
                </div>
                {status_strip_html}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    name_col = (
        "player_display_name"
        if "player_display_name" in pstats_df.columns
        else "player_name"
    )
    p_logs = pd.DataFrame()
    if not pstats_df.empty and name_col in pstats_df.columns:
        p_all = pstats_df[
            pstats_df[name_col].astype(str).str.strip().str.lower() == player_name.strip().lower()
        ].copy()
        if not p_all.empty:
            w_sub = p_all[pd.to_numeric(p_all["week"], errors="coerce") <= int(week_num)]
            p_logs = (w_sub if not w_sub.empty else p_all).sort_values("week")

    gp = len(p_logs) if not p_logs.empty else 0
    total_snaps = 0
    avg_snap_pct = 0.0
    if not snaps_df.empty:
        sp_col = "player" if "player" in snaps_df.columns else "player_name"
        s_all = snaps_df[
            snaps_df[sp_col].astype(str).str.strip().str.lower() == player_name.strip().lower()
        ].copy()
        if not s_all.empty:
            s_logs = s_all[pd.to_numeric(s_all["week"], errors="coerce") <= int(week_num)]
            if s_logs.empty:
                s_logs = s_all
            osn = _safe_num_series(s_logs, "offense_snaps", 0.0).sum()
            dsn = _safe_num_series(s_logs, "defense_snaps", 0.0).sum()
            total_snaps = int(osn + dsn)
            opct = _safe_num_series(s_logs, "offense_pct", 0.0)
            dpct = _safe_num_series(s_logs, "defense_pct", 0.0)
            pct_series = np.maximum(opct, dpct)
            if pct_series.max() <= 1.05:
                pct_series = pct_series * 100.0
            avg_snap_pct = float(pct_series.mean())

    tot_yds = 0
    tot_tds = 0
    tot_touches = 0
    if not p_logs.empty:
        ry = _safe_num_series(p_logs, "rushing_yards", 0.0).sum()
        recy = _safe_num_series(p_logs, "receiving_yards", 0.0).sum()
        py = _safe_num_series(p_logs, "passing_yards", 0.0).sum()
        rtd = _safe_num_series(p_logs, "rushing_tds", 0.0).sum()
        rectd = _safe_num_series(p_logs, "receiving_tds", 0.0).sum()
        ptd = _safe_num_series(p_logs, "passing_tds", 0.0).sum()
        car = _safe_num_series(p_logs, "carries", 0.0).sum()
        rec = _safe_num_series(p_logs, "receptions", 0.0).sum()
        tot_yds = int(py if pos == "QB" else (ry + recy))
        tot_tds = int(ptd if pos == "QB" else (rtd + rectd))
        tot_touches = int(car + rec)

    mc1, mc2, mc3, mc4 = st.columns(4)
    mc1.metric("Season Games Active", f"{gp} GP", f"{total_snaps} Snaps")
    mc2.metric("Snap Share", f"{avg_snap_pct:.1f}%", side)
    mc3.metric("Total Touches", f"{tot_touches}", f"{tot_touches/max(gp,1):.1f}/G")
    mc4.metric("Total Production", f"{tot_yds} Yds", f"{tot_tds} TD")

    tab_props, tab_logs, tab_inj_hist = st.tabs(["Props", "Game Logs", "Injuries"])

    with tab_props:
        if p_logs.empty:
            st.info("No weekly prop logs recorded yet for this player in the selected season.")
        else:
            cov_df = load_team_coverage_and_shell_splits(season, eff_df)
            market_options = {
                "Rushing Yards": "rushing_yards",
                "Receiving Yards": "receiving_yards",
                "Receptions": "receptions",
                "Carries": "carries",
                "Passing Yards": "passing_yards",
            }
            default_idx = 0 if pos == "RB" else (4 if pos == "QB" else 1)
            c_mkt, c_line, c_flt = st.columns([1.2, 1.3, 1.3])
            with c_mkt:
                sel_mkt_label = st.selectbox(
                    "Prop Market",
                    list(market_options.keys()),
                    index=default_idx,
                    key=f"dlg_mkt_{player_name}",
                )
            stat_col = market_options[sel_mkt_label]
            is_rush_prop = stat_col in ("rushing_yards", "carries")
            vals_all = _safe_num_series(p_logs, stat_col, 0.0)
            season_avg = float(vals_all.mean()) if len(vals_all) else 25.0
            default_line = float(np.floor(max(season_avg * 0.92, 0.5)) + 0.5)

            with c_line:
                user_line = st.slider(
                    f"Line ({sel_mkt_label})",
                    min_value=0.5,
                    max_value=float(max(vals_all.max() * 1.45, 45.5)),
                    value=default_line,
                    step=1.0,
                    key=f"dlg_line_{player_name}_{stat_col}",
                )
            with c_flt:
                opp_filter_mode = st.radio(
                    "Opponent Filter",
                    ["All Past Games", f"Similar to {opp_norm} Def"],
                    horizontal=True,
                    key=f"dlg_opp_flt_{player_name}_{stat_col}",
                )

            p_logs_chart = p_logs.copy()
            opp_col = (
                "opponent_team"
                if "opponent_team" in p_logs_chart.columns
                else ("opp" if "opp" in p_logs_chart.columns else None)
            )
            if not opp_col:
                p_logs_chart["opponent_team"] = "OPP"
                opp_col = "opponent_team"

            sim_scores = []
            sim_tags = []
            for _, r_log in p_logs_chart.iterrows():
                past_opp = str(r_log.get(opp_col, "OPP"))
                sc, tg = compute_defense_similarity(
                    opp_norm, past_opp, cov_df, is_rush_prop=is_rush_prop
                )
                sim_scores.append(sc)
                sim_tags.append(tg)
            p_logs_chart["sim_score"] = sim_scores
            p_logs_chart["sim_tag"] = sim_tags

            if opp_filter_mode.startswith("Similar"):
                filtered = p_logs_chart[p_logs_chart["sim_score"] >= 68].copy()
                if filtered.empty:
                    filtered = (
                        p_logs_chart.sort_values("sim_score", ascending=False)
                        .head(3)
                        .sort_values("week")
                    )
                p_logs_chart = filtered

            vals = _safe_num_series(p_logs_chart, stat_col, 0.0)
            hits = int((vals > user_line).sum())
            tot_g = max(len(vals), 1)
            hit_pct = hits / tot_g * 100.0
            l3_avg = float(vals.tail(3).mean()) if len(vals) else 0.0

            opp_cov_row = (
                cov_df[cov_df["team"] == opp_norm].iloc[0]
                if not cov_df.empty and (cov_df["team"] == opp_norm).any()
                else None
            )
            def_rk = (
                int(
                    opp_cov_row["rush_def_rank"]
                    if is_rush_prop
                    else opp_cov_row["pass_def_rank"]
                )
                if opp_cov_row is not None
                else 16
            )

            pm1, pm2, pm3 = st.columns(3)
            pm1.metric(
                f"Hit Rate (vs {user_line:.1f})",
                f"{hit_pct:.1f}% ({hits}/{tot_g})",
                "Over Trend" if hit_pct >= 55 else "Under Trend",
            )
            pm2.metric(
                "L3 Form vs Season",
                f"{l3_avg:.1f} L3",
                f"{l3_avg - season_avg:+.1f} vs {season_avg:.1f} Avg",
            )
            pm3.metric(
                f"vs {opp_norm} Defense",
                f"Rank #{def_rk}",
                "Favorable" if def_rk >= 20 else ("Tough" if def_rk <= 10 else "Neutral"),
            )

            side_pick = "OVER" if l3_avg >= user_line else "UNDER"
            win_p = float(
                np.clip(
                    0.53 + abs(l3_avg - user_line) / max(user_line, 12.0) * 0.25,
                    0.51,
                    0.74,
                )
            )
            odds_val = int(st.session_state.get("default_odds_american", -110))
            kelly_mult = float(st.session_state.get("kelly_fraction_mult", 0.25))
            ev_p, kelly_p = compute_ev_and_kelly(win_p, odds_val, kelly_mult)
            render_compact_bet_action_row(
                key_prefix=f"dlg_prop_{player_name}_{stat_col}",
                season=int(season),
                week=int(week_num),
                matchup=f"{tm_norm} vs {opp_norm}",
                category=f"Player Prop ({sel_mkt_label})",
                selection=f"{player_name} {side_pick} {user_line:.1f} {sel_mkt_label}",
                market_line=f"{user_line:.1f}",
                model_proj=f"L3 {l3_avg:.1f}",
                american_odds=odds_val,
                edge_score=round(abs(l3_avg - user_line), 1),
                ev_pct=ev_p,
                kelly_units=kelly_p,
                team_abbr=tm_norm,
                button_text_override=f"{side_pick} {user_line:.1f} {sel_mkt_label}",
            )

            x_labels = [
                f"Wk {int(r['week'])} vs {r[opp_col]}"
                for _, r in p_logs_chart.iterrows()
            ]
            bar_colors = [
                "#15803D" if v > user_line else "#B91C1C" for v in vals
            ]
            cum_avg = vals.expanding().mean()

            fig = go.Figure()
            fig.add_trace(
                go.Bar(
                    x=x_labels,
                    y=vals,
                    marker_color=bar_colors,
                    text=[f"{v:.0f}" for v in vals],
                    textposition="outside",
                    name=sel_mkt_label,
                    customdata=list(
                        zip(
                            p_logs_chart[opp_col].astype(str),
                            p_logs_chart["sim_score"],
                            p_logs_chart["sim_tag"],
                        )
                    ),
                    hovertemplate=(
                        "<b>%{x}</b><br>"
                        f"{sel_mkt_label}: <b>%{{y}}</b><br>"
                        f"Similarity to {opp_norm}: <b>%{{customdata[1]}}%</b> (%{{customdata[2]}})"
                        "<extra></extra>"
                    ),
                )
            )
            fig.add_trace(
                go.Scatter(
                    x=x_labels,
                    y=cum_avg,
                    mode="lines+markers",
                    name="Cumulative Avg",
                    line=dict(color="#3B82F6", width=2, dash="dot"),
                )
            )
            fig.add_hline(
                y=user_line,
                line_dash="dash",
                line_color="#F59E0B",
                annotation_text=f"Line: {user_line:.1f} ({hit_pct:.0f}% Hit)",
                annotation_position="top left",
            )
            fig.update_layout(
                height=290,
                margin=dict(l=16, r=16, t=28, b=24),
                paper_bgcolor="#15151B",
                plot_bgcolor="#15151B",
                font=dict(color="#FAFAFA", family="Inter, sans-serif"),
                dragmode=False,
                xaxis=dict(fixedrange=True, title="Week & Opponent (Click a bar to compare defense)"),
                yaxis=dict(fixedrange=True, title=sel_mkt_label),
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            )

            chart_event = st.plotly_chart(
                fig,
                use_container_width=True,
                key=f"locked_prop_chart_{player_name}_{stat_col}",
                on_select="rerun",
                selection_mode="points",
                config={
                    "displayModeBar": False,
                    "scrollZoom": False,
                    "doubleClick": False,
                },
            )

            past_opps_unique = (
                p_logs_chart[opp_col].dropna().astype(str).unique().tolist()
            )
            clicked_opp = None
            if (
                chart_event
                and hasattr(chart_event, "selection")
                and chart_event.selection
                and chart_event.selection.get("points")
            ):
                pt_idx = chart_event.selection["points"][0].get("point_index", 0)
                if 0 <= pt_idx < len(p_logs_chart):
                    clicked_opp = str(p_logs_chart.iloc[pt_idx][opp_col])

            if past_opps_unique and opp_cov_row is not None:
                default_cmp_idx = (
                    past_opps_unique.index(clicked_opp)
                    if clicked_opp in past_opps_unique
                    else len(past_opps_unique) - 1
                )
                sel_cmp_opp = st.selectbox(
                    f"Compare Past Opponent Defense vs Upcoming {opp_norm} Defense (or click any bar above)",
                    past_opps_unique,
                    index=default_cmp_idx,
                    key=f"cmp_opp_sel_{player_name}_{stat_col}",
                )
                cmp_rows = cov_df[cov_df["team"] == normalize_team_code(sel_cmp_opp)]
                if not cmp_rows.empty:
                    c_row = cmp_rows.iloc[0]
                    sim_sc, sim_tg = compute_defense_similarity(
                        opp_norm, sel_cmp_opp, cov_df, is_rush_prop=is_rush_prop
                    )
                    st.markdown(
                        f"""
                        <div class="glass-card" style="padding:12px 14px;margin-top:6px;border-left:4px solid #013369;">
                            <div style="display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:8px;margin-bottom:8px;">
                                <span style="font-weight:800;font-size:0.86rem;color:#FFFFFF;text-transform:uppercase;">
                                    Defensive Comparison: Past Opponent ({sel_cmp_opp}) vs Upcoming ({opp_norm})
                                </span>
                                <span class="badge-elite">{sim_sc}% Match · {sim_tg}</span>
                            </div>
                            <div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(175px,1fr));gap:10px;font-size:0.78rem;">
                                <div style="background:#0E0E12;padding:8px 10px;border:1px solid #2A2A35;">
                                    <div style="color:#A1A1AA;font-weight:700;text-transform:uppercase;font-size:0.66rem;">Rush & Pass Def Ranks</div>
                                    <div style="color:#FFFFFF;font-weight:800;margin-top:3px;">
                                        {sel_cmp_opp}: Rush #{int(c_row['rush_def_rank'])} · Pass #{int(c_row['pass_def_rank'])}<br/>
                                        {opp_norm}: Rush #{int(opp_cov_row['rush_def_rank'])} · Pass #{int(opp_cov_row['pass_def_rank'])}
                                    </div>
                                </div>
                                <div style="background:#0E0E12;padding:8px 10px;border:1px solid #2A2A35;">
                                    <div style="color:#A1A1AA;font-weight:700;text-transform:uppercase;font-size:0.66rem;">Safety Shell (1-High vs 2-High)</div>
                                    <div style="color:#FFFFFF;font-weight:800;margin-top:3px;">
                                        {sel_cmp_opp}: {c_row['one_high_pct']:.0f}% 1-Hi / {c_row['two_high_pct']:.0f}% 2-Hi<br/>
                                        {opp_norm}: {opp_cov_row['one_high_pct']:.0f}% 1-Hi / {opp_cov_row['two_high_pct']:.0f}% 2-Hi
                                    </div>
                                </div>
                                <div style="background:#0E0E12;padding:8px 10px;border:1px solid #2A2A35;">
                                    <div style="color:#A1A1AA;font-weight:700;text-transform:uppercase;font-size:0.66rem;">Coverage (Man vs Zone)</div>
                                    <div style="color:#FFFFFF;font-weight:800;margin-top:3px;">
                                        {sel_cmp_opp}: {c_row['man_pct']:.0f}% Man / {c_row['zone_pct']:.0f}% Zone<br/>
                                        {opp_norm}: {opp_cov_row['man_pct']:.0f}% Man / {opp_cov_row['zone_pct']:.0f}% Zone
                                    </div>
                                </div>
                                <div style="background:#0E0E12;padding:8px 10px;border:1px solid #2A2A35;">
                                    <div style="color:#A1A1AA;font-weight:700;text-transform:uppercase;font-size:0.66rem;">Box Count & Scheme</div>
                                    <div style="color:#FFFFFF;font-weight:800;margin-top:3px;">
                                        {sel_cmp_opp}: {c_row['light_box_pct']:.0f}% Light Box ({c_row['scheme_family']})<br/>
                                        {opp_norm}: {opp_cov_row['light_box_pct']:.0f}% Light Box ({opp_cov_row['scheme_family']})
                                    </div>
                                </div>
                            </div>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )

    with tab_logs:
        if p_logs.empty:
            st.info("No weekly game logs found for this player.")
        else:
            disp_cols = [
                c
                for c in [
                    "week",
                    "opponent_team",
                    "passing_yards",
                    "passing_tds",
                    "rushing_yards",
                    "carries",
                    "rushing_tds",
                    "targets",
                    "receptions",
                    "receiving_yards",
                    "receiving_tds",
                ]
                if c in p_logs.columns
            ]
            st.dataframe(
                p_logs[disp_cols].sort_values("week", ascending=False),
                use_container_width=True,
                hide_index=True,
            )

    with tab_inj_hist:
        st.markdown(
            """
            <div style="font-size:0.80rem;color:#A1A1AA;margin-bottom:10px;">
                Weekly practice progression (<b style="color:#FFFFFF;">Wed · Thu · Fri</b>) showing
                <span class="prac-day-pill prac-fp" style="display:inline-flex;width:28px;height:18px;font-size:0.62rem;">FP</span> Full,
                <span class="prac-day-pill prac-lp" style="display:inline-flex;width:28px;height:18px;font-size:0.62rem;">LP</span> Limited, or
                <span class="prac-day-pill prac-dnp" style="display:inline-flex;width:28px;height:18px;font-size:0.62rem;">DNP</span> Did Not Participate,
                paired with the official game designation.
            </div>
            """,
            unsafe_allow_html=True,
        )
        if not inj_hist:
            st.success(
                f"{player_name} has no recorded injury designations in the {season} season (Cleared / Active all weeks)."
            )
        else:
            for rec in inj_hist:
                st.markdown(
                    f"""
                    <div class="glass-card" style="padding:10px 14px;margin-bottom:8px;display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:10px;">
                        <div>
                            <div style="display:flex;align-items:center;gap:8px;">
                                <span class="badge-elite">WEEK {rec['week']}</span>
                                <span style="font-weight:800;color:#FFFFFF;font-size:0.90rem;">{rec['injury']}</span>
                            </div>
                            <div style="font-size:0.75rem;color:#A1A1AA;margin-top:4px;font-weight:600;">
                                Game Outcome: <b style="color:#E4E4E7;">{rec['outcome_str']}</b> · {rec['snaps_str']}
                            </div>
                        </div>
                        <div>
                            {rec['strip_html']}
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )


def render_underdog_props_and_betslip_modal(
    prop_logs: pd.DataFrame,
    away_team: str,
    home_team: str,
    away_eff: pd.Series,
    home_eff: pd.Series,
    headshot_lookup: Dict[str, Dict[str, Any]],
    season: int,
    week_num: int,
) -> None:
    odds_val = int(st.session_state.get("default_odds_american", -110))
    tab_board, tab_slip = st.tabs(
        [
            "Picks & Props",
            f"Bet Slip ({len(st.session_state['bet_slip'])})",
        ]
    )
    with tab_board:
        picks = build_top_player_picks(
            prop_logs, away_team, home_team, away_eff, home_eff, headshot_lookup
        )
        if not picks:
            st.info("No player prop projections available for this matchup.")
        else:
            for idx, pk in enumerate(picks):
                c_p, c_b = st.columns([1.4, 1.8])
                with c_p:
                    render_inline_player_trigger(
                        player_name=pk["player"],
                        team_abbr=pk["team"],
                        pos=pk["pos"],
                        key_suffix=f"ud_modal_{idx}_{pk['player']}",
                        extra_label=f"({pk['pos']} · Proj {pk['proj']} vs {pk['line']})",
                    )
                with c_b:
                    render_compact_bet_action_row(
                        key_prefix=f"ud_modal_bet_{idx}_{pk['player']}",
                        season=int(season),
                        week=int(week_num),
                        matchup=f"{away_team} @ {home_team}",
                        category=f"Prop ({pk['market']})",
                        selection=f"{pk['player']} {pk['side']} {pk['line']} {pk['market']}",
                        market_line=f"{pk['line']}",
                        model_proj=f"{pk['proj']}",
                        american_odds=odds_val,
                        edge_score=pk["edge_score"],
                        ev_pct=pk["ev_pct"],
                        kelly_units=pk["kelly_u"],
                        team_abbr=pk["team"],
                        button_text_override=f"{pk['side']} {pk['line']} {pk['market']}",
                    )
    with tab_slip:
        slip = st.session_state.get("bet_slip", [])
        if not slip:
            st.info("Your Bet Slip is currently empty. Click any line button to add plays.")
        else:
            df_slip = pd.DataFrame(slip)
            disp_cols = [c for c in df_slip.columns if c != "pick_id"]
            st.dataframe(df_slip[disp_cols], use_container_width=True, hide_index=True)
            if st.button("Clear All Tracked Bets", key="modal_clear_slip_btn"):
                clear_bet_slip()
                st.rerun()


# -----------------------------------------------------------------------------
# MAIN APPLICATION WORKSPACE
# -----------------------------------------------------------------------------
def main() -> None:
    master_df = load_master_games_csv()
    avail_seasons = (
        sorted(
            pd.to_numeric(master_df["season"], errors="coerce")
            .dropna()
            .astype(int)
            .unique()
            .tolist(),
            reverse=True,
        )
        if not master_df.empty and "season" in master_df.columns
        else [2025, 2024, 2023]
    )

    # Check query parameters for inline player links
    qp = st.query_params
    if "inspect_player" in qp and qp["inspect_player"]:
        p_qp = str(qp["inspect_player"]).strip()
        t_qp = str(qp.get("inspect_team", "")).strip().upper()
        pos_qp = str(qp.get("inspect_pos", "")).strip().upper()
        st.query_params.clear()
        trigger_player_popup(p_qp, t_qp, pos_qp)

    with st.sidebar:
        st.markdown(
            """
            <div style="padding:8px 0 12px 0;border-bottom:2px solid #262630;margin-bottom:12px;">
                <div style="font-family:'Plus Jakarta Sans',sans-serif;font-size:1.20rem;font-weight:900;color:#FFFFFF;letter-spacing:0.04em;text-transform:uppercase;">
                    FOOTBALL EDGER
                </div>
                <div style="font-size:0.72rem;color:#A1A1AA;font-weight:700;text-transform:uppercase;letter-spacing:0.06em;">
                    NFL Matchup & Prop Desk
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        sel_season = st.selectbox("Season", avail_seasons, index=0)
        sched_df = load_season_schedule(int(sel_season))
        avail_weeks = (
            sorted(
                pd.to_numeric(sched_df["week"], errors="coerce")
                .dropna()
                .astype(int)
                .unique()
                .tolist()
            )
            if not sched_df.empty and "week" in sched_df.columns
            else list(range(1, 19))
        )
        default_wk_idx = get_default_nfl_week_index(sched_df, avail_weeks)
        sel_week = st.selectbox("Week (Auto-Synced)", avail_weeks, index=default_wk_idx)

        odds_choices = [-105, -110, -115, -120, -125, 100, 105]
        cur_odds = int(st.session_state.get("default_odds_american", -110))
        sel_odds = st.selectbox(
            "Default Market Odds (Vig)",
            odds_choices,
            index=odds_choices.index(cur_odds) if cur_odds in odds_choices else 1,
            format_func=lambda x: f"{x:+d}",
        )
        st.session_state["default_odds_american"] = int(sel_odds)

        kelly_map = {
            "Quarter-Kelly (0.25x)": 0.25,
            "Half-Kelly (0.50x)": 0.50,
            "Full-Kelly (1.00x)": 1.00,
        }
        sel_kelly_lbl = st.selectbox("Kelly Stake Multiplier", list(kelly_map.keys()), index=0)
        st.session_state["kelly_fraction_mult"] = kelly_map[sel_kelly_lbl]

        st.markdown("#### Quick Bet Slip")
        slip_items = st.session_state.get("bet_slip", [])
        st.caption(f"{len(slip_items)} active selection(s) tracked")
        if slip_items:
            for item in slip_items[:5]:
                st.markdown(
                    f"- **{item.get('Selection', '')}** (`{item.get('Odds', '-110')}` · `{item.get('Kelly Stake (u)', 0.0)}u`)"
                )
            if st.button("Clear Slip", key="sidebar_clear_slip"):
                clear_bet_slip()
                st.rerun()

    wk_games = (
        sched_df[pd.to_numeric(sched_df["week"], errors="coerce") == int(sel_week)].reset_index(drop=True)
        if not sched_df.empty
        else pd.DataFrame()
    )

    if not wk_games.empty:
        valid_gids = wk_games["game_id"].astype(str).tolist()
        if st.session_state.get("selected_game") not in valid_gids:
            def_g_idx = get_default_next_game_index(wk_games)
            def_g_idx = min(max(0, def_g_idx), len(valid_gids) - 1)
            st.session_state["selected_game"] = valid_gids[def_g_idx]
            st.session_state["selected_game_idx"] = def_g_idx

    team_records = compute_team_records(sched_df, through_week=int(sel_week))
    eff_df = load_team_efficiency_csv(int(sel_season))
    cov_df = load_team_coverage_and_shell_splits(int(sel_season), eff_df)
    pstats_df = load_player_stats_csv(int(sel_season))
    snaps_df = load_snap_counts_csv(int(sel_season))
    inj_df = load_injuries_csv(
        int(sel_season), int(st.session_state.get("injury_refresh_token", 0))
    )
    rosters_df = load_rosters_headshots_csv(int(sel_season))
    headshot_lookup = build_headshot_lookup(int(sel_season))

    render_nfl_horizontal_ticker(week_games=wk_games, team_records=team_records)

    selected_gid = st.session_state.get("selected_game", "")
    game_row_matches = (
        wk_games[wk_games["game_id"].astype(str) == str(selected_gid)]
        if not wk_games.empty and "game_id" in wk_games.columns
        else pd.DataFrame()
    )
    if game_row_matches.empty and not wk_games.empty:
        game_row_matches = wk_games.iloc[[0]]

    game_row = (
        game_row_matches.iloc[0]
        if not game_row_matches.empty
        else pd.Series(
            {
                "game_id": f"{sel_season}_{sel_week}_DAL_ARI",
                "away_team": "DAL",
                "home_team": "ARI",
                "home_spread": -3.0,
                "total_line": 45.5,
                "rest_edge_home": 0.0,
                "week": sel_week,
            }
        )
    )

    away_team = normalize_team_code(str(game_row.get("away_team", "DAL")))
    home_team = normalize_team_code(str(game_row.get("home_team", "ARI")))

    away_eff_rows = eff_df[eff_df["team"] == away_team]
    home_eff_rows = eff_df[eff_df["team"] == home_team]
    away_eff = away_eff_rows.iloc[0] if not away_eff_rows.empty else eff_df.iloc[0]
    home_eff = (
        home_eff_rows.iloc[0]
        if not home_eff_rows.empty
        else eff_df.iloc[min(1, len(eff_df) - 1)]
    )

    away_inj_list = build_injury_impact_report(
        inj_df, snaps_df, rosters_df, away_team, int(sel_week), headshot_lookup
    )
    home_inj_list = build_injury_impact_report(
        inj_df, snaps_df, rosters_df, home_team, int(sel_week), headshot_lookup
    )
    away_off_pen, away_def_pen = compute_team_injury_penalties(away_inj_list)
    home_off_pen, home_def_pen = compute_team_injury_penalties(home_inj_list)

    model_eval = compute_model_fair_line_and_totals(
        a_eff=away_eff,
        h_eff=home_eff,
        away_off_pen=away_off_pen,
        away_def_pen=away_def_pen,
        home_off_pen=home_off_pen,
        home_def_pen=home_def_pen,
        away_tm=away_team,
        home_tm=home_team,
        market_home_spread=game_row.get("home_spread", np.nan),
        market_total=game_row.get("total_line", np.nan),
        rest_edge_home=float(game_row.get("rest_edge_home", 0.0) or 0.0),
        roof_str=str(game_row.get("roof", "Outdoors") or "Outdoors"),
    )
    mkt_splits = estimate_line_movement_and_splits(
        game_row=game_row,
        model_projection=model_eval,
        away_tm=away_team,
        home_tm=home_team,
    )
    prop_logs = prepare_matchup_player_prop_logs(
        pstats_df, away_team, home_team, int(sel_week)
    )

    odds_val = int(st.session_state.get("default_odds_american", -110))
    kelly_mult = float(st.session_state.get("kelly_fraction_mult", 0.25))

    top_matchup_tab, top_hub_tab = st.tabs(["Matchup", "League Hub"])

    with top_matchup_tab:
        away_hex, home_hex = get_matchup_team_colors(away_team, home_team)
        fair_sp_num = float(model_eval["fair_home_spread"])
        fav_tm = home_team if fair_sp_num <= 0 else away_team
        model_fair_plain = f"Model: {fav_tm} by {abs(fair_sp_num):.1f} ({model_eval['spread_edge_pts']:+.1f} pt edge)"

        st.markdown(
            f"""
            <div class="glass-card" style="padding:14px 18px;margin-bottom:14px;border-top:4px solid {away_hex};border-bottom:4px solid {home_hex};">
                <div style="display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:12px;">
                    <div style="display:flex;align-items:center;gap:10px;flex-wrap:wrap;">
                        {render_team_pill(away_team, team_records.get(away_team, "0-0"), color_override=away_hex)}
                        <span style="font-family:'Plus Jakarta Sans',sans-serif;font-weight:900;font-size:1.25rem;color:#FFFFFF;">
                            {NFL_TEAM_NAMES.get(away_team, away_team)} @ {NFL_TEAM_NAMES.get(home_team, home_team)}
                        </span>
                        {render_team_pill(home_team, team_records.get(home_team, "0-0"), color_override=home_hex)}
                    </div>
                    <div style="display:flex;align-items:center;gap:8px;flex-wrap:wrap;">
                        <span class="badge-elite">{model_fair_plain}</span>
                        <span class="badge-mid">Proj Score: {away_team} {model_eval['away_proj_pts']:.1f} - {home_team} {model_eval['home_proj_pts']:.1f} (Total {model_eval['fair_total']:.1f})</span>
                    </div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        sub_ov, sub_mu, sub_inj, sub_ts, sub_pd = st.tabs(
            ["Overview", "Matchups", "Injuries", "Team Stats", "Props & Depth"]
        )

        with sub_ov:
            b1, b2, b3 = st.columns(3)
            with b1:
                sp_ev, sp_kelly = compute_ev_and_kelly(
                    model_eval["spread_cover_prob"], odds_val, kelly_mult
                )
                st.markdown(
                    f"""
                    <div class="glass-card" style="padding:12px 14px;">
                        <div style="font-size:0.70rem;font-weight:800;color:#A1A1AA;text-transform:uppercase;">Spread Pick</div>
                        <div style="font-size:1.15rem;font-weight:900;color:#FFFFFF;margin:4px 0;">{model_eval['backed_spread_line_str']}</div>
                        <div style="font-size:0.76rem;color:#A1A1AA;margin-bottom:8px;">{model_fair_plain}</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
                render_compact_bet_action_row(
                    key_prefix=f"ov_sp_{away_team}_{home_team}",
                    season=int(sel_season),
                    week=int(sel_week),
                    matchup=f"{away_team} @ {home_team}",
                    category="Spread",
                    selection=model_eval["backed_spread_line_str"],
                    market_line=mkt_splits["cur_sp_str"],
                    model_proj=model_eval["fair_spread_str"],
                    american_odds=odds_val,
                    edge_score=model_eval["spread_edge_pts"],
                    ev_pct=sp_ev,
                    kelly_units=sp_kelly,
                    team_abbr=model_eval["backed_spread_team"],
                    button_text_override=f"{model_eval['backed_spread_line_str']} ({odds_val:+d})",
                )
            with b2:
                tot_dir = model_eval["total_lean_dir"]
                mkt_tot_val = float(game_row.get("total_line", 44.5) or 44.5)
                tot_ev, tot_kelly = compute_ev_and_kelly(
                    model_eval["total_hit_prob"], odds_val, kelly_mult
                )
                st.markdown(
                    f"""
                    <div class="glass-card" style="padding:12px 14px;">
                        <div style="font-size:0.70rem;font-weight:800;color:#A1A1AA;text-transform:uppercase;">Total Pick</div>
                        <div style="font-size:1.15rem;font-weight:900;color:#FFFFFF;margin:4px 0;">{tot_dir} {mkt_tot_val:.1f}</div>
                        <div style="font-size:0.76rem;color:#A1A1AA;margin-bottom:8px;">Model Proj: {model_eval['fair_total']:.1f} pts ({model_eval['total_edge_pts']:.1f} pt edge)</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
                render_compact_bet_action_row(
                    key_prefix=f"ov_tot_{away_team}_{home_team}",
                    season=int(sel_season),
                    week=int(sel_week),
                    matchup=f"{away_team} @ {home_team}",
                    category="Total",
                    selection=f"{tot_dir} {mkt_tot_val:.1f}",
                    market_line=f"{mkt_tot_val:.1f}",
                    model_proj=f"{model_eval['fair_total']:.1f}",
                    american_odds=odds_val,
                    edge_score=model_eval["total_edge_pts"],
                    ev_pct=tot_ev,
                    kelly_units=tot_kelly,
                    team_abbr=home_team if tot_dir == "OVER" else away_team,
                    button_text_override=f"{tot_dir} {mkt_tot_val:.1f} ({odds_val:+d})",
                )
            with b3:
                away_ml_ev, away_ml_kelly = compute_ev_and_kelly(
                    model_eval["away_win_prob_raw"], mkt_splits["away_ml_int"], kelly_mult
                )
                home_ml_ev, home_ml_kelly = compute_ev_and_kelly(
                    model_eval["home_win_prob_raw"], mkt_splits["home_ml_int"], kelly_mult
                )
                if home_ml_ev >= away_ml_ev:
                    ml_pick = home_team
                    ml_odds = mkt_splits["home_ml_int"]
                    ml_wp = model_eval["home_win_prob"]
                    ml_ev = home_ml_ev
                    ml_kelly = home_ml_kelly
                else:
                    ml_pick = away_team
                    ml_odds = mkt_splits["away_ml_int"]
                    ml_wp = model_eval["away_win_prob"]
                    ml_ev = away_ml_ev
                    ml_kelly = away_ml_kelly

                st.markdown(
                    f"""
                    <div class="glass-card" style="padding:12px 14px;">
                        <div style="font-size:0.70rem;font-weight:800;color:#A1A1AA;text-transform:uppercase;">Moneyline Pick</div>
                        <div style="font-size:1.15rem;font-weight:900;color:#FFFFFF;margin:4px 0;">{ml_pick} ML ({ml_odds:+d})</div>
                        <div style="font-size:0.76rem;color:#A1A1AA;margin-bottom:8px;">Win Prob: {ml_wp:.1f}% · Mkt: {mkt_splits['ml_str']}</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
                render_compact_bet_action_row(
                    key_prefix=f"ov_ml_{away_team}_{home_team}",
                    season=int(sel_season),
                    week=int(sel_week),
                    matchup=f"{away_team} @ {home_team}",
                    category="Moneyline",
                    selection=f"{ml_pick} ML",
                    market_line=f"{ml_odds:+d}",
                    model_proj=f"{ml_wp:.1f}% Win",
                    american_odds=ml_odds,
                    edge_score=round(abs(ml_ev), 1),
                    ev_pct=ml_ev,
                    kelly_units=ml_kelly,
                    team_abbr=ml_pick,
                    button_text_override=f"{ml_pick} ML ({ml_odds:+d})",
                )

            st.markdown("#### Top Player Props")
            top_picks = build_top_player_picks(
                prop_logs, away_team, home_team, away_eff, home_eff, headshot_lookup
            )[:4]
            if top_picks:
                p_cols = st.columns(2)
                for idx, pk in enumerate(top_picks):
                    with p_cols[idx % 2]:
                        st.markdown(
                            f"""
                            <div class="glass-card" style="padding:10px 12px;margin-bottom:8px;">
                                <div style="display:flex;align-items:center;gap:10px;">
                                    {render_mismatch_headshot_html(pk['player'], pk['team'], pk['pos'], headshot_lookup)}
                                    <div style="flex:1;">
                                        <div style="font-weight:800;color:#FFFFFF;font-size:0.92rem;">{pk['player']} ({pk['team']} · {pk['pos']})</div>
                                        <div style="font-size:0.75rem;color:#A1A1AA;">Proj: <b>{pk['proj']}</b> · Hit: {pk['hit_str']} · vs #{pk['def_rank']} Def</div>
                                    </div>
                                    <span class="{pk['tier_cls']}">{pk['tier_lbl']}</span>
                                </div>
                            </div>
                            """,
                            unsafe_allow_html=True,
                        )
                        render_compact_bet_action_row(
                            key_prefix=f"ov_prop_{idx}_{pk['player']}",
                            season=int(sel_season),
                            week=int(sel_week),
                            matchup=f"{away_team} @ {home_team}",
                            category=f"Prop ({pk['market']})",
                            selection=f"{pk['player']} {pk['side']} {pk['line']} {pk['market']}",
                            market_line=f"{pk['line']}",
                            model_proj=f"{pk['proj']}",
                            american_odds=odds_val,
                            edge_score=pk["edge_score"],
                            ev_pct=pk["ev_pct"],
                            kelly_units=pk["kelly_u"],
                            team_abbr=pk["team"],
                            button_text_override=f"{pk['side']} {pk['line']} {pk['market']}",
                        )

            h2h_df = get_five_year_h2h_history(
                master_df, away_team, home_team, int(sel_season)
            )
            render_five_year_h2h_visual(
                h2h_df=h2h_df,
                away_tm=away_team,
                home_tm=home_team,
                away_color=away_hex,
                home_color=home_hex,
                selected_season=int(sel_season),
            )

        with sub_mu:
            m_sub1, m_sub2 = st.tabs(["WR vs CB", "Touch Share"])
            with m_sub1:
                battles = build_cb_wr_matchup_battles(
                    prop_logs,
                    rosters_df,
                    away_team,
                    home_team,
                    away_eff,
                    home_eff,
                    headshot_lookup,
                )
                if not battles:
                    st.info("No WR vs CB battles available for this matchup.")
                else:
                    for b_idx, b in enumerate(battles):
                        st.markdown(
                            f"""
                            <div class="glass-card" style="padding:10px 14px;margin-bottom:8px;display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:10px;">
                                <div style="display:flex;align-items:center;gap:10px;">
                                    {render_mismatch_headshot_html(b['wr_name'], b['off_team'], b['wr_pos'], headshot_lookup)}
                                    <div>
                                        <div style="font-size:0.70rem;color:#A1A1AA;font-weight:800;text-transform:uppercase;">{b['slot_label']}</div>
                                        <div style="font-weight:800;color:#FFFFFF;font-size:0.92rem;">{b['wr_name']} ({b['off_team']}) vs {b['cb_name']} ({b['def_team']})</div>
                                        <div style="font-size:0.75rem;color:#A1A1AA;">{b['wr_ypg']} Yds/G · {b['wr_tpg']} Tgts/G · vs #{b['pass_def_rank']} Pass Def</div>
                                    </div>
                                </div>
                                <span class="{b['adv_cls']}">{b['adv_lbl']}</span>
                            </div>
                            """,
                            unsafe_allow_html=True,
                        )
            with m_sub2:
                u_col1, u_col2 = st.columns(2)
                with u_col1:
                    st.markdown(f"##### {away_team} Skill Usage")
                    st.dataframe(
                        aggregate_team_skill_usage(prop_logs, away_team),
                        use_container_width=True,
                        hide_index=True,
                    )
                with u_col2:
                    st.markdown(f"##### {home_team} Skill Usage")
                    st.dataframe(
                        aggregate_team_skill_usage(prop_logs, home_team),
                        use_container_width=True,
                        hide_index=True,
                    )

        with sub_inj:
            st.markdown(
                """
                <div class="glass-card" style="padding:10px 14px;margin-bottom:12px;display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:10px;">
                    <div style="font-size:0.80rem;color:#E4E4E7;font-weight:600;">
                        <b>Daily Practice Tracker (Wed · Thu · Fri)</b>: Each player card displays daily participation tags
                        (<span class="prac-day-pill prac-fp" style="display:inline-flex;width:26px;height:17px;font-size:0.60rem;">FP</span> Full,
                        <span class="prac-day-pill prac-lp" style="display:inline-flex;width:26px;height:17px;font-size:0.60rem;">LP</span> Limited,
                        <span class="prac-day-pill prac-dnp" style="display:inline-flex;width:26px;height:17px;font-size:0.60rem;">DNP</span> No Practice)
                        next to the primary game status designation.
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

            inj_col_away, inj_col_home = st.columns(2)
            for col_obj, tm_code, inj_list in [
                (inj_col_away, away_team, away_inj_list),
                (inj_col_home, home_team, home_inj_list),
            ]:
                with col_obj:
                    depth_url = get_team_depth_chart_url(tm_code)
                    tm_hex = resolve_team_display_color(tm_code)
                    st.markdown(
                        f"""
                        <div class="glass-card" style="padding:10px 14px;margin-bottom:10px;border-left:5px solid {tm_hex};display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:8px;">
                            <div style="display:flex;align-items:center;gap:8px;">
                                {render_team_pill(tm_code)}
                                <span style="font-family:'Plus Jakarta Sans',sans-serif;font-weight:900;font-size:1.0rem;color:#FFFFFF;text-transform:uppercase;">
                                    {NFL_TEAM_NAMES.get(tm_code, tm_code)} Injury Report
                                </span>
                            </div>
                            <a href="{depth_url}" target="_blank" rel="noopener noreferrer"
                               style="background:#013369;color:#FFFFFF;text-decoration:none;font-size:0.70rem;font-weight:800;padding:5px 10px;border:1px solid #3B82F6;text-transform:uppercase;letter-spacing:0.04em;">
                                Official {tm_code} Depth Chart ↗
                            </a>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )

                    if not inj_list:
                        st.success(f"No active injury designations reported for {tm_code}.")
                    else:
                        for idx_i, item in enumerate(inj_list):
                            st.markdown(
                                f"""
                                <div class="glass-card" style="padding:10px 12px;margin-bottom:6px;border-left:4px solid {tm_hex};">
                                    <div style="display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:10px;">
                                        <div style="display:flex;align-items:center;gap:10px;min-width:190px;flex:1;">
                                            {render_mismatch_headshot_html(item['player'], tm_code, item['pos'], headshot_lookup)}
                                            <div>
                                                <div style="display:flex;align-items:center;gap:6px;flex-wrap:wrap;">
                                                    <span style="font-weight:900;color:#FFFFFF;font-size:0.90rem;">{item['player']}</span>
                                                    <span class="badge-mid">{item['pos']}</span>
                                                </div>
                                                <div style="font-size:0.75rem;color:#A1A1AA;margin-top:2px;font-weight:600;">
                                                    <b style="color:#E4E4E7;">{item['injury']}</b> · {item['snap_pct']:.0f}% Snaps ({item['side']})
                                                </div>
                                            </div>
                                        </div>
                                        <div>
                                            {item['strip_html']}
                                        </div>
                                    </div>
                                </div>
                                """,
                                unsafe_allow_html=True,
                            )
                            render_inline_player_trigger(
                                player_name=item["player"],
                                team_abbr=tm_code,
                                pos=item["pos"],
                                key_suffix=f"inj_card_{tm_code}_{idx_i}_{item['player']}",
                                extra_label="— Open Injury & Prop Dossier",
                            )

        with sub_ts:
            st.markdown("#### Team Rankings & Defensive Coverage Tendencies")
            away_cov = (
                cov_df[cov_df["team"] == away_team].iloc[0]
                if not cov_df.empty and (cov_df["team"] == away_team).any()
                else None
            )
            home_cov = (
                cov_df[cov_df["team"] == home_team].iloc[0]
                if not cov_df.empty and (cov_df["team"] == home_team).any()
                else None
            )
            cmp_rows = [
                {
                    "Category": "Overall Offense EPA/Play",
                    away_team: f"{away_eff['off_epa_per_play']:+.3f} (#{int(away_eff['off_rank'])})",
                    home_team: f"{home_eff['off_epa_per_play']:+.3f} (#{int(home_eff['off_rank'])})",
                },
                {
                    "Category": "Overall Defense EPA/Play",
                    away_team: f"{away_eff['def_epa_per_play']:+.3f} (#{int(away_eff['def_rank'])})",
                    home_team: f"{home_eff['def_epa_per_play']:+.3f} (#{int(home_eff['def_rank'])})",
                },
                {
                    "Category": "Pass Offense",
                    away_team: f"{away_eff['pass_off_epa']:+.3f} (#{int(away_eff['pass_off_rank'])})",
                    home_team: f"{home_eff['pass_off_epa']:+.3f} (#{int(home_eff['pass_off_rank'])})",
                },
                {
                    "Category": "Rush Offense",
                    away_team: f"{away_eff['rush_off_epa']:+.3f} (#{int(away_eff['rush_off_rank'])})",
                    home_team: f"{home_eff['rush_off_epa']:+.3f} (#{int(home_eff['rush_off_rank'])})",
                },
            ]
            if away_cov is not None and home_cov is not None:
                cmp_rows.extend(
                    [
                        {
                            "Category": "Safety Shell (1-High / 2-High %)",
                            away_team: f"{away_cov['one_high_pct']:.0f}% 1-Hi / {away_cov['two_high_pct']:.0f}% 2-Hi",
                            home_team: f"{home_cov['one_high_pct']:.0f}% 1-Hi / {home_cov['two_high_pct']:.0f}% 2-Hi",
                        },
                        {
                            "Category": "Coverage Split (Man / Zone %)",
                            away_team: f"{away_cov['man_pct']:.0f}% Man / {away_cov['zone_pct']:.0f}% Zone",
                            home_team: f"{home_cov['man_pct']:.0f}% Man / {home_cov['zone_pct']:.0f}% Zone",
                        },
                        {
                            "Category": "Run Box (Light / Stacked %)",
                            away_team: f"{away_cov['light_box_pct']:.0f}% Light / {away_cov['stacked_box_pct']:.0f}% Stacked",
                            home_team: f"{home_cov['light_box_pct']:.0f}% Light / {home_cov['stacked_box_pct']:.0f}% Stacked",
                        },
                    ]
                )
            st.dataframe(
                pd.DataFrame(cmp_rows), use_container_width=True, hide_index=True
            )

        with sub_pd:
            pd_sub1, pd_sub2 = st.tabs(["Player Props", "Rosters"])
            with pd_sub1:
                picks_all = build_top_player_picks(
                    prop_logs,
                    away_team,
                    home_team,
                    away_eff,
                    home_eff,
                    headshot_lookup,
                )
                if not picks_all:
                    st.info("No player props found for this game.")
                else:
                    for idx_p, pk in enumerate(picks_all):
                        c1, c2 = st.columns([1.3, 1.7])
                        with c1:
                            render_inline_player_trigger(
                                player_name=pk["player"],
                                team_abbr=pk["team"],
                                pos=pk["pos"],
                                key_suffix=f"pd_tab_{idx_p}_{pk['player']}",
                                extra_label=f"({pk['pos']} · {pk['market']} {pk['line']})",
                            )
                        with c2:
                            render_compact_bet_action_row(
                                key_prefix=f"pd_bet_{idx_p}_{pk['player']}",
                                season=int(sel_season),
                                week=int(sel_week),
                                matchup=f"{away_team} @ {home_team}",
                                category=f"Prop ({pk['market']})",
                                selection=f"{pk['player']} {pk['side']} {pk['line']} {pk['market']}",
                                market_line=f"{pk['line']}",
                                model_proj=f"{pk['proj']}",
                                american_odds=odds_val,
                                edge_score=pk["edge_score"],
                                ev_pct=pk["ev_pct"],
                                kelly_units=pk["kelly_u"],
                                team_abbr=pk["team"],
                                button_text_override=f"{pk['side']} {pk['line']} {pk['market']}",
                            )
            with pd_sub2:
                rc1, rc2 = st.columns(2)
                with rc1:
                    st.markdown(f"##### {away_team} Active Roster & Snaps (LG / RG Specified)")
                    st.dataframe(
                        build_roster_usage_table(
                            snaps_df, pstats_df, inj_df, away_team, int(sel_week)
                        ),
                        use_container_width=True,
                        hide_index=True,
                    )
                with rc2:
                    st.markdown(f"##### {home_team} Active Roster & Snaps (LG / RG Specified)")
                    st.dataframe(
                        build_roster_usage_table(
                            snaps_df, pstats_df, inj_df, home_team, int(sel_week)
                        ),
                        use_container_width=True,
                        hide_index=True,
                    )

    with top_hub_tab:
        hub_bp, hub_pf, hub_mr, hub_st = st.tabs(
            ["Best Picks", "Prop Finder", "Model Record", "Standings"]
        )
        with hub_bp:
            st.markdown("#### Best Picks Across the Slate")
            st.dataframe(
                build_slate_best_bets_leaderboard(wk_games, eff_df),
                use_container_width=True,
                hide_index=True,
            )
        with hub_pf:
            st.markdown("#### League-Wide Prop Finder & Defensive Coverage Explorer")
            st.dataframe(
                cov_df[
                    [
                        "team",
                        "scheme_family",
                        "one_high_pct",
                        "two_high_pct",
                        "man_pct",
                        "zone_pct",
                        "light_box_pct",
                        "pass_def_rank",
                        "rush_def_rank",
                    ]
                ].sort_values("pass_def_rank"),
                use_container_width=True,
                hide_index=True,
            )
        with hub_mr:
            bt = run_season_backtest(sched_df, eff_df)
            k1, k2, k3 = st.columns(3)
            k1.metric("Season ATS Record", f"{bt['wins']}-{bt['losses']}", f"{bt.get('win_pct', 0.0):.1f}% Win")
            k2.metric("Net Units", f"{bt['units']:+.2f}u", "1u Flat Grading")
            k3.metric("Season ROI", f"{bt['roi']:+.1f}%", "Edges >= 1.5 pts")
            if not bt["df"].empty:
                st.dataframe(bt["df"], use_container_width=True, hide_index=True)
        with hub_st:
            div_standings = compute_nfl_division_standings(sched_df, through_week=int(sel_week))
            for conf_name in ["AFC", "NFC"]:
                st.markdown(f"#### {conf_name} Divisions")
                d_cols = st.columns(2)
                for d_idx, div_name in enumerate(
                    [f"{conf_name} East", f"{conf_name} North", f"{conf_name} South", f"{conf_name} West"]
                ):
                    with d_cols[d_idx % 2]:
                        if div_name in div_standings:
                            render_nfl_division_standings_card(
                                div_name=div_name,
                                div_df=div_standings[div_name],
                                highlight_teams={away_team, home_team},
                                season_label=int(sel_season),
                                week_label=int(sel_week),
                            )

    st.markdown('<div class="floating-fab-wrap">', unsafe_allow_html=True)
    if st.button("＋", key="floating_plus_fab_btn", help="Open Picks, Props & Bet Slip"):
        trigger_props_slip_popup()
        st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)

    if st.session_state.get("open_player_modal") and st.session_state.get("active_player"):
        p_info = st.session_state["active_player"]
        p_nm = p_info.get("name", p_info.get("player_name", ""))
        p_tm = normalize_team_code(p_info.get("team", away_team))
        p_opp = home_team if p_tm == away_team else away_team

        if hasattr(st, "dialog"):

            @st.dialog(f"{p_nm} — Player Dossier", width="large")
            def _show_player_dialog() -> None:
                render_player_popup_contents(
                    player_name=p_nm,
                    team_abbr=p_tm,
                    opp_team=p_opp,
                    season=int(sel_season),
                    week_num=int(sel_week),
                    pstats_df=pstats_df,
                    snaps_df=snaps_df,
                    inj_df=inj_df,
                    eff_df=eff_df,
                    headshot_lookup=headshot_lookup,
                )
                if st.button("Close Dossier", key="close_player_dlg_btn"):
                    st.session_state["open_player_modal"] = False
                    st.session_state["active_player"] = None
                    st.rerun()

            _show_player_dialog()

    if st.session_state.get("open_props_slip_modal"):
        if hasattr(st, "dialog"):

            @st.dialog("Matchup Prop Explorer & Bet Slip", width="large")
            def _show_underdog_dialog() -> None:
                render_underdog_props_and_betslip_modal(
                    prop_logs=prop_logs,
                    away_team=away_team,
                    home_team=home_team,
                    away_eff=away_eff,
                    home_eff=home_eff,
                    headshot_lookup=headshot_lookup,
                    season=int(sel_season),
                    week_num=int(sel_week),
                )
                if st.button("Close Explorer", key="close_ud_dlg_btn"):
                    st.session_state["open_props_slip_modal"] = False
                    st.rerun()

            _show_underdog_dialog()


if __name__ == "__main__":
    main()
