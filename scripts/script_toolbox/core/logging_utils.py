# -*- coding: utf-8 -*-
from __future__ import absolute_import
from __future__ import print_function

import logging


LOGGER_NAME = "script_toolbox"
_HANDLER_MARKER = "_script_toolbox_handler"


def get_logger():
    """Return the Script Toolbox logger without mutating the root logger."""
    logger = logging.getLogger(
        LOGGER_NAME
    )

    has_handler = False
    for handler in logger.handlers:
        if getattr(
            handler,
            _HANDLER_MARKER,
            False
        ):
            has_handler = True
            break

    if not has_handler:
        handler = logging.StreamHandler()
        setattr(
            handler,
            _HANDLER_MARKER,
            True
        )
        handler.setLevel(
            logging.WARNING
        )
        handler.setFormatter(
            logging.Formatter(
                "[Script Toolbox] %(levelname)s: %(message)s"
            )
        )
        logger.addHandler(
            handler
        )

    logger.setLevel(
        logging.DEBUG
    )
    logger.propagate = False
    return logger


def log_execution_result(
    result,
    logger=None
):
    """Log one structured execution result.

    Successful runs are debug-only; failures are always emitted to the host
    console through the package-local StreamHandler.
    """
    logger = logger or get_logger()

    if result.success:
        logger.debug(
            result.summary()
        )
        return result

    logger.error(
        result.diagnostic_text()
    )
    return result


__all__ = [
    "LOGGER_NAME",
    "get_logger",
    "log_execution_result",
]
