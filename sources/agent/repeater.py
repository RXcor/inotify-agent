from .transmission.abstract import Consumer, Receiver
from .transmission.sender import Sender


__all__ = ['Repeater']
    

class Repeater(Receiver):

    def __init__(self,
                 consumer: Consumer,
                 sender: Sender,
                 listen_path: str, exchange: str):
        super().__init__()
        self.consumer = consumer.proxy()
        self.sender = sender.proxy()        
        self.exchange = exchange
        self.listen_path = listen_path
        
        self.consumer.register_receiver(self.actor_ref.proxy(), listen_path)

    def receive_message(self, message): 
        self.sender.send(message, self.exchange)
