import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Standard tools that should always be available
from resumemaker.tools.custom_tool import PDFAnalyzerTool
from resumemaker.tools.pdf_analyzer_tool import PDFAnalyzerTool
from resumemaker.tools.opensource_rag_tool import OpenSourceRAGTool

# Tools that may have additional dependencies - try to import them safely
tools_list = ["PDFAnalyzerTool", "OpenSourceRAGTool"]

try:
    from resumemaker.tools.linkedin_extractor_tool import LinkedInExtractorTool
    tools_list.append("LinkedInExtractorTool")
except ImportError as e:
    logger.warning(f"Could not import LinkedInExtractorTool: {str(e)}")

try:
    from resumemaker.tools.githubanalyzer_tool import GitHubFetchTool
    tools_list.append("GitHubFetchTool")
except ImportError as e:
    logger.warning(f"Could not import GitHubFetchTool: {str(e)}")

try:
    from resumemaker.tools.mistral_pdf_upload_tool import MistralPDFUploadTool
    tools_list.append("MistralPDFUploadTool")
except ImportError as e:
    logger.warning(f"Could not import MistralPDFUploadTool: {str(e)}")

try:
    from resumemaker.tools.image_processing_tool import ImageProcessingTool
    tools_list.append("ImageProcessingTool")
except ImportError as e:
    logger.warning(f"Could not import ImageProcessingTool: {str(e)}")

try:
    from resumemaker.tools.latex_generator_tool import LaTeXGeneratorTool
    tools_list.append("LaTeXGeneratorTool")
except ImportError as e:
    logger.warning(f"Could not import LaTeXGeneratorTool: {str(e)}")

try:
    from resumemaker.tools.job_keyword_extractor_tool import JobKeywordExtractorTool
    tools_list.append("JobKeywordExtractorTool")
except ImportError as e:
    logger.warning(f"Could not import JobKeywordExtractorTool: {str(e)}")

try:
    from resumemaker.tools.resume_analyzer_tool import ResumeAnalyzerTool
    tools_list.append("ResumeAnalyzerTool")
except ImportError as e:
    logger.warning(f"Could not import ResumeAnalyzerTool: {str(e)}")

try:
    from resumemaker.tools.template_manager_tool import TemplateManagerTool
    tools_list.append("TemplateManagerTool")
except ImportError as e:
    logger.warning(f"Could not import TemplateManagerTool: {str(e)}")

__all__ = tools_list