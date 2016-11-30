import time
import functools


class NoneDict(dict):
    '''
    A dict that returns None when the key doesn't exist.
    '''
    def __getitem__(self, key):
        return self.get(key)


def rate_limit(interval):
    """
    Rate limiting decorator which allows the wrapped function to be
    called at most once per `interval`.
    """
    def decorator(fn):
        last_called = [0.0]  # This is a list because primitives are constant within the closure.

        @functools.wraps(fn)
        def wrapper(*args, **kwargs):
            elapsed = time.time() - last_called[0]
            remaining = interval - elapsed

            if remaining > 0:
                time.sleep(remaining)

            last_called[0] = time.time()
            return fn(*args, **kwargs)

        return wrapper

    return decorator
