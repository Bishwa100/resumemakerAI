import warnings
warnings.filterwarnings('ignore')

import os
import yaml
import logging
import json
from pathlib import Path
from dotenv import load_dotenv
from crewai import Agent, Crew, Process, Task, LLM
from crewai.project import CrewBase, agent, crew, task
from resumemaker.tools.opensource_rag_tool import OpenSourceRAGTool
from resumemaker.tools.image_processing_tool import ImageProcessingTool
from resumemaker.tools.latex_generator_tool import LaTeXGeneratorTool

# Setup logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Configure LLM
# class CustomLLM(LLM):
#     def call(self, messages, **kwargs):
#         if messages and messages[-1]["role"] == "assistant":
#             messages.append({"role": "user", "content": "Please continue with the resume creation."})
#         return super().call(messages, **kwargs)

# llm = CustomLLM(
#     model="mistral/mistral-large-latest",
#     temperature=0.3,
#     api_key=os.getenv('MISTRAL_API_KEY'),
# )


llm = LLM(
    model="gemini/gemini-1.5-pro-latest",
    temperature=0.7,
    api_key= os.getenv('GEMINI_API_KEY')
)

# Set up paths
BASE_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = Path(__file__).resolve().parents[4]  # 4 levels up from this file
INPUT_DIR = PROJECT_ROOT / "input"
OUTPUT_DIR = PROJECT_ROOT / "output"

@CrewBase
class LaTeXResumeCreation:
    """High ATS-Friendly LaTeX Resume Creation Crew"""
    
    config_files = {
        'agents': BASE_DIR / "config" / "resume_creation_agents.yaml",
        'tasks': BASE_DIR / "config" / "resume_creation_tasks.yaml"
    }
    
    configs = {}
    for key, file_path in config_files.items():
        file_path = file_path.resolve()
        if not file_path.exists():
            logger.warning(f"Config file not found at {file_path}. Ensure the file exists.")
            raise FileNotFoundError(f"Configuration file not found: {file_path}")
        with open(file_path, 'r') as file:
            configs[key] = yaml.safe_load(file)
    
    # Define Agents
    @agent
    def ats_optimization_agent(self) -> Agent:
        return Agent(config=self.configs["agents"]["ats_optimization_agent"], llm=llm, verbose=True)
    
    @agent
    def resume_content_agent(self) -> Agent:
        return Agent(config=self.configs["agents"]["resume_content_agent"], llm=llm, verbose=True)
    
    @agent
    def latex_resume_agent(self) -> Agent:
        return Agent(config=self.configs["agents"]["latex_resume_agent"], llm=llm, verbose=True)
    
    @agent
    def image_processing_agent(self) -> Agent:
        return Agent(config=self.configs["agents"]["image_processing_agent"], llm=llm, verbose=True)

    @agent
    def resume_compilation_agent(self) -> Agent:
        return Agent(config=self.configs["agents"]["resume_compilation_agent"], llm=llm, verbose=True)
    
    # Define Tasks
    @task
    def analyze_candidate_profile(self) -> Task:
        return Task(config=self.configs["tasks"]["analyze_candidate_profile"], agent=self.resume_content_agent())
    
    @task
    def identify_keywords_for_ats(self) -> Task:
        return Task(
            config=self.configs["tasks"]["identify_keywords_for_ats"],
            agent=self.ats_optimization_agent(),
            tools=[OpenSourceRAGTool()],
            context=[self.analyze_candidate_profile()]
        )
    
    @task
    def craft_resume_sections(self) -> Task:
        return Task(
            config=self.configs["tasks"]["craft_resume_sections"],
            agent=self.resume_content_agent(),
            context=[self.analyze_candidate_profile(), self.identify_keywords_for_ats()]
        )
    
    @task
    def process_profile_image(self) -> Task:
        return Task(
            config=self.configs["tasks"]["process_profile_image"],
            agent=self.image_processing_agent(),
            tools=[ImageProcessingTool()]
        )
    
    @task
    def create_latex_template(self) -> Task:
        return Task(
            config=self.configs["tasks"]["create_latex_template"],
            agent=self.latex_resume_agent(),
            tools=[OpenSourceRAGTool()],
            context=[self.craft_resume_sections()]
        )
    
    @task
    def generate_latex_resume(self) -> Task:
        return Task(
            config=self.configs["tasks"]["generate_latex_resume"],
            agent=self.latex_resume_agent(),
            tools=[LaTeXGeneratorTool()],
            context=[self.craft_resume_sections(), self.process_profile_image(), self.create_latex_template()]
        )
    
    @task
    def compile_final_resume(self) -> Task:
        return Task(
            config=self.configs["tasks"]["compile_final_resume"],
            agent=self.resume_compilation_agent(),
            tools=[LaTeXGeneratorTool()],
            context=[self.generate_latex_resume()]
        )
    
    @crew
    def crew(self) -> Crew:
        return Crew(
            agents=[
                self.ats_optimization_agent(),
                self.resume_content_agent(),
                self.latex_resume_agent(),
                self.image_processing_agent(),
                self.resume_compilation_agent()
            ],
            tasks=[
                self.analyze_candidate_profile(),
                self.identify_keywords_for_ats(),
                self.craft_resume_sections(),
                self.process_profile_image(),
                self.create_latex_template(),
                self.generate_latex_resume(),
                self.compile_final_resume()
            ],
            process=Process.sequential,
            verbose=True
        )

if __name__ == "__main__":
    try:
        # Make sure output directory exists
        OUTPUT_DIR.mkdir(exist_ok=True)
        
        # Load Candidate Profile
        profile_path = INPUT_DIR / "candidate_profile.json"
        if not profile_path.exists():
            raise FileNotFoundError(f"Error: Candidate profile file '{profile_path}' not found.")
        
        with open(profile_path, 'r') as f:
            candidate_profile = json.load(f)["json_dict"]  # Use the 'json_dict' section
        
        # Load Profile Image
        profile_image_path = INPUT_DIR / "bishwanath.jpg"
        if not profile_image_path.exists():
            logger.warning(f"Profile image not found at '{profile_image_path}'. Resume will be created without an image.")
            profile_image = None
        else:
            profile_image = profile_image_path
        
        # Initialize Crew and Start Processing
        resume_crew = LaTeXResumeCreation().crew()
        final_resume = resume_crew.kickoff(
            inputs={
                "candidate_profile": candidate_profile,
                "profile_image": str(profile_image_path) if profile_image else None,
                "ats_optimization_level": "high",
                "resume_style": "professional",
                "latex_class": "moderncv",
                "latex_color_theme": "black"
            }
        )
        
        logger.info("✅ High ATS-friendly LaTeX resume creation completed successfully!")
        logger.info(f"📄 Final resume PDF saved to: {final_resume}")
        
    except FileNotFoundError as fe:
        logger.error(f"❌ FileNotFoundError: {str(fe)}")
    except json.JSONDecodeError:
        logger.error("❌ JSONDecodeError: Failed to parse 'candidate_profile.json'. Ensure it's properly formatted.")
    except Exception as e:
        logger.error(f"❌ Error during LaTeX resume creation: {str(e)}")
        raise
