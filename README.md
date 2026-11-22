# CloudServe Intelligent Support System

A provider-independent customer-support pipeline for CloudServe Solutions.

It combines:

- TF-IDF intent classification for 22 intent categories
- TF-IDF RAG retrieval over the 29 supplied documentation articles
- LangChain prompt templates
- LangGraph state orchestration
- Optional OpenRouter generation with a deterministic grounded fallback
- Hard routing policies and guardrails
- Persistent SQLite decision logging
- An unattended evaluation harness with external input and output paths

## Requirements

- Windows, macOS or Linux
- Python 3.10 or later
- Internet access only if optional OpenRouter generation is enabled

No API key or external model service is required for tests or the standard evaluation harness.

## Clean-checkout setup

```powershell
cd cloudserve-support
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
Copy-Item .env.example .env
```

For macOS or Linux, activate the environment with:

```bash
source .venv/bin/activate
```

The `.env` file is ignored by Git. `.env.example` contains placeholders only.

## Configuration

Environment settings include:

```dotenv
OPENROUTER_API_KEY=your_key_here
MODEL_NAME=meta-llama/llama-3.1-8b-instruct:free
MODEL_TIMEOUT_SECONDS=20
CONFIDENCE_THRESHOLD=0.30
RETRIEVAL_THRESHOLD=0.05
DATABASE_URL=sqlite:///./storage/decisions.db
LOG_LEVEL=INFO
```

A placeholder key or no key uses the deterministic grounded fallback. OpenRouter is optional and must never be a gate for the validation harness.

## Run tests

```powershell
python -m pytest tests -v
```

The suite includes:

- Four-channel ingestion
- ML classifier structure and training
- Deterministic routing
- Protected security escalation
- Private-data and invented-citation guardrails
- TF-IDF RAG retrieval
- LangChain grounding and escalation prompt formatting

## Run the API

```powershell
python -m uvicorn src.api:app --host 127.0.0.1 --port 8000
```

Health endpoint:

```text
http://127.0.0.1:8000/health
```

Process endpoint:

```text
POST http://127.0.0.1:8000/process
```

## RAG implementation

The retriever chunks the 29 Markdown support articles and builds an in-memory TF-IDF vector model.

Each result contains:

- Real `doc_id`
- Article title
- Supporting passage
- Relevance score

A no-hit result escalates rather than generating a response from unsupported knowledge.

## LangChain and LangGraph

LangChain prompt templates define grounded answer and escalation instructions.

LangGraph defines the pipeline state and component flow:

```text
ingest -> classify -> retrieve -> route -> generate -> validate -> finalize
```

The LangGraph implementation is available in `src/langgraph_pipeline.py`.
The current FastAPI/harness process uses the equivalent tested Python pipeline; routing and guardrails remain deterministic outside the language model.

## Held-out calibration

Run calibration against a stratified holdout from the development tickets:

```powershell
python -m evaluation.calibrate
```

This produces:

```text
evaluation/results/calibration.json
```

The report contains confidence bands, stated versus observed accuracy and development holdout routing thresholds.
The threshold in `.env.example` is a development holdout starting point, not a claim of hidden-set calibration.

## Run the full unattended evaluation

```powershell
python -m evaluation.harness --input data/validation_tickets.json --output evaluation/results/validation
```

The command accepts arbitrary input and output paths.
It processes every ticket once and writes:

- `evaluation/results/validation/ticket_results.json`
- `evaluation/results/validation/metrics.json`

It produces volume, business, technical and governance figures.
The metrics report explicitly records hidden-set and human-review status.

## Human citation and hallucination review

The repository includes:

```text
evaluation/human_review_template.csv
evaluation/limitations.md
```

Before deployment, use two independent assessors to review at least fifty generated responses.
The final report must not claim a hallucination or semantic citation rate until those reviews are completed.

## Hidden-set limitation

The hidden evaluation set is not included in this repository.
Do not tune against hidden data.
When the final hidden set becomes available, run the harness once, record the date and system version, and report the result honestly.

## Repository layout

```text
src/                     application components
prompts/                 versioned prompt specifications
tests/                   automated tests
evaluation/              calibration, harness and evaluation reports
data/                    supplied project datasets
docs/                    architecture documentation
.github/workflows/       continuous integration
.env.example             placeholder environment template
requirements.txt         pinned Python dependencies
```

## Safety behavior

Protected or low-confidence tickets escalate.
Every generated response is checked for private data and unsupported commitments.
Citations must resolve to real retrieved passages.
Every decision is written to SQLite and reconciled against processed tickets.
