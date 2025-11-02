## Tests README

This folder contains a tiny, live HTTP test that hits a running instance of the app and compares results against expected ranges. It’s a smoke test rather than a strict unit test because reputation votes change over time.

### What’s here

- `test_api.py` — simple runner that POSTs to `/analyze` and prints results with a tolerance check.
- `data.json` — test cases with input URLs and indicative expected votes. (Note that votes may change over time)

`data.json` shape:

```json
[
	{
		"test_number": 0,
		"url": "http://example.com",
		"expected_output": { "malicious_votes": 0, "harmless_votes": 71 }
	}
]
```

### Prerequisites

1) Start the app locally and ensure the VirusTotal API key is available. The easiest way is a `.env` file in the project root:

```pwsh
# Windows (PowerShell)
Copy-Item ..\.env.example ..\.env
notepad ..\.env   # set VIRUS_TOTAL_API_KEY, optionally DEVELOPMENT_ENV=1
python -m pip install -r ..\requirements.txt
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

```bash
# Linux/macOS
cp ../.env.example ../.env
${EDITOR:-nano} ../.env   # set VIRUS_TOTAL_API_KEY, optionally DEVELOPMENT_ENV=1
python -m pip install -r ../requirements.txt
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Alternatively with Docker from the project root:

```bash
docker build -t url-analyzer:local .
docker run --rm -p 8000:8000 --env-file .env url-analyzer:local
```

2) Internet access is required; the test uses the live VirusTotal API via the server.

### Run the tests

Make sure the server is already running on http://127.0.0.1:8000, then run:

```pwsh
# Windows (PowerShell)
python .\tests\test_api.py
```

```bash
# Linux/macOS
python ./tests/test_api.py
```

You can run `test_api.py` from the project root or from the `tests` folder — it finds `data.json` relative to its own file path, not the current working directory.

To target a different API endpoint, set the `URL_ANALYZER_API` environment variable, e.g.:

```pwsh
$env:URL_ANALYZER_API = "http://localhost:8001/analyze"
python .\tests\test_api.py
```

```bash
export URL_ANALYZER_API="http://localhost:8001/analyze"
python ./tests/test_api.py
```

The script prints each URL, the received JSON, and whether the votes are within a tolerance window:

- malicious_votes: ±2
- harmless_votes: ±10

This tolerance exists because reputation counts evolve.

### Configuration knobs

- Target URL: edit `API_URL` in `tests/test_api.py` if your server runs on a different host/port.
- Auth header: Not used. The app does not require a client API key header. Only the server needs a VirusTotal API key via environment variables (see prerequisites).

### Troubleshooting

- HTTP 500: `VIRUS_TOTAL_API_KEY` missing on the server. Ensure `.env` has the key and the server restarted.
- HTTP 202: Analysis pending at VirusTotal. Wait a few seconds and re-run the test.
- HTTP 429/Rate limits: Your VirusTotal plan may throttle requests. Add caching, slow down tests, or try later.
- Request failed: Networking/DNS issues. Verify internet access and that the server is reachable at the configured `API_URL`.

### Sources of sample URLs

Some test URLs were inspired by publicly discussed lists of risky domains (e.g., Norton’s historical "most dangerous websites"). These are used purely as inputs to reputation lookups — the service does not fetch or execute site content.

— Tests maintained by Corentin COUSTY

