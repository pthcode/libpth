import os
import time
import functools


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


def locate(root, match_function, ignore_dotfiles=True):
    '''
    Yields all filenames within `root` for which match_function returns
    True.
    '''
    for path, dirs, files in os.walk(root):
        for filename in (os.path.abspath(os.path.join(path, filename))
                         for filename in files if match_function(filename)):
            if ignore_dotfiles and os.path.basename(filename).startswith('.'):
                pass
            else:
                yield filename


def ext_matcher(*extensions):
    '''
    Returns a function which checks if a filename has one of the specified
    extensions.
    '''
    return lambda f: os.path.splitext(f)[-1].lower() in set(extensions)
