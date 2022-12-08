from abc import abstractmethod
import logging
from typing import Tuple

from pykka import ActorDeadError

from agent.base import Actor

__all__ = ['Receiver', 'Consumer', 'Publisher']

logger = logging.getLogger(__name__)


class Receiver(Actor):
    
    @abstractmethod
    def receive_message(self, message: bytes): ...

class Publisher(Actor):
    CheckConnection = Actor.create_message('CheckConnection')
    ConnectionRevived = Actor.create_message('ConnectionRevived')

    def __init__(self, check_interval):
        super().__init__()
        self.receivers = []
        self.ready = False
        self.CHECK_INTERVAL = check_interval
        
    def on_start(self):
        self.actor_ref.tell(Publisher.CheckConnection)

    def on_receive(self, message):
        if message is Publisher.CheckConnection:
            self.check_connection()
            self.emit_after(Publisher.CheckConnection, self.CHECK_INTERVAL)
    
    def register_receiver(self, receiver: Actor):
        """Регистрация акторов для отправки 
        уведомлений о восстановлении соединения"""
        
        self.receivers.append(receiver)
    
    def notify_receivers(self):
        for receiver in self.receivers:
            try:
                receiver.tell(Publisher.ConnectionRevived)
            except ActorDeadError:
                self.receivers.remove(receiver)
                
    @abstractmethod
    def check_connection(self): ...
    
    @abstractmethod
    def publish(self, message_id: str, body: bytes, target: str): ...

    @abstractmethod
    def mass_publish(self, messages: Tuple[str, bytes, str]): ...


class Consumer(Actor):
    DrainEvents = Actor.create_message('DrainEvents')
    CheckConnection = Actor.create_message('CheckConnection')
    
    def __init__(self, check_interval: int, 
                 listen_events_types: list, server_side: bool):
        super().__init__()
        self.receivers = {}
        self.ready = False
        self.CHECK_INTERVAL = check_interval
        self.LISTEN_EVENTS_TYPES = listen_events_types
        self.SERVER_SIDE = server_side

    def register_receiver(self, receiver: Receiver, listen_path: str):
        self.receivers[listen_path] = receiver

    def restore_consumers(self):
        for listen_path, receiver in self.receivers.items():
            self.actor_ref.tell(Consumer.DrainEvents)

    def on_start(self):
        self.actor_ref.tell(Consumer.CheckConnection)
        
    def on_receive(self, message):
        if message is Consumer.CheckConnection:
            self.check_connection()
        if message is Consumer.DrainEvents:
            self.drain_events()
            self.emit_after(Consumer.DrainEvents, self.CHECK_INTERVAL)
    
    @abstractmethod
    def drain_events(self): ...

    @abstractmethod
    def check_connection(self): ...