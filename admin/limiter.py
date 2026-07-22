"""共享限流器实例，避免循环导入."""

try:
    from slowapi import Limiter
    from slowapi.util import get_remote_address
    limiter = Limiter(key_func=get_remote_address)
    LIMITER_AVAILABLE = True
except ImportError:
    limiter = None
    LIMITER_AVAILABLE = False


def rate_limit(rate: str):
    """限流装饰器包装器，未安装 slowapi 时无操作."""
    def decorator(func):
        if LIMITER_AVAILABLE and limiter is not None:
            return limiter.limit(rate)(func)
        return func
    return decorator
