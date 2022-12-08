import logging
import uuid

from .abstract import Actor, Publisher

__all__ = ['Sender']

logger = logging.getLogger(__name__)


class Sender(Actor):
    
    def __init__(self,
                 publisher: Publisher):
        super().__init__()
        self.publisher = publisher.proxy()
        self.publisher.register_receiver(self.actor_ref)

    def send(self, message: bytes, target: str):       
        message_id = str(uuid.uuid4())
        success = self.publisher.publish(
            message_id, message, target,
        ).get()
        if not success:
            logger.info(f"MESSAGE DON'T SENDED:{message_id}")
            
    def publisher_ready(self):
        return self.publisher.ready.get()