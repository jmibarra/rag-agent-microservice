import requests
from requests.auth import HTTPBasicAuth
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app.core.config import settings

url = f"{settings.JIRA_URL}/rest/servicedeskapi/request"
headers = {
    "Accept": "application/json",
    "Content-Type": "application/json"
}
auth = HTTPBasicAuth(settings.JIRA_USERNAME, settings.JIRA_API_TOKEN)

formats_to_test = [
    {"customfield_10066": {"id": "10024"}},
    {"customfield_10066": {"value": "Agilis - Fics"}},
    {"customfield_10066": "10024"},
    {"customfield_10066": "Agilis - Fics"},
    {"customfield_10066": [{"id": "10024"}]},
    {"customfield_10066": [{"value": "Agilis - Fics"}]}
]

for idx, f in enumerate(formats_to_test):
    payload = {
        "serviceDeskId": "2",
        "requestTypeId": "26",
        "requestFieldValues": {
            "summary": f"Test Format {idx}",
            "description": "Testing formats",
            **f
        }
    }
    
    print(f"Testing format {f}...")
    try:
        response = requests.post(url, headers=headers, json=payload, auth=auth)
        if response.status_code == 201:
            print(f"SUCCESS with format: {f}")
            break
        else:
            print(f"Failed ({response.status_code}): {response.json().get('errorMessage')}")
    except Exception as e:
        print(f"Error: {e}")

