from langchain_community.document_loaders.web_base import WebBaseLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.tools.retriever import create_retriever_tool
from langchain.vectorstores.chroma import Chroma
import chromadb
from langchain.embeddings.huggingface import HuggingFaceEmbeddings

modelPath = "BAAI/bge-small-en-v1.5" 
model_kwargs = {'device':'cpu','trust_remote_code':'True'}
encode_kwargs = {'normalize_embeddings': True}

embeddings = HuggingFaceEmbeddings(
    model_name=modelPath,    
    model_kwargs=model_kwargs,
    encode_kwargs=encode_kwargs
)

chroma = chromadb.PersistentClient(path="./chroma_db")

from chromadb.api import AdminAPI, ClientAPI
def collection_exists(client:ClientAPI, collection_name):
    collections = client.list_collections()
    filtered_collection = filter(lambda collection: collection.name == collection_name, collections)
    found = any(filtered_collection)
    return found

from langchain_community.document_loaders.web_base import WebBaseLoader
from langchain.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.tools.retriever import create_retriever_tool
from langchain.vectorstores.chroma import Chroma
import chromadb
import uuid

chroma = chromadb.PersistentClient(path="./chroma_db")

def load_process_docs(chroma, embeddings, location):
    if not collection_exists(chroma, "process_docs"):
        try:
            loader = PyPDFLoader(location)
            data = loader.load()
        except Exception as e:
            print(f"Error loading document from {location}: {str(e)}")
            return

        documents = RecursiveCharacterTextSplitter(
            chunk_size=1000, chunk_overlap=200
        ).split_documents(data)

        collection = chroma.create_collection("process_docs")
        for doc in documents:
            emb = embeddings.embed_documents([doc.page_content])
            collection.add(
                ids=[str(uuid.uuid1())], embeddings=emb, metadatas=doc.metadata, documents=doc.page_content
            )

load_process_docs(chroma, embeddings, "[Insert location or URL of the Process Description PDF]")

process_docs_retriever = create_retriever_tool(
    Chroma(chroma, collection_name="process_docs").as_retriever(),
    "process_docs_search",
    "Search for information in the Process Description and High-Level Steps document. The agent requires access to this document to ensure proper storage and reporting of extracted email data, including steps for viewing and saving encrypted or protected emails in Outlook and forwarding screenshots for permanent record-keeping."
)
