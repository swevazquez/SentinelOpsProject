FROM apache/airflow:2.10.5-python3.12

USER root

RUN apt-get update \
    && apt-get install -y --no-install-recommends openjdk-17-jre-headless \
    && rm -rf /var/lib/apt/lists/*

USER airflow

RUN pip install --no-cache-dir \
    "joblib>=1.4,<2.0" \
    "numpy>=1.26,<2.0" \
    "psycopg[binary]>=3.2,<4.0" \
    "scikit-learn>=1.6,<2.0" \
    "pyspark>=4.2,<4.3"
