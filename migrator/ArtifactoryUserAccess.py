from ArtifactoryBaseAccess import ArtifactoryBaseAccess
import urllib
import logging

'''
    Simple API for user, group and permission creation in Artifactory
    * Uses basic AUTH (not tokens)
    * Limited
'''
class ArtifactoryUserAccess(ArtifactoryBaseAccess):
    def __init__(self, url, username=None, password=None, ignore_cert=False, exlog=False):
        super(ArtifactoryUserAccess, self).__init__(url, username, password, ignore_cert, exlog)
        self.log = logging.getLogger(__name__)

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
        self.log.warn("Failed to create user with status %s: %s", stat, resp)
        return False

    '''
        Return true if the groups exists
        @param name - The group name to check for
    '''
    def group_exists(self, name):
        return bool(self.get_call_wrapper('/api/security/groups/' + name))

    '''
        Creates or replaces a group identified with the group name
        @param name - The group name to create
        @param description - A description of the group
        @param auto_join - If new users should automatically be added to this group (defaults to False)
    '''
    def create_group(self, name, description, auto_join=False):
        body = {
            "name": name,
            "description": description,
            "autoJoin": auto_join
        }

        resp, stat = self.do_unprocessed_request(method='PUT', path='/api/security/groups/' + name, body=body)
        if stat == 201:
            return True
        self.log.warn("Failed to create group with status %s: %s", stat, resp)
        return False

    '''
        Return true if the permission identified by the provided name exists
        @param name - The name of the permission
    '''
    def permission_exists(self, name):
        name_url_encoded = urllib.quote_plus(name)
        return bool(self.get_call_wrapper('/api/security/permissions/' + name_url_encoded))

    '''
        Creates or replaces a permission identified with the permission name
        @param name - The name of the permission
        @param repositories - The list of repository names this permission target applies to (must have at least one)
        @param users - A map with the users to to apply the permission to and the permissions to apply. Example:
          {
              "bob": ["r","w","m"],
              "alice" : ["d","w","n", "r"],
              ...
          }
          Where r = read, w = write, m=admin, d = delete, n = annotate
        @param groups - The groups to apply the permission to and the permissions to apply
          {
              "managers": ["r","w","m"],
              "deployers" : ["d","w","n", "r"],
              ...
          }
          Where r = read, w = write, m=admin, d = delete, n = annotate
        @param include_pattern - The include pattern for the permission. Defaults to allow "**" (comma separated)
        @param exclude_pattern -  The exclude pattern for the permission. Defaults to "" (comma separated)
    '''
    def create_permission(self, name, repositories, users=None, groups=None, include_pattern=None,
                          exclude_pattern=None):
        body = {
            "name": name,
            "repositories": repositories,
            "principals": {}
        }
        if users:
            body['principals'].update({"users": users})
        if groups:
            body['principals'].update({"groups": groups})
        if include_pattern:
            body.update({"includesPattern": include_pattern})
        if exclude_pattern:
            body.update({"excludesPattern": exclude_pattern})

        name_url_encoded = urllib.quote_plus(name)
        resp, stat = self.do_unprocessed_request(method='PUT', path='/api/security/permissions/' + name_url_encoded, body=body)
        if stat == 201:
            return True
        self.log.warn("Failed to create permission with status %s: %s", stat, resp)
        return False
