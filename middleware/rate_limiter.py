from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

# Initialize limiter (to be attached to app)
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"],
    storage_uri="memory://"
)

# Rate limit presets
AI_RATE_LIMIT = "10 per minute"      # AI endpoints: 10 requests/minute
REPORT_RATE_LIMIT = "30 per minute"  # Report endpoints: 30 requests/minute
CREATE_RATE_LIMIT = "5 per minute"   # Create interview: 5 requests/minute