from typing import Type, Dict, Any
import os
import requests
from pydantic import BaseModel, Field
from crewai.tools import BaseTool
from dotenv import load_dotenv

load_dotenv()

class GoogleSearchInput(BaseModel):
    """Input schema for GoogleSearchTool."""
    query: str = Field(..., description="Search query for Google.")

class GoogleSearchTool(BaseTool):
    name: str = "GoogleSearch"
    description: str = "Searches Google and returns the top 5 results."
    args_schema: Type[BaseModel] = GoogleSearchInput

    def _run(self, query: str) -> Dict[str, Any]:
        """Performs a Google search using the Custom Search API."""
        API_KEY = os.getenv("GOOGLE_API_KEY")
        CX = os.getenv("GOOGLE_CX")

        if not API_KEY or not CX:
            return {"error": "Missing GOOGLE_API_KEY or GOOGLE_CX in environment variables."}

        url = f"https://www.googleapis.com/customsearch/v1?q={query}&key={API_KEY}&cx={CX}"

        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            data = response.json()

            if "items" not in data:
                return {"error": "No search results found."}

            results = [
                {
                    "title": item.get("title", "No Title"),
                    "link": item.get("link", "No Link"),
                    "snippet": item.get("snippet", "No Description"),
                }
                for item in data["items"][:5]  # Get top 5 results
            ]

            return {"results": results}
        
        except requests.exceptions.RequestException as e:
            return {"error": str(e)} 