import functools
from typing import Callable, Concatenate, ParamSpec, TypeVar

import redis
from config import settings

T = TypeVar("T")
P = ParamSpec("P")

CONN_POOL = None


def init_conn_pool():
    """Initializes the connection pool."""
    global CONN_POOL
    if CONN_POOL is None:
        CONN_POOL = redis.Redis(
            host=settings["REDIS"]["host"],
            port=int(settings["REDIS"]["port"]),
            password=settings["REDIS"]["password"],
            db=int(settings["REDIS"]["db"]),
        )


def terminate_conn_pool():
    """Terminates the connection pool."""


def with_connection(func: Callable[Concatenate[redis.Redis, P], T]) -> Callable[P, T]:
    """
    Injects a database connection into a function as the first parameter.

    Args:
      **conn: A database connection, if None, a new connection is opened and closed. If
      the connection is provided, the responsibility of closing it is leveraged to the
      user of the function.
    """

    @functools.wraps(func)
    def wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
        conn = kwargs.pop("conn", None)
        if conn is not None:
            return func(conn, *args, **kwargs)

        init_conn_pool()
        return func(CONN_POOL, *args, **kwargs)

    return wrapper
