import logging


LOGGER = logging.getLogger('compiler')


def log_step(msg: str):
    LOGGER.info(msg)