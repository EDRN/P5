# NCI Deployment

Deploying the EDRN public portal (website, knowledge environment, and so forth; hereafter "portal") to the development, staging, and production tiers at the National Cancer Institute involves taking a snapshot of the production database, pulling the new software image from the Docker Hub, applying schema modifications to the database, and starting the Docker composition.

This document describes how to accomplish this.

👉 **Note:** By "database", we are referring to _both_ the PostgreSQL database that contains the portal content and the `media` folder that contains the media blobs (images, PDF files, PowerPoints, etc.)

Up to and including version 6.19.0 of the portal, [NCI Drupal Jenkins](https://nci-drupal-jenkins.nci.nih.gov/jenkins/login?from=%2Fjenkins%2F) automated the deployment of the software to the development, staging, and production tiers. Based on information from [Mahdi Dayan](mahdi.dayan@nih.gov), this will still be the case with the transition to [Oracle Linux 8](https://docs.oracle.com/en/operating-systems/oracle-linux/8/index.html) (OL8) and version 6.20.0 and later versions.


## Current Hosts

For version 6.19.0 and OL7, the current deployment hosts for the portal are as follows:

| Tier        | Host                        | Via                             |
|:------------|:----------------------------|:--------------------------------|
| Development | `nciws-d2094-c.nci.nih.gov` | https://edrn-dev.nci.nih.gov/   |
| Staging     | `nciws-s2101-c.nci.nih.gov` | https://edrn-stage.nci.nih.gov/ |
| Production  | `nciws-p2102-c.nci.nih.gov` | https://edrn.nci.nih.gov        |

👉 **Note:** The new canonical URL for the EDRN portal will be https://edrn.cancer.gov/

For version 6.20.0 and later, the new hosts are to be determined. The above hosts are all OL7 and will be decommissioned in favor of new OL8 platforms.

👉 **Note:** The EDRN portal software is completely containerized with Docker; [investigation into deploying with ECS Fargate](https://github.com/EDRN/P5/issues/418) is on the docket.


## The Properties and the Environment

The portal is deployed using the [CBIIT Drupal Jenkins instance]() which starts a Docker Composition ("`docker compose`") on a remote server. The Docker Composition uses an `.env` files that's populated with values from the "Properties" section on the Jenkins configurations for each portal tier.

 which itself uses a number of environment variables that are all contained within a `.env` file. Some of these variables have well-known values, some are arbitrary, and some contain secrets.

The following table describes the values that must go into the `.env` file before the portal is deployed and is required for the portal to run:

| Variable                | Purpose                                                  | Value                             |
|:------------------------|:---------------------------------------------------------|:----------------------------------|
| `BASE_URL`              | The URL of the portal, varies on tier                    | See below                         |
| `EDRN_DATA_DIR`         | Folder for `media` and `postgresql` Docker bind volumes  | Defaults to `/local/content/edrn` |
| `EDRN_PUBLISHED_PORT`   | Host port where portal answers `http:`                   | Defaults to 8080                  |
| `EDRN_VERSION`          | EDRN Docker image tag                                    | Defaults to `latest-uid26013`     |
| `LDAP_BIND_PASSWORD`    | For service account on ldaps://edrn-ds.jpl.nasa.gov      | Provided; see "Secrets"           |
| `POSTGRES_PASSWORD`     | Password to use for PostgreSQL                           | Can be anything; see "Secrets"    |
| `RECAPTCHA_PRIVATE_KEY` | Private API key for the reCAPTCHA service                | Provided; see "Secrets"           |
| `RECAPTCHA_PUBLIC_KEY`  | Public API key for the reCAPTCHA service                 | Provided; see "Secrets"           |
| `SIGNING_KEY`           | Hash input for creating session IDs, etc.                | Can be anything; see "Secrets"    |

Some notes on the above:

- The `BASE_URL` is either `https://edrn.cancer.gov/` (for production), `https://edrn-stage.nci.nih.gov/` (staging tier), for `https://edrn-dev.nci.nih.gov/` (development tier).
- See the following section on "Secrets" for additional details.


### Secrets

The portal uses several secrets in its operation. Some of these are arbitrary values that must be kept secret in the `.env` file, and some are provided and must be kept secret at all times (in the `.env` file, during transfer from one person to another, etc.).


### Arbitrary Secrets

The portal uses two arbitrary secrets; when creating the `.env` file, you can use any random text for these, but high-entropy strings of mixed letters and numbers are recommended.

- `POSTGRES_PASSWORD` is used to create and to connect to the portal database in Postgres.
- `SIGNING_KEY` is used to sign secure data, such as for signing session cookies and generating cross-site request forgert (CRSF) tokens for forms. It should be unique per portal installation and kept secret once created. 


### Provided Secrets

The portal uses three secrets that are maintained by JPL and must be provided to any new instance in a secure method, such as using encrypted email. These secrets aid in the operation of the portal and are as follows:

- `LDAP_BIND_PASSWORD` is used to authenticate a "service" account in the EDRN Directory at `ldaps://edrn-ds.jpl.nasa.gov`. This is used to look up users and groups in the portal when a user is not logged into the portal.
- `RECAPTCHA_PUBLIC_KEY` and `RECAPTCHA_PRIVATE_KEY` are the public and private API keys for the [reCAPTCHA](https://developers.google.com/recaptcha) service, which is used to protect against abuse of several web forms provided on the portal.


### Deprecated Properties

The following properties may still appear in the Jenkins configuration, however, they are no longer used:

- 

## Docker Images

The portal's `docker-compose.yaml` file uses several images in order to start the composed set of container-based services that run the software. The thrid-party images in use are:

- `postgres:17.6-alpine` — database for portal content; the container writes to a persistent bind-based volume
- `redis:7.0.11-alpine3.18` — cache and message broker service
- `elasticsearch:8.10.2` — full text indexing and search service
- `edrndocker/edrn-portal` — the actual portal software, based on the [Wagtail 7](https://wagtail.org/org) content management system, the [Django 5](https://www.djangoproject.com/) web framework, and the [Python 3.13](https://www.python.org/) programming language

The `edrndocker/edrn-portal` image has two main "flavors" of version tags:

- `edrndocker/edrn-portal:X.Y.Z-uid26013` or `edrndocker/edrn-portal:latest-uid26013` — a Linux-based image that uses user ID 26013 internally
- `edrndocker/edrn-portal:X.Y.Z-uid500` or `edrndocker/edrn-portal:latest-uid500` — a Linux-based image that uses user ID 500 internally

`X.Y.Z` refers to the major, minor, and micro version numbers. User ID 26013 was historically the `edrn` user on CBIIT-based machines at NCI and is required to run on `nciws-d2094-c.nci.nih.gov`, `nciws-s2101-c.nci.nih.gov`, and `nciws-p2102-c.nci.nih.gov`. User ID 500 is used at JPL.

**To deploy the portal at NCI, use the `-uid26013` version tags**.


## Development and Staging Tiers

To deploy the portal to the development and staging tiers, do the following:

1. **Prepare the deployment environment.** Set up a local workspace directory where you'll run the deployment from. You'll need:
   - SSH access to the target server (`nciws-d2094-c.nci.nih.gov` for development, `nciws-s2101-c.nci.nih.gov` for staging)
   - NIH username and password for accessing the production database at https://edrn.nci.nih.gov/database-access
   - Historically, this has been `/local/content/edrn/docker`, which should now be the current working directory.

2. **Set the environment variables.** Create the `.env` file with the 10 environment varialbes as listed above under "Environement. Set two additional environment variables:
   - `NIH_USERNAME` set to a NED user ID that has access to https://edrn.nci.nih.gov/database-access
   - `NIH_PASSWORD`, the password for `NIH_USERNAME`

3. **Retrieve the deployment script from GitHub:**
   ```bash
   curl -LO https://raw.githubusercontent.com/EDRN/P5/refs/heads/main/support/cbiit-deploy.sh
   chmod +x cbiit-deploy.sh
   ```

👉 **Note:** Always retrieve this file even if an older copiy exist on the filesystem, in case there have been recent updates.

4. **Run the deployment script.** Execute the deployment script:
   ```bash
   ./cbiit-deploy.sh
   ```
   The script will automatically:
   - Clean up the remote workspace (removing old files, media, static, and PostgreSQL directories)
   - Generate and copy a `.env` file to the target server with all necessary environment variables
   - Fetch the latest `docker-compose.yaml` and `sync-from-ops.sh` from GitHub
   - Download the production database snapshot (`edrn.sql.bz2`) and media files from the production server
   - Stop and remove all existing Docker containers
   - Pull the new Docker image (version specified by `EDRN_VERSION`)
   - Start the Docker containers (PostgreSQL database and portal application)
   - Drop and recreate the `edrn` database
   - Load the production database snapshot into the new database
   - Run Django migrations with `django-admin migrate`
   - Fix the content tree with `django-admin fixtree`
   - Collect static files with `django-admin collectstatic`
   - Reset development-specific settings with `django-admin edrndevreset`
   - Apply any version-specific upgrade commands
   - Restart the portal and search engine containers
   - Restart the Apache web server

5. **Monitor the deployment.** The deployment script will output progress messages as it executes each step. The entire process typically takes 30-45 minutes. If the deployment appears to hang for more than 45 minutes, abort and investigate.

6. **Verify the deployment.** Once complete, verify that the portal is accessible at the expected URL (e.g., https://edrn-dev.nci.nih.gov/ for development, https://edrn-stage.nci.nih.gov/ for staging) and that the portal is functioning correctly.


Input: image version (default: latest-uid26013), becomes EDRN_VERSION

Why uid 26013? 

Git repo: https://github.com/EDRN/P5.git

Secrets? I think we can skip these now — unless we need the NED secrets to fetch the DB?

Properties → .env

DEPLOYER_URL=https://raw.githubusercontent.com/EDRN/P5/main/support/cbiit-deploy.sh
WEBSERVER=nciws-d2094-c
USER=edrn
POSTGRES_USER_ID=26013
WEBROOT=/local/content/edrn/docker
NCIDOCKERHUB_USER=edrndocker-user
EDRN_DATA_DIR=/local/content/edrn
EDRN_PUBLISHED_PORT=8080
FINAL_HOSTNAME=edrn-dev.nci.nih.gov
POSTGRES_PASSWORD=rotated
LDAP_BIND_PASSWORD=changed
SIGNING_KEY=rotated
EDRN_LITE=--lite
RECAPTCHA_PRIVATE_KEY=rotated
RECAPTCHA_PUBLIC_KEY=rotated

Do RECAPTCHA still need to be set? Yes

Fetch deployment script from GitHub

Run: ${WORKSPACE}/support/cbiit-deploy.sh

What does WORKSPACE look like?

Abort if stuck after 45 minutes

