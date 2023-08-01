# coding: utf-8

import datetime
import app.helpers.useful_date_functions as udf
import app.helpers.useful_jira_functions as ujf
import requests
from app.main import jira_connection

today_date = datetime.date.today()

if today_date.weekday() != 0:
    exit()

WEBHOOK_URL_1 = ''
WEBHOOK_URL_2 = ''

JQL_QUERY_TEMPLATE = ""

PRETEXT_MESSAGE_TEMPLATE = '*Портфель в статусе _"{}"_ больше {} дней!*'

TEAM_SETTINGS = {
    "Team_1": {
        "channel_id": "channel_id",
        "webhook_url": WEBHOOK_URL_1,
        "status_limits": {
           'Декомпозиция: в работе': 4,
           'Разработка: в работе': 20,
           'Проработка: анализ проблемы': 7,
           'Проработка: генерация/отсев вариантов': 7,
           'Проработка: детализация решения': 7
        }
    },
    "Team_2": {
        "channel_id": "channel_id",
        "webhook_url": WEBHOOK_URL_1,
        "status_limits": {
           'Декомпозиция: в работе': 4,
           'Разработка: в работе': 20,
           'Проработка: анализ проблемы': 7,
           'Проработка: генерация/отсев вариантов': 7,
           'Проработка: детализация решения': 7
        }
    },
    "Team_3": {
        "channel_id": "channel_id",
        "webhook_url": WEBHOOK_URL_2,
        "status_limits": {
            'Разработка: в работе': 25
        }
    },
    "Team_4": {
        "channel_id": "channel_id",
        "webhook_url": WEBHOOK_URL_2,
        "status_limits": {
            'Разработка: в работе': 20
        }
    },
    "Team_5": {
        "channel_id": "channel_id",
        "webhook_url": WEBHOOK_URL_2,
        "status_limits": {
            'Разработка: в работе': 25
        }
    },
    "Team_6": {
        "channel_id": "channel_id",
        "webhook_url": WEBHOOK_URL_2,
        "status_limits": {
            'Разработка: в работе': 25
        }
    }
    # "Team_7": {
    #     "channel_id": "channel_id",
    #     "webhook_url": WEBHOOK_URL_2,
    #     "status_limits": {
    #         'Проработка: анализ проблемы': 10,
    #         'Проработка: генерация/отсев вариантов': 10,
    #         'Проработка: детализация решения': 10
    #     }
    # }
}


def get_message_attachment(issue, pretext_message, spent_calend_days_in_status):
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
                    "title": "Календарных дней в статусе",
                    "value": spent_calend_days_in_status,
                    "short": "true"
                }
            ]
        }


def get_message_attachments_for_team(dev_team):

    statuses = list(TEAM_SETTINGS[dev_team]['status_limits'].keys())
    statuses = ["'{}'".format(status) for status in statuses]
    jql_query = JQL_QUERY_TEMPLATE.format(dev_team, ", ".join(statuses))
    issues = jira_connection.search_issues(jql_query, expand='changelog')

    if not issues:
        return None

    message_attachments = []
    for issue in issues:
        status = str(issue.fields.status)

        to_status_date = ujf.get_issue_to_status_date(issue, status)
        spent_calend_days_in_status = udf.get_calend_days_count_for_date_interval(to_status_date, today_date) - 1

        limit = TEAM_SETTINGS[dev_team]["status_limits"][status]
        if spent_calend_days_in_status >= limit:
            pretext_message = PRETEXT_MESSAGE_TEMPLATE.format(status, limit)
            message_attachment = get_message_attachment(issue, pretext_message, spent_calend_days_in_status)
            message_attachments.append(message_attachment)

    return message_attachments


def notify_team_channel(dev_team):

    team_channel = TEAM_SETTINGS[dev_team].get("channel_id", 'email')
    team_webhook = TEAM_SETTINGS[dev_team].get("webhook_url", WEBHOOK_URL_2)
    message_attachments = get_message_attachments_for_team(dev_team)

    message_data = {
        "response_type": "in_channel",
        "channel": team_channel,
        "attachments": message_attachments
    }

    requests.post(team_webhook, json=message_data)


dev_teams = TEAM_SETTINGS.keys()
for team in dev_teams:
    notify_team_channel(team)
