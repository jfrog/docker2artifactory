import unittest
import os, sys
import util.LogUtils as LogUtils
import util.ArtifactoryUtil as ArtifactoryUtil
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from migrator import UCPAccess
from migrator import DTRAccess
from migrator import DockerEESecurityMigrator
from migrator import ArtifactoryUserAccess

@unittest.skip("Require work for generic use.")
class DockerEESecurityMigratorTest(unittest.TestCase):

    def setUp(self):
        LogUtils.start_logging()
        self.artutil = ArtifactoryUtil.ArtifactoryUtil()

        # Artifactory configuration
        self.artversion = 'latest'
        self.artport = '8081'
        self.artcontainername = 'artifactory'

        # Start Artifactory
        if not self.artutil.start_artifactory(self.artversion, self.artport, self.artcontainername):
            sys.exit('Failed to create the Artifactory instance')

        # Create target docker repo
        self.artaccess = self.artutil.get_artifactory_access(self.artport)
        self.artaccess.create_local_repo('docker-local', 'docker', 'simple-default')

        # Services access
        self.ucp = UCPAccess.UCPAccess(
            'https://ucpsoldev.jfrog.team', username='admin', password='password')
        self.dtr = DTRAccess.DTRAccess(
            'https://dtrsoldev.jfrog.team', username='admin', password='password')
        self.art_user = ArtifactoryUserAccess.ArtifactoryUserAccess(
            'http://localhost:8081/artifactory', username='admin', password='password')
        self.migrator = DockerEESecurityMigrator.DockerEESecurityMigrator(
            self.ucp, self.dtr, self.art_user, 'docker-local', True)

    def tearDown(self):
        self.artutil.delete_instance(self.artcontainername)

    def test_migration(self):
        self.migrator.migrate()

        # Check users migrated
        self.assertTrue(self.art_user.user_exists('user1'))
        self.assertTrue(self.art_user.user_exists('user2'))
        self.assertTrue(self.art_user.user_exists('user3'))
        self.assertTrue(self.art_user.user_exists('user4'))
        self.assertTrue(self.art_user.user_exists('user5'))
        self.assertTrue(self.art_user.user_exists('user6'))

        # Check groups migrated
        self.assertTrue(self.art_user.group_exists('my-org-admin'))
        self.assertTrue(self.art_user.group_exists('my-org-qa'))
        self.assertTrue(self.art_user.group_exists('my-org-dev'))

        # Check permissions migrated
        self.assertTrue(self.art_user.permission_exists('user1'))
        self.assertTrue(self.art_user.permission_exists('user2'))
        self.assertTrue(self.art_user.permission_exists('user3'))
        self.assertTrue(self.art_user.permission_exists('user4'))
        self.assertTrue(self.art_user.permission_exists('user5'))
        self.assertTrue(self.art_user.permission_exists('user6'))
        self.assertTrue(self.art_user.permission_exists('my-org/my-repo'))
        self.assertTrue(self.art_user.permission_exists('my-org/alpine'))

if __name__ == '__main__':
    unittest.main()
