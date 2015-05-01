"""Simple benchmark based on aiohttp benchmark client."""

import asyncio

from aiogremlin import GremlinClient


@asyncio.coroutine
def attack(loop):

    client = GremlinClient(loop=loop, poolsize=10)
    execute = client.execute

    processed_count = 0

    @asyncio.coroutine
    def drop_bomb():
        nonlocal processed_count
        try:
            t1 = loop.time()
            resp = yield from execute("1 + 1")
            assert resp[0].status_code == 200, resp[0].status_code
            t2 = loop.time()
            processed_count += 1
        except Exception:
            print("an exception occurred {}".format(resp[0].status_code))

    bombers = []
    append = bombers.append
    async = asyncio.async
    for i in range(10000):
        bomber = async(drop_bomb())
        append(bomber)

    t1 = loop.time()
    yield from asyncio.gather(*bombers, loop=loop)
    t2 = loop.time()
    rps = processed_count / (t2 - t1)
    print("Benchmark complete: {} rps".format(rps))


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(attack(loop))
