# ---------- Base: Python + runtime dependencies ----------
FROM python:3.13-slim AS base
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1
WORKDIR /app
# OCR tools: Ghostscript renders PDF pages to images, Tesseract recognizes the text on them.
# Language packs: English is included in tesseract-ocr, German is added for German documents.
RUN apt-get update \
 && apt-get install -y --no-install-recommends ghostscript tesseract-ocr tesseract-ocr-deu \
 && rm -rf /var/lib/apt/lists/*
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY ocr_worker ./ocr_worker

# ---------- Test: unit tests + coverage (build fails if a test fails or coverage < 70%) ----------
FROM base AS test
COPY requirements-dev.txt pyproject.toml ./
RUN pip install -r requirements-dev.txt
COPY tests ./tests
RUN pytest --cov=ocr_worker --cov-report=term-missing && touch /tmp/tests-passed

# ---------- Runtime: only the app, no test tools ----------
FROM base AS runtime
# Makes the runtime stage depend on the test stage, so tests always run on build
COPY --from=test /tmp/tests-passed /tmp/tests-passed
RUN useradd --create-home --uid 1000 worker
USER worker
CMD ["python", "-m", "ocr_worker"]
