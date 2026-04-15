import requests
from requests.auth import HTTPBasicAuth
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app.core.config import settings

url = f"{settings.JIRA_URL}/rest/servicedeskapi/servicedesk/2/requesttype/26/field"
headers = {
    "Accept": "application/json"
}

response = requests.get(
    url,
    headers=headers,
    auth=HTTPBasicAuth(settings.JIRA_USERNAME, settings.JIRA_API_TOKEN)
)

if response.status_code == 200:
    for field in response.json().get('requestTypeFields', []):
        print(f"Name: {field.get('name')}, FieldId: {field.get('fieldId')}, Required: {field.get('required')}")
        if 'validValues' in field:
            print(f"  Valid values: {[v.get('value') for v in field['validValues']]}")
else:
    print(f"Error {response.status_code}: {response.text}")

