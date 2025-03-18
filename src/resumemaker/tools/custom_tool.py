from typing import Type

from mistralai import Mistral
from crewai.tools import BaseTool
from pydantic import BaseModel, Field
import os
import requests
from typing import Dict, Any
from dotenv import load_dotenv
from langchain_community.document_loaders import TextLoader
from langchain_mistralai.chat_models import ChatMistralAI
from langchain_mistralai.embeddings import MistralAIEmbeddings
from langchain_community.vectorstores import FAISS
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_core.prompts import ChatPromptTemplate
from langchain.chains import create_retrieval_chain
from langchain_community.document_loaders import PyPDFLoader


load_dotenv()

class GoogleSearchInput(BaseModel):
    """Input schema for GoogleSearchTool."""
    query: str = Field(..., description="Search query for Google.")

class GoogleSearchTool(BaseTool):
    name: str = "GoogleSearch"
    description: str = "Searches Google and returns the top 5 results."
    args_schema: Type[BaseModel] = GoogleSearchInput

    def _run(self, query: str) -> Dict[str, Any]:
        """Performs a Google search using the Custom Search API."""
        API_KEY = os.getenv("GOOGLE_API_KEY")
        CX = os.getenv("GOOGLE_CX")

        if not API_KEY or not CX:
            return {"error": "Missing GOOGLE_API_KEY or GOOGLE_CX in environment variables."}

        url = f"https://www.googleapis.com/customsearch/v1?q={query}&key={API_KEY}&cx={CX}"

        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            data = response.json()

            if "items" not in data:
                return {"error": "No search results found."}

            results = [
                {
                    "title": item.get("title", "No Title"),
                    "link": item.get("link", "No Link"),
                    "snippet": item.get("snippet", "No Description"),
                }
                for item in data["items"][:5]  # Get top 5 results
            ]

            return {"results": results}
        
        except requests.exceptions.RequestException as e:
            return {"error": str(e)}


class PDFUploadInput(BaseModel):
    """Input schema for MistralPDFUploadTool."""
    file_path: str = Field(..., description="Path to the PDF file to upload.")


class MistralPDFUploadTool(BaseTool):
    name: str = "MistralPDFUpload"
    description: str = "Uploads a PDF file to Mistral for OCR processing."
    args_schema: Type[BaseModel] = PDFUploadInput

    def _run(self, file_path: str) -> Dict[str, Any]:
        """Uploads the PDF file to Mistral for OCR processing."""
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



class RAGInput(BaseModel):
    """Input schema for MistralRAGTool."""
    file_path: str = Field(..., description="Path to the text file containing the content.")
    query: str = Field(..., description="The question to ask based on the document.")


class MistralRAGTool(BaseTool):
    name: str = "MistralRAGTool"
    description: str = "Retrieves and generates answers using Mistral AI and FAISS vector storage."
    args_schema: Type[BaseModel] = RAGInput

    def _run(self, file_path: str, query: str) -> Dict[str, Any]:
        """Runs the retrieval-augmented generation process to answer the query."""
        API_KEY = os.getenv("MISTRAL_API_KEY")
        os.environ["HF_TOKEN"] = os.getenv("HUGGING_FACE")

        if not API_KEY:
            return {"error": "Missing MISTRAL_API_KEY in environment variables."}

        if not os.path.exists(file_path):
            return {"error": f"File '{file_path}' not found."}

        try:
            # Load data from the text file
            loader = TextLoader(file_path)
            docs = loader.load()

            # Split text into chunks
            text_splitter = RecursiveCharacterTextSplitter()
            documents = text_splitter.split_documents(docs)

            # Define the embedding model
            embeddings = MistralAIEmbeddings(model="mistral-embed", mistral_api_key=API_KEY)

            # Create the vector store
            vector = FAISS.from_documents(documents, embeddings)

            # Define a retriever interface
            retriever = vector.as_retriever()

            # Define LLM
            model = ChatMistralAI(mistral_api_key=API_KEY)

            # Define prompt template
            prompt = ChatPromptTemplate.from_template("""
            Answer the following question based only on the provided context:

            <context>
            {context}
            </context>

            Question: {input}""")

            # Create a retrieval chain to answer questions
            document_chain = create_stuff_documents_chain(model, prompt)
            retrieval_chain = create_retrieval_chain(retriever, document_chain)

            response = retrieval_chain.invoke({"input": query})

            return {"answer": response.get("answer", "No answer found.")}

        except Exception as e:
            return {"error": f"Unexpected error: {str(e)}"}
        

class PDFAnalyzerTool(BaseTool):
    name: str = "pdf_analyzer" 
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


