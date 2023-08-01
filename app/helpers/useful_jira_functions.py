import app.helpers.useful_date_functions as udf
from jira import JIRAError


def get_issue_to_status_date(issue, status):
    for history in reversed(issue.changelog.histories):
        for item in history.items:
            if item.field == 'status' and item.toString == str(status):
                return udf.get_date_obj_from_str(history.created)
    return None


def get_issue_last_blocking_date(issue):
    for history in reversed(issue.changelog.histories):
        for item in history.items:
            if item.field == 'Flagged' and item.toString == 'Impediment':
                return udf.get_date_obj_from_str(history.created)
    return None


def has_linked_issues(portfolio):
    result = False
    portfolio_issuelinks = portfolio.raw['fields']['issuelinks']
    if portfolio_issuelinks:
        for item in portfolio_issuelinks:
            if item['type']['outward'] == 'includes' and 'inwardIssue' not in item.keys():
                result = True
                break
    return result


def get_portfolio_included_issues(jira_connection, portfolio):
    linked_issues_jql = 'issueFunction in linkedIssuesOf("key = {}", "includes")'.format(portfolio.key)
    linked_issues = jira_connection.search_issues(linked_issues_jql, maxResults=1000)
    return linked_issues


def get_open_issues_from_issue_list(issue_list):
    return list(filter(lambda issue: str(issue.fields.status) == "Open", issue_list))


def get_closed_issues_from_issue_list(issue_list):
    return list(
        filter(lambda issue: str(issue.fields.status) in ("Closed", "Released", "Merged To RC", "Ready To Release"),
               issue_list))


def get_portfolio_included_issues_stats(jira_connection, portfolio):

    included_issues = get_portfolio_included_issues(jira_connection, portfolio)
    num_of_included_issues = len(included_issues)

    open_issues = get_open_issues_from_issue_list(included_issues)
    num_of_open_issues = len(open_issues)

    closed_issues = get_closed_issues_from_issue_list(included_issues)
    num_of_closed_issues = len(closed_issues)

    num_of_inwork_issues = num_of_included_issues - num_of_open_issues - num_of_closed_issues

    if get_sum_of_sp_for_issues(included_issues) is None:
        included_issues_sum_of_sp = None
        open_issues_sum_of_sp = None
        closed_issues_sum_of_sp = None
        inwork_issues_sum_of_sp = None
    else:
        included_issues_sum_of_sp = get_sum_of_sp_for_issues(included_issues)
        open_issues_sum_of_sp = get_sum_of_sp_for_issues(open_issues)
        closed_issues_sum_of_sp = get_sum_of_sp_for_issues(closed_issues)
        inwork_issues_sum_of_sp = included_issues_sum_of_sp - open_issues_sum_of_sp - closed_issues_sum_of_sp

    return {'all': {"count": num_of_included_issues,
                    "sp_sum": included_issues_sum_of_sp
                    },
            'open': {"count": num_of_open_issues,
                     "sp_sum": open_issues_sum_of_sp
                     },
            'closed': {"count": num_of_closed_issues,
                       "sp_sum": closed_issues_sum_of_sp
                       },
            'inwork': {"count": num_of_inwork_issues,
                       "sp_sum": inwork_issues_sum_of_sp
                       }}


def get_sum_of_sp_for_issues(issue_list):
    sum_of_sp = 0.
    for issue in issue_list:
        issue_sp = issue.fields.customfield_11212
        if issue_sp is None:
            return None
        sum_of_sp += float(issue_sp)
    return sum_of_sp


def is_issue_blocked(issue):
    return issue.fields.customfield_11210 is not None


def is_issue_exists(jira_connection, issue_key):
    try:
        jira_connection.issue(str(issue_key))
    except JIRAError:
        return False
    else:
        return True
