import app.helpers.useful_date_functions as udf
import app.helpers.useful_jira_functions as ujf
from app.models.portfolio import Portfolio


class PortfolioObjectBuilder(object):

    def __init__(self, jira_connection, jql_query):
        self.jira_connection = jira_connection
        self.jql_query = jql_query

    def get_portfolio_list(self):
        portfolio_list = []
        issues = self.jira_connection.search_issues(self.jql_query, expand='changelog', maxResults=1000)
        if not issues:
            return []
        else:
            for issue in issues:
                portfolio_list.append(self.build_portfolio_from_issue_data(issue))
        return portfolio_list

    def build_portfolio_from_issue_data(self, issue):
        issue_assignee = str(issue.fields.assignee)
        issue_assignee_avatar = str(issue.fields.assignee.raw['avatarUrls']['16x16'])
        issue_dev_team = str(issue.fields.customfield_10961)
        issue_number = str(issue.key)
        issue_summary = issue.fields.summary

        issue_duedate = None
        if issue.fields.duedate:
            issue_duedate = udf.get_date_obj_from_str(issue.fields.duedate)

        issue_inwork_date = ujf.get_issue_to_status_date(issue, "Разработка: в работе")

        issue_sp_estimate = issue.fields.customfield_11212 if issue.fields.customfield_11212 else None

        linked_issues = None
        if ujf.has_linked_issues(issue):
            linked_issues = ujf.get_portfolio_included_issues_stats(self.jira_connection, issue)

        issue_is_blocked = ujf.is_issue_blocked(issue)

        issue_blocking_date = None
        if issue_is_blocked:
            issue_blocking_date = ujf.get_issue_last_blocking_date(issue)

        issue_status = str(issue.fields.status)

        return Portfolio(assignee=issue_assignee,
                         assignee_avatar=issue_assignee_avatar,
                         dev_team=issue_dev_team,
                         key=issue_number,
                         summary=issue_summary,
                         inwork_date=issue_inwork_date,
                         duedate=issue_duedate,
                         blocking_date=issue_blocking_date,
                         sp_estimate=issue_sp_estimate,
                         linked_issues=linked_issues,
                         is_blocked=issue_is_blocked,
                         status=issue_status)
