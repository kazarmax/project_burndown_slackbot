# coding=utf-8

import datetime
import app.helpers.useful_date_functions as udf
import app.helpers.useful_jira_functions as ujf
from app.controller.portfolio_controller import PortfolioController


class SlackMessageAttachmentGenerator(object):
    text_templates = dict(
        portfolio_blocked="Портфель заблокирован. Для заблокированных портфелей прогноз не считается",
        portfolio_not_exists="Портфеля с номером {} не существует.",
        portfolio_not_inwork="Статистику можно получить только по портфелям в работе. Портфель {} не находится в статусе 'Разработка: в работе'",
        portfolio_has_no_included_issues="У портфеля нет подзадач. Без них нельзя посчитать прогноз",
        portfolio_duedate_expired="У портфеля просрочен прогноз. Нужно обновить",
        portfolio_has_no_duedate="Прогноз не указан",
        portfolio_inwork_with_all_issues_done="Все подзадачи закрыты. Кажется, что портфель выполнен. Либо же не все подзадачи заведены и сделаны."
    )

    def __init__(self, portfolio, use_cache):
        self.portfolio = portfolio
        self.portfolio_controller = PortfolioController(portfolio)
        self.use_cache = use_cache

    @staticmethod
    def generate_short_message_attachment(message_text):
        return {
            "pretext": "*{}*".format(message_text),
        }

    def generate_full_message_attachment(self, color="good"):

        use_cache_info = "Cached" if self.use_cache else ""

        return {
            "color": str(color),
            "title": self.portfolio.key + ' ' + self.portfolio.summary,
            "title_link": "https://jira.hh.ru/browse/" + self.portfolio.key,
            "author_name": "Ответственный: " + self.portfolio.assignee,
            "author_icon": self.portfolio.assignee_avatar,
            "fields": [
            ],
            "footer": use_cache_info
        }

    @staticmethod
    def add_field_to_full_attachment(attachment, field_title, field_value, is_short=True):
        new_field = {
            "title": str(field_title),
            "value": str(field_value),
            "short": is_short
        }
        attachment['fields'].append(new_field)
        return attachment

    def get_message_color(self):
        if self.portfolio.is_blocked or (self.portfolio.duedate and self.portfolio.duedate < datetime.date.today()):
            return "danger"

        if not self.portfolio.linked_issues or not self.portfolio.duedate or not self.portfolio.sp_estimate:
            return "warning"

        portfolio_work_completion_rate = int(self.portfolio_controller.get_work_completion_rate())
        portfolio_work_days_completion_rate = int(self.portfolio_controller.get_completion_rate_by_work_days())
        if portfolio_work_completion_rate < portfolio_work_days_completion_rate:
            return "warning"

        return "good"

    def get_duedate_accuracy_status_value(self):
        if not self.portfolio_controller.get_duedate_accuracy_index():
            return None
        duedate_accuracy_index = float(self.portfolio_controller.get_duedate_accuracy_index())
        if duedate_accuracy_index == 1:
            return "Идём в соответствии с прогнозом"
        elif duedate_accuracy_index > 1:
            return "Опережаем прогноз в {} раз(а)".format(duedate_accuracy_index)
        elif duedate_accuracy_index < 1:
            return "Отстаём от прогноза в {} раз(а)".format(round(1 / duedate_accuracy_index, 2))

    def get_completion_rate_by_tasks_field_value(self):
        completion_rate_by_tasks = self.portfolio_controller.get_completion_rate_by_tasks()
        if completion_rate_by_tasks is None:
            return None

        num_of_included_issues = self.portfolio.linked_issues['all']['count']
        num_of_open_linked_issues = self.portfolio.linked_issues['open']['count']
        num_of_closed_linked_issues = self.portfolio.linked_issues['closed']['count']
        num_of_inwork_linked_issues = self.portfolio.linked_issues['inwork']['count']
        completion_rate_by_tasks_field_value = "Закрыто {}%. \n_Всего задач: {} (открытых: {}, закрытых: {}, " \
                                               "в работе: {}_)".format(completion_rate_by_tasks,
                                                                       num_of_included_issues,
                                                                       num_of_open_linked_issues,
                                                                       num_of_closed_linked_issues,
                                                                       num_of_inwork_linked_issues)
        return completion_rate_by_tasks_field_value

    def get_completion_rate_by_task_sps_field_value(self):
        completion_rate_by_task_sps = self.portfolio_controller.get_completion_rate_by_task_sps()
        if completion_rate_by_task_sps is None:
            return None

        linked_issues_sum_of_sp = self.portfolio.linked_issues['all']['sp_sum']
        closed_linked_issues_sum_of_sp = self.portfolio.linked_issues['closed']['sp_sum']
        open_linked_issues_sum_of_sp = self.portfolio.linked_issues['open']['sp_sum']
        inwork_linked_issues_sum_of_sp = self.portfolio.linked_issues['inwork']['sp_sum']
        completion_rate_by_task_sps_field_value = "Закрыто {}%. \n_Всего sp: {} (открытых: {}, закрытых: {}, " \
                                                  "в работе: {}_)".format(completion_rate_by_task_sps,
                                                                          linked_issues_sum_of_sp,
                                                                          open_linked_issues_sum_of_sp,
                                                                          closed_linked_issues_sum_of_sp,
                                                                          inwork_linked_issues_sum_of_sp)
        return completion_rate_by_task_sps_field_value

    def get_message_attachment(self):
        if self.portfolio.status != "Разработка: в работе":
            message_text = self.text_templates['portfolio_not_inwork'].format(self.portfolio.key)
            return self.generate_short_message_attachment(message_text)

        message_color = self.get_message_color()
        portfolio_attachment = self.generate_full_message_attachment(message_color)

        if self.portfolio.is_blocked:
            message_text = self.text_templates['portfolio_blocked']
            self.add_field_to_full_attachment(portfolio_attachment, "Комментарий",
                                              message_text, False)
            calend_days_in_blocking = udf.get_calend_days_count_for_date_interval(self.portfolio.blocking_date, datetime.date.today())
            self.add_field_to_full_attachment(portfolio_attachment, "Дата блокировки", self.portfolio.blocking_date.strftime("%d-%m-%Y"))
            self.add_field_to_full_attachment(portfolio_attachment, "Кол-во дней в блокировке", calend_days_in_blocking)
            return portfolio_attachment

        if not self.portfolio.linked_issues:
            message_text = self.text_templates['portfolio_has_no_included_issues']
            self.add_field_to_full_attachment(portfolio_attachment, "Комментарий",
                                              message_text, False)

        if self.portfolio.duedate and self.portfolio.duedate < datetime.date.today():
            message_text = self.text_templates['portfolio_duedate_expired']
            self.add_field_to_full_attachment(portfolio_attachment, "Комментарий",
                                              message_text, False)

        if self.portfolio_controller.get_work_completion_rate():
            portfolio_work_completion_rate = int(self.portfolio_controller.get_work_completion_rate())
            if portfolio_work_completion_rate == 100:
                message_text = self.text_templates['portfolio_inwork_with_all_issues_done']
                self.add_field_to_full_attachment(portfolio_attachment, "Комментарий",
                                                  message_text, False)

        self.add_field_to_full_attachment(portfolio_attachment, "Взяли в работу",
                                          self.portfolio.inwork_date.strftime("%d-%m-%Y"))

        if self.portfolio.duedate:
            self.add_field_to_full_attachment(portfolio_attachment, "Срок исполнения",
                                              self.portfolio.duedate.strftime("%d-%m-%Y"))
        else:
            self.add_field_to_full_attachment(portfolio_attachment, "Срок исполнения",
                                              self.text_templates['portfolio_has_no_duedate'])

        spent_work_days_in_work = self.portfolio_controller.get_spent_work_days_in_work()
        self.add_field_to_full_attachment(portfolio_attachment, "Рабочих дней в статусе",
                                          spent_work_days_in_work)

        self.add_field_to_full_attachment(portfolio_attachment, "Календарных дней в статусе",
                                          self.portfolio_controller.get_spent_calend_days_in_work())

        if self.portfolio.duedate and self.portfolio_controller.get_completion_rate_by_work_days() is not None:
            completion_rate_by_work_days = self.portfolio_controller.get_completion_rate_by_work_days()
            total_work_days_count = self.portfolio_controller.get_total_work_days_count()
            completion_rate_by_work_days_field_value = "{} из {} ({}%)".format(spent_work_days_in_work,
                                                                               total_work_days_count,
                                                                               completion_rate_by_work_days)
            self.add_field_to_full_attachment(portfolio_attachment, "Пробег портфеля в рабочих днях",
                                              completion_rate_by_work_days_field_value)

        if self.portfolio.sp_estimate:
            self.add_field_to_full_attachment(portfolio_attachment, "Оценка в sp", self.portfolio.sp_estimate)
        else:
            self.add_field_to_full_attachment(portfolio_attachment, "Оценка в sp", "Не указана")

        completion_rate_by_tasks_field_value = self.get_completion_rate_by_tasks_field_value()
        if completion_rate_by_tasks_field_value is not None:
            self.add_field_to_full_attachment(portfolio_attachment, "Статистика по подзадачам",
                                              completion_rate_by_tasks_field_value, False)

        completion_rate_by_task_sps_field_value = self.get_completion_rate_by_task_sps_field_value()
        if completion_rate_by_task_sps_field_value is not None:
            self.add_field_to_full_attachment(portfolio_attachment, "Статистика по SP для подзадач",
                                              completion_rate_by_task_sps_field_value, False)

        duedate_accuracy_status_value = self.get_duedate_accuracy_status_value()
        if duedate_accuracy_status_value and not self.portfolio.is_blocked:
            self.add_field_to_full_attachment(portfolio_attachment, "Соответствие прогнозу",
                                              duedate_accuracy_status_value)

        if self.portfolio_controller.get_predicted_duedate() and not self.portfolio.is_blocked:
            self.add_field_to_full_attachment(portfolio_attachment, "Прогнозируемая дата выполнения",
                                              self.portfolio_controller.get_predicted_duedate().strftime("%d-%m-%Y"))

        return portfolio_attachment
