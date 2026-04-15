from requests.models import HTTPBasicAuth
import requests
from atlassian import Jira
from app.core.config import settings
from app.services.jsm_auth_manager import jsm_auth_manager


class JiraService:
    def __init__(self):
        self.jira = None
        if settings.JIRA_URL and settings.JIRA_USERNAME and settings.JIRA_API_TOKEN:
            self.jira = Jira(
                url=settings.JIRA_URL,
                username=settings.JIRA_USERNAME,
                password=settings.JIRA_API_TOKEN,
            )

    def get_issue_details_filtered(self, issue_key: str, customer_context: dict):
        if not self.jira:
            return None

        project_key = issue_key.split("-")[0]
        if project_key not in settings.JIRA_ALLOWED_PROJECTS:
            return None

        if customer_context is None:
            return None

        try:
            customer = self.get_customer_by_id(customer_context.get("id"))

            if customer is None:
                return None

            organizations = customer.get("organizations", [])

            print(
                f"issue: {issue_key}, reporter: {customer_context.get('email')}, request_participants: {customer.get('id')}, organizations: {organizations}"
            )

            if len(organizations) == 0:
                return None

            organization = organizations[0]

            print(organization)

            issue = self.get_issue_details_by_reporter_or_rp_or_organization(
                issue_key=issue_key,
                reporter=customer.get("email"),
                request_participants=customer.get("id"),
                organization=organization.get("name"),
            )

            if issue is None:
                return None

            print(issue)

            last_comment = self.get_last_public_comment_by_key(issue_key)

            if last_comment is None:
                return None

            print(last_comment)

            return (
                f"Jira Ticket {issue_key}: {issue['summary']}\n"
                f"Status: {issue['status']}\n"
                f"Last public comment: {last_comment}"
            )
        except Exception as e:
            print(f"Error fetching Jira issue {issue_key}: {e}")
            return None

    def get_issue_details_by_reporter_or_rp_or_organization(
        self,
        issue_key: str,
        reporter: str,
        request_participants: str,
        organization: str,
    ) -> str | None:
        if not self.jira:
            return None

        project_key = issue_key.split("-")[0]
        if project_key not in settings.JIRA_ALLOWED_PROJECTS:
            return None

        try:
            jql_str = f'key = "{issue_key}" AND (reporter = "{reporter}" OR "Request participants" = "{request_participants}" OR organization = "{organization}")'

            url = f"{settings.JIRA_URL.rstrip('/')}/rest/api/3/search/jql"
            params = {
                "jql": jql_str,
                "maxResults": 1,
                "fields": "summary,status",
            }

            headers = {"Accept": "application/json", "Content-Type": "application/json"}

            try:
                response = requests.get(
                    url,
                    params=params,
                    headers=headers,
                    auth=HTTPBasicAuth(settings.JIRA_USERNAME, settings.JIRA_API_TOKEN),
                    timeout=10,
                )

                response.raise_for_status()
                data = response.json()

                issues = data.get("issues", [])

                if not issues:
                    print(f"No se encontró el issue {issue_key}")
                    return None

                issue = issues[0]

                summary = issue["fields"]["summary"]
                status = issue["fields"]["status"]["name"]

                return {
                    "summary": summary,
                    "status": status,
                }
            except Exception as e:
                print(f"Error fetching Jira issue {issue_key}: {e}")
                return None
        except Exception as e:
            print(f"Error fetching Jira issue {issue_key}: {e}")
            return None

    def get_last_public_comment_by_key(self, key: str) -> str | None:
        if not self.jira:
            return None

        project_key = key.split("-")[0]
        if project_key not in settings.JIRA_ALLOWED_PROJECTS:
            return None

        try:
            url = f"{settings.JIRA_URL.rstrip('/')}/rest/servicedeskapi/request/{key}/comment"
            headers = {"Accept": "application/json", "Content-Type": "application/json"}

            response = requests.get(
                url,
                headers=headers,
                auth=HTTPBasicAuth(settings.JIRA_USERNAME, settings.JIRA_API_TOKEN),
                timeout=10,
            )

            response.raise_for_status()
            data = response.json()

            # print(data)

            comments = data.get("values", [])
            public_comments = [c for c in comments if c.get("public") == True]
            last_comment = "No public comments"
            if public_comments:
                last_comment = public_comments[-1]["body"]

            return last_comment
        except Exception as e:
            print(f"Error fetching Jira issue {key}: {e}")
            return None

    def get_issue_details(self, issue_key: str) -> str | None:
        """
        Fetches issue details if the project is allowed.
        Returns a formatted string or None if not found/not allowed.
        """
        if not self.jira:
            return None

        # Validation: Check allowed projects
        project_key = issue_key.split("-")[0]
        if project_key not in settings.JIRA_ALLOWED_PROJECTS:
            return None

        try:
            issue = self.jira.issue(issue_key, fields="summary,status,comment")

            print(f"Issue: {issue}")

            summary = issue["fields"]["summary"]
            status = issue["fields"]["status"]["name"]

            comments = issue["fields"].get("comment", {}).get("comments", [])
            last_comment = "No public comments"
            if comments:
                last_comment = comments[-1]["body"]

            return (
                f"Jira Ticket {issue_key}: {summary}\n"
                f"Status: {status}\n"
                f"Last public comment: {last_comment}"
            )
        except Exception as e:
            print(f"Error fetching Jira issue {issue_key}: {e}")
            return None

    def get_customer_by_id(self, customerId: str) -> dict | None:
        if not settings.JSM_CLOUD_ID:
            print("JSM Cloud ID not configured.")
            return None

        access_token = jsm_auth_manager.get_valid_token()
        if not access_token:
            print("No valid JSM access token available.")
            return None

        url = f"https://api.atlassian.com/jsm/csm/cloudid/{settings.JSM_CLOUD_ID}/api/v1/customer/{customerId}"
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Accept": "application/json",
            "Content-Type": "application/json",
        }

        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error fetching JSM customer by ID {customerId}: {e}")
            if hasattr(e, "response") and e.response is not None:
                print(f"Response details: {e.response.text}")
            return None

    def get_customer_by_detail_field(
        self, field_name: str, field_value: str
    ) -> dict | None:
        """
        Fetches a customer using the Jira Service Management CSM API
        based on a specific detail field.
        """
        if not settings.JSM_CLOUD_ID:
            print("JSM Cloud ID not configured.")
            return None

        access_token = jsm_auth_manager.get_valid_token()
        if not access_token:
            print("No valid JSM access token available.")
            return None

        url = f"https://api.atlassian.com/jsm/csm/cloudid/{settings.JSM_CLOUD_ID}/api/v1/customer/search-by-detail-field"
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Accept": "application/json",
            "Content-Type": "application/json",
        }
        payload = {"detailFields": [{"name": field_name, "value": field_value}]}

        try:
            response = requests.post(url, headers=headers, json=payload)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(
                f"Error fetching JSM customer by field {field_name}={field_value}: {e}"
            )
            if hasattr(e, "response") and e.response is not None:
                print(f"Response details: {e.response.text}")
            return None

    def create_customer_request(self, summary: str, description: str, producto_id: str, customer_id: str = None) -> str:
        """
        Creates a customer request in the 'SOP' project (ServiceDeskId=2) with RequestType 'Consultas' (RequestTypeId=26).
        """
        if not settings.JIRA_URL or not settings.JIRA_USERNAME or not settings.JIRA_API_TOKEN:
            return "Error: Jira credentials are not configured."

        url = f"{settings.JIRA_URL}/rest/servicedeskapi/request"
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json"
        }
        
        payload = {
            "serviceDeskId": "2",
            "requestTypeId": "26",
            "requestFieldValues": {
                "summary": summary,
                "description": description,
                "customfield_10066": [{"id": producto_id}]
            }
        }
        
        if customer_id:
            payload["raiseOnBehalfOf"] = customer_id
            
        try:
            response = requests.post(
                url,
                headers=headers,
                json=payload,
                auth=(settings.JIRA_USERNAME, settings.JIRA_API_TOKEN)
            )
            response.raise_for_status()
            data = response.json()
            issue_key = data.get("issueKey", "Unknown Key")
            return f"Ticket creado exitosamente: {issue_key}"
        except requests.exceptions.RequestException as e:
            error_msg = str(e)
            if hasattr(e, 'response') and e.response is not None:
                error_msg += f". Response details: {e.response.text}"
            print(f"Error creating customer request: {error_msg}")
            return f"Error al crear el ticket en Jira: {error_msg}"

jira_service = JiraService()
