class ClientContextManager:

    __slots__ = ("_client")

    def __init__(self, client):
        self._client = client

    def __enter__(self):
        return self._client

    def __exit__(self, *args):
        try:
            yield from self._client.close()
        finally:
            self._client = None


class ConnectionContextManager:

    __slots__ = ("_conn", "_pool")

    def __init__(self, conn, pool):
        self._conn = conn
        self._pool = pool

    def __enter__(self):
        return self._conn

    def __exit__(self, exception_type, exception_value, traceback):
        print("in __exit__")
        import ipdb; ipdb.set_trace()
        print("agains")
        try:
            print("hello")
            yield from self._conn.release()
        finally:
            self._conn = None
            self._pool = None
