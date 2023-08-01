# coding=utf-8

from app.main import jira_connection
from app.helpers.portfolio_object_builder import PortfolioObjectBuilder
import datetime
from app.views.slack_message_attachment_generator import SlackMessageAttachmentGenerator
from app.controller.portfolio_controller import PortfolioController
import requests

today_date = datetime.date.today()

if today_date.weekday() > 4:
    exit()

webhook_url = ''

team_channels = {
    "team1": "channel_id",
    "team2": "channel_id",
    "team3": "channel_id",
    "team4": "channel_id"
}


issue_alert_messages = dict(
    duedate_omitted='Проставить прогноз для портфеля надо',
    duedate_expired='Прогноз по задаче продолбали мы. Обновить надо, да скорее закончить начатое ...',
    issue_90_percent_done='Пробег портфеля перевалил за 90%. Проверить надо, всё ли идёт по плану ...',
    issue_75_percent_done='Пробег портфеля перевалил за 75%. Проверить надо, всё ли идёт по плану ...',
    issue_50_percent_done='Пробег портфеля перевалил за 50%. Проверить надо, всё ли идёт по плану ...',
)


def get_pretext_message(portfolio):
    pretext_message = None
    portfolio_controller = PortfolioController(portfolio)
    if portfolio.duedate and datetime.date.today() > portfolio.duedate:
        pretext_message = issue_alert_messages['duedate_expired']
    elif portfolio.duedate is None:
        pretext_message = issue_alert_messages['duedate_omitted']
    elif datetime.date.today() == portfolio_controller.get_percentile_date(0.9):
        pretext_message = issue_alert_messages['issue_90_percent_done']
    elif datetime.date.today() == portfolio_controller.get_percentile_date(0.75):
        pretext_message = issue_alert_messages['issue_75_percent_done']
    elif datetime.date.today() == portfolio_controller.get_percentile_date(0.50):
        pretext_message = issue_alert_messages['issue_50_percent_done']
    return pretext_message


def notify_team_channel(dev_team):
    jql_query = 'project="R&D :: Портфель проектов" and "Development Team"="{}" and status in ("Разработка: в работе")'.format(dev_team)
    portfolio_builder = PortfolioObjectBuilder(jira_connection, jql_query)
    portfolio_list = portfolio_builder.get_portfolio_list()
    message_attachments = []
    for portfolio in portfolio_list:
        pretext_message = get_pretext_message(portfolio)
        if pretext_message is not None:
            portf_message_attachment = SlackMessageAttachmentGenerator(portfolio, use_cache=False).get_message_attachment()
            portf_message_attachment["pretext"] = "_*{}*_".format(pretext_message)
            message_attachments.append(portf_message_attachment)

    channel = team_channels.get(dev_team, '@m.kazartsev')
    message_data = {
        "response_type": "in_channel",
        "channel": channel,
        "attachments": message_attachments
    }

    requests.post(webhook_url, json=message_data)

dev_teams = team_channels.keys()
for team in dev_teams:
    notify_team_channel(team)
