"""
report.py  -  SAVES THE FINISHED REPORT
=======================================

Puts the agent's report and every saved note (with its source link) into one
Markdown file in the "outputs" folder, so nothing is lost when the app closes.
"""

from datetime import datetime
from pathlib import Path

OUTPUT_FOLDER = Path(__file__).parent / "outputs"


def build_markdown(goal, brand, report, notes):
    lines = [f"# Competitor research for {brand}", "",
             f"**Goal:** {goal}  ", f"**Date:** {datetime.now():%d %B %Y}", "", report, "",
             "---", "", "## Research notes (as saved by the agent)", ""]
    for n, note in enumerate(notes, start=1):
        lines.append(f"{n}. **{note['competitor']}**: {note['finding']} ([source]({note['source_url']}))")
    if not notes:
        lines.append("No notes were saved.")
    return "\n".join(lines)


def save_report(goal, brand, report, notes):
    OUTPUT_FOLDER.mkdir(exist_ok=True)
    path = OUTPUT_FOLDER / f"research_{datetime.now():%Y-%m-%d_%H%M}.md"
    path.write_text(build_markdown(goal, brand, report, notes), encoding="utf-8")
    return path
