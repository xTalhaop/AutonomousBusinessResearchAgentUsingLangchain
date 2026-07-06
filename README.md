# Autonomous Business Research Agent (LangChain Multi-Agent Pipeline)

An autonomous **4-stage research pipeline** built with **LangChain 1.x** that transforms one business idea into a polished, structured **Word (.docx)** report.

You provide a topic (for example, *“poultry farming business”*), and the system runs four specialized agents in sequence:

1. Planner / Collector Agent  
2. Cleaner Agent  
3. Merger Agent  
4. Report Generator Agent  

Each stage has one clear responsibility and passes output through files on disk, making the system easy to debug, resume, and inspect.

---

## Table of Contents

1. [What This Project Does](#what-this-project-does)
2. [Detailed Architecture Diagram](#detailed-architecture-diagram)
3. [How the Pipeline Works (Deep Dive)](#how-the-pipeline-works-deep-dive)
4. [Agents Explained](#agents-explained)
5. [Tools Explained in Depth](#tools-explained-in-depth)
6. [Technology Stack](#technology-stack)
7. [Project Structure](#project-structure)
8. [Setup & Installation](#setup--installation)
9. [Environment Variables](#environment-variables)
10. [How to Run](#how-to-run)
11. [Outputs & Artifacts](#outputs--artifacts)
12. [Design Decisions](#design-decisions)
13. [Known Limitations](#known-limitations)
14. [Troubleshooting](#troubleshooting)
15. [Future Improvements](#future-improvements)

---

## What This Project Does

This project automates business research into a final report pipeline:

- Collects web sources across fixed business sub-topics
- Scrapes and converts raw page content into markdown files
- Cleans junk content (ads/nav/cookies/etc.)
- Merges all cleaned files into one coherent report
- Exports report to a professional DOCX document

It is intentionally split into specialized agents, instead of one giant prompt, to improve reliability and maintainability.

---

## Detailed Architecture Diagram

> The diagram below is intentionally deeper than a high-level flow: each agent block shows the tools/models it uses and what it writes.

```text
┌──────────────────────────────────────────────────────────────────────────────┐
│                              USER INPUT                                      │
│                 "Enter business idea: <your topic here>"                     │
└──────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌──────────────────────────────────────────────────────────────────────────────┐
│ STAGE 1: PLANNER / COLLECTOR AGENT                                           │
│ File: Agents/planner.py                                                      │
│ Model: Gemini (gemini-3.1-flash-lite)                                        │
│                                                                              │
│ Internal Tools:                                                              │
│   • search(query)    -> TavilySearch URLs                                    │
│   • scrape(url)      -> requests + BeautifulSoup text extraction             │
│   • html_to_md(html, filename) -> markdownify + save .md to disk             │
│                                                                              │
│ Behavior:                                                                    │
│   • Covers 13 business sub-topics                                            │
│   • Searches, scrapes, and MUST persist each useful scrape                   │
│ Output Directory: data/outputs/*.md                                          │
└──────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌──────────────────────────────────────────────────────────────────────────────┐
│ STAGE 2: CLEANER AGENT                                                       │
│ File: Agents/cleaner.py                                                      │
│ Model: Groq Llama (llama-3.3-70b-versatile)                                  │
│ Tools: none (pure text transformation agent)                                 │
│                                                                              │
│ Behavior:                                                                    │
│   • Reads every markdown file in data/outputs                                │
│   • Removes web noise (nav/footer/cookies/ads/newsletters/social links)      │
│   • Preserves facts, examples, tables, warnings, useful links                │
│ Output Directory: data/cleaned_outputs/*_clean.md                            │
└──────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌──────────────────────────────────────────────────────────────────────────────┐
│ STAGE 3: MERGER AGENT                                                        │
│ File: Agents/merger.py                                                       │
│ Model: Groq Llama (llama-3.3-70b-versatile)                                  │
│ Tools: none (pure synthesis/structuring agent)                               │
│                                                                              │
│ Behavior:                                                                    │
│   • Reads all cleaned files in order                                         │
│   • Deduplicates overlap while preserving unique facts                       │
│   • Produces one coherent, sectioned business report                         │
│ Output File: data/merged_output/merged_report.md                             │
└──────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌──────────────────────────────────────────────────────────────────────────────┐
│ STAGE 4: FINAL REPORT GENERATOR AGENT                                        │
│ File: Agents/final_report_generator.py                                       │
│ Model: Gemini (gemini-2.5-flash)                                             │
│                                                                              │
│ Internal Tool:                                                               │
│   • md_to_docx(input_file, output_file, title?)                              │
│     (custom markdown parser + python-docx renderer)                          │
│                                                                              │
│ Behavior:                                                                    │
│   • Always tool-calls md_to_docx                                             │
│   • Converts merged markdown into professional .docx                         │
│ Output File: data/final_reports/business_report.docx                         │
└──────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
                       FINAL DELIVERABLE: business_report.docx
```

---

## How the Pipeline Works (Deep Dive)

### 1) Planner / Collector (Breadth-first research)

- Receives the user business topic.
- Executes multiple searches and web fetches across **13 fixed business dimensions**:
  - Industry overview
  - Market size/growth
  - Business models
  - Startup requirements
  - Competition
  - Supply chain
  - Customers/demand
  - Revenue/profitability
  - Risks/challenges
  - Regulations/compliance
  - Technology/innovation
  - Opportunities
  - Practical first steps
- Saves each useful page as raw markdown in `data/outputs/`.

This stage optimizes for **coverage**, not polish.

### 2) Cleaner (Lossless cleanup)

- Processes each raw markdown file independently.
- Removes boilerplate webpage noise.
- Keeps research content intact.
- Writes cleaned files to `data/cleaned_outputs/`.

This stage optimizes for **signal extraction**.

### 3) Merger (Single coherent report)

- Reads all cleaned files.
- Merges and structures data using business-report headings.
- Removes duplicates while preserving unique details.
- Writes `merged_report.md`.

This stage optimizes for **coherence and structure**.

### 4) Report Generator (Markdown → DOCX)

- Runs a tool-using agent that calls `md_to_docx`.
- Converts markdown elements into native Word formatting.
- Writes final `.docx` report.

This stage optimizes for **deliverable quality**.

---

## Agents Explained

### Stage 1 — `Agents/planner.py`

- Uses `ChatGoogleGenerativeAI(model="gemini-3.1-flash-lite")`
- Registered tools: `search`, `scrape`, `html_to_md`
- System prompt enforces:
  - mandatory sub-topic coverage
  - mandatory persistence after useful scrapes
  - no final-report writing at this stage

### Stage 2 — `Agents/cleaner.py`

- Uses `ChatGroq(model="llama-3.3-70b-versatile")`
- No tool calls; pure content cleaning
- Reads from `data/outputs/*.md`, writes `data/cleaned_outputs/*_clean.md`

### Stage 3 — `Agents/merger.py`

- Uses `ChatGroq(model="llama-3.3-70b-versatile")`
- Reads all cleaned docs, creates one merged markdown report
- Output: `data/merged_output/merged_report.md`

### Stage 4 — `Agents/final_report_generator.py`

- Uses `ChatGoogleGenerativeAI(model="gemini-2.5-flash")`
- Tool-enabled with `md_to_docx`
- Writes final DOCX at `data/final_reports/business_report.docx`

---

## Tools Explained in Depth

This section explains both **what each tool does** and the underlying concepts/libraries.

### 1) `Tools/search.py` — Tavily-powered web URL discovery

#### Function
`search(query: str) -> list[str]`

#### What it does
- Uses `langchain_tavily.TavilySearch` to discover relevant web pages for a query.
- Returns a list of URLs (not full page text).
- Keeps retrieval lightweight so the Planner can do many searches across all 13 sub-topics.

#### Tavily (deeper explanation)

**Tavily** is a search API designed for **LLM/agent retrieval pipelines**, not only for human browsing.  
Instead of returning noisy web UI output, it provides structured search results that agents can process directly.

Why that matters in this project:
- The Planner needs to run repeated search loops quickly.
- We need link discovery first, then controlled scraping with our own tool.
- Structured results reduce friction in agent tool-calling workflows.

#### How Tavily fits this pipeline

The retrieval flow in this project is intentionally split:

1. `search()` (Tavily) finds candidate URLs.
2. `scrape()` fetches page content from selected URLs.
3. `html_to_md()` converts/saves that content to markdown files.

This separation is important:
- Tavily handles **source discovery**.
- Your own tools handle **content extraction and persistence**.
- Downstream agents (Cleaner/Merger) work on files, not transient responses.

#### Current Tavily configuration in your code

- `search_depth="fast"`  
  Faster, lower-cost retrieval. Good for high-volume iterative research loops.
- `max_results=5`  
  Prevents oversized result sets and keeps agent decisions focused.
- `topic="general"`  
  Broad domain behavior suitable for varied business topics.
- `include_answer=False`  
  Disables Tavily-generated answer synthesis (you only need sources here).
- `include_raw_content=False`  
  Avoids returning heavy page bodies at search stage; scraping is delegated to `scrape()`.

#### Practical trade-offs

- `fast` depth improves speed and cost efficiency but may miss some deeper sources.
- Increasing depth or result count can improve recall, but increases token/tool usage.
- Source quality can still vary; your Cleaner/Merger stages and prompt strategy help control this.

#### When Tavily is a strong fit
- Agentic research pipelines
- Multi-step retrieval/scrape/save workflows
- Situations where you want tool-friendly, structured web discovery

---

### 2) `Tools/scrape.py` — Requests + BeautifulSoup extraction

#### Function
`scrape(url: str) -> str`

#### What it does
- Fetches a web page with `requests.get(...)`.
- Parses HTML via `BeautifulSoup`.
- Removes typical non-content tags:
  - `script`, `style`, `nav`, `footer`, `header`, `noscript`
- Converts remaining DOM to plain text (`get_text(...)`).
- Truncates to max 6000 chars to control token usage.

#### BeautifulSoup concept (important)
**BeautifulSoup** is a Python HTML/XML parser that turns raw markup into a traversable tree.  
Why useful here:
- you can programmatically remove noisy tag sections
- you can extract text from semantic content regions
- robust against imperfect HTML in real-world pages

---

### 3) `Tools/html_to_md.py` — HTML → Markdown persistence tool

#### Function
`html_to_md(html: str, filename: str) -> str`

#### What it does
- Parses HTML with BeautifulSoup.
- Removes noise tags (same strip list concept).
- Converts cleaned HTML to markdown via `markdownify`.
- Writes to `data/outputs/<filename>`.

#### markdownify concept
**markdownify** converts HTML structure into markdown syntax:
- headings become `#`-style headings
- links become `[text](url)`
- lists and paragraphs are mapped to markdown equivalents

Why this matters:
- markdown is easier for downstream LLM processing than raw HTML
- keeps a readable archival intermediate format on disk

---

### 4) `Tools/md_to_docx.py` — Custom Markdown parser + Word renderer

#### Function
`md_to_docx(input_file: str, output_file: str, title: str = None) -> str`

#### What it does
- Reads markdown file.
- Creates a DOCX with `python-docx`.
- Applies consistent styling (Calibri, margins, heading styles).
- Parses markdown lines and maps to Word constructs:
  - headings (`#` to `####`)
  - bold/italic inline runs
  - numbered and bulleted lists
  - horizontal rules
  - markdown tables (header separator detection)

#### python-docx concept
**python-docx** is a Python library for generating/editing `.docx` files programmatically.  
In this project it’s used to:
- produce a true Word document (not plain text with `.docx` extension)
- apply consistent typography and spacing
- render tables/lists/headings natively for professional output

#### Why custom parser instead of off-the-shelf conversion?
- Full control over formatting behavior
- predictable output based on your report style
- easy to extend for your own markdown conventions

---

## Technology Stack

| Layer | Technology | Purpose |
|---|---|---|
| Agent orchestration | LangChain 1.x (`create_agent`) | Build tool-using and non-tool agents |
| Graph runtime | LangGraph | Execution engine under agent workflows |
| LLM provider A | Google Gemini (`langchain-google-genai`) | Planner + DOCX export agent |
| LLM provider B | Groq-hosted Llama (`langchain-groq`) | Cleaner + Merger agents |
| Web retrieval | Tavily (`langchain-tavily`) | URL search results |
| Web fetch/parsing | Requests + BeautifulSoup4 | HTTP fetch + HTML parsing |
| HTML conversion | markdownify | HTML → Markdown |
| DOCX generation | python-docx | Markdown → Word output |
| Config | python-dotenv | Load `.env` secrets |
| Language | Python 3.11+ | Runtime |

---

## Project Structure

```text
AutonomousBusinessResearchAgentUsingLangchain/
│
├── main.py
├── requirements.txt
├── .gitignore
├── README.md
│
├── Agents/
│   ├── planner.py
│   ├── cleaner.py
│   ├── merger.py
│   └── final_report_generator.py
│
├── Tools/
│   ├── search.py
│   ├── scrape.py
│   ├── html_to_md.py
│   └── md_to_docx.py
│
└── data/
    ├── outputs/
    ├── cleaned_outputs/
    ├── merged_output/
    └── final_reports/
```

---

## Setup & Installation

### 1) Clone repository
```bash
git clone https://github.com/xTalhaop/AutonomousBusinessResearchAgentUsingLangchain.git
cd AutonomousBusinessResearchAgentUsingLangchain
```

### 2) Create virtual environment
```bash
python -m venv .venv
```

Activate it:

- **Windows (PowerShell):**
```bash
.venv\Scripts\Activate.ps1
```

- **Windows (CMD):**
```bash
.venv\Scripts\activate.bat
```

- **macOS/Linux:**
```bash
source .venv/bin/activate
```

### 3) Install dependencies
```bash
pip install -r requirements.txt
```

---

## Environment Variables

Create `.env` in project root:

```env
GOOGLE_API_KEY=your_google_api_key
GROQ_API_KEY=your_groq_api_key
TAVILY_API_KEY=your_tavily_api_key
```

| Variable | Used in |
|---|---|
| `GOOGLE_API_KEY` | Planner + Final Report Generator |
| `GROQ_API_KEY` | Cleaner + Merger |
| `TAVILY_API_KEY` | Search tool |

---

## How to Run

From project root:

```bash
python main.py
```

You’ll see:

```text
Enter business idea:
```

Example input:
```text
Do deep research on web and give detailed content about poultry farming business
```

Pipeline runs all 4 stages in order and produces final docx.

---

## Outputs & Artifacts

| Path | Produced by | Description |
|---|---|---|
| `data/outputs/*.md` | Planner | Raw scraped markdown pages |
| `data/cleaned_outputs/*_clean.md` | Cleaner | Noise-cleaned markdown files |
| `data/merged_output/merged_report.md` | Merger | Unified markdown business report |
| `data/final_reports/business_report.docx` | Final Report Generator | Final polished deliverable |

---

## Design Decisions

1. **File-based stage boundaries**
   - Each stage reads/writes from disk.
   - Easier restart/recovery and debugging.

2. **Single-responsibility agents**
   - Planner collects, cleaner cleans, merger structures, exporter formats.
   - Better maintainability than one monolithic mega-prompt.

3. **Hybrid LLM providers**
   - Gemini for tool-heavy stages.
   - Groq Llama for transformation/synthesis stages.

4. **Custom DOCX rendering**
   - Predictable professional formatting.
   - Easy extension over time.

---

## Known Limitations

- Scraped text is capped at ~6000 chars in `scrape.py`.
- Markdown parser in `md_to_docx` is intentionally partial (focused on practical report syntax).
- No citation validation/scoring layer yet.
- Planner depends on web accessibility and source availability.
- Agent outputs can vary based on model behavior and provider-side changes.

---

## Troubleshooting

### `.env` parsing errors
Ensure every line is exactly `KEY=value` with no extra characters.

### Stage 4 says merged report missing
Make sure Stage 3 completed and `data/merged_output/merged_report.md` exists.

### Search returns weak sources
Increase Tavily depth/results or broaden query phrasing in planner prompt.

### Scrape failures
Some sites block scraping or require JS rendering (currently not implemented).

### DOCX formatting edge cases
Complex/nested markdown constructs may need parser extension in `Tools/md_to_docx.py`.

---

## Future Improvements

- Add source quality scoring + citation extraction.
- Add optional Playwright-based scraper for JS-heavy pages.
- Add concurrency in Planner sub-topic collection.
- Add retry/backoff and dead-link replacement strategy.
- Add optional PDF export pipeline.
- Add evaluation harness for report quality checks.

---

## Quick Summary

This project is a practical, modular, production-style multi-agent pipeline for business research:

- **Collect** broadly  
- **Clean** losslessly  
- **Merge** coherently  
- **Export** professionally  
