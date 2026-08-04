"""
Retry logic with exponential backoff and jitter for network & stream connections.
Conforms to Production Requirement #11.
"""
import time
import random
import logging
import functools
from typing import Callable, Any, Type, Tuple

logger = logging.getLogger(__name__)

def retry_with_backoff(
    max_retries: int = 3,
    initial_delay: float = 0.5,
    backoff_factor: float = 2.0,
    max_delay: float = 10.0,
    jitter: bool = True,
    exceptions_to_retry: Tuple[Type[Exception], ...] = (Exception,),
    is_auth_operation: bool = False
):
    """
    Decorator for retrying a function with exponential backoff and optional jitter.
    Crucially caps authentication retries to prevent account lockout.
    """
    def decorator(func: Callable[..., Any]):
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            effective_max_retries = min(max_retries, 3) if is_auth_operation else max_retries
            delay = initial_delay

            for attempt in range(1, effective_max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions_to_retry as e:
                    if attempt == effective_max_retries:
                        logger.error(f"Operation '{func.__name__}' failed after {attempt} attempts: {e}")
                        raise

                    sleep_time = delay
                    if jitter:
                        sleep_time += random.uniform(0, 0.1 * delay)

                    logger.warning(
                        f"Operation '{func.__name__}' attempt {attempt}/{effective_max_retries} failed ({e}). "
                        f"Retrying in {sleep_time:.2f}s..."
                    )
                    time.sleep(sleep_time)
                    delay = min(delay * backoff_factor, max_delay)

        return wrapper
    return decorator
