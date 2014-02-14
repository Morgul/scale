import sys
import logging
import collections
import signal
import socket

import pyuv

from .callback import Callback


def _processCallback(callback):
    """Call the callback, and handle exceptions

    """
    global _last_exc

    try:
        callback()
    except Exception:
        logging.exception('Exception in callback %s %r %r', callback.func, callback.args, callback.kwargs)
    except BaseException:
        _last_exc = sys.exc_info()


def _processImmediates():
    """Run through all immediates, and (assuming we've run less than `immediateLimit`) and call them.

    """
    global _immediates, _immediatesCalled, immediateLimit

    while _immediates and _immediatesCalled < immediateLimit:
        _immediatesCalled += 1
        _processCallback(_immediates.popleft())


def _processDeferreds(handle):
    """Process scheduled deferreds.

    Note: We only run the currently scheduled deferreds; any deferreds scheduled by callbacks we run will be run on the
    next iteration of the event loop. Any immediates scheduled will be run as soon as the current deferred finishes
    execution.

    """
    global _loop, _deferreds, _last_exc, _deferredsHandle, _immediatesCalled

    _immediatesCalled = 0
    deferredsScheduled = bool(_deferreds)

    while _deferreds:
        _processCallback(_deferreds.popleft())

    if deferredsScheduled and not _deferreds:
        _deferredsHandle.unref()


def _tick():
    """Iterates one tick of the event loop.

    """
    global _deferreds, _loop, _last_exc, _stop

    if _deferreds:
        mode = pyuv.UV_RUN_NOWAIT
    else:
        mode = pyuv.UV_RUN_ONCE

    # Handle exceptions
    if _last_exc is not None:
        exc, _last_exc = _last_exc, None
        raise exc[1]

    return _loop.run(mode)


def _exceptHook(typ, val, tb):
    """Handle exceptions, closing the application on KeyboardInterrupt.

    """
    if typ is KeyboardInterrupt:
        signal_checker.stop()
        _close()


def _close():
    """Helper function for cleaning up the event loop.

    """
    global _loop, _deferreds, _deferredsHandle

    _deferreds.clear()
    _immediates.clear()

    _waker.close()
    _deferredsHandle.close()

    def closeCB(handle):
        if not handle.closed:
            handle.close()

    # Run a loop iteration so that close callbacks are called and resources are freed
    _loop.walk(closeCB)

    assert not _loop.run(pyuv.UV_RUN_NOWAIT)
    _loop = None


#-----------------------------------------------------------------------------------------------------------------------
# Scheduling
#-----------------------------------------------------------------------------------------------------------------------


def callImmediately(func, *args, **kwargs):
    """Schedules the function to be called immediately after the current one finishes executing. This means it will be
    scheduled **before** all other events currently in the event queue. Equivalent to node.js' `process.nextTick`.

    """
    callback = Callback(func, args, kwargs)
    callback.after = _processImmediates
    _immediates.append(callback)

    return callback


def callSoon(func, *args, **kwargs):
    """Schedules the function to be called after the current tick finishes. This means it will be scheduled **after**
    any events currently in the event queue. Equivalent to node.js' `setImmediate`.

    """
    if not _deferreds:
        _deferredsHandle.ref()

    callback = Callback(func, args, kwargs)
    callback.after = _processImmediates
    _deferreds.append(callback)

    return callback


def setTimeout(func, delay, *args, **kwargs):
    """Schedules a callback to be called after a delay (in seconds). The delay may be a float.

    """
    global _loop

    if delay < 0:
        raise ValueError('invalid delay specified: {}'.format(delay))
    elif delay == 0:
        callSoon(func, args, kwargs)

    timer = pyuv.Timer(_loop)

    def timerCleanup():
        _timers.remove(timer)
        _processImmediates()

    callback = Callback(func, args, kwargs)
    callback.after = timerCleanup

    timer.handler = callback
    timer.start(callback, delay, 0)

    _timers.append(timer)

    return callback


def setInterval(func, interval, *args, **kwargs):
    """Schedules a callback to be called repeatedly, every `interval` seconds. The interval may be a float.

    """
    if interval < 0:
        raise ValueError('invalid interval specified: {}'.format(interval))

    timer = pyuv.Timer(_loop)

    def timerCleanup():
        _timers.remove(timer)

    callback = Callback(func, args, kwargs)
    callback.after = _processImmediates
    callback.onCanceled = timerCleanup

    timer.handler = callback
    timer.start(callback, interval, interval)

    _timers.append(timer)

    return callback


#-----------------------------------------------------------------------------------------------------------------------


def run():
    while _tick() and not _stop:
        pass


def runForever():
    """Starts the event loop and runs it forever.

    """
    callback = setInterval(24*3600, lambda: None)
    try:
        run()
    finally:
        callback.cancel = True


def runOnce(timeout=None):
    """Run through an iteration of the loop.

    """
    timer = None
    if timeout is not None:
        timer = pyuv.Timer(_loop)
        timer.start(lambda x: None, timeout, 0)

    # Run through the loop once
    _tick()

    # If we created a timer, close it
    if timeout is not None and timer.close:
        timer.close()


#-----------------------------------------------------------------------------------------------------------------------


def stop():
    """Tells the event loop to stop once it has finished processing all outstanding events.

    """
    global _stop, _waker

    _stop = True
    _waker.send()


def stopImmediately():
    """Tells the event loop to stop execution immediately, and free all outstanding resources.

    """
    _close()


def exit(code=0):
    """Ends the process with the specified code. If omitted, exit uses the 'success' code 0.

    """
    stop()
    _close()
    sys.exit(code)


#-----------------------------------------------------------------------------------------------------------------------


# Event loop
_loop = pyuv.Loop.default_loop()

_stop = False
_last_exc = None

_immediates = collections.deque()
_deferreds = collections.deque()
_timers = collections.deque()

immediateLimit = 10
_immediatesCalled = 0

_waker = pyuv.Async(_loop, lambda h: None)
_waker.unref()

_deferredsHandle = pyuv.Check(_loop)
_deferredsHandle.start(_processDeferreds)

# Signal handling
reader, writer = socket.socketpair()
reader.setblocking(False)
writer.setblocking(False)

_loop.excepthook = _exceptHook

signal.set_wakeup_fd(writer.fileno())
signal_checker = pyuv.util.SignalChecker(_loop, reader.fileno())
signal_checker.start()

#-----------------------------------------------------------------------------------------------------------------------
