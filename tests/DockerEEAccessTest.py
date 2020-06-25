import unittest
import os, sys
import util.LogUtils as LogUtils
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from migrator import UCPAccess
from migrator import DTRAccess

@unittest.skip("Require work for generic use.")
class DockerEEAccessTest(unittest.TestCase):

    def setUp(self):
        LogUtils.start_logging()
        self.ucp = UCPAccess.UCPAccess('https://ucpsoldev.jfrog.team', username='admin', password='password')
        self.dtr = DTRAccess.DTRAccess('https://dtrsoldev.jfrog.team', username='admin', password='password')

    def tearDown(self):
        pass

    def test_get_organizations(self):
        organizations = self.ucp.get_organizations()
        print organizations
        self.assertItemsEqual(organizations, ['docker-datacenter', 'my-org',
            'my-org2', 'org1', 'org10', 'org2', 'org3', 'org4', 'org5', 'org6',
            'org7', 'org8', 'org9'])

    def test_get_users(self):
        users = self.ucp.get_users()
        print users
        self.assertItemsEqual(users, ['admin', 'eliom', 'user1', 'user10',
            'user11', 'user12', 'user2', 'user3', 'user4', 'user5', 'user6',
            'user7', 'user8', 'user9'])

    def test_get_teams(self):
        teams = self.ucp.get_teams('my-org')
        print teams
        self.assertItemsEqual(teams, ['admin'])

    def test_get_members(self):
        members = self.ucp.get_members('my-org2', 'admin')
        print members
        self.assertItemsEqual(members, ['user1','user2','user3','user4','user5',
            'user6','user7','user8','user9','user10','user11','user12',])

    def test_get_permissions(self):
        permissions = self.dtr.get_team_permissions('my-org', 'admin')
        print permissions
        self.assertItemsEqual( permissions,
            [
                {
                    'accessLevel': 'read-only',
                    'repository': 'my-org/my-repo2'
                },
                {
                    'accessLevel': 'read-write',
                    'repository': 'my-org/my-repo'
                },
                {
                    'accessLevel': 'admin',
                    'repository': 'my-org/alpine'
                }
            ]
        )

if __name__ == '__main__':
    unittest.main()
