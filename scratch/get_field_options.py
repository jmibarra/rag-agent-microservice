import requests
from requests.auth import HTTPBasicAuth
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app.core.config import settings

headers = {"Accept": "application/json"}
auth = HTTPBasicAuth(settings.JIRA_USERNAME, settings.JIRA_API_TOKEN)

options = ['10026', '10024', '10031', '10346', '10025', '10028', '10027', '10029', '10030', '10032', '10034', '10033']
for opt in options:
    url = f"{settings.JIRA_URL}/rest/api/3/customFieldOption/{opt}"
    response = requests.get(url, headers=headers, auth=auth)
    if response.status_code == 200:
        print(f"Option {opt}: {response.json().get('value')}")
