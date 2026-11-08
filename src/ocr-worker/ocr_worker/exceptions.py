"""One exception per layer, so callers never depend on pika, boto3 or elasticsearch.

Configuration and broker errors stop the worker; all others only reject the current message.
"""


class OcrWorkerException(Exception):
    pass


class ConfigurationException(OcrWorkerException):
    pass


class BrokerConnectionException(OcrWorkerException):
    pass


class MessageFormatException(OcrWorkerException):
    pass


class StorageException(OcrWorkerException):
    pass


class OcrProcessingException(OcrWorkerException):
    pass


class IndexingException(OcrWorkerException):
    pass
