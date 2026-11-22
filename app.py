import re
import time
from html import escape
from io import BytesIO
from urllib.parse import urlparse

import streamlit as st
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import HRFlowable, ListFlowable, ListItem, Paragraph, SimpleDocTemplate, Spacer

from agents import build_search_agent, writer_chain, critic_chain
from tools import scrape_url


# ── Page config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Researchly | Multi-agent research workspace",
    page_icon="🔎",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ── Styles ───────────────────────────────────────────────────────────────────
st.markdown(
    """
<style>
@import url('https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,500;9..144,600;9..144,700&family=Source+Serif+4:opsz,wght@8..60,400;8..60,600&family=Inter:wght@400;500;600&display=swap');

:root {
    --bg: #F8F7F4;
    --card: #FFFFFF;
    --ink: #1C1B19;
    --muted: #6B6860;
    --line: #E7E4DC;
    --accent: #2F5D50;
    --accent-dark: #244A40;
    --accent-soft: #E3EEE9;
    --amber: #E8A600;
}

html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
    color: var(--ink);
}

.stApp { background: var(--bg); }

#MainMenu, footer, [data-testid="stToolbar"], .stDeployButton { display: none !important; }
[data-testid="stHeader"] { background: transparent; }

.block-container {
    padding: 1.2rem 3rem 4rem;
    max-width: 1080px;
}


/* ── Sidebar ── */

[data-testid="stSidebar"] {
    background: var(--card);
    border-right: 1px solid var(--line);
}

[data-testid="stSidebar"] .block-container,
[data-testid="stSidebarContent"] { padding-top: 1rem; }

.brand { display: flex; align-items: center; gap: .7rem; margin-bottom: 1.3rem; }

.brand-logo {
    width: 36px; height: 36px; border-radius: 10px;
    background: var(--accent); color: #fff;
    display: flex; align-items: center; justify-content: center;
    font-family: 'Fraunces', serif; font-weight: 700; font-size: 1.15rem;
}

.brand-name { font-family: 'Fraunces', serif; font-weight: 600; font-size: 1.15rem; line-height: 1.1; }
.brand-sub { font-size: .75rem; color: var(--muted); }

.side-label {
    font-size: .7rem; font-weight: 600; letter-spacing: .08em;
    text-transform: uppercase; color: var(--muted);
    margin: 1.4rem 0 .5rem;
}

.side-row {
    display: flex; justify-content: space-between; align-items: center;
    font-size: .9rem; font-weight: 600; margin-bottom: .4rem;
}

.count {
    background: var(--accent-soft); color: var(--accent);
    font-size: .72rem; font-weight: 600;
    padding: .1rem .5rem; border-radius: 999px;
}

.side-empty { font-size: .82rem; color: var(--muted); }

.st-key-history button {
    justify-content: flex-start !important;
    text-align: left !important;
    background: transparent !important;
    border: 1px solid transparent !important;
    font-weight: 500 !important;
    font-size: .85rem !important;
    padding: .45rem .6rem !important;
}

.st-key-history button:hover {
    background: var(--bg) !important;
    border-color: var(--line) !important;
}


/* ── Top bar ── */

.topbar {
    display: flex; justify-content: space-between; align-items: center;
    padding-bottom: .9rem; margin-bottom: 2.2rem;
    border-bottom: 1px solid var(--line);
    font-size: .85rem; color: var(--muted);
}

.topbar b { color: var(--ink); font-weight: 600; }

.saved::before {
    content: ''; display: inline-block; width: 7px; height: 7px;
    border-radius: 50%; background: var(--accent); margin-right: .45rem;
}


/* ── Hero ── */

.eyebrow {
    font-size: .75rem; font-weight: 600; letter-spacing: .1em;
    text-transform: uppercase; color: var(--accent); margin-bottom: .7rem;
}

.hero-title {
    font-family: 'Fraunces', serif; font-weight: 600;
    font-size: 3rem; line-height: 1.08; letter-spacing: -0.025em;
    margin: 0 0 .8rem;
}

.hero-sub {
    font-size: 1.05rem; color: var(--muted); line-height: 1.6;
    max-width: 560px; margin-bottom: 1.8rem;
}

.try-label {
    font-size: .8rem; font-weight: 600; color: var(--muted);
    margin: 1.4rem 0 .5rem;
}


/* ── Input ── */

.stTextArea textarea {
    background: var(--card) !important;
    border: 1.5px solid var(--line) !important;
    border-radius: 14px !important;
    font-size: 1rem !important;
    padding: 1rem 1.1rem !important;
    color: var(--ink) !important;
}

.stTextArea textarea:focus {
    border-color: var(--accent) !important;
    box-shadow: 0 0 0 3px rgba(47,93,80,.15) !important;
}

.stTextArea label p { font-weight: 600 !important; font-size: .9rem !important; }


/* ── Buttons ── */

.stButton > button,
.stDownloadButton > button {
    border-radius: 12px !important;
    font-family: 'Inter', sans-serif !important;
    font-weight: 600 !important;
    font-size: .95rem !important;
    padding: .6rem 1.3rem !important;
    border: 1.5px solid var(--line) !important;
    background: var(--card) !important;
    color: var(--ink) !important;
    transition: background .15s, border-color .15s !important;
}

.stButton > button:hover,
.stDownloadButton > button:hover {
    border-color: var(--accent) !important;
    color: var(--accent) !important;
}

.stButton > button[kind="primary"] {
    background: var(--accent) !important;
    border-color: var(--accent) !important;
    color: #fff !important;
}

.stButton > button[kind="primary"]:hover {
    background: var(--accent-dark) !important;
    border-color: var(--accent-dark) !important;
    color: #fff !important;
}

button:focus-visible { outline: 3px solid var(--accent) !important; outline-offset: 2px !important; }

.st-key-chips button,
.st-key-recent button {
    justify-content: flex-start !important;
    text-align: left !important;
    font-weight: 500 !important;
    font-size: .9rem !important;
}

.st-key-chips button { border-radius: 999px !important; padding: .4rem 1rem !important; }


/* ── Section headings ── */

.section { margin: 2.8rem 0 .3rem; }

.section-title {
    font-family: 'Fraunces', serif; font-weight: 600;
    font-size: 1.5rem; letter-spacing: -0.015em; margin: 0;
}

.section-sub { font-size: .9rem; color: var(--muted); margin-top: .2rem; }


/* ── Pipeline ── */

.pipeline {
    display: grid; grid-template-columns: repeat(4, 1fr);
    gap: .8rem; margin: 1rem 0 .4rem;
}

@media (max-width: 800px) { .pipeline { grid-template-columns: repeat(2, 1fr); } }

.pstep {
    background: var(--card); border: 1px solid var(--line);
    border-radius: 14px; padding: 1rem 1.1rem;
}

.pnum { font-size: .72rem; font-weight: 600; color: var(--muted); margin-bottom: .5rem; }
.pname { font-family: 'Fraunces', serif; font-weight: 600; font-size: 1.15rem; }
.pdesc { font-size: .82rem; color: var(--muted); margin: .15rem 0 .8rem; min-height: 2.4em; }

.pill {
    display: inline-block; font-size: .72rem; font-weight: 600;
    padding: .15rem .6rem; border-radius: 999px;
    background: #EEEDE8; color: var(--muted);
}

.pstep.running { border-color: var(--amber); animation: pulse 1.3s ease-in-out infinite; }
.pstep.running .pill { background: #FCF1D6; color: #8A5A00; }
.pstep.done .pill { background: var(--accent-soft); color: var(--accent); }
.pstep.error { border-color: #C0392B; }
.pstep.error .pill { background: #F8DEDA; color: #B3261E; }

@keyframes pulse {
    0%, 100% { box-shadow: 0 0 0 0 rgba(232,166,0,.35); }
    50% { box-shadow: 0 0 0 6px rgba(232,166,0,0); }
}

@media (prefers-reduced-motion: reduce) { .pstep.running { animation: none; } }


/* ── Report page ── */

.page-title {
    font-family: 'Fraunces', serif; font-weight: 600;
    font-size: 2.3rem; line-height: 1.12; letter-spacing: -0.02em;
    margin: 0 0 1.1rem;
}

.meta { display: flex; gap: .6rem; flex-wrap: wrap; margin-bottom: 1rem; }

.meta span {
    background: var(--card); border: 1px solid var(--line);
    border-radius: 999px; padding: .25rem .8rem;
    font-size: .8rem; color: var(--muted);
}

.meta b { color: var(--ink); }

.st-key-report_card,
.st-key-critic_card {
    background: var(--card);
    border: 1px solid var(--line);
    border-radius: 16px;
    padding: 2rem 2.4rem;
}

.st-key-report_card p,
.st-key-report_card li {
    font-family: 'Source Serif 4', Georgia, serif;
    font-size: 1.05rem; line-height: 1.75;
}

.st-key-report_card h1,
.st-key-report_card h2,
.st-key-report_card h3 {
    font-family: 'Fraunces', serif; letter-spacing: -0.015em; color: var(--ink);
}

.score-box {
    display: flex; align-items: center; justify-content: space-between;
    gap: 1rem; padding-bottom: 1.2rem; margin-bottom: 1.2rem;
    border-bottom: 1px solid var(--line);
}

.score-num { font-family: 'Fraunces', serif; font-weight: 600; font-size: 2.6rem; color: var(--accent); }
.score-den { font-size: 1rem; color: var(--muted); margin-left: .25rem; }
.score-label { font-size: .85rem; color: var(--muted); }


/* ── Sources ── */

.source {
    display: flex; gap: 1rem; align-items: flex-start;
    background: var(--card); border: 1px solid var(--line);
    border-radius: 12px; padding: .9rem 1.1rem; margin-bottom: .5rem;
    text-decoration: none !important;
}

.source:hover { border-color: var(--accent); }
.source-num { font-size: .8rem; font-weight: 600; color: var(--muted); padding-top: .15rem; }
.source-domain { font-weight: 600; color: var(--ink); font-size: .95rem; }
.source-url { color: var(--accent); font-size: .8rem; word-break: break-all; }


/* ── Expanders ── */

details summary { font-weight: 600 !important; color: var(--ink) !important; }
</style>
""",
    unsafe_allow_html=True,
)


# ── Constants ────────────────────────────────────────────────────────────────

STAGES = [
    ("search", "Search", "Discovering useful sources"),
    ("scrape", "Read", "Extracting key evidence"),
    ("write", "Write", "Building your report"),
    ("critique", "Critique", "Checking quality and gaps"),
]

SAMPLE_TOPICS = [
    "How does urban design affect mental wellbeing?",
    "Can community solar lower household energy costs?",
    "What makes a trustworthy AI research assistant?",
]


# ── PDF export ───────────────────────────────────────────────────────────────

_CHAR_MAP = {
    "\u2018": "'", "\u2019": "'", "\u201c": '"', "\u201d": '"',
    "\u2013": "-", "\u2014": "-", "\u2212": "-", "\u2026": "...",
    "\u2022": "-", "\u00a0": " ", "\u2192": "->", "\u2190": "<-",
    "\u2265": ">=", "\u2264": "<=", "\u2248": "~", "\u00d7": "x",
}


def _clean(text: str) -> str:
    """Core PDF fonts only support Latin-1, so swap/strip anything else."""
    for k, v in _CHAR_MAP.items():
        text = text.replace(k, v)
    return text.encode("latin-1", "ignore").decode("latin-1")


def _inline(text: str) -> str:
    """Markdown inline formatting -> reportlab mini-HTML."""
    text = escape(_clean(text), quote=False)
    text = re.sub(r"\[([^\]]+)\]\((https?://[^)\s]+)\)",
                  r'<a href="\2" color="#2F5D50"><u>\1</u></a>', text)
    text = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", text)
    text = re.sub(r"(?<![\*\w])\*(?!\s)(.+?)(?<!\s)\*(?![\*\w])", r"<i>\1</i>", text)
    text = re.sub(r"`([^`]+)`", r'<font face="Courier">\1</font>', text)
    return text


def markdown_to_pdf(title: str, markdown_text: str) -> bytes:
    ink = colors.HexColor("#1C1B19")
    accent = colors.HexColor("#2F5D50")

    body = ParagraphStyle("body", fontName="Times-Roman", fontSize=11, leading=16,
                          textColor=ink, alignment=TA_LEFT, spaceAfter=6)
    h1 = ParagraphStyle("h1", fontName="Helvetica-Bold", fontSize=20, leading=24,
                        textColor=ink, spaceBefore=14, spaceAfter=8)
    h2 = ParagraphStyle("h2", fontName="Helvetica-Bold", fontSize=15, leading=19,
                        textColor=accent, spaceBefore=12, spaceAfter=6)
    h3 = ParagraphStyle("h3", fontName="Helvetica-Bold", fontSize=12.5, leading=16,
                        textColor=ink, spaceBefore=10, spaceAfter=4)
    doc_title = ParagraphStyle("title", parent=h1, fontSize=24, leading=28, spaceBefore=0)

    buf = BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4, leftMargin=22 * mm, rightMargin=22 * mm,
                            topMargin=20 * mm, bottomMargin=20 * mm,
                            title=_clean(title), author="Researchly")

    story = [Paragraph(_inline(title), doc_title),
             HRFlowable(width="100%", thickness=1, color=accent, spaceAfter=10)]

    para, items, ordered = [], [], False

    def flush_para():
        nonlocal para
        if para:
            story.append(Paragraph(_inline(" ".join(para)), body))
            para = []

    def flush_list():
        nonlocal items
        if items:
            story.append(ListFlowable(
                [ListItem(Paragraph(_inline(t), body), leftIndent=14) for t in items],
                bulletType="1" if ordered else "bullet",
                bulletFormat="%s." if ordered else None,
                start=None if ordered else "\u2022",
                leftIndent=16, bulletFontName="Helvetica", bulletFontSize=11))
            story.append(Spacer(1, 4))
            items = []

    for raw in markdown_text.splitlines():
        line = raw.rstrip()
        s = line.strip()

        if not s:
            flush_para(); flush_list(); continue

        m = re.match(r"^(#{1,6})\s+(.*)$", s)
        if m:
            flush_para(); flush_list()
            level = len(m.group(1))
            story.append(Paragraph(_inline(m.group(2)), h1 if level == 1 else h2 if level == 2 else h3))
            continue

        if re.match(r"^(-{3,}|\*{3,}|_{3,})$", s):
            flush_para(); flush_list()
            story.append(HRFlowable(width="100%", thickness=0.5, color=colors.lightgrey, spaceBefore=6, spaceAfter=6))
            continue

        b = re.match(r"^[-*+]\s+(.*)$", s)
        n = re.match(r"^\d+[.)]\s+(.*)$", s)
        if b or n:
            flush_para()
            if items and ordered != bool(n):
                flush_list()
            ordered = bool(n)
            items.append((b or n).group(1))
            continue

        flush_list()
        para.append(s)

    flush_para(); flush_list()

    def footer(canvas, d):
        canvas.saveState()
        canvas.setFont("Helvetica", 8)
        canvas.setFillColor(colors.grey)
        canvas.drawString(22 * mm, 12 * mm, "Generated by Researchly")
        canvas.drawRightString(A4[0] - 22 * mm, 12 * mm, f"Page {d.page}")
        canvas.restoreState()

    doc.build(story, onFirstPage=footer, onLaterPages=footer)
    return buf.getvalue()


# ── Helpers ──────────────────────────────────────────────────────────────────

def render_pipeline(placeholder, states: dict, active: bool = False):
    """Draw the four agent cards."""
    labels = {
        "waiting": "Queued" if active else "Ready",
        "running": "Running",
        "done": "Completed",
        "error": "Failed",
    }

    html = ['<div class="pipeline">']

    for i, (key, name, desc) in enumerate(STAGES, start=1):
        state = states.get(key, "waiting")
        html.append(
            f'<div class="pstep {state}">'
            f'<div class="pnum">0{i}</div>'
            f'<div class="pname">{name}</div>'
            f'<div class="pdesc">{desc}</div>'
            f'<span class="pill">{labels[state]}</span>'
            f'</div>'
        )

    html.append("</div>")
    placeholder.markdown("".join(html), unsafe_allow_html=True)


def extract_urls(text: str) -> list[str]:
    """Extract unique URLs from search-agent output."""
    urls = re.findall(r"https?://[^\s<>\[\]\)\|]+", text or "")

    seen, clean = set(), []

    for u in urls:
        u = u.rstrip(").,;:'\"")
        if u not in seen:
            seen.add(u)
            clean.append(u)

    return clean


def extract_score(feedback: str):
    """Return the number from 'Score: X/10' (or None)."""
    m = re.search(
        r"Score\s*:\s*(\d+(?:\.\d+)?)\s*/\s*10",
        feedback or "",
        re.IGNORECASE,
    )
    return m.group(1) if m else None


def section_header(title: str, sub: str = ""):
    sub_html = f'<div class="section-sub">{sub}</div>' if sub else ""
    st.markdown(
        f'<div class="section"><div class="section-title">{title}</div>{sub_html}</div>',
        unsafe_allow_html=True,
    )


def short(text: str, n: int = 44) -> str:
    return text if len(text) <= n else text[:n].rstrip() + "…"


# ── Session state & callbacks ────────────────────────────────────────────────

if "runs" not in st.session_state:
    st.session_state.runs = []

if "selected" not in st.session_state:
    st.session_state.selected = None

if "view" not in st.session_state:
    st.session_state.view = "new"


def go_new():
    st.session_state.view = "new"


def open_run(i: int):
    st.session_state.selected = i
    st.session_state.view = "report"


def set_topic(t: str):
    st.session_state.topic_input = t


# ── Pipeline runner (your original logic, unchanged) ─────────────────────────

def run_pipeline(topic: str, tracker_slot) -> bool:
    states, state = {}, {}
    started = time.time()
    current = None

    try:
        # STEP 1 — SEARCH
        current = "search"
        states[current] = "running"
        render_pipeline(tracker_slot, states, active=True)

        search_agent = build_search_agent()

        sr = search_agent.invoke(
            {
                "messages": [
                    (
                        "user",
                        f"""
Find recent, reliable and detailed information about:

{topic}

Use the web search tool to research the topic.

IMPORTANT:
- Find at least 3 reliable sources.
- Prefer recent and trustworthy sources.
- Return the title and FULL URL of every useful source.
- Keep the URLs exactly as returned by the search tool.
- Do not invent URLs.
- Provide concise research notes for each source.
- Make sure the source URLs are clearly visible in your response.
""",
                    )
                ]
            }
        )

        state["search_results"] = sr["messages"][-1].content
        states[current] = "done"
        render_pipeline(tracker_slot, states, active=True)

        # STEP 2 — SCRAPE TOP URL
        current = "scrape"
        states[current] = "running"
        render_pipeline(tracker_slot, states, active=True)

        urls = extract_urls(state["search_results"])

        if urls:
            state["scraped_url"] = urls[0]
            state["scraped_content"] = scrape_url.invoke(urls[0])
        else:
            state["scraped_url"] = None
            state["scraped_content"] = "No URL found in search results."

        states[current] = "done"
        render_pipeline(tracker_slot, states, active=True)

        # STEP 3 — WRITER
        current = "write"
        states[current] = "running"
        render_pipeline(tracker_slot, states, active=True)

        research_combined = (
            f"SEARCH RESULTS:\n{state['search_results']}\n\n"
            f"DETAILED SCRAPED CONTENT:\n{state['scraped_content']}"
        )

        state["report"] = writer_chain.invoke(
            {"topic": topic, "research": research_combined}
        )

        states[current] = "done"
        render_pipeline(tracker_slot, states, active=True)

        # STEP 4 — CRITIC
        current = "critique"
        states[current] = "running"
        render_pipeline(tracker_slot, states, active=True)

        state["feedback"] = critic_chain.invoke(
            {"report": state["report"], "research": research_combined}
        )

        states[current] = "done"
        render_pipeline(tracker_slot, states, active=True)

        # SAVE RUN
        state["topic"] = topic
        state["seconds"] = time.time() - started

        st.session_state.runs.append(state)
        st.session_state.selected = len(st.session_state.runs) - 1

        return True

    except Exception as e:
        if current:
            states[current] = "error"
            render_pipeline(tracker_slot, states, active=True)

        st.error(f"The {current} stage failed: {e}")
        return False


# ── Sidebar ──────────────────────────────────────────────────────────────────

runs = st.session_state.runs

with st.sidebar:
    st.markdown(
        """
<div class="brand">
    <div class="brand-logo">R</div>
    <div>
        <div class="brand-name">Researchly</div>
        <div class="brand-sub">Personal workspace</div>
    </div>
</div>
""",
        unsafe_allow_html=True,
    )

    st.button(
        "＋  New research",
        type="primary",
        use_container_width=True,
        on_click=go_new,
        key="new_btn",
    )

    st.markdown('<div class="side-label">Workspace</div>', unsafe_allow_html=True)

    st.markdown(
        f'<div class="side-row"><span>Research History</span>'
        f'<span class="count">{len(runs)}</span></div>',
        unsafe_allow_html=True,
    )

    if runs:
        with st.container(key="history"):
            for i in reversed(range(len(runs))):
                st.button(
                    short(runs[i]["topic"], 34),
                    key=f"hist_{i}",
                    on_click=open_run,
                    args=(i,),
                    use_container_width=True,
                )
    else:
        st.markdown(
            '<div class="side-empty">Your finished reports will appear here.</div>',
            unsafe_allow_html=True,
        )


# ── Top bar ──────────────────────────────────────────────────────────────────

st.markdown(
    """
<div class="topbar">
    <span>Workspace &nbsp;/&nbsp; <b>Research</b></span>
    <span class="saved">Saved in this session</span>
</div>
""",
    unsafe_allow_html=True,
)


# ── Home view ────────────────────────────────────────────────────────────────

def render_home():
    st.markdown(
        """
<div class="eyebrow">A clearer path to knowledge</div>
<div class="hero-title">Research starts with a question.</div>
<div class="hero-sub">
    Bring a topic. Your four-agent research team will find sources,
    read deeply, write clearly, and check its work.
</div>
""",
        unsafe_allow_html=True,
    )

    topic = st.text_area(
        "What would you like to research?",
        placeholder="e.g. Recent breakthroughs in solid-state batteries",
        height=110,
        key="topic_input",
    )

    run_btn = st.button("Start research", type="primary")

    st.markdown('<div class="try-label">Try a topic</div>', unsafe_allow_html=True)

    with st.container(key="chips"):
        for i, t in enumerate(SAMPLE_TOPICS):
            st.button(t, key=f"chip_{i}", on_click=set_topic, args=(t,))

    section_header("Research pipeline", "Four specialists, one carefully reviewed report")

    tracker_slot = st.empty()
    render_pipeline(tracker_slot, {})

    if run_btn:
        if not topic.strip():
            st.warning("Enter a topic to start.")
        else:
            ok = run_pipeline(topic.strip(), tracker_slot)
            if ok:
                st.session_state.view = "report"
                st.rerun()

    if runs:
        section_header("Recent research", "Pick up where you left off")

        with st.container(key="recent"):
            for i in reversed(range(len(runs))[-3:]):
                score = extract_score(runs[i]["feedback"])
                suffix = f"   ·   {score} / 10" if score else ""
                st.button(
                    short(runs[i]["topic"], 70) + suffix,
                    key=f"recent_{i}",
                    on_click=open_run,
                    args=(i,),
                    use_container_width=True,
                )


# ── Report view ──────────────────────────────────────────────────────────────

def render_report(run: dict):
    words = len(run["report"].split())
    minutes = max(1, round(words / 200))

    sources = extract_urls(run["search_results"])
    scraped_url = run.get("scraped_url")
    if scraped_url and scraped_url not in sources:
        sources.append(scraped_url)

    score = extract_score(run["feedback"])

    # Title
    st.markdown(
        f'<div class="eyebrow">Research report · {minutes} min read</div>'
        f'<div class="page-title">{escape(run["topic"])}</div>'
        f'<div class="meta">'
        f'<span><b>{words:,}</b> words</span>'
        f'<span><b>{len(sources)}</b> sources</span>'
        f'<span><b>{run["seconds"]:.0f}s</b> to complete</span>'
        f'<span>Critic <b>{score + " / 10" if score else "n/a"}</b></span>'
        f'</div>',
        unsafe_allow_html=True,
    )

    st.download_button(
        "Download report (PDF)",
        data=markdown_to_pdf(run["topic"], run["report"]),
        file_name=f"report_{int(time.time())}.pdf",
        mime="application/pdf",
    )

    # Pipeline (all completed)
    section_header("Research pipeline")
    render_pipeline(
        st.empty(),
        {k: "done" for k, _, _ in STAGES},
    )

    # Report
    section_header("Report")
    with st.container(key="report_card"):
        st.markdown(run["report"])

    # Critic review
    section_header("Critic review", "Independent quality check")
    with st.container(key="critic_card"):
        st.markdown(
            f'<div class="score-box">'
            f'<div class="score-label">Evidence &amp; clarity</div>'
            f'<div><span class="score-num">{score or "n/a"}</span>'
            f'{"<span class=score-den>/ 10</span>" if score else ""}</div>'
            f'</div>',
            unsafe_allow_html=True,
        )

        if run["feedback"].strip():
            st.markdown(run["feedback"])
        else:
            st.warning("The critic did not return any feedback.")

    # Sources
    section_header("Sources", f"{len(sources)} references in this report")

    if sources:
        for i, u in enumerate(sources, start=1):
            domain = urlparse(u).netloc.replace("www.", "") or u
            st.markdown(
                f'<a class="source" href="{escape(u)}" target="_blank" rel="noopener">'
                f'<span class="source-num">{i:02d}</span>'
                f'<span>'
                f'<div class="source-domain">{escape(domain)}</div>'
                f'<div class="source-url">{escape(u)}</div>'
                f'</span>'
                f'</a>',
                unsafe_allow_html=True,
            )
    else:
        st.info("The search agent did not return any links.")

    if scraped_url:
        st.caption(f"Full text was read from: {scraped_url}")

    with st.expander("Raw search output"):
        st.text(run["search_results"])

    with st.expander("Raw scraped content"):
        st.text(run["scraped_content"])


# ── Router ───────────────────────────────────────────────────────────────────

if st.session_state.view == "report" and runs:
    sel = st.session_state.selected
    render_report(runs[sel if sel is not None else -1])
else:
    render_home()