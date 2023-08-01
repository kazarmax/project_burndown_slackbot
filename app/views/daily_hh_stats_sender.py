# coding: utf-8

from app.main import jira_connection
import datetime
import app.helpers.useful_date_functions as udf
import app.helpers.useful_jira_functions as ujf
import requests

today_date = datetime.date.today()

if today_date.weekday() > 4:
    exit()

WEBHOOK_URL = ''

JQL_QUERY_TEMPLATE = ''

OK_MESSAGE = 'По hh-кам всё оки-доки :dancing_bear:'

PRETEXT_MESSAGE_TEMPLATE = '*Задача в статусе _"{}"_ больше {} дней!*'

TEAM_SETTINGS = {
    "Brandy": {
        "channel_id": "G093Z216E",
        "status_limits": {
           'In Progress': 2,
           'Need Review': 1,
           'Need testing': 1,
           'Testing In Progress': 1,
           'Ready To Release': 1,
           'Merged To RC': 1
        }
    },
    "Marketing": {
        "channel_id": "G95SENJQ2",
        "status_limits": {
           'In Progress': 3,
           'Need Review': 1,
           'Need testing': 2,
           'Testing In Progress': 2,
           'Ready To Release': 1,
           'Merged To RC': 1
        }
    }
}


def get_issue_estimate(issue):
    estimate_value = None

    issue_sp = issue.fields.customfield_11212
    if issue_sp is not None:
        if float(issue_sp).is_integer():
            issue_sp = int(issue_sp)

    issue_tshirt_size = issue.fields.customfield_23911

    if issue_sp is not None and issue_tshirt_size is not None:
        estimate_value = "{} ({}sp)".format(issue_tshirt_size, issue_sp)
    elif issue_sp is not None:
        estimate_value = "{}sp".format(issue_sp)
    elif issue_tshirt_size is not None:
        estimate_value = "{}".format(issue_tshirt_size)

    return estimate_value


def get_message_attachment(issue, pretext_message, spent_work_days_in_status, spent_calend_days_in_status):
    return {
            "color": "warning",
            "title": str(issue.key) + ' ' + str(issue.fields.summary),
            "title_link": "https://jira.hh.ru/browse/" + str(issue.key),
            "author_name": "Разработчик: " + str(issue.fields.assignee),
            "author_icon": str(issue.fields.assignee.raw['avatarUrls']['16x16']),
            "pretext": pretext_message,
            "mrkdwn_in": ["pretext"],
            "fields": [
                {
                    "title": "Рабочих дней в статусе",
                    "value": spent_work_days_in_status,
                    "short": "true"
                },
                {
                    "title": "Календарных дней в статусе",
                    "value": spent_calend_days_in_status,
                    "short": "true"
                }
            ]
        }


def add_field_to_full_attachment(attachment, field_title, field_value, is_short=True):
    new_field = {
        "title": str(field_title),
        "value": str(field_value),
        "short": is_short
    }
    attachment['fields'].append(new_field)
    return attachment


def get_message_attachments_for_team(dev_team):

    jql_query = JQL_QUERY_TEMPLATE.format(dev_team)
    issues = jira_connection.search_issues(jql_query, expand='changelog')

    if not issues:
        return None

    message_attachments = []
    for issue in issues:
        if ujf.is_issue_blocked(issue):
            break
        status = str(issue.fields.status)
        to_status_date = ujf.get_issue_to_status_date(issue, status)
        spent_calend_days_in_status = udf.get_calend_days_count_for_date_interval(to_status_date, today_date) - 1
        spent_work_days_in_status = udf.get_workdays_count_for_date_interval(to_status_date, today_date) - 1

        limit = TEAM_SETTINGS[dev_team]["status_limits"][status]
        if spent_work_days_in_status > limit:
            pretext_message = PRETEXT_MESSAGE_TEMPLATE.format(status, limit)
            message_attachment = get_message_attachment(issue, pretext_message, spent_work_days_in_status,
                                                        spent_calend_days_in_status)
            estimate = get_issue_estimate(issue)
            if estimate is not None:
                add_field_to_full_attachment(message_attachment, "Размер задачи", estimate)
            message_attachments.append(message_attachment)

    return message_attachments


def send_simple_message(message_text, channel):
    requests.post(WEBHOOK_URL, json={
        "response_type": "in_channel",
        "channel": channel,
        "text": "_*{}*_".format(message_text)
    })


def notify_team_channel(dev_team):

    team_channel = TEAM_SETTINGS[dev_team].get("channel_id", '@m.kazartsev')
    message_attachments = get_message_attachments_for_team(dev_team)
    if not message_attachments:
        return send_simple_message(OK_MESSAGE, team_channel)

    message_data = {
        "response_type": "in_channel",
        "channel": team_channel,
        "attachments": message_attachments
    }

    requests.post(WEBHOOK_URL, json=message_data)


dev_teams = TEAM_SETTINGS.keys()

for team in dev_teams:
    notify_team_channel(team)
