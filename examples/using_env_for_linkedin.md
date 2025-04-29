# Using Environment Variables for LinkedIn Authentication

This guide explains how to use environment variables for authenticating with LinkedIn when using the LinkedIn Extractor tool.

## Step 1: Create a .env file

Create a file named `.env` in the root directory of your project with the following content:

```
LINKEDIN_EMAIL=your_linkedin_email@example.com
LINKEDIN_PASSWORD=your_linkedin_password
```

Replace the values with your actual LinkedIn credentials.

## Step 2: Using the Environment Variables

When using the LinkedIn Extractor tool, set the `use_env` parameter to `True`:

```python
from resumemaker.tools.linkedin_extractor_tool import LinkedInExtractorTool

extractor = LinkedInExtractorTool()
result = extractor._run(
    profile_url="https://www.linkedin.com/in/username/",
    use_env=True,  # This tells the tool to use credentials from .env
    screenshot=True
)
```

## Example Code

```python
import os
from pathlib import Path
from resumemaker.tools.linkedin_extractor_tool import LinkedInExtractorTool

# Create output directory
output_dir = Path("output")
output_dir.mkdir(parents=True, exist_ok=True)

# Initialize the LinkedIn extractor
extractor = LinkedInExtractorTool()

# Replace with the LinkedIn profile URL you want to extract
linkedin_profile_url = "https://www.linkedin.com/in/username/"

# Extract the profile using environment variables for authentication
result = extractor._run(
    profile_url=linkedin_profile_url,
    use_env=True,  # Use credentials from .env file
    screenshot=True,  # Take a screenshot of the profile
    output_path=str(output_dir)  # Save data to the output directory
)

if result["success"]:
    print(f"Successfully extracted profile data")
    print(f"Data saved to: {result['data_path']}")
else:
    print(f"Failed to extract profile: {result['error']}")
```

## Security Best Practices

1. **Never commit your .env file to version control**. Make sure to add `.env` to your `.gitignore` file.

2. **Keep your credentials secure**. Only share your LinkedIn credentials with trusted applications and tools.

3. **Create a dedicated account** for automation if you're using this tool extensively, to avoid potential issues with your personal LinkedIn account.

## Troubleshooting

If you encounter issues with authentication:

1. Make sure your .env file is in the correct location (project root directory)
2. Verify that your credentials are correct
3. Check that you have the latest version of the `python-dotenv` package installed
4. LinkedIn may use CAPTCHA or other security measures if it detects unusual login patterns 