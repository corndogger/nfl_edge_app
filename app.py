from urllib.parse import quote
import time
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
import streamlit.components.v1 as components

# -----------------------------------------------------------------------------
# 1. PAGE CONFIGURATION & CLEAN SLATE TERMINAL CSS THEME (STRICT NO-EMOJI UI)
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="Football Edger",
    layout="wide",
    initial_sidebar_state="expanded",
)

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
    font-size: 1.50rem !important;
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

/* Clean, Toned-Down Sports Analytics Terminal Cards */
.terminal-card {
    background-color: #121722;
    border: 1px solid #222B3A;
    border-left: 3px solid #4B83BD;
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
    color: #34D399 !important;
    text-decoration-color: #34D399;
}

/* Style Streamlit tertiary buttons to look like clean inline hyperlinked player names */
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
    font-family: monospace !important;
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
    color: #34D399 !important;
    text-decoration-color: #34D399 !important;
    background: rgba(52, 211, 153, 0.08) !important;
    border-radius: 3px !important;
}
button[kind="tertiary"] p {
    font-family: monospace !important;
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
   Forces Streamlit's column row containing .nfl-ticker-marker into a single
   non-wrapping horizontal scroll strip with compact 192px game cards.
   ============================================================================ */
div[data-testid="stHorizontalBlock"]:has(.nfl-ticker-marker) {
    display: flex !important;
    flex-direction: row !important;
    flex-wrap: nowrap !important;
    overflow-x: auto !important;
    overflow-y: hidden !important;
    white-space: nowrap !important;
    gap: 8px !important;
    padding: 8px 8px 12px 8px !important;
    margin-bottom: 8px !important;
    max-width: 100% !important;
    background: #0D1118 !important;
    border: 1px solid #1E2736 !important;
    border-radius: 8px !important;
    scrollbar-width: thin;
    scrollbar-color: #334155 #0D1118;
    -webkit-overflow-scrolling: touch;
}
div[data-testid="stHorizontalBlock"]:has(.nfl-ticker-marker)::-webkit-scrollbar {
    height: 7px;
}
div[data-testid="stHorizontalBlock"]:has(.nfl-ticker-marker)::-webkit-scrollbar-track {
    background: #0D1118;
    border-radius: 4px;
}
div[data-testid="stHorizontalBlock"]:has(.nfl-ticker-marker)::-webkit-scrollbar-thumb {
    background-color: #334155;
    border-radius: 4px;
}
div[data-testid="stHorizontalBlock"]:has(.nfl-ticker-marker) > div[data-testid="stColumn"],
div[data-testid="stHorizontalBlock"]:has(.nfl-ticker-marker) > div[data-testid="column"] {
    flex: 0 0 192px !important;
    min-width: 192px !important;
    max-width: 192px !important;
    width: 192px !important;
    white-space: nowrap !important;
}

/* Individual Ticker Card Visuals */
.ticker-card {
    background-color: #131823;
    border: 1px solid #242E3E;
    border-top: 2px solid #334155;
    border-radius: 6px 6px 0 0;
    padding: 7px 10px;
    margin-bottom: -14px;
    white-space: nowrap;
    transition: all 0.14s ease-in-out;
}
.ticker-card-active {
    background-color: #142225;
    border: 1px solid #34D399;
    border-top: 2px solid #34D399;
    border-radius: 6px 6px 0 0;
    padding: 7px 10px;
    margin-bottom: -14px;
    white-space: nowrap;
}
.ticker-top-bar {
    display: flex;
    justify-content: space-between;
    align-items: center;
    font-size: 0.66rem;
    font-family: monospace;
    color: #94A3B8;
    margin-bottom: 4px;
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
    font-family: monospace;
}
.ticker-team-row {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin: 3px 0;
    font-family: monospace;
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
    font-family: monospace;
    font-size: 0.71rem;
    font-weight: 600;
    color: #64748B;
    margin-left: 2px;
}
.ticker-score-win {
    font-family: monospace;
    font-size: 0.86rem;
    font-weight: 800;
    color: #34D399;
}
.ticker-score {
    font-family: monospace;
    font-size: 0.84rem;
    font-weight: 700;
    color: #CBD5E1;
}
.ticker-score-muted {
    font-family: monospace;
    font-size: 0.74rem;
    color: #64748B;
}
.ticker-footer {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-top: 5px;
    padding-top: 4px;
    border-top: 1px solid #1E293B;
    font-size: 0.65rem;
    font-family: monospace;
    color: #94A3B8;
    white-space: nowrap;
}

/* Style the action button docked seamlessly at the bottom of each ticker card */
div[data-testid="stHorizontalBlock"]:has(.nfl-ticker-marker) div[data-testid="stButton"] > button {
    border-radius: 0 0 6px 6px !important;
    font-family: monospace !important;
    font-size: 0.70rem !important;
    font-weight: 700 !important;
    height: 26px !important;
    min-height: 26px !important;
    padding: 0 8px !important;
    margin-top: 0 !important;
    white-space: nowrap !important;
}

/* Streamlined Active Game Selection Banner */
.active-game-spotlight {
    background-color: #121824;
    border: 1px solid #2A364B;
    border-left: 4px solid #34D399;
    border-radius: 10px;
    padding: 14px 18px;
    margin: 4px 0 12px 0;
    color: #F8FAFC;
    max-width: 100%;
    overflow-wrap: break-word;
}
.active-lock-pill {
    background-color: rgba(52, 211, 153, 0.12);
    color: #34D399;
    border: 1px solid rgba(52, 211, 153, 0.35);
    padding: 2px 9px;
    border-radius: 4px;
    font-size: 0.71rem;
    font-weight: 700;
    letter-spacing: 0.04em;
    font-family: monospace;
    display: inline-block;
    text-transform: uppercase;
}

/* ============================================================================
   COMPACT PLAYER HEADSHOT AVATARS FOR MISMATCH & PICK CARDS
   Clean 48x48 cutout frame that never overrides parent Streamlit column widths.
   ============================================================================ */
.mismatch-headshot-wrap {
    width: 48px;
    height: 48px;
    border-radius: 7px;
    background-color: #161E2C;
    border: 1px solid #263144;
    display: flex;
    align-items: flex-end;
    justify-content: center;
    overflow: hidden;
    flex-shrink: 0;
    margin: 2px 0 0 0;
    padding: 0;
}
.mismatch-headshot-img {
    width: 48px;
    height: 48px;
    object-fit: cover;
    object-position: top center;
    display: block;
    margin: 0;
    padding: 0;
}
.mismatch-headshot-fallback {
    width: 48px;
    height: 48px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-family: monospace;
    font-size: 0.82rem;
    font-weight: 700;
    color: #94A3B8;
    background: #141B26;
}
.cb-wr-vs-divider {
    text-align: center;
    padding-top: 24px;
    font-family: monospace;
    font-weight: 800;
    color: #64748B;
}

/* ============================================================================
   PLAYER POP-OUT DOSSIER HEADER & BORDERLESS FLUSH HEADSHOT
   ============================================================================ */
.player-modal-banner {
    background-color: #121824;
    border: 1px solid #263246;
    border-left: 4px solid #34D399;
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
    width: 156px;
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
}
.player-headshot-img {
    height: 124px;
    width: auto;
    max-width: 156px;
    object-fit: contain;
    object-position: bottom center;
    display: block;
    margin: 0;
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
    font-family: monospace;
    font-size: 1.5rem;
    font-weight: 800;
    color: #94A3B8;
}
.player-modal-meta {
    padding-bottom: 14px;
    max-width: 100%;
    overflow-wrap: break-word;
}

/* Toned-Down, Cohesive Unit Ranking & Status Badges (No Leading Dots) */
.badge-elite {
    background-color: rgba(52, 211, 153, 0.10);
    color: #34D399;
    border: 1px solid rgba(52, 211, 153, 0.35);
    padding: 2px 7px;
    border-radius: 4px;
    font-size: 0.72rem;
    font-weight: 700;
    font-family: monospace;
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
    font-family: monospace;
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
    font-family: monospace;
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
    font-family: monospace;
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
    font-family: monospace;
    display: inline-block;
    margin: 1px 2px;
    max-width: 100%;
    overflow-wrap: anywhere;
}
.badge-sage {
    background-color: rgba(96, 165, 250, 0.10);
    color: #93C5FD;
    border: 1px solid rgba(96, 165, 250, 0.30);
    padding: 2px 7px;
    border-radius: 4px;
    font-size: 0.72rem;
    font-weight: 600;
    font-family: monospace;
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
    font-family: monospace;
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
    font-family: monospace;
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
    font-family: monospace;
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
    font-family: monospace;
    display: inline-flex;
    align-items: center;
    gap: 8px;
    margin: 0 4px;
}
.metric-subtext {
    font-size: 0.79rem;
    color: #94A3B8;
    font-family: monospace;
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
    font-family: monospace;
    font-weight: 700;
    color: #64748B;
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
    padding: 4px 0;
    font-size: 0.80rem;
    border-bottom: 1px dashed rgba(71, 85, 105, 0.28);
}
.unit-tier-label {
    color: #CBD5E1;
    font-family: monospace;
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
    font-family: monospace;
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
.brief-context-strip {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 10px;
    background-color: #151B26;
    border: 1px solid #232C3D;
    border-radius: 7px;
    padding: 9px 12px;
}
.context-cell-title {
    font-size: 0.70rem;
    font-family: monospace;
    color: #94A3B8;
    text-transform: uppercase;
    letter-spacing: 0.04em;
    margin-bottom: 3px;
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
    font-family: monospace;
    color: #94A3B8;
    margin-bottom: 3px;
    white-space: normal;
    line-height: 1.25;
}
.epa-stat-num {
    font-size: 1.32rem;
    font-weight: 800;
    font-family: monospace;
    color: #F8FAFC;
    line-height: 1.2;
    margin-bottom: 5px;
    white-space: nowrap;
}

/* Historical Injury Timeline Row Cards */
.injury-history-row {
    background-color: #141A24;
    border: 1px solid #242E3E;
    border-left: 3px solid #4B83BD;
    border-radius: 6px;
    padding: 8px 12px;
    margin-bottom: 7px;
    display: flex;
    justify-content: space-between;
    align-items: center;
    flex-wrap: wrap;
    gap: 8px;
}

/* DataFrames, Tables & Tabs Horizontal Scroll Protection */
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
}
button[data-baseweb="tab"] {
    flex-shrink: 0 !important;
    white-space: nowrap !important;
}

/* ============================================================================
   MOBILE & TABLET RESPONSIVE MEDIA QUERIES (MAX-WIDTH: 768PX & 480PX)
   Automatically stacks multi-column layouts vertically, wraps flex containers,
   prevents text/number clipping ('...'), and keeps ticker/tables scrollable.
   ============================================================================ */
@media (max-width: 768px) {
    /* Prevent page-level horizontal overflow and tighten container padding */
    .stApp, .main {
        max-width: 100vw !important;
        overflow-x: hidden !important;
    }
    .block-container {
        padding-left: 0.75rem !important;
        padding-right: 0.75rem !important;
        padding-top: 1.25rem !important;
        max-width: 100% !important;
    }

    /* Stack all standard Streamlit multi-column blocks vertically on mobile
       EXCEPT the horizontal game ticker strip (.nfl-ticker-marker) */
    div[data-testid="stHorizontalBlock"]:not(:has(.nfl-ticker-marker)) {
        flex-direction: column !important;
        flex-wrap: wrap !important;
        gap: 0.55rem !important;
    }
    div[data-testid="stHorizontalBlock"]:not(:has(.nfl-ticker-marker)) > div[data-testid="stColumn"],
    div[data-testid="stHorizontalBlock"]:not(:has(.nfl-ticker-marker)) > div[data-testid="column"] {
        width: 100% !important;
        min-width: 100% !important;
        max-width: 100% !important;
        flex: 1 1 100% !important;
    }

    /* Keep the weekly game ticker horizontally scrollable with compact mobile cards */
    div[data-testid="stHorizontalBlock"]:has(.nfl-ticker-marker) {
        flex-direction: row !important;
        flex-wrap: nowrap !important;
        overflow-x: auto !important;
        gap: 6px !important;
        padding: 6px 6px 10px 6px !important;
    }
    div[data-testid="stHorizontalBlock"]:has(.nfl-ticker-marker) > div[data-testid="stColumn"],
    div[data-testid="stHorizontalBlock"]:has(.nfl-ticker-marker) > div[data-testid="column"] {
        flex: 0 0 166px !important;
        min-width: 166px !important;
        max-width: 166px !important;
        width: 166px !important;
    }

    /* Stack CSS Grid pillars (Unit Tier Matrix & Context Strip) into 1 column */
    .brief-grid,
    .brief-context-strip {
        grid-template-columns: 1fr !important;
        gap: 8px !important;
    }

    /* Compact EPA stat boxes on mobile so numbers never clip */
    .epa-stat-num {
        font-size: 1.12rem !important;
    }
    .epa-stat-box {
        padding: 7px 8px !important;
    }

    /* Adjust active matchup spotlight banner & team pills for mobile widths */
    .active-game-spotlight {
        padding: 12px 12px !important;
    }
    .team-pill-lg {
        font-size: 0.98rem !important;
        padding: 4px 9px !important;
        margin: 2px 2px !important;
    }
    .team-pill {
        font-size: 0.78rem !important;
        padding: 2px 7px !important;
    }

    /* Convert the 1-on-1 CB vs WR 'VS' column into a clean mobile divider */
    .cb-wr-vs-divider {
        padding: 4px 0 !important;
        margin: 2px 0 !important;
        text-align: left !important;
        font-size: 0.76rem !important;
        border-top: 1px dashed #232C3D;
        border-bottom: 1px dashed #232C3D;
    }

    /* Left-align right-aligned badge groups when columns stack vertically */
    div[data-testid="stColumn"] div[style*="text-align:right"],
    div[data-testid="column"] div[style*="text-align:right"] {
        text-align: left !important;
        padding-top: 2px !important;
    }

    /* Responsive Player Pop-Out Dossier Header */
    .player-modal-banner {
        padding: 12px 14px 4px 14px !important;
        gap: 10px !important;
    }
    .player-modal-left {
        flex-direction: column !important;
        align-items: flex-start !important;
        gap: 8px !important;
    }
    .player-headshot-wrap {
        width: 116px !important;
        height: 94px !important;
    }
    .player-headshot-img {
        height: 94px !important;
        max-width: 116px !important;
    }

    /* Compact badges, metric subtext & st.metric values so nothing clips with '...' */
    .badge-elite,
    .badge-cleared,
    .badge-mid,
    .badge-bad,
    .badge-amber,
    .badge-sage,
    .badge-hot,
    .badge-cold {
        font-size: 0.68rem !important;
        padding: 2px 6px !important;
        white-space: normal !important;
    }
    .metric-subtext {
        font-size: 0.75rem !important;
        line-height: 1.36 !important;
    }
    div[data-testid="stMetricValue"],
    div[data-testid="stMetricValue"] > div {
        font-size: 1.15rem !important;
        line-height: 1.22 !important;
        white-space: normal !important;
        overflow: visible !important;
        text-overflow: clip !important;
    }
    div[data-testid="stMetricDelta"],
    div[data-testid="stMetricDelta"] > div {
        font-size: 0.74rem !important;
        white-space: normal !important;
        overflow: visible !important;
        text-overflow: clip !important;
    }
}

@media (max-width: 480px) {
    .block-container {
        padding-left: 0.5rem !important;
        padding-right: 0.5rem !important;
    }
    .terminal-card,
    .terminal-card-elite,
    .terminal-card-vuln {
        padding: 10px 12px !important;
    }
    .mismatch-headshot-wrap,
    .mismatch-headshot-img,
    .mismatch-headshot-fallback {
        width: 42px !important;
        height: 42px !important;
    }
    div[data-testid="stMetricValue"],
    div[data-testid="stMetricValue"] > div {
        font-size: 1.06rem !important;
    }
    .epa-stat-num {
        font-size: 1.02rem !important;
    }
    button[kind="tertiary"],
    button[kind="tertiary"] p {
        font-size: 0.84rem !important;
    }
    button[data-baseweb="tab"] {
        padding-left: 10px !important;
        padding-right: 10px !important;
        font-size: 0.82rem !important;
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

if "injury_status_overrides" not in st.session_state:
    st.session_state["injury_status_overrides"] = {}
if "injury_refresh_token" not in st.session_state:
    st.session_state["injury_refresh_token"] = 0

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
) -> None:
    """
    Renders a native Streamlit tertiary button styled as an underlined inline text link.
    Clicking the player's name directly opens the pop-out dossier in-place.
    """
    clean_p = str(player_name).strip()
    if not clean_p or "Rotation" in clean_p:
        st.markdown(f"**{clean_p}** {extra_label}")
        return
    disp_text = f"{clean_p} {extra_label}".strip()
    if st.button(
        disp_text,
        key=f"inline_plr_{key_suffix}_{clean_p}_{team_abbr}",
        type="tertiary",
    ):
        trigger_player_popup(clean_p, team_abbr, pos)
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


def render_team_pill(team_abbr: str, role_tag: str = "", large: bool = False) -> str:
    """Renders an inline HTML team pill with embedded logo and optional clean record/role tag."""
    logo = get_team_logo_url(team_abbr)
    cls = "team-pill-lg" if large else "team-pill"
    img_sz = 28 if large else 17
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
    Renders standardized unit ranking tags without leading dots:
    - Top 5 (1-5): ELITE [#X]
    - Bottom 10 (23-32): BAD [#X]
    - Middle Tier (6-22): MID [#X]
    """
    lbl = f"{prefix} " if prefix else ""
    if rank <= 5:
        return f'<span class="badge-elite">{lbl}ELITE [#{rank}]</span>'
    if rank >= 23:
        return f'<span class="badge-bad">{lbl}BAD [#{rank}]</span>'
    return f'<span class="badge-mid">{lbl}MID [#{rank}]</span>'


def is_active_unresolved_injury(status_str: str) -> bool:
    """
    Strict gate helper: Returns True ONLY when a player's status is an active,
    unresolved injury designation ('OUT', 'DOUBTFUL', 'QUESTIONABLE', 'IR', 'PUP',
    'SUSPENDED', 'NFI', 'UNSPECIFIED (DNP)', 'UNSPECIFIED (LP)').
    Players who did not practice (DNP) or were limited (LP) with an Unspecified
    mid-week game status are NEVER treated as cleared.
    """
    if not status_str or pd.isna(status_str):
        return False
    s_clean = str(status_str).strip().upper()
    if s_clean in CLEARED_DESIGNATIONS or "CLEARED" in s_clean or "PLAYED" in s_clean:
        return False
    return s_clean in ACTIVE_INJURY_DESIGNATIONS


def is_unavailable_injury(status_str: str) -> bool:
    """
    Strict gate helper: Returns True ONLY when a player is ruled out or doubtful
    ('OUT', 'DOUBTFUL', 'IR', 'PUP', 'SUSPENDED', 'NFI').
    """
    if not status_str or pd.isna(status_str):
        return False
    s_clean = str(status_str).strip().upper()
    if s_clean in CLEARED_DESIGNATIONS or "CLEARED" in s_clean or "PLAYED" in s_clean:
        return False
    return s_clean in UNAVAILABLE_DESIGNATIONS


def extract_combined_injury_name(row: pd.Series) -> str:
    """
    Combines report_primary_injury / practice_primary_injury and secondary injury columns
    so mid-week practice report ailments (e.g., 'Knee / Toe', 'Shoulder / Foot', 'Ankle')
    never disappear when report_primary_injury is blank before Friday's final report.
    """
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
    """
    Normalizes raw nflverse injury designations and practice participation:
    - Official game designations ('OUT', 'DOUBTFUL', 'QUESTIONABLE', 'IR', 'PUP') take priority.
    - When game status is blank / 'Unspecified' mid-week:
        * DNP ('Did Not Participate') -> 'UNSPECIFIED (DNP)' (Active unresolved injury; NOT cleared)
        * LP ('Limited Participation') -> 'UNSPECIFIED (LP)' (Active unresolved injury; NOT cleared)
        * FP ('Full Participation') -> 'UNSPECIFIED (FP)' (Full practice participant; 0 EPA drag)
    """
    if pd.isna(raw_status):
        s_clean = ""
    else:
        s_clean = str(raw_status).strip().upper()
        if s_clean in ["NAN", "NONE", "NULL", "--", "-", "UNSPECIFIED"]:
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

    # When official game status is Unspecified (mid-week Mon/Tue/Wed/Thu injury reports):
    if not s_clean:
        if "DID NOT" in p_clean or "DNP" in p_clean:
            return "UNSPECIFIED (DNP)"
        if "LIMITED" in p_clean or p_clean == "LP":
            return "UNSPECIFIED (LP)"
        if "FULL" in p_clean or p_clean == "FP":
            return "UNSPECIFIED (FP)"
        return "UNSPECIFIED (LP)"

    return s_clean


def render_injury_badge(status: str) -> str:
    """Renders an HTML badge for official NFL injury report designations without leading dots."""
    status_clean = str(status).strip().upper()
    if status_clean == "UNSPECIFIED (DNP)":
        return '<span class="badge-bad">[UNSPECIFIED • DNP]</span>'
    if status_clean == "UNSPECIFIED (LP)":
        return '<span class="badge-amber">[UNSPECIFIED • LP]</span>'
    if status_clean == "UNSPECIFIED (FP)":
        return '<span class="badge-sage">[UNSPECIFIED • FP]</span>'
    if status_clean in CLEARED_DESIGNATIONS or "CLEARED" in status_clean or "PLAYED" in status_clean:
        return '<span class="badge-elite">[ACTIVE / CLEARED]</span>'
    if status_clean in ["OUT", "IR", "PUP", "SUSPENDED", "NFI"]:
        return f'<span class="badge-bad">[{status_clean}]</span>'
    if status_clean == "DOUBTFUL":
        return f'<span class="badge-bad">[{status_clean}]</span>'
    if status_clean == "QUESTIONABLE":
        return f'<span class="badge-amber">[{status_clean}]</span>'
    return f'<span class="badge-mid">[{status_clean}]</span>'


def render_practice_badge(practice_status: str) -> str:
    """Renders a clean tag badge for weekly practice participation (FP, LP, DNP)."""
    if pd.isna(practice_status) or not str(practice_status).strip():
        return '<span class="badge-mid">[PRACTICE: N/A]</span>'
    p_clean = str(practice_status).strip().upper()
    if p_clean in ["NAN", "NONE", "NULL"]:
        return '<span class="badge-mid">[PRACTICE: N/A]</span>'
    if "FULL" in p_clean or p_clean == "FP":
        return '<span class="badge-elite">[FP]</span>'
    if "LIMITED" in p_clean or p_clean == "LP":
        return '<span class="badge-amber">[LP]</span>'
    if "DID NOT" in p_clean or "DNP" in p_clean or "NONE" in p_clean:
        return '<span class="badge-bad">[DNP]</span>'
    return f'<span class="badge-mid">[{p_clean}]</span>'


def classify_primetime_code(row: pd.Series) -> str:
    """Detects compact broadcast tags ([TNF], [SNF], [MNF], [SPC])."""
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
    """Returns a clean, uniform slate badge for broadcast slots."""
    if slot_code in ["[TNF]", "[SNF]", "[MNF]", "[SPC]"]:
        return f'<span class="ticker-slot-tag">{slot_code}</span>'
    return '<span class="ticker-score-muted">[SUN]</span>'


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


def render_nfl_horizontal_ticker(
    week_games: pd.DataFrame, team_records: dict[str, str]
) -> None:
    """Renders the horizontally scrollable weekly game strip at the top of the page."""
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
                    <div class="ticker-team-row">
                        <span class="ticker-team-left">
                            <img src="{away_logo}" width="17" height="17" onerror="this.style.display='none'">
                            <span>{away_tm}</span>
                            <span class="ticker-team-record">({away_rec})</span>
                        </span>
                        {a_score_html}
                    </div>
                    <div class="ticker-team-row">
                        <span class="ticker-team-left">
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
            btn_label = (
                f"[ACTIVE: {away_tm} @ {home_tm}]"
                if is_selected
                else f"{away_tm} @ {home_tm}"
            )
            if st.button(
                btn_label,
                key=f"ticker_btn_{game_id}_{idx}",
                type="primary" if is_selected else "secondary",
                use_container_width=True,
            ):
                st.session_state["selected_game"] = game_id
                st.session_state["selected_game_idx"] = idx
                st.session_state["_user_manually_picked_game"] = True
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
    """
    Automatically selects the active/upcoming NFL week:
    1. First week that has unplayed games (no final score) or upcoming kickoff >= now.
    2. Otherwise, first week with gameday >= today.
    3. Otherwise, the final week of the season.
    """
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
    """
    Within the selected week's games, automatically defaults to the next upcoming
    or active game rather than lingering on already-completed games (like finished TNF).
    """
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
    """
    Evaluates a player's Last 3 Games (L3) output against their season baseline
    using clean tag badges without leading dots.
    """
    diff = l3_avg - season_avg
    rel_pct = (diff / season_avg * 100.0) if season_avg > 0.25 else (diff * 100.0)

    if is_negative_stat:
        if diff >= 0.35:
            return (
                f'<span class="badge-bad">[TURNOVER SPIKE: L3 {l3_avg:.2f}/g vs {season_avg:.2f} Avg]</span>',
                f"{diff:+.2f} vs Season Avg",
            )
        if diff <= -0.25:
            return (
                f'<span class="badge-elite">[CLEAN POCKET: L3 {l3_avg:.2f}/g vs {season_avg:.2f} Avg]</span>',
                f"{diff:+.2f} vs Season Avg",
            )
        return (
            f'<span class="badge-mid">[STEADY RATE: L3 {l3_avg:.2f}/g]</span>',
            f"{diff:+.2f} vs Season Avg",
        )

    if rel_pct >= 15.0 or (season_avg < 1.5 and diff >= 0.35):
        return (
            f'<span class="badge-hot">[HOT L3: {l3_avg:.1f} vs {season_avg:.1f} Avg]</span>',
            f"{diff:+.1f} L3 Surge ({rel_pct:+.0f}%)",
        )
    if rel_pct <= -15.0 or (season_avg < 1.5 and diff <= -0.35):
        return (
            f'<span class="badge-cold">[COLD L3: {l3_avg:.1f} vs {season_avg:.1f} Avg]</span>',
            f"{diff:+.1f} L3 Dip ({rel_pct:+.0f}%)",
        )
    return (
        f'<span class="badge-sage">[STEADY L3: {l3_avg:.1f} vs {season_avg:.1f} Avg]</span>',
        f"{diff:+.1f} vs Season Avg",
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
        df["away_label"] = df["away_team"].astype(str)
        df["home_label"] = df["home_team"].astype(str)

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


@st.cache_data(ttl=300)
def load_injuries_csv(season: int, refresh_token: int = 0) -> tuple[pd.DataFrame, int]:
    """
    Fetches official weekly NFL injury reports AND weekly roster reserve status feeds via pd.read_csv.
    Preserves mid-week DNP/LP practice statuses when official game status is Unspecified.
    """
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
            usecols=lambda c: c in ["full_name", "player_name", "team", "position", "week", "status", "status_description_abbr"],
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

        # Only use weekly_rosters to catch reserve/inactive list placements (IR, PUP, NFI, INA).
        # Never let 'ACT' (on 53-man active roster) overwrite a mid-week DNP/LP practice report!
        if not wr_df.empty and "week" in wr_df.columns and "status" in wr_df.columns:
            wr_name_col = "full_name" if "full_name" in wr_df.columns else "player_name"
            if wr_name_col in wr_df.columns:
                wr_df["clean_name"] = wr_df[wr_name_col].astype(str).str.strip().str.lower()
                wr_df["team"] = wr_df["team"].astype(str).str.strip().str.upper()
                wr_df["week"] = pd.to_numeric(wr_df["week"], errors="coerce").fillna(0).astype(int)
                wr_sub = wr_df.drop_duplicates(subset=["team", "clean_name", "week"], keep="last")
                inj_df = inj_df.merge(
                    wr_sub[["team", "clean_name", "week", "status"]],
                    on=["team", "clean_name", "week"],
                    how="left",
                    suffixes=("", "_roster"),
                )
                roster_st = inj_df["status"].fillna("").astype(str).str.upper()
                inj_df.loc[roster_st.isin(["RES", "IR", "PUP", "NFI"]), "normalized_status"] = "IR"
                inj_df.loc[roster_st.isin(["INA", "OUT"]), "normalized_status"] = "OUT"

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

                lookup: dict[str, dict] = {}
                for _, r in df.dropna(subset=[name_col]).iterrows():
                    nm = str(r[name_col]).strip()
                    clean_nm = nm.lower()
                    tm = str(r.get("team", "")).strip().upper()
                    pos = str(r.get("position", "")).strip().upper()
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
    Renders a clean 48x48px player headshot box for mismatch and pick cards,
    with graceful fallback to monogram initials if a photo is unavailable.
    """
    clean_p = str(player_name).strip()
    initials = "".join([part[0].upper() for part in clean_p.split()[:2] if part]) or "NFL"
    h_url, _ = get_player_headshot_and_meta(clean_p, team_abbr, headshot_lookup)
    if h_url and "Rotation" not in clean_p:
        return (
            f'<div class="mismatch-headshot-wrap">'
            f'<img src="{h_url}" class="mismatch-headshot-img" alt="{clean_p}" '
            f'onerror="this.style.display=\'none\'; this.parentElement.innerHTML=\'<div class=mismatch-headshot-fallback>{initials}</div>\';">'
            f"</div>"
        )
    return (
        f'<div class="mismatch-headshot-wrap">'
        f'<div class="mismatch-headshot-fallback">{initials}</div>'
        f"</div>"
    )


# -----------------------------------------------------------------------------
# 3. ANALYTICS, TOP 3 PLAYER PICKS, CB vs WR MISMATCH, H2H, ROSTER & BACKTEST
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
    """Prepares week-by-week player game logs for the selected matchup teams."""
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


def build_top_player_picks(
    usage_df: pd.DataFrame,
    prop_logs: pd.DataFrame,
    inj_df: pd.DataFrame,
    eff_df: pd.DataFrame,
    away_tm: str,
    home_tm: str,
) -> list[dict]:
    """
    Evaluates all available skill players (WR, RB, QB, TE) across both teams in the selected
    matchup and surfaces the Top 3 projected player picks based on model edge, target/touch
    share, recent L3 form, and opposing defensive unit favorability.
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
            if is_unavailable_injury(st_i):
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

            vol_pts = float(np.clip((tgt_sh - 15.0) * 0.65, -4.0, 12.0))
            prod_pts = float(np.clip((rec_ypg - 45.0) * 0.20, -4.0, 10.0))
            air_pts = float(np.clip((air_sh - 22.0) * 0.12, -1.5, 3.5)) if p_pos == "WR" else 1.0
            def_pts = float(np.clip(((opp_pass_rk - 16.5) / 15.5) * 14.0, -12.0, 14.0))
            form_pts = float(np.clip((l3_val - season_val) * 0.25, -5.0, 6.5))
            epa_pts = float(np.clip(epa_pg * 1.5, -2.5, 4.0))
            score += vol_pts + prod_pts + air_pts + def_pts + form_pts + epa_pts

            usage_tag = f"[{tgt_sh:.1f}% TGT SHARE]"
            matchup_tag = f"[VS #{opp_pass_rk} {opp_tm} PASS DEF]"
            rationale = (
                f"{tgt_sh:.1f}% tgt share ({rec_ypg:.1f} YPG, {l3_val:.1f} L3) "
                f"vs #{opp_pass_rk} {opp_tm} pass def ({opp_pass_epa:+.2f} EPA)."
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

            vol_pts = float(np.clip((rush_sh - 38.0) * 0.28 + (touches_pg - 12.0) * 0.55, -5.0, 13.0))
            prod_pts = float(np.clip((season_val - 55.0) * 0.16, -4.0, 9.5))
            def_pts = float(np.clip(((opp_rush_rk - 16.5) / 15.5) * 14.0, -12.0, 14.0))
            form_pts = float(np.clip((l3_val - season_val) * 0.22, -5.0, 6.0))
            epa_pts = float(np.clip(epa_pg * 1.4, -2.5, 4.0))
            score += vol_pts + prod_pts + def_pts + form_pts + epa_pts

            usage_tag = f"[{touches_pg:.1f} TOUCHES/G • {rush_sh:.0f}% RUSH]"
            matchup_tag = f"[VS #{opp_rush_rk} {opp_tm} RUSH DEF]"
            rationale = (
                f"{touches_pg:.1f} touches/g ({season_val:.1f} YPG, {l3_val:.1f} L3) "
                f"vs #{opp_rush_rk} {opp_tm} rush def ({opp_rush_epa:+.2f} EPA)."
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

            prod_pts = float(np.clip((pass_ypg - 225.0) * 0.14 + (rush_ypg * 0.12), -5.0, 12.0))
            def_pts = float(np.clip(((opp_pass_rk - 16.5) / 15.5) * 14.5, -12.0, 14.5))
            form_pts = float(np.clip((l3_val - season_val) * 0.10, -4.5, 5.5))
            epa_pts = float(np.clip(epa_pg * 1.2, -3.5, 6.0))
            score += prod_pts + def_pts + form_pts + epa_pts

            usage_tag = f"[{pass_ypg:.1f} PASS YPG]"
            matchup_tag = f"[VS #{opp_pass_rk} {opp_tm} PASS DEF]"
            rationale = (
                f"{pass_ypg:.1f} pass YPG ({l3_val:.1f} L3, {epa_pg:+.2f} EPA/g) "
                f"vs #{opp_pass_rk} {opp_tm} pass def ({opp_pass_epa:+.2f} EPA)."
            )

        if (p_tm, p_clean) in questionable_players:
            score -= 5.5

        score = float(np.clip(round(score, 1), 25.0, 96.0))
        hit_pct = (hits / n_g * 100.0) if n_g > 0 else 0.0

        picks.append(
            {
                "player_name": p_name,
                "team": p_tm,
                "opp_team": opp_tm,
                "position": p_pos,
                "edge_score": score,
                "play_label": f"OVER {line_val:.1f} {mkt_label}",
                "hit_record": f"{hits}/{n_g} ({hit_pct:.0f}%)",
                "usage_tag": usage_tag,
                "matchup_tag": matchup_tag,
                "rationale": rationale,
            }
        )

    picks_sorted = sorted(picks, key=lambda x: x["edge_score"], reverse=True)
    return picks_sorted[:3]


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
    Calibrated 1-on-1 Wide Receiver vs. Cornerback Mismatch Engine (0-100 scale).
    """
    if usage_df.empty:
        return []

    unavailable_off_players: set[str] = set()
    if not inj_df.empty and "team" in inj_df.columns:
        o_inj = inj_df[inj_df["team"] == off_tm]
        for _, r_o in o_inj.iterrows():
            st_o = str(r_o.get("report_status", "")).strip().upper()
            if is_unavailable_injury(st_o):
                unavailable_off_players.add(str(r_o.get("player_display", "")).strip().lower())

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

    sec_inj_map: dict[str, tuple[str, str]] = {}
    if not inj_df.empty and "team" in inj_df.columns:
        d_inj = inj_df[inj_df["team"] == def_tm].copy()
        for _, r_i in d_inj.iterrows():
            c_nm = str(r_i.get("player_display", "")).strip().lower()
            st_str = str(r_i.get("report_status", "")).strip().upper()
            inj_type = str(r_i.get("primary_injury", "")).strip()
            sec_inj_map[c_nm] = (st_str, inj_type)

    active_cbs = []
    missing_starting_cbs = []

    if not cb_roster.empty:
        for _, cb_row in cb_roster.iterrows():
            c_nm = cb_row["clean_name"]
            snap_sh = float(cb_row["def_snap_share"])
            p_disp = cb_row["player"]
            pos_u = cb_row["pos_upper"]
            raw_inj_status, inj_desc = sec_inj_map.get(c_nm, ("ACTIVE", ""))

            if is_unavailable_injury(raw_inj_status) and snap_sh >= 0.50:
                missing_starting_cbs.append(
                    {
                        "name": p_disp,
                        "status": raw_inj_status,
                        "snap_pct": snap_sh * 100.0,
                        "injury": inj_desc,
                    }
                )
            elif not is_unavailable_injury(raw_inj_status):
                if is_active_unresolved_injury(raw_inj_status):
                    resolved_status = raw_inj_status
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

    alignments = ["Alpha Perimeter (X)", "Flanker / Field (Z)", "Slot / Motion (Y)"]
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
            tier_badge = '<span class="badge-elite">[ELITE MISMATCH]</span>'
            tier_plain = "[ELITE MISMATCH]"
            card_style = "terminal-card-elite"
        elif score >= 60.0:
            tier_badge = '<span class="badge-sage">[ADVANTAGE WR]</span>'
            tier_plain = "[ADVANTAGE WR]"
            card_style = "terminal-card"
        elif score <= 40.0:
            tier_badge = '<span class="badge-bad">[CB LOCKDOWN SPOT]</span>'
            tier_plain = "[CB LOCKDOWN SPOT]"
            card_style = "terminal-card-vuln"
        else:
            tier_badge = '<span class="badge-mid">[NEUTRAL BATTLE]</span>'
            tier_plain = "[NEUTRAL BATTLE]"
            card_style = "terminal-card"

        if streak_type == "HOT":
            wr_streak_badge = f'<span class="badge-hot">[WR HOT L4: {l4_val:.1f} YPG ({diff_yds:+.1f})]</span>'
        elif streak_type == "WARM":
            wr_streak_badge = f'<span class="badge-amber">[WR L4 UPTICK: {l4_val:.1f} YPG ({diff_yds:+.1f})]</span>'
        elif streak_type == "COLD":
            wr_streak_badge = f'<span class="badge-cold">[WR COLD L4: {l4_val:.1f} YPG ({diff_yds:+.1f})]</span>'
        else:
            wr_streak_badge = f'<span class="badge-mid">[WR L4: {l4_val:.1f} YPG]</span>'

        if missing_starting_cbs and idx < len(missing_starting_cbs):
            cb_status_badge = '<span class="badge-bad">[BACKUP CB ELEVATED]</span>'
        elif cb_has_active_inj:
            cb_status_badge = f'<span class="badge-amber">[CB {cb_assigned["status"]}]</span>'
        elif def_pass_rk <= 5:
            cb_status_badge = f'<span class="badge-bad">[SHUTDOWN CB • {cb_assigned["snap_pct"]:.0f}% SNAPS]</span>'
        elif cb_assigned["status"] == "ACTIVE / CLEARED":
            cb_status_badge = f'<span class="badge-elite">[CB CLEARED / ACTIVE • {cb_assigned["snap_pct"]:.0f}% SNAPS]</span>'
        else:
            cb_status_badge = f'<span class="badge-mid">[ACTIVE • {cb_assigned["snap_pct"]:.0f}% DEF SNAPS]</span>'

        if not rationale_clauses:
            clr_prefix = "CB full practice (0 inj drag) • " if cb_assigned["status"] == "ACTIVE / CLEARED" else ""
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

    merged["position"] = merged["position"].astype(str).strip() if isinstance(merged["position"], str) else merged["position"].astype(str).str.strip().str.upper()
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
            if not is_active_unresolved_injury(st_v):
                status_map[(tm_k, nm_k)] = f"[{st_v}]{suffix}"
            else:
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
    status_overrides: dict[str, str] | None = None,
    game_is_completed: bool = False,
    snaps_season_matches: bool = False,
) -> pd.DataFrame:
    """
    Cross-references official weekly injury designations and mid-week practice participation
    with snap counts and manual overrides.
    - Players who are DNP or LP mid-week with 'Unspecified' game status remain flagged as
      active unresolved injuries ('UNSPECIFIED (DNP)' / 'UNSPECIFIED (LP)') and are NEVER
      auto-cleared.
    - Reads both report_primary_injury and practice_primary_injury so mid-week injury names
      (e.g., Knee, Ankle, Shoulder / Foot, Hamstring) are always preserved.
    """
    status_overrides = status_overrides or {}

    if injuries_df.empty or "team" not in injuries_df.columns:
        team_inj = pd.DataFrame()
    else:
        team_inj = injuries_df[injuries_df["team"].isin(teams)].copy()

    if not team_inj.empty and "week" in team_inj.columns:
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

    # Only check on-field snap completion if the selected game is already final AND
    # the loaded snap dataset is from the exact same season.
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

    if team_inj.empty and not status_overrides:
        return pd.DataFrame()

    if not team_inj.empty:
        name_col = "full_name" if "full_name" in team_inj.columns else "player_name"
        team_inj["clean_name"] = team_inj[name_col].astype(str).str.strip().str.lower()
        team_inj["player_display"] = team_inj[name_col].astype(str).str.strip()

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
            override_key = f"{nm_l}|{tm_u}"

            if override_key in status_overrides:
                ov_st = status_overrides[override_key].strip().upper()
                updated_statuses.append(ov_st)
                status_notes.append("Real-Time Manual Override Applied")
            elif (tm_u, nm_l) in played_in_selected_week:
                updated_statuses.append("ACTIVE / CLEARED")
                status_notes.append(f"Confirmed Active on Field (Wk {selected_week} Snaps Logged)")
            else:
                updated_statuses.append(cur_st)
                status_notes.append(
                    "Full Practice Participant"
                    if not is_active_unresolved_injury(cur_st)
                    else "Official NFL Injury / Practice Report"
                )

        team_inj["report_status"] = updated_statuses
        team_inj["status_source_note"] = status_notes
    else:
        team_inj = pd.DataFrame(
            columns=[
                "team",
                "clean_name",
                "player_display",
                "position",
                "report_status",
                "practice_status_clean",
                "combined_injury_desc",
                "status_source_note",
            ]
        )

    for ov_key, ov_status in status_overrides.items():
        if "|" not in ov_key:
            continue
        nm_l, tm_u = ov_key.split("|", 1)
        if tm_u not in teams:
            continue
        exists_mask = (team_inj["team"] == tm_u) & (team_inj["clean_name"] == nm_l) if not team_inj.empty else pd.Series([], dtype=bool)
        if not exists_mask.any():
            disp_nm = nm_l.title()
            pos_guess = "UNK"
            if not usage_df.empty:
                u_m = usage_df[(usage_df["team"] == tm_u) & (usage_df["player_name"].astype(str).str.lower() == nm_l)]
                if not u_m.empty:
                    disp_nm = str(u_m.iloc[0]["player_name"])
                    pos_guess = str(u_m.iloc[0]["position"])
            new_row = pd.DataFrame(
                [
                    {
                        "team": tm_u,
                        "clean_name": nm_l,
                        "player_display": disp_nm,
                        "position": pos_guess,
                        "report_status": ov_status.strip().upper(),
                        "practice_status_clean": "Real-Time Override",
                        "combined_injury_desc": "Coach / Beat Update",
                        "status_source_note": "Real-Time Manual Override Applied",
                    }
                ]
            )
            team_inj = pd.concat([team_inj, new_row], ignore_index=True)

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
            roles.append("[FULL PRACTICE / 0 EPA DRAG]")
            penalty = 0.0
        else:
            if is_key_player:
                if pos in ["T", "LT", "RT", "G", "C"]:
                    roles.append("[STARTING OL ANCHOR]")
                elif pos == "WR" or tgt >= 0.18:
                    roles.append("[PRIMARY TARGET / WR1]")
                elif pos in ["DE", "EDGE", "DT"]:
                    roles.append("[PRIMARY PASS RUSHER]")
                elif pos in ["CB", "S"]:
                    roles.append("[STARTING COVERAGE ANCHOR]")
                elif pos == "QB":
                    roles.append("[STARTING QUARTERBACK]")
                else:
                    roles.append("[KEY STARTING ANCHOR]")
            elif snap >= 0.35 or tgt >= 0.10:
                roles.append("[ROTATIONAL CONTRIBUTOR]")
            else:
                roles.append("[DEPTH / SPECIAL TEAMS]")

            base_w = pos_weights.get(pos, 0.015)
            usage_boost = 1.35 if tgt >= 0.20 else (1.15 if snap >= 0.75 else 0.75)
            prob_miss = status_prob_missing.get(status_str, 0.0)
            penalty = round(base_w * snap * usage_boost * prob_miss, 3)

        epa_penalties.append(penalty)

        if pos in ["QB", "WR", "TE", "T", "LT", "RT", "G", "C", "RB"]:
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


def get_player_season_injury_history(
    injuries_df: pd.DataFrame,
    snaps_df: pd.DataFrame,
    player_name: str,
    team_abbr: str = "",
    status_overrides: dict[str, str] | None = None,
    selected_week: int | None = None,
) -> pd.DataFrame:
    """Extracts a player's week-by-week historical injury log across the entire season."""
    status_overrides = status_overrides or {}
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

            ov_key = f"{clean_nm}|{tm_r}"
            if selected_week is not None and wk == selected_week and ov_key in status_overrides:
                norm_st = status_overrides[ov_key].strip().upper()
                prac_st = f"{prac_st} (Manual Override)" if prac_st != "N/A" else "Manual Override"

            injury_ailment = extract_combined_injury_name(r)

            tot_snaps, snap_pct = snap_by_week.get(wk, (0, 0.0))
            if selected_week is not None and wk < selected_week and tot_snaps > 0:
                gameday_outcome = f"ACTIVE ({tot_snaps} Snaps / {snap_pct:.0f}%)"
                if norm_st in ["QUESTIONABLE", "DOUBTFUL", "UNSPECIFIED (DNP)", "UNSPECIFIED (LP)"]:
                    norm_st = f"{norm_st} -> PLAYED"
            elif norm_st in ["OUT", "IR", "PUP", "SUSPENDED", "NFI"]:
                gameday_outcome = "DID NOT PLAY (INACTIVE)"
            elif not is_active_unresolved_injury(norm_st):
                gameday_outcome = "FULL PRACTICE / AVAILABLE"
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
# 4. INTERACTIVE PLAYER POP-OUT MODAL (FLUSH HEADSHOT + CONCISE TABS)
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
    """Renders the player pop-out dossier with concise tab names."""
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
            f'onerror="this.style.display=\'none\'; this.parentElement.innerHTML=\'<div class=player-headshot-fallback>{initials}</div>\';">'
            f"</div>"
        )
    else:
        headshot_html = (
            f'<div class="player-headshot-wrap">'
            f'<div class="player-headshot-fallback">{initials}</div>'
            f"</div>"
        )

    player_inj_history = get_player_season_injury_history(
        injuries_full_df,
        snaps_df,
        p_name,
        p_team,
        st.session_state.get("injury_status_overrides", {}),
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
                    f'<span class="badge-mid">[{prim_inj_val}]</span> '
                    f'<span class="badge-sage">[0.000 EPA DRAG]</span> '
                    f'{current_prac_badge}'
                )
            else:
                inj_badge_html = (
                    f'{render_injury_badge(current_status_str)} '
                    f'<span class="badge-bad">[{prim_inj_val}]</span> '
                    f'{current_prac_badge}'
                )
        else:
            inj_badge_html = '<span class="badge-elite">[ACTIVE / CLEAN REPORT]</span>'
    else:
        inj_badge_html = '<span class="badge-elite">[ACTIVE / CLEAN REPORT]</span>'

    opp_tm = home_tm if p_team == away_tm else away_tm
    render_html(
        f"""
        <div class="player-modal-banner">
            <div class="player-modal-left">
                {headshot_html}
                <div class="player-modal-meta">
                    <div style="display:flex; align-items:center; flex-wrap:wrap; gap:6px;">
                        <span style="font-size:1.35rem; font-weight:800; color:#F8FAFC; font-family:monospace;">
                            {p_name}
                        </span>
                        {render_team_pill(p_team) if p_team else ""}
                        <span class="badge-sage">[{p_pos or "NFL"}]</span>
                        <span class="badge-mid">[{unit_side.upper()}]</span>
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

    hist_count = len(player_inj_history)
    tab_stats, tab_props, tab_inj_hist = st.tabs(
        [
            "Game Logs",
            "Props",
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

    with tab_stats:
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
            m1.metric("Games Active", f"{s_games} GP", delta=f"{s_tot_snaps} Snaps", delta_color="off")
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

            mc1, mc2 = st.columns([1.3, 1.3])
            with mc1:
                sel_mkt = st.selectbox(
                    "Prop Market",
                    options=market_keys,
                    index=default_idx,
                    key=f"modal_prop_mkt_{clean_nm}",
                )
            stat_col, def_l, max_cap, stp = PROP_MARKETS[sel_mkt]
            is_td_int = stat_col in ["anytime_td", "receiving_tds", "interceptions"]
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

            s_avg = float(p_logs[stat_col].mean())
            l3_avg = float(p_logs.tail(3)[stat_col].mean())
            streak_badge, streak_delta = evaluate_player_streak_badge(
                s_avg, l3_avg, is_negative_stat=(stat_col == "interceptions")
            )

            p_logs_chart = p_logs.copy()
            p_logs_chart["hit"] = p_logs_chart[stat_col] >= modal_line
            p_logs_chart["bar_color"] = np.where(p_logs_chart["hit"], "#34D399", "#F87171")
            p_logs_chart["rolling_avg"] = p_logs_chart[stat_col].expanding().mean()

            hits_n = int(p_logs_chart["hit"].sum())
            tot_n = len(p_logs_chart)
            hit_pct = (hits_n / tot_n * 100.0) if tot_n > 0 else 0.0

            opp_def_rk = 16
            if not eff_df.empty and opp_tm in eff_df.index:
                is_rush = stat_col in ["rushing_yards", "carries"]
                opp_def_rk = int(
                    eff_df.loc[opp_tm, "def_rush_epa_rank" if is_rush else "def_pass_epa_rank"]
                )

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
                f"vs {opp_tm} Defense",
                f"Rank #{opp_def_rk}",
                delta="Favorable" if opp_def_rk >= 23 else ("Tough" if opp_def_rk <= 5 else "Neutral"),
                delta_color="normal" if opp_def_rk >= 23 else ("inverse" if opp_def_rk <= 5 else "off"),
            )

            render_html(f'<div style="margin:4px 0 8px 0;">{streak_badge}</div>')

            fig_m = go.Figure()
            fig_m.add_trace(
                go.Bar(
                    x=p_logs_chart["game_tag"],
                    y=p_logs_chart[stat_col],
                    marker_color=p_logs_chart["bar_color"],
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
                    x=p_logs_chart["game_tag"],
                    y=p_logs_chart["rolling_avg"],
                    mode="lines+markers",
                    line=dict(color="#60A5FA", width=2, dash="dot"),
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
                paper_bgcolor="#121722",
                plot_bgcolor="#121722",
                font=dict(color="#E2E8F0"),
                xaxis=dict(title="Week & Opponent", gridcolor="#222B3A"),
                yaxis=dict(title=sel_mkt, range=[0, y_max], gridcolor="#222B3A"),
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                height=320,
                margin=dict(l=16, r=16, t=32, b=24),
            )
            st.plotly_chart(fig_m, width="stretch", key=f"modal_plotly_{clean_nm}_{stat_col}")

    with tab_inj_hist:
        ov_key = f"{clean_nm}|{p_team}"
        current_ov = st.session_state["injury_status_overrides"].get(ov_key, "Auto (Official Feed)")
        ov_options = [
            "Auto (Official Feed)",
            "ACTIVE / CLEARED",
            "UNSPECIFIED (DNP)",
            "UNSPECIFIED (LP)",
            "QUESTIONABLE",
            "DOUBTFUL",
            "OUT",
            "IR",
        ]
        ov_idx = ov_options.index(current_ov) if current_ov in ov_options else 0

        ov_col1, ov_col2 = st.columns([1.6, 1.4])
        with ov_col1:
            selected_ov = st.selectbox(
                f"Week {selected_week} Status Override",
                options=ov_options,
                index=ov_idx,
                key=f"dossier_ov_select_{clean_nm}_{p_team}",
            )
        with ov_col2:
            st.write("")
            if st.button(
                "Apply Status Update",
                key=f"dossier_ov_btn_{clean_nm}_{p_team}",
                type="primary",
                use_container_width=True,
            ):
                if selected_ov == "Auto (Official Feed)":
                    st.session_state["injury_status_overrides"].pop(ov_key, None)
                else:
                    st.session_state["injury_status_overrides"][ov_key] = selected_ov
                st.session_state["open_player_modal"] = True
                st.rerun()

        if player_inj_history.empty:
            render_html(
                f"""
                <div class="terminal-card-elite" style="margin-top:8px;">
                    <span class="badge-elite">[CLEAN {inj_season} INJURY LOG]</span>
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


# -----------------------------------------------------------------------------
# 5. SIDEBAR CONTROLS & AUTOMATIC NEXT GAME SELECTION
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
if st.sidebar.button(
    "Refresh Injury Feed",
    use_container_width=True,
):
    st.session_state["injury_refresh_token"] += 1
    load_injuries_csv.clear()
    st.rerun()

active_ov_count = len(st.session_state.get("injury_status_overrides", {}))
if active_ov_count > 0:
    st.sidebar.caption(f"`{active_ov_count}` status override(s) active.")
    if st.sidebar.button("Reset Overrides", use_container_width=True):
        st.session_state["injury_status_overrides"] = {}
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

# Automatically default to the next upcoming/unplayed game when loading or switching weeks/filters
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
team_records_map = compute_team_records(schedule_df, through_week=selected_week)

# -----------------------------------------------------------------------------
# 6. PINNED TOP VIEW: STREAMLINED HEADER & HORIZONTAL GAME TICKER
# -----------------------------------------------------------------------------
top_hdr_left, top_hdr_right = st.columns([1.4, 1])
with top_hdr_left:
    st.markdown(f"### Football Edger — {selected_season} Week {selected_week}")
with top_hdr_right:
    render_html(
        f'<div style="text-align:right; padding-top:8px;">'
        f'<span class="active-lock-pill">ACTIVE: {active_game["away_team"]} @ {active_game["home_team"]}</span>'
        f"</div>"
    )

render_nfl_horizontal_ticker(week_games, team_records_map)

# -----------------------------------------------------------------------------
# 7. DETAIL VIEW: STREAMLINED SELECTED MATCHUP SPOTLIGHT
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
active_game_is_completed = bool(pd.notna(away_pts) and pd.notna(home_pts))

spread_str = f"{home_tm} {spread_v:+.1f}" if pd.notna(spread_v) else "Spread TBD"
total_str = f"O/U {total_v:.1f}" if pd.notna(total_v) else "Total TBD"
final_score_badge = (
    f'<span class="badge-amber">[FINAL: {away_tm} {int(away_pts)} - {home_tm} {int(home_pts)}]</span>'
    if active_game_is_completed
    else '<span class="badge-elite">[UPCOMING]</span>'
)
slot_badge = f'<span class="badge-mid">{slot_str}</span>' if slot_str else ""

if pd.notna(rest_v) and rest_v > 0:
    rest_badge = f'<span class="badge-elite">[REST: {home_tm} +{int(rest_v)}d]</span>'
elif pd.notna(rest_v) and rest_v < 0:
    rest_badge = f'<span class="badge-elite">[REST: {away_tm} +{int(abs(rest_v))}d]</span>'
else:
    rest_badge = '<span class="badge-mid">[EVEN REST]</span>'

a_eff = eff_df.loc[away_tm] if away_tm in eff_df.index else None
h_eff = eff_df.loc[home_tm] if home_tm in eff_df.index else None
usage_matchup = aggregate_team_skill_usage(player_df, [away_tm, home_tm])
inj_matchup = build_injury_impact_report(
    injuries_df,
    snaps_df,
    usage_matchup,
    [away_tm, home_tm],
    selected_week,
    st.session_state.get("injury_status_overrides", {}),
    game_is_completed=active_game_is_completed,
    snaps_season_matches=(snaps_season == selected_season and snaps_season == inj_season),
)
h2h_5yr = get_five_year_h2h_history(master_games_df, away_tm, home_tm, selected_season)
roster_matchup_table = build_roster_usage_table(
    snaps_df, usage_matchup, [away_tm, home_tm], inj_matchup
)
prop_logs_matchup = prepare_matchup_player_prop_logs(player_df, [away_tm, home_tm])


def get_unit_penalty(tm: str, side: str) -> float:
    """Strictly sums unit EPA penalties ONLY for active unresolved injury designations."""
    if inj_matchup.empty:
        return 0.0
    sub = inj_matchup[
        (inj_matchup["team"] == tm)
        & (inj_matchup["unit_side"] == side)
        & (~inj_matchup["is_cleared"])
        & (inj_matchup["report_status"].apply(is_active_unresolved_injury))
    ]
    if sub.empty:
        return 0.0
    return float(sub["est_epa_penalty"].sum())


away_off_pen = get_unit_penalty(away_tm, "Offense")
away_def_pen = get_unit_penalty(away_tm, "Defense")
home_off_pen = get_unit_penalty(home_tm, "Offense")
home_def_pen = get_unit_penalty(home_tm, "Defense")

a_ovr_badge = render_rank_badge(int(a_eff["off_epa_rank"]), f"{away_tm} Off") if a_eff is not None else ""
a_def_badge = render_rank_badge(int(a_eff["def_epa_rank"]), f"{away_tm} Def") if a_eff is not None else ""
h_ovr_badge = render_rank_badge(int(h_eff["off_epa_rank"]), f"{home_tm} Off") if h_eff is not None else ""
h_def_badge = render_rank_badge(int(h_eff["def_epa_rank"]), f"{home_tm} Def") if h_eff is not None else ""

away_rec_str = team_records_map.get(str(away_tm).strip().upper(), "0-0")
home_rec_str = team_records_map.get(str(home_tm).strip().upper(), "0-0")

render_html(
    f"""
    <div class="active-game-spotlight">
        <div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:12px;">
            <div>
                <div style="display:flex; align-items:center; flex-wrap:wrap; gap:8px;">
                    {render_team_pill(away_tm, away_rec_str, large=True)}
                    <span style="font-size:1.1rem; font-weight:700; color:#64748B; font-family:monospace;">AT</span>
                    {render_team_pill(home_tm, home_rec_str, large=True)}
                    <span class="metric-subtext" style="margin-left:6px;">{stadium_str} ({roof_str})</span>
                </div>
                <div style="margin-top:8px;">
                    {a_ovr_badge} {a_def_badge}
                    <span style="color:#334155; margin:0 5px;">|</span>
                    {h_ovr_badge} {h_def_badge}
                </div>
            </div>
            <div style="display:flex; flex-direction:column; align-items:flex-end; gap:6px;">
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

# Shortened, Concise Main Sub-Tab Names
subtab_brief, subtab_players, subtab_trench, subtab_props, subtab_roster, subtab_backtest = st.tabs(
    [
        "Overview",
        "Mismatches",
        "Unit EPA",
        "Props",
        "Rosters",
        "Backtest",
    ]
)

# =============================================================================
# SUB-TAB 1: OVERVIEW (TEAM-OWNED UNIT TIER MATRIX + TOP 3 PICKS + 5-YR H2H)
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
                "Model Lean",
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
                "Top Schematic Lever",
                best_phase_val[0],
                delta=f"{best_phase_val[1]:+.3f} EPA Delta",
                delta_color="normal",
            )
        with k3:
            total_flagged_inj = int((~inj_matchup["is_cleared"]).sum()) if not inj_matchup.empty and "is_cleared" in inj_matchup.columns else 0
            cleared_count = int(inj_matchup["is_cleared"].sum()) if not inj_matchup.empty and "is_cleared" in inj_matchup.columns else 0
            st.metric(
                "Injury Report Status",
                f"{total_flagged_inj} Flagged",
                delta=f"{cleared_count} FP | {away_tm} -{away_off_pen + away_def_pen:.2f} / {home_tm} -{home_off_pen + home_def_pen:.2f} EPA",
                delta_color="inverse" if total_flagged_inj > 0 else "normal",
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
                    delta="No recent meetings",
                    delta_color="off",
                )

        col_brief_left, col_brief_right = st.columns([1.15, 1.05])

        top_inj_row = None
        if not inj_matchup.empty:
            active_inj_rows = inj_matchup[~inj_matchup["is_cleared"]]
            if not active_inj_rows.empty:
                top_inj_row = active_inj_rows.iloc[0]

        with col_brief_left:
            # Away Team's own Offense & Defense ranks
            a_pass_rk, a_rush_rk = int(a_eff["off_pass_epa_rank"]), int(a_eff["off_rush_epa_rank"])
            a_pdef_rk, a_rdef_rk = int(a_eff["def_pass_epa_rank"]), int(a_eff["def_rush_epa_rank"])
            a_ovr_off_rk, a_ovr_def_rk = int(a_eff["off_epa_rank"]), int(a_eff["def_epa_rank"])

            # Home Team's own Offense & Defense ranks
            h_pass_rk, h_rush_rk = int(h_eff["off_pass_epa_rank"]), int(h_eff["off_rush_epa_rank"])
            h_pdef_rk, h_rdef_rk = int(h_eff["def_pass_epa_rank"]), int(h_eff["def_rush_epa_rank"])
            h_ovr_off_rk, h_ovr_def_rk = int(h_eff["off_epa_rank"]), int(h_eff["def_epa_rank"])

            away_air_gap = h_pdef_rk - a_pass_rk
            away_grd_gap = h_rdef_rk - a_rush_rk
            if away_air_gap >= away_grd_gap:
                away_lever_tag = (
                    f'<span class="badge-elite">[PASS EDGE: {away_air_gap:+d} RK]</span>'
                    if away_air_gap >= 6
                    else f'<span class="badge-sage">[PASS OFF: {a_eff["off_pass_epa"]:+.2f} EPA]</span>'
                )
            else:
                away_lever_tag = (
                    f'<span class="badge-elite">[RUSH EDGE: {away_grd_gap:+d} RK]</span>'
                    if away_grd_gap >= 6
                    else f'<span class="badge-sage">[RUSH OFF: {a_eff["off_rush_epa"]:+.2f} EPA]</span>'
                )

            home_air_gap = a_pdef_rk - h_pass_rk
            home_grd_gap = a_rdef_rk - h_rush_rk
            if home_air_gap >= home_grd_gap:
                home_lever_tag = (
                    f'<span class="badge-elite">[PASS EDGE: {home_air_gap:+d} RK]</span>'
                    if home_air_gap >= 6
                    else f'<span class="badge-sage">[PASS OFF: {h_eff["off_pass_epa"]:+.2f} EPA]</span>'
                )
            else:
                home_lever_tag = (
                    f'<span class="badge-elite">[RUSH EDGE: {home_grd_gap:+d} RK]</span>'
                    if home_grd_gap >= 6
                    else f'<span class="badge-sage">[RUSH OFF: {h_eff["off_rush_epa"]:+.2f} EPA]</span>'
                )

            if pd.notna(rest_v) and abs(rest_v) >= 1:
                adv_rest_tm = home_tm if rest_v > 0 else away_tm
                rest_cell_html = (
                    f'{render_inline_logo(adv_rest_tm, 16)}<b>+{int(abs(rest_v))}d Rest Edge</b> '
                    f'<span class="metric-subtext">• {roof_str}</span>'
                )
            else:
                rest_cell_html = (
                    f'<span class="badge-mid">[EVEN REST]</span> '
                    f'<span class="metric-subtext">{stadium_str} ({roof_str})</span>'
                )

            if top_inj_row is not None:
                inj_link_html = render_player_link(
                    top_inj_row["player_display"],
                    top_inj_row["team"],
                    str(top_inj_row.get("position", "")),
                )
                inj_cell_html = (
                    f'{render_inline_logo(top_inj_row["team"], 16)}{inj_link_html} '
                    f'({top_inj_row.get("position", "POS")} • {top_inj_row.get("primary_injury", "")}) '
                    f'{render_injury_badge(top_inj_row["report_status"])} '
                    f'<span style="color:#F87171; font-family:monospace; font-weight:700;">-{top_inj_row["est_epa_penalty"]:.3f} EPA</span>'
                )
            else:
                inj_cell_html = '<span class="badge-elite">[ALL ANCHORS FULL PRACTICE]</span>'

            render_html(
                f"""
                <div class="terminal-card">
                    <div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:6px; margin-bottom:10px;">
                        <h4 style="margin:0; color:#F1F5F9;">Unit Tier Matrix</h4>
                        <span class="metric-subtext">Each Team's Own Offense & Defense Tiers</span>
                    </div>
                    <div class="brief-grid">
                        <div class="unit-pillar">
                            <div class="unit-pillar-header">
                                <span>{render_inline_logo(away_tm, 18)}{away_tm} ({away_rec_str})</span>
                                <span class="metric-subtext">Off #{a_ovr_off_rk} • Def #{a_ovr_def_rk}</span>
                            </div>
                            <div class="unit-section-tag">{away_tm} Offense</div>
                            <div class="unit-tier-row">
                                <span class="unit-tier-label">AIR OFF</span>
                                <span class="unit-tier-right">
                                    <span class="unit-epa-mini">{a_eff["off_pass_epa"]:+.2f} EPA</span>
                                    {render_rank_badge(a_pass_rk, f"{away_tm} Off")}
                                </span>
                            </div>
                            <div class="unit-tier-row">
                                <span class="unit-tier-label">GROUND OFF</span>
                                <span class="unit-tier-right">
                                    <span class="unit-epa-mini">{a_eff["off_rush_epa"]:+.2f} EPA</span>
                                    {render_rank_badge(a_rush_rk, f"{away_tm} Off")}
                                </span>
                            </div>
                            <div class="unit-section-tag" style="margin-top:8px;">{away_tm} Defense</div>
                            <div class="unit-tier-row">
                                <span class="unit-tier-label">AIR DEF</span>
                                <span class="unit-tier-right">
                                    <span class="unit-epa-mini">{a_eff["def_pass_epa"]:+.2f} EPA</span>
                                    {render_rank_badge(a_pdef_rk, f"{away_tm} Def")}
                                </span>
                            </div>
                            <div class="unit-tier-row">
                                <span class="unit-tier-label">GROUND DEF</span>
                                <span class="unit-tier-right">
                                    <span class="unit-epa-mini">{a_eff["def_rush_epa"]:+.2f} EPA</span>
                                    {render_rank_badge(a_rdef_rk, f"{away_tm} Def")}
                                </span>
                            </div>
                            <div class="unit-lever-footer">
                                <span class="metric-subtext">{away_tm} Lever</span>
                                {away_lever_tag}
                            </div>
                        </div>
                        <div class="unit-pillar">
                            <div class="unit-pillar-header">
                                <span>{render_inline_logo(home_tm, 18)}{home_tm} ({home_rec_str})</span>
                                <span class="metric-subtext">Off #{h_ovr_off_rk} • Def #{h_ovr_def_rk}</span>
                            </div>
                            <div class="unit-section-tag">{home_tm} Offense</div>
                            <div class="unit-tier-row">
                                <span class="unit-tier-label">AIR OFF</span>
                                <span class="unit-tier-right">
                                    <span class="unit-epa-mini">{h_eff["off_pass_epa"]:+.2f} EPA</span>
                                    {render_rank_badge(h_pass_rk, f"{home_tm} Off")}
                                </span>
                            </div>
                            <div class="unit-tier-row">
                                <span class="unit-tier-label">GROUND OFF</span>
                                <span class="unit-tier-right">
                                    <span class="unit-epa-mini">{h_eff["off_rush_epa"]:+.2f} EPA</span>
                                    {render_rank_badge(h_rush_rk, f"{home_tm} Off")}
                                </span>
                            </div>
                            <div class="unit-section-tag" style="margin-top:8px;">{home_tm} Defense</div>
                            <div class="unit-tier-row">
                                <span class="unit-tier-label">AIR DEF</span>
                                <span class="unit-tier-right">
                                    <span class="unit-epa-mini">{h_eff["def_pass_epa"]:+.2f} EPA</span>
                                    {render_rank_badge(h_pdef_rk, f"{home_tm} Def")}
                                </span>
                            </div>
                            <div class="unit-tier-row">
                                <span class="unit-tier-label">GROUND DEF</span>
                                <span class="unit-tier-right">
                                    <span class="unit-epa-mini">{h_eff["def_rush_epa"]:+.2f} EPA</span>
                                    {render_rank_badge(h_rdef_rk, f"{home_tm} Def")}
                                </span>
                            </div>
                            <div class="unit-lever-footer">
                                <span class="metric-subtext">{home_tm} Lever</span>
                                {home_lever_tag}
                            </div>
                        </div>
                    </div>
                    <div class="brief-context-strip">
                        <div>
                            <div class="context-cell-title">Environment</div>
                            <div>{rest_cell_html}</div>
                        </div>
                        <div>
                            <div class="context-cell-title">Key Lineup Status</div>
                            <div>{inj_cell_html}</div>
                        </div>
                    </div>
                </div>
                """
            )

        with col_brief_right:
            top_3_picks = build_top_player_picks(
                usage_matchup,
                prop_logs_matchup,
                inj_matchup,
                eff_df,
                away_tm,
                home_tm,
            )

            with st.container(border=True):
                render_html(
                    """
                    <div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:6px; margin-bottom:6px;">
                        <h4 style="margin:0; color:#F1F5F9;">Top 3 Player Picks</h4>
                        <span class="metric-subtext">WR • RB • QB • TE Model Plays</span>
                    </div>
                    """
                )
                if not top_3_picks:
                    st.info("Insufficient player usage data to rank top player picks.")
                else:
                    for p_idx, pick in enumerate(top_3_picks):
                        p_pic_html = render_mismatch_headshot_html(
                            pick["player_name"], pick["team"], headshot_lookup
                        )
                        edge_cls = "badge-elite" if pick["edge_score"] >= 70.0 else "badge-sage"
                        with st.container(border=True):
                            pk_top_l, pk_top_r = st.columns([1.45, 1.05])
                            with pk_top_l:
                                render_inline_player_trigger(
                                    pick["player_name"],
                                    pick["team"],
                                    pick["position"],
                                    f"top3_pick_{p_idx}",
                                    f"[PICK #{p_idx + 1} • {pick['team']} {pick['position']}]",
                                )
                            with pk_top_r:
                                render_html(
                                    f'<div style="text-align:right;">'
                                    f'<span class="{edge_cls}">[{pick["play_label"]}]</span> '
                                    f'<span class="badge-mid">[EDGE {pick["edge_score"]:.0f}]</span>'
                                    f"</div>"
                                )
                            render_html(
                                f"""
                                <div style="display:flex; align-items:center; gap:10px; margin-top:4px;">
                                    {p_pic_html}
                                    <div class="metric-subtext" style="line-height:1.38;">
                                        {pick["usage_tag"]} {pick["matchup_tag"]} <span class="badge-mid">[HIT: {pick["hit_record"]}]</span><br>
                                        <span style="color:#CBD5E1;">{pick["rationale"]}</span>
                                    </div>
                                </div>
                                """
                            )

        render_html(
            f"<h4 style='margin:12px 0 6px 0;'>"
            f"{render_inline_logo(away_tm, 20)}{away_tm} vs {render_inline_logo(home_tm, 20)}{home_tm} — "
            f"5-Year Matchup History ({selected_season - 5}–{selected_season})</h4>"
        )
        if h2h_5yr.empty:
            st.info(
                f"No completed matchups between {away_tm} and {home_tm} in the {selected_season - 5}–{selected_season} window."
            )
        else:
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
# SUB-TAB 2: MISMATCHES (SHORTENED SUB-TAB NAMES + HEADSHOTS + CONCISE RATIONALE)
# =============================================================================
with subtab_players:
    pm_subtab_cbwr, pm_subtab_volume, pm_subtab_injuries = st.tabs(
        [
            "CB vs. WR",
            "Skill Volume",
            "Injuries",
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
                delta="Out / Doubtful / Questionable / DNP CBs",
            )
            c_k4.metric(
                "Wideouts on L4 Uptick",
                f"{len(hot_wrs)} Receivers",
                delta="Positive L4 YPG vs Season",
            )

            cb_col1, cb_col2 = st.columns(2)

            for col_ui, (off_tm_i, def_tm_i, battle_list) in [
                (cb_col1, (away_tm, home_tm, away_cb_wr_battles)),
                (cb_col2, (home_tm, away_tm, home_cb_wr_battles)),
            ]:
                with col_ui:
                    render_html(
                        f'<div style="margin-bottom:8px;">'
                        f'{render_team_pill(off_tm_i)} <b>Wideouts vs</b> '
                        f'{render_team_pill(def_tm_i)} <b>Cornerbacks</b></div>'
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
                                <div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:6px; margin-bottom:6px;">
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
                                    f"[{b['off_tm']} WR]",
                                )
                                render_html(
                                    f"""
                                    <div style="display:flex; align-items:center; gap:10px; margin-top:4px;">
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
                                    f"[{b['def_tm']} {b['cb_pos']}]",
                                )
                                render_html(
                                    f"""
                                    <div style="display:flex; align-items:center; gap:10px; margin-top:4px;">
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
            st.markdown("##### CB vs. WR Summary Matrix (Click Row for Dossier)")
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
                    row_sig = f"cbwr_row_{chosen_b['wr_name']}_{sel_b_idx}"
                    if st.session_state.get("_last_table_sig") != row_sig:
                        st.session_state["_last_table_sig"] = row_sig
                        trigger_player_popup(chosen_b["wr_name"], chosen_b["off_tm"], "WR")
                        st.rerun()

    with pm_subtab_volume:
        if usage_matchup.empty or a_eff is None or h_eff is None:
            st.info("Player usage or team efficiency splits unavailable for this matchup.")
        else:
            p_col1, p_col2 = st.columns(2)

            for col_ui, (off_tm_i, def_tm_i) in [
                (p_col1, (away_tm, home_tm)),
                (p_col2, (home_tm, away_tm)),
            ]:
                with col_ui:
                    render_html(
                        f'<div style="margin-bottom:8px;">'
                        f'{render_team_pill(off_tm_i)} <b>Skill Weapons vs</b> '
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
                                    f"[{off_tm_i} {pos_badge}]",
                                )
                            with top_c2:
                                render_html(f'<div style="text-align:right;">{opp_unit_badge}</div>')
                            render_html(
                                f"""
                                <div style="display:flex; align-items:center; gap:10px; margin-top:4px;">
                                    {w_pic_html}
                                    <div class="metric-subtext">
                                        {share_lbl} | EPA: <b>{w_row['total_epa']:+.1f}</b> |
                                        Scrimmage: <b>{scrim_yds} yds ({int(w_row['total_tds'])} TD)</b>
                                    </div>
                                </div>
                                """
                            )

    with pm_subtab_injuries:
        with st.expander("Status Override Control", expanded=False):
            ov_candidates = []
            if not inj_matchup.empty:
                for _, r_c in inj_matchup.iterrows():
                    ov_candidates.append(
                        f"{r_c['player_display']} ({r_c['team']} - {r_c.get('position', 'POS')}) [{r_c['report_status']}]"
                    )
            if not roster_matchup_table.empty:
                for _, r_c in roster_matchup_table.head(40).iterrows():
                    lbl_c = f"{r_c['player_name']} ({r_c['team']} - {r_c['position']}) [ROSTER]"
                    if not any(lbl_c.split(" (")[0] in x for x in ov_candidates):
                        ov_candidates.append(lbl_c)

            if ov_candidates:
                q_c1, q_c2, q_c3 = st.columns([1.8, 1.2, 1.0])
                with q_c1:
                    chosen_ov_plr = st.selectbox(
                        "Player",
                        options=ov_candidates,
                        key="quick_ov_player_select",
                    )
                with q_c2:
                    chosen_ov_st = st.selectbox(
                        "Status",
                        options=[
                            "ACTIVE / CLEARED",
                            "UNSPECIFIED (DNP)",
                            "UNSPECIFIED (LP)",
                            "QUESTIONABLE",
                            "DOUBTFUL",
                            "OUT",
                            "IR",
                            "Auto (Official Feed)",
                        ],
                        index=0,
                        key="quick_ov_status_select",
                    )
                with q_c3:
                    st.write("")
                    if st.button("Apply Override", type="primary", use_container_width=True, key="quick_ov_apply_btn"):
                        p_part = chosen_ov_plr.split(" (")[0].strip().lower()
                        tm_part = chosen_ov_plr.split(" (")[1].split(" - ")[0].strip().upper()
                        k_ov = f"{p_part}|{tm_part}"
                        if chosen_ov_st == "Auto (Official Feed)":
                            st.session_state["injury_status_overrides"].pop(k_ov, None)
                        else:
                            st.session_state["injury_status_overrides"][k_ov] = chosen_ov_st
                        st.rerun()

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

        if inj_matchup.empty:
            render_html(
                f"""
                <div class="terminal-card-elite">
                    <span class="badge-elite">[CLEAN INJURY REPORT]</span>
                    <p style="margin:6px 0 0 0;" class="metric-subtext">
                        No active Out, Doubtful, Questionable, or DNP/LP practice designations found for {away_tm} or {home_tm} in Week {selected_week}.
                    </p>
                </div>
                """
            )
        else:
            col_away_inj, col_home_inj = st.columns(2)

            for col_obj, tm in [(col_away_inj, away_tm), (col_home_inj, home_tm)]:
                with col_obj:
                    tm_inj_all = inj_matchup[inj_matchup["team"] == tm].copy()
                    total_off_drop = tm_inj_all[
                        (tm_inj_all["unit_side"] == "Offense") & (~tm_inj_all["is_cleared"])
                    ]["est_epa_penalty"].sum()
                    total_def_drop = tm_inj_all[
                        (tm_inj_all["unit_side"] == "Defense") & (~tm_inj_all["is_cleared"])
                    ]["est_epa_penalty"].sum()
                    flagged_tm_count = int((~tm_inj_all["is_cleared"]).sum()) if not tm_inj_all.empty else 0
                    cleared_tm_count = int(tm_inj_all["is_cleared"].sum()) if not tm_inj_all.empty else 0

                    if inj_view_mode == "Flagged (Out / Q / DNP / LP)":
                        tm_inj = tm_inj_all[~tm_inj_all["is_cleared"]].copy()
                    elif inj_view_mode == "Full Practice (FP / Cleared)":
                        tm_inj = tm_inj_all[tm_inj_all["is_cleared"]].copy()
                    else:
                        tm_inj = tm_inj_all.copy()

                    card_cls = "terminal-card-vuln" if flagged_tm_count > 0 else "terminal-card-elite"
                    badge_cls = "badge-bad" if flagged_tm_count > 0 else "badge-elite"
                    render_html(
                        f"""
                        <div class="{card_cls}">
                            <div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:6px;">
                                <h4 style="margin:0;">{render_inline_logo(tm, 20)}{tm} Injuries</h4>
                                <div>
                                    <span class="{badge_cls}">[{flagged_tm_count} FLAGGED]</span>
                                    <span class="badge-elite">[{cleared_tm_count} FP / CLEARED]</span>
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
                        for i_idx, (_, r_inj) in enumerate(tm_inj.head(12).iterrows()):
                            badge_html = render_injury_badge(r_inj["report_status"])
                            prac_html = render_practice_badge(r_inj.get("practice_status_clean", ""))
                            snap_pct = r_inj["snap_share"] * 100
                            pos_str = str(r_inj.get("position", "POS"))
                            is_clr = bool(r_inj.get("is_cleared", False))
                            epa_color = "#34D399" if is_clr else "#F87171"
                            epa_str = "0.000 (Full Practice)" if is_clr else f"-{r_inj['est_epa_penalty']:.3f}/play"

                            with st.container(border=True):
                                ic1, ic2 = st.columns([1.4, 1.2])
                                with ic1:
                                    render_inline_player_trigger(
                                        r_inj["player_display"],
                                        tm,
                                        pos_str,
                                        f"inj_{tm}_{i_idx}",
                                        f"[{tm} {pos_str}]",
                                    )
                                with ic2:
                                    render_html(f'<div style="text-align:right;">{badge_html} {prac_html}</div>')
                                render_html(
                                    f"""
                                    <div class="metric-subtext" style="margin-top:4px;">
                                        {r_inj['role_tier']} • <b>{r_inj['primary_injury']}</b> •
                                        Snaps: <b>{snap_pct:.0f}%</b> |
                                        EPA: <span style="color:{epa_color}; font-weight:700;">{epa_str}</span>
                                    </div>
                                    """
                                )

# =============================================================================
# SUB-TAB 3: UNIT EPA (COMPACT NON-CLIPPING EPA STAT BLOCKS)
# =============================================================================
with subtab_trench:
    if a_eff is None or h_eff is None:
        st.warning("Efficiency metrics unavailable for one or both teams.")
    else:
        def render_possession_block(
            off_tm: str,
            def_tm: str,
            o_row: pd.Series,
            d_row: pd.Series,
            off_pen: float,
            def_pen: float,
        ):
            render_html(
                f"<h4 style='margin:10px 0 6px 0;'>"
                f"{render_team_pill(off_tm)} Offense vs {render_team_pill(def_tm)} Defense</h4>"
            )
            c1, c2, c3 = st.columns(3)

            with c1:
                with st.container(border=True):
                    o_p_rk = int(o_row["off_pass_epa_rank"])
                    d_p_rk = int(d_row["def_pass_epa_rank"])
                    render_html(
                        f"""
                        <div>
                            <b>{render_inline_logo(off_tm, 16)}AIR ({off_tm} Pass vs {def_tm} Pass Def)</b>
                            <div class="epa-stat-grid">
                                <div class="epa-stat-box">
                                    <div class="epa-stat-label">{off_tm} Pass EPA</div>
                                    <div class="epa-stat-num">{o_row['off_pass_epa']:+.3f}</div>
                                    {render_rank_badge(o_p_rk, f"{off_tm} Off")}
                                </div>
                                <div class="epa-stat-box">
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
                            <b>{render_inline_logo(off_tm, 16)}GROUND ({off_tm} Rush vs {def_tm} Rush Def)</b>
                            <div class="epa-stat-grid">
                                <div class="epa-stat-box">
                                    <div class="epa-stat-label">{off_tm} Rush EPA</div>
                                    <div class="epa-stat-num">{o_row['off_rush_epa']:+.3f}</div>
                                    {render_rank_badge(o_r_rk, f"{off_tm} Off")}
                                </div>
                                <div class="epa-stat-box">
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
                        f'<span class="badge-bad">[-{off_pen:.3f} INJ DRAG]</span>'
                        if off_pen > 0
                        else '<span class="badge-elite">[FULL STRENGTH]</span>'
                    )
                    def_drag_badge = (
                        f'<span class="badge-bad">[+{def_pen:.3f} INJ DRAG]</span>'
                        if def_pen > 0
                        else '<span class="badge-elite">[FULL STRENGTH]</span>'
                    )
                    render_html(
                        f"""
                        <div>
                            <b>{render_inline_logo(off_tm, 16)}OVERALL & INJURY-ADJUSTED EPA</b>
                            <div style="margin-top:4px;">
                                {render_rank_badge(o_ovr_rk, f"{off_tm} Ovr")} {render_rank_badge(d_ovr_rk, f"{def_tm} Ovr")}
                            </div>
                            <div class="epa-stat-grid">
                                <div class="epa-stat-box">
                                    <div class="epa-stat-label">{off_tm} Adj Off EPA</div>
                                    <div class="epa-stat-num">{adj_off_epa:+.3f}</div>
                                    {off_drag_badge}
                                </div>
                                <div class="epa-stat-box">
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

        render_possession_block(away_tm, home_tm, a_eff, h_eff, away_off_pen, home_def_pen)
        render_possession_block(home_tm, away_tm, h_eff, a_eff, home_off_pen, away_def_pen)

# =============================================================================
# SUB-TAB 4: PROPS (PLAYER PROP TREND EXPLORER)
# =============================================================================
with subtab_props:
    if prop_logs_matchup.empty:
        st.info(f"No weekly player game logs found for {away_tm} or {home_tm}.")
    else:
        ctrl_col1, ctrl_col2, ctrl_col3 = st.columns([1, 1.4, 1.3])

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
            )

        selected_player_row = roster_summary[
            roster_summary["display_option"] == selected_player_disp
        ].iloc[0]
        sel_player_name = selected_player_row["player_label"]
        sel_player_team = selected_player_row["team"]
        sel_player_pos = selected_player_row["pos_clean"]

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
            )
        with slider_col2:
            if total_avail_games > 1:
                lookback_n = st.slider(
                    "Last N Games",
                    min_value=1,
                    max_value=total_avail_games,
                    value=min(10, total_avail_games),
                    step=1,
                )
            else:
                lookback_n = 1

        season_baseline_avg = float(p_log[stat_col_name].mean()) if total_avail_games > 0 else 0.0
        l3_avg = float(p_log.tail(3)[stat_col_name].mean()) if total_avail_games > 0 else 0.0
        streak_badge_html, streak_delta_str = evaluate_player_streak_badge(
            season_baseline_avg, l3_avg, is_negative_stat=(stat_col_name == "interceptions")
        )

        window_log = p_log.tail(lookback_n).copy()
        window_log["hit"] = window_log[stat_col_name] >= prop_threshold
        window_log["bar_color"] = np.where(window_log["hit"], "#34D399", "#F87171")
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
            f"Hit Rate (Last {sample_n})",
            f"{hit_rate_pct:.1f}% ({hits_count}/{sample_n})",
            delta="Over Trend" if hit_rate_pct >= 55 else "Under Trend",
            delta_color="normal" if hit_rate_pct >= 55 else "inverse",
        )
        pk2.metric(
            f"Window Avg",
            f"{avg_val:.2f}" if is_td_or_int else f"{avg_val:.1f}",
            delta=f"{diff_vs_line:+.1f} vs {prop_threshold}",
            delta_color="normal" if diff_vs_line >= 0 else "inverse",
        )
        pk3.metric(
            "L3 Form",
            f"{l3_avg:.2f}" if is_td_or_int else f"{l3_avg:.1f}",
            delta=streak_delta_str,
        )
        pk4.metric(
            f"vs {opp_def_tm} {def_type_str}",
            f"Rank #{opp_def_rk}",
            delta="Favorable" if opp_def_rk >= 23 else ("Tough" if opp_def_rk <= 5 else "Neutral"),
            delta_color="normal" if opp_def_rk >= 23 else ("inverse" if opp_def_rk <= 5 else "off"),
        )

        opp_badge_html = render_rank_badge(opp_def_rk, f"{opp_def_tm} {def_type_str}")
        hit_badge_html = (
            f'<span class="badge-elite">[{hits_count}/{sample_n} OVER ({hit_rate_pct:.0f}%)]</span>'
            if hit_rate_pct >= 55
            else f'<span class="badge-mid">[{hits_count}/{sample_n} OVER ({hit_rate_pct:.0f}%)]</span>'
        )

        with st.container(border=True):
            pc1, pc2 = st.columns([1.5, 1.5])
            with pc1:
                render_inline_player_trigger(
                    sel_player_name,
                    sel_player_team,
                    sel_player_pos,
                    "prop_hdr",
                    f"[{sel_player_team} {sel_player_pos}]",
                )
            with pc2:
                render_html(f'<div style="text-align:right;">{streak_badge_html} {hit_badge_html} {opp_badge_html}</div>')

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
                line=dict(color="#60A5FA", width=2, dash="dot"),
                marker=dict(size=6, color="#60A5FA"),
                name="Cumulative Avg",
            )
        )
        fig_prop.add_hline(
            y=prop_threshold,
            line_width=2,
            line_dash="dash",
            line_color="#FBBF24",
            annotation_text=f"Line: {prop_threshold} ({hit_rate_pct:.0f}% Hit)",
            annotation_position="top left",
            annotation_font=dict(color="#FBBF24", size=12),
        )

        y_upper = max(float(window_log[stat_col_name].max()), prop_threshold) * 1.25 + 1.0
        fig_prop.update_layout(
            paper_bgcolor="#121722",
            plot_bgcolor="#121722",
            font=dict(color="#E2E8F0"),
            xaxis=dict(title="Game Week & Opponent", gridcolor="#222B3A"),
            yaxis=dict(title=selected_market_label, range=[0, y_upper], gridcolor="#222B3A"),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            height=380,
            margin=dict(l=20, r=20, t=40, b=30),
        )
        st.plotly_chart(fig_prop, width="stretch")

# =============================================================================
# SUB-TAB 5: ROSTERS (TEAM ROSTER & USAGE EXPLORER)
# =============================================================================
with subtab_roster:
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
                "player_name": "Player (Click Row for Dossier)",
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
                row_sig = f"roster_row_{chosen_p['player_name']}_{sel_r_idx}"
                if st.session_state.get("_last_table_sig") != row_sig:
                    st.session_state["_last_table_sig"] = row_sig
                    trigger_player_popup(
                        chosen_p["player_name"],
                        chosen_p["team"],
                        chosen_p["position"],
                    )
                    st.rerun()

# =============================================================================
# SUB-TAB 6: BACKTEST (HISTORICAL BACKTEST PERFORMANCE)
# =============================================================================
with subtab_backtest:
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
                marker_color="#60A5FA",
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
            barmode="group",
            paper_bgcolor="#121722",
            plot_bgcolor="#121722",
            font=dict(color="#E2E8F0"),
            xaxis=dict(title="Win / Cover %", range=[0, 100], gridcolor="#222B3A"),
            yaxis=dict(autorange="reversed"),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            height=340,
            margin=dict(l=20, r=20, t=36, b=24),
        )
        st.plotly_chart(fig, width="stretch")

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

# -----------------------------------------------------------------------------
# 8. LAUNCH PLAYER POP-OUT MODAL WHEN ACTIVE_PLAYER IS TRIGGERED
# -----------------------------------------------------------------------------
if st.session_state.get("open_player_modal") and st.session_state.get("active_player"):
    st.session_state["open_player_modal"] = False
    active_p = st.session_state["active_player"]

    if hasattr(st, "dialog"):

        @st.dialog("Player Dossier", width="large")
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
            st.subheader("Player Dossier")
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