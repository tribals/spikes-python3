import sys
import threading


class PropagatingThread(threading.Thread):
    def __init__(self, group=None, target=None, name=None, args=tuple(), kwargs=dict()):
        super().__init__(
            group=group, target=target, name=name, args=args, kwargs=kwargs
        )
        self.ex = None
        self.tb = None

    def run(self):
        try:
            super().run()
        except Exception:
            _, self.ex, self.tb = sys.exc_info()

    def join(self):
        super().join()

        if self.ex:
            raise self.ex.with_traceback(self.tb)
