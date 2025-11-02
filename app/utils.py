from urllib.parse import urlparse
import os

def sanitize_url(url: str) -> str:
    """Sanitize the input URL to ensure it's in a proper format.
    Args:
        url (str): The URL to sanitize.
    Returns:
        str: The sanitized URL.
    """
    parsed = urlparse(str(url).strip())
    return f"{parsed.scheme}://{parsed.netloc}{parsed.path}"

def debug_print(message: str):
    """Print debug messages if in development environment.
    Args:
        message (str): The debug message to print.
    """
    # Check if in development environment
    if os.getenv("DEVELOPMENT_ENV", False) in [True, "True", "true", "1"]:
        print(f"[DEBUG] {message}")