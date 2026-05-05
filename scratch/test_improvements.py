import sys
import os
import json

# Add project root to path
sys.path.append(r'c:\Users\Aiswarya\Downloads\VivaAI')

from models.analytics import get_analytics_data

try:
    data = get_analytics_data()
    print("Improvements:")
    print(json.dumps(data['improvements'], indent=2))
except Exception as e:
    print(f"Error: {e}")
