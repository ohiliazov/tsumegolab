FROM python:3.11

ENV POETRY_INSTALLER_PARALLEL="false"
ENV POETRY_VIRTUALENVS_CREATE="false"
ENV PATH="$PATH:/root/.local/bin"

RUN apt update && \
    apt install -y curl build-essential && \
    rm -rf /var/lib/apt/lists/*

RUN curl -sSL https://install.python-poetry.org | python - --version 1.5.1

WORKDIR /tsumegolab
COPY poetry.lock pyproject.toml ./

RUN poetry install --sync --no-interaction --no-root
