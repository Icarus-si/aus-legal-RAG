# Australian Legal Case Analyser

A retrieval-augmented generation (RAG) system that reads real Australian High Court judgments and answers questions about them with exact page citations.

Built by Abhay Singh Wazir, Master of Data Science (Professional) student at Deakin University, Melbourne.

---

## Live Demo

| Resource | Link |
|---|---|
| API docs | aus-legal-rag.onrender.com/docs |
| Interactive UI | Streamlit app (link in repo) |

---

## What this is

Most RAG demos use generic PDFs or toy datasets. I wanted something that actually had to handle dense, technical language, so I used real High Court of Australia judgments, including a 2026 migration law case (San Bao Pty Ltd v Minister for Immigration and Citizenship). The system reads the case, chunks it, embeds it, and lets you ask questions like "why did the delegate refuse the nomination application?" and get back an answer with the exact page number it came from.

That citation requirement was non-negotiable for me. A legal AI tool that gives confident answers with no way to verify them is worse than useless, it's a liability. So every answer in this system points back to a specific page in the source document.

---

## Architecture

This is a standard retrieval-augmented generation pipeline: documents are embedded and indexed once, then relevant chunks are retrieved at query time and handed to an LLM along with strict instructions to only answer from what it's given.

PDF court case
|
PyPDFLoader -> page-level documents
|
RecursiveCharacterTextSplitter (1000 char chunks, 200 overlap)
|
Gemini embeddings (embedding-001)
|
FAISS vector index
|
User question
|
Retriever (top-5 similarity search)
|
Gemini 2.5 Flash + legal analyst system prompt
|
Answer with page citations

### Configuration

<<<<<<< HEAD
| Parameter | Value |
|---|---|
| Chunk size | 1000 characters |
| Chunk overlap | 200 characters |
| Retrieved chunks per query | 5 |
| Embedding model | Gemini embedding-001 |
| LLM | Gemini 2.5 Flash |
| Vector store | FAISS (local, in-memory) |

---

## How it works

1. A PDF court judgment is uploaded and split into overlapping chunks
2. Each chunk is embedded using Google's Gemini embedding model and stored in a FAISS vector index
3. When a question comes in, the system retrieves the 5 most relevant chunks
4. Those chunks are passed to Gemini along with a system prompt instructing it to answer strictly from the provided text and cite case name and page number
5. The answer and source chunks are returned together, so the answer can be verified against the original text

---

## Example Output

Question: `Why did the delegate refuse the nomination application?`
The delegate refused the Company's nomination application for Ms Haiming Du
for a Subclass 482 (Skills in Demand) visa. The delegate's reasoning included
considering documents and information provided by the Company, a requirement
under reg 2.72(10)(a), and that the organisational chart provided did not show
how the position of additional cook fit within the existing staffing structure.

(san_bao_case.pdf, Page 8, Page 9, Page 11)


Not a generic summary, every claim traces back to a page number in the actual judgment.

---

## Key Components

**Chunking strategy**
Legal documents reference earlier sections constantly ("as discussed in paragraph 14"), so chunk overlap matters more here than in general text. 200 characters of overlap reduces the chance that a key sentence gets split across two chunks with no shared context.

**Citation enforcement**
The system prompt explicitly instructs the model to cite case name and page number for every claim, and to say "I could not find this information" rather than guess. This is the single most important design decision in the project, an uncited legal answer is not a useful answer.

**Retrieval over fine-tuning**
RAG was the right choice here over fine-tuning a model on legal text, because the source documents change (new cases get added) and the answers need to be traceable to a specific source. Fine-tuning bakes knowledge into weights with no way to audit where an answer came from.

---

## Tech Stack

- **LLM:** Google Gemini (gemini-2.5-flash)
- **Embeddings:** Gemini embedding-001
- **Vector store:** FAISS
- **Orchestration:** LangChain
- **API:** FastAPI
- **Frontend:** Streamlit, with chat history and a source viewer
- **Deployment:** Render (API) + Streamlit Community Cloud (UI)

---

## Project Structure
aus-legal-RAG/
├── app/
│   └── main.py
├── rag/
│   └── pipeline.py
├── streamlit_app.py
├── data/
│   └── cases/
├── requirements.txt
├── Dockerfile
└── README.md

---

## Run Locally

```bash
git clone https://github.com/Icarus-si/aus-legal-RAG
cd aus-legal-RAG
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

Create a `.env` file with your own Gemini API key:              
GEMINI_API_KEY=your_key_here

Then run:
```bash
uvicorn app.main:app --reload
```

In a second terminal:
```bash
streamlit run streamlit_app.py
```
=======
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
>>>>>>> e59c81d534f1ab229857496594cd05419375ebe8

---

## What I Learned

Getting the LangChain version and Gemini model names right took longer than building the actual pipeline, the library moves fast and a lot of tutorials online reference deprecated imports and model names that no longer exist.

The bigger lesson was around scope. This works well because it's narrow. It's built for legal cases specifically, with a system prompt that assumes legal context. Feeding it an unrelated document, like a university assignment, produces confused output, because the model is told to think like a legal analyst regardless of what it's given. A more general-purpose RAG tool would need to detect document type first and adjust its system prompt accordingly.

---

## Related Projects

- [Tech Job Salary Predictor](https://github.com/Icarus-si/tech-job-predictor) — XGBoost ML API deployed on Render
- [GPT Transformer](https://github.com/Icarus-si/gpt-transformer) — 85M parameter transformer built from scratch

---

Master of Data Science (Professional), Deakin University, Melbourne, Australia
