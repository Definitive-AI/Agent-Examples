import uuid
from langchain_community.document_loaders.web_base import WebBaseLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.tools.retriever import create_retriever_tool
from langchain.vectorstores.chroma import Chroma
import chromadb
from langchain.embeddings.huggingface import HuggingFaceEmbeddings
import sys
__import__('pysqlite3')
sys.modules["sqlite3"] = sys.modules.pop("pysqlite3")   

modelPath = "thenlper/gte-small" 
model_kwargs = {'device':'cpu','trust_remote_code':'True'}
encode_kwargs = {'normalize_embeddings': True}

# Initialize an instance of HuggingFaceEmbeddings with the specified parameters
embeddings = HuggingFaceEmbeddings(
    model_name=modelPath,     # Provide the pre-trained model's path
    model_kwargs=model_kwargs, # Pass the model configuration options
    encode_kwargs=encode_kwargs # Pass the encoding options
)

chroma_client = chromadb.PersistentClient(path="./chroma_db")

from chromadb.api import AdminAPI, ClientAPI
def collection_exists(client:ClientAPI, collection_name):
    collections = client.list_collections()
    filtered_collection = filter(lambda collection: collection.name == collection_name, collections)
    found = any(filtered_collection)
    return found

def load_documentation(chroma, embeddings, collection_name, urls):
    if not collection_exists(chroma, collection_name):
        loader = WebBaseLoader(urls)
        data = loader.load()

        documents = RecursiveCharacterTextSplitter(
            chunk_size=1000, chunk_overlap=200
        ).split_documents(data)

        collection = chroma.create_collection(collection_name)
        for doc in documents:
            emb = embeddings.embed_documents([doc.page_content])
            collection.add(
                ids=[str(uuid.uuid1())], embeddings=emb, metadatas=doc.metadata, documents=doc.page_content
            )

# Load SEO best practices documentation
seo_urls = [
    "https://moz.com/beginners-guide-to-seo", 
    "https://backlinko.com/hub/seo/seo-techniques",
    "https://ahrefs.com/blog/seo-best-practices/",
    "https://www.semrush.com/blog/seo-best-practices/",
    "https://neilpatel.com/blog/seo-best-practices/",
    "https://www.searchenginejournal.com/seo-guide/",
    "https://www.searchenginewatch.com/category/seo/"
]
load_documentation(chroma_client, embeddings, "seo_best_practices", seo_urls)

seo_best_practices_retriever = create_retriever_tool(
    Chroma(client=chroma_client, collection_name="seo_best_practices", embedding_function=embeddings).as_retriever(),
    "seo_best_practices_search",
    "Search for information about SEO best practices, including keyword research, on-page optimization, meta tags, header tags, and other relevant factors. Use this tool to optimize articles for search engines according to the company's SEO standards."
)

# Load Universal Orchestrator documentation
uo_urls = ["https://wonderbotz.com/intelligent-automation-technologies/aria-coe"]
load_documentation(chroma_client, embeddings, "universal_orchestrator", uo_urls)

universal_orchestrator_retriever = create_retriever_tool(
    Chroma(client=chroma_client, collection_name="universal_orchestrator", embedding_function=embeddings).as_retriever(),
    "universal_orchestrator_search",
    "Search for information about the Universal Orchestrator product. For any questions related to Universal Orchestrator features, benefits or use cases, use this tool!"
)

# Load Wonderbotz articles for style and voice reference
wonderbotz_urls = ["https://wonderbotz.com/articles/"]
load_documentation(chroma_client, embeddings, "wonderbotz_articles", wonderbotz_urls)

wonderbotz_articles_retriever = create_retriever_tool(
    Chroma(client=chroma_client, collection_name="wonderbotz_articles", embedding_function=embeddings).as_retriever(),
    "wonderbotz_articles_search",
    "Search Wonderbotz articles for style and voice reference. Use this tool to find examples that maintain consistency with the company's desired tone and structure when generating new content."
)

# Load RPA Cloud Migration article
rpa_urls = ["https://wonderbotz.com/articles/rpa-cloud-migration-why-secure-cloud-is-the-critical-path-to-ai-readiness/"]
load_documentation(chroma_client, embeddings, "rpa_cloud_migration", rpa_urls)

rpa_cloud_migration_retriever = create_retriever_tool(
    Chroma(client=chroma_client, collection_name="rpa_cloud_migration", embedding_function=embeddings).as_retriever(),
    "rpa_cloud_migration_search",
    "Search the RPA Cloud Migration article for information about why secure cloud is critical for AI readiness in RPA. Use this tool to answer questions specifically related to RPA and cloud migration."
)

# Load ChatGPT and AI in Automation Technology article
chatgpt_urls = ["https://wonderbotz.com/articles/exciting-new-uses-for-chatgpt-and-ai-in-automation-technology/"]
load_documentation(chroma_client, embeddings, "chatgpt_automation", chatgpt_urls)

chatgpt_automation_retriever = create_retriever_tool(
    Chroma(client=chroma_client, collection_name="chatgpt_automation", embedding_function=embeddings).as_retriever(),
    "chatgpt_automation_search",
    "Search for information in the Wonderbotz article about exciting new uses for ChatGPT and AI in automation technology. For any questions related to the content of this specific article, use this tool!"
)
