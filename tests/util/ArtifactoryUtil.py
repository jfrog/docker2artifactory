import os
import sys
import time
import logging
from subprocess import call
import ArtifactoryAccess

class ArtifactoryUtil:
    def __init__(self):
        self.log = logging.getLogger(__name__)

    def start_artifactory(self, version, port, name):
        self.log.info('Starting artifactory container with name: ' + name)
        license_contents = self.get_license_configuration()
        code = call(['docker', 'run', '--name', name, '-d', '-p', port + ":8081",
                  'jfrog-docker-reg2.bintray.io/jfrog/artifactory-pro:' + version])
        if code != 0:
            return False
        url = 'http://localhost:' + port + '/artifactory'
        art = ArtifactoryAccess.ArtifactoryAccess(url, 'admin', 'password')
        for i in range(0, 12):
            self.log.info('Sleeping for 10 seconds to let Artifactory startup...')
            time.sleep(10)
            if art.get_license():
                return art.install_license(license_contents)
            else:
                self.log.info('Artifactory is still not up.')
        return False

    def get_artifactory_access(self, port):
        url = 'http://localhost:' + port + '/artifactory'
        return ArtifactoryAccess.ArtifactoryAccess(url, 'admin', 'password')

    def get_license_configuration(self):
        try:
            with open(os.path.dirname(os.path.dirname(os.path.abspath(__file__))) + '/config/artifactory.lic', 'r') as myfile:
                return myfile.read()
        except IOError as ex:
            sys.exit('Unable to read license from config/artifactory.lic')

    def delete_instance(self, name):
        self.log.info('Deleting artifactory container with name: ' + name)
        call(['docker', 'rm', '-f', name])

    def validate_generated_docker_image(self, port, reponame, imagenamespace, imagename, package, tagversion, buildnumber):
        art = self.get_artifactory_access(port)
        generatedimage = '{0}{1}-{2}'.format(imagename, package, buildnumber)
        generatedtag = '1.{0}'.format(tagversion)
        return self.validate_docker_image(port, reponame, imagenamespace, generatedimage, generatedtag)

    def validate_docker_image(self, port, reponame, imagenamespace, imagename, tagversion):
        art = self.get_artifactory_access(port)
        tagpath = '{0}/{1}/{2}/'.format(imagenamespace, imagename, tagversion)

        # Validate manifest file
        manifestpath = tagpath + 'manifest.json'
        manifest = art.get_artifact_json_content(reponame, manifestpath)
        if not manifest:
            return False

        # Validate layers
        layers = []

        # Schema V1
        if manifest['schemaVersion'] == 1:
            for layer in manifest['fsLayers']:
                layers.append(layer['blobSum'])

        # Schema V2
        else:
            layers.append(manifest['config']['digest'])
            for layer in manifest['layers']:
                layers.append(layer['digest'])

        for layer in layers:
            layerpath = tagpath + layer.replace(':', '__')
            layer_exists = art.artifact_exists(reponame, layerpath)
            if not layer_exists:
                return False
        return True
