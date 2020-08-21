import logging
import copy
from threading import Thread
from Queue import Queue

class DockerEESecurityMigrator(object):
    def __init__(self, ucp_access, dtr_access, art_access, repository, overwrite=False,
        default_password="password", default_email_suffix="email.com"):
        self.log = logging.getLogger(__name__)
        self.ucp_access = ucp_access
        self.dtr_access = dtr_access
        self.art_access = art_access
        self.repository = repository
        self.overwrite = overwrite
        self.default_password = default_password
        self.default_email_suffix = default_email_suffix

        # List of protected usernames ignored by migrator
        self.ignored_users = ['anonymous', '_internal', 'admin', 'access-admin', 'xray']

        self.users = []
        self.organizations = []
        self.groups = []
        self.users_groups = {}
        self.repository_permissions = {}
        self.permission_name_prefix='dtr-'

    '''
        Migrate security data from UCP and DTR to Artifactory
    '''
    def migrate(self):
        self.__clear_counters()
        self.__fetch_source_data()
        self.__create_groups()
        self.__create_users()
        self.__create_permissions()
        print "Security migration finished"
        print "Total of migrated entities: " + str(self.counters)

    def __clear_counters(self):
        self.counters = {
            'users': 0,
            'teams': 0,
            'permissions': 0
        }

    def __increment_counter(self, entity):
        self.counters[entity] = self.counters[entity] + 1

    '''
        Fetch security data from source
    '''
    def __fetch_source_data(self):
        print "Fetching data from sources..."
        self.log.info("Fetching users data...")
        art_users = self.art_access.get_users()
        self.users = self.ucp_access.get_users(art_users)
        self.log.info("Fetching organizations...")
        self.organizations = self.ucp_access.get_organizations()
        for organization in self.organizations:
            self.log.info("Fetching " + organization + " teams...")
            teams = self.ucp_access.get_teams(organization)
            for team in teams:
                group = organization + '-' + team.replace(' ', '-')
                self.log.info("Fetching " + group + " members...")
                members = self.ucp_access.get_members(organization, team)
                self.log.info("Fetching " + group + " permissions...")
                permissions = self.dtr_access.get_team_permissions(organization, team)
                if (members and permissions):
                    self.groups.append(group)
                    for member in members:
                        # If a member is part of a team, we want that user to be created in Artifactory
                        if not member in self.users:
                            self.log.info("Found user '%s' in team but not in Artifactory.")
                            self.users.append(member)
                        if not member in self.users_groups:
                            self.users_groups[member] = []
                        self.users_groups[member].append(group)
                    for permission in permissions:
                        if not permission['repository'] in self.repository_permissions:
                            self.repository_permissions[permission['repository']] = {
                                'admin': [], 'read-only': [], 'read-write': []
                            }
                        self.repository_permissions[permission['repository']][permission['accessLevel']].append(group)

    '''
        Create Groups
    '''
    def __create_groups(self):
        print "Migrating teams..."
        for group in self.groups:
            group_exists = self.art_access.group_exists(group)
            if not self.overwrite and group_exists:
                self.log.info("Group %s exists. Skipping...", group)
            else:
                self.log.info("Creating group %s", group)
                group_created = self.art_access.create_group(group, group)
                if not group_created:
                    raise Exception("Failed to create group.")
                self.__increment_counter('teams')

    '''
        Create Users
    '''
    def __create_users(self):
        print "Migrating users..."
        for user in self.users:
            if user not in self.ignored_users:
                user_exists = self.art_access.user_exists(user)
                if user_exists:
                    self.log.info("User %s exists. Skipping user creation...", user)
                    if user in self.users_groups:
                        for group in self.users_groups[user]:
                            self.art_access.add_user_to_group(user, group)
                else:
                    self.log.info("Creating user %s", user)
                    groups = None
                    if user in self.users_groups:
                        groups = self.users_groups[user]
                    user_created = self.art_access.create_user(user, user + '@' + self.default_email_suffix,
                        self.default_password, groups, admin=False, disablePassword=True)
                    if user_created:
                        self.__increment_counter('users')
                    else:
                        #raise Exception("Failed to create user.")
                        self.log.error("Unable to user %s" % user)


                permission_name=self.permission_name_prefix + user
                permission_exists = self.art_access.permission_exists(permission_name)
                if not self.overwrite and permission_exists:
                    self.log.info("Permission %s exists. Skipping...", permission_name)
                else:
                    self.log.info("Creating permission %s", permission_name)
                    permission_created = self.art_access.create_permission(permission_name,
                        [self.repository], users={user: ["d","w","n","r","m"]},
                        include_pattern=user + '/**')
                    if permission_created:
                        self.__increment_counter('permissions')
                    else:
                        #raise Exception("Failed to create permission.")
                        self.log.error("Unable to create permissions for user %s" % user)

    '''
        Create Permissions
    '''
    def __create_permissions(self):
        print "Migrating permissions..."
        for permission in self.repository_permissions:
            permission_pattern=permission
            permission_name=self.permission_name_prefix + permission.replace('/', '-')
            permission_exists = self.art_access.permission_exists(permission_name)
            if not self.overwrite and permission_exists:
                self.log.info("Permission %s exists. Skipping...", permission_name)
            else:
                self.log.info("Creating permission %s", permission_name)
                groups = {}
                for scope in self.repository_permissions[permission]:
                    art_permissions = ['r']
                    if scope == 'read-write':
                        art_permissions.extend(['w', 'n'])
                    if scope == 'admin':
                        art_permissions.extend(["d","w","n","m"])
                    for group in self.repository_permissions[permission][scope]:
                        groups[group] = art_permissions

                self.log.info("Groups: %s", groups)
                permission_created = self.art_access.create_permission(permission_name,
                    [self.repository], groups=groups,
                    include_pattern=permission_pattern + '/**')
                if not permission_created:
                    raise Exception("Failed to create permission.")
                self.__increment_counter('permissions')
