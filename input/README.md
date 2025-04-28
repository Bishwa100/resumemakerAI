# Input Directory

Place the following files in this directory:

1. `resume.pdf` - Your resume in PDF format
2. `job_description.txt` - The job description text

## Configuration

Update the settings in the `config.json` file:

```json
{
  "linkedin_url": "https://www.linkedin.com/in/your-profile",
  "github_url": "your-github-username",
  "resume_file": "resume.pdf",
  "job_description_file": "job_description.txt",
  "model_settings": {
    "provider": "openrouter",
    "model": "anthropic/claude-3-opus",
    "temperature": 0.7
  }
}
```

### Available Models

You can change the model in the config file. Some recommended options:

- `anthropic/claude-3-opus` - Highest quality, best for complex analysis
- `anthropic/claude-3-sonnet` - Good balance of quality and speed
- `openai/gpt-4o` - Good alternative option
- `meta-llama/llama-3-70b-instruct` - Open source alternative 