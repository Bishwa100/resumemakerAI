# Project Structure

```
resumemaker/
│
├── .git/                     # Git repository
├── .gitignore                # Git ignore file
├── .dockerignore             # Docker ignore file
├── .venv/                    # Python virtual environment
│
├── input/                    # Input files directory
│   ├── README.md             # Instructions for input directory
│   ├── config.json           # Configuration for the application
│   ├── bishwanath.jpg        # Sample profile image
│   ├── candidate_profile.json # Sample candidate profile
│   └── job_description.txt.example # Example job description
│
├── output/                   # Generated outputs directory
│   └── README.md             # Instructions for output directory
│
├── src/                      # Source code
│   └── resumemaker/          # Main package
│       ├── __init__.py       # Package initialization
│       ├── main.py           # Main entry point
│       ├── cli.py            # Command-line interface
│       │
│       ├── crews/            # AI crews (agent orchestration)
│       │   ├── __init__.py
│       │   └── poem_crew/    # POEM (Process-Oriented Extraction Method) crew
│       │       ├── __init__.py
│       │       ├── resume_making_crew.py  # Resume creation crew
│       │       ├── data_extraction_crew.py # Data extraction crew
│       │       ├── data_extraction_output.py # Output schema
│       │       ├── config/   # Configuration files
│       │       │   ├── data_extraction_agents.yaml
│       │       │   ├── data_extraction_tasks.yaml
│       │       │   ├── resume_creation_agents.yaml
│       │       │   └── resume_creation_tasks.yaml
│       │       └── generated_resumes/ # Temporary storage for generated resumes
│       │
│       ├── tools/            # AI tools for specific tasks
│       │   ├── __init__.py
│       │   ├── custom_tool.py # Compatibility layer for old imports
│       │   ├── google_search_tool.py # Google search tool
│       │   ├── opensource_rag_tool.py # Open source RAG tool (replacement for MistralRAG)
│       │   ├── pdf_analyzer_tool.py # PDF analysis tool
│       │   ├── mistral_pdf_upload_tool.py # Mistral PDF upload tool
│       │   ├── githubanalyzer_tool.py # GitHub repository analyzer
│       │   ├── latex_generator_tool.py # LaTeX document generator
│       │   ├── pdfGenarator_tool.py # PDF generation tool
│       │   ├── image_processing_tool.py # Image processing tool
│       │   ├── linkedin_extractor_tool.py # LinkedIn profile extractor
│       │   ├── job_keyword_extractor_tool.py # Job keyword extraction tool
│       │   ├── resume_analyzer_tool.py # Resume analysis tool
│       │   └── template_manager_tool.py # Template management tool
│       │
│       └── utils/            # Utility functions
│           ├── __init__.py
│           └── api_check.py  # API key validation
│
├── docker-compose.yml        # Docker Compose configuration
├── Dockerfile                # Docker container definition
├── Makefile                  # Build automation
├── pyproject.toml            # Python project metadata
├── requirements.txt          # Python dependencies
├── resumemaker.ps1           # Windows launcher script
├── resumemaker.sh            # Unix launcher script
├── README.md                 # Project documentation
├── PROJECT_STRUCTURE.md      # This file
└── uv.lock                   # Lock file for dependencies
```

## Directory Descriptions

### Input Directory
Contains all input files needed for the application including:
- User config
- Profile images
- Resume data
- Job descriptions

### Output Directory
Contains all generated outputs:
- Final resumes
- Analysis reports
- Extracted profiles

### Source Code
Organized into packages:

#### Crews
AI agent orchestration groups that coordinate complex tasks, organized with:
- Agent definitions
- Task definitions
- YAML configuration files

#### Tools
Individual AI-powered tools that perform specific functions:
- Search tools (Google, LinkedIn, GitHub)
- Analysis tools (PDF, Resume, Job)
- Generation tools (LaTeX, PDF)
- RAG tools (Open Source implementation)

#### Utils
Helper utilities used across the application.

## Architecture Overview

The application follows a modular architecture:

1. **CLI Layer** - User interface through command line
2. **Crew Layer** - Orchestrates complex workflows using multiple agents
3. **Tools Layer** - Individual capabilities provided to agents
4. **Utility Layer** - Shared functionality across the application

Each layer is designed to be independent and extensible, allowing for easy addition of new features. 