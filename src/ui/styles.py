"""Custom visual treatment for the Streamlit application."""

APP_CSS = r"""
<style>
    .block-container { max-width: 1240px; padding-top: 2rem; padding-bottom: 4rem; }
    [data-testid="stSidebar"] { border-right: 1px solid rgba(128,128,128,.18); }
    .app-kicker { font-size: .82rem; letter-spacing: .12em; text-transform: uppercase; opacity: .65; font-weight: 700; }
    .app-title { font-size: 2.35rem; font-weight: 780; letter-spacing: -.035em; margin: .15rem 0 .35rem 0; }
    .app-subtitle { font-size: 1.02rem; opacity: .72; max-width: 760px; margin-bottom: 1.25rem; }
    .metric-card { border: 1px solid rgba(128,128,128,.18); border-radius: 16px; padding: 1rem 1.1rem; background: rgba(128,128,128,.04); }
    .source-card { border-left: 3px solid #6c63ff; padding: .75rem .9rem; margin: .55rem 0; background: rgba(108,99,255,.06); border-radius: 0 12px 12px 0; }
    .source-title { font-weight: 700; margin-bottom: .2rem; }
    .source-meta { opacity: .62; font-size: .82rem; }
    .source-text { opacity: .88; margin-top: .45rem; font-size: .91rem; }
    .stButton > button, .stDownloadButton > button { border-radius: 10px; font-weight: 650; }
    div[data-testid="stFileUploader"] section { border-radius: 14px; }
</style>
"""
