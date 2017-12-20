import yaml
import numpy as np


class ConfigParser:

    def __init__(self, file_path):
        with open(file_path, 'r') as config:
            self.config = yaml.load(config)
            # print self.config

    def get_by_key(self, key):
        if key in self.config:
            self.key = key
            return self.config[key]

    def flatten(self, l):
        return self.flatten(l[0]) + (self.flatten(l[1:]) if len(l) > 1 else []) if type(l) is list else [l]

    def merge_sub_groups(self, from_, what_):
        for value in self.config[self.key][from_]:
            value[what_] = self.flatten(value[what_])
