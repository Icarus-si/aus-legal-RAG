import os
from dotenv import load_dotenv
from langchain_google_genai import GoogleGenerativeAIEmbeddings, ChatGoogleGenerativeAI
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
FAISS_INDEX_PATH = "faiss_index"

def load_and_index_pdfs(pdf_paths: list):
    print(f"Loading {len(pdf_paths)} PDFs...")
    all_docs = []
    for path in pdf_paths:
        loader = PyPDFLoader(path)
        docs = loader.load()
        for doc in docs:
            doc.metadata["source"] = os.path.basename(path)
        all_docs.extend(docs)
    print(f"Loaded {len(all_docs)} pages total")

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200
    )
    chunks = splitter.split_documents(all_docs)
    print(f"Split into {len(chunks)} chunks")

    embeddings = GoogleGenerativeAIEmbeddings(
        model="models/gemini-embedding-001",
        google_api_key=GEMINI_API_KEY
    )
    vectorstore = FAISS.from_documents(chunks, embeddings)
    vectorstore.save_local(FAISS_INDEX_PATH)
    print(f"✅ Saved FAISS index with {len(chunks)} chunks")
    return len(chunks)

def load_vectorstore():
    embeddings = GoogleGenerativeAIEmbeddings(
        model="models/gemini-embedding-001",
        google_api_key=GEMINI_API_KEY
    )
    vectorstore = FAISS.load_local(
        FAISS_INDEX_PATH,
        embeddings,
        allow_dangerous_deserialization=True
    )
    return vectorstore

def get_rag_chain(vectorstore):
    llm = ChatGoogleGenerativeAI(
        model="gemini-2.5-flash",
        google_api_key=GEMINI_API_KEY,
        temperature=0.2
    )
    retriever = vectorstore.as_retriever(search_kwargs={"k": 5})

    prompt = ChatPromptTemplate.from_template("""
You are an expert Australian legal analyst.
Answer the question based strictly on the provided legal case documents.
Always cite the specific case name and page number.
If the answer is not in the documents, say "I could not find this information in the provided cases."

Context from legal cases:
{context}

Question: {question}

Answer with citations:
""")

    def format_docs(docs):
        return "\n\n".join([
            f"[Source: {doc.metadata.get('source', 'Unknown')}, Page {doc.metadata.get('page', 0) + 1}]\n{doc.page_content}"
            for doc in docs
        ])

    chain = (
        {"context": retriever | format_docs, "question": RunnablePassthrough()}
        | prompt
        | llm
        | StrOutputParser()
    )
    return chain, retriever

def ask_question(chain_tuple, question: str):
    chain, retriever = chain_tuple
    answer = chain.invoke(question)
    docs = retriever.invoke(question)

    sources = []
    for doc in docs:
        sources.append({
            "case": doc.metadata.get("source", "Unknown"),
            "page": doc.metadata.get("page", 0) + 1,
            "excerpt": doc.page_content[:200] + "..."
        })

    return {
        "answer": answer,
        "sources": sources
    }