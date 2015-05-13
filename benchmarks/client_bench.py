import asyncio
import collections

from aiogremlin import GremlinClient


@asyncio.coroutine
def attack(loop):

    client = GremlinClient(loop=loop, poolsize=1000)
    execute = client.execute

    out_times = collections.deque()
    processed_count = 0

    @asyncio.coroutine
    def do_bomb():
        nonlocal processed_count
        try:
            t1 = loop.time()
            resp = yield from execute("1 + 1")
            assert resp[0].status_code == 200, resp[0].status_code
            t2 = loop.time()
            out_times.append(t2 - t1)
            processed_count += 1
        except Exception:
            print("an exception occurred {}".format(resp[0].status_code))

    bombers = []
    for i in range(10000):
        bomber = asyncio.async(do_bomb())
        bombers.append(bomber)

    t1 = loop.time()
    yield from asyncio.gather(*bombers, loop=loop)
    t2 = loop.time()
    rps = processed_count / (t2 - t1)
    print("Benchmark complete: {} rps".format(rps))

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(attack(loop))
