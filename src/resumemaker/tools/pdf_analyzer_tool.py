from typing import Type
from crewai.tools import BaseTool
from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter

class PDFAnalyzerTool(BaseTool):
    name: str = "PDFAnalyzer" 
    description: str = "Extracts and processes text from scientific PDF papers."  

    def _run(self, pdf_path: str) -> str:
        try:
            loader = PyPDFLoader(pdf_path)
            documents = loader.load()
            text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
            docs = text_splitter.split_documents(documents)
            return "\n\n".join([doc.page_content for doc in docs])
        except Exception as e:
            return f"Error processing PDF: {str(e)}" 