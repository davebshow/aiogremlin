"""Simple benchmark based on aiohttp benchmark client.
https://github.com/KeepSafe/aiohttp/blob/master/benchmark/async.py
"""
import argparse
import asyncio

import aiogremlin


@asyncio.coroutine
def run(client, count, concurrency, loop):
    processed_count = 0
    execute = client.execute

    @asyncio.coroutine
    def do_bomb():
        nonlocal processed_count
        for x in range(count):
            try:
                t1 = loop.time()
                resp = yield from execute("%d" % x)
                assert resp[0].status_code == 200, resp[0].status_code
                assert resp[0].data[0] == x, resp[0].data[0]
                t2 = loop.time()
                processed_count += 1
            except Exception:
                continue

    bombers = []
    append = bombers.append
    async = asyncio.async
    for i in range(concurrency):
        bomber = async(do_bomb(), loop=loop)
        append(bomber)

    t1 = loop.time()
    yield from asyncio.gather(*bombers, loop=loop)
    t2 = loop.time()
    rps = processed_count / (t2 - t1)
    print("Benchmark complete: {} rps. {} messages in {}".format(rps,
        processed_count, t2-t1))
    return rps


@asyncio.coroutine
def main(client, tests, count, concurrency, loop):
    execute = client.execute
    # warmup
    for i in range(10000):
        resp = yield from execute("1+1")
        assert resp[0].status_code == 200, resp[0].status_code
    print("Warmup successful!")
    # Rest
    yield from asyncio.sleep(30)
    rps = yield from run(client, count, concurrency, loop)
    for i in range(tests - 1):
        # Take a breather between tests.
        yield from asyncio.sleep(60)
        rps = yield from run(client, count, concurrency, loop)


ARGS = argparse.ArgumentParser(description="Run benchmark.")
ARGS.add_argument(
    '-t', '--tests', action="store",
    nargs='?', type=int, default=5,
    help='number of tests (default: `%(default)s`)')
ARGS.add_argument(
    '-n', '--count', action="store",
    nargs='?', type=int, default=10000,
    help='message count (default: `%(default)s`)')
ARGS.add_argument(
    '-c', '--concurrency', action="store",
    nargs='?', type=int, default=10,
    help='count of parallel requests (default: `%(default)s`)')
ARGS.add_argument(
    '-p', '--poolsize', action="store",
    nargs='?', type=int, default=256,
    help='num connected websockets (default: `%(default)s`)')


if __name__ == "__main__":
    args = ARGS.parse_args()
    num_tests = args.tests
    num_mssg = args.count
    concurr = args.concurrency
    poolsize = args.poolsize
    loop = asyncio.get_event_loop()
    client = loop.run_until_complete(
        aiogremlin.create_client(loop=loop, poolsize=poolsize))
    try:
        print(
            "Runs: {}. Messages: {}. Concurrency: {}. Total mssg/run: {} ".format(
            num_tests, num_mssg, concurr, num_mssg * concurr))
        main = main(client, num_tests, num_mssg, concurr, loop)
        loop.run_until_complete(main)
    finally:
        loop.run_until_complete(client.close())
        loop.close()
        print("CLOSED CLIENT AND LOOP")
