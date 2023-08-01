import datetime


class Portfolio(object):

    def __init__(self,
                 assignee: str,
                 assignee_avatar: str,
                 dev_team: str,
                 key: str,
                 summary: str,
                 inwork_date: datetime.date,
                 duedate: datetime.date,
                 blocking_date: datetime.date,
                 sp_estimate: str,
                 linked_issues: list,
                 is_blocked: bool,
                 status: str):

        self.assignee = assignee
        self.assignee_avatar = assignee_avatar
        self.dev_team = dev_team
        self.key = key
        self.summary = summary
        self.inwork_date = inwork_date
        self.duedate = duedate
        self.blocking_date = blocking_date
        self.sp_estimate = sp_estimate
        self.linked_issues = linked_issues
        self.is_blocked = is_blocked
        self.status = status
