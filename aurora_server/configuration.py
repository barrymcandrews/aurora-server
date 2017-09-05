import json
import os
from configparser import RawConfigParser
from typing import List, Dict
from aurora_server.lights import pins

config_dir_path = os.path.dirname(os.path.realpath(__file__)) + '/../config/'


class Configuration(object):

    def __init__(self):
        self.config = RawConfigParser()
        self.config.read(config_dir_path + 'aurora.conf')

        self.core = None
        self.hardware = None
        self.lights = None

        self.set_core()
        self.set_hardware()
        self.set_lights()

    def set_core(self):
        section = 'core'
        core = dict()

        core['port'] = self.config.getint(section, 'port')
        core['hostname'] = self.config.get(section, 'hostname')

        self.core = Section(core)

    def set_hardware(self):
        section = 'hardware'
        hdwr = dict()

        all_pins: List[int] = []
        devices: List[pins.Device] = []

        for name, json_dev in json.loads(self.config.get(section, 'devices')).items():
            mapping: Dict[int, str] = {}
            for pin_str, label in json_dev['channels'].items():
                mapping.update({int(pin_str): label})
                all_pins.append(int(pin_str))
            devices.append(pins.Device(name, mapping))

        hdwr['devices'] = devices
        hdwr['all_pins'] = all_pins

        self.hardware = Section(hdwr)

    def set_lights(self):
        section = 'lights'
        lights = dict()

        lights['initial_preset'] = json.loads(self.config.get(section, 'initial_preset'))

        # Visualization
        lights['fifo_path'] = self.config.get(section, 'fifo_path')
        lights['attenuate_pct'] = self.config.getint(section, 'attenuate_pct')
        lights['SD_low'] = self.config.getfloat(section, 'SD_low')
        lights['SD_high'] = self.config.getfloat(section, 'SD_high')
        lights['decay_factor'] = self.config.getfloat(section, 'decay_factor')
        lights['delay'] = self.config.getfloat(section, 'delay')
        lights['chunk_size'] = self.config.getint(section, 'chunk_size')
        lights['sample_rate'] = self.config.getint(section, 'sample_rate')
        lights['min_frequency'] = self.config.getint(section, 'min_frequency')
        lights['max_frequency'] = self.config.getint(section, 'max_frequency')
        lights['input_channels'] = self.config.getint(section, 'input_channels')

        temp = self.config.get(section, 'custom_channel_mapping')
        lights["custom_channel_mapping"] = map(int, temp.split(',')) if temp else 0
        temp = self.config.get(section, 'custom_channel_frequencies')
        lights["custom_channel_frequencies"] = map(int, temp.split(',')) if temp else 0

        self.lights = Section(lights)


class Section(object):
    def __init__(self, config):
        self.config = config
        self.set_values(self.config)

    def set_config(self, config):
        self.config = config
        self.set_values(self.config)

    def get_config(self):
        return self.config

    def set_value(self, key, value):
        setattr(self, key, value)

    def set_values(self, dict_of_items):
        for key, value in dict_of_items.items():
            setattr(self, key, value)

    def get(self, item):
        return getattr(self, item)

