import logging

class QuayEESecurityMigrator(object):
    def __init__(self, quay_access, art_access, repository, overwrite=False, default_password="password"):
        self.log = logging.getLogger(__name__)
        self.quayee_access = quay_access
        self.art_access = art_access
        self.repository = repository
        self.overwrite = overwrite
        self.default_password = default_password

        # List of protected usernames ignored by migrator
        self.ignored_users = ['anonymous', '_internal', 'admin', 'access-admin', 'xray']

        self.users = []
        self.organizations = []
        self.groups = []
        self.robots = []
        self.users_groups = {}
        self.repository_permissions = {}
        self.org_permissions = {}

    '''
        Migrate security data from Quay EE to Artifactory
    '''
    def migrate(self):
        self.__clear_counters()
        self.__fetch_source_data()
        self.__create_groups()
        self.__create_robots()
        self.__create_users()
        self.__create_permissions_for_org()
        self.__create_permissions_for_team_repo()
        print "Security migration finished"
        print "Total of migrated entities: " + str(self.counters)

    def __clear_counters(self):
        self.counters = {
            'users': 0,
            'robots': 0,
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
        self.users = self.quayee_access.get_users()
        self.log.info("Fetching organizations...")
        self.organizations = self.quayee_access.get_organizations()
        # Get organization permissions
        for organization in self.organizations:
            organization_name = organization['name']
            # Robot permissions for the organization
            self.log.info("Fetching " + organization_name + " robots...")
            robots = self.quayee_access.get_robots_in_org(organization_name)
            self.robots.extend(robots)
            # Team permissions
            self.log.info("Fetching " + organization_name + " teams...")
            teams = self.quayee_access.get_teams_in_org(organization_name)
            for team_name, team in teams.iteritems():
                self.__fetch_team_permissions(organization_name, team_name, team)
        # Repository/user permissions
        self.log.info("Fetching repositories...")
        repositories = self.quayee_access.get_repositories()
        for repository in repositories:
            self.__fetch_user_permissions(repository)

    '''
        Fetch security data for users for a specific repository
        Permissions include:
            1. Repository specific permissions for users
            2. Repository specific permissions for robots
        @param repository - THe repository settings
        
    '''
    def __fetch_user_permissions(self, repository):
        namespace = repository['namespace']['name']
        is_org = repository['namespace']['kind'] == 'organization'
        repository_name = "%s/%s" % (namespace, repository['name'])
        user_permissions = self.quayee_access.get_user_permissions_for_repo(repository_name)
        if repository_name not in self.repository_permissions:
            self.repository_permissions[repository_name] = {
                "group": {
                    'admin': [], 'read': [], 'write': []
                },
                "user": {
                    'admin': [], 'read': [], 'write': []
                }
            }
        if user_permissions:
            for user_name, user_permission in user_permissions.iteritems():
                # No need to apply permissions to the owner since he is admin already (default permissions)
                # Also, don't add permissions to ignored users
                if user_name != namespace and user_name not in self.ignored_users:
                    # Only robot from organizations are imported so no need to account for user robots
                    if not user_permission['is_robot'] or is_org:
                        self.repository_permissions[repository_name]['user'][user_permission['role']].append(user_name)

    '''
        Fetch security data for specified team in the specified organization
        Permissions include:
            1. Organization wide permissions for a team
            2. Repository specific permissions for a team
        @param organization_name - The name of the organization
        @param team_name - The name of the team
        @param team - The details of the team
    '''
    def __fetch_team_permissions(self, organization_name, team_name, team):
        group = organization_name + '-' + team_name
        self.log.info("Fetching " + group + " members...")
        members = self.quayee_access.get_users_in_team(organization_name, team_name)
        # Get repository level permissions for the teams
        self.log.info("Fetching " + group + " permissions...")
        permissions = self.quayee_access.get_team_permissions_for_org(organization_name, team_name)
        # Get Organization wide permissions for a team
        self.org_permissions[group] = team['role']
        # Add to the global list of groups
        self.groups.append(group)
        if members:
            for member in members:
                member_name = member['name']
                if not member_name in self.users_groups:
                    self.users_groups[member_name] = []
                self.users_groups[member_name].append(group)
        if permissions:
            for permission in permissions:
                repo_name = "%s/%s" % (organization_name, permission['repository']['name'])
                if repo_name not in self.repository_permissions:
                    self.repository_permissions[repo_name] = {
                        "group": {
                            'admin': [], 'read': [], 'write': []
                        },
                        "user": {
                            'admin': [], 'read': [], 'write': []
                        }
                    }
            self.repository_permissions[repo_name]['group'][permission['role']].append(group)

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
        Create Robots
    '''
    def __create_robots(self):
        print "Migrating robots..."
        for robot in self.robots:
            bot_name = robot['name'].replace('+', '-')
            if bot_name not in self.ignored_users:
                bot_exists = self.art_access.user_exists(bot_name)
                if not self.overwrite and bot_exists:
                    self.log.info("Robot %s exists. Skipping...", bot_name)
                else:
                    self.log.info("Creating robot %s", bot_name)
                    groups = None
                    if bot_name in self.users_groups:
                        groups = self.users_groups[bot_name]
                    bot_created = self.art_access.create_user(bot_name, "fake@example.org", robot['token'], groups)
                    if not bot_created:
                        raise Exception("Failed to create robot.")
                    self.__increment_counter('robots')

    '''
        Create Users
    '''
    def __create_users(self):
        print "Migrating users..."
        for user in self.users:
            user_name = user['name']
            if user_name not in self.ignored_users:
                user_exists = self.art_access.user_exists(user_name)
                if not self.overwrite and user_exists:
                    self.log.info("User %s exists. Skipping...", user_name)
                else:
                    self.log.info("Creating user %s", user_name)
                    groups = None
                    if user_name in self.users_groups:
                        groups = self.users_groups[user_name]
                    user_created = self.art_access.create_user(user_name, user['email'], self.default_password, groups)
                    if not user_created:
                        raise Exception("Failed to create user.")
                    self.__increment_counter('users')

                permission_name = "quayee-%s" % user_name
                permission_exists = self.art_access.permission_exists(permission_name)
                if not self.overwrite and permission_exists:
                    self.log.info("Permission %s exists. Skipping...", permission_name)
                else:
                    self.log.info("Creating permission %s", permission_name)
                    permission_created = self.art_access.create_permission(permission_name,
                                                                           [self.repository], users={user_name: ["d","w","n","r","m"]},
                                                                           include_pattern=user_name + '/**')
                    if not permission_created:
                        raise Exception("Failed to create permission.")
                    self.__increment_counter('permissions')

    '''
        Create permissions based on team roles at the organization level
        Roles: 
        member - No organization wide permissions
        creator - Write/read access at the org level
        admin - Admin privs on entire organization 
    '''
    def __create_permissions_for_org(self):
        print "Migrating organization level permissions for teams..."
        for group, role in self.org_permissions.iteritems():
            permission_name = "%s-role" % group
            org_namespace=group.split('-', 1)[1]
            permission_exists = self.art_access.permission_exists(permission_name)
            groups = {}
            if role == 'admin':
                groups[group] = ["r","d","w","n","m"]
            elif role == 'creator':
                groups[group] = ["r","d","w","n"]
            if groups:
                if not self.overwrite and permission_exists:
                    self.log.info("Permission %s exists. Skipping...", permission_name)
                else:
                    self.log.info("Creating permission %s", permission_name)
                    permission_created = self.art_access.create_permission(permission_name,
                                                                           [self.repository], groups=groups,
                                                                           include_pattern=org_namespace + '/**')
                    if not permission_created:
                        raise Exception("Failed to create permission.")
                    self.__increment_counter('permissions')


    '''
        Create Permissions for repositories
    '''
    def __create_permissions_for_team_repo(self):
        print "Migrating repository permissions..."
        for permission in self.repository_permissions:
            # Extract the namespace
            permission_pattern=permission
            permission_name=permission.replace('/', '-')
            permission_exists = self.art_access.permission_exists(permission_name)
            if not self.overwrite and permission_exists:
                self.log.info("Permission %s exists. Skipping...", permission_name)
            else:
                self.log.info("Creating permission %s", permission_name)
                groups = {}
                users = {}
                # Group permissions
                for scope in self.repository_permissions[permission]['group']:
                    art_permissions = ['r']
                    if scope == 'write':
                        art_permissions.extend(['w', 'n', 'd'])
                    if scope == 'admin':
                        art_permissions.extend(["d","w","n","m"])
                    for group in self.repository_permissions[permission]['group'][scope]:
                        groups[group] = art_permissions
                # User permissions
                for scope in self.repository_permissions[permission]['user']:
                    art_permissions = ['r']
                    if scope == 'write':
                        art_permissions.extend(['w', 'n', 'd'])
                    if scope == 'admin':
                        art_permissions.extend(["d","w","n","m"])
                    for user in self.repository_permissions[permission]['user'][scope]:
                        users[user] = art_permissions
                self.log.info("Groups: %s", groups)
                self.log.info("Users: %s", users)
                permission_created = self.art_access.create_permission(permission_name,
                                                                       [self.repository], users=users, groups=groups,
                                                                       include_pattern=permission_pattern + '/**')
                if not permission_created:
                    raise Exception("Failed to create permission.")
                self.__increment_counter('permissions')
