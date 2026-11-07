# OCR Worker (Python)

Consumes document IDs from the RabbitMQ queue `ocr-queue` (sent by the REST API on upload)
and processes them. Runs as its own container, separate from the REST API.

Sprint 4: Ghostscript + Tesseract are installed in the image and wrapped by `OcrEngine`.
Fetching the PDF from RustFS and calling the engine is task 4.

## Structure

| Layer | Module | Exception |
|---|---|---|
| Configuration | `ocr_worker/config.py` | `ConfigurationException` |
| Messaging | `ocr_worker/messaging/consumer.py`, `message_parser.py` | `BrokerConnectionException`, `MessageFormatException` |
| Processing | `ocr_worker/processing/ocr_processor.py` | `OcrProcessingException` |
| Processing (OCR) | `ocr_worker/processing/ocr_engine.py` (Ghostscript + Tesseract) | `OcrProcessingException` |

All exceptions extend `OcrWorkerException` (`ocr_worker/exceptions.py`).
Failed messages are rejected without requeue, so a broken message cannot loop forever.

## Configuration (environment variables)

| Variable | Default | |
|---|---|---|
| `RABBITMQ_HOST` | `rabbitmq` | |
| `RABBITMQ_PORT` | `5672` | |
| `RABBITMQ_USER` | – | required |
| `RABBITMQ_PASSWORD` | – | required |
| `OCR_QUEUE` | `ocr-queue` | |
| `LOG_LEVEL` | `INFO` | |
| `RABBITMQ_CONNECT_RETRIES` | `10` | |
| `RABBITMQ_CONNECT_RETRY_DELAY` | `3.0` | seconds |
| `OCR_LANGUAGE` | `deu+eng` | Tesseract languages |
| `OCR_DPI` | `300` | resolution of the rendered pages |
| `OCR_MAX_PAGES` | `50` | later pages are ignored |
| `OCR_TIMEOUT_SECONDS` | `120` | per Ghostscript/Tesseract call |

## OCR engine (Ghostscript + Tesseract)

```python
text = OcrEngine(language="deu+eng").extract_text(pdf_bytes)
```

1. Ghostscript renders each page to a 300 dpi grayscale PNG (`-dSAFER`: the PDF may not access other files).
2. Tesseract recognizes the text of each image.

At startup the worker logs the tool versions (`OCR tools ready: ...`) and exits with code 3 if a tool is missing.
Try it by hand:

```powershell
docker cp HelloWorld.pdf dms-ocr-worker:/tmp/HelloWorld.pdf
docker exec dms-ocr-worker python -m ocr_worker.processing.ocr_engine /tmp/HelloWorld.pdf
```

## Tests

Tests run automatically during `docker compose build` (build fails if a test fails
or coverage drops below 70 %). Locally:

```bash
pip install -r requirements.txt -r requirements-dev.txt
pytest --cov=ocr_worker
```
