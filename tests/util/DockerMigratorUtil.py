import logging
import os
from subprocess import call

class DockerMigratorUtil:

    def __init__(self):
        self.log = logging.getLogger(__name__)

    def perform_migration(self, args):
        migratorDir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        toolPath = os.path.join(migratorDir, 'DockerMigrator.py')
        code = call(['python', toolPath] + args + ['-v'])
        if code != 0:
            return False
        return True

    def get_resources_absolute_path(self, filename):
        resourcesPath = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'resources')
        filePath = os.path.join(resourcesPath, filename)
        return filePath
