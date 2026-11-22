FROM python:3.13-slim AS base
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1
WORKDIR /app
RUN apt-get update \
 && apt-get install -y --no-install-recommends ghostscript tesseract-ocr tesseract-ocr-deu \
 && rm -rf /var/lib/apt/lists/*
COPY ocr-worker/requirements.txt .
RUN pip install -r requirements.txt
COPY ocr-worker/ocr_worker ./ocr_worker
COPY worker-common/worker_common ./worker_common

# Build fails if a test fails or coverage < 70%
FROM base AS test
COPY ocr-worker/requirements-dev.txt ocr-worker/pyproject.toml ./
RUN pip install -r requirements-dev.txt
COPY ocr-worker/tests ./tests
COPY worker-common/tests ./worker-common-tests
RUN pytest --cov=ocr_worker --cov-report=term-missing tests worker-common-tests && touch /tmp/tests-passed

FROM base AS runtime
# Depending on the test stage makes the tests run on every build
COPY --from=test /tmp/tests-passed /tmp/tests-passed
RUN useradd --create-home --uid 1000 worker
USER worker
CMD ["python", "-m", "ocr_worker"]
