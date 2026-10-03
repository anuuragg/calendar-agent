import asyncio
import html
import json
import re
from datetime import datetime

import streamlit as st

from mcp import Client, StdioServerParameters

from src.agent import (
    run_agent,
    convert_mcp_tools_to_groq,
)


# ============================================================
# CONFIG
# ============================================================

SUGGESTIONS = [
    "What's on my calendar today?",
    "Schedule a walk at 9 PM for 2 hours",
    "Schedule a 2 hour brainstorming session tomorrow",
    "Find my meetings this week",
]

st.set_page_config(
    page_title="Calendar Agent",
    page_icon="📅",
    layout="centered",
    initial_sidebar_state="collapsed",
)


# ============================================================
# CSS (iMessage look)
# ============================================================

CSS = """
<style>

html {
    color-scheme: light;
}

#MainMenu, header, footer {
    visibility: hidden;
}

[data-testid="stDecoration"],
[data-testid="stToolbar"],
[data-testid="stStatusWidget"] {
    display: none !important;
}

.stApp,
[data-testid="stAppViewContainer"],
[data-testid="stMain"] {
    background: #ffffff;
}

.stApp {
    font-family: -apple-system, BlinkMacSystemFont, "SF Pro Text",
                 "Helvetica Neue", Helvetica, Arial, sans-serif;
}

.block-container {
    max-width: 760px;
    padding-top: 110px;
    padding-bottom: 110px;
}

/* tight vertical rhythm, like Messages */

.block-container [data-testid="stVerticalBlock"] {
    gap: 0.15rem;
}

/* ---------- Header ---------- */

.app-header {
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    z-index: 100;

    height: 88px;

    display: flex;
    flex-direction: row;
    align-items: center;
    justify-content: flex-start;
    gap: 10px;
    padding-left: max(30px, calc((100vw - 760px) / 2 + 28px));

    background: rgba(246, 246, 246, 0.85);
    backdrop-filter: blur(20px);
    -webkit-backdrop-filter: blur(20px);
    border-bottom: 1px solid rgba(0, 0, 0, 0.12);
}

.avatar {
    width: 38px;
    height: 38px;
    border-radius: 50%;

    display: flex;
    align-items: center;
    justify-content: center;

    background: linear-gradient(180deg, #a6abb8 0%, #7d8290 100%);
    font-size: 19px;
}

.contact {
    font-size: 16px;
    font-weight: 600;
    color: #000000;
    letter-spacing: 0.1px;
}

/* ---------- Timestamp ---------- */

.timestamp {
    text-align: center;
    font-size: 11px;
    color: #8e8e93;
    margin: 14px 0 10px;
}

.timestamp b {
    font-weight: 600;
}

/* ---------- Sent bubbles + typing (plain HTML) ---------- */

.row {
    display: flex;
    width: 100%;
    padding: 0 12px;
    margin-top: 8px;
}

.row.grouped {
    margin-top: 2px;
}

.row.sent {
    justify-content: flex-end;
}

.row.received {
    justify-content: flex-start;
}

.bubble {
    position: relative;
    max-width: 75%;
    padding: 7px 13px;
    border-radius: 18px;

    font-size: 16px;
    line-height: 1.3;
    word-wrap: break-word;
}

.bubble.sent {
    background: #007aff;
    color: #ffffff;
}

.bubble.received {
    background: #e9e9eb;
    color: #000000;
}

.bubble.tail::before,
.bubble.tail::after {
    content: "";
    position: absolute;
    bottom: 0;
}

.bubble.sent.tail::before {
    right: -8px;
    height: 18px;
    width: 20px;
    background: #007aff;
    border-bottom-left-radius: 15px;
}

.bubble.sent.tail::after {
    right: -10px;
    width: 10px;
    height: 20px;
    background: #ffffff;
    border-bottom-left-radius: 10px;
}

.bubble.received.tail::before {
    left: -8px;
    height: 18px;
    width: 20px;
    background: #e9e9eb;
    border-bottom-right-radius: 15px;
}

.bubble.received.tail::after {
    left: -10px;
    width: 10px;
    height: 20px;
    background: #ffffff;
    border-bottom-right-radius: 10px;
}

.status {
    text-align: right;
    padding: 8px 14px 6px 0;
    font-size: 11px;
    color: #8e8e93;
}

/* Typing indicator */

.typing {
    padding: 12px 15px;
}

.typing span {
    display: inline-block;
    width: 8px;
    height: 8px;
    margin: 0 2px;
    border-radius: 50%;
    background: #8e8e93;
    animation: blink 1.3s infinite both;
}

.typing span:nth-child(2) {
    animation-delay: 0.2s;
}

.typing span:nth-child(3) {
    animation-delay: 0.4s;
}

@keyframes blink {
    0%, 80%, 100% { opacity: 0.25; }
    40% { opacity: 1; }
}

/* ---------- Received text bubble (rendered markdown) ---------- */

[class*="st-key-bot_"] {
    position: relative;
    width: fit-content;
    max-width: 75%;
    margin-left: 12px;
    padding: 8px 14px;
    gap: 0.3rem;

    background: #e9e9eb;
    border-radius: 18px;
}

[class*="st-key-bot_"][class*="_g0_"] {
    margin-top: 6px;
}

[class*="st-key-bot_"] :is(p, li, td, th, span, strong, em, h1, h2, h3, h4, div) {
    color: #000000 !important;
}

[class*="st-key-bot_"] a {
    color: #007aff !important;
}

/* Streamlit gives every markdown container a negative bottom margin, which
   makes bubbles end early and overlap the next row. Cancel it everywhere. */

[data-testid="stMarkdownContainer"] {
    margin-bottom: 0 !important;
}

[class*="st-key-bot_"] [data-testid="stMarkdownContainer"] > :last-child,
[class*="st-key-evts_"] [data-testid="stMarkdownContainer"] > :last-child {
    margin-bottom: 0 !important;
}

[class*="st-key-bot_"] [data-testid="stMarkdownContainer"] p {
    margin: 0 0 6px;
    font-size: 16px;
    line-height: 1.35;
}

[class*="st-key-bot_"] :is(ul, ol) {
    margin: 0 0 6px;
    padding-left: 22px;
}

[class*="st-key-bot_"] :is(ul, ol) :is(ul, ol) {
    margin: 2px 0 0;
    padding-left: 20px;
}

[class*="st-key-bot_"] li {
    margin: 0 0 2px;
    padding-left: 0;
    line-height: 1.35;
}

[class*="st-key-bot_"] li > p {
    margin: 0;
}

[class*="st-key-bot_"] table td:first-child {
    white-space: nowrap;
}

[class*="st-key-bot_"] :is(h1, h2, h3, h4) {
    font-size: 16px;
    font-weight: 600;
    margin: 4px 0;
    padding: 0;
}

[class*="st-key-bot_"] table {
    border-collapse: collapse;
    font-size: 14px;
}

[class*="st-key-bot_"] :is(th, td) {
    border: 1px solid #c7c7cc;
    padding: 4px 8px;
    background: transparent !important;
}

[class*="st-key-bot_"] code {
    background: rgba(0, 0, 0, 0.07);
    border-radius: 4px;
}

/* tail on the last bubble of a reply */

[class*="st-key-bot_"][class*="_t1_"]::before,
[class*="st-key-bot_"][class*="_t1_"]::after {
    content: "";
    position: absolute;
    bottom: 0;
}

[class*="st-key-bot_"][class*="_t1_"]::before {
    left: -8px;
    height: 18px;
    width: 20px;
    background: #e9e9eb;
    border-bottom-right-radius: 15px;
}

[class*="st-key-bot_"][class*="_t1_"]::after {
    left: -10px;
    width: 10px;
    height: 20px;
    background: #ffffff;
    border-bottom-right-radius: 10px;
}

/* ---------- Event blocks ---------- */

[class*="st-key-evts_"] {
    width: 75%;
    min-width: 260px;
    margin-left: 12px;
}

[class*="st-key-evts_"][class*="_g0_"] {
    margin-top: 6px;
}

[class*="st-key-evts_"] [data-testid="stExpander"] {
    background: #f2f2f7 !important;
    border: none !important;
    border-left: 4px solid #007aff !important;
    border-radius: 10px !important;
    overflow: hidden;
}

[class*="st-key-evts_"] [data-testid="stExpander"] details {
    background: transparent !important;
    border: none !important;
}

[class*="st-key-evts_"] [data-testid="stExpander"] summary {
    padding: 10px 14px;
}

[class*="st-key-evts_"] :is(p, span, summary, strong, li, div) {
    color: #000000 !important;
}

[class*="st-key-evts_"] summary p {
    margin: 0;
    font-size: 15px;
    font-weight: 600;
}

[class*="st-key-evts_"] summary svg {
    color: #8e8e93 !important;
}

[class*="st-key-evts_"] [data-testid="stExpanderDetails"] {
    padding: 4px 14px 12px 14px;
}

[class*="st-key-evts_"] [data-testid="stExpanderDetails"] [data-testid="stVerticalBlock"] {
    gap: 0.4rem;
}

[class*="st-key-evts_"] [data-testid="stExpanderDetails"] [data-testid="stElementContainer"] {
    overflow: visible;
    height: auto;
}

[class*="st-key-evts_"] [data-testid="stExpanderDetails"] p {
    margin: 0;
    font-size: 14px;
    line-height: 1.4;
}

/* ---------- Suggestion chips ---------- */

div.stButton > button {
    border-radius: 18px;
    border: 1px solid #007aff;
    background: #ffffff;
    color: #007aff;
    font-size: 13px;
    padding: 8px 14px;
    transition: 0.15s ease;
}

div.stButton > button:hover {
    background: #007aff;
    color: #ffffff;
    border-color: #007aff;
}

/* ---------- Input bar ---------- */

[data-testid="stBottom"],
[data-testid="stBottom"] > div,
[data-testid="stBottomBlockContainer"] {
    background: #ffffff !important;
}

[data-testid="stChatInput"] {
    background: #ffffff !important;
    border: 1px solid #c7c7cc !important;
    border-radius: 22px !important;
    overflow: hidden;
}

[data-testid="stChatInput"] div,
[data-testid="stChatInput"] textarea {
    background: #ffffff !important;
    border-color: transparent !important;
    box-shadow: none !important;
}

[data-testid="stChatInput"] textarea {
    color: #000000 !important;
    -webkit-text-fill-color: #000000 !important;
    font-size: 16px !important;
}

[data-testid="stChatInput"] textarea::placeholder {
    color: #8e8e93 !important;
    -webkit-text-fill-color: #8e8e93 !important;
    opacity: 1;
}

[data-testid="stChatInputSubmitButton"] {
    background: #007aff !important;
    color: #ffffff !important;
    border-radius: 50% !important;
}

[data-testid="stChatInputSubmitButton"]:disabled {
    background: #c7c7cc !important;
}

/* Hide default chat avatars */

[data-testid="stChatMessageAvatar"] {
    display: none !important;
}

</style>
"""

st.markdown(CSS, unsafe_allow_html=True)


# ============================================================
# SESSION STATE
# ============================================================

if "messages" not in st.session_state:
    st.session_state.messages = []

if "pending" not in st.session_state:
    st.session_state.pending = False


# ============================================================
# MCP
# ============================================================

async def process_message(user_message):

    server_params = StdioServerParameters(
        command="python",
        args=["mcp/server.py"],
    )

    client = Client(server_params)

    await client.__aenter__()

    try:
        tools_result = await client.list_tools()

        groq_tools = convert_mcp_tools_to_groq(
            tools_result.tools
        )

        response = await run_agent(
            user_message,
            client,
            groq_tools,
        )

        return response

    finally:
        await client.__aexit__(None, None, None)


# ============================================================
# TEXT + EVENT PARSING
# ============================================================

# The model wraps events in a fenced block tagged "events", holding a JSON list:
# ```events
# [{"title": "DSA", "date": "2026-10-03", "start": "10:00", "end": "13:00",
#   "location": "", "description": ""}]
# ```
EVENTS_RE = re.compile(r"```events\s*(.*?)```", re.DOTALL | re.IGNORECASE)


def clean_text(text):
    """Normalise the odd unicode spaces/hyphens some models emit."""
    return (
        str(text)
        .replace(" ", " ")
        .replace(" ", " ")
        .replace("‑", "-")
    )


def md_safe(text):
    """Stop '$' from being treated as LaTeX by Streamlit's markdown."""
    return str(text).replace("$", "\\$")


def parse_events(raw):
    try:
        data = json.loads(raw)
    except ValueError:
        return None

    if isinstance(data, dict):
        data = data.get("events", [data])

    if not isinstance(data, list):
        return None

    return [e for e in data if isinstance(e, dict)]


def split_reply(text):
    """Split a reply into [("text", str) | ("events", list)] parts."""
    parts = []
    pos = 0

    for match in EVENTS_RE.finditer(text):

        before = text[pos:match.start()].strip()
        if before:
            parts.append(("text", before))

        events = parse_events(match.group(1))

        if events is None:
            parts.append(("text", match.group(0)))
        else:
            parts.append(("events", events))

        pos = match.end()

    tail = text[pos:].strip()
    if tail:
        parts.append(("text", tail))

    return parts


def flat(value):
    """Accept '10:00', ISO strings, or Google-style {'dateTime': ...}."""
    if isinstance(value, dict):
        value = value.get("dateTime") or value.get("date") or ""
    return str(value or "").strip()


def fmt_clock(value):
    value = flat(value)

    if not value or re.fullmatch(r"\d{4}-\d{2}-\d{2}", value):
        return ""

    for parse in (
        datetime.fromisoformat,
        lambda v: datetime.strptime(v, "%H:%M"),
    ):
        try:
            return parse(value).strftime("%I:%M %p").lstrip("0")
        except ValueError:
            continue

    return value


def fmt_day(value):
    try:
        d = datetime.fromisoformat(flat(value)[:10])
        return f"{d:%a}, {d.day} {d:%b %Y}"
    except ValueError:
        return flat(value)


def event_when(ev):
    start = flat(ev.get("start"))
    end = flat(ev.get("end"))
    date = flat(ev.get("date")) or (start[:10] if "T" in start else "")

    s, e = fmt_clock(start), fmt_clock(end)
    clock = f"{s} to {e}" if s and e else s

    return "  ·  ".join(p for p in (fmt_day(date) if date else "", clock) if p)


# ============================================================
# RENDERING
# ============================================================

def fmt_time(ts):
    return ts.strftime("%I:%M %p").lstrip("0")


def send(text):
    """Queue a user message. The agent runs further down the script."""
    st.session_state.messages.append(
        {
            "role": "user",
            "content": text,
            "ts": datetime.now(),
        }
    )
    st.session_state.pending = True
    st.rerun()


def render_user(text, tail, grouped):
    row_cls = "row sent" + (" grouped" if grouped else "")
    bubble_cls = "bubble sent" + (" tail" if tail else "")
    safe = html.escape(str(text)).replace("\n", "<br>")

    st.markdown(
        f'<div class="{row_cls}">'
        f'<div class="{bubble_cls}">{safe}</div>'
        f"</div>",
        unsafe_allow_html=True,
    )


def render_event(ev):
    title = ev.get("title") or ev.get("summary") or ev.get("name") or "Untitled event"

    with st.expander(md_safe(title)):

        shown = False

        when = event_when(ev)
        if when:
            st.markdown(f"🕒  {md_safe(when)}")
            shown = True

        location = flat(ev.get("location"))
        if location:
            st.markdown(f"📍  {md_safe(location)}")
            shown = True

        description = flat(ev.get("description"))
        if description:
            st.markdown(md_safe(description))
            shown = True

        if not shown:
            st.caption("No more details.")


def render_reply(idx, text, grouped_first):
    parts = split_reply(clean_text(text))

    if not parts:
        parts = [("text", "(empty reply)")]

    for n, (kind, payload) in enumerate(parts):

        is_last = n == len(parts) - 1
        g = int(grouped_first or n > 0)

        if kind == "text":
            with st.container(key=f"bot_{idx}_{n}_t{int(is_last)}_g{g}_e"):
                st.markdown(md_safe(payload))

        else:
            with st.container(key=f"evts_{idx}_{n}_g{g}_e"):
                for ev in payload:
                    render_event(ev)


# ============================================================
# HEADER
# ============================================================

st.markdown(
    """
<div class="app-header">
    <div class="avatar">📅</div>
    <div class="contact">Calendar Agent</div>
</div>
""",
    unsafe_allow_html=True,
)


# ============================================================
# INPUT (handled before rendering so new messages show at once)
# ============================================================

user_input = st.chat_input(
    "iMessage",
    disabled=st.session_state.pending,
)

if user_input:
    send(user_input)


# ============================================================
# MESSAGE HISTORY
# ============================================================

messages = st.session_state.messages

if messages:
    first_ts = messages[0].get("ts", datetime.now())
    st.markdown(
        f'<div class="timestamp"><b>Today</b> {fmt_time(first_ts)}</div>',
        unsafe_allow_html=True,
    )

last_user_idx = max(
    (i for i, m in enumerate(messages) if m["role"] == "user"),
    default=-1,
)

for i, message in enumerate(messages):

    role = message["role"]

    prev_same = i > 0 and messages[i - 1]["role"] == role
    next_same = i + 1 < len(messages) and messages[i + 1]["role"] == role

    if role == "user":
        render_user(
            message["content"],
            tail=not next_same,
            grouped=prev_same,
        )
    else:
        render_reply(i, message["content"], grouped_first=prev_same)

    if i == last_user_idx:
        status = "Delivered" if st.session_state.pending else "Read"
        st.markdown(
            f'<div class="status">{status}</div>',
            unsafe_allow_html=True,
        )


# ============================================================
# WELCOME (suggestion chips)
# ============================================================

if not messages:

    st.markdown(
        '<div class="timestamp"><b>Today</b> '
        f"{fmt_time(datetime.now())}</div>",
        unsafe_allow_html=True,
    )

    cols = st.columns(2)

    for idx, text in enumerate(SUGGESTIONS):
        with cols[idx % 2]:
            if st.button(text, key=f"chip_{idx}", use_container_width=True):
                send(text)


# ============================================================
# RUN AGENT FOR THE PENDING MESSAGE
# ============================================================

if st.session_state.pending:

    slot = st.empty()

    slot.markdown(
        '<div class="row received">'
        '<div class="bubble received tail typing">'
        "<span></span><span></span><span></span>"
        "</div></div>",
        unsafe_allow_html=True,
    )

    last_message = st.session_state.messages[-1]["content"]

    try:
        response = asyncio.run(process_message(last_message))

        if response is None:
            response = "I couldn't generate a response."

    except Exception as e:
        response = f"Error: {e}"

    st.session_state.messages.append(
        {
            "role": "assistant",
            "content": response,
            "ts": datetime.now(),
        }
    )
    st.session_state.pending = False

    st.rerun()