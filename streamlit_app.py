import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import boto3
import io
from pyathena import connect

# ─────────────────────────────────────────────────────────────────────────────
# PAGE CONFIG
# ─────────────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Project Insights",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ─────────────────────────────────────────────────────────────────────────────
# STYLES
# ─────────────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Syne:wght@400;600;700;800&family=DM+Mono:wght@300;400;500&family=Manrope:wght@300;400;500;600&display=swap');

html, body, [class*="css"] { font-family: 'Manrope', sans-serif !important; }
.stApp { background: #0c0d10 !important; }
.main .block-container { padding: 2rem 2.5rem 4rem 2.5rem !important; max-width: 1400px !important; }

/* Sidebar */
[data-testid="stSidebar"] { background: #0a0b0e !important; border-right: 1px solid #1c1f26 !important; }
[data-testid="stSidebar"] > div { padding: 2rem 1.2rem !important; }
.sidebar-logo { font-family: 'Syne', sans-serif; font-size: 22px; font-weight: 800; letter-spacing: -0.5px; color: #ffffff; margin-bottom: 4px; }
.sidebar-tagline { font-family: 'DM Mono', monospace; font-size: 10px; color: #e8a020; letter-spacing: 2px; text-transform: uppercase; margin-bottom: 28px; }
.sidebar-divider { height: 1px; background: linear-gradient(to right, #e8a020, transparent); margin: 20px 0; opacity: 0.35; }
.sidebar-section-label { font-family: 'DM Mono', monospace; font-size: 9px; letter-spacing: 2.5px; text-transform: uppercase; color: #4a5060; margin-bottom: 10px; }
.sidebar-stat { display: flex; flex-direction: column; margin-bottom: 16px; }
.sidebar-stat-val { font-family: 'Syne', sans-serif; font-size: 20px; font-weight: 700; color: #ffffff; line-height: 1.1; }
.sidebar-stat-lbl { font-size: 11px; color: #5a6070; margin-top: 2px; }

/* Page header */
.page-header { margin-bottom: 32px; padding-bottom: 24px; border-bottom: 1px solid #1c1f26; }
.page-title { font-family: 'Syne', sans-serif; font-size: 38px; font-weight: 800; letter-spacing: -1.5px; color: #ffffff; line-height: 1.0; margin-bottom: 6px; }
.page-title span { color: #e8a020; }
.page-subtitle { font-family: 'DM Mono', monospace; font-size: 11px; color: #4a5060; letter-spacing: 1px; }

/* Metric cards */
.metric-card { background: #111318; border: 1px solid #1c1f26; border-radius: 4px; padding: 20px 22px; position: relative; overflow: hidden; height: 100%; }
.metric-card::before { content: ''; position: absolute; top: 0; left: 0; width: 3px; height: 100%; background: #e8a020; }
.metric-card.blue::before { background: #4a9eff; }
.metric-card.green::before { background: #50c878; }
.metric-card.red::before { background: #e85050; }
.metric-label { font-family: 'DM Mono', monospace; font-size: 10px; letter-spacing: 2px; text-transform: uppercase; color: #4a5060; margin-bottom: 8px; }
.metric-value { font-family: 'Syne', sans-serif; font-size: 24px; font-weight: 700; color: #ffffff; letter-spacing: -0.5px; line-height: 1.1; }
.metric-value.sm { font-size: 16px; }
.metric-sub { font-size: 11px; color: #e8a020; margin-top: 4px; font-family: 'DM Mono', monospace; }
.metric-sub.blue { color: #4a9eff; }
.metric-sub.green { color: #50c878; }

/* Section headers */
.section-header { display: flex; align-items: center; gap: 12px; margin-bottom: 20px; margin-top: 8px; }
.section-number { font-family: 'DM Mono', monospace; font-size: 11px; color: #e8a020; letter-spacing: 1px; }
.section-title { font-family: 'Syne', sans-serif; font-size: 20px; font-weight: 700; color: #ffffff; letter-spacing: -0.3px; }
.section-line { flex: 1; height: 1px; background: #1c1f26; }
.section-divider { height: 1px; background: #1c1f26; margin: 36px 0; }
.section-caption { font-family: 'DM Mono', monospace; font-size: 11px; color: #4a5060; margin-bottom: 16px; margin-top: -12px; letter-spacing: 0.5px; }

/* Tab styling */
.stTabs [data-baseweb="tab-list"] { background: transparent !important; border-bottom: 1px solid #1c1f26 !important; gap: 0; margin-bottom: 28px; }
.stTabs [data-baseweb="tab"] { background: transparent !important; color: #4a5060 !important; font-family: 'DM Mono', monospace !important; font-size: 12px !important; letter-spacing: 1.5px !important; text-transform: uppercase !important; padding: 10px 24px !important; border: none !important; border-bottom: 2px solid transparent !important; }
.stTabs [aria-selected="true"] { color: #ffffff !important; border-bottom: 2px solid #e8a020 !important; }
.stTabs [data-baseweb="tab"]:hover { color: #ffffff !important; }
.stTabs [data-baseweb="tab-panel"] { padding: 0 !important; }

/* Inputs */
.stTextInput > div > div > input { background: #111318 !important; border: 1px solid #1c1f26 !important; border-radius: 4px !important; color: #ffffff !important; font-family: 'Manrope', sans-serif !important; font-size: 14px !important; padding: 12px 16px !important; caret-color: #e8a020 !important; }
.stTextInput > div > div > input:focus { border-color: #e8a020 !important; box-shadow: 0 0 0 1px #e8a020 !important; }
.stTextInput > div > div > input::placeholder { color: #3a4050 !important; }
.stSelectbox > div > div { background: #111318 !important; border: 1px solid #1c1f26 !important; border-radius: 4px !important; color: #ffffff !important; }

/* Insight box */
.insight-box { background: #111318; border: 1px solid #1c1f26; border-left: 3px solid #4a9eff; border-radius: 4px; padding: 14px 18px; margin-bottom: 20px; }
.insight-box.amber { border-left-color: #e8a020; }
.insight-box.green { border-left-color: #50c878; }
.insight-label { font-family: 'DM Mono', monospace; font-size: 9px; letter-spacing: 2px; text-transform: uppercase; color: #4a5060; margin-bottom: 6px; }
.insight-text { font-size: 13px; color: #c8cdd8; line-height: 1.5; }
.insight-text b { color: #ffffff; }

/* Gainers/Losers badge */
.badge-up { color: #50c878; font-family: 'DM Mono', monospace; font-size: 12px; font-weight: 600; }
.badge-down { color: #e85050; font-family: 'DM Mono', monospace; font-size: 12px; font-weight: 600; }

/* Misc */
.stPlotlyChart { border-radius: 4px; overflow: hidden; }
.stCaption { color: #4a5060 !important; font-family: 'DM Mono', monospace !important; font-size: 11px !important; }
#MainMenu { visibility: hidden; } footer { visibility: hidden; } header { visibility: hidden; }
::-webkit-scrollbar { width: 4px; } ::-webkit-scrollbar-track { background: #0c0d10; }
::-webkit-scrollbar-thumb { background: #1c1f26; border-radius: 2px; }
::-webkit-scrollbar-thumb:hover { background: #e8a020; }

/* Overview card */
.overview-card { background: #111318; border: 1px solid #1c1f26; border-radius: 4px; padding: 16px 20px; margin-bottom: 20px; }
.overview-meta { display: flex; gap: 20px; margin-bottom: 10px; flex-wrap: wrap; }
.overview-meta-item { font-family: 'DM Mono', monospace; font-size: 10px; color: #4a5060; letter-spacing: 1px; }
.overview-meta-item span { color: #c8cdd8; }
.overview-text { font-size: 13px; color: #8a9090; line-height: 1.6; font-style: italic; }
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# CONSTANTS
# ─────────────────────────────────────────────────────────────────────────────
BUCKET    = 'project-insight-shravan'
CHART_BG  = "rgba(0,0,0,0)"
GRID      = "#1c1f26"
FONT_COL  = "#c8cdd8"
AMBER     = "#e8a020"
BLUE      = "#4a9eff"
GREEN     = "#50c878"
RED       = "#e85050"

MOVIE_GENRE_MAP = {
    28:"Action", 12:"Adventure", 16:"Animation", 35:"Comedy", 80:"Crime",
    99:"Documentary", 18:"Drama", 10751:"Family", 14:"Fantasy", 36:"History",
    27:"Horror", 10402:"Music", 9648:"Mystery", 10749:"Romance", 878:"Sci-Fi",
    10770:"TV Movie", 53:"Thriller", 10752:"War", 37:"Western"
}
TV_GENRE_MAP = {
    10759:"Action & Adventure", 16:"Animation", 35:"Comedy", 80:"Crime",
    99:"Documentary", 18:"Drama", 10751:"Family", 10762:"Kids", 9648:"Mystery",
    10763:"News", 10764:"Reality", 10765:"Sci-Fi & Fantasy", 10766:"Soap",
    10767:"Talk", 10768:"War & Politics", 37:"Western"
}
LANG_MAP = {
    'en':'English','hi':'Hindi','ko':'Korean','ja':'Japanese','fr':'French',
    'es':'Spanish','zh':'Chinese','it':'Italian','de':'German','pt':'Portuguese',
    'tr':'Turkish','th':'Thai','ru':'Russian','ar':'Arabic','ta':'Tamil','te':'Telugu'
}
PALETTE = ['#e8a020','#4a9eff','#50c878','#e85050','#9b59b6',
           '#1abc9c','#f39c12','#e74c3c','#3498db','#2ecc71','#ff6b9d','#a29bfe']

# ─────────────────────────────────────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────────────────────────────────────
def parse_genre(g, genre_map):
    try:
        ids = [int(x.strip()) for x in g.strip("[]").split(",")]
        for i in ids:
            if i in genre_map:
                return genre_map[i]
    except:
        pass
    return "Other"

def base_layout(height=420, title="", show_xgrid=True, show_ygrid=True):
    return dict(
        height=height,
        paper_bgcolor=CHART_BG, plot_bgcolor=CHART_BG,
        font=dict(family="Manrope, sans-serif", color=FONT_COL, size=12),
        margin=dict(l=16, r=16, t=44 if title else 20, b=16),
        showlegend=False,
        title=dict(text=title, font=dict(family="Syne, sans-serif", color="#ffffff", size=14), x=0),
        xaxis=dict(gridcolor=GRID if show_xgrid else "rgba(0,0,0,0)", linecolor=GRID, tickfont=dict(color="#5a6070")),
        yaxis=dict(gridcolor=GRID if show_ygrid else "rgba(0,0,0,0)", linecolor=GRID, tickfont=dict(color="#c8cdd8"))
    )

def section(num, title):
    st.markdown(f'<div class="section-header"><span class="section-number">{num}</span><span class="section-title">{title}</span><div class="section-line"></div></div>', unsafe_allow_html=True)

def divider():
    st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)

def insight(text, color="blue"):
    st.markdown(f'<div class="insight-box {color}"><div class="insight-label">Insight</div><div class="insight-text">{text}</div></div>', unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# DATA LOADERS
# ─────────────────────────────────────────────────────────────────────────────
@st.cache_resource
def get_s3():
    return boto3.client(
        's3',
        region_name=st.secrets["aws"]["region_name"],
        aws_access_key_id=st.secrets["aws"]["aws_access_key_id"],
        aws_secret_access_key=st.secrets["aws"]["aws_secret_access_key"]
    )

@st.cache_resource
def get_athena():
    return connect(
        s3_staging_dir=f"s3://{BUCKET}/athena-results/",
        region_name=st.secrets["aws"]["region_name"],
        aws_access_key_id=st.secrets["aws"]["aws_access_key_id"],
        aws_secret_access_key=st.secrets["aws"]["aws_secret_access_key"]
    )

@st.cache_data(ttl=3600)
def load_processed(filename):
    """Read a pre-computed CSV from processed/ folder."""
    s3 = get_s3()
    obj = s3.get_object(Bucket=BUCKET, Key=f'processed/{filename}')
    return pd.read_csv(io.BytesIO(obj['Body'].read()))

@st.cache_data(ttl=3600)
def run_query(sql):
    """Run live Athena query — used only for Trend Explorer searches."""
    conn = get_athena()
    return pd.read_sql(sql, conn)

# ─────────────────────────────────────────────────────────────────────────────
# SIDEBAR
# ─────────────────────────────────────────────────────────────────────────────
# Load sidebar stats
try:
    m_top10   = load_processed('movies_top10_today.csv')
    tv_top10  = load_processed('tv_top10_today.csv')
    m_days    = run_query("SELECT COUNT(DISTINCT snapshot_date) as days FROM project_insights.daily_metrics")
    tv_days   = run_query("SELECT COUNT(DISTINCT snapshot_date) as days FROM project_insights.tv_daily_metrics")
    latest_dt = run_query("SELECT MAX(snapshot_date) as dt FROM project_insights.daily_metrics")
except Exception as e:
    st.error(f"Error loading data: {e}")
    st.stop()

with st.sidebar:
    st.markdown('<div class="sidebar-logo">Project Insights</div>', unsafe_allow_html=True)
    st.markdown('<div class="sidebar-tagline">Entertainment Analytics</div>', unsafe_allow_html=True)
    st.markdown('<div class="sidebar-divider"></div>', unsafe_allow_html=True)
    st.markdown('<div class="sidebar-section-label">Pipeline Stats</div>', unsafe_allow_html=True)
    st.markdown(f"""
    <div class="sidebar-stat"><span class="sidebar-stat-val">10,449</span><span class="sidebar-stat-lbl">Movies Tracked</span></div>
    <div class="sidebar-stat"><span class="sidebar-stat-val">10,332</span><span class="sidebar-stat-lbl">TV Shows Tracked</span></div>
    <div class="sidebar-stat"><span class="sidebar-stat-val">{m_days['days'][0]}</span><span class="sidebar-stat-lbl">Days of Movie Data</span></div>
    <div class="sidebar-stat"><span class="sidebar-stat-val">{tv_days['days'][0]}</span><span class="sidebar-stat-lbl">Days of TV Data</span></div>
    <div class="sidebar-stat"><span class="sidebar-stat-val">{latest_dt['dt'][0]}</span><span class="sidebar-stat-lbl">Latest Snapshot</span></div>
    """, unsafe_allow_html=True)
    st.markdown('<div class="sidebar-divider"></div>', unsafe_allow_html=True)
    st.markdown('<div class="sidebar-section-label">Data Source</div>', unsafe_allow_html=True)
    st.markdown("<div style='font-size:11px;color:#3a4050;line-height:2;font-family:DM Mono,monospace;'>TMDB API<br>AWS Lambda<br>AWS S3 + Athena<br>Updated · 9 PM IST daily</div>", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# PAGE HEADER
# ─────────────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="page-header">
  <div class="page-title">Project <span>Insights</span></div>
  <div class="page-subtitle">TMDB · AWS LAMBDA · S3 · ATHENA · DAILY TREND TRACKING</div>
</div>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# TABS
# ─────────────────────────────────────────────────────────────────────────────
tab_movies, tab_tv = st.tabs(["🎬  Movies", "📺  TV Shows"])

# ═════════════════════════════════════════════════════════════════════════════
# MOVIES TAB
# ═════════════════════════════════════════════════════════════════════════════
with tab_movies:

    # Load all processed data
    top10       = load_processed('movies_top10_today.csv')
    gainers     = load_processed('movies_gainers_7d.csv')
    losers      = load_processed('movies_losers_7d.csv')
    by_year     = load_processed('movies_by_year.csv')
    genre_raw   = load_processed('movies_genre_ratings.csv')
    lang_data   = load_processed('movies_language_dist.csv')
    top_voted   = load_processed('movies_top_voted.csv')

    # ── Stat Cards ──────────────────────────────────────────────────────────
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown(f'<div class="metric-card"><div class="metric-label">Movies Tracked</div><div class="metric-value">10,449</div><div class="metric-sub">2020 – 2026</div></div>', unsafe_allow_html=True)
    with c2:
        if not top10.empty:
            st.markdown(f'<div class="metric-card blue"><div class="metric-label">Most Popular Today</div><div class="metric-value sm">{top10["title"].iloc[0]}</div><div class="metric-sub blue">Score · {top10["popularity"].iloc[0]:.1f}</div></div>', unsafe_allow_html=True)
        else:
            st.markdown(f'<div class="metric-card blue"><div class="metric-label">Most Popular Today</div><div class="metric-value sm">—</div><div class="metric-sub blue">No data yet</div></div>', unsafe_allow_html=True)
    with c3:
        if not gainers.empty:
            st.markdown(f'<div class="metric-card green"><div class="metric-label">Biggest Gainer (7d)</div><div class="metric-value sm">{gainers["title"].iloc[0]}</div><div class="metric-sub green">+{gainers["popularity_change"].iloc[0]:.1f} pts</div></div>', unsafe_allow_html=True)
        else:
            st.markdown(f'<div class="metric-card green"><div class="metric-label">Biggest Gainer (7d)</div><div class="metric-value sm">—</div><div class="metric-sub green">Needs 7 days of data</div></div>', unsafe_allow_html=True)
    with c4:
        days_val = m_days["days"][0] if not m_days.empty and len(m_days) > 0 else 0
        st.markdown(f'<div class="metric-card"><div class="metric-label">Days of Trend Data</div><div class="metric-value">{days_val}</div><div class="metric-sub">~{int(days_val)*10430:,} total rows</div></div>', unsafe_allow_html=True)

    divider()

    # ── 01 Top 10 Today ─────────────────────────────────────────────────────
    section("01", "Top 10 Most Popular Today")
    st.markdown('<div class="section-caption">Ranked by TMDB popularity score — updated daily at 9 PM IST</div>', unsafe_allow_html=True)

    fig1 = go.Figure(go.Bar(
        x=top10['popularity'], y=top10['display_title'], orientation='h',
        marker=dict(color=top10['popularity'],
            colorscale=[[0,'#1a2a1a'],[0.5,'#2d6a2d'],[1,'#50c878']], line=dict(width=0)),
        customdata=top10[['vote_average','vote_count']].values,
        hovertemplate='<b>%{y}</b><br>Popularity: %{x:.1f}<br>Rating: %{customdata[0]:.1f} / 10<br>Votes: %{customdata[1]:,}<extra></extra>',
        text=top10['popularity'].round(1), textposition='outside',
        textfont=dict(color=FONT_COL, size=11, family='DM Mono, monospace')
    ))
    l1 = base_layout(420)
    l1['yaxis']['autorange'] = 'reversed'
    fig1.update_layout(**l1)
    st.plotly_chart(fig1, use_container_width=True)

    divider()

    # ── 02 Gainers & Losers ─────────────────────────────────────────────────
    section("02", "Popularity Movers — Last 7 Days")
    st.markdown('<div class="section-caption">This data only exists because of our daily snapshots — no public source tracks this</div>', unsafe_allow_html=True)

    if gainers.empty or losers.empty:
        st.markdown('<div class="section-caption" style="opacity:0.6;">Not enough historical data yet — this section needs 7+ days of daily snapshots to compute movement. Check back once the pipeline has run for a week.</div>', unsafe_allow_html=True)
    else:
        insight(f"<b>{gainers['title'].iloc[0]}</b> had the biggest gain — up <b>+{gainers['popularity_change'].iloc[0]:.1f} points</b> ({gainers['pct_change'].iloc[0]:.1f}%) over the last 7 days.", "green")

        col_g, col_l = st.columns(2)

        with col_g:
            st.markdown("<div style='font-family:DM Mono,monospace;font-size:10px;letter-spacing:2px;color:#50c878;text-transform:uppercase;margin-bottom:12px;'>▲ Biggest Gainers</div>", unsafe_allow_html=True)
            fig_g = go.Figure(go.Bar(
                x=gainers['popularity_change'], y=gainers['display_title'], orientation='h',
                marker=dict(color=gainers['popularity_change'],
                    colorscale=[[0,'#0d2010'],[0.5,'#1a4a20'],[1,'#50c878']], line=dict(width=0)),
                customdata=gainers[['popularity_7d_ago','popularity_today','pct_change']].values,
                hovertemplate='<b>%{y}</b><br>7 days ago: %{customdata[0]:.1f}<br>Today: %{customdata[1]:.1f}<br>Change: <b>+%{x:.1f}</b> pts (%{customdata[2]:.1f}%)<extra></extra>',
                text=[f'+{v:.1f}' for v in gainers['popularity_change']], textposition='outside',
                textfont=dict(color=GREEN, size=10, family='DM Mono, monospace')
            ))
            lg = base_layout(460)
            lg['yaxis']['autorange'] = 'reversed'
            fig_g.update_layout(**lg)
            st.plotly_chart(fig_g, use_container_width=True)

        with col_l:
            st.markdown("<div style='font-family:DM Mono,monospace;font-size:10px;letter-spacing:2px;color:#e85050;text-transform:uppercase;margin-bottom:12px;'>▼ Biggest Losers</div>", unsafe_allow_html=True)
            fig_l = go.Figure(go.Bar(
                x=losers['popularity_drop'], y=losers['display_title'], orientation='h',
                marker=dict(color=losers['popularity_drop'],
                    colorscale=[[0,'#200d0d'],[0.5,'#4a1a1a'],[1,'#e85050']], line=dict(width=0)),
                customdata=losers[['popularity_7d_ago','popularity_today','pct_drop']].values,
                hovertemplate='<b>%{y}</b><br>7 days ago: %{customdata[0]:.1f}<br>Today: %{customdata[1]:.1f}<br>Drop: <b>-%{x:.1f}</b> pts (%{customdata[2]:.1f}%)<extra></extra>',
                text=[f'-{v:.1f}' for v in losers['popularity_drop']], textposition='outside',
                textfont=dict(color=RED, size=10, family='DM Mono, monospace')
            ))
            ll = base_layout(460)
            ll['yaxis']['autorange'] = 'reversed'
            fig_l.update_layout(**ll)
            st.plotly_chart(fig_l, use_container_width=True)

    divider()

    # ── 03 Trend Explorer ───────────────────────────────────────────────────
    section("03", "Trend Explorer")
    st.markdown('<div class="section-caption">Search any movie to see how its popularity, rating, and vote count changed over time</div>', unsafe_allow_html=True)

    search_m = st.text_input("", placeholder="Search movie — e.g. Tenet, Dune, Inception...",
                              label_visibility="collapsed", key="movie_search")
    if search_m:
        movie_list = run_query(f"""
            SELECT * FROM (
                SELECT DISTINCT m.id, m.title, m.release_year,
                    CONCAT(m.title, ' (', CAST(m.release_year AS VARCHAR), ')') as display_title
                FROM project_insights.movies_master m
                WHERE LOWER(m.title) LIKE LOWER('%{search_m}%')
            ) sub ORDER BY release_year DESC LIMIT 15
        """)
        if movie_list.empty:
            st.warning("No movies found. Try a different search term.")
        else:
            selected = st.selectbox("", movie_list['display_title'].tolist(),
                                    label_visibility="collapsed", key="movie_select")
            movie_id = movie_list[movie_list['display_title'] == selected].iloc[0]['id']

            # Fetch overview from movies_master
            movie_info = run_query(f"""
                SELECT overview, original_language, genre_ids, release_date
                FROM project_insights.movies_master
                WHERE id = {movie_id} LIMIT 1
            """)
            if not movie_info.empty:
                overview_text = movie_info['overview'].iloc[0] or 'No overview available.'
                lang = LANG_MAP.get(movie_info['original_language'].iloc[0], movie_info['original_language'].iloc[0].upper())
                genre = parse_genre(str(movie_info['genre_ids'].iloc[0]), MOVIE_GENRE_MAP)
                release = str(movie_info['release_date'].iloc[0])[:4] if movie_info['release_date'].iloc[0] else 'N/A'
                st.markdown(f'''<div class="overview-card">
                    <div class="overview-meta">
                        <div class="overview-meta-item">GENRE &nbsp;<span>{genre}</span></div>
                        <div class="overview-meta-item">LANGUAGE &nbsp;<span>{lang}</span></div>
                        <div class="overview-meta-item">RELEASE &nbsp;<span>{release}</span></div>
                    </div>
                    <div class="overview-text">{overview_text}</div>
                </div>''', unsafe_allow_html=True)

            trend = run_query(f"""
                SELECT snapshot_date, popularity, vote_average, vote_count
                FROM project_insights.daily_metrics
                WHERE id = {movie_id}
                ORDER BY snapshot_date
            """)
            trend['snapshot_date'] = trend['snapshot_date'].astype(str)

            if len(trend) < 2:
                st.info("Not enough data points yet for this movie. Check back after more days of collection.")
            else:
                # Time range filter
                time_filter_m = st.radio("", ["All time", "Last 7 days", "Last 30 days", "Last 90 days"],
                    horizontal=True, label_visibility="collapsed", key="movie_time_filter")
                filter_map = {"Last 7 days": 7, "Last 30 days": 30, "Last 90 days": 90}
                if time_filter_m in filter_map:
                    trend = trend.tail(filter_map[time_filter_m])

                # Insight
                pop_change = trend["popularity"].iloc[-1] - trend["popularity"].iloc[0]
                direction = "gained" if pop_change > 0 else "lost"
                start_date = trend["snapshot_date"].iloc[0]
                period = f"over the {time_filter_m.lower()}" if time_filter_m != "All time" else f"since tracking began on {start_date}"
                insight(f"<b>{selected}</b> has {direction} <b>{abs(pop_change):.1f} popularity points</b> {period}.", "amber")

                col1, col2 = st.columns(2)
                with col1:
                    fig_t1 = go.Figure(go.Scatter(
                        x=trend['snapshot_date'], y=trend['popularity'],
                        mode='lines+markers',
                        line=dict(color=BLUE, width=2.5),
                        marker=dict(size=7, color=BLUE, line=dict(color='#0c0d10', width=2)),
                        fill='tozeroy', fillcolor='rgba(74,158,255,0.06)',
                        hovertemplate='%{x}<br>Popularity: <b>%{y:.1f}</b><extra></extra>'
                    ))
                    fig_t1.update_layout(**base_layout(300, "Popularity Trend"))
                    st.plotly_chart(fig_t1, use_container_width=True)

                with col2:
                    fig_t2 = go.Figure(go.Scatter(
                        x=trend['snapshot_date'], y=trend['vote_average'],
                        mode='lines+markers',
                        line=dict(color=AMBER, width=2.5),
                        marker=dict(size=7, color=AMBER, line=dict(color='#0c0d10', width=2)),
                        fill='tozeroy', fillcolor='rgba(232,160,32,0.06)',
                        hovertemplate='%{x}<br>Rating: <b>%{y:.2f}</b><extra></extra>'
                    ))
                    lt2 = base_layout(300, "Rating Trend")
                    lt2['yaxis']['range'] = [0, 10]
                    fig_t2.update_layout(**lt2)
                    st.plotly_chart(fig_t2, use_container_width=True)

                fig_t3 = go.Figure(go.Bar(
                    x=trend['snapshot_date'], y=trend['vote_count'],
                    marker=dict(color=GREEN, opacity=0.8, line=dict(width=0)),
                    hovertemplate='%{x}<br>Total Votes: <b>%{y:,}</b><extra></extra>'
                ))
                fig_t3.update_layout(**base_layout(240, "Vote Count Growth"))
                st.plotly_chart(fig_t3, use_container_width=True)

    divider()

    # ── 04 Head-to-Head ─────────────────────────────────────────────────────
    section("04", "Head-to-Head Comparison")
    st.markdown('<div class="section-caption">Compare popularity trends of two movies over time</div>', unsafe_allow_html=True)

    hcol1, hcol2 = st.columns(2)
    with hcol1:
        search_h1 = st.text_input("", placeholder="Movie 1 — e.g. Dune",
                                   label_visibility="collapsed", key="h2h_1")
    with hcol2:
        search_h2 = st.text_input("", placeholder="Movie 2 — e.g. Oppenheimer",
                                   label_visibility="collapsed", key="h2h_2")

    if search_h1 and search_h2:
        list1 = run_query(f"""
            SELECT * FROM (
                SELECT DISTINCT m.id, m.release_year,
                    CONCAT(m.title, ' (', CAST(m.release_year AS VARCHAR), ')') as display_title
                FROM project_insights.movies_master m
                WHERE LOWER(m.title) LIKE LOWER('%{search_h1}%')
            ) sub ORDER BY release_year DESC LIMIT 10
        """)
        list2 = run_query(f"""
            SELECT * FROM (
                SELECT DISTINCT m.id, m.release_year,
                    CONCAT(m.title, ' (', CAST(m.release_year AS VARCHAR), ')') as display_title
                FROM project_insights.movies_master m
                WHERE LOWER(m.title) LIKE LOWER('%{search_h2}%')
            ) sub ORDER BY release_year DESC LIMIT 10
        """)
        if not list1.empty and not list2.empty:
            sc1, sc2 = st.columns(2)
            with sc1:
                sel1 = st.selectbox("", list1['display_title'].tolist(), label_visibility="collapsed", key="h2h_sel1")
            with sc2:
                sel2 = st.selectbox("", list2['display_title'].tolist(), label_visibility="collapsed", key="h2h_sel2")

            id1 = list1[list1['display_title'] == sel1].iloc[0]['id']
            id2 = list2[list2['display_title'] == sel2].iloc[0]['id']

            t1 = run_query(f"SELECT snapshot_date, popularity FROM project_insights.daily_metrics WHERE id = {id1} ORDER BY snapshot_date")
            t2 = run_query(f"SELECT snapshot_date, popularity FROM project_insights.daily_metrics WHERE id = {id2} ORDER BY snapshot_date")
            t1['snapshot_date'] = t1['snapshot_date'].astype(str)
            t2['snapshot_date'] = t2['snapshot_date'].astype(str)

            fig_h = go.Figure()
            fig_h.add_trace(go.Scatter(
                x=t1['snapshot_date'], y=t1['popularity'], name=sel1,
                mode='lines+markers', line=dict(color=BLUE, width=2.5),
                marker=dict(size=6, color=BLUE),
                hovertemplate=f'<b>{sel1}</b><br>%{{x}}<br>Popularity: %{{y:.1f}}<extra></extra>'
            ))
            fig_h.add_trace(go.Scatter(
                x=t2['snapshot_date'], y=t2['popularity'], name=sel2,
                mode='lines+markers', line=dict(color=AMBER, width=2.5),
                marker=dict(size=6, color=AMBER),
                hovertemplate=f'<b>{sel2}</b><br>%{{x}}<br>Popularity: %{{y:.1f}}<extra></extra>'
            ))
            lh = base_layout(360, "Popularity — Head-to-Head")
            lh['showlegend'] = True
            lh['legend'] = dict(font=dict(color=FONT_COL, size=12), bgcolor='rgba(0,0,0,0)', bordercolor=GRID, borderwidth=1)
            fig_h.update_layout(**lh)
            st.plotly_chart(fig_h, use_container_width=True)

    divider()

    # ── 05 By Release Year ──────────────────────────────────────────────────
    section("05", "Average Popularity by Release Year")
    st.markdown('<div class="section-caption">Which release year has the highest average popularity today</div>', unsafe_allow_html=True)

    fig5 = go.Figure(go.Bar(
        x=by_year['release_year'], y=by_year['avg_popularity'],
        marker=dict(color=by_year['avg_popularity'],
            colorscale=[[0,'#12243a'],[0.5,'#1a4a7a'],[1,'#4a9eff']], line=dict(width=0)),
        text=by_year['movie_count'].astype(str) + ' films',
        textposition='outside',
        textfont=dict(color='#5a6070', size=10, family='DM Mono, monospace'),
        hovertemplate='<b>%{x}</b><br>Avg Popularity: %{y:.2f}<extra></extra>'
    ))
    l5 = base_layout(400)
    l5['xaxis']['dtick'] = 1
    fig5.update_layout(**l5)
    st.plotly_chart(fig5, use_container_width=True)

    divider()

    # ── 06 Genre Ratings ────────────────────────────────────────────────────
    section("06", "Average Rating by Genre")
    st.markdown('<div class="section-caption">Genre ratings based on today\'s snapshot across all tracked movies</div>', unsafe_allow_html=True)

    genre_raw['primary_genre'] = genre_raw['genre_ids'].apply(lambda g: parse_genre(g, MOVIE_GENRE_MAP))
    genre_agg = genre_raw.groupby('primary_genre').agg(
        avg_rating=('avg_rating', 'mean'),
        movie_count=('movie_count', 'sum')
    ).reset_index()
    genre_agg = genre_agg[genre_agg['primary_genre'] != 'Other'].sort_values('avg_rating', ascending=True)
    genre_agg['avg_rating'] = genre_agg['avg_rating'].round(2)

    fig6 = go.Figure(go.Bar(
        x=genre_agg['avg_rating'], y=genre_agg['primary_genre'], orientation='h',
        marker=dict(color=genre_agg['avg_rating'],
            colorscale=[[0,'#1a1200'],[0.5,'#7a4800'],[1,'#e8a020']], line=dict(width=0)),
        text=genre_agg['avg_rating'].astype(str),
        textposition='outside',
        textfont=dict(color=FONT_COL, size=11, family='DM Mono, monospace'),
        customdata=genre_agg['movie_count'].values,
        hovertemplate='<b>%{y}</b><br>Avg Rating: %{x:.2f} / 10<br>Movies: %{customdata:,}<extra></extra>'
    ))
    l6 = base_layout(500)
    l6['xaxis']['range'] = [0, 10]
    fig6.update_layout(**l6)
    st.plotly_chart(fig6, use_container_width=True)

    divider()

    # ── 07 Language Distribution ────────────────────────────────────────────
    section("07", "Movies by Original Language")

    lang_data['language'] = lang_data['original_language'].map(lambda x: LANG_MAP.get(str(x), str(x).upper()) if pd.notna(x) else 'Unknown')
    fig7 = go.Figure(go.Pie(
        labels=lang_data['language'], values=lang_data['movie_count'],
        hole=0.55, marker=dict(colors=PALETTE, line=dict(color='#0c0d10', width=2)),
        textfont=dict(family='Manrope, sans-serif', size=12, color='#ffffff'),
        hovertemplate='<b>%{label}</b><br>%{value:,} movies · %{percent}<extra></extra>',
        textposition='outside'
    ))
    fig7.update_layout(
        height=440, paper_bgcolor=CHART_BG,
        font=dict(family="Manrope, sans-serif", color=FONT_COL),
        margin=dict(l=16, r=16, t=20, b=16), showlegend=True,
        legend=dict(font=dict(color=FONT_COL, size=12), bgcolor='rgba(0,0,0,0)', bordercolor=GRID, borderwidth=1),
        annotations=[dict(
            text=f"<b>{lang_data['movie_count'].sum():,}</b><br>movies",
            x=0.5, y=0.5, font=dict(size=18, color='#ffffff', family='Syne, sans-serif'),
            showarrow=False
        )]
    )
    st.plotly_chart(fig7, use_container_width=True)

    divider()

    # ── 08 Most Voted ───────────────────────────────────────────────────────
    section("08", "Top 10 Most Voted Movies")
    st.markdown('<div class="section-caption">Movies with the highest total vote count — colored by their rating</div>', unsafe_allow_html=True)

    fig8 = go.Figure(go.Bar(
        x=top_voted['vote_count'], y=top_voted['display_title'], orientation='h',
        marker=dict(
            color=top_voted['vote_average'],
            colorscale=[[0,'#1a0a0a'],[0.4,'#7a1a1a'],[0.7,'#c8601a'],[1,'#e8a020']],
            line=dict(width=0), showscale=True,
            colorbar=dict(
                title=dict(text="Rating", font=dict(color=FONT_COL, size=11)),
                tickfont=dict(color=FONT_COL, size=10), thickness=8, len=0.7
            )
        ),
        text=['⭐ ' + str(round(r, 1)) for r in top_voted['vote_average']],
        textposition='outside',
        textfont=dict(color=FONT_COL, size=11, family='DM Mono, monospace'),
        hovertemplate='<b>%{y}</b><br>Votes: %{x:,}<extra></extra>'
    ))
    l8 = base_layout(420)
    l8['yaxis']['autorange'] = 'reversed'
    fig8.update_layout(**l8)
    st.plotly_chart(fig8, use_container_width=True)

# ═════════════════════════════════════════════════════════════════════════════
# TV SHOWS TAB
# ═════════════════════════════════════════════════════════════════════════════
with tab_tv:

    tv_top10     = load_processed('tv_top10_today.csv')
    tv_gainers   = load_processed('tv_gainers_7d.csv')
    tv_losers    = load_processed('tv_losers_7d.csv')
    tv_by_year   = load_processed('tv_by_year.csv')
    tv_genre_raw = load_processed('tv_genre_ratings.csv')
    tv_lang      = load_processed('tv_language_dist.csv')
    tv_top_voted = load_processed('tv_top_voted.csv')

    # ── Stat Cards ──────────────────────────────────────────────────────────
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown(f'<div class="metric-card"><div class="metric-label">TV Shows Tracked</div><div class="metric-value">10,332</div><div class="metric-sub">2020 – 2026</div></div>', unsafe_allow_html=True)
    with c2:
        st.markdown(f'<div class="metric-card blue"><div class="metric-label">Most Popular Today</div><div class="metric-value sm">{tv_top10["name"].iloc[0]}</div><div class="metric-sub blue">Score · {tv_top10["popularity"].iloc[0]:.1f}</div></div>', unsafe_allow_html=True)
    with c3:
        st.markdown(f'<div class="metric-card green"><div class="metric-label">Biggest Gainer (7d)</div><div class="metric-value sm">{tv_gainers["name"].iloc[0]}</div><div class="metric-sub green">+{tv_gainers["popularity_change"].iloc[0]:.1f} pts</div></div>', unsafe_allow_html=True)
    with c4:
        st.markdown(f'<div class="metric-card"><div class="metric-label">Days of Trend Data</div><div class="metric-value">{tv_days["days"][0]}</div><div class="metric-sub">~{int(tv_days["days"][0])*10303:,} total rows</div></div>', unsafe_allow_html=True)

    divider()

    # ── 01 Top 10 Today ─────────────────────────────────────────────────────
    section("01", "Top 10 Most Popular Today")
    st.markdown('<div class="section-caption">Ranked by TMDB popularity score — updated daily at 9 PM IST</div>', unsafe_allow_html=True)

    fig_tv1 = go.Figure(go.Bar(
        x=tv_top10['popularity'], y=tv_top10['display_title'], orientation='h',
        marker=dict(color=tv_top10['popularity'],
            colorscale=[[0,'#1a1530'],[0.5,'#2d2a6a'],[1,'#9b59b6']], line=dict(width=0)),
        customdata=tv_top10[['vote_average','vote_count']].values,
        hovertemplate='<b>%{y}</b><br>Popularity: %{x:.1f}<br>Rating: %{customdata[0]:.1f} / 10<br>Votes: %{customdata[1]:,}<extra></extra>',
        text=tv_top10['popularity'].round(1), textposition='outside',
        textfont=dict(color=FONT_COL, size=11, family='DM Mono, monospace')
    ))
    l_tv1 = base_layout(420)
    l_tv1['yaxis']['autorange'] = 'reversed'
    fig_tv1.update_layout(**l_tv1)
    st.plotly_chart(fig_tv1, use_container_width=True)

    divider()

    # ── 02 Gainers & Losers ─────────────────────────────────────────────────
    section("02", "Popularity Movers — Last 7 Days")
    st.markdown('<div class="section-caption">This data only exists because of our daily snapshots — no public source tracks this</div>', unsafe_allow_html=True)

    insight(f"<b>{tv_gainers['name'].iloc[0]}</b> had the biggest gain — up <b>+{tv_gainers['popularity_change'].iloc[0]:.1f} points</b> ({tv_gainers['pct_change'].iloc[0]:.1f}%) over the last 7 days.", "green")

    col_g, col_l = st.columns(2)
    with col_g:
        st.markdown("<div style='font-family:DM Mono,monospace;font-size:10px;letter-spacing:2px;color:#50c878;text-transform:uppercase;margin-bottom:12px;'>▲ Biggest Gainers</div>", unsafe_allow_html=True)
        fig_tvg = go.Figure(go.Bar(
            x=tv_gainers['popularity_change'], y=tv_gainers['display_title'], orientation='h',
            marker=dict(color=tv_gainers['popularity_change'],
                colorscale=[[0,'#0d2010'],[0.5,'#1a4a20'],[1,'#50c878']], line=dict(width=0)),
            customdata=tv_gainers[['popularity_7d_ago','popularity_today','pct_change']].values,
            hovertemplate='<b>%{y}</b><br>7 days ago: %{customdata[0]:.1f}<br>Today: %{customdata[1]:.1f}<br>Change: <b>+%{x:.1f}</b> pts (%{customdata[2]:.1f}%)<extra></extra>',
            text=[f'+{v:.1f}' for v in tv_gainers['popularity_change']], textposition='outside',
            textfont=dict(color=GREEN, size=10, family='DM Mono, monospace')
        ))
        lg_tv = base_layout(460)
        lg_tv['yaxis']['autorange'] = 'reversed'
        fig_tvg.update_layout(**lg_tv)
        st.plotly_chart(fig_tvg, use_container_width=True)

    with col_l:
        st.markdown("<div style='font-family:DM Mono,monospace;font-size:10px;letter-spacing:2px;color:#e85050;text-transform:uppercase;margin-bottom:12px;'>▼ Biggest Losers</div>", unsafe_allow_html=True)
        fig_tvl = go.Figure(go.Bar(
            x=tv_losers['popularity_drop'], y=tv_losers['display_title'], orientation='h',
            marker=dict(color=tv_losers['popularity_drop'],
                colorscale=[[0,'#200d0d'],[0.5,'#4a1a1a'],[1,'#e85050']], line=dict(width=0)),
            customdata=tv_losers[['popularity_7d_ago','popularity_today','pct_drop']].values,
            hovertemplate='<b>%{y}</b><br>7 days ago: %{customdata[0]:.1f}<br>Today: %{customdata[1]:.1f}<br>Drop: <b>-%{x:.1f}</b> pts (%{customdata[2]:.1f}%)<extra></extra>',
            text=[f'-{v:.1f}' for v in tv_losers['popularity_drop']], textposition='outside',
            textfont=dict(color=RED, size=10, family='DM Mono, monospace')
        ))
        ll_tv = base_layout(460)
        ll_tv['yaxis']['autorange'] = 'reversed'
        fig_tvl.update_layout(**ll_tv)
        st.plotly_chart(fig_tvl, use_container_width=True)

    divider()

    # ── 03 Trend Explorer ───────────────────────────────────────────────────
    section("03", "Trend Explorer")
    st.markdown('<div class="section-caption">Search any TV show to see how its popularity, rating, and votes changed over time</div>', unsafe_allow_html=True)

    search_tv = st.text_input("", placeholder="Search TV show — e.g. Bridgerton, Squid Game, The Bear...",
                               label_visibility="collapsed", key="tv_search")
    if search_tv:
        tv_list = run_query(f"""
            SELECT * FROM (
                SELECT DISTINCT t.id, t.name, t.first_air_year,
                    CONCAT(t.name, ' (', CAST(t.first_air_year AS VARCHAR), ')') as display_title
                FROM project_insights.tv_master t
                WHERE LOWER(t.name) LIKE LOWER('%{search_tv}%')
            ) sub ORDER BY first_air_year DESC LIMIT 15
        """)
        if tv_list.empty:
            st.warning("No TV shows found. Try a different search term.")
        else:
            sel_tv = st.selectbox("", tv_list['display_title'].tolist(),
                                  label_visibility="collapsed", key="tv_select")
            tv_id = tv_list[tv_list['display_title'] == sel_tv].iloc[0]['id']

            # Fetch overview from tv_master
            tv_info = run_query(f"""
                SELECT overview, original_language, genre_ids, first_air_date
                FROM project_insights.tv_master
                WHERE id = {tv_id} LIMIT 1
            """)
            if not tv_info.empty:
                tv_overview_text = tv_info['overview'].iloc[0] or 'No overview available.'
                tv_overview_lang = LANG_MAP.get(tv_info['original_language'].iloc[0], tv_info['original_language'].iloc[0].upper())
                tv_genre = parse_genre(str(tv_info['genre_ids'].iloc[0]), TV_GENRE_MAP)
                tv_release = str(tv_info['first_air_date'].iloc[0])[:4] if tv_info['first_air_date'].iloc[0] else 'N/A'
                st.markdown(f'''<div class="overview-card">
                    <div class="overview-meta">
                        <div class="overview-meta-item">GENRE &nbsp;<span>{tv_genre}</span></div>
                        <div class="overview-meta-item">LANGUAGE &nbsp;<span>{tv_overview_lang}</span></div>
                        <div class="overview-meta-item">FIRST AIRED &nbsp;<span>{tv_release}</span></div>
                    </div>
                    <div class="overview-text">{tv_overview_text}</div>
                </div>''', unsafe_allow_html=True)

            tv_trend = run_query(f"""
                SELECT snapshot_date, popularity, vote_average, vote_count
                FROM project_insights.tv_daily_metrics
                WHERE id = {tv_id}
                ORDER BY snapshot_date
            """)
            tv_trend['snapshot_date'] = tv_trend['snapshot_date'].astype(str)

            if len(tv_trend) < 2:
                st.info("Not enough data points yet for this show.")
            else:
                # Time range filter
                time_filter_tv = st.radio("", ["All time", "Last 7 days", "Last 30 days", "Last 90 days"],
                    horizontal=True, label_visibility="collapsed", key="tv_time_filter")
                filter_map_tv = {"Last 7 days": 7, "Last 30 days": 30, "Last 90 days": 90}
                if time_filter_tv in filter_map_tv:
                    tv_trend = tv_trend.tail(filter_map_tv[time_filter_tv])

                # Insight
                pop_change = tv_trend["popularity"].iloc[-1] - tv_trend["popularity"].iloc[0]
                direction = "gained" if pop_change > 0 else "lost"
                tv_start_date = tv_trend["snapshot_date"].iloc[0]
                period = f"over the {time_filter_tv.lower()}" if time_filter_tv != "All time" else f"since tracking began on {tv_start_date}"
                insight(f"<b>{sel_tv}</b> has {direction} <b>{abs(pop_change):.1f} popularity points</b> {period}.", "amber")

                col1, col2 = st.columns(2)
                with col1:
                    fig_tv_t1 = go.Figure(go.Scatter(
                        x=tv_trend['snapshot_date'], y=tv_trend['popularity'],
                        mode='lines+markers',
                        line=dict(color='#9b59b6', width=2.5),
                        marker=dict(size=7, color='#9b59b6', line=dict(color='#0c0d10', width=2)),
                        fill='tozeroy', fillcolor='rgba(155,89,182,0.06)',
                        hovertemplate='%{x}<br>Popularity: <b>%{y:.1f}</b><extra></extra>'
                    ))
                    fig_tv_t1.update_layout(**base_layout(300, "Popularity Trend"))
                    st.plotly_chart(fig_tv_t1, use_container_width=True)

                with col2:
                    fig_tv_t2 = go.Figure(go.Scatter(
                        x=tv_trend['snapshot_date'], y=tv_trend['vote_average'],
                        mode='lines+markers',
                        line=dict(color=AMBER, width=2.5),
                        marker=dict(size=7, color=AMBER, line=dict(color='#0c0d10', width=2)),
                        fill='tozeroy', fillcolor='rgba(232,160,32,0.06)',
                        hovertemplate='%{x}<br>Rating: <b>%{y:.2f}</b><extra></extra>'
                    ))
                    lt2_tv = base_layout(300, "Rating Trend")
                    lt2_tv['yaxis']['range'] = [0, 10]
                    fig_tv_t2.update_layout(**lt2_tv)
                    st.plotly_chart(fig_tv_t2, use_container_width=True)

                fig_tv_t3 = go.Figure(go.Bar(
                    x=tv_trend['snapshot_date'], y=tv_trend['vote_count'],
                    marker=dict(color='#9b59b6', opacity=0.8, line=dict(width=0)),
                    hovertemplate='%{x}<br>Total Votes: <b>%{y:,}</b><extra></extra>'
                ))
                fig_tv_t3.update_layout(**base_layout(240, "Vote Count Growth"))
                st.plotly_chart(fig_tv_t3, use_container_width=True)

    divider()

    # ── 04 Head-to-Head ─────────────────────────────────────────────────────
    section("04", "Head-to-Head Comparison")
    st.markdown('<div class="section-caption">Compare popularity trends of two TV shows over time</div>', unsafe_allow_html=True)

    hcol1, hcol2 = st.columns(2)
    with hcol1:
        search_tv_h1 = st.text_input("", placeholder="Show 1 — e.g. Squid Game",
                                      label_visibility="collapsed", key="tv_h2h_1")
    with hcol2:
        search_tv_h2 = st.text_input("", placeholder="Show 2 — e.g. Bridgerton",
                                      label_visibility="collapsed", key="tv_h2h_2")

    if search_tv_h1 and search_tv_h2:
        tv_list1 = run_query(f"""
            SELECT * FROM (
                SELECT DISTINCT t.id, t.first_air_year,
                    CONCAT(t.name, ' (', CAST(t.first_air_year AS VARCHAR), ')') as display_title
                FROM project_insights.tv_master t
                WHERE LOWER(t.name) LIKE LOWER('%{search_tv_h1}%')
            ) sub ORDER BY first_air_year DESC LIMIT 10
        """)
        tv_list2 = run_query(f"""
            SELECT * FROM (
                SELECT DISTINCT t.id, t.first_air_year,
                    CONCAT(t.name, ' (', CAST(t.first_air_year AS VARCHAR), ')') as display_title
                FROM project_insights.tv_master t
                WHERE LOWER(t.name) LIKE LOWER('%{search_tv_h2}%')
            ) sub ORDER BY first_air_year DESC LIMIT 10
        """)
        if not tv_list1.empty and not tv_list2.empty:
            sc1, sc2 = st.columns(2)
            with sc1:
                tv_sel1 = st.selectbox("", tv_list1['display_title'].tolist(), label_visibility="collapsed", key="tv_h2h_sel1")
            with sc2:
                tv_sel2 = st.selectbox("", tv_list2['display_title'].tolist(), label_visibility="collapsed", key="tv_h2h_sel2")

            tv_id1 = tv_list1[tv_list1['display_title'] == tv_sel1].iloc[0]['id']
            tv_id2 = tv_list2[tv_list2['display_title'] == tv_sel2].iloc[0]['id']

            tt1 = run_query(f"SELECT snapshot_date, popularity FROM project_insights.tv_daily_metrics WHERE id = {tv_id1} ORDER BY snapshot_date")
            tt2 = run_query(f"SELECT snapshot_date, popularity FROM project_insights.tv_daily_metrics WHERE id = {tv_id2} ORDER BY snapshot_date")
            tt1['snapshot_date'] = tt1['snapshot_date'].astype(str)
            tt2['snapshot_date'] = tt2['snapshot_date'].astype(str)

            fig_tvh = go.Figure()
            fig_tvh.add_trace(go.Scatter(
                x=tt1['snapshot_date'], y=tt1['popularity'], name=tv_sel1,
                mode='lines+markers', line=dict(color='#9b59b6', width=2.5),
                marker=dict(size=6, color='#9b59b6'),
                hovertemplate=f'<b>{tv_sel1}</b><br>%{{x}}<br>Popularity: %{{y:.1f}}<extra></extra>'
            ))
            fig_tvh.add_trace(go.Scatter(
                x=tt2['snapshot_date'], y=tt2['popularity'], name=tv_sel2,
                mode='lines+markers', line=dict(color=AMBER, width=2.5),
                marker=dict(size=6, color=AMBER),
                hovertemplate=f'<b>{tv_sel2}</b><br>%{{x}}<br>Popularity: %{{y:.1f}}<extra></extra>'
            ))
            ltvh = base_layout(360, "Popularity — Head-to-Head")
            ltvh['showlegend'] = True
            ltvh['legend'] = dict(font=dict(color=FONT_COL, size=12), bgcolor='rgba(0,0,0,0)', bordercolor=GRID, borderwidth=1)
            fig_tvh.update_layout(**ltvh)
            st.plotly_chart(fig_tvh, use_container_width=True)

    divider()

    # ── 05 By Air Year ──────────────────────────────────────────────────────
    section("05", "Average Popularity by First Air Year")
    st.markdown('<div class="section-caption">Which year\'s shows are most popular today</div>', unsafe_allow_html=True)

    fig_tv5 = go.Figure(go.Bar(
        x=tv_by_year['first_air_year'], y=tv_by_year['avg_popularity'],
        marker=dict(color=tv_by_year['avg_popularity'],
            colorscale=[[0,'#1a1530'],[0.5,'#2d2a6a'],[1,'#9b59b6']], line=dict(width=0)),
        text=tv_by_year['show_count'].astype(str) + ' shows',
        textposition='outside',
        textfont=dict(color='#5a6070', size=10, family='DM Mono, monospace'),
        hovertemplate='<b>%{x}</b><br>Avg Popularity: %{y:.2f}<extra></extra>'
    ))
    l_tv5 = base_layout(400)
    l_tv5['xaxis']['dtick'] = 1
    fig_tv5.update_layout(**l_tv5)
    st.plotly_chart(fig_tv5, use_container_width=True)

    divider()

    # ── 06 Genre Ratings ────────────────────────────────────────────────────
    section("06", "Average Rating by Genre")

    tv_genre_raw['primary_genre'] = tv_genre_raw['genre_ids'].apply(lambda g: parse_genre(g, TV_GENRE_MAP))
    tv_genre_agg = tv_genre_raw.groupby('primary_genre').agg(
        avg_rating=('avg_rating', 'mean'),
        show_count=('show_count', 'sum')
    ).reset_index()
    tv_genre_agg = tv_genre_agg[tv_genre_agg['primary_genre'] != 'Other'].sort_values('avg_rating', ascending=True)
    tv_genre_agg['avg_rating'] = tv_genre_agg['avg_rating'].round(2)

    fig_tv6 = go.Figure(go.Bar(
        x=tv_genre_agg['avg_rating'], y=tv_genre_agg['primary_genre'], orientation='h',
        marker=dict(color=tv_genre_agg['avg_rating'],
            colorscale=[[0,'#0d0d20'],[0.5,'#2d2a6a'],[1,'#9b59b6']], line=dict(width=0)),
        text=tv_genre_agg['avg_rating'].astype(str),
        textposition='outside',
        textfont=dict(color=FONT_COL, size=11, family='DM Mono, monospace'),
        customdata=tv_genre_agg['show_count'].values,
        hovertemplate='<b>%{y}</b><br>Avg Rating: %{x:.2f} / 10<br>Shows: %{customdata:,}<extra></extra>'
    ))
    l_tv6 = base_layout(460)
    l_tv6['xaxis']['range'] = [0, 10]
    fig_tv6.update_layout(**l_tv6)
    st.plotly_chart(fig_tv6, use_container_width=True)

    divider()

    # ── 07 Language Distribution ────────────────────────────────────────────
    section("07", "TV Shows by Original Language")

    tv_lang['language'] = tv_lang['original_language'].map(lambda x: LANG_MAP.get(str(x), str(x).upper()) if pd.notna(x) else 'Unknown')
    fig_tv7 = go.Figure(go.Pie(
        labels=tv_lang['language'], values=tv_lang['show_count'],
        hole=0.55, marker=dict(colors=PALETTE, line=dict(color='#0c0d10', width=2)),
        textfont=dict(family='Manrope, sans-serif', size=12, color='#ffffff'),
        hovertemplate='<b>%{label}</b><br>%{value:,} shows · %{percent}<extra></extra>',
        textposition='outside'
    ))
    fig_tv7.update_layout(
        height=440, paper_bgcolor=CHART_BG,
        font=dict(family="Manrope, sans-serif", color=FONT_COL),
        margin=dict(l=16, r=16, t=20, b=16), showlegend=True,
        legend=dict(font=dict(color=FONT_COL, size=12), bgcolor='rgba(0,0,0,0)', bordercolor=GRID, borderwidth=1),
        annotations=[dict(
            text=f"<b>{tv_lang['show_count'].sum():,}</b><br>shows",
            x=0.5, y=0.5, font=dict(size=18, color='#ffffff', family='Syne, sans-serif'),
            showarrow=False
        )]
    )
    st.plotly_chart(fig_tv7, use_container_width=True)

    divider()

    # ── 08 Most Voted ───────────────────────────────────────────────────────
    section("08", "Top 10 Most Voted TV Shows")
    st.markdown('<div class="section-caption">Shows with the highest total vote count — colored by their rating</div>', unsafe_allow_html=True)

    fig_tv8 = go.Figure(go.Bar(
        x=tv_top_voted['vote_count'], y=tv_top_voted['display_title'], orientation='h',
        marker=dict(
            color=tv_top_voted['vote_average'],
            colorscale=[[0,'#0d0d20'],[0.4,'#2d2a6a'],[0.7,'#6c3483'],[1,'#9b59b6']],
            line=dict(width=0), showscale=True,
            colorbar=dict(
                title=dict(text="Rating", font=dict(color=FONT_COL, size=11)),
                tickfont=dict(color=FONT_COL, size=10), thickness=8, len=0.7
            )
        ),
        text=['⭐ ' + str(round(r, 1)) for r in tv_top_voted['vote_average']],
        textposition='outside',
        textfont=dict(color=FONT_COL, size=11, family='DM Mono, monospace'),
        hovertemplate='<b>%{y}</b><br>Votes: %{x:,}<extra></extra>'
    ))
    l_tv8 = base_layout(420)
    l_tv8['yaxis']['autorange'] = 'reversed'
    fig_tv8.update_layout(**l_tv8)
    st.plotly_chart(fig_tv8, use_container_width=True)

# ─────────────────────────────────────────────────────────────────────────────
# FOOTER
# ─────────────────────────────────────────────────────────────────────────────
st.markdown("<div style='text-align:center;padding:8px 0 0;'><span style='font-family:DM Mono,monospace;font-size:10px;color:#2a2f3a;letter-spacing:2px;'>PROJECT INSIGHTS &nbsp;·&nbsp; SEM 6 MINI PROJECT &nbsp;·&nbsp; TMDB + AWS LAMBDA + S3 + ATHENA</span></div>", unsafe_allow_html=True)
