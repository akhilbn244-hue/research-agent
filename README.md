# Competitor Research Agent

An AI agent that researches competitors on its own. You give it a goal, and it decides what to search, opens the useful pages, saves each fact with its source link, and writes a cited competitor report. Every step appears live on screen.

Built with **Gemini function calling**, the **ReAct agent loop**, and **Streamlit**. Part of my AI engineering portfolio.

![App screenshot](screenshot.png)

## What it does

- **Plans its own research:** picks search queries, chooses which links to open, and decides when it has enough.
- **Shows its work live:** every search 🔎, page read 📄 and saved note 📝 appears on screen as it happens.
- **Cites everything:** each fact in the report links back to the page it came from.
- **Writes a ready-to-use report:** a summary, a competitor comparison table, what competitors do well, opportunities for your brand, and a numbered source list.
- **Saves and downloads:** each report is saved to `outputs/` and can be downloaded as Markdown.

**Example goal:** *"Find modest fashion brands selling online in Dubai and the UAE, and compare their offers, positioning and channels."*

## How it works

The agent runs the **ReAct loop** (Reason + Act), the pattern most AI agents are built on:

```
Goal ─→ THINK (Gemini reads the goal, its notes so far and the tool menu)
          │
          ├─ asks for a tool ─→ ACT (our code runs it) ─→ OBSERVE (result goes back) ─┐
          │                                                                           │
          │  ←──────────────────────── repeat ────────────────────────────────────────┘
          │
          └─ has enough ─→ writes the final report
```

### The agent's tools

Gemini can't browse the internet by itself. It gets a menu of tools, each with a name and a description, and replies with the tool it wants to use. My code then runs that tool and hands the result back.

| Tool | What it does |
| --- | --- |
| `web_search` | Searches DuckDuckGo (free, no key) and returns 5 results with title, link and snippet |
| `read_webpage` | Opens one page and returns its readable text (menus, scripts and styling removed, first 4,000 characters) |
| `save_note` | Saves one finding for the report. Notes without a source link are rejected |

Automatic function calling is switched off on purpose: my code runs each tool itself, so every action can be shown, limited and checked.

### Guardrails

- **Step limit:** after the chosen number of rounds (slider, default 12), the agent loses its tools and must write the report with what it has found. This prevents endless loops and keeps API usage within the free tier.
- **Prompt-injection defence:** text from web pages is treated as information, not instructions. If a page contains something like "ignore your instructions", the agent ignores it.
- **Safe browsing:** `read_webpage` only opens public websites. It refuses addresses on your own computer or home network.
- **No guessing:** facts must come from a page the agent actually read. Anything it couldn't find is written as "not found".
- **Graceful errors:** a failed search or unreadable page goes back to the agent as a message, so it can try another query or link instead of crashing.
- **Resilient API calls:** retries when Gemini is busy, and waits then switches model when the free-tier limit is hit.

## Tech used

Python · Gemini API function calling (`google-genai`) · DuckDuckGo search (`ddgs`) · `requests` + BeautifulSoup · Streamlit · pandas

## Project structure

| File | Job |
| --- | --- |
| `tools.py` | The tool menu Gemini reads, and the three tools themselves |
| `agent.py` | The ReAct loop, the step limit and the agent's instructions |
| `llm.py` | Talks to Gemini: retry when busy, wait-and-switch model on rate limits |
| `report.py` | Saves the report plus all notes to `outputs/` as Markdown |
| `app.py` | The screen: goal, live step trail, report, notes table, download |
| `setup.bat` / `run.bat` | Double-click installer and launcher for Windows |

## How to run it (Windows)

1. Get a free Gemini API key at [aistudio.google.com](https://aistudio.google.com).
2. Double-click `setup.bat`. When Notepad opens, paste your key after `GEMINI_API_KEY=`, save and close.
3. Double-click `run.bat`. Chrome opens the app.
4. Pick an example or write your own goal, then click **Start research**.

A run usually takes 1 to 3 minutes and 8 to 12 Gemini calls, which fits the free tier.

> Your API key stays in the local `.env` file, which `.gitignore` keeps out of GitHub.

## Testing

I tested the agent offline with a scripted stand-in for Gemini and the web, covering:

- a normal research run from first search to final report
- a broken link, a note without a source, and a request for a tool that doesn't exist
- the step limit forcing a report
- an empty reply from Gemini
- blocked private addresses (`localhost`, `192.168.x.x`, `file://`)
- page cleaning (scripts and menus removed)
- the Streamlit screen, including the missing-API-key message

## Limitations and next steps

- Some websites block automated reading, and Instagram pages can't be read without logging in. The agent then works from search snippets only.
- Free DuckDuckGo search is sometimes rate-limited for a short time.
- Ideas for next steps: run several searches in parallel, remember past research so it can be compared over time, and export the report to PDF.

## What I learned

- **How AI agents actually work:** an agent is a loop. The model thinks, asks for a tool, gets the result, and repeats. The model never runs anything itself; my code does.
- **Tool descriptions matter:** Gemini only knows what a tool does from its short description, so clear descriptions lead to better tool choices.
- **Guardrails are part of the design:** a step limit, the prompt-injection defence, blocking private addresses and requiring a source for every fact are what make an agent safe to let loose on the open web.
- **Handling failure:** returning errors to the agent as messages, instead of crashing, lets it adapt and try something else.
