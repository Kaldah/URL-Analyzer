# URL-Analyzer

Built by Corentin COUSTY

URL-Analyzer is a lightweight web service for detecting potentially malicious URLs. It exposes a simple HTTP API (POST /analyze) that accepts a URL and returns a risk assessment summary from reputation sources (currently VirusTotal; more adapters can be added).

This repository contains a minimal FastAPI implementation with a static test UI and examples for integration with SOC, SIEMs, and automation tooling. The code is modular so reputation sources and analyzers can be added or replaced easily.

## Key features

- HTTP-based URL analysis with JSON input/output
- Aggregates results from multiple reputation sources (malicious/harmless votes)
- Small, modular codebase intended for automation and SIEM integration
- Clear JSON contract for easy programmatic use

## API

POST /analyze

Request (application/json):

{
	"url": "http://example.com"
}

Response (application/json):

{
	"url": "http://example.com",
	"malicious_votes": 2,
	"harmless_votes": 85,
	"score": 0.02,
	"sources": [
		{ "name": "VirusTotal", "malicious": 1, "harmless": 10 },
		{ "name": "PhishTank", "malicious": 1, "harmless": 75 }
	]
}

Fields:
- `url` — the analyzed URL (echoed back)
- `malicious_votes` — aggregated count of malicious votes across configured sources
- `harmless_votes` — aggregated count of harmless/benign votes across sources
- `score` — normalized risk score (malicious_votes / (malicious_votes + harmless_votes)) when votes exist, otherwise 0
- `sources` — optional per-source breakdown (helpful for triage and auditing)

Notes:
- The exact keys returned may vary depending on enabled adapters. The above contract is the recommended normalized shape for consumers.
- In the current POC, the backend returns `url`, `malicious_votes`, `harmless_votes` (no `score` yet). The frontend hides `score` when absent.

Status codes:
- `200 OK` — analysis completed; response includes votes (may be `0/0` when no votes yet)
- `202 Accepted` — analysis still pending upstream; try again shortly
- `500` — server not configured correctly (missing `VIRUS_TOTAL_API_KEY`)
- `502` — upstream/network error contacting VirusTotal

## Requirements

- Python 3.10+ (tested with 3.12)
- A VirusTotal API key

## How to run

Set your VirusTotal API key as an environment variable `VIRUS_TOTAL_API_KEY`.

### Using a .env file (recommended)

An example env file is provided. Copy it and fill in your values:

```pwsh
# Windows (PowerShell)
Copy-Item .env.example .env
notepad .env   # edit VIRUS_TOTAL_API_KEY, optionally DEVELOPMENT_ENV
```

```bash
# Linux/macOS
cp .env.example .env
${EDITOR:-nano} .env   # edit VIRUS_TOTAL_API_KEY, optionally DEVELOPMENT_ENV
```

The app automatically loads `.env` via python-dotenv on startup, so you don’t need to export variables manually if `.env` exists.

### Create a virtual environment (clean install)

Windows (PowerShell):

```pwsh
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

Linux/macOS:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

### Windows (PowerShell)

```pwsh
# from project root
$env:VIRUS_TOTAL_API_KEY = "<your_api_key>"
# optional for verbose logs
$env:DEVELOPMENT_ENV = "1"
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Linux/macOS (bash/zsh)

```bash
# from project root
export VIRUS_TOTAL_API_KEY="<your_api_key>"
# optional for verbose logs
export DEVELOPMENT_ENV=1
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Docker

```bash
# build
docker build -t url-analyzer:local .

# run (exposes http://localhost:8000)
docker run --rm -p 8000:8000 \
  -e VIRUS_TOTAL_API_KEY="<your_api_key>" \
  url-analyzer:local
```

Alternatively, pass your local `.env` directly:

```bash
docker run --rm -p 8000:8000 --env-file .env url-analyzer:local
```

Open http://localhost:8000/ to access the test UI.

### Quick API calls

Use curl or PowerShell to POST a URL to the service. Replace <HOST> with your service host (e.g., http://localhost:8000).

PowerShell (recommended on Windows):

```pwsh
Invoke-RestMethod -Method POST -Uri "http://<HOST>/analyze" -ContentType "application/json" -Body (@{ url = 'http://example.com' } | ConvertTo-Json)
```

curl (Linux/macOS/WSL/PowerShell alias):

```bash
curl -X POST "http://<HOST>/analyze" -H "Content-Type: application/json" -d '{"url":"http://example.com"}'
```

Example response (shape may vary):

```json
{
  "url": "http://example.com",
  "malicious_votes": 2,
  "harmless_votes": 85
}
```

Note: If the server returns `202 Accepted`, the analysis is still processing at VirusTotal. Retry after a few seconds — the web UI shows a pending banner with a Retry button.

## How it works (quickly)

- The FastAPI app exposes `POST /analyze`.
- The VirusTotal adapter (`app/services/virus_total.py`) submits the URL for analysis, then polls the analysis endpoint. If status becomes `completed`, it returns the votes (even `0/0`). If still `queued/running` after several attempts, it returns `202` to indicate pending.
- The result returns a normalized shape: `{ url, malicious_votes, harmless_votes }`.
- The static page (`/`) lets you try URLs and renders the JSON result.

Future adapters (e.g., PhishTank, Google Safe Browsing) can be added following the same interface and aggregated into totals.

## Integration notes

- Aggregation: The service aggregates vote counts from configured reputation adapters and returns both totals and a per-source breakdown for triage.
- Extensibility: Add new reputation adapters as separate modules that implement a simple interface (query(url) -> {malicious, harmless, raw}).
- Caching: For production use, enable result caching to reduce API calls to external reputation providers and improve throughput.
- Rate limiting & API keys: Configure per-source API keys and rate limits; fail gracefully when a source is unavailable and still return partial results.

## Security considerations

- Treat the input URL as untrusted. If the service dereferences URLs (fetches the content), enforce strict timeouts and avoid executing any returned content.
- Store third-party API keys securely (environment variables or secret store), not in source control.

## Contributing

Contributions are welcome. Suggested small improvements:

- Add new reputation adapters (VirusTotal, PhishTank, Google Safe Browsing, etc.)
- Add tests for the adapter interface and aggregation logic
- Add docker-compose or deployment manifests for common environments

Please open issues or PRs with clear descriptions and small, focused changes.

## Running the tests

The test runner in `tests/test_api.py` sends HTTP requests to a running server. Start the app first (see above), then in another terminal:

### Windows (PowerShell)

```pwsh
python .\tests\test_api.py
```

### Linux/macOS

```bash
python ./tests/test_api.py
```

Notes:
- Tests require the `VIRUS_TOTAL_API_KEY` to be set in the server's environment.
- The script compares vote counts within a tolerance (these numbers vary over time).

## License

This project is provided under the MIT License. See LICENSE file for details.

---

Made with care by Corentin COUSTY.

