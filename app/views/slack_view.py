# coding=utf-8

from flask import jsonify
import requests
from app.views.slack_message_attachment_generator import SlackMessageAttachmentGenerator


class SlackView(object):
    answer_templates = dict(
        no_in_work_issues="У команды нет портфелей в работе",
        portfolio_not_exists="Портфеля {} не существует"
    )

    def __init__(self,
                 portfolio_list: list,
                 response_url,
                 use_cache: bool):

        self.portfolio_list = portfolio_list
        self.response_url = response_url
        self.use_cache = use_cache

    @staticmethod
    def send_quick_message(message_text):
        return jsonify(
            response_type='in_channel',
            text="{}".format(message_text)
        )

    @staticmethod
    def show_help():
        help_message = '''Команда `/portfolio` показывает статистику по портфелям в работе ("Разработка в работе"): \n
        - `/portfolio <dev_team_name>` (напр. `/portfolio Billing`) показывает статистку выполнения по портфелям указанной команды разработки \n
        - `/portfolio <portfolio_number>` (напр. `/portfolio 5132`) показывает статистку выполнения по указанному портфелю \n
        - `/portfolio teams` показывает список команд разработки, по которым можэно смотреть статистику '''
        return SlackView.send_quick_message(help_message)

    @staticmethod
    def show_teams(dev_teams):
        result = ""
        for team in sorted(dev_teams):
            result += " - `{}`\n".format(team)
        return SlackView.send_quick_message(result)

    def send_portfolio_stats(self):
        message_attachments = self.prepare_message_data()

        if not message_attachments:
            message_data = {
                "response_type": "in_channel",
                "text": self.answer_templates['no_in_work_issues']
            }
            return requests.post(self.response_url, json=message_data)

        message_data = {
            "response_type": "in_channel",
            "attachments": message_attachments
        }
        requests.post(self.response_url, json=message_data)

    def prepare_message_data(self):
        message_attachments = []
        if not self.portfolio_list:
            return None
        else:
            for portfolio in self.portfolio_list:
                portf_message_attachment = SlackMessageAttachmentGenerator(portfolio, self.use_cache).get_message_attachment()
                message_attachments.append(portf_message_attachment)
        return message_attachments
