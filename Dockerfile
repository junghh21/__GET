# Dockerfile
FROM python:3.10-slim

ARG DEBIAN_FRONTEND=noninteractive

RUN apt-get update \
  && apt-get install -y --no-install-recommends \
     git ca-certificates curl wget locales fonts-liberation fonts-nanum \
  && sed -i 's/# ko_KR.UTF-8 UTF-8/ko_KR.UTF-8 UTF-8/' /etc/locale.gen \
  && locale-gen ko_KR.UTF-8 \
  && rm -rf /var/lib/apt/lists/*

ENV LANG=ko_KR.UTF-8
ENV LC_ALL=ko_KR.UTF-8
ENV PYTHONIOENCODING=utf-8

WORKDIR /app

COPY requirements.txt /app/requirements.txt
RUN python -m pip install --upgrade pip setuptools wheel \
  && pip install -r /app/requirements.txt \
  && playwright install --with-deps chromium \
  && rm -rf /var/lib/apt/lists/* /root/.cache/pip
