import logging


INFO = logging.INFO


logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")


logger = logging.getLogger("aiogremlin")
