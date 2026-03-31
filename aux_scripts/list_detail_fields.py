import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.config import settings
from app.services.jsm_auth_manager import jsm_auth_manager
import requests

def list_detail_fields():
    access_token = jsm_auth_manager.get_valid_token()
    if not access_token:
        print("No valid JSM access token available.")
        return
        
    url = f"https://api.atlassian.com/jsm/csm/cloudid/{settings.JSM_CLOUD_ID}/api/v1/customer/details"
    print(url)
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Accept": "application/json"
    }
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        import json
        print(json.dumps(response.json(), indent=4, ensure_ascii=False))
    except Exception as e:
        print(f"Error: {e}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"Details: {e.response.text}")

if __name__ == "__main__":
    list_detail_fields()
