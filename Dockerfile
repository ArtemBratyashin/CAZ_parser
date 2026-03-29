FROM python:3.11-slim

WORKDIR /opt/app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/opt/app:/opt/app/app:/opt/app/app/src

COPY requirements.txt /opt/app/requirements.txt
RUN pip install --no-cache-dir -r /opt/app/requirements.txt

COPY alembic.ini /opt/app/alembic.ini
COPY migrations /opt/app/migrations
COPY app /opt/app/app
COPY data /opt/app/data
