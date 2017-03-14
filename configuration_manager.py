from configparser import RawConfigParser
import os
import json


config_dir_path = os.path.dirname(os.path.realpath(__file__)) + '/config/'


class Configuration(object):

    def __init__(self):
        self.config = RawConfigParser()
        self.config.read(config_dir_path + 'aurora.conf')

        self.core = None
        self.hardware = None
        self.static_light = None
        self.light_show = None

        self.set_core()
        self.set_hardware()
        self.set_static_light()
        self.set_light_show()

    def set_core(self):
        section = 'core'
        core = dict()

        core['port'] = self.config.getint(section, 'port')
        core['hostname'] = self.config.get(section, 'hostname')

        self.core = Section(core)

    def set_hardware(self):
        section = 'hardware'
        hdwr = dict()

        hdwr['red_pin'] = self.config.getint(section, 'red_pin')
        hdwr['green_pin'] = self.config.getint(section, 'green_pin')
        hdwr['blue_pin'] = self.config.getint(section, 'blue_pin')

        self.hardware = Section(hdwr)

    def set_static_light(self):
        section = 'static_light'
        sl = dict()

        sl['enabled'] = self.config.getboolean(section, 'enabled')
        sl['run_at_start'] = self.config.getboolean(section, 'run_at_start')
        sl['initial_preset'] = json.loads(self.config.get(section, 'initial_preset'))

        self.static_light = Section(sl)

    def set_light_show(self):
        section = 'light_show'
        ls = dict()

        ls['enabled'] = self.config.getboolean(section, 'enabled')
        ls['run_at_start'] = self.config.getboolean(section, 'run_at_start')

        ls['fifo_path'] = self.config.get(section, 'fifo_path')
        ls['attenuate_pct'] = self.config.getint(section, 'attenuate_pct')
        ls['SD_low'] = self.config.getfloat(section, 'SD_low')
        ls['SD_high'] = self.config.getfloat(section, 'SD_high')
        ls['decay_factor'] = self.config.getfloat(section, 'decay_factor')
        ls['delay'] = self.config.getfloat(section, 'delay')
        ls['chunk_size'] = self.config.getint(section, 'chunk_size')
        ls['sample_rate'] = self.config.getint(section, 'sample_rate')
        ls['min_frequency'] = self.config.getint(section, 'min_frequency')
        ls['max_frequency'] = self.config.getint(section, 'max_frequency')
        ls['input_channels'] = self.config.getint(section, 'input_channels')

        temp = self.config.get(section, 'custom_channel_mapping')
        ls["custom_channel_mapping"] = map(int, temp.split(',')) if temp else 0
        temp = self.config.get(section, 'custom_channel_frequencies')
        ls["custom_channel_frequencies"] = map(int, temp.split(',')) if temp else 0

        self.light_show = Section(ls)


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
