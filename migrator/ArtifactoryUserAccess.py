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
        return bool(self.get_call_wrapper('/api/security/users/' + urllib.quote(username.encode('utf8'))))

    '''
        Creates or replaces a user with the specified username
        @param username - The username to create
        @param email - The email of the user
        @param groups - The groups the user should belong to (defaults to none)
        @param admin - True if this user should be an admin (defaults to false)
        @param disablePassword - Disables the internal password from use
    '''
    def create_user(self, username, email, password, groups=None, admin=False, disablePassword=False):
        body = {
            "email": email,
            "password": password,
            "admin": admin,
            "internalPasswordDisabled": disablePassword
        }
        if groups:
            body.update({"groups": groups})

        resp, stat = self.do_unprocessed_request(method='PUT', path='/api/security/users/' + urllib.quote(username.encode('utf8')), body=body)
        if stat == 201:
            return True
        self.log.warn("Failed to create user with status %s: %s", stat, resp)
        self.log.warn("Body of failed request: " + body)
        return False

    '''
        Creates or replaces a user with the specified username
        @param username - The user to add to the group
        @param group - The group to add the user to
    '''
    def add_user_to_group(self, username, group):
        user_details = self.get_call_wrapper('/api/security/users/%s' % urllib.quote(username.encode('utf8')))
        if not user_details:
            self.log.error("Unable to retrieve user %s" % username)
        if 'groups' not in user_details:
            user_details['groups'] = []

        # If already in the group, don't try to add it again
        if group in user_details['groups']:
            return

        user_details['groups'].append(group)

        resp, stat = self.do_unprocessed_request(method='POST', path='/api/security/users/' + urllib.quote(username.encode('utf8')), body=user_details)
        if stat == 201:
            return True
        self.log.warn("Failed to update user with status %s: %s", stat, resp)
        return False

    '''
        Return true if the groups exists
        @param name - The group name to check for
    '''
    def group_exists(self, name):
        return bool(self.get_call_wrapper('/api/security/groups/' + urllib.quote(name.encode('utf8'))))

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

        resp, stat = self.do_unprocessed_request(method='PUT', path='/api/security/groups/' + urllib.quote(name.encode('utf8')), body=body)
        if stat == 201:
            return True
        self.log.warn("Failed to create group with status %s: %s", stat, resp)
        return False

    '''
        Return true if the permission identified by the provided name exists
        @param name - The name of the permission
    '''
    def permission_exists(self, name):
        name_url_encoded = urllib.quote(name.encode('utf8'))
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

        name_url_encoded = urllib.quote(name.encode('utf8'))
        resp, stat = self.do_unprocessed_request(method='PUT', path='/api/security/permissions/' + name_url_encoded, body=body)
        if stat == 201:
            return True
        self.log.warn("Failed to create permission with status %s: %s", stat, resp)
        return False

    '''
        Returns the full list of all users in the Artifactory instance
    '''
    def get_users(self):
        self.log.info("Getting a list of all Artifactory users")
        users = []
        results = self.get_call_wrapper('/api/security/users')
        if results and len(results) > 0:
            users = [o['name'] for o in results]
        return users
