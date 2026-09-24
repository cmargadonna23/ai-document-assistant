# AI Document Assistant

A portfolio-grade **Retrieval-Augmented Generation (RAG)** application for asking questions about uploaded documents. The app extracts and chunks document text, creates vector embeddings, retrieves the most relevant passages for each question, and uses an OpenAI model to produce source-grounded answers with citations.

## Why this project exists

Many AI demos send an entire document to a model and hope for a good answer. This project demonstrates a more scalable architecture:

```text
Upload documents
      ↓
Parse text + preserve source locations
      ↓
Create overlapping chunks
      ↓
Generate embeddings
      ↓
Build an in-memory vector index
      ↓
User asks a question
      ↓
Embed the question + retrieve relevant chunks
      ↓
Send only relevant evidence to the model
      ↓
Grounded answer with [S1], [S2] citations
```

## Features

- Upload multiple **PDF, DOCX, TXT, CSV, and XLSX** files
- Semantic search using OpenAI embeddings
- Source-grounded document Q&A
- Inline citation labels such as `[S1]` and `[S2]`
- Expandable evidence cards with similarity scores and excerpts
- Executive document summaries
- Side-by-side document comparison
- Persistent chat history for the current Streamlit session
- Markdown transcript export
- Light/dark-compatible modern Streamlit interface
- File-size validation and duplicate-file detection
- Prompt-injection-aware system instructions that treat document text as untrusted data
- HTML escaping for document excerpts rendered in the UI
- Unit tests for parsing, chunking, retrieval, exports, and the end-to-end local RAG pipeline
- GitHub Actions test workflow

## Technology stack

- **Python** — application language
- **Streamlit** — interactive web interface
- **OpenAI Responses API** — grounded answer generation, summaries, and comparison
- **OpenAI Embeddings API** — semantic vector representations
- **NumPy** — transparent cosine-similarity vector retrieval
- **PyPDF** — PDF text extraction
- **python-docx** — DOCX parsing
- **openpyxl** — Excel parsing
- **pytest** — automated tests

The default embedding model is `text-embedding-3-small`. The text model is configurable and defaults to `gpt-5.6-luna`.

## Project structure

```text
ai_document_assistant/
│
├── app.py
├── README.md
├── requirements.txt
├── .env.example
├── .gitignore
│
├── .streamlit/
│   └── config.toml
│
├── .github/
│   └── workflows/
│       └── tests.yml
│
├── sample_docs/
│   └── demo_handbook.txt
│
├── src/
│   ├── __init__.py
│   ├── config.py
│   ├── models.py
│   │
│   ├── ingestion/
│   │   ├── __init__.py
│   │   ├── parsers.py
│   │   └── chunking.py
│   │
│   ├── rag/
│   │   ├── __init__.py
│   │   ├── embeddings.py
│   │   ├── index.py
│   │   └── pipeline.py
│   │
│   ├── services/
│   │   ├── __init__.py
│   │   ├── openai_client.py
│   │   └── export.py
│   │
│   └── ui/
│       ├── __init__.py
│       └── styles.py
│
└── tests/
    ├── __init__.py
    ├── test_chunking.py
    ├── test_export.py
    ├── test_index.py
    ├── test_parsers.py
    └── test_pipeline.py
```

## Architecture

### Ingestion layer

`src/ingestion/parsers.py` converts supported formats into `DocumentSection` objects while retaining useful source locations such as PDF page numbers, spreadsheet sheet/row ranges, and document paragraph ranges.

`src/ingestion/chunking.py` turns those sections into overlapping chunks while retaining source metadata. Stable chunk IDs are generated for traceability.

### Retrieval layer

`src/rag/embeddings.py` provides an embedding-provider abstraction and an OpenAI implementation.

`src/rag/index.py` contains a small, transparent in-memory vector store using normalized NumPy arrays and cosine similarity. This keeps the retrieval mechanics visible instead of hiding them behind a large vector-database dependency.

### Generation layer

`src/services/openai_client.py` uses the OpenAI Responses API for:

- grounded Q&A
- executive summaries
- document comparison

The answer prompt explicitly requires use of the retrieved context and requires citations such as `[S1]`.

### Orchestration layer

`src/rag/pipeline.py` coordinates parsing, chunking, embedding, indexing, retrieval, and generation through the `DocumentAssistant` class.

### UI layer

`app.py` owns the Streamlit page layout and session state. Business logic remains in `src/`, keeping the interface separate from the document/RAG logic.

## Setup

### 1. Clone the repository

```bash
git clone <your-repository-url>
cd ai_document_assistant
```

### 2. Create a virtual environment

```bash
python -m venv .venv
```

Activate it.

**Windows PowerShell**

```powershell
.\.venv\Scripts\Activate.ps1
```

**macOS / Linux**

```bash
source .venv/bin/activate
```

### 3. Install dependencies

```bash
python -m pip install -r requirements.txt
```

### 4. Configure your OpenAI API key

Copy the example environment file:

**macOS / Linux**

```bash
cp .env.example .env
```

**Windows PowerShell**

```powershell
Copy-Item .env.example .env
```

Then edit `.env`:

```text
OPENAI_API_KEY=your_api_key_here
```

`.env` is intentionally listed in `.gitignore`, so your secret API key should not be committed to GitHub.

You can also enter the key into the password field in the app sidebar instead of saving a `.env` file.

> OpenAI API usage is billed separately from a ChatGPT subscription. Review your API account billing and usage settings before running the application.

## Run the application

```bash
streamlit run app.py
```

Streamlit will open the app in your browser.

## Quick demo

A fictional employee handbook is included at:

```text
sample_docs/demo_handbook.txt
```

Upload it and try questions such as:

```text
How many PTO days do full-time employees receive?
What is the remote-work policy?
When are receipts required for expenses?
What security requirements apply to remote employees?
When do performance reviews happen?
```

## Run tests

```bash
pytest -q
```

Current local build result:

```text
13 passed
```

The tests do **not** require an OpenAI API call. The pipeline test injects fake embedding and text services so the retrieval architecture can be tested without network access or API cost.

## Supported file behavior

### PDF

Text is extracted page by page, allowing evidence labels such as:

```text
employee_handbook.pdf — page 7
```

Scanned/image-only PDFs are not OCR'd in this version.

### DOCX

Non-empty paragraphs are grouped while paragraph ranges are preserved as source locations.

### CSV

Rows are converted into readable `column: value` records in batches.

### XLSX

Each worksheet is read independently. Sheet names and row ranges are preserved in source labels.

### TXT

UTF-8 and common Windows text encodings are supported.

## Security and privacy considerations

This project includes several intentionally visible safety choices:

- The API key is never hard-coded in source control.
- `.env` and Streamlit secrets files are excluded through `.gitignore`.
- Uploaded document excerpts are HTML-escaped before custom HTML rendering.
- Document text is treated as **untrusted reference data** in model instructions to reduce prompt-injection risk.
- Unsupported file formats are rejected.
- Individual upload size is limited by application configuration.
- The model is instructed to say when the retrieved evidence is insufficient rather than fabricate an answer.

For a production deployment, additional controls would typically include authentication, malware scanning, encrypted persistent storage, tenant isolation, audit logging, rate limiting, and organization-specific data-retention policies.

## Design decisions

### Why use a simple NumPy vector index?

For a portfolio project, it makes the retrieval algorithm easy to explain in an interview. Every embedding is normalized and ranked through cosine similarity. A production system with millions of chunks could swap this component for pgvector, Pinecone, Qdrant, Elasticsearch, or another vector database without changing the rest of the application architecture.

### Why dependency injection?

`DocumentAssistant` accepts custom embedding and text services. That makes cloud integrations replaceable and allows the RAG pipeline to be tested without real API calls.

### Why preserve source metadata before chunking?

Citations are only useful if the system knows where retrieved text came from. Page, sheet, row, and paragraph metadata are preserved from ingestion through retrieval.

## Current limitations

- No OCR for scanned PDFs
- Vector index is in memory and resets when the Streamlit process restarts
- No user authentication or multi-tenant storage
- Summaries and comparisons cap the amount of text sent to the model to control context size
- Citation labels are generated from retrieval metadata rather than a formal academic citation style

These are deliberate boundaries for the portfolio version and natural extension points for a production version.

## Possible next steps

- Add OCR for image-based PDFs
- Persist vectors in PostgreSQL + pgvector
- Add user accounts and workspaces
- Add document-level permissions
- Add hybrid keyword + vector retrieval
- Add reranking
- Add evaluation datasets for retrieval quality
- Add Docker deployment
- Deploy to a cloud platform
- Add structured extraction for contracts, policies, or financial reports

## Resume-ready description

> Built a Python retrieval-augmented generation (RAG) application that ingests PDF, DOCX, spreadsheet, CSV, and text documents; performs embedding-based semantic retrieval; and generates evidence-grounded answers with source citations. Designed modular ingestion, retrieval, AI-service, and UI layers with automated pytest coverage and prompt-injection-aware controls.

## Official OpenAI references

- Responses API guide: https://developers.openai.com/api/docs/guides/migrate-to-responses
- Embeddings guide: https://developers.openai.com/api/docs/guides/embeddings
