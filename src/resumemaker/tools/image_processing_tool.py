from typing import Type, Dict, Any
from crewai.tools import BaseTool
from pydantic import BaseModel, Field
from pathlib import Path
from PIL import Image
import io
import logging
import base64

logger = logging.getLogger(__name__)

class ImageProcessingInput(BaseModel):
    """Input schema for ImageProcessingTool."""
    image_path: str = Field(..., description="Path to the image file to process")
    target_size: tuple = Field((200, 200), description="Desired dimensions (width, height) for the output image")
    crop_to_face: bool = Field(True, description="Whether to attempt face detection and cropping")

class ImageProcessingTool(BaseTool):
    name: str = "ImageProcessing"
    description: str = "Processes images for optimal resume integration"
    args_schema: Type[BaseModel] = ImageProcessingInput

    def _run(self, image_path: str, target_size: tuple = (200, 200), crop_to_face: bool = True) -> Dict[str, Any]:
        """
        Process an image for resume use
        """
        try:
            # Convert string path to Path object if needed
            if isinstance(image_path, str):
                image_path = Path(image_path)
            
            if not image_path.exists():
                return {
                    "success": False,
                    "error": f"Image not found at path: {image_path}"
                }
                
            # Open and process the image
            with Image.open(image_path) as img:
                # Convert to RGB if needed
                if img.mode != 'RGB':
                    img = img.convert('RGB')
                
                # Implement face detection if crop_to_face is True
                # For simplicity, we'll just resize here
                # In a production system, you might use a library like OpenCV or a face detection API
                
                # Resize the image
                img = img.resize(target_size, Image.LANCZOS)
                
                # Save the processed image
                output_path = image_path.parent / f"processed_{image_path.name}"
                img.save(output_path, format="JPEG", quality=90)
                
                # Create a base64 representation for embedding
                buffered = io.BytesIO()
                img.save(buffered, format="JPEG")
                img_base64 = base64.b64encode(buffered.getvalue()).decode('utf-8')
                
                return {
                    "success": True,
                    "processed_path": str(output_path),
                    "original_path": str(image_path),
                    "dimensions": img.size,
                    "format": "JPEG",
                    "base64": img_base64
                }
                
        except Exception as e:
            logger.error(f"Error processing image: {str(e)}")
            return {
                "success": False,
                "error": f"Failed to process image: {str(e)}"
            }