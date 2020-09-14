from DockerEEHTTPAccess import DockerEEHTTPAccess
from DockerRegistryAccess import DockerRegistryAccess
import logging
'''
    Simple API for accessing DTR resources

    Supports:


'''
class DTRAccess(DockerEEHTTPAccess, DockerRegistryAccess):
    def __init__(self, url, username=None, password=None, ignore_cert=False, exlog=False):
        DockerEEHTTPAccess.__init__(self, url, username, password, ignore_cert, exlog)
        DockerRegistryAccess.__init__(self, url, username, password, method='token', ignore_cert=ignore_cert)
        self.log = logging.getLogger(__name__)

    '''
        Test connection with DTR
    '''
    def test_connection(self):
        return bool(super(DTRAccess, self).get_call_wrapper(
            '/api/v0/accounts/' + super(DTRAccess, self).get_username() + '/settings'))

    '''
        Gets the list of team permissions
        @return None if there was an error, else the a list of permissions of a team
    '''
    def get_team_permissions(self, organization, team):
        return super(DTRAccess, self).get_with_pagination('api/v0/accounts/' + organization + '/teams/' + team + '/repositoryAccess',
            'repositoryAccessList', 'repository.id', self.__get_team_permissions_page_handler,
            pageSizeQueryParam='pageSize', pageStartQueryParam='pageStart')

    '''
        Return a full list of all the repositories from DTR
    '''
    def get_repositories(self):
        return super(DTRAccess, self).get_with_header_pagination('api/v0/repositories', 'repositories',
                                                          self.__get_repositories_page_handler)

    '''
        Return a full list of all tags for a particular image in DTR
    '''
    def get_image_tags(self, image):
        return super(DTRAccess, self).get_with_header_pagination('api/v0/repositories/%s/tags' % image, None,
                                                          self.__get_tags_page_handler)

    def __get_team_permissions_page_handler(self, result, page_results):
        for permission in page_results:
            access = {}
            access['accessLevel'] = permission['accessLevel']
            access['repository'] = permission['repository']['namespace'] + '/' + permission['repository']['name']
            result.append(access)

    def __get_repositories_page_handler(self, result, page_results):
        for repository in page_results:
            # Enrich the info to allow paging
            full_name = "%s/%s" % (repository['namespace'], repository['name'])
            repository['full_name'] = full_name
            result.append(full_name)

    def __get_tags_page_handler(self, result, page_results):
        for tag in page_results:
            result.append(tag['name'])

    def get_catalog(self):
        return self.get_repositories()

    def get_tags(self, image):
        return self.get_image_tags(image)




