import redis
from db import rdconn


@rdconn.with_connection
def get_last_po_post_url_visited_by_id(conn: redis.Redis, wsid: str) -> str:
    if lppuv := conn.hget(wsid, "last_po_post_url_visited"):
        return lppuv.decode("UTF-8")
    return ""


@rdconn.with_connection
def set_last_po_post_url_visited_by_id(
    conn: redis.Redis,
    wsid: str,
    last_po_post_url_visited: str,
):
    return conn.hset(wsid, "last_po_post_url_visited", last_po_post_url_visited)
