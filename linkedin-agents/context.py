from langchain_community.document_loaders.web_base import WebBaseLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.tools.retriever import create_retriever_tool
from langchain.vectorstores.chroma import Chroma
import chromadb
from langchain.embeddings.huggingface import HuggingFaceEmbeddings
import uuid

chroma = chromadb.PersistentClient(path="./chroma_db")

from chromadb.api import AdminAPI, ClientAPI
def collection_exists(client:ClientAPI, collection_name):
    collections = client.list_collections()
    filtered_collection = filter(lambda collection: collection.name == collection_name, collections)
    found = any(filtered_collection)
    return found

embeddings = HuggingFaceEmbeddings()

def load_redstone_security_sources(chroma, embeddings):
    urls = [
        "https://twitter.com/TrendMicro",
        "https://www.knowbe4.com/",
        "https://twitter.com/Fortinet", 
        "https://twitter.com/SocEngineerInc",
        "https://twitter.com/mandiant"
    ]
    
    if not collection_exists(chroma, "redstone_security_sources"):
        loader = WebBaseLoader(urls)
        data = loader.load()

        documents = RecursiveCharacterTextSplitter(
            chunk_size=1000, chunk_overlap=200
        ).split_documents(data)

        collection = chroma.create_collection("redstone_security_sources")
        for doc in documents:
            emb = embeddings.embed_documents([doc.page_content])
            collection.add(
                ids=[str(uuid.uuid1())], embeddings=emb, metadatas=doc.metadata, documents=doc.page_content
            )

load_redstone_security_sources(chroma, embeddings)

redstone_security_sources_retriever = create_retriever_tool(
    Chroma(client=chroma, collection_name="redstone_security_sources", embedding_function=embeddings).as_retriever(),
    "redstone_security_sources",
    "Search for companies Redstone Security follows for post sources. For any questions about the list of companies, you must use this tool!"
)
