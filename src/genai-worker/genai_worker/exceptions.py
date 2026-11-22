class GenAiWorkerException(Exception):
    pass


class ConfigurationException(GenAiWorkerException):
    pass


class BrokerConnectionException(GenAiWorkerException):
    pass


class MessageFormatException(GenAiWorkerException):
    pass


class GenAiException(GenAiWorkerException):
    pass
