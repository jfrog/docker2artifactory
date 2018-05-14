import logging
from subprocess import call

class GenericRegistryUtil:

    def __init__(self):
        self.log = logging.getLogger(__name__)

    def start_generic_docker_repo(self, name, port):
        self.log.info('Starting generic docker registry with name: ' + name)
        code = call(['docker', 'run', '-d', '-p', port + ':5000', '--name', name, 'registry:2'])
        if code != 0:
            return False
        return True

    def delete_generic_docker_repo(self, name):
        self.log.info('Deleting generic docker registry with name: ' + name)
        call(['docker', 'rm', '-f', name])
