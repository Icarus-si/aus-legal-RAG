Australian Legal Case Analyser

A retrieval-augmented generation (RAG) system that reads real Australian High Court judgments and answers questions about them with exact page citations.

Built by Abhay Singh Wazir, Master of Data Science (Professional) student at Deakin University, Melbourne.

Live demo


API docs: aus-legal-rag.onrender.com/docs
Interactive UI: Streamlit app (link in repo)

What this is

Most RAG demos use generic PDFs or toy datasets. I wanted something that actually had to handle dense, technical language — so I used real High Court of Australia judgments, including a 2026 migration law case (San Bao Pty Ltd v Minister for Immigration and Citizenship). The system reads the case, chunks it, embeds it, and lets you ask questions like "why did the delegate refuse the nomination application?" and get back an answer with the exact page number it came from.

That citation requirement was non-negotiable for me. A legal AI tool that gives confident answers with no way to verify them is worse than useless — it's a liability. So every answer in this system points back to a specific page in the source document.

How it works

1. A PDF court judgment is uploaded and split into overlapping chunks (1000 characters, 200 character overlap).
2. Each chunk is embedded using Google's Gemini embedding model and stored in a FAISS vector index.
3. When a question comes in, the system retrieves the 5 most relevant chunks.
4. Those chunks are passed to Gemini along with a system prompt instructing it to answer strictly from the provided text and cite case name and page number.
5. The answer and source chunks are returned together, so you can verify the answer against the original text.

Tech stack

LLM: Google Gemini (gemini-2.5-flash)
Embeddings: Gemini embedding-001
Vector store: FAISS
Framework: LangChain
API: FastAPI
Frontend: Streamlit (with chat history and source viewer)
Deployment: Render + Streamlit Community Cloud

Example interaction

Question: Why did the delegate refuse the nomination application?

Answer: The delegate refused the Company's nomination application for Ms Haiming Du for a Subclass 482 (Skills in Demand) visa. The delegate's reasoning included considering documents and information provided by the Company, a requirement under reg 2.72(10)(a), and that the organisational chart provided did not show how the position of additional cook fit within the existing staffing structure.

(san_bao_case.pdf, Page 8, Page 9, Page 11)

Architecture

PDF court case
|
PyPDFLoader -> page-level documents
|
RecursiveCharacterTextSplitter (1000 char chunks, 200 overlap)
|
Gemini embeddings -> FAISS vector index
|
User question
|
Retriever (top-5 similarity search)
|
Gemini (gemini-2.5-flash) with legal analyst system prompt
|
Answer + page citations

Run locally

1. bash:                                          
git clone https://github.com/Icarus-si/aus-legal-RAG                        
cd aus-legal-RAG                                            
python -m venv venv                                                     
venv\Scripts\activate                                                  
pip install -r requirements.txt                                      

2. Create a .env file with your own Gemini API key:                                                                                                              
GEMINI_API_KEY=your_key_here

3. Then run:                                                        
bashuvicorn app.main:app --reload

4. In a second terminal:                                                                       
bashstreamlit run streamlit_app.py

What I learned

Getting the LangChain version and Gemini model names right took longer than building the actual pipeline — the library moves fast and a lot of tutorials online reference deprecated imports and model names that no longer exist. The bigger lesson was around scope: this works well because it's narrow. It's built for legal cases specifically, with a system prompt that assumes legal context. Feeding it an unrelated document, like a university assignment, produces confused output, because the model is told to think like a legal analyst regardless of what it's given. A more general-purpose RAG tool would need to detect document type first.

Related projects

Tech Job Salary Predictor — XGBoost ML API deployed on Render
GPT Transformer — 85M parameter transformer built from scratch


Master of Data Science (Professional), Deakin University, Melbourne, Australia
