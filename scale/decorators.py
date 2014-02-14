from functools import partial

import process


def defer(func):
    """Defers a function's execution using `process.callLater`. Any calls to the decorated function will happen on the
    next tick of the event loop, after this tick has finished.

    """
    return lambda *a, **kw: process.callSoon(func, *a, **kw)


def asyncFunc(func):
    """Marks a function as taking an asynchronous callback. This allows you to use the decorated function as a decorator
    on you inline callback, preventing you from needing to pass the function around. Also gives you the ability to call
    the callback either synchronously, or asynchronously.

    Example:
        @asyncFunc
        def doStuff(name, callback):
            if name != 'Dave':
                callback(None, 'Welcome, traveler!')
            else:
                callback("I'm sorry Dave, but I can't let you do that.")

        @doStuff.async('Bob')
        def cb(error, msg):
            if error:
                print('Error:', error)
            else:
                print('Message:', msg)

        // prints out "Message: Welcome, traveler!"

    """
    func.async = lambda *a, **kw: (lambda cb: func.sync(*a, **kw)(defer(cb)))
    func.sync = lambda *a, **kw: partial(partial, func)(*a, **kw)

    return func

