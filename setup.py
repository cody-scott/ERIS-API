import setuptools

import configparser
config = configparser.ConfigParser()
config.read('pyproject.toml')
n = config['tool.poetry']['name'].replace('"','')
v = config['tool.poetry']['version'].replace('"','')


setuptools.setup(
    name=n,
    version=v
)