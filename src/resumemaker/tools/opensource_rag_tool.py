from typing import Type, Dict, Any
import os
from pydantic import BaseModel, Field
from crewai.tools import BaseTool
from dotenv import load_dotenv
from langchain_community.document_loaders import TextLoader
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_core.prompts import ChatPromptTemplate
from langchain.chains import create_retrieval_chain
from langchain_community.llms import HuggingFaceEndpoint

load_dotenv()

class OpenSourceRAGInput(BaseModel):
    """Input schema for OpenSourceRAGTool."""
    file_path: str = Field(..., description="Path to the text file containing the content.")
    query: str = Field(..., description="The question to ask based on the document.")


class OpenSourceRAGTool(BaseTool):
    name: str = "OpenSourceRAGTool"
    description: str = "Retrieves and generates answers using open-source models and FAISS vector storage."
    args_schema: Type[BaseModel] = OpenSourceRAGInput

    def _run(self, file_path: str, query: str) -> Dict[str, Any]:
        """Runs the retrieval-augmented generation process to answer the query."""
        HF_TOKEN = os.getenv("HUGGING_FACE_TOKEN")

        if not HF_TOKEN:
            return {"error": "Missing HUGGING_FACE_TOKEN in environment variables."}

        if not os.path.exists(file_path):
            return {"error": f"File '{file_path}' not found."}

        try:
            # Load data from the text file
            loader = TextLoader(file_path)
            docs = loader.load()

            # Split text into chunks
            text_splitter = RecursiveCharacterTextSplitter()
            documents = text_splitter.split_documents(docs)

            # Define the embedding model - uses HuggingFace instead of Mistral
            embeddings = HuggingFaceEmbeddings(
                model_name="sentence-transformers/all-MiniLM-L6-v2", 
                huggingfacehub_api_token=HF_TOKEN
            )

            # Create the vector store
            vector = FAISS.from_documents(documents, embeddings)

            # Define a retriever interface
            retriever = vector.as_retriever()

            # Define LLM - uses HuggingFace instead of Mistral
            model = HuggingFaceEndpoint(
                repo_id="google/flan-t5-xxl",
                huggingfacehub_api_token=HF_TOKEN,
            )

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