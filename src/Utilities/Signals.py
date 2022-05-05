'''
    Last Modified: 2021-04-27

    @author: Jesse M. Barr

    Contains:
        -SignalTranslator

    This is a helper class to translate between pydispatch and PyQt.

    Why?
    PyQt objects can not be called from another thread, but pyqtSignals work
        around that problem.

    This also works with args and kwargs, where pyqtSignal by itself can only
        use args.
'''
from PyQt5.QtCore import QObject, pyqtSignal as Signal
from acestatpy import Signal as ACEstatSignal


class SignalTranslator(QObject):
    __signal = Signal(object)
    __acestatSig = None
    __callback = None

    def __init__(self, acestatSig, callback):
        if not isinstance(acestatSig, ACEstatSignal):
            raise Exception("Expected a ACEstatPy Signal object.")
        elif not callable(callback):
            raise Exception("callback must be a function.")
        super().__init__()

        self.__acestatSig = acestatSig
        self.__callback = callback

        self.__signal.connect(self.__fnCall)
        self.__acestatSig.connect(self.__fnSignal, weak=False)

    def __fnCall(self, data):
        if not self.__callback:
            return
        return self.__callback(*data["args"], **data["kwargs"])

    def __fnSignal(self, *args, **kwargs):
        # ACEstatPy signals include the signal name and sender, which we don't
        #   need.
        kwargs.pop("sender", None)
        kwargs.pop("signal", None)
        self.__signal.emit({
            "args": args,
            "kwargs": kwargs
        })

    def disconnect(self):
        self.__acestatSig.disconnect(self.__fnSignal)
        self.__signal.disconnect(self.__fnCall)

    def __del__(self):
        try:
            self.disconnect()
        except:
            pass
