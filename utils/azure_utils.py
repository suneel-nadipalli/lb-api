import os, io, sys

sys.path.append("..")

from dotenv import load_dotenv

load_dotenv()

from azure.storage.blob import BlobServiceClient

from PyPDF2 import PdfReader

from langchain.docstore.document import Document
from langchain.vectorstores import FAISS
from langchain.text_splitter import CharacterTextSplitter
from langchain.embeddings import OpenAIEmbeddings

# Step 1: Load PDF documents from Azure Blob Storage
def load_documents_from_azure(blob_service_client, container_name):
    container_client = blob_service_client.get_container_client(container_name)
    blob_list = container_client.list_blobs()

    documents = []
    for blob in blob_list:
        # Download the blob content (PDF file)
        blob_client = container_client.get_blob_client(blob.name)
        pdf_content = blob_client.download_blob().readall()

        # Parse the PDF content
        pdf_reader = PdfReader(io.BytesIO(pdf_content))
        text = ""
        for page in pdf_reader.pages:
            text += page.extract_text()

        # Create a Document object for LangChain
        documents.append(Document(page_content=text, metadata={"source": blob.name}))

    return documents

# Step 2: Create embeddings and vector store
def create_vector_store(documents):
    embeddings = OpenAIEmbeddings()
    text_splitter = CharacterTextSplitter(chunk_size=1000, chunk_overlap=0)
    split_documents = text_splitter.split_documents(documents)
    vector_store = FAISS.from_documents(split_documents, embeddings)
    return vector_store

def prep_docs():
    connection_string = os.getenv('AZURE_BS_URL')
    blob_service_client = BlobServiceClient.from_connection_string(connection_string)

    # Specify the container name where your PDFs are stored
    container_name = "rag-data-v1"

    documents = load_documents_from_azure(blob_service_client, container_name)

    return documents

def prep_vs():
    documents = prep_docs()
    vector_store = create_vector_store(documents)
    return vector_store