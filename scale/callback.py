from .compat import Object


class Callback(Object):
    def __init__(self, func=None, args=[], kwargs={}, after=None):
        self.func = func
        self.args = args
        self.kwargs = kwargs
        self.after = after
        self._canceled = False
        self.onCanceled = None

    @property
    def canceled(self):
        return self._canceled

    @canceled.setter
    def canceled(self, value):
        self.canceled = value

        if(value and self.onCanceled):
            self.onCanceled(value)

    def __call__(self, *_args):
        if not self.canceled:
            self.func(*self.args, **self.kwargs)

            if self.after:
                self.after()
