import unittest
import util.LogUtils as LogUtils
import util.GenericRegistryUtil as GenericRegistryUtil
import util.DataGenerationUtil as DataGenerationUtil
import util.ArtifactoryUtil as ArtifactoryUtil
import util.ArtifactoryAccess as ArtifactoryAccess
import util.DockerMigratorUtil as DockerMigratorUtil
import sys

class GenericMigrationTest(unittest.TestCase):

    def setUp(self):
        LogUtils.start_logging()

        self.genericregistryutil = GenericRegistryUtil.GenericRegistryUtil()
        self.artutil = ArtifactoryUtil.ArtifactoryUtil()
        self.datagenerationutil = DataGenerationUtil.DataGenerationUtil()
        self.migratorutil = DockerMigratorUtil.DockerMigratorUtil()

        # Artifactory configuration
        self.artversion = 'latest'
        self.artport = '8081'
        self.artcontainername = 'artifactory'

        # Generic Registry Configuration
        self.registryname = 'registry'
        self.registryport = '5000'

        # Start generic registry
        if not self.genericregistryutil.start_generic_docker_repo(self.registryname, self.registryport):
            sys.exit('Failed to create the Generic Registry instance')

        # Start Artifactory
        if not self.artutil.start_artifactory(self.artversion, self.artport, self.artcontainername):
            sys.exit('Failed to create the Artifactory instance')

    def tearDown(self):
        self.genericregistryutil.delete_generic_docker_repo(self.registryname)
        self.artutil.delete_instance(self.artcontainername)

    def test_all_images_migration(self):
        # Data configuration
        baseimage = 'busybox'

        numofimages = 2
        numoftags = 2
        numoflayers = 5
        layersize = '10000K'

        buildnumber = 1
        imagenamespace = 'test'
        imagename = 'image'

        # Artifactory configuration
        dockerrepo = 'docker-local'

        # Generate docker images
        self.datagenerationutil.generate_docker_packages(imagename, imagenamespace, numofimages,
            numoftags, numoflayers, layersize, buildnumber, baseimage,
            'localhost:5000', 'user', 'password')

        # Create target docker repo
        self.artaccess = self.artutil.get_artifactory_access(self.artport)
        self.artaccess.create_local_repo(dockerrepo, 'docker', 'simple-default')

        # Execute Migration
        self.assertTrue(self.migratorutil.perform_migration(['generic', 'http://localhost:' + self.registryport,
            'http://localhost:' + self.artport + '/artifactory', 'admin', 'password', dockerrepo]))

        # Validate migrated docker images
        for image in range(numofimages):
            for tag in range(numoftags):
                self.assertTrue(self.artutil.validate_generated_docker_image(self.artport, dockerrepo,
                                imagenamespace, imagename, image + 1, tag, buildnumber))

    def test_selected_image_migration(self):
        # Data configuration
        baseimage = 'busybox'
        numofimages = 1
        numoftags = 4
        numoflayers = 3
        layersize = '1K'
        buildnumber = 1
        imagenamespace = 'test'
        should_migrate_imagename = 'image-a'
        should_not_migrate_imagename = 'image-b'

        # Artifactory configuration
        dockerrepo = 'docker-local'

        # Generate docker images that will be migrated
        self.datagenerationutil.generate_docker_packages(should_migrate_imagename, imagenamespace, numofimages,
            numoftags, numoflayers, layersize, buildnumber, baseimage,
            'localhost:5000', 'user', 'password')

        # Generate docker images that shoul not be migrate
        self.datagenerationutil.generate_docker_packages(should_not_migrate_imagename, imagenamespace, numofimages,
            numoftags, numoflayers, layersize, buildnumber, baseimage,
            'localhost:5000', 'user', 'password')

        # Create target docker repo
        self.artaccess = self.artutil.get_artifactory_access(self.artport)
        self.artaccess.create_local_repo(dockerrepo, 'docker', 'simple-default')

        # Execute Migration
        self.assertTrue(self.migratorutil.perform_migration(['generic',
            '--image-file', self.migratorutil.get_resources_absolute_path('image-file.txt'),
            'http://localhost:' + self.registryport,
            'http://localhost:' + self.artport + '/artifactory', 'admin', 'password', dockerrepo]))

        # Validate migrated docker images
        for tag in range(numoftags):
            self.assertTrue(self.artutil.validate_generated_docker_image(self.artport, dockerrepo,
                            imagenamespace, should_migrate_imagename, 1, tag, buildnumber))

        # Validate non migrated docker images
        for tag in range(numoftags):
            self.assertFalse(self.artutil.validate_generated_docker_image(self.artport, dockerrepo,
                            imagenamespace, should_not_migrate_imagename, 1, tag, buildnumber))

    def test_selected_tag_migration(self):
        # Data configuration
        baseimage = 'busybox'
        numofimages = 1
        numoftags = 4
        numoflayers = 3
        layersize = '1K'
        buildnumber = 1
        imagenamespace = 'test'
        should_migrate_imagename = 'image-a'

        # Artifactory configuration
        dockerrepo = 'docker-local'

        # Generate docker images that will be migrated
        self.datagenerationutil.generate_docker_packages(should_migrate_imagename, imagenamespace, numofimages,
            numoftags, numoflayers, layersize, buildnumber, baseimage,
            'localhost:5000', 'user', 'password')

        # Create target docker repo
        self.artaccess = self.artutil.get_artifactory_access(self.artport)
        self.artaccess.create_local_repo(dockerrepo, 'docker', 'simple-default')

        # Execute Migration
        self.assertTrue(self.migratorutil.perform_migration(['generic',
            '--image-file', self.migratorutil.get_resources_absolute_path('tag-file.txt'),
            'http://localhost:' + self.registryport,
            'http://localhost:' + self.artport + '/artifactory', 'admin', 'password', dockerrepo]))

        # Validate migrated docker images
        for tag in range(2):
            self.assertTrue(self.artutil.validate_generated_docker_image(self.artport, dockerrepo,
                            imagenamespace, should_migrate_imagename, 1, tag, buildnumber))

        # Validate non migrated docker images
        for tag in range(2,4):
            self.assertFalse(self.artutil.validate_generated_docker_image(self.artport, dockerrepo,
                            imagenamespace, should_migrate_imagename, 1, tag, buildnumber))

    def test_overwrite_option(self):
        # Data configuration
        baseimage = 'busybox'
        numofimages = 1
        numoftags = 1
        numoflayers = 3
        layersize = '10K'
        buildnumber = 1
        imagenamespace = 'test'
        imagename = 'image'

        # Artifactory configuration
        dockerrepo = 'docker-local'

        # Create target docker repo
        self.artaccess = self.artutil.get_artifactory_access(self.artport)
        self.artaccess.create_local_repo(dockerrepo, 'docker', 'simple-default')

        # Add a broken docker image to Artifactory
        self.assertTrue(self.artaccess.upload_file('/docker-local/test/image1-1/1.0/manifest.json',
            'application/json', self.migratorutil.get_resources_absolute_path('invalid_metadata.json')))

        # Generate docker images
        self.datagenerationutil.generate_docker_packages(imagename, imagenamespace, numofimages,
            numoftags, numoflayers, layersize, buildnumber, baseimage,
            'localhost:5000', 'user', 'password')

        # Execute Migration without Overwrite
        self.assertTrue(self.migratorutil.perform_migration(['generic', 'http://localhost:' + self.registryport,
            'http://localhost:' + self.artport + '/artifactory', 'admin', 'password', dockerrepo]))

        # Validate docker images still broken
        self.assertFalse(self.artutil.validate_generated_docker_image(self.artport, dockerrepo,
                        imagenamespace, imagename, 1, 0, buildnumber))

        # Execute Migration with Overwrite
        self.assertTrue(self.migratorutil.perform_migration(['generic', '--overwrite', 'http://localhost:' + self.registryport,
            'http://localhost:' + self.artport + '/artifactory', 'admin', 'password', dockerrepo]))

        # Validate migrated docker images
        self.assertTrue(self.artutil.validate_generated_docker_image(self.artport, dockerrepo,
                        imagenamespace, imagename, 1, 0, buildnumber))

if __name__ == '__main__':
    unittest.main()
