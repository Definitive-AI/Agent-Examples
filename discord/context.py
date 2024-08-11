from langchain_community.document_loaders.web_base import WebBaseLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.tools.retriever import create_retriever_tool
from langchain.vectorstores.chroma import Chroma
import chromadb
from langchain_community.embeddings import HuggingFaceEmbeddings

modelPath = "BAAI/bge-small-en-v1.5" 
model_kwargs = {'device':'cpu','trust_remote_code':'True'}
encode_kwargs = {'normalize_embeddings': True}

# Initialize an instance of HuggingFaceEmbeddings with the specified parameters
embeddings = HuggingFaceEmbeddings(
    model_name=modelPath,     # Provide the pre-trained model's path
    model_kwargs=model_kwargs, # Pass the model configuration options
    encode_kwargs=encode_kwargs # Pass the encoding options
)

chroma = chromadb.PersistentClient(path="./chroma_db")

from chromadb.api import AdminAPI, ClientAPI
def collection_exists(client:ClientAPI, collection_name):
    collections = client.list_collections()
    filtered_collection = filter(lambda collection: collection.name == collection_name, collections)
    found = any(filtered_collection)
    return found

from langchain_community.document_loaders import WebBaseLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.tools.retriever import create_retriever_tool
from langchain.vectorstores.chroma import Chroma
import chromadb
from langchain_community.embeddings import HuggingFaceEmbeddings
import uuid
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

chroma = chromadb.PersistentClient(path="./chroma_db")
embeddings = HuggingFaceEmbeddings()

def collection_exists(client, collection_name):
    collections = client.list_collections()
    return any(collection.name == collection_name for collection in collections)

def load_documentation(chroma, embeddings, urls, collection_name):
    if not collection_exists(chroma, collection_name):
        try:
            logger.info(f"Loading documents for {collection_name}")
            loader = WebBaseLoader(urls)
            data = loader.load()

            text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=1000, chunk_overlap=200
            )
            documents = text_splitter.split_documents(data)

            collection = chroma.create_collection(collection_name)
            for doc in documents:
                emb = embeddings.embed_documents([doc.page_content])
                collection.add(
                    ids=[str(uuid.uuid4())],
                    embeddings=emb,
                    metadatas=[doc.metadata],
                    documents=[doc.page_content]
                )
            logger.info(f"Successfully loaded {len(documents)} documents into {collection_name}")
        except Exception as e:
            logger.error(f"Error loading documents: {str(e)}")
    else:
        logger.info(f"Collection {collection_name} already exists. Skipping document loading.")

def create_tool(collection_name, tool_name, tool_description):
    return create_retriever_tool(
        Chroma(client=chroma, collection_name=collection_name, embedding_function=embeddings).as_retriever(),
        tool_name,
        tool_description
    )

# Discord documentation
discord_urls = [
    "https://discord.com/developers/docs/intro",
    "https://github.com/discord/discord-api-docs",
    "https://discord.com/guidelines",
    "https://support.discord.com/hc/en-us/articles/360035969312",
    "https://support.discord.com/hc/en-us/articles/115001987272",
    "https://discord.com/moderation"
]
load_documentation(chroma, embeddings, discord_urls, "discord_docs")

discord_retriever_tool = create_tool(
    "discord_docs",
    "discord_search",
    "Search for information about Discord server monitoring, initial triage, and Discord's API. For any questions about Discord guidelines, moderation, or API, you must use this tool!"
)

# AI Knowledge Base
ai_kb_urls = [
    "https://www.phpkb.com/kb/article/building-a-knowledge-base-with-artificial-intelligence-295.html",
    "https://medium.com/@oalmourad/artificial-intelligence-based-knowledge-management-part-i-state-of-knowledge-management-d25b5efd1a29",
    "https://www.artificialintelligence-news.com/2023/12/05/overcoming-the-last-mile-problem-in-knowledge-management-from-ai-vendors/",
    "https://ieeexplore.ieee.org/document/1281736/",
    "https://www.earley.com/insights/knowledge-managements-rebirth-knowledge-engineering-artificial-intelligence",
    "https://towardsdatascience.com/seat-of-knowledge-ai-systems-with-deeply-structure-knowledge-37f1a5ab4bc5?gi=a6975bda173f"
]
load_documentation(chroma, embeddings, ai_kb_urls, "ai_knowledge_base")

ai_knowledge_base_tool = create_tool(
    "ai_knowledge_base",
    "ai_knowledge_base_search",
    "Search for information about AI-powered knowledge bases, FAQ systems, and documentation integration. Use this tool for questions related to building and managing AI-enhanced knowledge management systems, chatbots for FAQs, and integrating AI with documentation."
)

# Language Model Knowledge
lm_urls = [
    "https://www.topbots.com/choosing-the-right-language-model/",
    "https://www.kdnuggets.com/7-steps-to-mastering-large-language-models-llms",
    "https://www.topbots.com/leading-nlp-language-models-2020/",
    "https://www.borealisai.com/research-blogs/a-high-level-overview-of-large-language-models/",
    "https://www.nvidia.com/en-us/lp/ai-data-science/large-language-models-ebook/",
    "https://www.analyticsvidhya.com/blog/2023/09/cutting-edge-tricks-of-applying-large-language-models/",
    "https://arxiv.org/abs/2307.06435v2"
]
load_documentation(chroma, embeddings, lm_urls, "language_model_knowledge")

language_model_tool = create_tool(
    "language_model_knowledge",
    "language_model_search",
    "Search for information about language models and NLP. For any questions about language models or natural language processing, you must use this tool!"
)

# AI Quality and Sentiment Analysis
ai_quality_urls = [
    "https://blog.isqi.org/10-quality-problems-ai",
    "https://www.jisc.ac.uk/guides/developing-high-quality-question-and-answer-sets-for-chatbots",
    "https://sloanreview.mit.edu/article/the-no-1-question-to-ask-when-evaluating-ai-tools/",
    "https://dzone.com/articles/how-to-test-ai-models-an-introduction-guide-for-qa-1",
    "https://www.thepromptengineer.org/master-the-art-of-prompt-engineering-unlock-the-full-potential-of-your-ai-assistant/",
    "https://www.kdnuggets.com/2021/04/improving-model-performance-through-human-participation.html",
    "https://towardsdatascience.com/text-sentiment-analysis-in-nlp-ce6baba6d466",
    "https://towardsdatascience.com/sentiment-analysis-is-difficult-but-ai-may-have-an-answer-a8c447110357",
    "https://www.kdnuggets.com/2018/08/emotion-sentiment-analysis-practitioners-guide-nlp-5.html",
    "https://towardsdatascience.com/a-guide-to-text-classification-and-sentiment-analysis-2ab021796317",
    "https://dzone.com/articles/what-is-sentiment-analysis-and-how-to-perform-one",
    "https://pub.towardsai.net/sentiment-analysis-opinion-mining-with-python-nlp-tutorial-d1f173ca4e3c",
    "https://www.freecodecamp.org/news/what-is-sentiment-analysis-a-complete-guide-to-for-beginners",
    "https://www.leewayhertz.com/reinforcement-learning-from-human-feedback",
    "https://www.forbes.com/sites/edstacey/2021/04/09/what-humans-can-learn-from-human-in-the-loop-learning/",
    "https://www.unite.ai/what-is-reinforcement-learning-from-human-feedback-rlhf/",
    "https://labelbox.com/blog/using-reinforcement-learning-from-human-feedback-to-fine-tune-large-language-models/",
    "https://www.clarifai.com/blog/closing-the-loop-how-feedback-loops-help-to-maintain-quality-long-term-ai-results",
    "https://blog.pangeanic.com/what-is-reinforcement-learning-from-human-feedback-rlhf-how-it-works"
]
load_documentation(chroma, embeddings, ai_quality_urls, "ai_quality")

ai_quality_retriever_tool = create_tool(
    "ai_quality",
    "ai_quality_search",
    "Search for information about AI quality, sentiment analysis, and human feedback in AI. Use this tool for questions related to improving AI responses, sentiment analysis techniques, and incorporating human feedback in AI systems."
)

# Server Guidelines
server_guidelines_urls = [
    "https://www.veamly.com/blog-posts/prioritize-support-tickets",
    "https://www.sentisum.com/library/how-to-properly-prioritize-customer-support-issues",
    "https://www.freshworks.com/freshdesk/customer-support/prioritize-support-enquiry-blog/",
    "https://www.vivantio.com/blog/the-problems-with-itils-approach-to-support-ticket-prioritization/",
    "https://www.visionhelpdesk.com/5-ways-to-improve-the-efficiency-of-your-ticket-queue-management.html",
    "https://www.jitbit.com/news/ticket-queue-management",
    "https://www.teamsupport.com/blog/5-tips-for-defining-support-ticket-severity",
    "https://www.atlassian.com/blog/halp/top-5-ways-to-prioritize-and-resolve-it-support-tickets-faster",
    "https://customergauge.com/blog/customer-experiences-secret-weapon-responding-to-customer-feedback-fast",
    "https://usersnap.com/blog/collecting-customer-feedback/",
    "https://www.customerthermometer.com/customer-feedback/handling-customer-feedback/",
    "https://www.salesforce.com/resources/articles/how-to-measure-customer-satisfaction/?bc=HA&sfdc-redirect=416",
    "https://www.nngroup.com/articles/user-feedback/",
    "https://www.feedbear.com/blog/how-to-collect-and-manage-customer-feedback",
    "https://www.useresponse.com/blog/how-to-gather-quality-feedback/",
    "https://www.surveymonkey.com/mp/customer-feedback-guide/"
]
load_documentation(chroma, embeddings, server_guidelines_urls, "server_guidelines")

server_guidelines_tool = create_tool(
    "server_guidelines",
    "server_guidelines_search",
    "Search for information about managing the ticketing system, prioritizing issues based on server policies, and handling user feedback. Use this tool for questions related to posting responses, monitoring user feedback, and managing the final stages of response delivery."
)
