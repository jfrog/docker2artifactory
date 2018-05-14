import logging
import ConfigParser
import os

class ConfigUtil:

    def __init__(self):
        self.log = logging.getLogger(__name__)

    def read_config_file(self, filename):
        config = ConfigParser.ConfigParser()
        config.read(os.path.dirname(os.path.dirname(os.path.abspath(__file__))) + '/config/' + filename)
        return config
