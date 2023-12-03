import time
from contextlib import contextmanager
from logging import Logger


@contextmanager
def timelogger(logger: Logger, title: str):
    start = time.perf_counter()
    yield
    logger.debug("%s: %s seconds", title, time.perf_counter() - start)
