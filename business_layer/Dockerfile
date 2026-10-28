FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

RUN groupadd --system app \
    && useradd --system --gid app --home-dir /app --shell /usr/sbin/nologin app \
    && mkdir -p /data \
    && chown app:app /data

COPY requirements.txt ./requirements.txt
RUN python -m pip install --no-cache-dir --disable-pip-version-check -r requirements.txt

COPY --chown=app:app business_layer ./business_layer
COPY --chown=app:app database_persistent ./database_persistent

USER app

EXPOSE 8000

CMD ["uvicorn", "business_layer.main:app", "--host", "0.0.0.0", "--port", "8000"]
