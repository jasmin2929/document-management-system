import logging
import sys

LOG_FORMAT = "%(asctime)s %(levelname)-5s [%(name)s] %(message)s"


def configure_logging(level: str = "INFO") -> None:
    logging.basicConfig(level=level, format=LOG_FORMAT, stream=sys.stdout, force=True)
    logging.getLogger("pika").setLevel(logging.WARNING)
