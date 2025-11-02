# 🕵️‍♂️ URL-Analyzer

Author: Corentin COUSTY  
Repository: https://github.com/Kaldah/URL-Analyzer

---

## Overview

URL-Analyzer is a lightweight web application for detecting potentially malicious URLs. It exposes a simple HTTP API (POST `/analyze`) that takes a URL and returns a security assessment based on VirusTotal reputation data.

The backend is built with FastAPI, and a small static web page is provided to test URLs directly in the browser. The project is designed to be modular — future adapters (e.g., PhishTank, Google Safe Browsing) can easily be added.

---

## Key Features

- Simple HTTP API (JSON in/out)
- Integration with VirusTotal API v3
- Modular, extensible code structure
- Docker-ready with .env configuration
- Static HTML/JS UI for quick testing
- Command-line test script (`tests/test_api.py`)

---

## How It Works

1. The API exposes one endpoint: `POST /analyze`

	 Example input:

	 ```json
	 { "url": "http://example.com" }
	 ```

2. The backend:

	 - Sanitizes and validates the input URL
	 - Submits it to VirusTotal (`POST /api/v3/urls`)
	 - Polls the analysis status (`GET /api/v3/analyses/{id}`)
	 - Returns the final vote counts

	 Example response:

	 ```json
	 { "url": "http://example.com", "malicious_votes": 0, "harmless_votes": 71 }
	 ```

	 If analysis is still running:

	 ```json
	 { "detail": "Analysis still in progress, try again later." }
	 ```

	 → HTTP 202 Accepted

---

## API Specification

`POST /analyze`

Fields:

- `url` (string): URL to analyze

Response codes:

- 200 OK – Completed
- 202 Accepted – Pending analysis
- 500 – Invalid API key
- 502 – Network/upstream failure

> Note: If `VIRUS_TOTAL_API_KEY` is missing at startup, the app exits with a configuration warning and will not serve HTTP requests. With an invalid key present, the endpoint returns HTTP 500.

---

## Requirements

- Python 3.10+ (tested with 3.12)
- FastAPI, Uvicorn, httpx, python-dotenv
- A valid VirusTotal API key

---

## Environment Configuration

Create a `.env` file at project root:

```
VIRUS_TOTAL_API_KEY=your_api_key_here
```

Optionally:

```
DEVELOPMENT_ENV=1
```

Windows (PowerShell):

```powershell
Copy-Item .env.example .env
notepad .env
```

Linux/macOS:

```bash
cp .env.example .env
nano .env
```

---

## Running the Application

Local mode (recommended):

Windows (PowerShell):

```powershell
python -m venv .venv
\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Linux/macOS:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Then open http://localhost:8000

---

### Run with Docker

```bash
docker build -t url-analyzer .
docker run --rm -p 8000:8000 --env-file .env url-analyzer
```

Open http://localhost:8000

---

## Try it from the command line

Make sure the app is running locally on http://127.0.0.1:8000 (see steps above), then:

Windows (PowerShell):

```powershell
$Body = @{ url = "http://example.com" } | ConvertTo-Json
Invoke-RestMethod -Uri http://127.0.0.1:8000/analyze -Method POST -ContentType 'application/json' -Body $Body
```

Linux/macOS:

```bash
curl -s -X POST http://127.0.0.1:8000/analyze \
	-H 'Content-Type: application/json' \
	-d '{"url":"http://example.com"}'
```

If the analysis is still pending, the server will return HTTP 202. To see the status code with curl, add `-i`.

---

## Running the Tests

Start the app, then run:

```bash
python tests/test_api.py
```

Example output:

```
🔍 Running 2 tests against http://127.0.0.1:8000/analyze
🧪 Test #0 → http://example.com
✅ OK — within expected range
🧪 Test #1 → http://dfwdiesel.net
✅ OK — within expected range
```

Test data (`tests/data.json`):

```json
[
	{
		"test_number": 0,
		"url": "http://example.com",
		"expected_output": { "malicious_votes": 0, "harmless_votes": 71 }
	},
	{
		"test_number": 1,
		"url": "http://dfwdiesel.net",
		"expected_output": { "malicious_votes": 4, "harmless_votes": 63 }
	}
]
```

---

## Project Structure

```
URL-Analyzer/
├── app/
│   ├── main.py                 # FastAPI entrypoint
│   ├── models.py               # Pydantic schemas
│   ├── services/
│   │   └── virus_total.py      # VirusTotal adapter
│   ├── utils.py                # URL sanitization helpers
│   └── static/
│       ├── index.html          # Test UI
│       ├── script.js           # Frontend logic
│       └── style.css           # Styles for the UI
├── tests/
│   ├── data.json
│   └── test_api.py
├── .env.example
├── requirements.txt
├── Dockerfile
└── README.md
```

---

## Security Notes

- The service never fetches page content — only VirusTotal data.
- API keys are stored via environment variables, never in Git.
- Use `.env.example` for sharing configuration templates.

---

## Future Improvements

- Add caching (SQLite/Redis)
- Add new reputation adapters
- Add pytest-based automated tests
- Add CI/CD pipeline with GitHub Actions

---

## License

Released under the MIT License. See `LICENSE` for details.

---

Made with care by Corentin COUSTY

