from redis_cache import get_redis_connection

key = lambda t, i: '{0}:{1}:visits'.format(t, i)


def get_visits(prefix, page_id):
    r = get_redis_connection()
    return r.get(key(prefix, page_id))


def visit(prefix, page_id):
    r = get_redis_connection()
    r.incr(key(prefix, page_id))


def set_visits(prefix, page_id, visits):
    r = get_redis_connection()
    r.set(key(prefix, page_id), visits)
