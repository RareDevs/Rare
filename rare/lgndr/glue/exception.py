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


class LgndrCLILogHandler(logging.Handler):
    def emit(self, record: logging.LogRecord) -> None:
        # lk: FATAL is the same as CRITICAL
        if record.levelno == logging.ERROR or record.levelno == logging.CRITICAL:
            raise LgndrException(record.getMessage())
        # if record.levelno < logging.ERROR or record.levelno == logging.WARNING:
        #     warnings.warn(record.getMessage())


class LgndrCoreLogHandler(logging.Handler):
    def emit(self, record: logging.LogRecord) -> None:
        # lk: FATAL is the same as CRITICAL
        if record.levelno == logging.CRITICAL:
            raise LgndrException(record.getMessage())
        # if record.levelno < logging.CRITICAL:
        #     warnings.warn(record.getMessage())
