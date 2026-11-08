# OCR Worker (Python)

Consumes OCR jobs from the RabbitMQ queue `ocr-queue` (sent by the REST API on upload),
downloads the original PDF from RustFS, runs the OCR (Ghostscript + Tesseract) and
stores the recognized text in Elasticsearch (indexing worker).
Runs as its own container, separate from the REST API.

## Flow

```text
REST API ──{"documentId":5,"bucket":"dms-documents","objectKey":"documents/<uuid>.pdf"}──▶ ocr-queue
ocr-queue ──▶ OcrQueueConsumer ──OcrJob──▶ OcrProcessor
OcrProcessor ──▶ ObjectStorageClient.download()  (RustFS, S3 API via boto3)
             ──▶ OcrEngine.extract_text()         (Ghostscript → PNG → Tesseract)
             ──▶ IndexingWorker.index()           (Elasticsearch index "documents", _id = document ID)
OcrQueueConsumer ──{"documentId":5,"status":"PROCESSED","content":"..."}──▶ ocr-result-queue ──▶ REST API
                                                                  (sets status + content in PostgreSQL)
```

The message is acknowledged only after the OCR text was indexed and the result was sent.
On any failure the worker sends `"status":"FAILED"` instead (except for unreadable messages,
which have no document ID), so the document never stays `PENDING`.
Indexing the same document again overwrites its entry (no duplicates).

## Structure

| Layer | Module | Exception |
|---|---|---|
| Configuration | `ocr_worker/config.py` | `ConfigurationException` |
| Messaging | `ocr_worker/messaging/consumer.py`, `message_parser.py` | `BrokerConnectionException`, `MessageFormatException` |
| Storage | `ocr_worker/storage/object_storage.py` (RustFS via boto3) | `StorageException` |
| Processing | `ocr_worker/processing/ocr_processor.py` | `OcrProcessingException` |
| Processing (OCR) | `ocr_worker/processing/ocr_engine.py` (Ghostscript + Tesseract) | `OcrProcessingException` |
| Indexing | `ocr_worker/indexing/indexing_worker.py` (Elasticsearch) | `IndexingException` |

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
| `OCR_RESULT_QUEUE` | `ocr-result-queue` | results back to the REST API |
| `LOG_LEVEL` | `INFO` | |
| `RABBITMQ_CONNECT_RETRIES` | `10` | |
| `RABBITMQ_CONNECT_RETRY_DELAY` | `3.0` | seconds |
| `OCR_LANGUAGE` | `deu+eng` | Tesseract languages |
| `OCR_DPI` | `300` | resolution of the rendered pages |
| `OCR_MAX_PAGES` | `50` | later pages are ignored |
| `OCR_TIMEOUT_SECONDS` | `120` | per Ghostscript/Tesseract call |
| `STORAGE_ENDPOINT` | `http://rustfs:9000` | RustFS S3 API |
| `STORAGE_ACCESS_KEY` | – | required |
| `STORAGE_SECRET_KEY` | – | required |
| `STORAGE_BUCKET` | `dms-documents` | used if the message has no bucket |
| `STORAGE_REGION` | `us-east-1` | ignored by RustFS, required by the S3 client |
| `STORAGE_MAX_FILE_SIZE` | `52428800` | bytes; larger objects are refused |
| `ELASTICSEARCH_URL` | `http://elasticsearch:9200` | |
| `ELASTICSEARCH_USER` | `elastic` | |
| `ELASTICSEARCH_PASSWORD` | – | required |
| `ELASTICSEARCH_INDEX` | `documents` | |

## OCR engine (Ghostscript + Tesseract)

```python
text = OcrEngine(language="deu+eng").extract_text(pdf_bytes)
```

1. Ghostscript renders each page to a 300 dpi grayscale PNG (`-dSAFER`: the PDF may not access other files).
2. Tesseract recognizes the text of each image.

At startup the worker logs the tool versions (`OCR tools ready: ...`) and exits with code 3 if a tool is missing.
It also checks the bucket (`Object storage ready: ...`) and Elasticsearch (`Elasticsearch ready: ...`);
if one of them is not ready yet, it only logs a warning.

## Try the whole pipeline

```powershell
docker compose up -d --build
# upload HelloWorld.pdf via http://localhost/ (or curl / Postman against the REST API), then:
docker compose logs -f ocr-worker
```

Expected log lines:

```text
INFO  [ocr_worker.messaging.consumer] Received OCR job for document ID: 1
INFO  [ocr_worker.processing.ocr_processor] Starting OCR processing for document ID: 1 (object 'documents/....pdf')
INFO  [ocr_worker.storage.object_storage] Downloaded 'dms-documents/documents/....pdf' from object storage (12345 bytes)
INFO  [ocr_worker.processing.ocr_engine] Rendered 1 page(s) with Ghostscript, starting Tesseract (deu+eng)
INFO  [ocr_worker.processing.ocr_processor] OCR processing finished for document ID: 1, 11 characters recognized. Preview: "Hello World"
INFO  [ocr_worker.indexing.indexing_worker] Indexed document ID: 1 in Elasticsearch index 'documents'
INFO  [ocr_worker.messaging.consumer] Sent OCR result for document ID: 1 (PROCESSED) to queue 'ocr-result-queue'
```

The document then shows the status `Processed` in the web UI.

Check the index (password = `ELASTIC_PASSWORD`), or browse it in Kibana at http://localhost:5601 (user `elastic`):

```powershell
curl -u elastic:elastic_password_change_me "http://localhost:9200/documents/_doc/1?pretty"
curl -u elastic:elastic_password_change_me "http://localhost:9200/documents/_search?q=content:hello&pretty"
```

Only the OCR engine, by hand:

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
