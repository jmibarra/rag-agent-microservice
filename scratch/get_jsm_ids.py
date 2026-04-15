from atlassian import ServiceDesk
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.config import settings

sd = ServiceDesk(
    url=settings.JIRA_URL,
    username=settings.JIRA_USERNAME,
    password=settings.JIRA_API_TOKEN
)

print("--- Service Desks ---")
try:
    desks = sd.get_service_desks()
    # desks is a list in atlassian-python-api or a dict depending on the method. Let's see:
    if isinstance(desks, dict):
        elements = desks.get('values', [])
    else:
        elements = desks
    
    for d in elements:
        print(f"ID: {d['id']} - Name: {d['projectName']} - Key: {d['projectKey']}")
        if d['projectKey'] == 'SOP':
            print(f"> Found SOP! ID is {d['id']}")
            print("--- Request Types for SOP ---")
            types = sd.get_request_types(d['id'])
            for t in types.get('values', []):
                print(f"  ReqType ID: {t['id']} - Name: {t['name']}")
                if t['id'] == '26' or t['id'] == 26:
                    print("    --- Fields for Consulta ---")
                    try:
                        fields = sd.get_request_type_fields(d['id'], t['id'])
                        for f in fields.get('requestTypeFields', []):
                            print(f"      Field: {f['fieldId']} (Required: {f['required']})")
                    except Exception as e:
                        print(f"      Error getting fields: {e}")
except Exception as e:
    print(f"Error: {e}")
