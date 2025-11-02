from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from app.models import URLRequest, URLResponse
from app.services.virus_total import analyze_url
from dotenv import load_dotenv
from app.utils import debug_print
import os

# Load environment variables from .env file from the root directory
load_dotenv()

# Get the VirusTotal API key from environment variables
VT_API_KEY = os.getenv("VIRUS_TOTAL_API_KEY")
DEVELOPMENT_ENV = os.getenv("DEVELOPMENT_ENV", False)

print("🚀 URL-Analyzer starting — built by Corentin COUSTY")

# Checking for the VirusTotal API key
if not VT_API_KEY:
    print("⚠️ Warning: VIRUS_TOTAL_API_KEY not found in environment! It is required for the application to function.")
    exit(1)
else:
    debug_print(f"✅ VIRUS_TOTAL_API_KEY loaded successfully: {VT_API_KEY[:4]}****")

debug_print("⚙️ Running in development environment.")
debug_print("Debugging features enabled.")

# Initialize FastAPI application
app = FastAPI(title="URL Analyzer")

# Mount static files for serving frontend assets of the application
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# Endpoint to analyze a given URL
@app.post("/analyze", response_model=URLResponse)
async def analyze(request: Request, payload: URLRequest):
    return await analyze_url(payload.url)

# Endpoint to serve the homepage
@app.get("/", response_class=HTMLResponse)
async def home():
    return FileResponse("app/static/index.html")
