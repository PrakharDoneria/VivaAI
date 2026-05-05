import json
from models.analytics import get_analytics_data

try:
    data = get_analytics_data()
    print(json.dumps(data, indent=2))
except Exception as e:
    print(f"Error: {e}")
