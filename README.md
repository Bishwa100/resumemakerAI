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
GEMINI_API_KEY=your_gemini_api_key_here
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

1. Fill in your details in `crews/poem_crew/candidate_profile.json`
2. Add the job description in `crews/poem_crew/job_description.json`
3. (Optional) Add your professional photo as `crews/poem_crew/profile_photo.jpg`
4. Run the resume maker:

   Local:
   ```bash
   python -m resumemaker.crews.poem_crew.resume_making_crew
   ```
   
   Docker:
   ```bash
   docker-compose run resumemaker
   # Or with Makefile
   make run
   ```

## Output

The tool will generate output files in the `output` directory:
- An ATS-optimized LaTeX resume
- A compiled PDF version of your resume
- Keyword analysis and optimization suggestions

## Features

- ATS optimization
- Keyword analysis
- Professional LaTeX formatting
- Profile photo integration (optional)
- Modern and clean design
- Multiple resume sections support
