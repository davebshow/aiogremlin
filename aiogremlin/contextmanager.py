class ConnectionContextManager:

    __slots__ = ("_ws")

    def __init__(self, ws):
        self._ws = ws

    def __enter__(self):
        if self._ws.closed:
            raise RuntimeError("Connection closed unexpectedly.")
        return self._ws

    def __exit__(self, exception_type, exception_value, traceback):
        try:
            self._ws._close_code = 1000
            self._ws._closing = True
            self._ws._do_close()
        finally:
            self._ws = None
