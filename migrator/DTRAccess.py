from DockerEEHTTPAccess import DockerEEHTTPAccess
import logging
import urllib
'''
    Simple API for accessing DTR resources

    Supports:


'''
class DTRAccess(DockerEEHTTPAccess):
    def __init__(self, url, username=None, password=None, ignore_cert=False, exlog=False):
        super(DTRAccess, self).__init__(url, username, password, ignore_cert, exlog)
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
        team_encoded = urllib.quote(team)
        return super(DTRAccess, self).get_with_pagination('api/v0/accounts/' + organization + '/teams/' + team_encoded + '/repositoryAccess',
            'repositoryAccessList', 'repository.id', self.__get_team_permissions_page_handler,
            pageSizeQueryParam='pageSize', pageStartQueryParam='pageStart')

    def __get_team_permissions_page_handler(self, result, page_results):
        for permission in page_results:
            access = {}
            access['accessLevel'] = permission['accessLevel']
            access['repository'] = permission['repository']['namespace'] + '/' + permission['repository']['name']
            result.append(access)
