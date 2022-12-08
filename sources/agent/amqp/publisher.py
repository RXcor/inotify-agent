import logging
from typing import Tuple

from functools import wraps
import signal

import amqp
from amqp.exceptions import AMQPError, ConnectionForced, MessageNacked, \
    RecoverableConnectionError

from agent.transmission import Publisher

from .connection import ConnectionFabric

__all__ = ['AMQPPublisher']

logger = logging.getLogger(__name__)

class TimeoutError(Exception):
    pass

class AMQPPublisher(Publisher):

    def __init__(self, connection_fabric: ConnectionFabric, check_interval=1):
        super().__init__(check_interval)
        self.create_connection = connection_fabric.create_connection
        self.connection = None
        self.channel = None
        self.CHECK_INTERVAL = check_interval

    def publish(self, message_id: str, body: bytes, target: str, *args):
        if self.ready:
            try:
                message = amqp.Message(body, message_id=message_id)

                channel = self.connection.channel(1)

                channel.basic_publish_confirm(message, target)

                logger.debug(f'SENDING SUCCESS {message_id} TO {target}')
                return True

            except (ConnectionError, 
                BrokenPipeError, 
                MessageNacked, 
                OSError, 
                RecoverableConnectionError):
                self.ready = False
                logger.debug(f'SENDING FAILED {message_id} TO {target}')
                return False
        else:
            logger.debug(f'SENDING FAILED (CONNECTION NOT READY) '
                           f'{message_id} TO {target}')
            return False

    def mass_publish(self, *messages: Tuple[str, bytes, str, int, int]):
        sent_ids = []
        
        # По хорошему, должен быть способ массовой отправки,
        # но это не предусмотрено в использованном здесь клиенте AMQP
        for message in messages:
            success = self.publish(*message)
            if not success:
                break
                
            sent_ids.append(message[0])
        return sent_ids
    
    def check_connection(self):
        if not self.ready:
            logger.debug('CONNECTING')
            try:
                if self.connection:
                    self.connection.close()

                self.connection = self.create_connection()
                self.connection.connect()
                self.ready = True
                logger.info('CONNECTION WITH BROKER SUCCESSFUL')
                
                self.notify_receivers()

            except (ConnectionError, AMQPError, OSError):
                logger.warning('CONNECTING WITH BROKER FAILED')
        else:
            try:
                self.connection.heartbeat_tick()
            except ConnectionForced:
                self.ready = False

