import os
import sys
import logging
from pathlib import Path
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

def check_api_keys():
    """Check if necessary API keys are present"""
    # Load environment variables
    load_dotenv()
    
    # Check for OpenRouter API key
    openrouter_api_key = os.getenv('OPENROUTER_API_KEY')
    if not openrouter_api_key:
        logger.error("ERROR: OPENROUTER_API_KEY environment variable is not set.")
        logger.error("Please create a .env file with your OpenRouter API key or set the environment variable.")
        logger.error("You can get an API key from https://openrouter.ai/")
        return False
    
    return True

if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    if not check_api_keys():
        sys.exit(1)
    
    logger.info("API key check passed successfully.")
    sys.exit(0) 