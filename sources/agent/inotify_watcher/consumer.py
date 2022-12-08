import logging
import uuid
import json
import inotify.adapters
from inotify import constants
from typing import Tuple
from inotify.calls import InotifyError
import os
from datetime import datetime, timezone

from agent.transmission import Consumer, Receiver
from inotify.constants import IN_CLOSE_WRITE

__all__ = ['InotifyConsumer']

logger = logging.getLogger(__name__)

class InotifyConsumer(Consumer):

    def __init__(self, check_interval: int = 1, 
                 listen_events_types: list = ['IN_CREATE', 
                                              'IN_CLOSE_WRITE', 'IN_DELETE'],
                 server_side: bool = False,
                 listen_dir: str = 'tmp'):
        super().__init__(check_interval, listen_events_types, server_side)
        self.ready = False
        self.client = None
        self.listen_dir = listen_dir

    def on_message(self, message):
        logger.debug(f'INOTIFY ON MESAGE: {message}')
        for receiver in self.receivers.values():
            receiver.receive_message(message)

    def create_client(self):
        # client = inotify.adapters.Inotify()
        # TO DO Добавить маску для подписки только на определенные события
        client = inotify.adapters.InotifyTree(self.listen_dir)
        return client

    # def consume(self, path: str):
    #     try:
    #         # self.client.add_watch(path)
    #         self.listen_dir = path
    #         logger.debug(f'INOTIFY WATCH {path}')
    #     except InotifyError:
    #         logger.warning(f"INOTIFY DON'T WATCH {path}")

    def check_connection(self):
        if not self.ready:
            logger.debug('INOTIFY CONNECTING')
            try:                
                self.client = self.create_client()
            except Exception as e:
                logger.error(f'CREATING CLIENT RETURN EXCEPTION: {e}')
                return            
            self.ready = True
            logger.info('CONNECTION WITH INOTIFY SUCCESSFUL')
            
            self.actor_ref.tell(Consumer.DrainEvents)
            self.restore_consumers()

    def drain_events(self):
        if self.ready:
            logger.debug('DRAIN EVENTS')
            for event in self.client.event_gen(timeout=1):
                logger.debug(f'EVENT: {event}')
                if event is not None:
                    (event, type_names, path, filename) = event
                    # если нашли пересечение, то обрабатываем
                    if not set(type_names).isdisjoint(self.LISTEN_EVENTS_TYPES):
                        
                        if path == self.listen_dir:
                            child_dir = '/'
                        else:
                            child_dir = path.replace(self.listen_dir, '', 1)
                        timestamp = datetime.now(timezone.utc).timestamp()
                        message = {'event': event, 'type_names': type_names, 
                            'path': child_dir, 'name': filename, 
                            'timestamp': timestamp}
                        message['server_side'] = self.SERVER_SIDE
                        try:
                            filesize = os.path.getsize('/'.join([path, filename]))
                            message['size'] = filesize
                        except FileNotFoundError:
                            pass 
                        message = json.dumps(message).encode('utf-8')
                        self.on_message(message)
                        
                    else:
                        continue
            self.actor_ref.tell(Consumer.DrainEvents)

   