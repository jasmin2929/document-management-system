import logging
import sys

from genai_worker.config import load_settings
from genai_worker.consumer import GenAiQueueConsumer
from genai_worker.exceptions import BrokerConnectionException, ConfigurationException
from genai_worker.gemini_client import GeminiClient
from genai_worker.logging_config import configure_logging
from worker_common.runner import run_consumer

log = logging.getLogger("genai_worker")


def main() -> int:
    configure_logging()
    try:
        settings = load_settings()
    except ConfigurationException as ex:
        log.critical("Invalid configuration: %s", ex)
        return 2
    configure_logging(settings.log_level)

    gemini = GeminiClient(
        api_key=settings.gemini_api_key,
        model=settings.gemini_model,
        base_url=settings.gemini_base_url,
        timeout=settings.gemini_timeout_seconds,
        max_retries=settings.gemini_max_retries,
        max_input_chars=settings.max_input_chars,
    )
    log.info("Using Gemini model '%s'", settings.gemini_model)
    consumer = GenAiQueueConsumer(settings, gemini)

    return run_consumer(consumer, log, BrokerConnectionException)


if __name__ == "__main__":
    sys.exit(main())
