from DockerEEHTTPAccess import DockerEEHTTPAccess
import urllib
import logging
'''
    Simple API for accessing UCP resources

    Supports:


'''
class UCPAccess(DockerEEHTTPAccess):
    def __init__(self, url, username=None, password=None, ignore_cert=False, exlog=True):
        super(UCPAccess, self).__init__(url, username, password, ignore_cert, exlog)
        self.log = logging.getLogger(__name__)

    '''
        Test connection with UCP
    '''
    def test_connection(self):
        return bool(super(UCPAccess, self).get_call_wrapper('/id/'))

    '''
        Gets the list of all organizations
        @return None if there was an error, else the a list of available organizations
    '''
    def get_organizations(self):
        return super(UCPAccess, self).get_with_pagination('accounts/', 'accounts', 'name', self.__get_organizations_page_handler)

    def __get_organizations_page_handler(self, result, page_results):
        for account in page_results:
            if account['isOrg'] == True:
                result.append(account['name'])

    '''
        Gets the list of all users
        @return None if there was an error, else the a list of available team of a given organization
    '''
    def get_users(self):
        return super(UCPAccess, self).get_with_pagination('accounts/', 'accounts', 'name', self.__get_users_page_handler)

    def __get_users_page_handler(self, result, page_results):
        for account in page_results:
            if account['isOrg'] == False and account['isActive'] == True:
                result.append(account['name'])

    '''
        Get the list of all teams of a given organizations
        @return None if there was an error, else the a list of available team of a given organization
    '''
    def get_teams(self, organization):
        org_encoded = urllib.quote_plus(organization)
        return super(UCPAccess, self).get_with_pagination("accounts/" + org_encoded + "/teams/", 'teams', 'name', self.__get_teams_page_handler)

    def __get_teams_page_handler(self, result, page_results):
        for team in page_results:
            result.append(team['name'])

    '''
        Get the list of members of a given team
        @return None if there was an error, else the a list of available members of a given team
    '''
    def get_members(self, organization, team):
        org_encoded = urllib.quote_plus(organization)
        team_encoded = urllib.quote_plus(team)
        return super(UCPAccess, self).get_with_pagination("accounts/" + org_encoded + "/teams/" + team + "/members/", 'members', 'member.id', self.__get_members_page_handler)

    def __get_members_page_handler(self, result, page_results):
        for member in page_results:
            result.append(member['member']['name'])
