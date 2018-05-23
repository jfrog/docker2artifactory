import json
from HTTPAccess import HTTPAccess
from DockerTokenAccess import DockerTokenAccess
import re
import hashlib
import logging
import json


'''
    Provides basic access to a Docker registry
    Features include:
      * The ability to get a token
      * The ability to get an image
      
    @param url - The URL of the registry
    @param username - The username for token/basic auth
    @param password - The password for token/basic auth
    @param method - The access method [token, basic] (Defaults to token)
'''
class DockerRegistryAccess:
    def __init__(self, url, username=None, password=None, method=None, ignore_cert=False):
        self.url = url.rstrip('/')
        self.username = username
        self.password = password
        self.ignore_cert = ignore_cert
        self.CHUNK = 16 * 1024
        self.log = logging.getLogger(__name__)
        self.link_reg_ex = re.compile('<(.*)>;.*rel="next"')
        self.anon_access = HTTPAccess(url=self.url, ignore_cert=self.ignore_cert)
        self.valid_methods = ['token', 'basic']
        if not method:
            self.method = 'token'
        else:
            if method not in self.valid_methods:
                raise ValueError("Invalid method '%s' for DockerRegistryAccess" % method)
            self.method = method

        if self.method == 'token':
            self.token_access = DockerTokenAccess(url=self.url, username=self.username, password=self.password,
                                                  ignore_cert=self.ignore_cert)
            self.access = self.token_access
        elif self.method == 'basic':
            self.basic_access = HTTPAccess(url=self.url, username=username, password=password,
                                           ignore_cert=self.ignore_cert)
            self.access = self.basic_access

    '''
        Verifies that the repository is a valid V2 repository
    '''
    def verify_is_v2(self):
        self.log.info("Verify Registry is V2")
        try:
            # Perform request without credentials
            response, status = self.anon_access.do_unprocessed_request('GET', '/v2/')
            return response and response.headers['Docker-Distribution-API-Version']
        except Exception as ex:
            self.log.info(ex.message)
            return False

    '''
        Returns a full listing of all the catalog. 
        If the upstream repository uses pagination, aggregates the results
        @param path - (optional) The endpoint for the catalog (used for paging)
    '''
    def get_catalog(self, path='/v2/_catalog'):
        if self.method == 'token':
            # Some registries allow access to the catalog anonymously but if the user provided credentials, we need to try
            # it with the credentials or we may be missing certain images only that user can use.
            if self.username and self.password and not self.token_access.has_token():
                self.token_access.populate_generic_token()
        out = self.access.get_code_and_msg_wrapper(path)
        if not out:
            return False
        output, response = out
        code = response.getcode()
        if code != 200:
            self.log.error("Unable to get a listing of the upstream images. Catalog call returned: %d." % code)
            return False
        # Workaround for ECR returning wrong content-type
        if isinstance(output, basestring):
            output = json.loads(output)
        # END Workaround
        if response and 'link' in response.headers:
            link_value = response.headers['link']
            results = self.link_reg_ex.findall(link_value)
            if results and len(results) == 1:
                return output['repositories'] + self.get_catalog(self.access.get_relative_url(results[0]))
        return output['repositories']

    '''
        Returns a full listing of all the tags for a particular image. 
        If the upstream repository uses pagination, aggregates the results
        @param image - The image to get the tags for
        @param path - (optional) The endpoint for the tags (used for paging)
    '''
    def get_tags(self, image, path=None):
        if not path:
            out = self.access.get_code_and_msg_wrapper("/v2/" + image + "/tags/list")
        else:
            out = self.access.get_code_and_msg_wrapper(path)
        if not out:
            return False
        output, response = out
        code = response.getcode()
        if code != 200:
            self.log.error("Unable to get a listing of the tags for image '%s'. Tags call returned: %d."
                           % (image, code))
            return False
        # Workaround for ECR returning wrong content-type
        if isinstance(output, basestring):
            output = json.loads(output)
        # END Workaround
        if response and 'link' in response.headers:
            link_value = response.headers['link']
            results = self.link_reg_ex.findall(link_value)
            if results and len(results) == 1:
                return output['tags'] + self.get_tags(image, self.access.get_relative_url(results[0]))
        return output['tags']

    '''
        Downloads a manifest for the specified image/tag or image/digest
        @param image - The image name
        @param reference - The reference, which can be either a tag name or a digest
        @param file - The file to store the contents into
    '''
    def download_manifest(self, image, reference, file):
        # For now only accept v2.2 and not fat manifest
        headers = {
            'Accept': 'application/vnd.docker.distribution.manifest.v2+json, '
                      'application/vnd.docker.distribution.manifest.v1+json, application/json'
        }
        response = self.access.get_raw_call_wrapper(url="/v2/" + image + "/manifests/" + reference, headers=headers)
        if response.getcode() == 200:
            try:
                with open(file, 'wb') as f:
                    contents = response.read()
                    f.write(contents)
                return True
            except Exception as ex:
                self.log.error("Failed to download manifest for image " + image)
                return False
        return False

    '''
        Downloads the specified layer from the specified image and stores it in the specified path
        @param image - The image name
        @param layer - The layer (in the format 'sha256:03....')
        @param file - The file to store the contents into
    '''
    def download_layer(self, image, layer, file):
        response = self.access.get_raw_call_wrapper(url="/v2/" + image + "/blobs/" + layer)
        # Write the contents into a file and verify the sha256 while we are at it
        if response.getcode() == 200:
            try:
                hash_256 = hashlib.sha256()
                hash_1 = hashlib.sha1()
                with open(file, 'wb') as f:
                    while True:
                        chunk = response.read(self.CHUNK)
                        if not chunk:
                            break
                        hash_256.update(chunk)
                        hash_1.update(chunk)
                        f.write(chunk)
                expected_sha = layer.replace('sha256:', '')
                found_sha = hash_256.hexdigest()
                if found_sha == expected_sha:
                    return hash_1.hexdigest()
                else:
                    self.log.error("Layer did not match expected sha. Expected " + expected_sha + " but got " +
                                   found_sha)
            except Exception as ex:
                self.log.error(ex.message)
        self.log.error("Failed to download layer %s for image %s" % (layer, image))
        return False

    # Extracts the layers of the manifest file as well as the type
    # Returns (type, layers)
    def interpret_manifest(self, manif):
        type = None
        layers = []
        try:
            with open(manif, 'r') as m: js = json.load(m)
            # V2-1 (https://docs.docker.com/registry/spec/manifest-v2-1)
            if js['schemaVersion'] == 1:
                # According to official spec: '"application/json" will also be accepted for schema1'
                type = "application/json"
                for layer in js['fsLayers']:
                    layers.append(layer['blobSum'])
            else:  # V2-2 (https://docs.docker.com/registry/spec/manifest-v2-2)
                if 'mediaType' in js:
                    type = js['mediaType']
                else:
                    type = 'application/vnd.docker.distribution.manifest.v2+json'
                layers.append(js['config']['digest'])
                for layer in js['layers']:
                    # Don't try to grab foreign layers
                    if 'mediaType' not in layer \
                            or layer['mediaType'] != 'application/vnd.docker.image.rootfs.foreign.diff.tar.gzip':
                        layers.append(layer['digest'])
        except:
            self.log.exception("Error reading Docker manifest %s:", manif)
        return type, layers


    '''
        Create a deep copy of this object
    '''
    def __deepcopy__(self, memo):
        return DockerRegistryAccess(url=self.url, username=self.username, password=self.password, method=self.method,
                                    ignore_cert=self.ignore_cert)

