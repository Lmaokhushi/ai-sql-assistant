"""
All the CSS for the app. The palette comes from config.THEMES and is chosen
to match whichever theme (light or dark) the visitor's Streamlit is using.
"""

import streamlit as st

from config import THEMES


def current_theme():
    """Return "dark" or "light". st.context.theme exists in Streamlit 1.46+."""
    try:
        theme_type = st.context.theme.type
    except AttributeError:
        theme_type = None
    return "dark" if theme_type == "dark" else "light"


def inject_css():
    c = THEMES[current_theme()]
    st.markdown(f"""<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

    /* ================= Base ================= */
    html, body, .stApp, .stApp button, .stApp input, .stApp textarea {{
        font-family:'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
    }}
    .stApp, [data-testid="stAppViewContainer"] {{
        background:
            radial-gradient(900px 420px at 70% -120px, {c['background_glow']}, transparent 70%),
            {c['background']};
    }}
    header[data-testid="stHeader"] {{ background:transparent; }}
    [data-testid="stBottom"], [data-testid="stBottom"] > div,
    [data-testid="stBottomBlockContainer"] {{ background:{c['background']}; }}
    .block-container {{ max-width:1040px; padding-top:2.2rem; padding-bottom:7rem; }}

    .stApp, .stApp p, .stApp li, .stApp label, .stApp span,
    .stApp h1, .stApp h2, .stApp h3, .stApp h4, .stApp h5,
    [data-testid="stMarkdownContainer"] {{ color:{c['text']}; }}
    [data-testid="stCaptionContainer"], [data-testid="stCaptionContainer"] * {{ color:{c['muted']} !important; }}
    .stApp a {{ color:{c['primary_text']}; }}

    /* ================= Sidebar ================= */
    section[data-testid="stSidebar"] {{
        background:{c['surface']}; border-right:1px solid {c['border']};
    }}
    section[data-testid="stSidebar"] .block-container {{ padding-top:1.2rem; }}
    .qp-brand {{ display:flex; align-items:center; gap:.75rem; margin:.2rem 0 1rem; }}
    .qp-logo {{
        width:40px; height:40px; border-radius:12px; display:grid; place-items:center; flex-shrink:0;
        background:linear-gradient(135deg, {c['primary']}, {c['accent']});
        color:#fff; box-shadow:0 6px 16px {c['glow']};
    }}
    .qp-brand-name {{ font-weight:800; font-size:1.2rem; letter-spacing:-.02em; color:{c['text']}; line-height:1.1; }}
    .qp-brand-sub {{ color:{c['muted']}; font-size:.8rem; }}
    .qp-section {{
        font-size:.68rem; font-weight:700; text-transform:uppercase; letter-spacing:.1em;
        color:{c['muted']}; margin:1.3rem 0 .45rem; display:flex; justify-content:space-between;
    }}
    .qp-status {{
        display:flex; align-items:center; gap:.5rem; font-size:.8rem; color:{c['muted']};
        padding:.55rem .75rem; border:1px solid {c['border']}; border-radius:10px; background:{c['surface_alt']};
    }}
    .qp-dot {{ width:8px; height:8px; border-radius:50%; flex-shrink:0; }}
    .qp-dot.ok {{ background:{c['success']}; box-shadow:0 0 0 3px {c['success_bg']}; }}
    .qp-dot.bad {{ background:{c['danger']}; box-shadow:0 0 0 3px {c['danger_bg']}; }}

    /* chat list: buttons look like list rows */
    .st-key-chat_list button {{
        justify-content:flex-start !important; text-align:left; min-height:2.3rem;
    }}
    .st-key-chat_list button p {{
        white-space:nowrap; overflow:hidden; text-overflow:ellipsis; text-align:left; font-size:.88rem;
    }}
    .st-key-chat_list [data-testid="stBaseButton-secondary"] {{
        background:{c['tint']}; border-color:{c['border_strong']}; color:{c['primary_text']};
    }}
    .st-key-chat_list [data-testid="stBaseButton-secondary"] * {{ color:{c['primary_text']} !important; }}
    section[data-testid="stSidebar"] [data-testid="stBaseButton-tertiary"],
    section[data-testid="stSidebar"] button[kind="tertiary"] {{
        width:100%; justify-content:flex-start; padding:.45rem .65rem; border-radius:9px;
        color:{c['text']}; font-weight:450; border:1px solid transparent;
    }}
    section[data-testid="stSidebar"] [data-testid="stBaseButton-tertiary"]:hover,
    section[data-testid="stSidebar"] button[kind="tertiary"]:hover {{
        background:{c['tint']}; color:{c['primary_text']};
    }}
    section[data-testid="stSidebar"] [data-testid="stBaseButton-tertiary"] p,
    section[data-testid="stSidebar"] button[kind="tertiary"] p {{
        white-space:nowrap; overflow:hidden; text-overflow:ellipsis; text-align:left; font-size:.88rem;
    }}

    /* ================= Hero ================= */
    .qp-hero {{ text-align:center; padding:1.6rem 1rem 1.8rem; }}
    .qp-badge {{
        display:inline-flex; align-items:center; gap:.45rem; padding:.32rem .85rem;
        border-radius:999px; font-size:.78rem; font-weight:600;
        background:{c['surface']}; color:{c['primary_text']}; border:1px solid {c['border']};
        box-shadow:0 2px 10px {c['shadow']}; margin-bottom:1.1rem;
    }}
    .qp-hero h1 {{
        font-size:clamp(2rem, 4.2vw, 3rem); font-weight:800; line-height:1.08;
        margin:0 0 .8rem; letter-spacing:-.035em; color:{c['text']} !important; padding:0;
    }}
    .qp-gradient {{
        background:linear-gradient(90deg, {c['primary']}, {c['accent']});
        -webkit-background-clip:text; background-clip:text; color:transparent !important;
    }}
    .qp-hero p {{ color:{c['muted']} !important; font-size:1.06rem; max-width:620px; margin:0 auto; line-height:1.55; }}

    /* ================= Cards ================= */
    .qp-card {{
        background:{c['surface']}; border:1px solid {c['border']}; border-radius:18px;
        padding:1.4rem 1.45rem 1.25rem; box-shadow:0 8px 28px {c['shadow']};
        min-height:300px; margin-bottom:.7rem; transition:transform .18s ease, border-color .18s ease;
    }}
    .qp-card:hover {{ transform:translateY(-2px); border-color:{c['border_strong']}; }}
    .qp-card-icon {{
        width:46px; height:46px; border-radius:13px; display:grid; place-items:center;
        background:{c['tint']}; color:{c['primary_text']}; margin-bottom:.95rem;
    }}
    .qp-card h4 {{ margin:0 0 .4rem; font-size:1.06rem; font-weight:700; color:{c['text']} !important; padding:0; }}
    .qp-card p {{ margin:0; color:{c['muted']} !important; font-size:.92rem; line-height:1.55; }}
    .qp-card code, .qp-inline-code {{
        background:{c['tint']}; color:{c['primary_text']} !important; padding:.08rem .38rem;
        border-radius:6px; font-size:.84em;
    }}
    .qp-card ul {{ margin:.6rem 0 0; padding-left:1.1rem; }}
    .qp-card li {{ color:{c['muted']} !important; font-size:.88rem; margin-bottom:.2rem; }}

    .qp-steps {{ display:grid; grid-template-columns:repeat(3, 1fr); gap:.9rem; margin:.4rem 0 1.6rem; }}
    @media (max-width: 760px) {{ .qp-steps {{ grid-template-columns:1fr; }} }}
    .qp-step {{
        background:{c['surface']}; border:1px solid {c['border']}; border-radius:16px; padding:1.05rem 1.1rem;
        display:flex; gap:.8rem; align-items:flex-start;
    }}
    .qp-step-num {{
        width:30px; height:30px; border-radius:9px; flex-shrink:0; display:grid; place-items:center;
        font-weight:800; font-size:.85rem; color:#fff;
        background:linear-gradient(135deg, {c['primary']}, {c['accent']});
    }}
    .qp-step b {{ display:block; font-size:.93rem; color:{c['text']}; margin-bottom:.15rem; }}
    .qp-step span {{ font-size:.84rem; color:{c['muted']} !important; line-height:1.45; }}

    .qp-setup {{
        background:{c['warning_bg']}; border:1px solid {c['warning']}; border-radius:16px;
        padding:1.1rem 1.25rem; margin-bottom:1.4rem;
    }}
    .qp-setup b, .qp-setup li, .qp-setup p {{ color:{c['text']} !important; }}
    .qp-setup ol {{ margin:.5rem 0 0; padding-left:1.2rem; }}
    .qp-setup li {{ font-size:.9rem; margin-bottom:.25rem; }}

    .qp-label {{
        text-align:center; font-size:.7rem; font-weight:700; letter-spacing:.1em; text-transform:uppercase;
        color:{c['muted']}; margin:1.6rem 0 .7rem;
    }}

    /* ================= Chat header ================= */
    .qp-chat-title {{ font-size:1.35rem; font-weight:750; letter-spacing:-.02em; color:{c['text']}; margin:0; line-height:1.3; }}
    .qp-chat-sub {{ margin-top:.35rem; }}

    /* ================= Chips ================= */
    .qp-chip {{
        display:inline-flex; align-items:center; gap:.3rem; padding:.2rem .62rem; border-radius:999px;
        font-size:.76rem; font-weight:600; margin:0 .35rem .35rem 0; background:{c['tint']};
        color:{c['primary_text']} !important; border:1px solid {c['border']};
    }}
    .qp-ok {{ background:{c['success_bg']}; color:{c['success']} !important; border-color:transparent; }}
    .qp-bad {{ background:{c['danger_bg']}; color:{c['danger']} !important; border-color:transparent; }}
    .qp-warn {{ background:{c['warning_bg']}; color:{c['warning']} !important; border-color:transparent; }}

    /* ================= Chat messages ================= */
    [data-testid="stChatMessage"] {{
        background:{c['surface']}; border:1px solid {c['border']}; border-radius:18px;
        padding:1rem 1.2rem; box-shadow:0 4px 18px {c['shadow']}; margin-bottom:.4rem;
    }}
    [data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarUser"]) {{
        background:{c['tint']}; border-color:transparent; box-shadow:none;
    }}
    [data-testid="stChatMessageAvatarUser"], [data-testid="stChatMessageAvatarAssistant"],
    [data-testid="stChatMessageAvatarCustom"] {{
        background:linear-gradient(135deg, {c['primary']}, {c['accent']}); color:#fff; border-radius:10px;
    }}
    [data-testid="stChatMessageAvatarUser"] {{ background:{c['surface']}; color:{c['primary_text']}; border:1px solid {c['border']}; }}

    [data-testid="stChatInput"], [data-testid="stChatInput"] > div {{
        background:{c['surface']} !important; border-color:{c['border_strong']} !important; border-radius:16px !important;
    }}
    [data-testid="stChatInput"] {{ box-shadow:0 8px 30px {c['shadow']}; }}
    [data-testid="stChatInput"] textarea {{ color:{c['text']} !important; font-size:.98rem; }}
    [data-testid="stChatInput"] textarea::placeholder {{ color:{c['muted']} !important; }}
    [data-testid="stChatInputSubmitButton"] {{
        background:linear-gradient(135deg, {c['primary']}, {c['accent']}) !important; color:#fff !important; border-radius:11px;
    }}

    /* ================= Buttons ================= */
    .stButton > button, .stDownloadButton > button, [data-testid="stPopover"] button {{
        border-radius:11px; border:1px solid {c['border']}; background:{c['surface']};
        color:{c['text']}; font-weight:550; transition:all .15s ease;
    }}
    .stButton > button:hover, .stDownloadButton > button:hover, [data-testid="stPopover"] button:hover {{
        border-color:{c['primary']}; color:{c['primary_text']}; background:{c['tint']};
    }}
    .stButton > button p, .stDownloadButton > button p {{ color:inherit !important; }}
    .stButton > button[kind="primary"], [data-testid="stBaseButton-primary"] {{
        background:linear-gradient(135deg, {c['primary']}, {c['primary_dark']}); color:#fff !important;
        border:none; box-shadow:0 6px 16px {c['glow']};
    }}
    .stButton > button[kind="primary"]:hover {{ color:#fff; filter:brightness(1.08); }}
    .stButton > button[kind="primary"] *, [data-testid="stBaseButton-primary"] * {{ color:#fff !important; }}

    /* ================= Inputs ================= */
    [data-testid="stFileUploaderDropzone"] {{
        background:{c['surface_alt']}; border:1.5px dashed {c['border_strong']}; border-radius:13px;
    }}
    [data-testid="stFileUploaderDropzone"] button {{ background:{c['surface']}; color:{c['text']}; border:1px solid {c['border']}; }}
    [data-testid="stFileUploaderDropzoneInstructions"] * {{ color:{c['muted']} !important; }}
    [data-testid="stFileUploaderFile"] * {{ color:{c['text']} !important; }}
    div[data-baseweb="select"] > div, div[data-baseweb="input"] > div, .stTextInput input {{
        background:{c['surface']} !important; border-color:{c['border']} !important;
        border-radius:10px !important; color:{c['text']} !important;
    }}
    div[data-baseweb="select"] * {{ color:{c['text']} !important; }}
    div[data-baseweb="popover"] ul, div[data-baseweb="popover"] [role="listbox"] {{ background:{c['surface']} !important; }}
    div[data-baseweb="popover"] li {{ color:{c['text']} !important; }}
    [data-testid="stPopoverBody"] {{ background:{c['surface']}; border:1px solid {c['border']}; border-radius:14px; }}

    /* ================= Expanders, code, alerts, dialog ================= */
    [data-testid="stExpander"] details {{
        background:{c['surface_alt']}; border:1px solid {c['border']} !important; border-radius:12px;
    }}
    [data-testid="stExpander"] summary:hover * {{ color:{c['primary_text']} !important; }}
    [data-testid="stCode"], .stCode {{ border-radius:12px; border:1px solid {c['border']}; overflow:hidden; }}
    [data-testid="stAlert"] {{ border-radius:12px; }}
    div[role="dialog"] {{ background:{c['surface']}; border:1px solid {c['border']}; border-radius:18px; }}
    div[role="dialog"] * {{ color:{c['text']}; }}
    hr {{ border-color:{c['border']} !important; }}
    </style>""", unsafe_allow_html=True)
