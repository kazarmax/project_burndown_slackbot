FROM python:3.6.6

# install cron and copy file with cron jobs to image
RUN apt-get clean && apt-get update && apt-get install -y cron
COPY cronjobs /etc/cron.d/
RUN chmod 0644 /etc/cron.d/cronjobs

# copy application code to image
ADD . /opt/portfolio_burndown

WORKDIR /opt/portfolio_burndown

# fetch app specific deps
RUN pip install -r requirements.txt && chmod +x docker-entrypoint.sh

EXPOSE 8009

CMD ["/opt/portfolio_burndown/docker-entrypoint.sh"]
