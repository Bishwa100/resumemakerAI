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
from crewai_tools import ScrapeWebsiteTool
from resumemaker.tools.custom_tool import MistralRAGTool
from resumemaker.tools.pdfGenarator_tool import PDFGeneratorTool
from resumemaker.tools.image_processing_tool import ImageProcessingTool

# Setup logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Configure LLM
class CustomLLM(LLM):
    def call(self, messages, **kwargs):
        # Ensure the last message is a user role if needed
        if messages and messages[-1]["role"] == "assistant":
            messages.append({"role": "user", "content": "Please continue with the resume creation."})
        return super().call(messages, **kwargs)

llm = CustomLLM(
    model="mistral/mistral-large-latest",
    temperature=0.5,  # Lower temperature for more precise outputs
    api_key=os.getenv('MISTRAL_API_KEY'),
)

BASE_DIR = Path(__file__).resolve().parent

@CrewBase
class ResumeCreation:
    """ATS-Friendly Resume Creation Crew with design capabilities"""
    
    config_files = {
        'agents': BASE_DIR / "config" / "resume_creation_agents.yaml",
        'tasks': BASE_DIR / "config" / "resume_creation_tasks.yaml"
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
    def ats_optimization_agent(self) -> Agent:
        """Agent responsible for making resume content ATS-friendly"""
        return Agent(
            role="ATS Optimization Specialist",
            config=self.configs["agents"]["ats_optimization_agent"],
            llm=llm,
            verbose=True
        )
    
    @agent
    def resume_content_agent(self) -> Agent:
        """Agent responsible for crafting compelling resume content"""
        return Agent(
            role="Resume Content Specialist",
            config=self.configs["agents"]["resume_content_agent"],
            llm=llm,
            verbose=True
        )
    
    @agent
    def resume_design_agent(self) -> Agent:
        """Agent responsible for visual design and layout of the resume"""
        return Agent(
            role="Resume Design Specialist",
            config=self.configs["agents"]["resume_design_agent"],
            llm=llm,
            verbose=True
        )
    
    @agent
    def image_integration_agent(self) -> Agent:
        """Agent responsible for handling and integrating images into the resume"""
        return Agent(
            role="Resume Image Integration Specialist",
            config=self.configs["agents"]["image_integration_agent"],
            llm=llm,
            verbose=True
        )
    
    @task
    def analyze_candidate_profile(self) -> Task:
        """Analyzes the candidate profile JSON from data extraction crew"""
        return Task(
            config=self.configs["tasks"]["analyze_candidate_profile"],
            agent=self.resume_content_agent(),
        )
    
    @task
    def identify_keywords_for_ats(self) -> Task:
        """Extracts and optimizes keywords for ATS systems"""
        return Task(
            config=self.configs["tasks"]["identify_keywords_for_ats"],
            agent=self.ats_optimization_agent(),
            tools=[MistralRAGTool()],
            context=[self.analyze_candidate_profile()]
        )
    
    @task
    def craft_resume_sections(self) -> Task:
        """Creates optimized content for each resume section"""
        return Task(
            config=self.configs["tasks"]["craft_resume_sections"],
            agent=self.resume_content_agent(),
            context=[self.analyze_candidate_profile(), self.identify_keywords_for_ats()]
        )
    
    @task
    def process_profile_image(self) -> Task:
        """Processes the user-provided profile image for resume integration"""
        return Task(
            config=self.configs["tasks"]["process_profile_image"],
            agent=self.image_integration_agent(),
            tools=[ImageProcessingTool()]
        )
    
    @task
    def design_resume_layout(self) -> Task:
        """Creates the visual design and layout for the resume"""
        return Task(
            config=self.configs["tasks"]["design_resume_layout"],
            agent=self.resume_design_agent(),
            tools=[MistralRAGTool()],
            context=[self.craft_resume_sections(), self.process_profile_image()]
        )
    
    @task
    def generate_final_resume(self) -> Task:
        """Generates the final ATS-friendly resume with integrated design and image"""
        return Task(
            config=self.configs["tasks"]["generate_final_resume"],
            agent=self.resume_design_agent(),
            tools=[PDFGeneratorTool()],
            context=[
                self.craft_resume_sections(),
                self.process_profile_image(),
                self.design_resume_layout()
            ]
        )
    
    @crew
    def crew(self) -> Crew:
        return Crew(
            agents=[
                self.ats_optimization_agent(),
                self.resume_content_agent(),
                self.resume_design_agent(),
                self.image_integration_agent()
            ],
            tasks=[
                self.analyze_candidate_profile(),
                self.identify_keywords_for_ats(),
                self.craft_resume_sections(),
                self.process_profile_image(),
                self.design_resume_layout(),
                self.generate_final_resume()
            ],
            process=Process.sequential,
            verbose=True
        )

if __name__ == "__main__":
    try:
        # Load candidate profile from data extraction crew output
        profile_path = BASE_DIR / "candidate_profile.json"
        
        if not profile_path.exists():
            raise FileNotFoundError(f"Error: Candidate profile file '{profile_path}' not found.")
        
        with open(profile_path, 'r') as f:
            candidate_profile = json.load(f)
        
        # Get user's profile image path
        profile_image_path = BASE_DIR / "bishwanath.jpg"
        
        if not profile_image_path.exists():
            logger.warning(f"Profile image not found at '{profile_image_path}'. Resume will be created without an image.")
            profile_image = None
        else:
            profile_image = profile_image_path
        
        # Create and run the resume creation crew
        resume_crew = ResumeCreation().crew()
        
        final_resume = resume_crew.kickoff(
            inputs={
                "candidate_profile": candidate_profile,
                "profile_image": str(profile_image_path),
                "ats_optimization_level": "high",  # Options: low, medium, high
                "design_style": "professional"  # Options: minimal, professional, creative
            }
        )
        
        logger.info("Resume creation completed successfully!")
        logger.info(f"Final resume saved to: {final_resume}")
        
    except Exception as e:
        logger.error(f"Error during resume creation: {str(e)}")
        raise