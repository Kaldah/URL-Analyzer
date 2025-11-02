from pydantic import BaseModel, HttpUrl

# Request model for URL analysis
class URLRequest(BaseModel):
    url: HttpUrl

# Response model for URL analysis results
class URLResponse(BaseModel):
    url: str
    malicious_votes: int
    harmless_votes: int
