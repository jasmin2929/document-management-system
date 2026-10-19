"""Layer-specific exceptions of the OCR worker.

Every layer raises its own exception type, so the caller can decide how to
react (retry, drop the message, stop the service, ...) without depending on
the libraries used inside that layer (e.g. pika or json).

Hierarchy::

    OcrWorkerException
    ├── ConfigurationException      (configuration layer)
    ├── BrokerConnectionException   (messaging layer)
    ├── MessageFormatException      (messaging layer)
    └── OcrProcessingException      (processing layer)
"""


class OcrWorkerException(Exception):
    """Base class for all exceptions raised by the OCR worker.

    Catching this type handles every expected worker error at once.
    """


class ConfigurationException(OcrWorkerException):
    """Configuration layer: an environment variable is missing or invalid.

    Fatal: the worker exits immediately (exit code 2).
    """


class BrokerConnectionException(OcrWorkerException):
    """Messaging layer: the RabbitMQ broker cannot be reached or the connection was lost.

    Fatal: the worker exits (exit code 1) and Docker restarts it.
    """


class MessageFormatException(OcrWorkerException):
    """Messaging layer: a received message cannot be parsed.

    Affects only that message: it is rejected and the worker keeps running.
    """


class OcrProcessingException(OcrWorkerException):
    """Processing layer: a document cannot be processed.

    Affects only that message: it is rejected and the worker keeps running.
    """
