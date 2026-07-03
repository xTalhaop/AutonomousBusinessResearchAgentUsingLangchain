from langchain_tavily import TavilySearch
from langchain_core.tools import tool
from dotenv import load_dotenv

load_dotenv()

_Tavily = TavilySearch(
    search_depth="fast",
    max_results=5,
    topic="general",
    include_answer=False,
    include_raw_content=False
)

@tool
def search(query: str) -> list[str]:
    """Search the web and return relevant URLs for a given query. Returns no page content."""
    try:
        results = _Tavily.invoke({"query": query})
        return [r["url"] for r in results["results"]]
    except Exception as e:
        return [f"Search failed for query '{query}': {e}"]