import logging
from typing import Tuple

from paho.mqtt import client as mqtt

from agent.transmission import Publisher

from .connection import ConnectionFabric

__all__ = ['MQTTPublisher']

logger = logging.getLogger(__name__)


class MQTTPublisher(Publisher):
    
    def __init__(self, connection_fabric: ConnectionFabric, check_interval=1):
        super().__init__(check_interval)
        self.client = None
        self.connection_kwargs = {'host': connection_fabric.kwargs['host']}
        port = connection_fabric.kwargs.get('port')
        if port:
            self.connection_kwargs['port'] = port

    def publish(self, message_id: str, body: bytes, target: str, *args):
        if self.ready:
            result = self.client.publish(target, body, qos=1)
            if result[0] != mqtt.MQTT_ERR_SUCCESS:
                self.ready = False
                return False
            logger.debug(f'SENDING SUCCESS {message_id} TO {target}')
            return True
        else:
            logger.warning(f'SENDING FAILED (CONNECTION NOT READY) '
                           f'{message_id} TO {target}')
            return False

    def mass_publish(self, *messages: Tuple[str, bytes, str, int, int]):
        sent_ids = []
        
        # По хорошему, должен быть способ массовой отправки,
        # но, кажется, это не предусмотрено в MQTT
        for message in messages:
            success = self.publish(*message)
            if not success:
                break
                
            sent_ids.append(message[0])
        return sent_ids
    
    def create_client(self):
        client = mqtt.Client()
        client.max_inflight_messages_set(0)
        
        login = self.connection_kwargs.get('login')
        password = self.connection_kwargs.get('password')
        if login:
            client.username_pw_set(login, password)
        
        return client
    
    def check_connection(self):
        if not self.ready:
            logger.debug('CONNECTING')
            try:
                if self.client:
                    result = self.client.reconnect()
                else:
                    self.client = self.create_client()
                    result = self.client.connect(**self.connection_kwargs)
            except ConnectionError:
                logger.warning('CONNECTING WITH BROKER FAILED')
                return
                
            if result != mqtt.MQTT_ERR_SUCCESS:
                logger.warning('CONNECTING WITH BROKER FAILED')
                return

            self.ready = True
            logger.info('CONNECTION WITH BROKER SUCCESSFUL')

            self.notify_receivers()
            
        else:
            if self.client.loop() != mqtt.MQTT_ERR_SUCCESS:
                self.ready = False
