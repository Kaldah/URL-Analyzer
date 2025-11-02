import httpx, base64, os, asyncio
from fastapi import HTTPException
from app.utils import sanitize_url
from app.utils import debug_print


async def analyze_url(url: str):
    """Analyze a URL using the VirusTotal API.
    Args:
        url (str): The URL to analyze.
    """
    VT_API_KEY = os.getenv("VIRUS_TOTAL_API_KEY")
    if not VT_API_KEY:
        debug_print("⚠️ VIRUS_TOTAL_API_KEY not set in environment!")
        raise HTTPException(status_code=500, detail="VIRUS_TOTAL_API_KEY not set")
    # Sanitize the URL
    clean_url = sanitize_url(url)
    # Prepare headers for VirusTotal API requests
    headers = {
        "x-apikey": VT_API_KEY,
        "accept": "application/json",
    }

    try:
        # We use an async HTTP client
        async with httpx.AsyncClient(timeout=30) as client:
            # Submit the URL for analysis
            resp = await client.post(
                "https://www.virustotal.com/api/v3/urls",
                headers=headers,
                data={"url": clean_url},
            )
            # Check for submission errors
            if resp.status_code not in (200, 201):
                raise HTTPException(status_code=resp.status_code, detail=f"VT POST error: {resp.text}")

            # Extract the analysis ID
            analysis_id = resp.json()["data"]["id"]

            # Poll VirusTotal until analysis completes or max attempts reached
            # Distinguish between a pending analysis vs. a completed analysis with 0 votes
            max_attempts = 10
            last_status = None
            for attempt in range(max_attempts):
                # Get the analysis report
                report = await client.get(
                    f"https://www.virustotal.com/api/v3/analyses/{analysis_id}",
                    headers=headers,
                )
                # Check for report retrieval errors
                if report.status_code != 200:
                    raise HTTPException(status_code=report.status_code, detail=f"VT GET error: {report.text}")
                # Parse the report status and stats
                attrs = report.json().get("data", {}).get("attributes", {})
                last_status = attrs.get("status")  # queued | running | completed | failed
                stats = attrs.get("stats", {})
                malicious_votes = stats.get("malicious", 0)
                harmless_votes = stats.get("harmless", 0)

                debug_print(
                    f"Attempt {attempt+1}/{max_attempts} for {clean_url}: status={last_status}, stats={stats}"
                )

                # If analysis completed, return the votes
                if last_status == "completed":
                    return {
                        "url": clean_url,
                        "malicious_votes": malicious_votes,
                        "harmless_votes": harmless_votes,
                    }

                # If not completed yet, wait before next attempt - progressive backoff
                if attempt < max_attempts - 1:
                    delay = 1 if attempt < 3 else 4 if attempt < 8 else 8
                    await asyncio.sleep(delay)

        # If we exit the loop and analysis is still not completed, indicate it's pending
        debug_print(
            f"Analysis for {clean_url} still pending after {max_attempts} attempts (last_status={last_status})."
        )
        # 202 Accepted conveys that processing is still in progress
        # We should inform the user to try again later
        raise HTTPException(status_code=202, detail="Analysis pending. Try again shortly, server is busy.")
    # If we reach here, it means the analysis failed because of a request error
    except httpx.RequestError as e:
        raise HTTPException(status_code=502, detail=f"VirusTotal request failed, service may be down: {e}")
