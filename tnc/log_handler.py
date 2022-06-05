import logging.config

import structlog


# https://www.structlog.org/en/stable/standard-library.html
def setup_logging(filename: str = "", level: str = "DEBUG"):
    """

    Args:
      filename:
      level:str: Log level to output, possible values are:
        "CRITICAL", "FATAL", "ERROR", "WARNING", "WARN", "INFO", "DEBUG"

    """

    timestamper = structlog.processors.TimeStamper(fmt="%Y-%m-%d %H:%M:%S")
    pre_chain = [
        # Add the log level and a timestamp to the event_dict if the log entry
        # is not from structlog.
        structlog.stdlib.add_log_level,
        timestamper,
    ]

    logging.config.dictConfig(
        {
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {
                "plain": {
                    "()": structlog.stdlib.ProcessorFormatter,
                    "processor": structlog.dev.ConsoleRenderer(colors=False),
                    "foreign_pre_chain": pre_chain,
                },
                "colored": {
                    "()": structlog.stdlib.ProcessorFormatter,
                    "processor": structlog.dev.ConsoleRenderer(colors=True),
                    "foreign_pre_chain": pre_chain,
                },
            },
            "handlers": {
                "default": {
                    "level": level,
                    "class": "logging.StreamHandler",
                    "formatter": "colored",
                },
                "file": {
                    "level": level,
                    "class": "logging.handlers.WatchedFileHandler",
                    "filename": f"{filename}.log",
                    "formatter": "plain",
                },
            },
            "loggers": {
                "": {
                    "handlers": ["default", "file"] if filename else ["default"],
                    "level": level,
                    "propagate": True,
                },
            },
        }
    )
    structlog.configure(
        processors=[
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            timestamper,
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )
