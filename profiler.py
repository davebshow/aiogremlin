import cProfile
import asyncio
import aiogremlin

loop = asyncio.get_event_loop()
gc = aiogremlin.GremlinClient(loop=loop)

execute = gc.execute("x + x", bindings={"x": 4})
cProfile.run('loop.run_until_complete(execute)')
