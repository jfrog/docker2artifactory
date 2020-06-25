import unittest
import util.LogUtils as LogUtils
import util.GenericRegistryUtil as GenericRegistryUtil
import util.DataGenerationUtil as DataGenerationUtil
import util.ArtifactoryUtil as ArtifactoryUtil
import util.ArtifactoryAccess as ArtifactoryAccess
import util.DockerMigratorUtil as DockerMigratorUtil
import util.ConfigUtil as ConfigUtil
import sys

@unittest.skip("Require work for generic use.")
class QuayMigrationTest(unittest.TestCase):

    def setUp(self):
        LogUtils.start_logging()

        self.artutil = ArtifactoryUtil.ArtifactoryUtil()
        self.migratorutil = DockerMigratorUtil.DockerMigratorUtil()
        self.configutil = ConfigUtil.ConfigUtil()

        # Read test Configuration
        self.config = self.configutil.read_config_file('quay_test_data.ini')

        # Artifactory configuration
        self.artversion = 'latest'
        self.artport = '8081'
        self.artcontainername = 'artifactory'

        # Start Artifactory
        if not self.artutil.start_artifactory(self.artversion, self.artport, self.artcontainername):
            sys.exit('Failed to create the Artifactory instance')

    def tearDown(self):
        self.artutil.delete_instance(self.artcontainername)        

    def test_all_images_migration(self):
        # Data configuration
        baseimage = 'busybox'

        # Test configuration
        quaynamespace = self.config.get('Quay', 'namespace')
        quaytoken = self.config.get('Quay', 'token')
        imagename = self.config.get('Quay', 'imagename')
        imagetag = self.config.get('Quay', 'imagetag')

        # Artifactory configuration
        dockerrepo = 'docker-local'

        # Create target docker repo
        self.artaccess = self.artutil.get_artifactory_access(self.artport)
        self.artaccess.create_local_repo(dockerrepo, 'docker', 'simple-default')

        # Execute Migration
        self.assertTrue(self.migratorutil.perform_migration(['quay', quaynamespace, quaytoken,
            'http://localhost:' + self.artport + '/artifactory', 'admin', 'password', dockerrepo]))

        # Validate migrated docker image
        self.assertTrue(self.artutil.validate_docker_image(self.artport, dockerrepo,
            quaynamespace, imagename, imagetag))

if __name__ == '__main__':
    unittest.main()
