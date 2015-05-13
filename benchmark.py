"""Simple benchmark based on aiohttp benchmark client.
https://github.com/KeepSafe/aiohttp/blob/master/benchmark/async.py
"""
import argparse
import asyncio
import collections
import random

import aiogremlin


@asyncio.coroutine
def run(client, count, concurrency, loop):
    processed_count = 0
    execute = client.execute
    inqueue = collections.deque()
    popleft = inqueue.popleft

    @asyncio.coroutine
    def do_bomb():
        nonlocal processed_count
        while inqueue:
            mssg, result = popleft()
            try:
                resp = yield from execute(mssg)
                assert resp[0].status_code == 200, resp[0].status_code
                assert resp[0].data[0] == result, resp[0].data[0]
                processed_count += 1
            except Exception:
                raise

    for i in range(count):
        rnd1 = random.randint(1, 9)
        rnd2 = random.randint(1, 9)
        mssg = "{} + {}".format(rnd1, rnd2)
        result = rnd1 + rnd2
        inqueue.append((mssg, result))

    bombers = []
    for i in range(concurrency):
        bomber = asyncio.async(do_bomb(), loop=loop)
        bombers.append(bomber)

    t1 = loop.time()
    yield from asyncio.gather(*bombers, loop=loop)
    t2 = loop.time()
    mps = processed_count / (t2 - t1)
    print("Benchmark complete: {} mps. {} messages in {}".format(mps,
        processed_count, t2-t1))
    return mps


@asyncio.coroutine
def main(client, tests, count, concurrency, warmups, loop):
    execute = client.execute
    # warmup
    for x in range(warmups):
        print("Warmup run {}:".format(x))
        yield from run(client, count, concurrency, loop)
    print("Warmup successful!")
    mps_list = []
    for i in range(tests):
        # Take a breather between tests.
        yield from asyncio.sleep(1)
        mps = yield from run(client, count, concurrency, loop)
        mps_list.append(mps)
    print("Average messages per second: {}".format(
        sum(mps_list) / float(len(mps_list))))


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
    nargs='?', type=int, default=256,
    help='count of parallel requests (default: `%(default)s`)')
ARGS.add_argument(
    '-p', '--poolsize', action="store",
    nargs='?', type=int, default=256,
    help='num connected websockets (default: `%(default)s`)')
ARGS.add_argument(
    '-w', '--warmups', action="store",
    nargs='?', type=int, default=5,
    help='num warmups (default: `%(default)s`)')


if __name__ == "__main__":
    args = ARGS.parse_args()
    num_tests = args.tests
    num_mssg = args.count
    concurr = args.concurrency
    poolsize = args.poolsize
    num_warmups = args.warmups
    loop = asyncio.get_event_loop()
    client = loop.run_until_complete(
        aiogremlin.create_client(loop=loop, poolsize=poolsize))
    try:
        print("Runs: {}. Warmups: {}. Messages: {}. Concurrency: {}. Poolsize: {}".format(
            num_tests, num_warmups, num_mssg, concurr, poolsize))
        main = main(client, num_tests, num_mssg, concurr, num_warmups, loop)
        loop.run_until_complete(main)
    finally:
        loop.run_until_complete(client.close())
        loop.close()
        print("CLOSED CLIENT AND LOOP")
