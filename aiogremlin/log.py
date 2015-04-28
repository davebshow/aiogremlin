import logging
# logging.basicConfig(level=logging.DEBUG)

INFO = logging.INFO


logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")


client_logger = logging.getLogger("aiogremlin.client")
conn_logger = logging.getLogger("aiogremlin.connection")
task_logger = logging.getLogger("aiogremlin.task")
