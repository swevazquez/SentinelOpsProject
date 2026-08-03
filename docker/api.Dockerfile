FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN apt-get update \
    && apt-get install -y --no-install-recommends default-jre-headless curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY pyproject.toml README.md ./
RUN pip install --no-cache-dir \
    "fastapi>=0.115,<1.0" \
    "joblib>=1.4,<2.0" \
    "numpy>=1.26,<2.0" \
    "openai>=2.0,<3.0" \
    "psycopg[binary]>=3.2,<4.0" \
    "scikit-learn>=1.6,<2.0" \
    "uvicorn>=0.34,<1.0" \
    "pyspark>=4.2,<4.3"

CMD ["uvicorn", "services.api.app:app", "--host", "0.0.0.0", "--port", "8000"]
