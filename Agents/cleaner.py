from pathlib import Path
from langchain.agents import create_agent
from langchain_groq import ChatGroq
from dotenv import load_dotenv

load_dotenv()

# This file lives at Agents/cleaner.py, so parent.parent = project root
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
OUTPUTS_DIR = DATA_DIR / "outputs"
CLEANED_DIR = DATA_DIR / "cleaned_outputs"


def run():
    system_prompt = """You are the Cleaning Agent in a Deep Research pipeline.

Your task is to clean ONE raw Markdown (.md) document generated from a scraped webpage.

Your responsibilities are:

- Remove navigation menus.
- Remove cookie notices.
- Remove advertisements.
- Remove newsletter and subscription sections.
- Remove social media links/buttons.
- Remove "Related Articles", "Read More", and promotional content.
- Remove page headers, footers, copyright notices, privacy policy links, and terms of service.
- Remove duplicate headings, paragraphs, and excessive blank lines.
- Remove broken or unnecessary Markdown formatting.

Preserve:

- All research-relevant information.
- Technical explanations.
- Definitions.
- Examples.
- Code blocks.
- Tables.
- Lists.
- Important notes and warnings.
- Hyperlinks that are useful for the topic.
- Proper Markdown formatting.

Do NOT summarize.
Do NOT rewrite the content unnecessarily.
Do NOT generate new information.
Do NOT remove important information.
If you are unsure whether something is relevant, keep it.

Return ONLY the cleaned Markdown document.

The output must be a complete Markdown document that can be directly saved as a `.md` file."""

    llm = ChatGroq(
        model="llama-3.3-70b-versatile",
        temperature=0
    )
    agent = create_agent(
        model=llm,
        system_prompt=system_prompt
    )

    files = list(OUTPUTS_DIR.glob("*.md"))
    if not files:
        print(f"No raw markdown files found in {OUTPUTS_DIR}. Skipping cleaning.")
        return

    CLEANED_DIR.mkdir(parents=True, exist_ok=True)

    for file in files:
        with open(file, "r", encoding="utf-8") as f:
            markdown = f.read()

        print(f"Cleaning: {file.name}")
        response = agent.invoke({
            "messages": [
                {"role": "user", "content": markdown}
            ]
        })

        output_file = CLEANED_DIR / f"{file.stem}_clean.md"
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(response["messages"][-1].content)

        print(f"Saved: {output_file}")


if __name__ == "__main__":
    run()