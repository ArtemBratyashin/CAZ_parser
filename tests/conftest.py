import logging


def pytest_configure(config):
    logging.disable(logging.CRITICAL)
