import logging
import sys

LOG_FORMAT = "%(asctime)s %(levelname)-5s [%(name)s] %(message)s"


def configure_logging(level: str = "INFO") -> None:
    # force=True: may be called twice (defaults first, then the configured level)
    logging.basicConfig(level=level, format=LOG_FORMAT, stream=sys.stdout, force=True)
    # both libraries log every connection/request on INFO
    logging.getLogger("pika").setLevel(logging.WARNING)
    logging.getLogger("elastic_transport").setLevel(logging.WARNING)
