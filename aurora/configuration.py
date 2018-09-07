import os
import json
from configparser import RawConfigParser
from typing import List, Dict

config_dir_path = os.path.dirname(os.path.realpath(__file__)) + '/../config/'


class Channel(object):
    def __init__(self, d):
        self.pin: int = None
        self.label: str = None
        self.device: str = None
        self.__dict__ = d

    def __eq__(self, other):
        return self.pin == other.pin \
               and self.label == other.label \
               and self.device == other.device

    def __ne__(self, other):
        return not self.__eq__(other)


class Configuration(object):

    class Core(object):
        def __init__(self, config: RawConfigParser):
            section = 'core'
            self.hostname: str = config.get(section, 'hostname')
            self.port: int = config.getint(section, 'port')
            self.debug: bool = config.getboolean(section, 'debug')
            self.openapi: bool = config.getboolean(section, 'openapi')
            self.process_name = "aurora-server"
            self.serverName: str = config.get(section, 'serverName')
            self.description: str = config.get(section, 'description')
            self.version = "2.3.0"
            self.logo = """
     ____       __         _______     ________   _______        ____
    /    \     |  |       |_____  \   /   __   \ |_____  \      /    \ 
   /  /\  \    |  |   __   _____)  |  |  |  |  |  _____)  |    /  /\  \ 
  /  /  \__\   |  |  |  | |_____  |   |  |  |  | |_____  |    /  /  \__\ 
 /  /     ___  |  |__|  |       \  \  |  |__|  |      \  \   /  /     ___ 
/__/      \__\ \________/        \__\ \________/       \__\ /__/      \__\ 

           --     Light Server     --     Version 2.3.0     --
"""

    class Hardware(object):
        def __init__(self, config: RawConfigParser):
            section = 'hardware'
            self.channels: List[Channel] = []
            self.channels_dict: Dict[int, Channel] = {}
            for json_pin in json.loads(config.get(section, 'channels')):
                self.channels.append(Channel(json_pin))
                self.channels_dict[int(json_pin['pin'])] = Channel(json_pin)

    class Filter(object):
        def __init__(self, d):
            self.name = 'default'
            self.attenuate_pct = 50
            self.sd_low = 0.4
            self.sd_high = 0.85
            self.decay_factor = 0
            self.delay = 1.0
            self.chunk_size = 2048
            self.sample_rate = 48000
            self.min_frequency = 20
            self.max_frequency = 15000
            self.custom_channel_mapping = 0
            self.custom_channel_frequencies = 0
            self.input_channels = 2
            if d is not None:
                self.__dict__ = d

    def __init__(self):
        config = RawConfigParser()
        config.read(config_dir_path + 'aurora.conf')

        self.core = Configuration.Core(config)
        self.hardware = Configuration.Hardware(config)

        self.filters = []
        for v_dict in json.loads(config.get('visualizer', 'filters')):
            self.filters.append(Configuration.Filter(v_dict))
