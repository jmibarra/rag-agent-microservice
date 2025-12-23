from atlassian import Jira
from app.core.config import settings

class JiraService:
    def __init__(self):
        self.jira = None
        if settings.JIRA_URL and settings.JIRA_USERNAME and settings.JIRA_API_TOKEN:
            self.jira = Jira(
                url=settings.JIRA_URL,
                username=settings.JIRA_USERNAME,
                password=settings.JIRA_API_TOKEN
            )

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

jira_service = JiraService()
