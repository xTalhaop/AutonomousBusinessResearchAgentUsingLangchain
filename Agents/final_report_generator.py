from pathlib import Path
from langchain.agents import create_agent
from langchain_google_genai import ChatGoogleGenerativeAI
from dotenv import load_dotenv

from Tools.md_to_docx import md_to_docx

load_dotenv()

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
MERGED_REPORT_PATH = DATA_DIR / "merged_output" / "merged_report.md"
FINAL_DOCX_PATH = DATA_DIR / "final_reports" / "business_report.docx"


def run():
    if not MERGED_REPORT_PATH.exists():
        print(f"No merged report found at {MERGED_REPORT_PATH}. Skipping export.")
        return

    system_prompt = """
You are the Document Export Agent.

Your job is to generate a Microsoft Word (.docx) document from a Markdown (.md) file.

You have access to one tool:

- md_to_docx

Always use this tool whenever the user requests a DOCX document.

Do not answer manually.

Return the tool result after execution.
"""

    llm = ChatGoogleGenerativeAI(
        model="gemini-2.5-flash",
        temperature=0
    )

    agent = create_agent(
        model=llm,
        tools=[md_to_docx],
        system_prompt=system_prompt
    )

    FINAL_DOCX_PATH.parent.mkdir(parents=True, exist_ok=True)

    response = agent.invoke({
        "messages": [
            {
                "role": "user",
                "content": f"""
Convert the following Markdown file into a DOCX document.

Input File:
{MERGED_REPORT_PATH}

Output File:
{FINAL_DOCX_PATH}
"""
            }
        ]
    })

    print(response["messages"][-1].content)


if __name__ == "__main__":
    run()