import argparse
import logging
import sys
from migrator.ArtifactoryDockerAccess import ArtifactoryDockerAccess
from migrator.ArtifactoryUserAccess import ArtifactoryUserAccess
from migrator.UCPAccess import UCPAccess
from migrator.DTRAccess import DTRAccess
from migrator.DockerEESecurityMigrator import DockerEESecurityMigrator
from migrator.QuayEEAccess import QuayEEAccess
from migrator.QuayEESecurityMigrator import QuayEESecurityMigrator

'''
    Entry point and argument parser for security data migration to Artifactory

    Supports:

     dockeree - Migrate from a Docker EE.
'''

def add_extra_args(parser):
    parser.add_argument('--ignore-certs', dest='ignore_cert', action='store_const', const=True, default=False,
                                help='Ignore any certificate errors from both source and destination')
    parser.add_argument('--overwrite', action='store_true',
                                help='Overwrite existing users, groups or permissions on the destination')
    parser.add_argument('-v', '--verbose', action='store_true', help='Make the operation more talkative')
    parser.add_argument('initial-password', help='The password to be assigned to migrated users in Artifactory')

def add_art_access(parser):
    art_group = parser.add_argument_group('artifactory')
    art_group.add_argument('artifactory', help='The destination Artifactory URL')
    art_group.add_argument('username', help='The username to use for authentication to Artifactory')
    art_group.add_argument('password', help='The password to use for authentication to Artifactory')
    art_group.add_argument('repo', help='The docker repository')

# Sets up the argument parser for the application
def get_arg_parser():
    parser = argparse.ArgumentParser(prog='python SecurityMigrator.py',
        description='Docker registry security data to Artifactory migrator.')
    # Docker EE Parser
    subparsers = parser.add_subparsers(help='sub-command help')
    parser_dockeree = subparsers.add_parser('dockeree',
        help='Request security migration from Docker EE tools',
        description='Docker EE security data to Artifactory migrator. Migrates users, teams and permissions from Docker EE UCP and DTR to Artifactory.')
    # Docker EE tools access
    dockeree_group = parser_dockeree.add_argument_group('dockeree')
    dockeree_group.add_argument('ucp', help='The Docker Universal Control Plane (UCP) URL')
    dockeree_group.add_argument('dtr', help='The Docker Trusted Registry (DTR) URL')
    dockeree_group.add_argument('dockeree-username', help='The username to use for authentication to the Docker EE tools')
    dockeree_group.add_argument('dockeree-password', help='The password to use for authentication to the Docker EE tools')
    # Artifactory access
    add_art_access(parser_dockeree)
    # Extra options
    add_extra_args(parser_dockeree)
    parser_dockeree.add_argument('email-suffix', help='The email suffix to be assigned to migrated users in Artifactory',
                    default="mail.com")
    parser_dockeree.set_defaults(func=dockeree_migration)

    # Quay EE Parser
    parser_quayee = subparsers.add_parser('quayee',
                                        help='Request security migration from Quay EE tools',
                                        description='Quay EE security data to Artifactory migrator. Migrates users, teams and permissions from Quay EE to Artifactory.')
    quay_ee_source = parser_quayee.add_argument_group('source')
    quay_ee_source.add_argument('source', help='The source registry URL')
    quay_ee_source.add_argument('token', help='The OAuth2 Access Token of the super user')
    # Artifactory access
    add_art_access(parser_quayee)
    # Extra options
    add_extra_args(parser_quayee)
    parser_quayee.set_defaults(func=quayee_migration)

    return parser

'''
    DockerEE Security Data migration
    @param args - The user provided arguments
'''
def dockeree_migration(args):
    # Set up and verify the connection to the source components
    ucp = UCPAccess(args['ucp'], args['dockeree-username'], args['dockeree-password'], args['ignore_cert'])
    if not ucp.test_connection():
        sys.exit("Cannot connect to UCP. Check the provided URL and credentials.")

    dtr = DTRAccess(args['dtr'], args['dockeree-username'], args['dockeree-password'], args['ignore_cert'])
    if not dtr.test_connection():
        sys.exit("Cannot connect to DTR. Check the provided URL and credentials.")

    # Set up and verify the connection to Artifactory
    setup_art_access(args['artifactory'], args['username'],
        args['password'], args['repo'], args['ignore_cert'])
    art_user_access = ArtifactoryUserAccess(args['artifactory'], args['username'],
        args['password'])

    # Perform the migration
    migrator = DockerEESecurityMigrator(ucp, dtr, art_user_access, args['repo'],
        args['overwrite'], args['initial-password'], args['email-suffix'])
    migrator.migrate()

'''
    QuayEE Security Data migration
    @param args - The user provided arguments
'''
def quayee_migration(args):
    # Set up and verify the connection to the source
    quayee_access = QuayEEAccess(args['source'], args['token'], ignore_cert=args['ignore_cert'])

    if not quayee_access.is_quay_ee():
        sys.exit("Provided URL does not seem to be a valid Quay Enterprise server.")
    bots = quayee_access.get_robots_in_org("org1")

    permission = quayee_access.get_team_permissions_for_org("org1", "mendoza")

    # Set up and verify the connection to Artifactory
    setup_art_access(args['artifactory'], args['username'],
                                  args['password'], args['repo'], args['ignore_cert'])
    art_user_access = ArtifactoryUserAccess(args['artifactory'], args['username'],
                                            args['password'])

    # Perform the migration
    migrator = QuayEESecurityMigrator(quayee_access, art_user_access, args['repo'],
                                        args['overwrite'], args['initial-password'])
    migrator.migrate()




'''
    Set up and verify the connection to Artifactory
    @param artifactory_url - The URL to the Artifactory instance
    @param username - The username to access Artifactory
    @param password - The password (API Key, encrypted password, token) to access Artifactory
    @param repo - The repo name
    @param ignore_cert - True if the certificate to this instance should be ignored
'''
def setup_art_access(artifactory_url, username, password, repo, ignore_cert):
    art_access = ArtifactoryDockerAccess(url=artifactory_url, username=username,
                                   password=password, repo=repo, ignore_cert=ignore_cert)
    if not art_access.is_valid():
        sys.exit("The provided Artifactory URL or credentials do not appear valid.")
    if not art_access.is_valid_version():
        sys.exit("The provided Artifactory instance is version %s but only 4.4.3+ is supported." %
                 art_access.get_version())
    if not art_access.is_valid_docker_repo():
        sys.exit("The repo %s does not appear to be a valid V2 Docker repository." % args.repo)

    return art_access

def setup_logging(level):
    fmt = "%(asctime)s [%(threadName)s] [%(levelname)s]"
    fmt += " (%(name)s:%(lineno)d) - %(message)s"
    formatter = logging.Formatter(fmt)
    stdouth = logging.StreamHandler(sys.stdout)
    stdouth.setFormatter(formatter)

    logger = logging.getLogger()
    logger.setLevel(level)
    logger.handlers = []
    logger.addHandler(stdouth)

if __name__ == '__main__':
    # Argument parsing
    logging.info("Parsing and verifying user provided arguments.")
    parser = get_arg_parser()
    args = parser.parse_args()

    # Set log level
    if args.verbose:
        setup_logging(logging.INFO)
    else:
        setup_logging(logging.WARN)

    # Calls the appropriate function based on user's selected operation
    args.func(vars(args))
