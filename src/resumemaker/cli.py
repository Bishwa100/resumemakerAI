import os
import sys
import argparse
import logging
import json
from pathlib import Path
from typing import Dict, Any

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Add the src directory to the path so we can import our modules
src_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(src_dir))

from resumemaker.tools.custom_tool import PDFAnalyzerTool
from resumemaker.tools.resume_analyzer_tool import ResumeAnalyzerTool
from resumemaker.tools.template_manager_tool import TemplateManagerTool
from resumemaker.tools.job_keyword_extractor_tool import JobKeywordExtractorTool
from resumemaker.crews.poem_crew.data_extraction_crew import DataExtraction
from resumemaker.utils.api_check import check_api_keys
from resumemaker.main import complete_resume_pipeline

def parse_args():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description="Resume Maker CLI")
    
    # Create subparsers for different commands
    subparsers = parser.add_subparsers(dest="command", help="Command to run")
    
    # Generate command
    generate_parser = subparsers.add_parser("generate", help="Generate a resume")
    generate_parser.add_argument("--resume", "-r", required=True, help="Path to resume PDF file")
    generate_parser.add_argument("--job", "-j", required=True, help="Path to job description file")
    generate_parser.add_argument("--template", "-t", default="classic", help="Template name to use (default: classic)")
    generate_parser.add_argument("--output", "-o", help="Output directory (default: ./output)")
    generate_parser.add_argument("--linkedin", "-l", help="LinkedIn profile URL")
    generate_parser.add_argument("--github", "-g", help="GitHub username")
    
    # Analyze command
    analyze_parser = subparsers.add_parser("analyze", help="Analyze a resume against a job description")
    analyze_parser.add_argument("--resume", "-r", required=True, help="Path to resume PDF file")
    analyze_parser.add_argument("--job", "-j", required=True, help="Path to job description file")
    
    # Keywords command
    keywords_parser = subparsers.add_parser("keywords", help="Extract keywords from a job description")
    keywords_parser.add_argument("--job", "-j", required=True, help="Path to job description file")
    keywords_parser.add_argument("--resume", "-r", help="Optional: Path to resume PDF file for comparison")
    keywords_parser.add_argument("--max", "-m", type=int, default=30, help="Maximum number of keywords to extract")
    keywords_parser.add_argument("--output", "-o", help="Output JSON file for results")
    
    # Template command
    template_parser = subparsers.add_parser("template", help="Manage resume templates")
    template_parser.add_argument("action", choices=["list", "get", "create", "save", "delete"], help="Template action")
    template_parser.add_argument("--name", "-n", help="Template name")
    template_parser.add_argument("--type", "-t", default="latex", choices=["latex", "html"], help="Template type")
    template_parser.add_argument("--file", "-f", help="JSON file containing template content for create/save actions")
    
    # Extract command
    extract_parser = subparsers.add_parser("extract", help="Extract data from resume and job description")
    extract_parser.add_argument("--resume", "-r", required=True, help="Path to resume PDF file")
    extract_parser.add_argument("--job", "-j", required=True, help="Path to job description file")
    extract_parser.add_argument("--linkedin", "-l", help="LinkedIn profile URL")
    extract_parser.add_argument("--github", "-g", help="GitHub username")
    extract_parser.add_argument("--output", "-o", help="Output JSON file (default: ./output/candidate_profile.json)")
    
    # Full pipeline command (new)
    pipeline_parser = subparsers.add_parser("full-pipeline", help="Run the complete resume creation pipeline")
    pipeline_parser.add_argument("--config", "-c", help="Custom config file path (optional)")
    
    return parser.parse_args()

def read_file(file_path: str) -> str:
    """Read text from a file"""
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    
    try:
        if path.suffix.lower() == '.pdf':
            pdf_analyzer = PDFAnalyzerTool()
            return pdf_analyzer._run(str(path))
        else:
            return path.read_text(encoding="utf-8")
    except Exception as e:
        logger.error(f"Error reading file {file_path}: {str(e)}")
        raise

def analyze_resume(args):
    """Analyze a resume against a job description"""
    try:
        resume_analyzer = ResumeAnalyzerTool()
        job_text = read_file(args.job)
        
        logger.info(f"Analyzing resume {args.resume} against job description...")
        result = resume_analyzer._run(resume_path=args.resume, job_description=job_text)
        
        if not result.get("success", False):
            logger.error(f"Analysis failed: {result.get('error', 'Unknown error')}")
            return 1
        
        # Print results in a user-friendly format
        print("\n=== Resume Analysis Results ===")
        print(f"ATS Compatibility Score: {result['ats_compatibility_score']}/100")
        
        if result.get("issues"):
            print("\nPotential Issues:")
            for issue_key, issue_value in result["issues"].items():
                if issue_key == "missing_sections" and isinstance(issue_value, list):
                    if issue_value:
                        print(f"  - Missing sections: {', '.join(issue_value)}")
                else:
                    print(f"  - {issue_value}")
        
        if result.get("keyword_match"):
            match_pct = result["keyword_match"]["match_percentage"]
            print(f"\nKeyword Match: {match_pct}%")
            
            if result["keyword_match"].get("missing"):
                missing = result["keyword_match"]["missing"][:10]  # Show top 10 missing keywords
                print(f"  Top missing keywords: {', '.join(missing)}")
        
        if result.get("suggestions"):
            print("\nSuggestions for Improvement:")
            for i, suggestion in enumerate(result["suggestions"], 1):
                print(f"  {i}. {suggestion}")
                
        return 0
        
    except Exception as e:
        logger.error(f"Error analyzing resume: {str(e)}")
        return 1

def extract_keywords(args):
    """Extract keywords from a job description and compare with resume if available"""
    try:
        # Read job description
        job_text = read_file(args.job)
        
        # Read resume if provided
        resume_text = None
        if args.resume:
            resume_text = read_file(args.resume)
        
        # Extract keywords
        keyword_extractor = JobKeywordExtractorTool()
        logger.info(f"Extracting keywords from job description: {args.job}")
        result = keyword_extractor._run(
            job_description=job_text,
            resume_text=resume_text,
            max_keywords=args.max,
            include_scores=True
        )
        
        if not result.get("success", False):
            logger.error(f"Keyword extraction failed: {result.get('error', 'Unknown error')}")
            return 1
        
        # Save to output file if requested
        if args.output:
            output_path = Path(args.output)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, 'w') as f:
                json.dump(result, f, indent=2)
            print(f"Keywords saved to {output_path}")
        
        # Print results in a user-friendly format
        print("\n=== Job Keywords Analysis ===")
        
        # Print categorized keywords
        if "categorized_keywords" in result:
            categories = result["categorized_keywords"]
            
            if categories.get("technical_skills"):
                print("\nTechnical Skills:")
                skills = categories["technical_skills"]
                print(f"  {', '.join(skills.keys())}")
            
            if categories.get("soft_skills"):
                print("\nSoft Skills:")
                skills = categories["soft_skills"]
                print(f"  {', '.join(skills.keys())}")
            
            if categories.get("requirements"):
                print("\nRequirements:")
                for req, score in categories["requirements"].items():
                    print(f"  - {req.capitalize()}")
            
            if categories.get("domain_keywords"):
                print("\nDomain-Specific Terms:")
                domain = list(categories["domain_keywords"].keys())[:10]  # Top 10
                print(f"  {', '.join(domain)}")
        
        # Print resume comparison if available
        if "resume_match" in result:
            match_info = result["resume_match"]
            print(f"\nResume Keyword Match: {match_info.get('match_percentage', 0)}%")
            print(f"  - Keywords found: {match_info.get('total_matches', 0)} of {match_info.get('total_keywords', 0)}")
            
            if match_info.get("missing_keywords"):
                print("\nTop Missing Keywords (consider adding these to your resume):")
                for keyword in match_info["missing_keywords"][:10]:
                    print(f"  - {keyword}")
        
        return 0
        
    except Exception as e:
        logger.error(f"Error extracting keywords: {str(e)}")
        return 1

def manage_templates(args):
    """Manage resume templates"""
    try:
        template_manager = TemplateManagerTool()
        
        if args.action == "list":
            result = template_manager._run(action="list", template_type=args.type)
            if result.get("success", False):
                print(f"\n=== Available {args.type.capitalize()} Templates ===")
                for template in result.get("templates", []):
                    print(f"- {template['name']}: {template.get('description', 'No description')}")
            else:
                logger.error(f"Failed to list templates: {result.get('error')}")
                return 1
                
        elif args.action in ["get", "delete"]:
            if not args.name:
                logger.error(f"Template name is required for '{args.action}' action")
                return 1
                
            result = template_manager._run(action=args.action, template_name=args.name, template_type=args.type)
            if not result.get("success", False):
                logger.error(f"Template operation failed: {result.get('error')}")
                return 1
                
            if args.action == "get":
                print(f"\n=== Template: {args.name} ({args.type}) ===")
                print(json.dumps(result.get("template", {}), indent=2))
            else:
                print(result.get("message", f"Template {args.name} deleted successfully"))
                
        elif args.action in ["create", "save"]:
            if not args.name:
                logger.error(f"Template name is required for '{args.action}' action")
                return 1
                
            if not args.file:
                logger.error(f"Template file is required for '{args.action}' action")
                return 1
                
            try:
                with open(args.file, 'r') as f:
                    template_content = json.load(f)
            except Exception as e:
                logger.error(f"Error reading template file: {str(e)}")
                return 1
                
            result = template_manager._run(
                action=args.action, 
                template_name=args.name, 
                template_content=template_content,
                template_type=args.type
            )
            
            if not result.get("success", False):
                logger.error(f"Template operation failed: {result.get('error')}")
                return 1
                
            print(result.get("message", f"Template {args.name} saved successfully"))
            
        return 0
            
    except Exception as e:
        logger.error(f"Error managing templates: {str(e)}")
        return 1

def extract_data(args):
    """Extract data from resume and job description"""
    try:
        # Check API keys first
        if not check_api_keys():
            logger.error("Required API keys missing. Please check your .env file.")
            return 1
        
        # Create output directory if needed
        output_dir = Path("output")
        output_dir.mkdir(exist_ok=True)
        
        # Set default output file if not provided
        output_file = args.output if args.output else output_dir / "candidate_profile.json"
        output_file = Path(output_file)
        
        # Read resume and job description
        pdf_analyzer = PDFAnalyzerTool()
        resume_text = pdf_analyzer._run(args.resume)
        job_text = read_file(args.job)
        
        # Set LinkedIn and GitHub info
        linkedin_url = args.linkedin or "your-linkedin-profile"
        github_url = args.github or "your-github-username"
        
        logger.info("Starting data extraction process...")
        logger.info(f"Using resume: {args.resume}")
        logger.info(f"Using job description: {args.job}")
        
        # Initialize crew
        extraction_crew = DataExtraction().crew()
        
        # Run the extraction
        logger.info("Extracting data from resume and job description...")
        result = extraction_crew.kickoff(
            inputs={
                "resume_details": resume_text,
                "linkedin_url": linkedin_url,
                "github_url": github_url,
                "job_posting": job_text
            }
        )
        
        # Save result to output file
        with open(output_file, "w") as f:
            json.dump(result.dict(), f, indent=2)
            
        logger.info(f"Data extraction complete. Results saved to {output_file}")
        print(f"Data extraction complete. Results saved to {output_file}")
        return 0
        
    except Exception as e:
        logger.error(f"Error extracting data: {str(e)}")
        return 1

def generate_resume(args):
    """Generate a resume"""
    logger.info("Resume generation not yet implemented")
    print("Resume generation coming soon!")
    return 0

def run_full_pipeline(args):
    """Run the complete end-to-end pipeline for resume creation"""
    try:
        # If a custom config file is provided, temporarily replace the default one
        config_backup = None
        if args.config:
            config_path = Path(args.config)
            if not config_path.exists():
                logger.error(f"Config file not found: {args.config}")
                return 1
                
            input_dir = Path(__file__).resolve().parents[3] / "input"
            default_config = input_dir / "config.json"
            
            if default_config.exists():
                # Backup the existing config
                with open(default_config, 'r') as f:
                    config_backup = f.read()
                    
            # Replace with custom config
            with open(config_path, 'r') as src, open(default_config, 'w') as dst:
                dst.write(src.read())
            
            logger.info(f"Using custom config from {args.config}")
        
        logger.info("Starting complete resume creation pipeline...")
        
        # Run the integrated pipeline
        success = complete_resume_pipeline()
        
        # Restore the original config if needed
        if config_backup is not None:
            input_dir = Path(__file__).resolve().parents[3] / "input"
            default_config = input_dir / "config.json"
            with open(default_config, 'w') as f:
                f.write(config_backup)
        
        if success:
            logger.info("✅ Resume creation pipeline completed successfully!")
            return 0
        else:
            logger.error("❌ Resume creation pipeline failed.")
            return 1
            
    except Exception as e:
        logger.error(f"Error running resume creation pipeline: {str(e)}")
        return 1

def main():
    """Main entry point for the CLI"""
    args = parse_args()
    
    if args.command == "analyze":
        return analyze_resume(args)
    elif args.command == "template":
        return manage_templates(args)
    elif args.command == "extract":
        return extract_data(args)
    elif args.command == "generate":
        return generate_resume(args)
    elif args.command == "keywords":
        return extract_keywords(args)
    elif args.command == "full-pipeline":
        return run_full_pipeline(args)
    else:
        logger.error(f"Unknown command: {args.command}")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 