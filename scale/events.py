import logging
from functools import partial
from collections import defaultdict

# local imports
from .compat import Object
from .decorators import defer as build_deferred
from .utils import isNumber, isNan


logger = logging.getLogger('EventEmitter')


class EventEmitter(Object):
    """A port of node.js's EventEmitter class. Built to work with the rest of the async framework by default. From
    node's documentation:

    Typically, event names are represented by a camel-cased string, however, there aren't any strict restrictions on
    that, as any string will be accepted.

    Functions can then be attached to objects, to be executed when an event is emitted. These functions are called
    _listeners_.

    """

    def __init__(self):
        self._events = defaultdict(set)
        self._warned = list()
        self._maxListeners = 10

    def addListener(self, event, listener):
        """Adds a listener to the end of the listeners array for the specified event.

        """
        if not callable(listener):
            raise TypeError('listener must be callable')

        # Avoid recursion in the case that event == "newListener".
        if self._events['newListener']:
            self.emit('newListener', event, listener.listener if callable(listener.listener) else listener)

        # Since events is a default dict, we can always simply add the new listener
        self._events[event].add(listener)

        # Detect event emitter leaks
        if event not in self._warned:
            if 1 < self._maxListeners < len(self._events[event]):
                logger.warning(("Possible EventEmitter memory leak detected. {} listeners added. " +
                                "Use emitter.setMaxListeners() to increase limit.").format(len(self._events[event])))

                self._warned.add('event')

                #TODO: print a trace?

        return self

    def on(self, event, listener=None, defer=False):
        """Adds a listener to the end of the listeners array for the specified event. Optionally supports deferring the
        callback with the `@defer` decorator.

        This can also be used as a decorator:

            @emitter.on('some event')
            def cb(arg1, arg2):
                print("Got args:", arg1, arg2)

        """
        if listener is None:
            return partial(self.on, event)
        else:
            if defer:
                listener = build_deferred(listener)
            self.addListener(event, listener)

    def once(self, event, listener):
        """Adds a **one time** listener for the event. This listener is invoked only the next time the event is fired,
        after which it is removed.

        """
        def fireOnce():
            self.removeListener(event, fireOnce)
            listener()

        self.addListener(event, fireOnce)

    def removeAllListeners(self, event=None):
        """Removes all listeners for the event.

        """
        # Check to see if we need to bother emitting 'removeListener'
        if 'removeListener' not in self._events:
            if event:
                if event not in self._events:
                    return
                else:
                    del self._events[event]
            else:
                # Remove all event listeners
                self._events = {}
        else:
            if event:
                if event not in self._events:
                    return
                else:
                    for listener in self._events[event]:
                        self.removeListener(event, listener)
            else:
                # Remove all event listeners
                for event in self._events.keys():
                    if event != 'removeListener':
                        for listener in self._events[event]:
                            self.removeListener(event, listener)

                # Make sure to clear out the 'removeListener' listeners, too.
                self._events = {}

    def removeListener(self, event, listener):
        """Removes all listeners, or those of the specified event.
        Returns emitter, so calls can be chained.

        """
        if not callable(listener):
            raise TypeError('listener must be callable')

        if event in self._events:
            self._events[event].remove(listener)
            self.emit('removeListener', event, listener)

    def setMaxListeners(self, num):
        """By default EventEmitters will print a warning if more than 10 listeners are added for a particular event.
        This is a useful default which helps finding memory leaks. Obviously not all Emitters should be limited to 10.
        This function allows that to be increased. Set to zero for unlimited.

        """
        if not isNumber(num) or num < 0 or isNan(num):
            raise TypeError('num must be a positive number.')
        self._maxListeners = num
        return self

    def listeners(self, event):
        """Returns an array of listeners for the specified event.

        """
        if event in self._events:
            return self._events[event]

        return []

    def emit(self, event, *args, **kwargs):
        """Execute each of the listeners in order with the supplied arguments.

        Returns `True` if event had listeners, `False` otherwise.

        """
        if event == 'error' and len(self._events[event]) > 0:
            raise RuntimeError('Uncaught, unspecified "error" event.')

        for listener in self._events[event]:
            listener(*args, **kwargs)

    @classmethod
    def listenerCount(cls, emitter, event):
        """Return the number of listeners on a given EventEmitter for the event.

        """
        return len(emitter.listeners(event))
