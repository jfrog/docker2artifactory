Docker2Artifactory
==================
This tool is designed to ease the transition from 3rd party V2 Docker registries to JFrog Artifactory.

---
# Features

## Data Migration

* Token based registries
* Anonynous access registries
* Quay (SaaS)
* Quay EE (Enterprise Edition)

## Security Migration (Users, Groups and Permissions)

* Docker EE (UCP and DTR)

## Requirements

* Artifactory 4.4.3+
* Python 2 (tested on 2.7) **or** Docker with internet access

---
# Usage

## Data Migration

1. Checkout the project: 
```bash
git clone https://github.com/JFrogDev/docker2artifactory.git
```
2. Go into the directory you just cloned
3. Run the tool:
   * Using Python: 
```bash
python DockerMigrator.py ......
```
   * Using Docker: 
```bash
docker run -it --rm --name my-running-script -v "$PWD":/usr/src/myapp -w /usr/src/myapp python:2.7.14 python DockerMigrator.py .....
```

### Generic registry migrator
The generic registry migrator works against token based registries. This includes DockerHub, Artifactory registries, and many others. The this tool has two modes of operation, auto-discovery and guided migrations. In auto-discovery mode, the tool will query the source registry (using standard Docker registry apis) to get a full listing of all the available image names and tags. It will then migrate all of the images it finds. In the guided mode, you provide a list of image names and tags you wish to migrate (see [Image file format](#image-file-format))

#### Input

```bash
usage: python DockerMigrator.py generic [-h]
                                        [--source-username SOURCE_USERNAME]
                                        [--source-password SOURCE_PASSWORD]
                                        [--ignore-certs] [--overwrite]
                                        [--num-of-workers WORKERS] [-v]
                                        [--image-file IMAGE_FILE]
                                        source artifactory username password
                                        repo

optional arguments:
  -h, --help            show this help message and exit
  --ignore-certs        Ignore any certificate errors from both source and
                        destination
  --overwrite           Overwrite existing image/tag on the destination
  --num-of-workers WORKERS
                        Number of worker threads. Defaults to 2.
  -v, --verbose         Make the operation more talkative
  --image-file IMAGE_FILE
                        Limit the import to a set of images in the provided
                        file. Format of new line separated file: '<image-
                        name>:<tag>' OR '<image-name>' to import all tags of
                        that repository.

source:
  source                The source registry URL
  --source-username SOURCE_USERNAME
                        The username to use for authentication to the source
  --source-password SOURCE_PASSWORD
                        The password to use for authentication to the source

artifactory:
  artifactory           The destination Artifactory URL
  username              The username to use for authentication to Artifactory
  password              The password to use for authentication to Artifactory
  repo                  The docker repository
```

#### Importing from DockerHub
DockerHub does not implement the catalog API. To migrate images from DockerHub, follow these guide lines:

1. Set the source registry URL as https://registry-1.docker.io
2. Provide an [image file list](#image-file-format) of the images you want to migrate
3. If the image is an 'offiial' image (like centos, busybox, hello-world), the name must be prepended with `library/`. For centos, this would look be `library/centos` or `library/centos:latest` for the latest tag.
4. If you are migrating images that are private, provide the --source-username and --source-password.

### Quay registry migrator
The Quay registry migrator works against Quay's SaaS offering. It works against both public and private registries. The this tool has two modes of operation, auto-discovery and guided migrations. In auto-discovery mode, the tool will query the source registry (using Quay specifc apis) to get a full listing of all the available image names and tags. It will then migrate all of the images it finds. In the guided mode, you provide a list of image names and tags you wish to migrate (see [Image file format](#image-file-format))

To use this tool, you **need** to [generate a token for internal application use](https://docs.quay.io/api/).

#### Input

```bash
usage: python DockerMigrator.py quay [-h] [--ignore-certs] [--overwrite]
                                     [--num-of-workers WORKERS] [-v]
                                     [--image-file IMAGE_FILE]
                                     namespace token artifactory username
                                     password repo

optional arguments:
  -h, --help            show this help message and exit
  --ignore-certs        Ignore any certificate errors from both source and
                        destination
  --overwrite           Overwrite existing image/tag on the destination
  --num-of-workers WORKERS
                        Number of worker threads. Defaults to 2.
  -v, --verbose         Make the operation more talkative
  --image-file IMAGE_FILE
                        Limit the import to a set of images in the provided
                        file. Format of new line separated file: '<image-
                        name>:<tag>' OR '<image-name>' to import all tags of
                        that repository.

quay:
  namespace             The username or organization to import repositories
                        from
  token                 The OAuth2 Access Token

artifactory:
  artifactory           The destination Artifactory URL
  username              The username to use for authentication to Artifactory
  password              The password to use for authentication to Artifactory
  repo                  The docker repository
```

### Quay Enterprise Edition registry migrator
The Quay registry migrator works against Quay's Enterprise offering. It works against both public and private registries. The this tool has two modes of operation, auto-discovery and guided migrations. In auto-discovery mode, the tool will query the source registry to get a full listing of all the available image names and tags. It will then migrate all of the images it finds. In the guided mode, you provide a list of image names and tags you wish to migrate (see [Image file format](#image-file-format))

To use this tool, you need to provide the *super user's* credentials or an oauth [token](https://docs.quay.io/api/) with all permissions.

#### LIMITATIONS

Quay does not have the concept of an all seeing user. The super user cannot see other users' repositories. **To properly import all repositories, all users/organizations should grant the super user being used READ access to their repositories.**

#### Input

```bash
usage: python DockerMigrator.py quayee [-h]
                                       [--source-username SOURCE_USERNAME]
                                       [--source-password SOURCE_PASSWORD]
                                       [--token TOKEN] [--ignore-certs]
                                       [--overwrite]
                                       [--num-of-workers WORKERS] [-v]
                                       [--image-file IMAGE_FILE]
                                       source artifactory username password
                                       repo

optional arguments:
  -h, --help            show this help message and exit
  --ignore-certs        Ignore any certificate errors from both source and
                        destination
  --overwrite           Overwrite existing image/tag on the destination
  --num-of-workers WORKERS
                        Number of worker threads. Defaults to 2.
  -v, --verbose         Make the operation more talkative
  --image-file IMAGE_FILE
                        Limit the import to a set of images in the provided
                        file. Format of new line separated file: '<image-
                        name>:<tag>' OR '<image-name>' to import all tags of
                        that repository.

source:
  source                The source registry URL
  --source-username SOURCE_USERNAME
                        The super user username
  --source-password SOURCE_PASSWORD
                        The super user password
  --token TOKEN         The OAuth2 Access Token

artifactory:
  artifactory           The destination Artifactory URL
  username              The username to use for authentication to Artifactory
  password              The password to use for authentication to Artifactory
  repo                  The docker repository

```

### Image file format
The image file format accepts two types of entries. The first is specifying an image and optionally a namespace. The second is specifying an image (and optional a namespace) and a tag. When the first option is used (no tag is specified), the tool will migrate ALL the tags for that particular image name.

For example:
```
busybox
jfrog/artifactory-pro
jfrog/mission-control:1.0
```

This would result in all tags of `busybox` and `jfrog/artifactory-pro` being migrated but only the 1.0 tag for `jfrog/mission-control`.

## Security Migration

To migrate security information from the Docker registry to Artifactory, follow the steps described at the Data Migration session but use the `SecurityMigrator.py` script instead of `DockerMigrator.py`. Examples:

* Using Python: 
```bash
python SecurityMigrator.py ......
```
   * Using Docker: 
```bash
docker run -it --rm --name my-running-script -v "$PWD":/usr/src/myapp -w /usr/src/myapp python:2.7.14 python SecurityMigrator.py .....
```

### Docker EE Security Migration

Using this option, the tool reads Users, Organizations and Teams data from Docker Universal Control Plane (UCP) and Permissions information from Docker Trusted Registry (DTR) and creates the appropriate Users, Groups and Permissions in Artifactory. This feature has been tested with UCP 2.2.5 and DTR 2.4.1.

#### Input

```bash
usage: python SecurityMigrator.py dockeree [-h] [--ignore-certs] [--overwrite]
                                           [-v]
                                           ucp dtr dockeree-username
                                           dockeree-password artifactory
                                           username password repo
                                           initial-password email-suffix

Docker EE security data to Artifactory migrator. Migrates users, teams and
permissions from Docker EE UCP and DTR to Artifactory.

positional arguments:
  initial-password   The password to be assigned to migrated users in
                     Artifactory
  email-suffix       The email suffix to be assigned to migrated users in
                     Artifactory

optional arguments:
  -h, --help         show this help message and exit
  --ignore-certs     Ignore any certificate errors from both source and
                     destination
  --overwrite        Overwrite existing users, groups or permissions on the
                     destination
  -v, --verbose      Make the operation more talkative

dockeree:
  ucp                The Docker Universal Control Plane (UCP) URL
  dtr                The Docker Trusted Registry (DTR) URL
  dockeree-username  The username to use for authentication to the Docker EE
                     tools
  dockeree-password  The password to use for authentication to the Docker EE
                     tools

artifactory:
  artifactory        The destination Artifactory URL
  username           The username to use for authentication to Artifactory
  password           The password to use for authentication to Artifactory
  repo               The docker repository
```

### Quay EE Security Migration

Using this option, the tool reads users, organization robots, organizations, teams, and permissions. The tools imports these elements (with some adjustments and mappings). See Limitations and Notes.

#### LIMITATIONS AND NOTES

* To use this tool, you **need** to [generate a token for internal application use (for a super user)](https://docs.quay.io/api/)
* Only the organization/repos/permissions the super user has access to will be imported
* To properly import all permissions, all users/organizations need to make the super user account being used to run this tool an admin of the repository/organization
* Robot accounts
  * Imported only for organizations
  * Name changes from org+name to org-name
  * Retain their same keys but it is a password in Artifactory

#### Input

```bash
usage: python SecurityMigrator.py quayee [-h] [--ignore-certs] [--overwrite]
                                         [-v]
                                         source token artifactory username
                                         password repo initial-password

Quay EE security data to Artifactory migrator. Migrates users, teams and
permissions from Quay EE to Artifactory.

positional arguments:
  initial-password  The password to be assigned to migrated users in
                    Artifactory

optional arguments:
  -h, --help        show this help message and exit
  --ignore-certs    Ignore any certificate errors from both source and
                    destination
  --overwrite       Overwrite existing users, groups or permissions on the
                    destination
  -v, --verbose     Make the operation more talkative

source:
  source            The source registry URL
  token             The OAuth2 Access Token of the super user

artifactory:
  artifactory       The destination Artifactory URL
  username          The username to use for authentication to Artifactory
  password          The password to use for authentication to Artifactory
  repo              The docker repository
 ```


---
# Testing

This project uses Python's [unittest framework][]. To run the tests, you can use your favorite IDE, or run them from the command line.

## Setup
1. Copy the tests/config/*.example to tests/config/* and populate the properties

To run the unit tests from the command line (requires Python 2.7):

``` shell
cd tests
python -m unittest discover -v -p "*Test.py"
```

[unittest framework]: https://docs.python.org/2/library/unittest.html

