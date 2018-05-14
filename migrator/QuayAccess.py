from HTTPAccess import HTTPAccess
import logging
'''
    Simple API for accessing various Quay resources
    * Limited

    Supports:

    1. Getting a list of repositories for a given namespace
    2. Getting a list of all tags for a given namespace
'''
class QuayAccess:
    def __init__(self, namespace, token):
        self.log = logging.getLogger(__name__)
        self.namespace = namespace
        self.token = token
        self.headers = {'Authorization': 'Bearer %s' % self.token}
        self.access = HTTPAccess(url='https://quay.io')

    '''
        Gets the catalog of repositories using Quay specific API
        @return None if there w as an error, else the a list of available repositories
    '''
    def get_catalog(self):
        repos = None
        path = "api/v1/repository?public=true&namespace=%s" % self.namespace
        resp, stat = self.access.do_unprocessed_request(method='GET', path=path, headers=self.headers)
        if stat == 200:
            processed_response = self.access.process_response(resp)
            if 'repositories' in processed_response:
                repos = ["%s/%s" % (entry['namespace'], entry['name']) for entry in processed_response['repositories']]
        else:
            self.log.error("Error getting catalog from Quay, received code %d." % self.stat)
        return repos

    def get_tags(self, image):
        pass
