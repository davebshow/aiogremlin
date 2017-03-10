class ConfigError(Exception):
    pass


class ClientError(Exception):
    pass


class MappingError(Exception):
    pass


class ValidationError(Exception):
    pass


class ElementError(Exception):
    pass


class ConfigurationError(Exception):
    pass


class GremlinServerError(Exception):

    def __init__(self, status_code, msg):
        super().__init__(msg)
        self.status_code = status_code
        self.msg = msg


class ResponseTimeoutError(Exception):
    pass
