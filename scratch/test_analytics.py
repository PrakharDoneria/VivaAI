import sys
import os
import json

# Add project root to path
sys.path.append(r'c:\Users\Aiswarya\Downloads\VivaAI')

from models.analytics import get_analytics_data

try:
    data = get_analytics_data()
    print("Analytics Data Summary:")
    print(json.dumps(data['summary'], indent=2))
    print("\nSkill Averages:")
    print(json.dumps(data['skill_averages'], indent=2))
    print("\nHistory (last entry):")
    if data['history']:
        print(json.dumps(data['history'][0], indent=2))
    else:
        print("No history found.")
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
