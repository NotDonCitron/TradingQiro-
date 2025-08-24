FROM python:3.11-slim

# Install Chrome dependencies for Selenium and create non-root user
RUN apt-get update && apt-get install -y \
    wget \
    curl \
    gnupg \
    unzip \
    xvfb \
    && wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | apt-key add - \
    && echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google.list \
    && apt-get update \
    && apt-get install -y google-chrome-stable \
    && rm -rf /var/lib/apt/lists/* \
    && groupadd -r trading \
    && useradd -r -g trading trading

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY ./src ./src
COPY ./alembic ./alembic
COPY ./alembic.ini ./alembic.ini
COPY ./cookies.txt ./cookies.txt

# Set ownership and switch to non-root user
RUN chown -R trading:trading /app
USER trading

# Expose ports
EXPOSE 8080 9090

# Environment variables for Chrome in Docker
ENV CRYPTET_HEADLESS=true
ENV DISPLAY=:99

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:8080/health || exit 1

CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8080"]