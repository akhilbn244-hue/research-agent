"""
app.py  -  THE SCREEN YOU SEE
=============================

1. Type who you are and what to research (or pick an example).
2. Watch the agent's trail live: every search, page read and note, as it happens.
3. Read the cited report, check the notes behind it, and download it.
"""

import pandas as pd
import streamlit as st

from llm import AIError, get_api_key

st.set_page_config(page_title="Competitor Research Agent", page_icon="🔎", layout="wide")
st.title("Competitor Research Agent")
st.caption("An AI agent that decides what to search, reads the pages, saves cited notes and writes a competitor report.")

try:
    get_api_key()
    from agent import run_research
    from report import build_markdown, save_report
except AIError as problem:
    st.error(str(problem))
    st.stop()

EXAMPLES = {
    "Bespoke bridal tailoring in Kerala": ("AETHOL by Meghna, a custom bridal and occasion wear boutique",
                                           "Find boutiques offering custom-made bridal and occasion wear in Kerala, India, "
                                           "and how they present themselves online."),
    "Modest fashion brands in Dubai": ("Noor Fashion, a fictional modest-wear brand in Dubai",
                                       "Find modest fashion brands selling online in Dubai and the UAE, and compare their "
                                       "offers, positioning and channels."),
    "AI marketing agencies in Dubai": ("a junior AI engineer researching the market",
                                       "Find agencies in Dubai that offer AI-powered marketing services, and what services "
                                       "they list."),
}

ICONS = {"web_search": "🔎", "read_webpage": "📄", "save_note": "📝"}

with st.sidebar:
    st.header("Agent settings")
    max_steps = st.slider("Step limit", 4, 20, 12,
                          help="The most think → act rounds before the agent must write its report. "
                               "Each round is one Gemini call.")
    st.caption("Searches use DuckDuckGo (free, no key). Pages are read directly from the web.")

choice = st.selectbox("Start from an example, or write your own below", ["(write my own)"] + list(EXAMPLES))
brand_default, goal_default = EXAMPLES.get(choice, ("", ""))
brand = st.text_input("Who is this research for?", brand_default, key=f"brand-{choice}",
                      placeholder="e.g. AETHOL by Meghna, a custom bridal boutique")
goal = st.text_area("What should the agent find out?", goal_default, key=f"goal-{choice}", height=90,
                    placeholder="e.g. Find custom bridal boutiques in Kochi and compare their offers and channels.")

if st.button("Start research", type="primary", disabled=not (brand.strip() and goal.strip())):
    st.session_state.pop("result", None)
    with st.status("Researching…", expanded=True) as status:
        try:
            for event in run_research(goal.strip(), brand.strip(), max_steps=max_steps):
                if event["type"] == "tool":
                    st.write(f"{ICONS.get(event['name'], '•')} **Step {event['step']}** · {event['summary']}")
                else:
                    path = save_report(goal.strip(), brand.strip(), event["text"], event["notes"])
                    st.session_state.result = dict(event, goal=goal.strip(), brand=brand.strip(), file=path.name)
            status.update(label="Research complete", state="complete")
        except AIError as problem:
            status.update(label="Stopped", state="error")
            st.error(str(problem))

result = st.session_state.get("result")
if result:
    m1, m2, m3 = st.columns(3)
    m1.metric("Steps used", result["steps"])
    m2.metric("Notes saved", len(result["notes"]))
    m3.metric("Tokens used", f"{result['tokens']:,}")
    if result["hit_limit"]:
        st.info("The agent reached the step limit, so it wrote the report with what it had found so far.")

    report_tab, notes_tab = st.tabs(["Report", "Notes behind it"])
    with report_tab:
        st.markdown(result["text"])
    with notes_tab:
        if result["notes"]:
            st.dataframe(pd.DataFrame(result["notes"]), width="stretch", hide_index=True,
                         column_config={"source_url": st.column_config.LinkColumn("source")})
        else:
            st.write("The agent didn't save any notes.")

    st.download_button("Download report (Markdown)",
                       build_markdown(result["goal"], result["brand"], result["text"], result["notes"]),
                       file_name=result["file"])
    st.caption(f"Also saved to outputs/{result['file']}")
