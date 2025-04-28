import os
import yaml
import logging
import sys
from pathlib import Path
from dotenv import load_dotenv
from crewai import Agent, Crew, Process, Task, LLM
from crewai.project import CrewBase, agent, crew, task
from crewai_tools import ScrapeWebsiteTool
from resumemaker.tools.custom_tool import (
    PDFAnalyzerTool, GoogleSearchTool
)
from resumemaker.tools.opensource_rag_tool import OpenSourceRAGTool
from resumemaker.tools.githubanalyzer_tool import GitHubFetchTool
from resumemaker.crews.poem_crew.data_extraction_output import CandidateProfile
from resumemaker.utils.api_check import check_api_keys
import json

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Set up paths
BASE_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = Path(__file__).resolve().parents[4]  # 4 levels up from this file
INPUT_DIR = PROJECT_ROOT / "input"
OUTPUT_DIR = PROJECT_ROOT / "output"

def load_config():
    """Load configuration from config.json"""
    config_path = INPUT_DIR / "config.json"
    try:
        with open(config_path, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        logger.warning(f"Config file not found at {config_path}. Using default values.")
        return {
            "linkedin_url": "https://www.linkedin.com/in/your-profile",
            "github_url": "your-github-username",
            "resume_file": "resume.pdf",
            "job_description_file": "job_description.txt",
            "model_settings": {
                "provider": "openrouter",
                "model": "meta-llama/llama-4-maverick:free",
                "temperature": 0.7
            }
        }
    except json.JSONDecodeError:
        logger.error(f"Error parsing config file at {config_path}. Using default values.")
        return {
            "linkedin_url": "https://www.linkedin.com/in/your-profile",
            "github_url": "your-github-username",
            "resume_file": "resume.pdf",
            "job_description_file": "job_description.txt",
            "model_settings": {
                "provider": "openrouter",
                "model": "meta-llama/llama-4-maverick:free",
                "temperature": 0.7
            }
        }

# Check API keys
if not check_api_keys():
    logger.error("Missing required API keys. Exiting.")
    sys.exit(1)

# Load configuration
config = load_config()
model_settings = config.get("model_settings", {
    "provider": "openrouter",
    "model": "meta-llama/llama-4-maverick:free",
    "temperature": 0.7
})

# Set LLM configuration with OpenRouter using settings from config
llm = LLM(
    provider=model_settings.get("provider", "openrouter"),
    model=model_settings.get("model", "meta-llama/llama-4-maverick:free"),
    temperature=model_settings.get("temperature", 0.7),
    api_key=os.getenv('OPENROUTER_API_KEY'),
    api_base="https://openrouter.ai/api/v1"
)

@CrewBase
class DataExtraction:
    """Data Extraction Crew with enhanced capabilities"""
    
    config_files = {
        'agents': BASE_DIR / "config" / "data_extraction_agents.yaml",
        'tasks': BASE_DIR / "config" / "data_extraction_tasks.yaml"
    }
    
    # Load configurations
    configs = {}
    for key, file_path in config_files.items():
        file_path = file_path.resolve()
        if not file_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {file_path}")
        
        with open(file_path, 'r') as file:
            configs[key] = yaml.safe_load(file)
    
    @agent
    def data_extraction_agent(self) -> Agent:
        return Agent(
            role="CrewAI Data Extraction Specialist",
            config=self.configs["agents"]["data_extraction_agent"],
            llm=llm,
            verbose=True
        )
    
    @agent
    def github_extraction_agent(self) -> Agent:
        """Dedicated agent for GitHub repository analysis"""
        return Agent(
            config=self.configs["agents"]["github_extraction_agent"],
            llm=llm,
            verbose=True
        )
    
    @agent
    def job_analysis_agent(self) -> Agent:
        return Agent(
            config=self.configs["agents"]["job_analysis_agent"],
            llm=llm,
            verbose=True
        )
    
    @agent
    def profile_structuring_agent(self) -> Agent:
        return Agent(
            config=self.configs["agents"]["profile_structuring_agent"],
            llm=llm,
            verbose=True
        )
    
    @task
    def extract_resume_data(self) -> Task:
        return Task(
            config=self.configs["tasks"]["extract_resume_data"],
            agent=self.data_extraction_agent(),
        )

    @task
    def extract_linkedin_data(self) -> Task:
        return Task(
            config=self.configs["tasks"]["extract_linkedin_data"],
            agent=self.data_extraction_agent(),
            tools=[GoogleSearchTool(), ScrapeWebsiteTool()]
        )

    @task
    def extract_github_profile(self) -> Task:
        return Task(
            config=self.configs["tasks"]["extract_github_data"],
            agent=self.github_extraction_agent(),
            tools=[GitHubFetchTool()]
        )

    @task
    def analyze_github_repositories(self) -> Task:
        return Task(
            config=self.configs["tasks"]["analyze_github_repositories"],
            agent=self.github_extraction_agent(),
            tools=[GitHubFetchTool()],
            context=[self.extract_github_profile()]
        )

    @task
    def analyze_job_posting(self) -> Task:
        return Task(
            config=self.configs["tasks"]["analyze_job_posting"],
            agent=self.job_analysis_agent(),
        )

    @task
    def compare_resume_with_job(self) -> Task:
        return Task(
            config=self.configs["tasks"]["compare_resume_with_job"],
            agent=self.job_analysis_agent(),
            context=[self.extract_resume_data(), self.analyze_job_posting()]
        )

    @task
    def structure_candidate_profile(self) -> Task:
        return Task(
            config=self.configs["tasks"]["structure_candidate_profile"],
            agent=self.profile_structuring_agent(),
            tools=[OpenSourceRAGTool()],
            context=[
                self.extract_resume_data(),
                self.extract_linkedin_data(),
                self.extract_github_profile(),
                self.analyze_github_repositories(),
                self.analyze_job_posting(),
                self.compare_resume_with_job()
            ],
            output_json=CandidateProfile
        )

    @crew
    def crew(self) -> Crew:
        return Crew(
            agents=[
                self.data_extraction_agent(),
                self.github_extraction_agent(),
                self.job_analysis_agent(),
                self.profile_structuring_agent()
            ],
            tasks=[
                self.extract_resume_data(),
                self.extract_linkedin_data(),
                self.extract_github_profile(),
                self.analyze_github_repositories(),
                self.analyze_job_posting(),
                self.compare_resume_with_job(),
                self.structure_candidate_profile()
            ],
            process=Process.sequential,
            verbose=True
        )

if __name__ == "__main__":
    try:
        # Make sure output directory exists
        OUTPUT_DIR.mkdir(exist_ok=True)
        
        # Load configuration
        config = load_config()
        
        # Initialize tools and crew
        extraction_crew = DataExtraction().crew()
        pdfAnalyzerTool = PDFAnalyzerTool()

        # Set file paths
        resume_path = INPUT_DIR / config["resume_file"]
        job_posting_path = INPUT_DIR / config["job_description_file"]

        # Validate paths
        if not resume_path.exists():
            raise FileNotFoundError(f"Error: Resume file '{resume_path}' not found.")
        if not job_posting_path.exists():
            raise FileNotFoundError(f"Error: Job posting file '{job_posting_path}' not found.")

        # Extract data from files
        read_resume = pdfAnalyzerTool._run(resume_path)
        read_jobPosting = job_posting_path.read_text(encoding="utf-8")

        # Get LinkedIn and GitHub info from config
        linkedin_url = config["linkedin_url"]
        github_url = config["github_url"]
        
        logger.info(f"Starting data extraction with:")
        logger.info(f"- Resume: {resume_path}")
        logger.info(f"- Job description: {job_posting_path}")
        logger.info(f"- LinkedIn: {linkedin_url}")
        logger.info(f"- GitHub: {github_url}")
        
        # Run the extraction crew
        candidate_profile = extraction_crew.kickoff(
            inputs={
                "resume_details": read_resume,
                "linkedin_url": linkedin_url,
                "github_url": github_url,
                "job_posting": read_jobPosting
            }
        )
        
        logger.info("Data extraction completed successfully!")
        
        # Save the extracted profile
        output_file = OUTPUT_DIR / "candidate_profile.json"
        with open(output_file, "w") as f:
            json.dump(candidate_profile.dict(), f, indent=2)
        
        logger.info(f"Profile saved to {output_file}")
        
    except Exception as e:
        logger.error(f"Error during data extraction: {str(e)}")
        raise