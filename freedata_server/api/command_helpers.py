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
        bool: True if the command ran successfully, False otherwise.
    """
    params = params or {}
    try:
        # Instantiate the command with required components
        command = cmd_class(ctx, params)
        logger.info("Enqueueing transmit command", command=command.get_name())
        # Run in a thread to avoid blocking the event loop
        result = await asyncio.to_thread(command.run)
        return bool(result)
    except Exception as e:
        logger.error("Command execution failed", error=str(e))
        return False
