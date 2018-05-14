import logging
import os, sys
from subprocess import call

class DataGenerationUtil:

    def __init__(self):
        self.log = logging.getLogger(__name__)

    def get_docker_host_hostname(self):
        hostname = '172.17.0.1'
        if sys.platform.startswith('darwin'):
            return 'docker.for.mac.localhost'
        if sys.platform.startswith('win'):
            return '10.0.75.1'
        return hostname

    def fix_docker_host_hostname(self, url):
        return url.replace('localhost', self.get_docker_host_hostname())

    # Generate docker packages
    def generate_docker_packages(self, name, namespace, numpackages, numversions, numlayers, size,
                                    buildnumber, baseimage, registry, username, password):
        self.log.info('Generating ' + str(numpackages * numversions) + ' (' + str(numpackages) + ' * ' + str(numversions) + ') docker images...')
        fixed_registry = self.fix_docker_host_hostname(registry)
        generatorimage = 'solengha-dockerv2.jfrog.io/soldev/qa/docker-generator:generic'
        call (['docker', 'pull', generatorimage])
        call(['docker', 'run', '--rm', '--privileged',
            '-e', 'DNAME=' + name,
            '-e', 'NAMESPACE=' + namespace,
            '-e', 'INUM=' + str(numpackages),
            '-e', 'NUMOFTAGS=' + str(numversions),
            '-e', 'LNUM=' + str(numlayers),
            '-e', 'FNUM=1',
            '-e', 'SIZE=' + size,
            '-e', 'BUILD_NUMBER=' + str(buildnumber),
            '-e', 'MODE=bp',
            '-e', 'baseImage=' + baseimage,
            '-e', 'DOCKER_REGISTRY=' + fixed_registry,
            '-e', 'ARTIUSER=' + username,
            '-e', 'PASSWORD=' + password,
            generatorimage])
