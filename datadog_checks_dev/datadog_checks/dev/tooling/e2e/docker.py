# (C) Datadog, Inc. 2018
# All rights reserved
# Licensed under a 3-clause BSD style license (see LICENSE)
import re

from .agent import DEFAULT_AGENT_VERSION, FAKE_API_KEY, get_agent_exe, get_agent_conf_dir
from .config import locate_config_dir, locate_config_file, locate_env_dir, write_env_data
from ..constants import get_root
from ...subprocess import run_command
from ...utils import path_join, remove_path

MANIFEST_VERSION_PATTERN = 'agent (\d)'


class DockerInterface(object):
    def __init__(self, check, env, config=None, metadata=None, agent_build=None, api_key=None):
        self.check = check
        self.env = env
        self.config = config or {}
        self.metadata = metadata or {}
        self.agent_build = agent_build
        self.api_key = api_key or FAKE_API_KEY

        self._agent_version = None
        self.container_name = 'dd_{}_{}'.format(self.check, self.env)
        self.config_dir = locate_config_dir(check, env)
        self.config_file = locate_config_file(check, env)

    @property
    def agent_version(self):
        return self._agent_version or DEFAULT_AGENT_VERSION

    @property
    def check_mount_dir(self):
        return '/home/{}'.format(self.check)

    @property
    def agent_command(self):
        return 'docker exec {} {}'.format(
            self.container_name,
            get_agent_exe(self.agent_version)
        )

    def remove_config(self):
        remove_path(locate_env_dir(self.check, self.env))

    def write_config(self):
        write_env_data(self.check, self.env, self.config, self.metadata)

    def detect_agent_version(self):
        command = [
            'docker', 'run', '-e', 'DD_API_KEY={}'.format(self.api_key), self.agent_build,
            'head', '--lines=1', '/opt/datadog-agent/version-manifest.txt'
        ]
        if self.agent_version is None:
            result = run_command(command, capture=True)
            match = re.search(MANIFEST_VERSION_PATTERN, result.stdout)
            if match:
                self._agent_version = int(match.group(1))

            self.metadata['agent_version'] = self.agent_version

    def update_check(self):
        command = [
            'docker', 'exec', self.container_name, 'pip', 'install', '-e', self.check_mount_dir
        ]
        run_command(command, capture=True, check=True)

    def update_agent(self):
        run_command(['docker', 'pull', self.agent_build], capture=True, check=True)

    def start_agent(self):
        command = [
            'docker', 'run',
            # Keep it up
            '-d',
            # Ensure consistent naming
            '--name', self.container_name,
            # Ensure access to host network
            '--network', 'host',
            # Agent 6 will simply fail without an API key
            '-e', 'DD_API_KEY={}'.format(self.api_key),
            # Mount the config directory, not the file, to ensure updates are propagated
            # https://github.com/moby/moby/issues/15793#issuecomment-135411504
            '-v', '{}:{}'.format(self.config_dir, get_agent_conf_dir(self.check, self.agent_version)),
            # Mount the check directory
            '-v', '{}:{}'.format(path_join(get_root(), self.check), self.check_mount_dir),
            # The chosen tag
            self.agent_build
        ]
        return run_command(command, capture=True)

    def stop_agent(self):
        run_command(['docker', 'stop', self.container_name], capture=True)
        run_command(['docker', 'rm', self.container_name], capture=True)


def get_docker_networks():
    command = ['docker', 'network', 'ls', '--format', '{{.Name}}']
    lines = run_command(command, capture='out', check=True).stdout.splitlines()

    return [line.strip() for line in lines]
