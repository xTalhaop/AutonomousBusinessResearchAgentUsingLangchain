from langchain_core.tools import tool
from bs4 import BeautifulSoup
import requests

@tool
def scrape(url: str) -> str:
    """Given a URL, scrape the main text content of the page and return it as a string.
    Returns an error message if the page cannot be reached."""
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        return f"Could not fetch {url}: {e}"

    soup = BeautifulSoup(response.text, "html.parser")

    # Remove non-content elements
    for tag in soup(["script", "style", "nav", "footer", "header", "noscript"]):
        tag.decompose()

    text = soup.get_text(separator="\n", strip=True)

    # Cap length to avoid blowing token limits
    max_chars = 6000
    if len(text) > max_chars:
        text = text[:max_chars] + "\n\n[Content truncated due to length]"

    return text