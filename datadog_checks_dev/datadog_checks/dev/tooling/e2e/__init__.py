# (C) Datadog, Inc. 2018
# All rights reserved
# Licensed under a 3-clause BSD style license (see LICENSE)
from .docker import DockerInterface
from .run import start_environment, stop_environment


def get_interface(env_type):
    if env_type == 'docker':
        return DockerInterface
