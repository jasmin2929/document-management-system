FROM python:3.13-slim AS base
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1
WORKDIR /app
COPY genai-worker/requirements.txt .
RUN pip install -r requirements.txt
COPY genai-worker/genai_worker ./genai_worker
COPY worker-common/worker_common ./worker_common

FROM base AS test
COPY genai-worker/requirements-dev.txt genai-worker/pyproject.toml ./
RUN pip install -r requirements-dev.txt
COPY genai-worker/tests ./tests
COPY worker-common/tests ./worker-common-tests
RUN pytest --cov=genai_worker --cov-report=term-missing tests worker-common-tests && touch /tmp/tests-passed

FROM base AS runtime
COPY --from=test /tmp/tests-passed /tmp/tests-passed
RUN useradd --create-home --uid 1000 worker
USER worker
CMD ["python", "-m", "genai_worker"]
