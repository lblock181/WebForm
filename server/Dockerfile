FROM python:3.10

RUN apt-get update -y

COPY src/ /app
COPY requirements.txt .
WORKDIR /app

RUN pip install -r ../requirements.txt

CMD [ "gunicorn", "-c", "gunicorn_settings.py", "wsgi:app" ]