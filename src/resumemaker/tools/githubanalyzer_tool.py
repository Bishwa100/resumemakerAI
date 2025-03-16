import os
import time
import logging
import random
import requests
import json
from typing import Dict, List, Any
from dotenv import load_dotenv
# Logger setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
load_dotenv()
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")  # Replace with your actual GitHub token
API_BASE_URL = "https://api.github.com"
MAX_RETRIES = 10

def fetch_github_data(username: str, max_repos: int = 10, retry_count: int = 0) -> Dict[str, Any]:
    """Fetch GitHub project details and tech stack for a given username."""
    headers = {"Authorization": f"token {GITHUB_TOKEN}", "Accept": "application/vnd.github+json"}
    user_response = None # Initialize the user response variable.
    repos_response = None # Initialize the repos response variable.

    try:
        user_url = f"{API_BASE_URL}/users/{username}"
        user_response = requests.get(user_url, headers=headers)
        user_response.raise_for_status()  # Raise HTTPError for bad responses (4xx or 5xx)
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
                    "tech_stack": detect_tech_stack(repo["full_name"]),
                    "language": repo.get("language"),
                }
                projects.append(project_data)
                logger.info(f"Processed repository: {repo['name']}")

        return {"projects": projects}

    except requests.exceptions.RequestException as e:
        if user_response is not None and user_response.status_code == 403 or repos_response is not None and repos_response.status_code == 403:
            if retry_count >= MAX_RETRIES:
                return {"error": "Max retries reached due to rate limit."}

            reset_time = int(user_response.headers.get("X-RateLimit-Reset"))
            current_time = time.time()
            wait_time = reset_time - current_time

            if wait_time <= 0:
                return fetch_github_data(username, max_repos, retry_count)
            else:
                retry_count += 1
                backoff_time = (2 ** retry_count) + wait_time
                jitter = random.uniform(0, 1)
                sleep_time = backoff_time + jitter

                logger.warning(f"Rate limit exceeded. Reset time: {time.ctime(reset_time)}. Waiting {sleep_time:.2f} seconds.")
                time.sleep(sleep_time)
                return fetch_github_data(username, max_repos, retry_count)
        else:
            logger.error(f"GitHub API error: {str(e)}")
            return {"error": f"GitHub API error: {str(e)}"}
    except Exception as e:
        logger.error(f"Error fetching GitHub projects: {str(e)}")
        return {"error": f"Error fetching GitHub projects: {str(e)}"}

def detect_tech_stack(full_repo_name: str) -> List[str]:
    """Detect technologies used in the repository."""
    headers = {"Authorization": f"token {GITHUB_TOKEN}", "Accept": "application/vnd.github+json"}
    tech_stack = []

    try:
        contents_url = f"{API_BASE_URL}/repos/{full_repo_name}/contents"
        contents_response = requests.get(contents_url, headers=headers)
        contents_response.raise_for_status()
        contents_data = contents_response.json()

        # ... (rest of your tech stack detection logic using requests)
        # add the logic from the previous answer here.

    except requests.exceptions.RequestException as e:
        logger.error(f"Error detecting tech stack for {full_repo_name}: {str(e)}")
    except Exception as e:
        logger.error(f"Error detecting tech stack for {full_repo_name}: {str(e)}")

    return tech_stack
