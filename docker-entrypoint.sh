#!/bin/bash

#starting cron to run cron jobs from /etc/cron.d
service cron start

#starting gunicorn server to serve requests from slack slash command
gunicorn --bind 0.0.0.0:8009 wsgi:app
