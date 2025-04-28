# ATS-Friendly Resume Maker

This tool helps create beautiful and ATS-friendly resumes tailored to specific job descriptions.

## Setup

### Option 1: Local Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Set up environment variables:
Create a `.env` file in the root directory with:
```
OPENROUTER_API_KEY=your_openrouter_api_key_here
```

### Option 2: Using Docker (Recommended)

1. Install [Docker](https://docs.docker.com/get-docker/) and [Docker Compose](https://docs.docker.com/compose/install/)

2. Set up environment variables:
   - Copy `env.example` to `.env` and fill in your API keys
   ```bash
   cp env.example .env
   # Edit .env with your favorite editor
   ```

3. Use the provided Makefile commands:
   ```bash
   # Build and run
   make

   # Only build the Docker image
   make build

   # Run in detached mode
   make run-detached

   # View logs
   make logs

   # Stop containers
   make stop

   # Clean up everything
   make clean
   ```

## Usage

### Prepare Input Files

1. Place your input files in the `input` directory:
   - `resume.pdf` - Your resume in PDF format
   - `job_description.txt` - The job description

2. Configure your profile information in `input/config.json`:
   ```json
   {
     "linkedin_url": "https://www.linkedin.com/in/your-profile",
     "github_url": "your-github-username",
     "resume_file": "resume.pdf",
     "job_description_file": "job_description.txt"
   }
   ```

### Command Line Interface

The application now includes a powerful CLI with several useful commands:

#### Windows:
```powershell
.\resumemaker.ps1 <command> [options]
```

#### Linux/MacOS:
```bash
./resumemaker.sh <command> [options]
```

#### Available Commands:

1. **analyze** - Analyze a resume for ATS compatibility
   ```
   ./resumemaker.sh analyze --resume input/resume.pdf --job input/job_description.txt
   ```

2. **keywords** - Extract key skills and requirements from a job description
   ```
   ./resumemaker.sh keywords --job input/job_description.txt [--resume input/resume.pdf]
   ```

3. **template** - Manage resume templates
   ```
   ./resumemaker.sh template list --type latex
   ./resumemaker.sh template get --name classic --type latex
   ```

4. **extract** - Extract structured data from resume and job description
   ```
   ./resumemaker.sh extract --resume input/resume.pdf --job input/job_description.txt
   ```

5. **generate** - Generate an optimized resume (coming soon)
   ```
   ./resumemaker.sh generate --resume input/resume.pdf --job input/job_description.txt --template modern
   ```

### Using Docker:

```bash
docker-compose up
# Or with Makefile
make run
```

## Output

The tool will generate output files in the `output` directory:
- `candidate_profile.json` - Structured profile data with skills, experience, and job matches
- ATS-optimized LaTeX resume
- A compiled PDF version of your resume

## Features

- ATS optimization
- Keyword analysis
- Professional LaTeX formatting
- GitHub project analysis
- LinkedIn profile integration
- Job requirements matching
- Tailored resume generation
- Powered by OpenRouter API with high-quality AI models

## Advanced Tools

The application includes several specialized tools:

1. **Resume Analyzer Tool** - Assesses ATS compatibility and provides suggestions
2. **Job Keyword Extractor** - Extracts important skills and requirements from job descriptions
3. **Template Manager** - Manages different resume templates and formats
4. **PDF Generator** - Creates professional PDF resumes

## Project Structure

The project is organized in a modular structure with clear separation of concerns. See [PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md) for a detailed breakdown of the project structure.

### Key Components

- **AI Crews**: Orchestration of AI agents for complex tasks
- **AI Tools**: Individual capabilities like search, analysis, and generation
- **Open Source RAG**: Retrieval-Augmented Generation using HuggingFace models and FAISS
- **LaTeX Generation**: High-quality resume generation with LaTeX

### Tools Overview

The application uses several tools to accomplish its tasks:

- **OpenSourceRAGTool**: Retrieval-Augmented Generation using HuggingFace embeddings and models
- **GoogleSearchTool**: Searches Google for relevant information
- **PDFAnalyzerTool**: Extracts text from PDF resumes
- **GitHubExtractorTool**: Analyzes GitHub repositories for skills and projects
- **LinkedInExtractorTool**: Extracts professional details from LinkedIn profiles
