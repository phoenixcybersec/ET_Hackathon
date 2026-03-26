import yaml
import os


class Config:
    def __init__(self, path="config/config.yaml"):
        with open(path, "r") as file:
            self.config = yaml.safe_load(file)

    def get(self, *keys, default=None):
        data = self.config
        for key in keys:
            data = data.get(key, {})
        return data or default


config = Config()