import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app.services.jira_service import jira_service

res = jira_service.create_customer_request("Test Issue", "Testing creation with id 10024", producto_id="10024")
print(res)
