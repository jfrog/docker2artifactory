import unittest
import util.LogUtils as LogUtils
import util.ArtifactoryUtil as ArtifactoryUtil
import os, sys
# Allows easily running the tests without setting up python path
sys.path.append((os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from migrator.ArtifactoryUserAccess import ArtifactoryUserAccess



'''
    Test the ability to create:
      * Users
      * Groups
      * Permissions
'''
class ArtifactoryUserManagementTest(unittest.TestCase):

    def setUp(self):
        LogUtils.start_logging()
        self.artutil = ArtifactoryUtil.ArtifactoryUtil()

        # Artifactory configuration
        self.artversion = 'latest'
        self.artport = '8081'
        self.artcontainername = 'artifactory'

        # Start Artifactory
        if not self.artutil.start_artifactory(self.artversion, self.artport, self.artcontainername):
            sys.exit('Failed to create the Artifactory instance')

        self.user_access = ArtifactoryUserAccess(url="http://localhost:%d/artifactory" % int(self.artport),
                                                 username='admin', password='password')

    def tearDown(self):
        self.artutil.delete_instance(self.artcontainername)

    def test_user(self):
        self.artaccess = self.artutil.get_artifactory_access(self.artport)

        #************* Exists *************#
        # Should exist
        self.assertTrue(self.user_access.user_exists("admin"))
        # Should not
        self.assertFalse(self.user_access.user_exists('foobar'))

        #************* Create *************#
        # Regular user
        user = {
            "username": "jose",
            "email": "jose.arcadio.buendia@gmail.com",
            "password": "password"
        }
        success = self.user_access.create_user(username=user['username'], email=user['email'], password=user['password'])
        self.assertTrue(success)
        user_result = self.artaccess.get_user("jose")
        self.assertTrue(user_result)
        self.assertEqual(user_result['email'], user['email'])
        self.assertFalse(user_result['admin'])
        # Admin user
        user = {
            "username": "ursula",
            "email": "ursula.iguaran@gmail.com",
            "password": "password",
            "admin": True,
        }
        success = self.user_access.create_user(username=user['username'], email=user['email'],
                                               password=user['password'], admin=user['admin'])
        self.assertTrue(success)
        user_result = self.artaccess.get_user("ursula")
        self.assertTrue(user_result)
        self.assertEqual(user_result['email'], user['email'])
        self.assertTrue(user_result['admin'])
        # Invalid username
        user = {
            "username": "_int*%#",
            "email": "ursula.iguaran@gmail.com",
            "password": "password"
        }
        success = self.user_access.create_user(username=user['username'], email=user['email'],
                                               password=user['password'])
        self.assertFalse(success)

    def test_group(self):
        self.artaccess = self.artutil.get_artifactory_access(self.artport)
        #************* Exists *************#
        # Should exist
        self.assertTrue(self.user_access.group_exists("readers"))
        # Should not
        self.assertFalse(self.user_access.group_exists("foobar"))

        #************* Create *************#
        # Should not
        self.assertFalse(self.artaccess.get_group("foobar"))
        group = {
            "name": "foobar",
            "description": "This is for testing",
            "auto_join": True,
        }
        self.user_access.create_group(name=group['name'], description=group['description'],
                                      auto_join=group['auto_join'])
        # Should exist now
        group_returned = self.artaccess.get_group("foobar")
        self.assertTrue(group_returned)
        self.assertEqual(group_returned['name'], group['name'])
        self.assertEqual(group_returned['description'], group['description'])
        self.assertEqual(group_returned['autoJoin'], group['auto_join'])

        # Test update
        group = {
            "name": "foobar",
            "description": "This is for testing updates",
            "auto_join": False,
        }
        self.user_access.create_group(name=group['name'], description=group['description'],
                                      auto_join=group['auto_join'])
        group_returned = self.artaccess.get_group("foobar")
        self.assertTrue(group_returned)
        self.assertEqual(group_returned['name'], group['name'])
        self.assertEqual(group_returned['description'], group['description'])
        self.assertEqual(group_returned['autoJoin'], group['auto_join'])

    def test_permission(self):
        self.artaccess = self.artutil.get_artifactory_access(self.artport)
        #************* Exists *************#
        # Should exist
        self.assertTrue(self.user_access.permission_exists("Any Remote"))
        # Should not
        self.assertFalse(self.user_access.permission_exists("foobar"))
        #************* Create *************#
        # Should not
        self.assertFalse(self.artaccess.get_permission("foobar"))
        permission = {
            "name": "foobar",
            "repositories": ["ANY REMOTE"],
            "groups": {
                "readers": ["d", "w", "n", "r", "m"]
            }
        }
        self.assertTrue(self.user_access.create_permission(name=permission['name'],
                                                           repositories=permission['repositories'],
                                                           groups=permission['groups']))
        permission_returned = self.artaccess.get_permission("foobar")
        self.assertTrue(permission_returned)
        self.assertEqual(permission_returned['name'], permission['name'])


if __name__ == '__main__':
    unittest.main()
