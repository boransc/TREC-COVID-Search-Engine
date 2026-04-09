import streamlit as st

THEMES: dict[str, dict[str, str]] = {
    "Light": {
        "bg_1": "#f8fafc",        # cleaner background
        "card": "#ffffff",        # pure white cards
        "ink": "#111827",         # strong readable text
        "muted": "#6b7280",
        "accent": "#2563eb",
        "line": "#d1d5db",        # stronger borders
        "sidebar": "#f1f5f9",
        "mark_bg": "#fde68a",
    },
    "Dark": {
        "bg_1": "#0d1117",
        "bg_2": "#131a24",
        "card": "#171f2b",
        "ink": "#e6edf7",
        "muted": "#a8b5ca",
        "accent": "#7fb3ff",
        "line": "#2a3546",
        "sidebar": "#101722",
        "chip_bg": "#1d2a3c",
        "chip_ink": "#d6e6ff",
        "chip_line": "#355174",
        "mark_bg": "#705e2d",
    },
}


def inject_theme(theme_name: str) -> None:
    tokens = THEMES.get(theme_name, THEMES["Light"])

    st.markdown(f"""
<style>

/* ROOT VARIABLES */
:root {{
    --bg: {tokens['bg_1']};
    --card: {tokens['card']};
    --text: {tokens['ink']};
    --muted: {tokens['muted']};
    --accent: {tokens['accent']};
    --border: {tokens['line']};
}}

/* APP BACKGROUND */
.stApp {{
    background: var(--bg);
    color: var(--text);
}}

/* HEADINGS */
h1, h2, h3 {{
    font-family: 'Crimson Text', serif;
    color: var(--text);
}}

/* HERO */
.hero {{
    background: var(--card);
    border: 1px solid var(--border);
    border-radius: 16px;
    padding: 20px;
}}

/* RESULT CARDS */
.result-card {{
    background: var(--card);
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 14px;
    margin-bottom: 12px;
}}

/* SIDEBAR */
section[data-testid="stSidebar"] {{
    background-color: {tokens['sidebar']} !important;
}}

section[data-testid="stSidebar"] * {{
    color: var(--text) !important;
}}

/* INPUT FIELDS */
input, textarea {{
    background-color: var(--card) !important;
    color: var(--text) !important;
    border: 1px solid var(--border) !important;
}}

/* SELECTBOX */
div[data-baseweb="select"] > div {{
    background-color: var(--card) !important;
    color: var(--text) !important;
}}

/* BUTTONS */
button {{
    background-color: var(--card) !important;
    color: var(--text) !important;
    border: 1px solid var(--border) !important;
}}

/* SLIDER TEXT */
.stSlider {{
    color: var(--text) !important;
}}

/* FORM BLOCK */
div[data-testid="stForm"] {{
    background: var(--card) !important;
    border: 1px solid var(--border);
}}

/* SNIPPET HIGHLIGHT */
mark {{
    background: {tokens['mark_bg']};
    color: black;
}}

/* ========================= */
/* EXPANDER FIX (IMPORTANT) */
/* ========================= */

div[data-testid="stExpander"] {{
    background-color: var(--card) !important;
    border: 1px solid var(--border);
    border-radius: 10px;
}}

div[data-testid="stExpander"] > details > summary {{
    color: var(--text) !important;
    background-color: var(--card) !important;
}}

div[data-testid="stExpander"] > details > div {{
    background-color: var(--card) !important;
    color: var(--text) !important;
}}

/* ========================= */
/* LINKS */
/* ========================= */

a {{
    color: var(--accent);
    text-decoration: none;
}}

a:hover {{
    text-decoration: underline;
}}

/* Make expander visually part of card */
div[data-testid="stExpander"] {{
    margin-top: -20px !important;   /* pulls it into the card */
    border-top: none !important;
    border-radius: 0 0 12px 12px !important;
}}

/* Remove double border effect */
div[data-testid="stExpander"] > div {{
    border-top: none !important;
}}

/* Make expander header blend */
div[data-testid="stExpander"] summary {{
    padding-top: 6px;
    padding-bottom: 6px;
}}

</style>
""", unsafe_allow_html=True)