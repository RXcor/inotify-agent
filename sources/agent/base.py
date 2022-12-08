import sys
import logging
import signal
import time
from abc import ABC
from typing import Any
from threading import Timer

import pykka

__all__ = ['Actor']

logger = logging.getLogger(__name__)

class Actor(ABC, pykka.ThreadingActor):

    def ask(self, message: Any) -> None: ...

    def tell(self, message: Any) -> pykka.Future: ...

    def proxy(self): ...

    def emit_after(self, message, delay):
        def emit():
            try:
                self.actor_ref.tell(message)
            except pykka.ActorDeadError:
                pass
        t = Timer(delay, emit, args=None, kwargs=None)
        t.start()

    @staticmethod
    def create_message(name):
        return type(name, (object,), {})

    @staticmethod
    def signal_handler(*args):
        logger.info('TRYING TO STOP GRACEFULLY')
        
        # try:
        pykka.ActorRegistry.stop_all(timeout=5)
        # except pykka._exceptions.Timeout:
        #     logger.info('STOPPED WITH TIMEOUT EXCEPTION')            
        logger.info('STOPPED')
        sys.exit(0)

    @classmethod
    def run_until_interrupt(cls):
        signal.signal(signal.SIGINT, cls.signal_handler)
        signal.signal(signal.SIGTERM, cls.signal_handler)
        while True:
            time.sleep(1)