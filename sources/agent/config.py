import configparser
import os

__all__ = ['ini_config']


ini_config = configparser.ConfigParser()

config_path = os.getenv('BINDINGS_CONF', 'bindings.ini')

if not os.path.isabs(config_path):
    config_path = os.path.join(
        os.getcwd(),
        config_path
    )


if not os.path.exists(config_path):
    raise FileNotFoundError(f'File {config_path} do not exists')

ini_config.read(config_path)
