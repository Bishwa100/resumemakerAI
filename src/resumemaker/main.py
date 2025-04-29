#!/usr/bin/env python
import os
import logging
import json
from pathlib import Path
from dotenv import load_dotenv

from resumemaker.crews.poem_crew.data_extraction_crew import DataExtraction
from resumemaker.crews.poem_crew.resume_making_crew import LaTeXResumeCreation
from resumemaker.tools.custom_tool import PDFAnalyzerTool
from resumemaker.utils.api_check import check_api_keys

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Set up paths
PROJECT_ROOT = Path(__file__).resolve().parents[3]  # 3 levels up from this file
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

def complete_resume_pipeline():
    """Full pipeline that integrates both data extraction and resume creation"""
    try:
        # Check API keys
        if not check_api_keys():
            logger.error("Missing required API keys. Exiting.")
            return False

        # Make sure output directory exists
        OUTPUT_DIR.mkdir(exist_ok=True)
        
        # Load configuration
        config = load_config()
        
        # Set file paths
        resume_path = INPUT_DIR / config["resume_file"]
        job_posting_path = INPUT_DIR / config["job_description_file"]
        profile_image_path = INPUT_DIR / "bishwanath.jpg"

        # Validate paths
        if not resume_path.exists():
            raise FileNotFoundError(f"Error: Resume file '{resume_path}' not found.")
        if not job_posting_path.exists():
            raise FileNotFoundError(f"Error: Job posting file '{job_posting_path}' not found.")

        # 1. Extract data using the data extraction crew
        logger.info("Starting data extraction process...")
        
        # Initialize tools and extraction crew
        extraction_crew = DataExtraction().crew()
        pdf_analyzer = PDFAnalyzerTool()
        
        # Extract data from files
        read_resume = pdf_analyzer._run(resume_path)
        read_job_posting = job_posting_path.read_text(encoding="utf-8")
        
        # Run the data extraction crew
        extraction_result = extraction_crew.kickoff(
            inputs={
                "resume_details": read_resume,
                "linkedin_url": config["linkedin_url"],
                "github_url": config["github_url"],
                "job_posting": read_job_posting
            }
        )
        
        # Save the extracted candidate profile
        candidate_profile_path = OUTPUT_DIR / "candidate_profile.json"
        with open(candidate_profile_path, 'w') as f:
            json.dump(extraction_result.dict(), f, indent=2)
        
        logger.info(f"✅ Data extraction completed. Profile saved to {candidate_profile_path}")
        
        # 2. Create resume using the resume making crew
        logger.info("Starting resume creation process...")
        
        # Initialize resume crew
        resume_crew = LaTeXResumeCreation().crew()
        
        # Check if profile image exists
        if not profile_image_path.exists():
            logger.warning(f"Profile image not found at '{profile_image_path}'. Resume will be created without an image.")
            profile_image = None
        else:
            profile_image = str(profile_image_path)
        
        # Run the resume creation crew
        final_resume = resume_crew.kickoff(
            inputs={
                "candidate_profile": extraction_result.dict(),
                "profile_image": profile_image,
                "ats_optimization_level": "high",
                "resume_style": "professional",
                "latex_class": "moderncv",
                "latex_color_theme": "black"
            }
        )
        
        logger.info("✅ High ATS-friendly LaTeX resume creation completed successfully!")
        logger.info(f"📄 Final resume PDF saved to: {final_resume}")
        
        return True
        
    except FileNotFoundError as fe:
        logger.error(f"❌ FileNotFoundError: {str(fe)}")
        return False
    except Exception as e:
        logger.error(f"❌ Error during resume creation pipeline: {str(e)}")
        return False

def kickoff():
    """Main entry point for the application"""
    complete_resume_pipeline()

if __name__ == "__main__":
    kickoff()
