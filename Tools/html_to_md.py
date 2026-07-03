import warnings
from pathlib import Path

from bs4 import BeautifulSoup, MarkupResemblesLocatorWarning
from markdownify import markdownify
from langchain_core.tools import tool

warnings.filterwarnings("ignore", category=MarkupResemblesLocatorWarning)

# This file lives at Tools/html_to_md.py, so parent.parent = project root
PROJECT_ROOT = Path(__file__).resolve().parent.parent
OUTPUTS_DIR = PROJECT_ROOT / "data" / "outputs"

STRIP_TAGS = ["script", "style", "nav", "footer", "header", "noscript"]


@tool
def html_to_md(html: str, filename: str) -> str:
    """Convert raw HTML content into clean Markdown text and save it to the outputs folder."""
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(STRIP_TAGS):
        tag.decompose()

    markdown = markdownify(str(soup), heading_style="ATX")

    OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)
    file_path = OUTPUTS_DIR / filename
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(markdown)

    return f"Saved markdown to {file_path}"