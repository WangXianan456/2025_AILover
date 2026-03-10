import os
import time
from collections import defaultdict

_limit = int(os.getenv("CHAT_RATE_LIMIT", "10"))
_window = 60

_redis = None
_fallback: dict[str, list[float]] = defaultdict(list)


def _get_redis():
    global _redis
    if _redis is not None:
        return _redis
    url = os.getenv("REDIS_URL")
    if not url:
        return None
    try:
        import redis
        _redis = redis.from_url(url, decode_responses=True)
        _redis.ping()
        return _redis
    except Exception:
        return None


def check_rate_limit(key: str) -> bool:
    r = _get_redis()
    if r:
        try:
            now = time.time()
            k = f"rate_limit:{key}"
            pipe = r.pipeline()
            pipe.zremrangebyscore(k, 0, now - _window)
            pipe.zcard(k)
            count = pipe.execute()[1]
            if count >= _limit:
                return False
            pipe = r.pipeline()
            pipe.zadd(k, {str(time.time_ns()): now})
            pipe.expire(k, _window + 1)
            pipe.execute()
            return True
        except Exception:
            pass
    now = time.time()
    cutoff = now - _window
    _fallback[key] = [t for t in _fallback[key] if t > cutoff]
    if len(_fallback[key]) >= _limit:
        return False
    _fallback[key].append(now)
    return True
