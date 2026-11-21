# CloudServe Intelligent Support System

## Requirements
- Windows, macOS or Linux
- Python 3.10 or later

## Setup from a clean checkout

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
Copy-Item .env.example .env
```

The supplied provider key is not included. The system does not require a key for the deterministic development harness, so `.env` may retain placeholder values.

## Run the API

```powershell
python -m uvicorn src.api:app --host 127.0.0.1 --port 8000
```

Health: `http://127.0.0.1:8000/health`

The API and unattended harness do not require a UI. The harness is the primary submission interface and must accept external input and output paths.

## Run the full unattended evaluation

```powershell
python -m evaluation.harness --input data/validation_tickets.json --output evaluation/results/validation
```

The command accepts arbitrary input and output paths. The supplied validation set, or the hidden assessment set, can replace `--input`. One run processes every ticket and writes:

- `ticket_results.json`
- `metrics.json`

## Run tests

```powershell
python -m pytest tests -v
```

## Repository layout

- `src/`: ingest, classifier, retrieval, routing, generation, guardrails and decision log
- `prompts/`: versioned prompt specifications
- `evaluation/harness.py`: unattended input/output harness
- `tests/`: unit and integration tests
- `data/`: supplied project datasets
- `storage/`: runtime SQLite and generated data; excluded from Git

## Safety behavior

The system escalates protected classes, no-retrieval cases and low-confidence cases. It blocks private data, unsupported commitments and invented citations. Every automated decision is written to SQLite.
