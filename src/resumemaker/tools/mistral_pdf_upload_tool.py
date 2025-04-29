from typing import Type, Dict, Any
import os
import logging
import requests
from pydantic import BaseModel, Field
from crewai.tools import BaseTool
from dotenv import load_dotenv

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

load_dotenv()

# Try to import Mistral, but provide graceful fallback if not available
MISTRAL_AVAILABLE = False
try:
    from mistralai import Mistral
    MISTRAL_AVAILABLE = True
except ImportError:
    logger.warning("mistralai package not found. MistralPDFUploadTool will be available but non-functional.")
    logger.warning("Install with: pip install mistralai")

class PDFUploadInput(BaseModel):
    """Input schema for MistralPDFUploadTool."""
    file_path: str = Field(..., description="Path to the PDF file to upload.")


class MistralPDFUploadTool(BaseTool):
    name: str = "MistralPDFUpload"
    description: str = "Uploads a PDF file to Mistral for OCR processing."
    args_schema: Type[BaseModel] = PDFUploadInput

    def _run(self, file_path: str) -> Dict[str, Any]:
        """Uploads the PDF file to Mistral for OCR processing."""
        if not MISTRAL_AVAILABLE:
            return {
                "error": "mistralai package not installed. Install with: pip install mistralai",
                "fallback": "Using local PDF processing instead."
            }
            
        API_KEY = os.getenv("MISTRAL_API_KEY")

        if not API_KEY:
            return {"error": "Missing MISTRAL_API_KEY in environment variables."}

        if not os.path.exists(file_path):
            return {"error": f"File '{file_path}' not found."}

        try:
            client = Mistral(api_key=API_KEY)

            with open(file_path, "rb") as file:
                uploaded_pdf = client.files.upload(
                    file={"file_name": os.path.basename(file_path), "content": file},
                    purpose="ocr"
                )

            return {"status": "success", "file_id": uploaded_pdf.id}

        except requests.exceptions.RequestException as e:
            return {"error": f"Request error: {str(e)}"}

        except Exception as e:
            return {"error": f"Unexpected error: {str(e)}"} 