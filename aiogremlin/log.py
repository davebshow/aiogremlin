import logging


INFO = logging.INFO


logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")


client_logger = logging.getLogger("aiogremlin.client")
conn_logger = logging.getLogger("aiogremlin.connection")
