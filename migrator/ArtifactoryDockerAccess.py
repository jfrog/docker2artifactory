from ArtifactoryBaseAccess import ArtifactoryBaseAccess
import logging
from distutils.version import LooseVersion

'''
    Simple API for uploading Docker images to Artifactory
    * Uses basic AUTH (not tokens)
    * Limited 
    
    Deploy image process:
    
    1. Deploy each (and every non-foreign) layer
      * Try a checksum deploy first
      * If the checksum deploy fails, perform an upload
    2. Deploy the manifest
'''
class ArtifactoryDockerAccess(ArtifactoryBaseAccess):
    def __init__(self, url, repo, username=None, password=None, ignore_cert=False, exlog=False):
        super(ArtifactoryDockerAccess, self).__init__(url, username, password, ignore_cert, exlog)
        self.log = logging.getLogger(__name__)
        self.repo = repo

    '''
        Return true if the user exists
        @param username - The username to check for
    '''
    def user_exists(self, username):
        return bool(self.get_call_wrapper('/api/security/users/' + username))

    '''
        Creates or replaces a user with the specified username
        @param username - The username to create
        @param email - The email of the user
        @param groups - The groups the user should belong to (defaults to none)
        @param admin - True if this user should be an admin (defaults to false)
    '''
    def create_user(self, username, email, password, groups=None, admin=False):

        body = {
            "email": email,
            "password": password,
            "admin": admin
        }
        if groups:
            body.update({"groups": groups})

        resp, stat = self.do_unprocessed_request(method='PUT', path='/api/security/users/' + username, body=body)
        if stat == 201:
            return True
        return False

    '''
        Tries to perform a sha1 checksum deployment
        @param image - The image name
        @param tag - The tag name
        @param layer - The layer sha256 sum
        @param sha1 - The sha1 sum of the layer (this is the checksum that will be used for deployment)
        @return True if successful, else False
    '''
    def checksum_deploy_sha1(self, image, tag, layer, sha1):
        self.log.debug("Trying sha1 deploy of %s/%s with sha2: %s and sha1: %s" % (image, tag, layer, sha1))
        headers = {
            'X-Checksum-Deploy': 'true',
            'X-Checksum-Sha1': sha1,
        }
        path_fragment = "%s/%s/sha256__%s;sha256=%s" % (image, tag, layer, layer)
        resp, stat = self.do_unprocessed_request(method='PUT', path=self.__assemble_path(path_fragment),
                                                 headers=headers)
        if stat == 201:
            return True
        return False


    '''
        Tries to perform a sha2 checksum deployment
        @param image - The image name
        @param tag - The tag name
        @param layer - The layer sha256 sum
        @return True if successful, else False
    '''
    def checksum_deploy_sha2(self, image, tag, layer):
        # Only try in versions that support sha2 and don't run into RTFACT-15096
        if LooseVersion(self.version) < LooseVersion("5.6.0"):
            return False
        self.log.debug("Trying sha2 deploy of %s/%s with sha2: %s" % (image, tag, layer))
        headers = {
            'X-Checksum-Deploy': 'true',
            'X-Checksum-Sha256': layer,
        }
        path_fragment = "%s/%s/sha256__%s;sha256=%s" % (image, tag, layer, layer)
        resp, stat = self.do_unprocessed_request(method='PUT', path=self.__assemble_path(path_fragment),
                                                 headers=headers)
        if stat == 201:
            return True
        return False

    '''
        Uploads the specified layer (whose contents are in the file) to the specified image
        @param image - The image name
        @param tag - The tag name
        @param layer - The layer sha256 sum
        @param file - The file path of the layer
        @return True is successful, else False
    '''
    def upload_layer(self, image, tag, layer, file):
        self.log.debug("Uploading layer %s for %s/%s using file at %s" % (layer, image, tag, file))
        #path_fragment = "/%s/%s/_uploads/sha256__%s;sha256=%s" % (self.repo, image, layer, layer)
        path_fragment = "/%s/%s/%s/sha256__%s;sha256=%s" % (self.repo, image, tag, layer, layer)
        stat = self.deployFileByStream(path=path_fragment, file_path=file)
        return stat == 201

    '''
        Uploads an image's manifest
        @param image - The image name
        @param tag - The tag name
        @param type - The manifest type
        @param file - The file path of the manifest's contents
        @return True is successful, else False
    '''
    def upload_manifest(self, image, tag, type, file):
        self.log.debug("Uploading manifest for %s/%s of type %s using file at %s" % (image, tag, type, file))
        headers = {
            'Content-Type': type
        }
        stat = self.deployFileByStream(path=self.__assemble_manifest_path(image, tag), file_path=file, headers=headers)
        return stat == 201

    '''
        True if the docker repo exists and is v2 in the specified Artifactory instance
        False else
    '''
    def is_valid_docker_repo(self):
        self.log.info("Checking the Artifatory Docker repo '%s'" % self.repo)
        msg = self.get_call_wrapper("/api/repositories/%s" % self.repo)
        if msg and 'packageType' in msg and msg['packageType'] == 'docker':
            if 'dockerApiVersion' in msg and msg['dockerApiVersion'] == "V2":
                return True
        # JCR does not support the api/repositories call, so try a different way to verify
        msg = self.get_call_wrapper("/api/docker/%s/v2/_catalog" % self.repo)
        if msg and 'repositories' in msg:
            return True
        return False

    '''
        Returns True if and only if the specific image/tag exists
        @param image - The image name
        @param tag - The tag name
    '''
    def image_exists(self, image, tag):
        return self.head_call_wrapper(self.__assemble_manifest_path(image, tag))



    '''
        Assembles a path based on the optional context, repo and fragment
        @param fragment - The fragment (which should NOT start with a '/')
    '''
    def __assemble_path(self, fragment):
        path = "/%s/%s" % (self.repo, fragment)
        return path
    '''
        Assembles a path to deploy a manifest to
    '''
    def __assemble_manifest_path(self, image, tag):
        path = "/api/docker/%s/v2/%s/manifests/%s" % (self.repo, image, tag)
        return path

    '''
        Create a deep copy of this object
    '''
    def __deepcopy__(self, memo):
        return ArtifactoryDockerAccess(self.url, self.repo, self.username, self.password, self.ignore_cert, self.exlog)

