import logging
from HTTPAccess import HTTPAccess

'''
 An API for accessing Artifactory (4.0+)
 The API is for testing and not for general usage. As such, functionality such as uploading/downloading is not
 implemented.
 APIs for:
  * Users
  * Permissions
  * Configurations
  * Artifacts
'''

class ArtifactoryAccess(HTTPAccess):
    def __init__(self, url, username, password, ignore_cert = False, exlog=False):
        super(ArtifactoryAccess, self).__init__( url, username, password, ignore_cert, exlog)
        self.log = logging.getLogger(__name__)

    # Get a list of all the users
    def get_users(self):
        return self.get_call_wrapper('/api/security/users')

    # Get detailed info of a specific user
    # False if no such user exists or there was an error getting it
    def get_user(self, username):
        return self.get_call_wrapper('/api/security/users/' + username)

    # Get a list of all the groups
    def get_groups(self):
        return self.get_call_wrapper('/api/security/groups')

    # Get detailed info of a specific group
    # False if no such user exists
    def get_group(self, group_name):
        return self.get_call_wrapper('/api/security/groups/' + group_name)

    # Get a list of all the permissions
    def get_permissions(self):
        return self.get_call_wrapper('/api/security/permissions')

    # Get detailed info of a specific permission
    def get_permission(self, permission_name):
        return self.get_call_wrapper('/api/security/permissions/' + permission_name)

    # Ping the Artifactory instance
    # @return True if Artifactory responds with 200, else False
    def ping(self):
        return self.get_call_wrapper('/api/system/ping') != False

    # True if the artifact exists at the specified path
    def artifact_exists(self, repo_name, artifact_path):
        return self.get_artifact_details(repo_name, artifact_path) != False

    # True if the artifact exists at the specified path
    def search_artifact(self, repo_name, artifact_name):
        return self.get_call_wrapper('/api/search/artifact?name=' + artifact_name + '&repos=' + repo_name)

    # Get detailed info of the item
    # False if no such artifact exists
    def get_artifact_details(self, repo_name, artifact_path):
        return self.get_call_wrapper('/api/storage/' + repo_name + '/' + artifact_path.lstrip('/'))

    # Get artifact properties
    def get_artifact_properties(self, repo_name, artifact_path):
        return self.get_call_wrapper('/api/storage/' + repo_name + '/' + artifact_path.lstrip('/') + '?properties')

    # Get artifact json content
    def get_artifact_json_content(self, repo_name, artifact_path):
        return self.get_call_wrapper('/' + repo_name + '/' + artifact_path)

    # Get a list of all the repositories
    def get_repositories(self):
        return self.get_call_wrapper('/api/repositories')

    # Get detailed info of the repository
    # False if no such repository exists
    def get_repository(self, repo_name):
        return self.get_call_wrapper('/api/repositories/' + repo_name)

    # Get license info
    def get_license(self):
        return self.get_call_wrapper('/api/system/license')


    # Get the full Artifactory configuration
    def get_configuration(self):
        return self.get_call_wrapper('/api/system/configuration')

    # Install a license into an Artifactory instance
    def install_license(self, license_contents):
        try:
            response = self.dorequest('POST', '/api/system/license', {'licenseKey': license_contents})
            return response
        except Exception as ex:
            return False

    # Create get_repository
    def create_local_repo(self, reponame, type, layoutref):
        body = {'key': reponame, 'rclass': 'local', 'packageType': type, 'repoLayoutRef': layoutref}
        try:
            response = self.dorequest('PUT', '/api/repositories/' + reponame, body)
            return response
        except Exception as ex:
            return False

    # Upload manifest
    def upload_file(self, path, type, file):
        headers = {
            'Content-Type': type
        }
        stat = self.deployFileByStream(path=path, file_path=file, headers=headers)
        return stat == 201
