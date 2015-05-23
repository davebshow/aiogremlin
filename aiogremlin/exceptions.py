"""
Gremlin Server exceptions.
"""

__all__ = ("RequestError", "GremlinServerError", "SocketClientError")


class SocketClientError(IOError):
    pass


class StatusException(IOError):

    def __init__(self, value, result):
        """Handle all exceptions returned from the Gremlin Server as per:
        https://github.com/apache/incubator-tinkerpop/blob/ddd0b36bed9a2b1ce5b335b1753d881f0614a6c4/gremlin-driver/src/main/java/org/apache/tinkerpop/gremlin/driver/message/ResponseStatusCode.java
        """
        self.value = value
        self.response = {
            498: ("MALFORMED_REQUEST",
                  ("The request message was not properly formatted which " +
                   "means it could not be parsed at all or the 'op' code " +
                   "was not recognized such that Gremlin Server could " +
                   "properly route it for processing. Check the message " +
                   "format and retry the request")),
            499: ("INVALID_REQUEST_ARGUMENTS",
                  ("The request message was parseable, but the arguments " +
                   "supplied in the message were in conflict or incomplete. " +
                   "Check the message format and retry the request.")),
            500: ("SERVER_ERROR",
                  ("A general server error occurred that prevented the " +
                   "request from being processed.")),
            596: ("TRAVERSAL_EVALUATION",
                  ("The remote " +
                   "{@link org.apache.tinkerpop.gremlin.process.Traversal} " +
                   "submitted for processing evaluated in on the server " +
                   "with errors and could not be processed")),
            597: ("SCRIPT_EVALUATION",
                  ("The script submitted for processing evaluated in the " +
                   "{@code ScriptEngine} with errors and could not be  " +
                   "processed.Check the script submitted for syntax errors " +
                   "or other problems and then resubmit.")),
            598: ("TIMEOUT",
                  ("The server exceeded one of the timeout settings for the " +
                   "request and could therefore only partially respond or " +
                   " not respond at all.")),
            599: ("SERIALIZATION",
                  ("The server was not capable of serializing an object " +
                   "that was returned from the script supplied on the " +
                   "requst. Either transform the object into something " +
                   "Gremlin Server can process within the script or install " +
                   "mapper serialization classes to Gremlin Server."))
        }
        if result:
            result = "\n\n{}".format(result)
        self.message = 'Code [{}]: {}. {}.{}'.format(
            self.value,
            self.response[self.value][0],
            self.response[self.value][1],
            result)
        super().__init__(self.message)


class RequestError(StatusException):
    pass


class GremlinServerError(StatusException):
    pass
