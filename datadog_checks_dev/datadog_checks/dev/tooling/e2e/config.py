# (C) Datadog, Inc. 2018
# All rights reserved
# Licensed under a 3-clause BSD style license (see LICENSE)
import json

import yaml

from ..config import APP_DIR
from ...utils import ensure_dir_exists, path_join, write_file

ENV_DIR = path_join(APP_DIR, 'envs')


def locate_env_dir(check, env):
    return path_join(ENV_DIR, check, env)


def locate_config_dir(check, env):
    return path_join(locate_env_dir(check, env), 'config')


def locate_config_file(check, env):
    return path_join(locate_config_dir(check, env), '{}.yaml'.format(check))


def locate_metadata_file(check, env):
    return path_join(locate_env_dir(check, env), 'metadata.json')


def write_env_data(check, env, config=None, metadata=None):
    ensure_dir_exists(locate_config_dir(check, env))

    if config:
        write_file(locate_config_file(check, env), config_to_yaml(config))

    if metadata:
        write_file(locate_metadata_file(check, env), metadata_to_json(metadata))


def config_to_yaml(config):
    if 'instances' not in config:
        config = {'instances': [config]}

    # Agent 5 requires init_config
    if 'init_config' not in config:
        config = {
            'init_config': {},
            **config,
        }

    return yaml.dump(config, default_flow_style=False)


def metadata_to_json(metadata):
    return json.dumps(metadata, indent=2, separators=(',', ': '))
