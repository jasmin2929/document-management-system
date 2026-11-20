import logging
import signal


def run_consumer(consumer, log: logging.Logger, broker_error: type) -> int:
    def handle_shutdown(signum, _frame):
        log.info("Received signal %s, shutting down", signal.Signals(signum).name)
        consumer.stop()

    signal.signal(signal.SIGTERM, handle_shutdown)
    signal.signal(signal.SIGINT, handle_shutdown)

    try:
        consumer.connect()
        consumer.start()
    except broker_error as ex:
        log.critical("%s", ex)
        return 1
    finally:
        consumer.close()

    log.info("Worker stopped")
    return 0
