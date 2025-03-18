import warnings
warnings.filterwarnings('ignore')

import os
import yaml
import logging
from pathlib import Path
from dotenv import load_dotenv
from crewai import Agent, Crew, Process, Task, LLM
from crewai.project import CrewBase, agent, crew, task
from crewai_tools import ScrapeWebsiteTool
from resumemaker.tools.custom_tool import (
    PDFAnalyzerTool, MistralRAGTool, GoogleSearchTool, MistralPDFUploadTool
)
from resumemaker.tools.githubanalyzer_tool import GitHubFetchTool
from resumemaker.crews.poem_crew.data_extraction_output import CandidateProfile
import json
import litellm
litellm._turn_on_debug()

# Setup logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Set LLM configuration
# llm = LLM(
#     model="ollama/deepseek-r1:8b",
#     base_url="http://localhost:11435"
# )

llm = LLM(
    model="mistral/mistral-large-latest",
    temperature=0.7,
    api_key= os.getenv('MISTRAL_API_KEY')
)

BASE_DIR = Path(__file__).resolve().parent

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
            tools=[GitHubFetchTool(), GoogleSearchTool(), ScrapeWebsiteTool()]
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
            tools=[MistralRAGTool()]
        )

    @task
    def compare_resume_with_job(self) -> Task:
        return Task(
            config=self.configs["tasks"]["compare_resume_with_job"],
            agent=self.job_analysis_agent(),
            tools=[MistralRAGTool()],
            context=[self.extract_resume_data(), self.analyze_job_posting()]
        )

    @task
    def structure_candidate_profile(self) -> Task:
        return Task(
            config=self.configs["tasks"]["structure_candidate_profile"],
            agent=self.profile_structuring_agent(),
            tools=[MistralRAGTool()],
            context=[
                self.extract_resume_data(),
                self.extract_linkedin_data(),
                self.analyze_github_repositories(),
                self.analyze_job_posting(),
                self.compare_resume_with_job()
            ],
            output_pydantic=CandidateProfile
        )

    @crew
    def crew(self) -> Crew:
        return Crew(
            agents=[
                self.data_extraction_agent(),
                # self.github_extraction_agent(),
                # self.job_analysis_agent(),
                # self.profile_structuring_agent()
            ],
            tasks=[
                self.extract_resume_data(),
                # self.extract_linkedin_data(),
                # self.extract_github_profile(),
                # self.analyze_github_repositories(),
                # self.analyze_job_posting(),
                # self.compare_resume_with_job(),
                # self.structure_candidate_profile()
            ],
            process=Process.sequential,
            verbose=True
        )

if __name__ == "__main__":
    try:
        extraction_crew = DataExtraction().crew()
        pdfAnalyzerTool = PDFAnalyzerTool()

        resume_path = BASE_DIR / 'resume.pdf'
        job_posting_path = BASE_DIR / "abc.txt"

        # Validate paths
        if not resume_path.exists():
            raise FileNotFoundError(f"Error: Resume file '{resume_path}' not found.")
        if not job_posting_path.exists():
            raise FileNotFoundError(f"Error: Job posting file '{job_posting_path}' not found.")

        # Extract data from files
        read_resume = pdfAnalyzerTool._run(resume_path)
        logger.debug(f"Raw Resume Text: {read_resume}")  # Log raw text for verification
        read_jobPosting = job_posting_path.read_text(encoding="utf-8")
        logger.debug(f"Raw Job Posting Text: {read_jobPosting}")

        # Replace with your actual LinkedIn and GitHub info
        linkedin_url = "https://www.linkedin.com/in/bishwanath-jana"  # Example
        github_url = "Bishwa100"  # Your GitHub username
        
        # Run the extraction crew
        candidate_profile = extraction_crew.kickoff(
            inputs={
                "resume_details": read_resume
                # "linkedin_url": linkedin_url,
                # "github_url": github_url,
                # "job_posting": read_jobPosting
            }
        )
        
        logger.info("Data extraction completed successfully!")
        logger.info(f"Candidate Profile: {candidate_profile}")
        
        # Save the extracted profile
        output_file = BASE_DIR / "candidate_profile.json"
        with open(output_file, "w") as f:
            json.dump(candidate_profile.dict(), f, indent=2)
        
    except Exception as e:
        logger.error(f"Error during data extraction: {str(e)}")
        raise