import unittest
import util.LogUtils as LogUtils
import util.GenericRegistryUtil as GenericRegistryUtil
import util.DataGenerationUtil as DataGenerationUtil
import util.ArtifactoryUtil as ArtifactoryUtil
import util.ArtifactoryAccess as ArtifactoryAccess
import util.DockerMigratorUtil as DockerMigratorUtil
import util.ConfigUtil as ConfigUtil
import sys
import tempfile

@unittest.skip("Require work for generic use.")
class AuthenticatedGenericMigrationTest(unittest.TestCase):

    def setUp(self):
        LogUtils.start_logging()

        self.genericregistryutil = GenericRegistryUtil.GenericRegistryUtil()
        self.artutil = ArtifactoryUtil.ArtifactoryUtil()
        self.datagenerationutil = DataGenerationUtil.DataGenerationUtil()
        self.migratorutil = DockerMigratorUtil.DockerMigratorUtil()
        self.configutil = ConfigUtil.ConfigUtil()

        # Read test Configuration
        self.config = self.configutil.read_config_file('dtr_test_data.ini')

        # Artifactory configuration
        self.artversion = 'latest'
        self.artport = '8081'
        self.artcontainername = 'artifactory'

        # # Start Artifactory
        if not self.artutil.start_artifactory(self.artversion, self.artport, self.artcontainername):
            sys.exit('Failed to create the Artifactory instance')

    def tearDown(self):
        self.artutil.delete_instance(self.artcontainername)

    def test_selected_image_migration(self):

        # Test configuration
        registryurl = self.config.get('Registry', 'registryurl')
        registryuser= self.config.get('Registry', 'registryuser')
        registrypassword = self.config.get('Registry', 'registrypassword')
        imagenamespace = self.config.get('Repository', 'imagenamespace')
        imagename = self.config.get('Repository', 'imagename')
        imagetag = self.config.get('Repository', 'imagetag')

        # Artifactory configuration
        dockerrepo = 'docker-local'

        # # Create target docker repo
        self.artaccess = self.artutil.get_artifactory_access(self.artport)
        self.artaccess.create_local_repo(dockerrepo, 'docker', 'simple-default')

        # Execute Migration
        self.assertTrue(self.migratorutil.perform_migration(['generic', '--ignore-certs',
            '--source-username', registryuser, '--source-password', registrypassword,
            registryurl, 'http://localhost:' + self.artport + '/artifactory',
            'admin', 'password', dockerrepo]))

        # Validate migrated docker images
        self.assertTrue(self.artutil.validate_docker_image(self.artport, dockerrepo,
            imagenamespace, imagename, imagetag))

if __name__ == '__main__':
    unittest.main()
