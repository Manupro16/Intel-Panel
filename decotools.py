from aiohttp import ClientSession
from functools import wraps
import threading
import traceback
import logging
from typing import Callable, Any

logger = logging.getLogger(__name__)


def threaded_task(daemon: bool = False) -> Callable:
    """
    Decorator to run the decorated function in a separate thread to prevent blocking,
    especially useful for running async tasks in a synchronous environment like Tkinter.

    Args:
        daemon (bool): If True, the thread runs as a daemon, meaning it won't block program exit.

    Returns:
        Callable: Decorated function that runs in a separate thread.
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> threading.Thread:
            def run() -> None:
                try:
                    func(*args, **kwargs)
                except Exception as e:
                    logger.error(f"An error occurred in threaded task {func.__name__}: {e}")
                    logger.debug(traceback.format_exc())

            thread = threading.Thread(target=run)
            thread.daemon = daemon  # Set thread as daemon if specified
            thread.start()
            return thread  # Optionally return the thread object

        return wrapper

    return decorator


def session_manager(func: Callable) -> Callable:
    """
    Decorator to manage aiohttp ClientSession. Creates a new session if one is not provided in kwargs
    and passes it to the decorated async function. Closes the session after the function execution
    if it was created by the decorator.

    Args:
        func (Callable): The async function to be decorated.
    """

    @wraps(func)
    async def wrapper(*args: Any, **kwargs: Any) -> Any:
        session_provided = kwargs.get("session", None)
        if session_provided:
            return await func(*args, **kwargs)
        else:
            async with ClientSession() as session:
                kwargs['session'] = session
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    logger.error(f"An error occurred in {func.__name__}: {e}")
                    logger.debug(traceback.format_exc())
                    raise

    return wrapper
