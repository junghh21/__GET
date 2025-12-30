FROM python:3.10-slim

# 기본 패키지 설치
RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
    curl \
    wget \
    gnupg \
    unzip \
    locales \
    fonts-nanum* \
    && rm -rf /var/lib/apt/lists/*

# Google 키를 gpg로 dearmor 하여 keyring에 저장하고 sources.list에 signed-by 옵션 추가
RUN apt-get update && apt-get install -y --no-install-recommends \
    wget ca-certificates \
  && wget -q -O /tmp/chrome.deb https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb \
  && apt-get update \
  && apt-get install -y --no-install-recommends /tmp/chrome.deb \
  && rm -f /tmp/chrome.deb \
  && rm -rf /var/lib/apt/lists/*


# 로케일 설정
RUN sed -i 's/# ko_KR.UTF-8 UTF-8/ko_KR.UTF-8 UTF-8/' /etc/locale.gen \
    && locale-gen ko_KR.UTF-8
ENV LANG=ko_KR.UTF-8
ENV LC_ALL=ko_KR.UTF-8
ENV PYTHONIOENCODING=utf-8

# Google Chrome 설치
RUN wget -q -O - https://dl.google.com/linux/linux_signing_key.pub | apt-key add - \
    && echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" > /etc/apt/sources.list.d/google-chrome.list \
    && apt-get update \
    && apt-get install -y --no-install-recommends google-chrome-stable \
    && rm -rf /var/lib/apt/lists/*

# ChromeDriver 설치 (Chrome 버전에 맞춰 자동으로 최신 안정 버전 설치)
ARG CHROMEDRIVER_VERSION=latest
RUN if [ "$CHROMEDRIVER_VERSION" = "latest" ]; then \
      CHROMEDRIVER_VERSION=$(wget -qO- https://chromedriver.storage.googleapis.com/LATEST_RELEASE); \
    fi && \
    wget -q "https://chromedriver.storage.googleapis.com/${CHROMEDRIVER_VERSION}/chromedriver_linux64.zip" -O /tmp/chromedriver.zip && \
    unzip /tmp/chromedriver.zip -d /usr/local/bin/ && \
    rm /tmp/chromedriver.zip && \
    chmod +x /usr/local/bin/chromedriver

# 작업 디렉터리
WORKDIR /app

# 의존성 복사 및 설치
COPY requirements.txt /app/requirements.txt
RUN python -m pip install --upgrade pip setuptools wheel \
    && pip install -r /app/requirements.txt

# 소스 복사
COPY . /app

# 기본 커맨드 (테스트 실행은 워크플로에서 오버라이드)
CMD ["python", "main.py"]
