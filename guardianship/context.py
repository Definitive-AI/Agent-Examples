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



from langchain_community.document_loaders.web_base import WebBaseLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.tools.retriever import create_retriever_tool
from langchain.vectorstores.chroma import Chroma
import chromadb
import uuid

chroma = chromadb.PersistentClient(path="./chroma_db")

def collection_exists(client, collection_name):
    try:
        client.get_collection(collection_name)
        return True
    except ValueError:
        return False

def load_guardianship_renewal_guidelines(chroma, embeddings):
    collection_name = "langchain_tools"
    if not collection_exists(chroma, collection_name):
        urls = [
            "https://snohomishcountywa.gov/1424/Guardianships",
            "https://www.courts.wa.gov/guardianportal/guardianship2022/content/pdf/Information%20Sheet%20for%20Current%20Guardians%20-%20New%20Washington%20Guardianship%20Law.pdf",
            "https://www.familylawselfhelpcenter.org/self-help/guardianship/filing-for-guardianship-over-an-adult/147-after-the-hearing"
        ]
        
        loader = WebBaseLoader(urls)
        data = loader.load()

        documents = RecursiveCharacterTextSplitter(
            chunk_size=1000, chunk_overlap=200
        ).split_documents(data)

        collection = chroma.create_collection(collection_name)
        for doc in documents:
            emb = embeddings.embed_documents([doc.page_content])
            collection.add(
                ids=[str(uuid.uuid1())],
                embeddings=emb,
                metadatas=[doc.metadata],
                documents=[doc.page_content]
            )

load_guardianship_renewal_guidelines(chroma, embeddings)

chroma_store = Chroma(
    client=chroma,
    collection_name="langchain_tools",
    embedding_function=embeddings,
)

guardianship_renewal_guidelines = create_retriever_tool(
    chroma_store.as_retriever(),
    "guardianship_renewal_guidelines",
    "Search for information about guardianship renewal guidelines, processes, deadlines, and key milestones. Use this tool for any questions related to guardianship renewals."
)


import uuid
from langchain_community.document_loaders import WebBaseLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.tools.retriever import create_retriever_tool
from langchain.vectorstores import Chroma

urls = [
    "https://fastercapital.com/content/Expense-Categorization--How-to-Categorize-Your-Expenses-and-Organize-Them-into-Meaningful-Groups.html",
    "https://fastercapital.com/content/Financial-Reporting--Improving-Financial-Reporting-with-Expense-Categorization.html",
    "https://livewell.com/finance/how-to-find-capital-expenditures-in-financial-statements/",
    "https://accountinginsights.org/managing-and-recording-capital-expenditures-in-financial-statements/",
    "https://www.pwc.com/gx/en/audit-services/ifrs/publications/ifrs-in-depth-classification-and-measurement.pdf",
    "https://enrichest.com/en/blog/understanding-expenses-categories-how-to-categorize-financial-records",
    "https://lendza.com/blog/how-to-categorize-expenses",
    "https://yokoy.io/blog/business-expenses/"
]

def load_financial_categorization_rules(chroma, embeddings):
    if not collection_exists(chroma, "financial_categorization_rules"):
        loader = WebBaseLoader(urls)
        data = loader.load()

        documents = RecursiveCharacterTextSplitter(
            chunk_size=1000, chunk_overlap=200
        ).split_documents(data)

        collection = chroma.create_collection("financial_categorization_rules")
        for doc in documents:
            collection.add(
                ids=[str(uuid.uuid1())],
                embeddings=embeddings.embed_documents([doc.page_content]),
                metadatas=doc.metadata,
                documents=[doc.page_content]
            )

load_financial_categorization_rules(chroma, embeddings)

financial_categorization_rules = create_retriever_tool(
    Chroma(
        client=chroma,
        collection_name="financial_categorization_rules",
        embedding_function=embeddings
    ).as_retriever(),
    "financial_categorization_rules",
    "Search for financial categorization rules and guidelines for identifying large expenditures requiring explanation in financial reports. Use this tool for any questions about expense categorization or financial reporting requirements."
)


from langchain_community.document_loaders.web_base import WebBaseLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.tools.retriever import create_retriever_tool
from langchain.vectorstores.chroma import Chroma
import uuid
import requests

urls = [
    "https://www.ftc.gov/business-guidance/privacy-security/privacy-and-security",
    "https://www.hhs.gov/hipaa/for-professionals/privacy/index.html",
    "https://www.justice.gov/opcl/privacy-act-1974",
    "https://www.dol.gov/general/ppii",
    "https://www.nist.gov/privacy-framework",
    "https://www.congress.gov/bill/116th-congress/senate-bill/3456/text",
    "https://iapp.org/resources/article/us-state-privacy-legislation-tracker/",
    "https://www.ncsl.org/technology-and-communication/state-laws-related-to-digital-privacy",
    "https://www.oag.ca.gov/privacy/ccpa",
    "https://gdpr-info.eu/"
]

def load_privacy_regulations(chroma, embeddings):
    if not collection_exists(chroma, "privacy_regulations"):
        loader = WebBaseLoader(urls)
        try:
            data = loader.load()
        except requests.RequestException as e:
            print(f"Error loading data: {e}")
            return

        documents = RecursiveCharacterTextSplitter(
            chunk_size=1000, chunk_overlap=200
        ).split_documents(data)

        collection = chroma.create_collection("privacy_regulations")
        for doc in documents:
            emb = embeddings.embed_documents([doc.page_content])
            collection.add(
                ids=[str(uuid.uuid1())], embeddings=emb, metadatas=doc.metadata, documents=[doc.page_content]
            )

load_privacy_regulations(chroma, embeddings)

chroma_store = Chroma(
    client=chroma,
    collection_name="privacy_regulations",
    embedding_function=embeddings,
)

privacy_regulations = create_retriever_tool(
    chroma_store.as_retriever(),
    "privacy_regulations_search",
    "Search for information about privacy regulations and proper handling of sensitive information. Use this tool for any questions related to privacy laws, data protection, and compliance."
)


from langchain_community.document_loaders import WebBaseLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.tools.retriever import create_retriever_tool
from langchain.vectorstores import Chroma
import uuid

urls = [
    "https://www.law.georgetown.edu/wp-content/uploads/2018/02/secondarysources.pdf",
    "https://www.clio.com/resources/legal-document-templates/",
    "https://libguides.law.illinois.edu/c.php?g=1272613&p=9336249",
    "https://beyondcounsel.io/legal-formatting-how-to-properly-format-legal-documents/",
    "https://www.anylawyer.com/blog/legal-drafting-guide",
    "https://bluenotary.us/contract-drafting-tips-and-best-practices/"
]

def load_legal_templates(chroma, embeddings):
    if not collection_exists(chroma, "legal_templates"):
        try:
            loader = WebBaseLoader(urls)
            data = loader.load()

            documents = RecursiveCharacterTextSplitter(
                chunk_size=1000, chunk_overlap=200
            ).split_documents(data)

            collection = chroma.create_collection("legal_templates")
            for doc in documents:
                emb = embeddings.embed_documents([doc.page_content])
                collection.add(
                    ids=[str(uuid.uuid1())],
                    embeddings=emb,
                    metadatas=doc.metadata,
                    documents=[doc.page_content]
                )
        except Exception as e:
            print(f"Error loading legal templates: {e}")

load_legal_templates(chroma, embeddings)

legal_templates_tool = create_retriever_tool(
    Chroma(
        client=chroma,
        collection_name="legal_templates",
        embedding_function=embeddings
    ).as_retriever(),
    "legal_templates_search",
    "Search for information about legal document templates, structure, content, and formatting. For any questions about legal templates and document formatting, you must use this tool!"
)


import uuid
from langchain_community.document_loaders.web_base import WebBaseLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.tools.retriever import create_retriever_tool
from langchain.vectorstores.chroma import Chroma

urls = [
    "https://finance.alabama.gov/media/2ksjdzw0/oidsadmrules.pdf",
    "https://minute7.com/blog/ethical-considerations-in-legal-billing-practices-for-law-firms",
    "https://lawbillity.com/post/ethical-considerations-in-legal-billing-best-practices-to-ensure-accurate-invoicing/",
    "https://www.lawpay.com/about/blog/sample-billing-language-for-attorneys/",
    "https://www.advocatecapital.com/blog/best-practices-for-drafting-attorney-client-fee-agreements/",
    "https://store.legal.thomsonreuters.com/law-products/solutions/firm-central/resources/ethical-legal-billing",
    "https://www.dentons.com/en/insights/newsletters/2016/november/21/practice-tips-for-lawyers/good-billing-practices-is-an-ethical-duty"
]

def load_legal_billing_guidelines(chroma, embeddings):
    if not collection_exists(chroma, "langchain_tools"):
        loader = WebBaseLoader(urls)
        data = loader.load()

        documents = RecursiveCharacterTextSplitter(
            chunk_size=1000, chunk_overlap=200
        ).split_documents(data)

        collection = chroma.get_or_create_collection("langchain_tools")
        
        ids = [str(uuid.uuid1()) for _ in documents]
        contents = [doc.page_content for doc in documents]
        metadatas = [doc.metadata for doc in documents]
        
        embeddings_list = embeddings.embed_documents(contents)
        
        collection.add(
            ids=ids, embeddings=embeddings_list, metadatas=metadatas, documents=contents
        )

load_legal_billing_guidelines(chroma, embeddings)

chroma_store = Chroma(
    client=chroma,
    collection_name="langchain_tools",
    embedding_function=embeddings,
)

legal_billing_guidelines = create_retriever_tool(
    chroma_store.as_retriever(),
    "legal_billing_guidelines",
    "Search for guidelines and ethical considerations related to attorney fee declarations and legal billing practices. Use this tool for any questions about professional standards in legal billing."
)


import uuid
from langchain_community.document_loaders.web_base import WebBaseLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.tools.retriever import create_retriever_tool
from langchain.vectorstores.chroma import Chroma

urls = [
    "https://www.courts.ca.gov/cms/rules/index.cfm?title=two&linkid=rule2_111",
    "https://www.supremecourt.gov/filingandrules/electronicfilingguidelines.pdf",
    "https://www.ca11.uscourts.gov/sites/default/files/courtdocs/clk/CMECFGuideToElectronicFiling.pdf",
    "https://www.civillawselfhelpcenter.org/self-help/getting-started/48-basics-of-court-forms-and-filings",
    "https://guides.ll.georgetown.edu/legal_forms"
]

def load_court_guidelines(chroma, embeddings):
    if not collection_exists(chroma, "langchain_tools"):
        loader = WebBaseLoader(urls)
        data = loader.load()

        documents = RecursiveCharacterTextSplitter(
            chunk_size=1000, chunk_overlap=200
        ).split_documents(data)

        collection = chroma.create_collection("langchain_tools")
        for doc in documents:
            collection.add(
                ids=[str(uuid.uuid1())],
                embeddings=embeddings.embed_documents([doc.page_content]),
                metadatas=[doc.metadata],
                documents=[doc.page_content]
            )

load_court_guidelines(chroma, embeddings)

court_guidelines = create_retriever_tool(
    Chroma(client=chroma, collection_name="langchain_tools", embedding_function=embeddings).as_retriever(),
    "court_guidelines_search",
    "Search for court guidelines and requirements for different document types. Use this tool for any questions about court document formatting and filing rules."
)


from langchain_community.document_loaders import WebBaseLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.tools.retriever import create_retriever_tool
from langchain.vectorstores import Chroma
import uuid

urls = [
    "https://apastyle.apa.org/style-grammar-guidelines/paper-format",
    "https://libguides.uww.edu/apa/format",
    "https://support.microsoft.com/en-us/office/use-section-breaks-to-change-the-layout-or-formatting-in-one-section-of-your-document-4cdfa638-3ea9-434a-8034-bf1e4274c450",
    "https://www.courts.ca.gov/cms/rules/index.cfm?title=two&linkid=rule2_111",
    "https://grants.nih.gov/grants/how-to-apply-application-guide/format-and-write/format-attachments.htm",
    "https://owl.purdue.edu/owl/research_and_citation/apa_style/apa_formatting_and_style_guide/index.html",
    "https://www.plainlanguage.gov/guidelines/"
]

def load_formatting_guide(chroma, embeddings):
    if not collection_exists(chroma, "langchain_tools"):
        loader = WebBaseLoader(urls)
        data = loader.load()

        documents = RecursiveCharacterTextSplitter(
            chunk_size=1000, chunk_overlap=200
        ).split_documents(data)

        collection = chroma.create_collection("langchain_tools")
        for doc in documents:
            collection.add(
                ids=[str(uuid.uuid1())],
                embeddings=embeddings.embed_documents([doc.page_content]),
                metadatas=doc.metadata,
                documents=[doc.page_content]
            )

load_formatting_guide(chroma, embeddings)

formatting_guide = create_retriever_tool(
    Chroma(client=chroma, collection_name="langchain_tools", embedding_function=embeddings).as_retriever(),
    "formatting_guide",
    "Search for information on proper formatting rules, including spacing, section breaks, and signature page requirements. Use this tool for any questions about document formatting and style guidelines."
)


from langchain_community.document_loaders.web_base import WebBaseLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.tools.retriever import create_retriever_tool
from langchain.vectorstores.chroma import Chroma
import uuid

urls = [
    "https://www.civillawselfhelpcenter.org/self-help/getting-started/court-basics/48-basics-of-court-forms-and-filings",
    "https://www.supremecourt.gov/filingandrules/electronicfilingguidelines.pdf",
    "https://www.ctd.uscourts.gov/sites/default/files/Electronic-Filing-Policies-and-Procedures-3-22-24.pdf",
    "https://drlegalprocess.com/how-to-serve-court-papers-legally-and-effectively/",
    "https://saclaw.org/resource_library/serving-motions-and-other-papers-during-a-civil-case/"
]

def load_filing_procedures(chroma, embeddings):
    if not collection_exists(chroma, "langchain_tools"):
        loader = WebBaseLoader(urls)
        data = loader.load()

        documents = RecursiveCharacterTextSplitter(
            chunk_size=1000, chunk_overlap=200
        ).split_documents(data)

        collection = chroma.create_collection("langchain_tools")
        for doc in documents:
            emb = embeddings.embed_documents([doc.page_content])
            collection.add(
                ids=[str(uuid.uuid1())], embeddings=emb, metadatas=doc.metadata, documents=[doc.page_content]
            )

load_filing_procedures(chroma, embeddings)

filing_procedures = create_retriever_tool(
    Chroma(client=chroma, collection_name="langchain_tools", embedding_function=embeddings).as_retriever(),
    "filing_procedures",
    "Search for information about correct procedures for filing court documents and distributing them to interested parties. Use this tool for any questions related to court filing and document distribution procedures."
)
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



import uuid
from langchain_community.document_loaders import WebBaseLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.tools.retriever import create_retriever_tool
from langchain.vectorstores import Chroma
import chromadb
from langchain_community.embeddings import HuggingFaceEmbeddings

chroma = chromadb.PersistentClient(path="./chroma_db")
embeddings = HuggingFaceEmbeddings()

def collection_exists(client, collection_name):
    return collection_name in [collection.name for collection in client.list_collections()]

urls = [
    "https://www.pandadoc.com/blog/how-create-effective-document-templates/",
    "https://www.templafy.com/blog/what-is-document-generation-and-the-10-best-tools-in-2024/",
    "https://dzone.com/articles/the-power-of-template-based-document-generation-wi",
    "https://www.halfofthe.com/how-to/step-by-step-guide-how-to-create-custom-templates-in-word/",
    "https://www.docupilot.app/blog/document-generation-software",
    "https://www.linkedin.com/pulse/document-generation-best-practices-tips-error-free-documents-hzemc",
    "https://perfectdoc.studio/inspiration/what-is-document-generation-a-guide-to-generate-documents-in-the-right-way/"
]

def load_template_documents(chroma, embeddings):
    if not collection_exists(chroma, "template_documents"):
        try:
            loader = WebBaseLoader(urls)
            data = loader.load()

            documents = RecursiveCharacterTextSplitter(
                chunk_size=1000, chunk_overlap=200
            ).split_documents(data)

            collection = chroma.create_collection("template_documents")
            for doc in documents:
                emb = embeddings.embed_documents([doc.page_content])
                collection.add(
                    ids=[str(uuid.uuid1())], embeddings=emb, metadatas=doc.metadata, documents=[doc.page_content]
                )
        except Exception as e:
            print(f"Error loading documents: {e}")

load_template_documents(chroma, embeddings)

chroma_store = Chroma(
    client=chroma,
    collection_name="template_documents",
    embedding_function=embeddings
)

template_documents = create_retriever_tool(
    chroma_store.as_retriever(),
    "template_documents",
    "Search for information about generating initial documents correctly and ensuring proper formatting using templates. Use this tool for questions about document templates, generation, and formatting best practices."
)


import uuid
from langchain_community.document_loaders.web_base import WebBaseLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.tools.retriever import create_retriever_tool
from langchain.vectorstores.chroma import Chroma

urls = [
    "https://support.microsoft.com/en-us/office/overview-of-excel-tables-7ab0bb7d-3a9e-4b56-a3c9-6c94334e492c",
    "https://www.excel-easy.com/data-analysis/data-structure.html",
    "https://www.ablebits.com/office-addins-blog/excel-data-structure/",
    "https://exceljet.net/excel-tables",
    "https://www.myexcelonline.com/blog/excel-data-structure/"
]

def load_excel_data_structure_guide(chroma, embeddings):
    if not collection_exists(chroma, "langchain_tools"):
        loader = WebBaseLoader(urls)
        data = loader.load()

        documents = RecursiveCharacterTextSplitter(
            chunk_size=1000, chunk_overlap=200
        ).split_documents(data)

        collection = chroma.create_collection("langchain_tools")
        for doc in documents:
            collection.add(
                ids=[str(uuid.uuid1())], embeddings=None, metadatas=doc.metadata, documents=[doc.page_content]
            )

load_excel_data_structure_guide(chroma, embeddings)

excel_data_structure_chroma_retriever = Chroma(
    client=chroma,
    collection_name="langchain_tools",
    embedding_function=embeddings,
)

excel_data_structure_guide = create_retriever_tool(
    excel_data_structure_chroma_retriever.as_retriever(),
    "excel_data_structure_guide",
    "Search for information about Excel data structure, tables, and how to extract and interpret data from Excel files. Use this tool for any questions related to understanding Excel data organization and manipulation."
)


import uuid
from langchain_community.document_loaders.web_base import WebBaseLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.tools.retriever import create_retriever_tool
from langchain.vectorstores.chroma import Chroma

urls = [
    "https://datamanagement.hms.harvard.edu/plan-design/file-naming-conventions",
    "https://hivo.co/blog/understanding-file-naming-conventions-examples-and-best-practices",
    "https://www.lucapallotta.com/optimal-file-naming-conventions/",
    "https://cssanimation.io/blog/how-to-master-digital-file-organization-12-best-practices/",
    "https://teslagov.com/file-naming-and-data-organization-best-practices-from-clutter-and-chaos-to-knowledge-management-nirvana/",
    "https://wordfields.com/blog/file-naming-conventions/"
]

def load_file_naming_conventions(chroma, embeddings):
    if not collection_exists(chroma, "file_naming_conventions"):
        loader = WebBaseLoader(urls)
        data = loader.load()

        documents = RecursiveCharacterTextSplitter(
            chunk_size=1000, chunk_overlap=200
        ).split_documents(data)

        collection = chroma.create_collection("file_naming_conventions")
        for doc in documents:
            emb = embeddings.embed_documents([doc.page_content])
            collection.add(
                ids=[str(uuid.uuid1())], embeddings=emb, metadatas=doc.metadata, documents=[doc.page_content]
            )

load_file_naming_conventions(chroma, embeddings)

file_naming_conventions_db = Chroma(
    client=chroma,
    collection_name="file_naming_conventions",
    embedding_function=embeddings,
)

file_naming_conventions_retriever_tool = create_retriever_tool(
    file_naming_conventions_db.as_retriever(),
    "file_naming_conventions",
    "Search for information about file naming conventions and best practices for file management and organization. Use this tool for any questions related to file naming, organization, or management."
)


from langchain_community.document_loaders import WebBaseLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.tools.retriever import create_retriever_tool
from langchain.vectorstores.chroma import Chroma
import chromadb
import uuid

chroma = chromadb.PersistentClient(path="./chroma_db")

def collection_exists(client, collection_name):
    return collection_name in [c.name for c in client.list_collections()]

urls = [
    "https://arxiv.org/pdf/2403.07557.pdf",
    "https://tingofurro.github.io/pdfs/TACL2021_SummaC.pdf",
    "https://arxiv.org/pdf/2310.13189v2.pdf",
    "https://aicontentfy.com/en/blog/quality-control-how-to-verify-ai-generated-content",
    "https://toloka.ai/blog/fact-checking-llm-generated-content/",
    "https://medium.com/@senol.isci/comprehensive-guide-on-evaluation-of-response-generation-and-retrieval-with-llms-0cbc2adb3ae6",
    "https://products.groupdocs.app/comparison/total",
    "https://app.copyleaks.com/text-compare"
]

def load_template_documents(chroma, embeddings):
    collection_name = "template_documents"
    if not collection_exists(chroma, collection_name):
        try:
            loader = WebBaseLoader(urls)
            data = loader.load()

            documents = RecursiveCharacterTextSplitter(
                chunk_size=1000, chunk_overlap=200
            ).split_documents(data)

            collection = chroma.create_collection(collection_name)
            for doc in documents:
                emb = embeddings.embed_documents([doc.page_content])
                collection.add(
                    ids=[str(uuid.uuid4())], embeddings=emb, metadatas=doc.metadata, documents=[doc.page_content]
                )
        except Exception as e:
            print(f"Error loading documents: {e}")

load_template_documents(chroma, embeddings)

template_documents = Chroma(
    client=chroma,
    collection_name="template_documents",
    embedding_function=embeddings,
)

template_documents_tool = create_retriever_tool(
    template_documents.as_retriever(),
    "template_documents_search",
    "Search for template documents to compare with generated documents and detect errors and inconsistencies. Use this tool for any questions about document comparison or verification of AI-generated content."
)


from langchain_community.document_loaders import WebBaseLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.tools.retriever import create_retriever_tool
from langchain.vectorstores.chroma import Chroma
import uuid

def collection_exists(client, collection_name):
    collections = client.list_collections()
    return collection_name in [c.name for c in collections]

urls = [
    "https://snohomishcountywa.gov/1424/Guardianships",
    "https://www.courts.wa.gov/guardianportal/guardianship2022/content/pdf/Information Sheet for Current Guardians - New Washington Guardianship Law.pdf",
    "https://www.iowacourts.gov/faq/guardianships-adult",
    "https://www.familylawselfhelpcenter.org/self-help/guardianship/guardianship-forms",
    "https://www.justice.gov/elderjustice/guardianship-key-concepts-and-resources"
]

def load_guardianship_documentation(chroma, embeddings):
    if not collection_exists(chroma, "langchain_tools"):
        try:
            loader = WebBaseLoader(urls)
            data = loader.load()

            documents = RecursiveCharacterTextSplitter(
                chunk_size=1000, chunk_overlap=200
            ).split_documents(data)

            collection = chroma.create_collection("langchain_tools")
            for doc in documents:
                emb = embeddings.embed_documents([doc.page_content])
                collection.add(
                    ids=[str(uuid.uuid1())], embeddings=emb, metadatas=doc.metadata, documents=[doc.page_content]
                )
        except Exception as e:
            print(f"Error loading guardianship documentation: {e}")

load_guardianship_documentation(chroma, embeddings)

chroma_store = Chroma(
    client=chroma,
    collection_name="langchain_tools",
    embedding_function=embeddings,
)

guardianship_renewal_requirements = create_retriever_tool(
    chroma_store.as_retriever(),
    "guardianship_renewal_search",
    "Search for information about guardianship renewal requirements. Use this tool for any questions related to legal and procedural requirements for guardianship renewals."
)


from langchain_community.document_loaders.web_base import WebBaseLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.tools.retriever import create_retriever_tool
from langchain.vectorstores.chroma import Chroma
import uuid

urls = [
    "https://www.hhs.texas.gov/sites/default/files/documents/laws-regulations/legal-information/guardianship/texas-guide-adult-guardianship.pdf",
    "https://www.dshs.wa.gov/sites/default/files/ALTSA/stakeholders/documents/guardianship/Guardianship%20and%20Power%20of%20Attorney%20FAQs.pdf",
    "https://www.minnesotaguardianship.org/faq/",
    "https://www.courts.wa.gov/guardianportal/guardianship2022/content/pdf/Information%20Sheet%20for%20Current%20Guardians%20-%20New%20Washington%20Guardianship%20Law.pdf",
    "https://www.oregon.gov/odhs/providers-partners/community-services-supports/Pages/guardianship.aspx"
]

def load_guardianship_documentation(chroma, embeddings):
    if not collection_exists(chroma, "langchain_tools"):
        loader = WebBaseLoader(urls)
        data = loader.load()

        documents = RecursiveCharacterTextSplitter(
            chunk_size=1000, chunk_overlap=200
        ).split_documents(data)

        collection = chroma.create_collection("langchain_tools")
        for doc in documents:
            emb = embeddings.embed_documents([doc.page_content])
            collection.add(
                ids=[str(uuid.uuid1())], embeddings=emb, metadatas=doc.metadata, documents=[doc.page_content]
            )

load_guardianship_documentation(chroma, embeddings)

guardianship_renewal_requirements = create_retriever_tool(
    Chroma(client=chroma, collection_name="langchain_tools", embedding_function=embeddings).as_retriever(),
    "guardianship_renewal_search",
    "Search for information about guardianship renewal requirements. For any questions about guardianship renewal, you must use this tool!"
)


from langchain_community.document_loaders.web_base import WebBaseLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.tools.retriever import create_retriever_tool
from langchain.vectorstores.chroma import Chroma
import uuid

urls = [
    "https://www.calbar.ca.gov/Public/Free-Legal-Information/Working-with-an-Attorney/What-to-Expect-Regarding-Fees-and-Billing",
    "https://www.upcounsel.com/attorney-fees-and-costs",
    "https://lawbillity.com/post/ensuring-accurate-client-billing-in-your-law-firm/",
    "https://casepacer.com/resources/law-firm-billing",
    "https://www.accuratelegalbilling.com/blog/billing-guidelines-key-to-success-for-law-firms-of-all-sizes",
    "https://www.advocatemagazine.com/article/2022-december/showing-what-you-re-worth",
    "https://content.next.westlaw.com/practical-law/document/If383b232222f11e698dc8b09b4f043e0/Attorneys-Fees-Toolkit-Federal",
    "https://www.thurmanarnold.com/documents/sample-attorney-fee-declaration-for-fees-mid-level-case.pdf",
    "https://library.nclc.org/article/tips-handling-attorney-fee-hearings"
]

def load_attorney_fee_guidelines(chroma, embeddings):
    if not collection_exists(chroma, "langchain_tools"):
        loader = WebBaseLoader(urls)
        data = loader.load()

        documents = RecursiveCharacterTextSplitter(
            chunk_size=1000, chunk_overlap=200
        ).split_documents(data)

        collection = chroma.create_collection("langchain_tools")
        for doc in documents:
            emb = embeddings.embed_documents([doc.page_content])
            collection.add(
                ids=[str(uuid.uuid1())], embeddings=emb, metadatas=doc.metadata, documents=[doc.page_content]
            )

load_attorney_fee_guidelines(chroma, embeddings)

attorney_fee_guidelines = create_retriever_tool(
    Chroma(client=chroma, collection_name="langchain_tools", embedding_function=embeddings).as_retriever(),
    "attorney_fee_guidelines",
    "Search for information about attorney fee guidelines, fee declarations, and accurate billing practices. Use this tool for any questions related to attorney fees, billing, and fee declarations."
)


from langchain_community.document_loaders.web_base import WebBaseLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.tools.retriever import create_retriever_tool
from langchain.vectorstores.chroma import Chroma
import uuid

urls = [
    "https://www.hfma.org/wp-content/uploads/2024/02/PFC-best-practices-2024.pdf",
    "https://www.boardeffect.com/blog/best-financial-practices-for-healthcare-organizations/",
    "https://www.sharevault.com/blog/secure-file-sharing/safeguarding-sensitive-document-information",
    "https://oneconverse.com/blog/handling-sensitive-documents-a-guide-to-confidentiality/",
    "https://gaine.com/blog/health/the-handbook-of-regulatory-compliance-in-healthcare/",
    "https://www.smartsheet.com/content/regulatory-compliance-for-business-managers",
    "https://www.epa.gov/system/files/documents/2024-04/pfas-npdwr_prepubfederalregisternotice_4.8.24.pdf"
]

def load_financial_medical_guidelines(chroma, embeddings):
    collection_name = "financial_medical_guidelines"
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
                ids=[str(uuid.uuid1())], embeddings=emb, metadatas=doc.metadata, documents=[doc.page_content]
            )

load_financial_medical_guidelines(chroma, embeddings)

financial_medical_guidelines = create_retriever_tool(
    Chroma(client=chroma, collection_name="financial_medical_guidelines", embedding_function=embeddings).as_retriever(),
    "financial_medical_guidelines",
    "Search for financial and medical guidelines related to sensitive documents. Use this tool for questions about best practices, regulatory compliance, and handling confidential information in medical and financial contexts."
)


import uuid
from langchain_community.document_loaders.web_base import WebBaseLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.tools.retriever import create_retriever_tool
from langchain.vectorstores.chroma import Chroma

urls = [
    "https://www.uscourts.gov/rules-policies/current-rules-practice-procedure",
    "https://www.americanbar.org/groups/legal_services/flh-home/flh-court-rules/",
    "https://www.law.cornell.edu/wex/rules_of_court",
    "https://www.ncsc.org/topics/court-management/court-rules/resource-guide",
    "https://www.fjc.gov/content/345414/court-rules",
    "https://www.courtlistener.com/recap/",
    "https://www.pacer.gov/",
    "https://www.supremecourt.gov/filingandrules/rules_guidance.aspx",
    "https://www.americanbar.org/groups/litigation/resources/rules/",
    "https://www.law.georgetown.edu/library/research/court-rules-forms-dockets/"
]

def load_court_specific_guidelines(chroma):
    collection_name = "langchain_tools"
    if not collection_exists(chroma, collection_name):
        loader = WebBaseLoader(urls)
        data = loader.load()

        documents = RecursiveCharacterTextSplitter(
            chunk_size=1000, chunk_overlap=200
        ).split_documents(data)

        collection = chroma.create_collection(collection_name)
        for doc in documents:
            collection.add(
                ids=[str(uuid.uuid1())],
                embeddings=embeddings.embed_documents([doc.page_content]),
                metadatas=doc.metadata,
                documents=[doc.page_content]
            )

load_court_specific_guidelines(chroma)

court_guidelines_db = Chroma(
    client=chroma,
    collection_name="langchain_tools",
    embedding_function=embeddings,
)

court_specific_guidelines = create_retriever_tool(
    court_guidelines_db.as_retriever(),
    "court_specific_guidelines",
    "Search for information about adapting documents and processes based on specific court procedures. Use this tool for any questions related to court rules, guidelines, or procedures."
)


from langchain_community.document_loaders.web_base import WebBaseLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.tools.retriever import create_retriever_tool
from langchain.vectorstores.chroma import Chroma
import uuid

urls = [
    "https://snohomishcountywa.gov/1424/Guardianships",
    "https://www.courts.wa.gov/guardianportal/index.cfm?fa=guardianportal.guardianship2022",
    "https://www.courts.wa.gov/forms/?fa=forms.home&dis=y",
    "https://www.washingtonlawhelp.org/issues/family-law/guardianship-of-a-child"
]

def load_guardianship_renewal_requirements(chroma, embeddings):
    if not collection_exists(chroma, "langchain_tools"):
        loader = WebBaseLoader(urls)
        data = loader.load()

        documents = RecursiveCharacterTextSplitter(
            chunk_size=1000, chunk_overlap=200
        ).split_documents(data)

        collection = chroma.create_collection("langchain_tools")
        for doc in documents:
            emb = embeddings.embed_documents([doc.page_content])
            collection.add(
                ids=[str(uuid.uuid1())],
                embeddings=emb,
                metadatas=doc.metadata,
                documents=[doc.page_content]
            )

load_guardianship_renewal_requirements(chroma, embeddings)

guardianship_renewal_requirements = create_retriever_tool(
    Chroma(client=chroma, collection_name="langchain_tools", embedding_function=embeddings).as_retriever(),
    "guardianship_renewal_search",
    "Search for information about guardianship renewal requirements in Washington state. For any questions about guardianship renewal, you must use this tool!"
)


import uuid
from langchain_community.document_loaders.web_base import WebBaseLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.tools.retriever import create_retriever_tool
from langchain.vectorstores.chroma import Chroma

urls = [
    "https://library.si.edu/sites/default/files/tutorial/pdf/filenamingorganizing20180227.pdf",
    "https://guides.library.harvard.edu/c.php?g=1033502",
    "https://projectmanagementreport.com/blog/file-management",
    "https://hivo.co/blog/understanding-file-naming-conventions-examples-and-best-practices",
    "https://hivo.co/blog/2022-best-practices-for-file-naming-conventions",
    "https://teslagov.com/file-naming-and-data-organization-best-practices-from-clutter-and-chaos-to-knowledge-management-nirvana/"
]

def load_file_naming_conventions(chroma, embeddings):
    if not collection_exists(chroma, "langchain_tools"):
        loader = WebBaseLoader(urls)
        data = loader.load()

        documents = RecursiveCharacterTextSplitter(
            chunk_size=1000, chunk_overlap=200
        ).split_documents(data)

        collection = chroma.create_collection("langchain_tools")
        for doc in documents:
            emb = embeddings.embed_documents([doc.page_content])
            collection.add(
                ids=[str(uuid.uuid1())], embeddings=emb, metadatas=doc.metadata, documents=[doc.page_content]
            )

load_file_naming_conventions(chroma, embeddings)

chroma_db = Chroma(
    client=chroma,
    collection_name="langchain_tools",
    embedding_function=embeddings,
)

file_naming_conventions = create_retriever_tool(
    chroma_db.as_retriever(),
    "file_naming_conventions",
    "Search for information about file naming conventions, organization strategies, and best practices for maintaining consistency in file management processes. Use this tool for any questions related to file naming and organization."
)
