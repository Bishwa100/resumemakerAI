import os
import time
import logging
import random
import requests
from typing import Dict, List, Any, Type
from pydantic import BaseModel, Field
from crewai.tools import BaseTool
from dotenv import load_dotenv

# Logger setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
API_BASE_URL = "https://api.github.com"
MAX_RETRIES = 10

class GitHubFetchInput(BaseModel):
    """Input schema for GitHubFetchTool."""
    username: str = Field(..., description="GitHub username to fetch project details for.")
    max_repos: int = Field(10, description="Maximum number of repositories to fetch.")

class GitHubFetchTool(BaseTool):
    name: str = "GitHubFetchTool"
    description: str = "Fetches GitHub project details and tech stack for a given user."
    args_schema: Type[BaseModel] = GitHubFetchInput

    def _run(self, username: str, max_repos: int = 10) -> Dict[str, Any]:
        """Fetch GitHub project details and tech stack for a given username."""
        headers = {"Authorization": f"token {GITHUB_TOKEN}", "Accept": "application/vnd.github+json"}
        user_url = f"{API_BASE_URL}/users/{username}"

        try:
            user_response = requests.get(user_url, headers=headers)
            user_response.raise_for_status()
            user_data = user_response.json()
            
            repos_url = f"{user_data['repos_url']}?per_page={max_repos}"
            repos_response = requests.get(repos_url, headers=headers)
            repos_response.raise_for_status()
            repos_data = repos_response.json()
            
            projects = []
            for repo in repos_data:
                if not repo["fork"]:
                    project_data = {
                        "name": repo["name"],
                        "description": repo["description"] or "No description",
                        "url": repo["html_url"],
                        "tech_stack": self.detect_tech_stack(repo["full_name"]),
                        "language": repo.get("language"),
                    }
                    projects.append(project_data)
                    logger.info(f"Processed repository: {repo['name']}")

            return {"projects": projects}
        
        except requests.exceptions.RequestException as e:
            logger.error(f"GitHub API error: {str(e)}")
            return {"error": f"GitHub API error: {str(e)}"}
        except Exception as e:
            logger.error(f"Error fetching GitHub projects: {str(e)}")
            return {"error": f"Error fetching GitHub projects: {str(e)}"}
    
    def detect_tech_stack(self, full_repo_name: str) -> List[str]:
        """Detect technologies used in the repository."""
        headers = {"Authorization": f"token {GITHUB_TOKEN}", "Accept": "application/vnd.github+json"}
        tech_stack = []
        
        try:
            contents_url = f"{API_BASE_URL}/repos/{full_repo_name}/contents"
            contents_response = requests.get(contents_url, headers=headers)
            contents_response.raise_for_status()
            contents_data = contents_response.json()
            
            # Implement tech stack detection logic based on repo contents
            for file in contents_data:
                if "package.json" in file["name"]:
                    tech_stack.append("JavaScript/Node.js")
                elif "requirements.txt" in file["name"]:
                    tech_stack.append("Python")
                elif "Gemfile" in file["name"]:
                    tech_stack.append("Ruby on Rails")
                # Add more detections as needed
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error detecting tech stack for {full_repo_name}: {str(e)}")
        except Exception as e:
            logger.error(f"Error detecting tech stack for {full_repo_name}: {str(e)}")
        
        return tech_stack

# if __name__ == "__main__":
#     tool = GitHubFetchTool()
#     username = "Bishwa100"  # Replace with a valid GitHub username
#     result = tool._run(username=username, max_repos=5)
#     print(result)