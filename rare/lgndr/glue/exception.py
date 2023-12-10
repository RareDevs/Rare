import logging
# import warnings


class LgndrException(RuntimeError):
    def __init__(self, message="Error in Legendary"):
        self.message = message
        super(LgndrException, self).__init__(self.message)


class LgndrWarning(RuntimeWarning):
    def __init__(self, message="Warning in Legendary"):
        self.message = message
        super(LgndrWarning, self).__init__(self.message)


# Minimum exception levels per class to get back useful error strings
# CLI: ERROR
# Core: CRITICAL (FATAL)
class LgndrLogHandler(logging.Handler):
    def __init__(self, level=logging.NOTSET):
        super().__init__(level=level)

    def emit(self, record: logging.LogRecord) -> None:
        if record.levelno >= self.level:
            raise LgndrException(record.getMessage())
        # if self.level > record.levelno >= logging.WARNING:
        #     warnings.warn(record.getMessage())
