FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

RUN useradd -m -u 10001 appuser

COPY Typhon/ Typhon/

USER appuser

EXPOSE 6240

CMD ["python", "-m", "Typhon.cli", "webui"]
