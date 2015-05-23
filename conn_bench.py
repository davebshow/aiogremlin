import argparse
import asyncio
import aiogremlin


@asyncio.coroutine
def create_destroy(loop, factory, poolsize):
    client = yield from aiogremlin.create_client(loop=loop,
                                                 factory=factory,
                                                 poolsize=poolsize)
    yield from client.close()

# NEED TO ADD MORE ARGS/CLEAN UP like benchmark.py
ARGS = argparse.ArgumentParser(description="Run benchmark.")
ARGS.add_argument(
    '-t', '--tests', action="store",
    nargs='?', type=int, default=10,
    help='number of tests (default: `%(default)s`)')

ARGS.add_argument(
    '-s', '--session', action="store",
    nargs='?', type=str, default="false",
    help='use session to establish connections (default: `%(default)s`)')


if __name__ == "__main__":
    args = ARGS.parse_args()
    tests = args.tests
    print("tests", tests)
    session = args.session
    loop = asyncio.get_event_loop()
    if session == "true":
        factory = aiogremlin.WebSocketSession()
    else:
        factory = aiogremlin.AiohttpFactory()
    print("factory: {}".format(factory))
    try:
        m1 = loop.time()
        for x in range(50):
            tasks = []
            for x in range(tests):
                task = asyncio.async(
                    create_destroy(loop, factory, 100)
                )
                tasks.append(task)
            t1 = loop.time()
            loop.run_until_complete(
                asyncio.async(asyncio.gather(*tasks, loop=loop)))
            t2 = loop.time()
            print("avg: time to establish conn: {}".format(
                (t2 - t1) / (tests * 100)))
        m2 = loop.time()
        print("time to establish conns: {}".format((m2 - m1)))
        print("avg time to establish conns: {}".format(
            (m2 - m1) / (tests * 100 * 50)))
    finally:
        loop.close()
        print("CLOSED CLIENT AND LOOP")
