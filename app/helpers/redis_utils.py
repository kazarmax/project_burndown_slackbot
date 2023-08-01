# coding=utf-8

import redis
import app.helpers.useful_date_functions as udf
import datetime
import json
from app.models.portfolio import Portfolio
from app.helpers.portfolio_object_builder import PortfolioObjectBuilder
from jira import JIRA


redis_host = "redis"
redis_port = 6379
redis_password = ""
redis = redis.StrictRedis(host=redis_host, port=redis_port, password=redis_password, decode_responses=True)

jira_connection = JIRA(basic_auth=('user', 'password'), options={'server': 'server_url'})

dev_team_list = ""

jql_query = ''


class CustomEncoder(json.JSONEncoder):

    def default(self, o):
        if isinstance(o, datetime.date):
            return {'__datetime__': o.isoformat()}

        return {'__{}__'.format(o.__class__.__name__): o.__dict__}


def decode_object(o):
    if '__Portfolio__' in o:
        portfolio = Portfolio(o['__Portfolio__']['assignee'],
                              o['__Portfolio__']['assignee_avatar'],
                              o['__Portfolio__']['dev_team'],
                              o['__Portfolio__']['key'],
                              o['__Portfolio__']['summary'],
                              o['__Portfolio__']['inwork_date'],
                              o['__Portfolio__']['duedate'],
                              o['__Portfolio__']['blocking_date'],
                              o['__Portfolio__']['sp_estimate'],
                              o['__Portfolio__']['linked_issues'],
                              o['__Portfolio__']['is_blocked'],
                              o['__Portfolio__']['status']
                              )
        portfolio.__dict__.update(o['__Portfolio__'])
        return portfolio

    elif '__datetime__' in o:
        return udf.get_date_obj_from_str(o['__datetime__'])
    return o


def put_portfolios_to_redis():

    try:
        redis.flushdb()

        portfolio_builder = PortfolioObjectBuilder(jira_connection, jql_query)
        portfolio_list = portfolio_builder.get_portfolio_list()

        portfolio_by_teams = dict()
        for portfolio in portfolio_list:
            redis.set(portfolio.key, json.dumps(portfolio, indent=4, cls=CustomEncoder))

            if portfolio.dev_team not in portfolio_by_teams.keys():
                portfolio_by_teams[portfolio.dev_team] = list()
                portfolio_by_teams[portfolio.dev_team].append(json.dumps(portfolio, indent=4, cls=CustomEncoder))
            else:
                portfolio_by_teams[portfolio.dev_team].append(json.dumps(portfolio, indent=4, cls=CustomEncoder))

        for dev_team_key, portfolio_list_value in portfolio_by_teams.items():
            redis.lpush(dev_team_key, *portfolio_list_value)

    except Exception as e:
        print(e)


def get_data_from_redis(command_param):

    content_type = redis.type(command_param)
    if content_type == 'none':
        return None

    try:

        if content_type == 'string':
            redis_portfolio = redis.get(command_param)
            portfolio = json.loads(redis_portfolio, object_hook=decode_object)
            return [portfolio]

        elif content_type == 'list':
            redis_portfolio_list = redis.lrange(command_param, 0, -1)
            portfolio_list = [json.loads(portf, object_hook=decode_object) for portf in redis_portfolio_list]
            return portfolio_list

    except Exception as e:
        print(e)
        return None


if __name__ == "__main__":
    put_portfolios_to_redis()

