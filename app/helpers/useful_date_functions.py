import datetime


def get_date_obj_from_str(string_date):
    year = int(string_date[0:4])
    month = int(string_date[5:7])
    day = int(string_date[8:10])
    return datetime.date(year, month, day)


def get_calend_days_count_for_date_interval(begin_date, end_date):
    return (end_date - begin_date).days + 1


def get_workdays_list_for_date_interval(begin_date, end_date):
    days_in_interval = get_calend_days_count_for_date_interval(begin_date, end_date)
    date_list = [begin_date + datetime.timedelta(days=x) for x in range(0, days_in_interval)]
    return list(filter(lambda date_item: date_item.weekday() <= 4, date_list))


def get_percentile_date_from_date_list(percentile, date_list):
    k = 0
    percentile_date = None
    for i in range(len(date_list)):
        if round(k/len(date_list), 2) > percentile:
            percentile_date = date_list[i]
            break
        k += 1
    return percentile_date


def get_workdays_count_for_date_interval(begin_date, end_date):
    return len(get_workdays_list_for_date_interval(begin_date, end_date))


def get_shifted_work_date(start_date, days_offset):
    day_increment = datetime.timedelta(1)
    calculated_work_date = start_date
    count = 0
    while count < days_offset:
        calculated_work_date += day_increment
        if calculated_work_date.weekday() <= 4:
            count += 1
    return calculated_work_date
