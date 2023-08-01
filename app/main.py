from app.helpers.portfolio_object_builder import PortfolioObjectBuilder
import app.helpers.useful_jira_functions as ujf
from app.views.slack_view import SlackView
import app.helpers.redis_utils as redis_utils
from jira import JIRA
import json
import requests
from flask import abort, Flask, request
import threading
import os


app = Flask(__name__)

config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'config.json')
with open(config_path, 'r') as f:
    config = json.load(f)
jira_server = config['JIRA']['server']
jira_login = config['JIRA']['user_name']
jira_password = config['JIRA']['user_password']
slack_token = config['SLACK']['token']

dev_teams = ""

jira_connection = JIRA(basic_auth=(jira_login, jira_password), options={'server': jira_server})


def execute_query(command_param, jql_query, response_url, use_cache=True):

    portfolio_list = []

    portfolio_list_from_redis = redis_utils.get_data_from_redis(command_param)
    if portfolio_list_from_redis and use_cache:
        portfolio_list = portfolio_list_from_redis
    else:
        portfolio_builder = PortfolioObjectBuilder(jira_connection, jql_query)
        portfolio_list = portfolio_builder.get_portfolio_list()
        use_cache = False

    SlackView(portfolio_list, response_url, use_cache).send_portfolio_stats()


def check_issue_exists(response_url, portfolio_key):
    if not ujf.is_issue_exists(jira_connection, portfolio_key):

        message_data = {
            "response_type": "in_channel",
            "text": SlackView.answer_templates['portfolio_not_exists'].format(portfolio_key)
        }
        return requests.post(response_url, json=message_data)


@app.route('/', methods=['POST'])
def main():

    command_key_prefix = '--'
    use_cache = True
    no_cache_key = 'f'

    if request.form['token'] != slack_token:
        return abort(400)

    response_url = request.form['response_url']
    command_param = request.form['text'].strip().split(command_key_prefix)

    if len(command_param) == 2 and command_param[1].strip() == no_cache_key:
        use_cache = False

    if len(command_param) == 2 and command_param[1].strip() != no_cache_key:
        return SlackView.send_quick_message("Указан неверный параметр")

    if len(command_param) > 2:
        return SlackView.send_quick_message("Указаны неверные параметры")

    if len(command_param) == 1 and command_param[0] == "teams":
        return SlackView.show_teams(dev_teams)

    elif (len(command_param) == 1 and command_param[0] == "help") or len(command_param[0]) == 0:
        return SlackView.show_help()

    elif command_param[0].strip() in dev_teams:
        dev_team = command_param[0].strip()
        jql_query = 'project="R&D :: Портфель проектов" and "Development Team"="{}" and status in ("Разработка: в ' \
                    'работе")'.format(dev_team)
        threading.Thread(target=execute_query, args=(dev_team, jql_query, response_url, use_cache,)).start()
        return SlackView.send_quick_message("Подождите немного ...")

    elif command_param[0].strip().isdecimal() and 1 <= len(command_param[0].strip()) <= 4:
        portfolio_key = "PORTFOLIO-{}".format(command_param[0].strip())
        threading.Thread(target=check_issue_exists, args=(response_url, portfolio_key,)).start()
        jql_query = 'key={}'.format(portfolio_key)
        threading.Thread(target=execute_query, args=(portfolio_key, jql_query, response_url, use_cache,)).start()
        return SlackView.send_quick_message("Подождите немного ...")

    else:
        return SlackView.send_quick_message("Нужно указать название команды или номер портфеля - см. `/portfolio help`")
