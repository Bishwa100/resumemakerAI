import warnings
warnings.filterwarnings('ignore')
from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task

# If you want to run a snippet of code before or after the crew starts,
# you can use the @before_kickoff and @after_kickoff decorators
# https://docs.crewai.com/concepts/crews#example-crew-class-with-decorators

from langchain_mistralai import ChatMistralAI
from crewai_tools import ScrapeWebsiteTool
from resumemaker.tools.custom_tool import PDFAnalyzerTool,MistralRAGTool,GoogleSearchTool,MistralPDFUploadTool
import getpass
import os
from resumemaker.crews.poem_crew.data_extraction_output import CandidateProfile
from pathlib import Path
import yaml
from dotenv import load_dotenv

load_dotenv()


from langchain_community.llms import Ollama

llm = Ollama(
    model="deepseek-r1:8b",  # Adjust if the model name differs
    base_url="http://localhost:11435"  # Your specified URL
)

# # Set Mistral API key if not already set
# if "MISTRAL_API_KEY" not in os.environ:
#     os.environ["MISTRAL_API_KEY"] = getpass.getpass("Enter your Mistral API key: ")

# # Debug: Print the API key to verify
# print(f"MISTRAL_API_KEY: {os.environ.get('MISTRAL_API_KEY')}")

# # Initialize the LLM with the correct provider
# llm = ChatMistralAI(
#     model="mistral/mistral-medium-latest",  # Add the provider prefix "mistral/"
#     temperature=0,
#     max_retries=2,
# )

# Rest of your code remains the same

# if "MISTRAL_API_KEY" not in os.environ:
#     os.environ["MISTRAL_API_KEY"] = getpass.getpass(os.environ["MISTRAL_API_KEY"])

# llm = ChatMistralAI(
#     model="mistral/mistral-large-latest",  # Add the provider prefix "mistral/"
#     temperature=0,
#     max_retries=2,
#     prefix_messages=True,  # Add this parameter
#     api_key=os.environ["MISTRAL_API_KEY"]
# )
BASE_DIR = Path(__file__).resolve().parent

@CrewBase
class DataExtraction:
    """Data Extraction"""

    files = {
    'agents_config': BASE_DIR / "config" / "data_extraction_agents.yaml",
    'tasks_config': BASE_DIR / "config" / "data_extraction_tasks.yaml",
}

# Check if files exist before loading
    configs = {}
    for config_type, file_path in files.items():
        file_path = file_path.resolve()
        if not file_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {file_path}")
        
        with open(file_path, 'r') as file:
            configs[config_type] = yaml.safe_load(file)
    

    agents_config = configs['agents_config']
    tasks_config = configs['tasks_config']
    
        
    @agent
    def data_extraction_agent(self) -> Agent:
        return Agent(
            config=self.configs["agents_config"]["data_extraction_agent"],
            llm= llm,
            verbose= True,
            tools=[GoogleSearchTool(),ScrapeWebsiteTool()]
        )
    
    @agent
    def job_analysis_agent(self) -> Agent:
        return Agent(
            config=self.configs["agents_config"]["job_analysis_agent"],
            llm= llm,
            verbose= True,
            tools=[GoogleSearchTool(),ScrapeWebsiteTool()]
        )
    @agent
    def profile_structuring_agent(self) -> Agent:
        return Agent(
            config=self.configs["agents_config"]["profile_structuring_agent"],
            llm= llm,
            verbose= True,
            tools=[GoogleSearchTool(),ScrapeWebsiteTool(), MistralRAGTool()]
        )
    # To learn more about structured task outputs,
    # task dependencies, and task callbacks, check out the documentation:
    # https://docs.crewai.com/concepts/tasks#overview-of-a-task
    

    @task
    def extract_linkedin_data(self) -> Task:
        return Task(
            config=self.configs["tasks_config"]["extract_linkedin_data"],
            agent=self.data_extraction_agent()
        )

    @task
    def extract_github_data(self) -> Task:
        return Task(
            config=self.configs["tasks_config"]["extract_github_data"],
            agent=self.data_extraction_agent()
        )

    @task
    def analyze_job_posting(self) -> Task:
        return Task(
            config=self.configs["tasks_config"]["analyze_job_posting"],
            agent=self.job_analysis_agent()
        )

    @task
    def compare_resume_with_job(self) -> Task:
        return Task(
            config=self.configs["tasks_config"]["compare_resume_with_job"],
            agent=self.job_analysis_agent()
        )

    @task
    def structure_candidate_profile(self) -> Task:
        return Task(
            config= self.configs["tasks_config"]["structure_candidate_profile"],
            context=[
                 # Call the method to get the Task object
                self.extract_linkedin_data(),
                self.extract_github_data(),
                self.analyze_job_posting(),
                self.compare_resume_with_job()
            ],
            agent=self.profile_structuring_agent(),  # Also call this method
            output_pydantic=CandidateProfile
        )

    @crew
    def crew(self) -> Crew:
        """Creates the Data Extraction and Resume Analysis Crew"""
        
        return Crew(
            agents=[
                self.data_extraction_agent(),  # Call to get the Agent object
                self.job_analysis_agent(),
                self.profile_structuring_agent()
            ],
            tasks=[
                  # Call to get the Task object
                self.extract_linkedin_data(),
                self.extract_github_data(),
                self.analyze_job_posting(),
                self.compare_resume_with_job(),
                self.structure_candidate_profile()
            ],
            process=Process.sequential,
            verbose=True
        )
    
if __name__ == "__main__":
    extraction_crew = DataExtraction().crew()
    pdfAnalyzerTool = PDFAnalyzerTool()

    # Process Resume PDF
    resume_path = BASE_DIR / 'resume.pdf'
    if Path(resume_path).exists():
        read_resume = pdfAnalyzerTool._run(resume_path)
    else:
        raise FileNotFoundError(f"Error: '{resume_path}' not found.")

    # Read Job Posting (since it's a TXT file, read normally)
    job_posting_path = BASE_DIR / "abc.txt"
    if Path(job_posting_path).exists():
        read_jobPosting = Path(job_posting_path).read_text(encoding="utf-8")
    else:
        raise FileNotFoundError(f"Error: '{job_posting_path}' not found.")

    # Pass extracted data to Crew
    extraction_crew.kickoff(inputs={
        "resume_file": read_resume,
        "linkedin_url": "https://www.linkedin.com/in/bishwanath-jana/",
        "github_url": "https://github.com/Bishwa100",
        "job_posting": read_jobPosting
    })
