from HTTPAccess import HTTPAccess
import logging
from distutils.version import LooseVersion

'''
    Simple basic operations for Artifactory
    * Uses basic AUTH (not tokens)
    * Limited 
'''
class ArtifactoryBaseAccess(HTTPAccess):
    def __init__(self, url, username=None, password=None, ignore_cert=False, exlog=False):
        super(ArtifactoryBaseAccess, self).__init__(url, username, password, ignore_cert, exlog)
        self.log = logging.getLogger(__name__)
        self.version = self.__get_version()

    '''
        True if the upstream appears to be an Artifactory instance that is accessible and responding
    '''
    def is_valid(self):
        return bool(self.version)

    '''
        True if the Artifactory instance is a version that supports Docker V2-2 schema
    '''
    def is_valid_version(self):
        return LooseVersion(self.version) >= LooseVersion("4.4.3")

    '''
        Get the version of the connected Artifactory
    '''
    def get_version(self):
        return self.version

    '''
        Let Artifactory know this tool is being used
    '''
    def report_usage(self, registry):
        self.log.info("Usage call")
        body = {
            "productId": "Docker2Artifactory/1.0.0",
            "features": [
                {
                    "featureId": "Registry/%s" % registry
                }
            ]
        }
        #  This is not a vital operation, app should ignore any failures here
        try:
            response = self.dorequest('POST', '/api/system/usage', body)
        except Exception as ex:
            self.log.info("Exception caught when executing usage command: %s", ex)


    '''
        Get the artifactory version
    '''
    def __get_version(self):
        self.log.info("Checking the Artifatory version")
        msg = self.get_call_wrapper("/api/system/version")
        if msg and 'version' in msg:
            self.log.info("Found version: " + msg['version'])
            return msg['version']
        self.log.error("The server does not appear to be an Artifactory instance or is not replying as expected.")
        return None
