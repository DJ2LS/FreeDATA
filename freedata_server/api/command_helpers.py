import asyncio
from freedata_server.context import AppContext
import structlog

logger = structlog.get_logger()


async def enqueue_tx_command(ctx: AppContext, cmd_class, params: dict = None) -> bool:
    """
    Enqueue a transmit command using the application context's managers.

    Args:
        ctx: AppContext containing config, state, event managers, etc.
        cmd_class: The command class to instantiate and run.
        params: A dict of parameters for the command (optional).

    Returns:
        bool: True if the command was instantiated and run without raising,
        False if an exception occurred. The return value of command.run() is
        not used, as most commands return None (or a non-indicative value)
        on success.
    """
    params = params or {}
    try:
        # Instantiate the command with required components
        command = cmd_class(ctx, params)
        logger.info("Enqueueing transmit command", command=command.get_name())
        # Run in a thread to avoid blocking the event loop
        await asyncio.to_thread(command.run)
        return True
    except Exception as e:
        logger.error("Command execution failed", command=getattr(cmd_class, "__name__", str(cmd_class)), error=str(e))
        return False
