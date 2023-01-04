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

    timestamper = structlog.processors.TimeStamper(fmt="iso")
    pre_chain = [
        # Add the log level and a timestamp to the event_dict if the log entry
        # is not from structlog.
        structlog.stdlib.add_log_level,
        timestamper,
    ]

    config_dict = {
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
        },
        "loggers": {
            "": {
                "handlers": ["default"],
                "level": level,
                "propagate": True,
            },
        },
    }

    if filename:
        config_dict["handlers"]["file"] = {
            "level": level,
            "class": "logging.handlers.WatchedFileHandler",
            "filename": f"{filename}.log",
            "formatter": "plain",
        }
        config_dict["loggers"][""]["handlers"].append("file")

    logging.config.dictConfig(config_dict)
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
