from HTTPAccess import HTTPAccess
import logging
import urllib
'''
    Simple API for accessing various Quay EE resources
    * Limited

    Supports:

    
'''
class QuayEEAccess:
    def __init__(self, url, token, ignore_cert=False, exlog=False):
        self.log = logging.getLogger(__name__)
        self.url = url
        self.token = token
        self.headers = {'Authorization': 'Bearer %s' % self.token}
        self.access = HTTPAccess(url=url, ignore_cert=ignore_cert, exlog=exlog)

    '''
        Returns true if and only if the HEAD api/v1/discovery returns a 200
    '''
    def is_quay_ee(self):
        path = "api/v1/superuser/users/"
        try:
            resp, stat = self.access.do_unprocessed_request(method='GET', path=path, headers=self.headers)
            return stat == 200
        except:
            return False

    '''
        Returns a list of all the repositories this user has access to
    '''
    def get_repositories(self, page=1):
        path = "/api/v1/find/repositories?page=%d" % page
        results = []
        resp = self.access.dorequest(method='GET', path=path, headers=self.headers)
        if resp and 'results' in resp:
            results.extend(resp['results'])
            if resp['has_additional']:
                results.extend(self.get_repositories(page + 1))
        return results

    '''
        Returns a list of all the users
        @param disabled - If set to true, returns disabled users as well(Default to False)
    '''
    def get_users(self, disabled=False):
        path = "api/v1/superuser/users/?disabled=%s" % disabled
        resp = self.access.dorequest(method='GET', path=path, headers=self.headers)
        if resp and 'users' in resp:
            return resp['users']
        return []


    '''
        Returns a list of organizations the current user has admin access to
    '''
    def get_organizations(self):
        path = "api/v1/user/"
        resp = self.access.dorequest(method='GET', path=path, headers=self.headers)
        if resp and 'organizations' in resp:
            return resp['organizations']
        return []

    '''
        Returns a list of teams for the given organization
        @param organization - The name of the organization
    '''
    def get_teams_in_org(self, organization):
        path = "api/v1/organization/%s" % urllib.quote_plus(organization)
        resp = self.access.dorequest(method='GET', path=path, headers=self.headers)
        if resp and 'teams' in resp:
            return resp['teams']
        return []

    '''
        Returns a list of users in a given organization/team
        @param organization - The name of the organization
        @param team - The name of the team
    '''
    def get_users_in_team(self, organization, team):
        path = "/api/v1/organization/%s/team/%s/members" % (urllib.quote_plus(organization), urllib.quote_plus(team))
        resp = self.access.dorequest(method='GET', path=path, headers=self.headers)
        if resp and 'members' in resp:
            return resp['members']
        return []

    '''
        Returns a list of robots in a given organization
        @param organization - The name of the organization
    '''
    def get_robots_in_org(self, organization):
        path = "/api/v1/organization/%s/robots" % urllib.quote_plus(organization)
        resp = self.access.dorequest(method='GET', path=path, headers=self.headers)
        if resp and 'robots' in resp:
            return resp['robots']
        return {}

    '''
        Returns a list of collaborators (users without a team) in a given organization
        @param organization - The name of the organization
    '''
    def get_collaborators_in_org(self, organization):
        path = "/api/v1/organization/%s/collaborators" % urllib.quote_plus(organization)
        resp = self.access.dorequest(method='GET', path=path, headers=self.headers)
        if resp and 'collaborators' in resp:
            return resp['collaborators']
        return []

    '''
        Get a list of the permissions for all users on a particular repository
        @param repository - The repository name
    '''
    def get_user_permissions_for_repo(self, repository):
        path = "/api/v1/repository/%s/permissions/user/" % urllib.quote_plus(repository)
        resp = self.access.dorequest(method='GET', path=path, headers=self.headers)
        if resp and 'permissions' in resp:
            return resp['permissions']
        return {}

    '''
        Get a list of the permissions for all teams on a particular repository
        @param repository - The repository name
    '''
    def get_team_permissions_for_repo(self, repository):
        path = "/api/v1/repository/%s/permissions/team/" % urllib.quote_plus(repository)
        resp = self.access.dorequest(method='GET', path=path, headers=self.headers)
        if resp and 'permissions' in resp:
            return resp['permissions']
        return {}

    '''
        Get a list of the permissions for a particular team for all repositories in an org
        @param organization - The organization name
        @param team - The team name
    '''
    def get_team_permissions_for_org(self, organization, team):
        path = "/api/v1/organization/%s/team/%s/permissions" % (urllib.quote_plus(organization),
                                                                urllib.quote_plus(team))
        resp = self.access.dorequest(method='GET', path=path, headers=self.headers)
        if resp and 'permissions' in resp:
            return resp['permissions']
        return {}

    '''
        Get a list of the permissions for a robot user on a particular organization
        @param organization - The organization name
        @param robot - The robot name
    '''
    def get_robot_permissions_for_organization(self, organization, robot):
        path = "/api/v1/organization/}%s/robots/%s/permissions" % (urllib.quote_plus(organization),
                                                                urllib.quote_plus(robot))
        resp = self.access.dorequest(method='GET', path=path, headers=self.headers)
        if resp and 'permissions' in resp:
            return resp['permissions']
        return {}
