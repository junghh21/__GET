# Dockerfile
FROM python:3.10-slim

ARG DEBIAN_FRONTEND=noninteractive
ARG CHROMEDRIVER_VERSION=auto

# 필수 패키지 설치 (gnupg, curl, wget 등 포함)
RUN apt-get update \
  && apt-get install -y --no-install-recommends \
     ca-certificates curl gnupg wget unzip locales libnss3 libgconf-2-4 libasound2 fonts-liberation fonts-nanum* \
  && sed -i 's/# ko_KR.UTF-8 UTF-8/ko_KR.UTF-8 UTF-8/' /etc/locale.gen \
  && locale-gen ko_KR.UTF-8 \
  && rm -rf /var/lib/apt/lists/*

ENV LANG=ko_KR.UTF-8
ENV LC_ALL=ko_KR.UTF-8
ENV PYTHONIOENCODING=utf-8

# Google Chrome 저장소 키를 keyring에 저장하고 signed-by로 sources 추가 (apt-key 사용 안함)
RUN curl -fsSL https://dl.google.com/linux/linux_signing_key.pub \
    | gpg --dearmor -o /usr/share/keyrings/google-linux-signing-keyring.gpg \
  && echo "deb [arch=amd64 signed-by=/usr/share/keyrings/google-linux-signing-keyring.gpg] http://dl.google.com/linux/chrome/deb/ stable main" \
    > /etc/apt/sources.list.d/google-chrome.list \
  && apt-get update \
  && apt-get install -y --no-install-recommends google-chrome-stable \
  && rm -rf /var/lib/apt/lists/*

# ChromeDriver 설치: auto이면 설치된 Chrome 메이저 버전에 맞춰 자동으로 다운로드
RUN wget -q -O /tmp/chrome.deb https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb \
  && apt-get install -y --no-install-recommends /tmp/chrome.deb \
  && rm -f /tmp/chrome.deb && rm -rf /var/lib/apt/lists/*


WORKDIR /app

# 파이썬 의존성 설치
COPY requirements.txt /app/requirements.txt
RUN python -m pip install --upgrade pip setuptools wheel \
  && pip install -r /app/requirements.txt

#COPY . /app

#CMD ["python", "main.py"]

