import datetime
import app.helpers.useful_date_functions as udf
import app.helpers.useful_jira_functions as ujf
import math


class PortfolioController(object):

    def __init__(self, portfolio):
        self.portfolio = portfolio

    def get_spent_calend_days_in_work(self):
        return udf.get_calend_days_count_for_date_interval(self.portfolio.inwork_date,
                                                           datetime.date.today()) - 1

    def get_spent_work_days_in_work(self):
        return udf.get_workdays_count_for_date_interval(self.portfolio.inwork_date, datetime.date.today()) - 1

    def get_total_work_days_count(self):
        if self.portfolio.duedate:
            return udf.get_workdays_count_for_date_interval(self.portfolio.inwork_date, self.portfolio.duedate)
        else:
            return None

    def get_percentile_date(self, percentile):
        if self.portfolio.duedate is None:
            return None
        work_days_list = udf.get_workdays_list_for_date_interval(self.portfolio.inwork_date, self.portfolio.duedate)
        percentile_date = udf.get_percentile_date_from_date_list(percentile, work_days_list)
        return percentile_date

    def get_completion_rate_by_work_days(self):

        if self.get_total_work_days_count() == 0:
            return None

        if self.portfolio.duedate:
            return int(round(self.get_spent_work_days_in_work() /
                             self.get_total_work_days_count(), 2) * 100)
        else:
            return None

    def get_completion_rate_by_tasks(self):
        if not self.portfolio.linked_issues:
            return None

        num_of_closed_issues = self.portfolio.linked_issues['closed']['count']
        num_of_all_issues = self.portfolio.linked_issues['all']['count']

        return int(round(num_of_closed_issues / num_of_all_issues, 2) * 100)

    def get_completion_rate_by_task_sps(self):
        linked_issues = self.portfolio.linked_issues
        if not linked_issues:
            return None

        linked_issues_sum_of_sp = linked_issues['all']['sp_sum']
        if linked_issues_sum_of_sp is None:
            return None

        closed_linked_issues_sum_of_sp = linked_issues['closed']['sp_sum']
        return int(round(closed_linked_issues_sum_of_sp / linked_issues_sum_of_sp, 2) * 100)

    def get_work_completion_rate(self):
        completion_rate_by_task_sps = self.get_completion_rate_by_task_sps()
        completion_rate_by_tasks = self.get_completion_rate_by_tasks()

        if completion_rate_by_task_sps is not None:
            return completion_rate_by_task_sps
        elif completion_rate_by_tasks is not None:
            return completion_rate_by_tasks
        else:
            return None

    def get_duedate_accuracy_index(self):
        work_completion_rate = self.get_work_completion_rate()
        completion_rate_by_work_days = self.get_completion_rate_by_work_days()
        if work_completion_rate and work_completion_rate < 100 and completion_rate_by_work_days:
            return round(work_completion_rate / completion_rate_by_work_days, 2)
        else:
            return None

    def get_predicted_duedate(self):
        predicted_duedate = None

        if self.get_duedate_accuracy_index():
            duedate_accuracy_index = float(self.get_duedate_accuracy_index())
            portfolio_total_work_days_count = self.get_total_work_days_count()
            corrected_portfolio_total_work_days_count = math.ceil(portfolio_total_work_days_count / duedate_accuracy_index)
            predicted_duedate = udf.get_shifted_work_date(self.portfolio.inwork_date, corrected_portfolio_total_work_days_count - 1)
        elif not self.portfolio.duedate:
            portf_work_completion_rate = self.get_work_completion_rate()
            portf_inwork_days_count = udf.get_workdays_count_for_date_interval(self.portfolio.inwork_date, datetime.date.today())
            if portf_work_completion_rate and portf_work_completion_rate < 100 and portf_inwork_days_count > 0:
                predicted_total_work_days_count = math.ceil(portf_inwork_days_count * 100 / portf_work_completion_rate)
                predicted_duedate = udf.get_shifted_work_date(self.portfolio.inwork_date, predicted_total_work_days_count - 1)

        return predicted_duedate
