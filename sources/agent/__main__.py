import logging.config
import os

from agent.base import Actor
from agent import amqp, mqtt, inotify_watcher, watchdog_consumer
from agent.transmission import Sender
from .repeater import Repeater

from .config import ini_config


logging.basicConfig(level=logging.INFO)

LOGGING_CONF = os.getenv('LOGGING_CONF')
if LOGGING_CONF is None:
    LOGGING_CONF = os.path.join(os.getcwd(), 'logging.ini')

if os.path.isfile(LOGGING_CONF):
    logging.config.fileConfig(fname=LOGGING_CONF,
                              disable_existing_loggers=False)
    
def create_broker_client(config, broker_name):
    broker_type = config['broker_protocol']
    if broker_type.lower() == 'amqp':
        publisher_cls = amqp.AMQPPublisher
        connection_fabric = amqp.ConnectionFabric(
            host=config['broker_host'],
            login=config['broker_login'],
            password=config['broker_password'],
            virtual_host=config['broker_virtual_host'],
            ssl = config.getboolean('ssl'),
        )
        
    elif broker_type.lower() == 'mqtt':
        publisher_cls = mqtt.MQTTPublisher
        connection_fabric = mqtt.ConnectionFabric(
            host=config['broker_host'],
            port=config.getint('broker_port'),
            login=config.get('broker_login'),
            password=config.get('broker_password'),
        )
    else:
        raise ValueError(f'Unsupported protocol for broker "{broker_name}"')
    publisher = publisher_cls.start(
        connection_fabric=connection_fabric,
        check_interval=config.getfloat('publisher_check_interval'),
    )
    sender = Sender.start(
        publisher=publisher,
    )
    return sender

def create_watcher(config):
    watcher = inotify_watcher.InotifyConsumer.start(
        listen_events_types = config['listen_events_types'].split(','),
        server_side = config.getboolean('server_side'), 
        listen_dir = config.get('listen_dir'))
    return watcher

def create_watchdog(config):
    watchdog = watchdog_consumer.WatchdogConsumer.start(
        listen_events_types = config['listen_events_types'].split(','),
        server_side = config.getboolean('server_side'), 
        listen_dir = config.get('listen_dir'))
    return watchdog
    

def create_repeater(config, broker):
    # consumer = create_watcher(config) 
    consumer = create_watchdog(config)
    sender = broker
        
    return Repeater.start(
        consumer=consumer,
        sender=sender,
        listen_path=config['listen_dir'],
        exchange=config['target_point'],
    )

# brokers = {}
# brokers_names = ini_config['brokers']['names'].split(',')
# for name in brokers_names:
#     section = ini_config[f'{name}_broker']
#     brokers[name] = create_broker_client(section, name)

bindings = {}
bindings_names = ini_config['bindings']['names'].split(',')
for name in bindings_names:
    binding_section = ini_config[f'binding_{name}']    
    broker_name = binding_section['target_broker']
    broker_section = ini_config[f'{broker_name}_broker']    
    broker = create_broker_client(broker_section, broker_section)
    bindings[name] = create_repeater(binding_section, broker)

Actor.run_until_interrupt()
