# Autonomous Business Research Agent

An autonomous, multi-agent research pipeline built with **LangChain 1.x** that takes a single business idea typed by a user and turns it into a polished, professionally formatted **Word (.docx) business research report**  with zero manual research, writing, or formatting required.

You type a business idea (e.g. *"poultry farming business"*), and four specialized LLM agents work in sequence to search the web, scrape sources, clean the raw content, merge everything into a structured report, and export it as a formatted `.docx` file.

---

## Table of Contents

1. [How It Works — High-Level Overview](#how-it-works--high-level-overview)
2. [Pipeline Architecture](#pipeline-architecture)
3. [Technology Stack](#technology-stack)
4. [Project Structure](#project-structure)
5. [Step-by-Step Walkthrough of Each Agent](#step-by-step-walkthrough-of-each-agent)
6. [Tools Explained](#tools-explained)
7. [Setup & Installation](#setup--installation)
8. [Environment Variables](#environment-variables)
9. [How to Run](#how-to-run)
10. [Output Files & Where They Go](#output-files--where-they-go)
11. [Design Decisions & Known Limitations](#design-decisions--known-limitations)
12. [Troubleshooting](#troubleshooting)
13. [Possible Future Improvements](#possible-future-improvements)

---

## How It Works — High-Level Overview

This project is a **4-stage autonomous pipeline**, where each stage is its own independent LangChain agent with its own LLM, its own system prompt, and its own single responsibility. The stages run one after another, and each stage's output on disk becomes the next stage's input.

```
User types a business idea
        │
        ▼
┌─────────────────┐
│  1. Planner /    │  Searches the web, scrapes pages, saves raw
│     Collector    │  markdown files for 13 research sub-topics
└────────┬─────────┘
         ▼
┌─────────────────┐
│  2. Cleaner      │  Strips ads/nav/junk from each raw file,
│                  │  keeps only research-relevant content
└────────┬─────────┘
         ▼
┌─────────────────┐
│  3. Merger       │  Combines all cleaned files into ONE
│                  │  coherent, structured Markdown report
└────────┬─────────┘
         ▼
┌─────────────────┐
│  4. Report       │  Converts the final Markdown report into
│     Generator    │  a formatted Word (.docx) document
└────────┬─────────┘
         ▼
   business_report.docx
```

This is a **multi-agent system**, not a single monolithic prompt — each agent is deliberately narrow in scope (single-responsibility principle applied to LLM agents), which makes the pipeline easier to debug, easier to swap models for, and far more reliable than asking one agent to "research and write a report" in one shot.

---

## Pipeline Architecture

| Stage | Agent Name | LLM Provider | Model | Job |
|---|---|---|---|---|
| 1 | Planner / Collector | Google Gemini | `gemini-3.1-flash-lite` | Search the web, scrape pages, save raw markdown |
| 2 | Cleaner | Groq (Llama) | `llama-3.3-70b-versatile` | Strip noise from each raw markdown file |
| 3 | Merger | Groq (Llama) | `llama-3.3-70b-versatile` | Merge cleaned files into one structured report |
| 4 | Report Generator | Google Gemini | `gemini-2.5-flash` | Convert final Markdown into a DOCX file via a tool call |

**Why two different LLM providers?** Gemini is used for the tool-heavy, agentic steps (web search + scraping + file export) where its tool-calling and large context window are useful. Groq's Llama 3.3 70B is used for the pure text-transformation steps (cleaning, merging) where speed matters more and no external tools are needed — Groq's inference is extremely fast, which keeps the cleaning stage (which runs once **per file**, often 10-15 times) from becoming a bottleneck.

**Why is data passed via the filesystem instead of in-memory?**
Each stage writes its output to a folder on disk, and the next stage reads from that folder. This is intentional:
- It makes the pipeline **resumable** — if stage 3 fails, you don't have to re-run stage 1's expensive web scraping.
- It makes each stage **independently debuggable** — you can open `outputs/`, `cleaned_outputs/`, or `merged_output/` at any time and inspect exactly what an agent produced.
- It avoids blowing past LLM context windows by not passing the entire accumulated pipeline state through every function call in memory.

---

## Technology Stack

| Category | Technology | Purpose |
|---|---|---|
| Agent framework | **LangChain 1.x** (`langchain.agents.create_agent`) | Builds each stage as an autonomous tool-using agent |
| Agent runtime | **LangGraph** | Underlying graph execution engine that `create_agent` runs on |
| LLM Provider 1 | **Google Gemini** (`langchain-google-genai`) | Powers the Planner and Report Generator agents |
| LLM Provider 2 | **Groq** (`langchain-groq`) | Powers the Cleaner and Merger agents (Llama 3.3 70B) |
| Web search | **Tavily** (`langchain-tavily`) | Returns relevant URLs for each research sub-topic |
| Web scraping | **Requests** + **BeautifulSoup4** | Fetches and parses raw HTML content from URLs |
| HTML → Markdown | **markdownify** | Converts scraped HTML into clean Markdown |
| Markdown → DOCX | **python-docx** (custom parser) | Hand-written Markdown parser that renders headings, tables, lists, bold/italic into a formatted Word document |
| Config | **python-dotenv** | Loads API keys from a local `.env` file |
| Language | **Python 3.11+** | |

---

## Project Structure

```
AutonomousBusinessResearchAgentLangchain/
│
├── main.py                        # Entry point — runs all 4 stages in order
├── requirements.txt                # Python dependencies
├── .env                            # API keys (not committed — see Environment Variables)
│
├── Agents/
│   ├── planner.py                  # Stage 1: Collector agent
│   ├── cleaner.py                  # Stage 2: Cleaning agent
│   ├── merger.py                   # Stage 3: Merge & Report agent
│   ├── final_report_generator.py   # Stage 4: DOCX export agent
│   │
│   ├── outputs/                    # Raw scraped markdown (Stage 1 output)
│   ├── cleaned_outputs/            # Cleaned markdown (Stage 2 output)
│   ├── merged_output/              # Final merged report .md (Stage 3 output)
│   └── final_reports/              # Final business_report.docx (Stage 4 output)
│
└── Tools/
    ├── search.py                   # Tavily web search tool
    ├── scrape.py                   # BeautifulSoup HTML scraper tool
    ├── html_to_md.py                # HTML → Markdown + save-to-file tool
    └── md_to_docx.py                # Markdown → formatted DOCX tool
```

Each folder under `Agents/` (`outputs/`, `cleaned_outputs/`, `merged_output/`, `final_reports/`) is created automatically at runtime if it doesn't exist — you never need to create them manually.

---

## Step-by-Step Walkthrough of Each Agent

### Stage 1 — Planner / Collector Agent (`Agents/planner.py`)

**Role:** Gather raw research material. This agent does **not** write a report — its only job is breadth of coverage.

**Model:** `gemini-3.1-flash-lite` via `ChatGoogleGenerativeAI`

**Tools given to this agent:**
- `search` — find URLs for a query
- `scrape` — fetch and clean the text content of a URL
- `html_to_md` — convert content to Markdown and save it to `outputs/`

**How it operates:**
1. The system prompt instructs the agent to research **13 fixed sub-topics** covering every angle of starting and running the business: Industry Overview, Market Size & Growth, Business Models, Startup Requirements, Key Players & Competition, Supply Chain & Operations, Customers & Demand, Revenue & Profitability, Risks & Challenges, Regulations & Compliance, Technology & Innovation, Opportunities for Newcomers, and Practical First Steps.
2. For each sub-topic, the agent calls `search` to find 3-5 credible URLs, then `scrape` on the 2-3 most promising ones.
3. **Every single successful scrape must be immediately followed by a call to `html_to_md`** — the system prompt makes this mandatory so no scraped content is lost before being persisted to disk.
4. Files are saved with a numbered naming convention (e.g. `04_startup_requirements_licensing.md`) so downstream stages can process them in a sensible order.
5. The agent is explicitly told **not** to clean, summarize, or filter content quality at this stage — that's the next agent's job. Breadth over polish.
6. When finished, it prints a short status summary of what was covered and flags any sub-topics where good sources couldn't be found.

**Output:** A folder of raw, messy, possibly redundant `.md` files in `Agents/outputs/`.

### Stage 2 — Cleaner Agent (`Agents/cleaner.py`)

**Role:** Strip web page noise out of each raw file, one file at a time.

**Model:** `llama-3.3-70b-versatile` via `ChatGroq` (no tools — pure text transformation)

**How it operates:**
1. Reads every `.md` file in `Agents/outputs/`.
2. For each file, sends the raw markdown to the LLM with a system prompt instructing it to remove navigation menus, cookie notices, ads, newsletter prompts, social buttons, "related articles" sections, footers/headers, and duplicate/broken formatting — while preserving every fact, table, list, code block, and useful hyperlink.
3. Critically, the prompt tells the model **not to summarize or rewrite** — this is lossless cleanup, not compression.
4. Saves each result to `Agents/cleaned_outputs/{original_filename}_clean.md`.

**Output:** The same number of files as Stage 1, but noise-free, in `Agents/cleaned_outputs/`.

### Stage 3 — Merger Agent (`Agents/merger.py`)

**Role:** Combine every cleaned file into one single, coherent, well-organized report.

**Model:** `llama-3.3-70b-versatile` via `ChatGroq` (no tools — pure text transformation)

**How it operates:**
1. Reads every `*_clean.md` file from `Agents/cleaned_outputs/` in sorted (numeric) order.
2. Concatenates them into one large prompt, each document clearly delimited and labeled with its filename, prefixed with the original research topic the user typed.
3. The system prompt gives the LLM a fixed report structure to follow (Executive Summary → Industry Overview → ... → Conclusion → References) and instructs it to deduplicate information across sources while preserving every unique fact.
4. Saves the single resulting Markdown document to `Agents/merged_output/merged_report.md`.

**Output:** One polished Markdown file — the full business report, still in `.md` form.

### Stage 4 — Report Generator / DOCX Export Agent (`Agents/final_report_generator.py`)

**Role:** Convert the final Markdown report into a professionally formatted Word document.

**Model:** `gemini-2.5-flash` via `ChatGoogleGenerativeAI`

**Tools given to this agent:**
- `md_to_docx` — a custom tool (see [Tools Explained](#tools-explained)) that parses Markdown and builds a `.docx` file

**How it operates:**
1. The agent is instructed to always call the `md_to_docx` tool and never attempt to "answer" the conversion manually in text.
2. It's told the exact input path (`merged_output/merged_report.md`) and output path (`final_reports/business_report.docx`).
3. The tool itself does all the real work: it parses the Markdown line-by-line and converts headings, bold/italic text, bullet lists, numbered lists, tables, and horizontal rules into native Word formatting (see below).

**Output:** `Agents/final_reports/business_report.docx` — the final deliverable.

---

## Tools Explained

Tools live in the `Tools/` folder and are plain Python functions decorated with LangChain's `@tool` decorator, which exposes them to an agent as callable functions.

### `Tools/search.py` — `search(query: str) -> list[str]`
Wraps `langchain_tavily.TavilySearch` with `search_depth="fast"` and `max_results=5`. Given a text query, returns a list of relevant URLs (not page content — just links). Used exclusively by the Planner agent to find sources for each research sub-topic.

### `Tools/scrape.py` — `scrape(url: str) -> str`
Given a URL, performs an HTTP GET (10 second timeout) using `requests`, parses the HTML with `BeautifulSoup`, strips out `<script>`, `<style>`, `<nav>`, `<footer>`, `<header>`, and `<noscript>` tags, and returns the remaining visible text (capped at 6,000 characters to avoid blowing the LLM's context window). Returns a descriptive error string instead of raising if the page can't be fetched.

### `Tools/html_to_md.py` — `html_to_md(html: str, filename: str) -> str`
Converts raw HTML into Markdown using the `markdownify` library, then writes it to `Agents/outputs/{filename}` (creating the `outputs/` folder automatically if it doesn't exist). This is the tool responsible for actually persisting the Planner agent's scraped content to disk.

### `Tools/md_to_docx.py` — `md_to_docx(input_file, output_file, title=None) -> str`
The most substantial tool in the project — a hand-written Markdown → DOCX converter built on `python-docx`. It does **not** rely on any third-party Markdown-to-Word library; instead it implements its own line-by-line parser that supports:
- Headings (`#` through `####`) mapped to Word heading styles
- **Bold** and *italic* inline text (including `_underscore italics_`)
- Bulleted and numbered lists
- Markdown tables (`| col | col |` syntax with header/separator detection), rendered as native Word tables with the "Light Grid Accent 1" style
- Horizontal rules (`---`, `***`, `___`) rendered as a bottom-border paragraph
- An optional title page (centered, large bold title + page break) if a `title` argument is passed
- Consistent document-wide styling: Calibri font, 1-inch margins, and sized/spaced heading styles for a professional look

This tool is what turns the final Markdown report into the polished `.docx` file the user actually receives.

---

## Setup & Installation

### 1. Clone / download the project
```bash
git clone <your-repo-url>
cd AutonomousBusinessResearchAgentLangchain
```

### 2. Create and activate a virtual environment
```bash
python -m venv .venv

# Windows
.venv\Scripts\activate

# macOS / Linux
source .venv/bin/activate
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Create your `.env` file
Create a file named `.env` in the project root (same level as `main.py`) with your API keys — see [Environment Variables](#environment-variables) below.

---

## Environment Variables

This project needs API keys for three services. Create a `.env` file in the project root:

```env
GOOGLE_API_KEY=your_google_gemini_api_key_here
GROQ_API_KEY=your_groq_api_key_here
TAVILY_API_KEY=your_tavily_api_key_here
```

| Variable | Used By | Where to get it |
|---|---|---|
| `GOOGLE_API_KEY` | Planner agent, Report Generator agent | [Google AI Studio](https://aistudio.google.com/apikey) |
| `GROQ_API_KEY` | Cleaner agent, Merger agent | [console.groq.com](https://console.groq.com/keys) |
| `TAVILY_API_KEY` | `Tools/search.py` | [tavily.com](https://tavily.com) |

**Important formatting note:** each line must be exactly `KEY=value` with no quotes, no spaces around the `=`, and no trailing comments on the same line — `python-dotenv` will silently fail to parse malformed lines (you'll see a `python-dotenv could not parse statement...` warning at startup if a line is broken, and that key simply won't load, which usually surfaces later as an authentication error).

---

## How to Run

From the project root (the folder containing `main.py`):

```bash
python main.py
```

You'll be prompted:

```
Enter business idea:
```

Type any business idea in plain English, e.g.:

```
Enter business idea: Do deep research on web and give detailed content about the poultry business
```

The pipeline then runs all four stages automatically, printing progress for each:

```
============================================================
STEP 1 : Planner Agent
============================================================
...

============================================================
STEP 2 : Cleaning Agent
============================================================
...

============================================================
STEP 3 : Merge Agent
============================================================
...

============================================================
STEP 4 : Report Generator
============================================================
...

Project completed successfully.
```

Depending on how many sources are researched, the full run typically takes several minutes — most of the time is spent in Stage 1 (web search + scraping) and Stage 2 (cleaning runs once per file).

### Running a single stage on its own
Each agent file can also be run independently for debugging, since every stage reads from disk rather than requiring in-memory state from the previous stage:

```bash
python Agents/planner.py     # only run the collector
python Agents/cleaner.py     # only re-run cleaning on whatever is in outputs/
python Agents/merger.py      # only re-merge whatever is in cleaned_outputs/
python Agents/final_report_generator.py   # only re-export the docx
```

This is especially useful if a later stage fails — you don't need to re-run Stage 1's web scraping every time.

---

## Output Files & Where They Go

| Folder | Created By | Contents |
|---|---|---|
| `Agents/outputs/` | Stage 1 (Planner) | Raw, unclean `.md` files, one per scraped page |
| `Agents/cleaned_outputs/` | Stage 2 (Cleaner) | Same files, noise-stripped, suffixed `_clean.md` |
| `Agents/merged_output/` | Stage 3 (Merger) | Single file: `merged_report.md` — the complete report in Markdown |
| `Agents/final_reports/` | Stage 4 (Report Generator) | Single file: `business_report.docx` — the final deliverable |

All four folders are created automatically at runtime — nothing needs to be set up by hand.

---

## Design Decisions & Known Limitations

- **Path resolution:** All stages resolve their input/output folders relative to their own file location (`Path(__file__).resolve().parent`), not the current working directory. This means the pipeline behaves consistently whether you run `python main.py` from the project root or run an individual agent file directly from inside `Agents/`.
- **No shared memory between agents:** Each agent only knows what's on disk. This is a deliberate tradeoff for reliability and resumability over raw speed.
- **Fixed 13-topic research structure:** The Planner always researches the same 13 sub-topics regardless of business type. This gives consistent report structure across any business idea, but means very niche businesses may get some generic sections.
- **Scrape content is capped at 6,000 characters per page** to control token usage — very long articles will be truncated.
- **The DOCX converter is a custom Markdown parser**, not a full CommonMark implementation — it supports the constructs the report-generation prompt is instructed to produce (headings, bold/italic, lists, tables, horizontal rules) but is not a general-purpose Markdown renderer.

---

## Troubleshooting

**`python-dotenv could not parse statement starting at line N`**
A line in your `.env` file isn't valid `KEY=VALUE` syntax. Check line N for stray quotes, spaces around `=`, or inline comments.

**`FileNotFoundError` in Stage 4 (`merged_output/merged_report.md` not found)**
This happens if any stage's paths are relative to the current working directory instead of the script's own location. Make sure every agent file resolves its folders via `Path(__file__).resolve().parent`, and always run `main.py` from the project root.

**A sub-topic in Stage 1 comes back empty / "couldn't find good information"**
This is expected and by design — the Planner is instructed to report gaps honestly rather than fabricate information. Re-running Stage 1 alone, or manually adding sources to `outputs/`, can fill the gap before re-running Stages 2-4.

**Groq or Gemini authentication errors**
Double-check `.env` formatting (see above) and confirm the relevant API key hasn't expired or hit a rate limit.

---

## Possible Future Improvements

- Convert `main.py` into a CLI with flags (`--topic`, `--skip-cleaning`, etc.) instead of an interactive `input()` prompt.
- Add retry/backoff logic around each LLM provider call for transient rate-limit errors.
- Allow the 13 research sub-topics to be configurable instead of hardcoded in the Planner's system prompt.
- Add a PDF export option alongside DOCX.
- Add unit tests for `Tools/md_to_docx.py`'s Markdown parser (tables and inline formatting in particular).
