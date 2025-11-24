FROM python:3.13

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends gcc libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY . ./

RUN pip install uv

RUN uv sync

EXPOSE 8000

