import logging
import time
import os
import json
from datetime import datetime, timezone
from typing import List

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, EVENT_TYPE_CREATED,\
    EVENT_TYPE_DELETED, EVENT_TYPE_MODIFIED, EVENT_TYPE_MOVED,\
    EVENT_TYPE_CLOSED

from agent.transmission import Consumer
from ._bufer import MessagesBufer


__all__ = ['WatchdogConsumer']

logger = logging.getLogger(__name__)


class WatchdogConsumer(Consumer):

    def __init__(self, check_interval: int = 1, 
                 listen_events_types: list = ['IN_CREATE', 
                                              'IN_CLOSE_WRITE', 'IN_DELETE'],
                 server_side: bool = False,
                 listen_dir: str = 'tmp'):
        super().__init__(check_interval, listen_events_types, server_side)
        self.ready = False
        self.client = None
        self.listen_dir = listen_dir
        self.messages_bufer = MessagesBufer()
        
    def create_client(self):
        client = Observer()
        self.messages_handler = Handler(self.actor_ref.proxy(), self.listen_dir, 
                                   self.LISTEN_EVENTS_TYPES, 
                                   self.SERVER_SIDE, self.messages_bufer)
        client.schedule(self.messages_handler, 
                        path=self.listen_dir, 
                        recursive=True)
        client.start()
        return client

    def check_connection(self):
        if not self.ready:
            logger.debug('WATCHDOG CONNECTING')
            try:                
                self.client = self.create_client()
            except Exception as e:
                logger.error(f'CREATING CLIENT RETURN EXCEPTION: {e}')
                return            
            self.ready = True
            logger.info('CONNECTION WITH WATCHDOG SUCCESSFUL')
            
            self.actor_ref.tell(Consumer.DrainEvents)
            self.restore_consumers() 
            
    def drain_events(self):
        for receiver in self.receivers.values():
            for cr_m in self.messages_bufer.\
                pop_all_messages_by_event_type(EVENT_TYPE_CREATED): 
                receiver.receive_message(cr_m)
            for upd_m in self.messages_bufer.\
                pop_all_messages_by_event_type(EVENT_TYPE_MODIFIED): 
                receiver.receive_message(upd_m)
            for clwr_m in self.messages_bufer.\
                pop_all_messages_by_event_type(EVENT_TYPE_CLOSED):
                receiver.receive_message(clwr_m)
            for del_m in self.messages_bufer.\
                pop_all_messages_by_event_type(EVENT_TYPE_DELETED):
                receiver.receive_message(del_m)


class Handler(FileSystemEventHandler):

    def __init__(self, proxy_consumer, listen_dir, listen_events_types, 
                 server_side=False, messages_bufer: MessagesBufer = None):
        super().__init__()
        self.messages_bufer = messages_bufer
        self.listen_events_types = listen_events_types
        self.server_side = server_side
        self.proxy_consumer = proxy_consumer
        self.listen_dir = listen_dir

        self.conversion = {
            EVENT_TYPE_CREATED: 'IN_CREATE',
            EVENT_TYPE_CLOSED: 'IN_CLOSE_WRITE',
            EVENT_TYPE_MODIFIED: 'IN_MODIFY',
            EVENT_TYPE_DELETED: 'IN_DELETE' 
        }
        
    def dispatch(self, event):
        """Dispatches events to the appropriate methods.

        :param event:
            The event object representing the file system event.
        :type event:
            :class:`FileSystemEvent`
        """
        self.on_any_event(event)

    def on_any_event(self, event):
        if event.event_type not in self.listen_events_types:
            pass 
        type_names = []
        type_names.append(self.conversion[event.event_type])
        if event.is_directory:
            type_names.append('IN_ISDIR')

        if event.src_path == self.listen_dir:
            return
        else:
            parent_path = os.path.dirname(event.src_path).\
                replace(self.listen_dir, '', 1)
        
        if parent_path == '':
            parent_path = '/'
        
        filename = event.src_path.split('/')[-1]
        timestamp = datetime.now(timezone.utc).timestamp()
        message = {'type_names': type_names, 
                  'path': parent_path, 'name': filename, 
                  'timestamp': timestamp, 'server_side': self.server_side}
        try:
            filesize = os.path.getsize(event.src_path)
            message['size'] = filesize
        except FileNotFoundError:
            pass 
        message = json.dumps(message).encode('utf-8')
        # logger.debug(f'WATCHDOG HANDLER CREATE MESSAGE: {message}' )
        self.messages_bufer.send_mes_to_buf(event.event_type, parent_path, 
                                            filename, message)     
