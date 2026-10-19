# OCR Worker (Python)

Consumes document IDs from the RabbitMQ queue `ocr-queue` (sent by the REST API on upload)
and processes them. Sprint 3: "empty" worker that only validates and logs.

## Structure

| Layer | Module | Exception |
|---|---|---|
| Configuration | `ocr_worker/config.py` | `ConfigurationException` |
| Messaging | `ocr_worker/messaging/consumer.py`, `message_parser.py` | `BrokerConnectionException`, `MessageFormatException` |
| Processing | `ocr_worker/processing/ocr_processor.py` | `OcrProcessingException` |

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

## Tests

Tests run automatically during `docker compose build` (build fails if a test fails
or coverage drops below 70 %). Locally:

```bash
pip install -r requirements.txt -r requirements-dev.txt
pytest --cov=ocr_worker
```
