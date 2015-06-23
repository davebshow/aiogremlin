from aiogremlin.client import SimpleGremlinClient


class ConnectionContextManager:

    __slots__ = ("_conn")

    def __init__(self, conn):
        self._conn = conn
        self._client = SimpleGremlinClient(conn)

    def __enter__(self):
        if self._conn.closed:
            raise RuntimeError("Connection closed unexpectedly.")
        return self._client

    def __exit__(self, exception_type, exception_value, traceback):
        try:
            self._conn._close_code = 1000
            self._conn._closing = True
            self._conn._close()
        finally:
            self._conn = None
            self._client = None
