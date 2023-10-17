FROM python:3.10

RUN apt-get update && apt-get upgrade -y && apt-get autoremove && apt-get autoclean && apt-get install gettext -y

ENV PYTHONUNBUFFERED 1
COPY ./requirements.txt ./requirements.txt

RUN pip install -r requirements.txt

RUN mkdir /app
COPY ./ ./app

WORKDIR /app

EXPOSE 8000

# ENV REDIS_HOST="localhost"
RUN python manage.py collectstatic --no-input --settings=elternsprechtag.settings.test && python manage.py compilemessages --settings=elternsprechtag.settings.test

RUN chmod +x entrypoint.sh

CMD ["./entrypoint.sh"]