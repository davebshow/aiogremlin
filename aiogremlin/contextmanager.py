class ConnectionContextManager:

    __slots__ = ("_conn")

    def __init__(self, conn):
        self._conn = conn

    def __enter__(self):
        return self._conn

    def __exit__(self, exception_type, exception_value, traceback):
        try:
            self._conn._closing = True
            self._conn._close()
        finally:
            self._conn = None
