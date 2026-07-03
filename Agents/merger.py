from pathlib import Path
from dotenv import load_dotenv
from langchain.agents import create_agent
from langchain_groq import ChatGroq

load_dotenv()

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
CLEANED_DIR = DATA_DIR / "cleaned_outputs"
MERGED_DIR = DATA_DIR / "merged_output"
MERGED_REPORT_PATH = MERGED_DIR / "merged_report.md"


def run(topic: str = "the researched business"):
    system_prompt = """
You are the Merge & Report Agent in a Deep Research pipeline.

You receive multiple cleaned Markdown documents covering different aspects of the same research topic.

Your task is to merge them into ONE professional, well-structured business research report.

Instructions:
- Merge all documents into one coherent report.
- Remove duplicate information.
- Preserve every unique fact.
- Organize the report with logical headings and subheadings.
- Maintain a professional and objective writing style.
- Keep important statistics, examples, tables, lists and citations.
- Do not invent information.
- Do not omit important information.
- Write smooth transitions between sections.

Structure the report as follows (if applicable):

# Title
## Executive Summary
## Industry Overview
## Market Size & Growth
## Business Models
## Startup Requirements
## Supply Chain
## Customer Segments
## Revenue Streams & Profitability
## Key Competitors
## Risks & Challenges
## Regulations & Compliance
## Technology & Innovation
## Opportunities
## Practical First Steps
## Conclusion
## References

Return ONLY the final report in valid Markdown.

The output should be directly savable as a .md file.
"""

    llm = ChatGroq(
        model="llama-3.3-70b-versatile",
        temperature=0
    )

    agent = create_agent(
        model=llm,
        system_prompt=system_prompt
    )

    files = sorted(CLEANED_DIR.glob("*_clean.md"))
    if not files:
        print(f"No cleaned files found in {CLEANED_DIR}. Skipping merge.")
        return

    merged_input = f"# Research Topic\n\n{topic}\n\n"

    for i, file in enumerate(files, start=1):
        with open(file, "r", encoding="utf-8") as f:
            content = f.read()

        merged_input += f"""
====================================================

Document {i}

Filename:
{file.name}

Content:

{content}

====================================================

"""

    print("Generating Final Report...\n")

    response = agent.invoke({
        "messages": [
            {"role": "user", "content": merged_input}
        ]
    })

    final_report = response["messages"][-1].content

    MERGED_DIR.mkdir(parents=True, exist_ok=True)
    with open(MERGED_REPORT_PATH, "w", encoding="utf-8") as f:
        f.write(final_report)

    print(f"Final merged report saved successfully at:\n{MERGED_REPORT_PATH}")


if __name__ == "__main__":
    run()