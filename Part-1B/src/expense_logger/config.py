"""Named limits and settings, in one place."""

MODEL = "gemini-3.5-flash-lite"
API_HOST = "generativelanguage.googleapis.com"
TEMPERATURE = 0
RESPONSE_MIME_TYPE = "application/json"
TIMEOUT_SECONDS = 60
MAX_RETRIES = 3
RETRY_WAITS = (5, 15, 45)  # seconds before the first, second and third retry
MAX_TEXT_LENGTH = 1000
