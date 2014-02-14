from .events import EventEmitter
import process


class Timer(EventEmitter):
    """A simple event based timer class that supports single-shot or interval based timeouts.

    Listen for the 'timeout' signal to perform action once the timer fires.

    """
    def __init__(self, delay, repeating=False):
        super(Timer, self).__init__()

        self.delay = delay
        self.repeating = repeating
        self._callback = None

    def start(self):
        """Start the timer. Emits the 'started' signal.

        """
        if self.repeating:
            self._callback = process.setInterval(self._timeout, self.delay)
        else:
            self._callback = process.setTimeout(self._timeout, self.delay)

        self.emit('started')

    def stop(self):
        """Stops the timer. Emits the 'stopped' signal.

        """
        self._callback.cancel = True
        self.emit('stopped')

    def _timeout(self):
        self.emit('timeout')
