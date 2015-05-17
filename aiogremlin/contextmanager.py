class ConnectionContextManager:

    __slots__ = ("_conn", "_pool")

    def __init__(self, conn, pool):
        self._conn = conn
        self._pool = pool

    def __enter__(self):
        return self._conn

    def __exit__(self, exception_type, exception_value, traceback):
        try:
            self._conn._closing = True
            self._conn._close()
        finally:
            self._conn = None
            self._pool = None
