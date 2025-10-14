# NCI Deployment

Deploying the EDRN public portal (website, knowledge environment, and so forth; hereafter "portal") to the development, staging, and production tiers at the National Cancer Institute involves taking a snapshot of the production database, pulling the new software image from the Docker Hub, applying schema modifications to the database, and starting the Docker composition.

This document describes how to accomplish this.

👉 **Note:** By "database", we are referring to _both_ the PostgreSQL database that contains the portal content and the `media` folder that contains the media blobs (images, PDF files, PowerPoints, etc.)

Up to and including version 6.19.0 of the portal running on [Oracle Linux 7](https://docs.oracle.com/en/operating-systems/oracle-linux/7/), [NCI Drupal Jenkins](https://nci-drupal-jenkins.nci.nih.gov/jenkins/login?from=%2Fjenkins%2F) automated the deployment of the software to the development, staging, and production tiers. Based on information from [Mahdi Dayan](mahdi.dayan@nih.gov), this will still be the case with the transition to version 6.20.0 of the portal on [Oracle Linux 8](https://docs.oracle.com/en/operating-systems/oracle-linux/8/index.html) (OL8).


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

The portal is deployed using the [CBIIT Drupal Jenkins instance](https://nci-drupal-jenkins.nci.nih.gov/jenkins) which starts a Docker Composition ("`docker compose`") on a remote server. The Docker Composition uses a `.env` file that's populated with values from the "Properties" section on the Jenkins configurations for each portal tier.

Some of these properties have common and well-known values, some are arbitrary, and some contain secrets.

The following table describes the properties that automatically end up in the `.env` file before the portal is deployed and is required for the portal to run:

| Variable                | Purpose                                                  | Value                             |
|:------------------------|:---------------------------------------------------------|:----------------------------------|
| `EDRN_DATA_DIR`         | Folder for `media` and `postgresql` Docker bind volumes  | `/local/content/edrn`             |
| `EDRN_LITE`             | Not used                                                 | Doesn't matter                    |
| `EDRN_PUBLISHED_PORT`   | Host port where portal answers `http:`                   | `8080`                            |
| `EDRN_VERSION`          | EDRN Docker image tag                                    | Defaults to `latest-uid26013`     |
| `FINAL_HOSTNAME`        | Host part of the portal URL, varies by tier              | See below                         |
| `LDAP_BIND_PASSWORD`    | For service account on ldaps://edrn-ds.jpl.nasa.gov      | Provided; see "Secrets"           |
| `NCIDOCKERHUB_USER`     | Not used                                                 | Doesn't matter                    |
| `POSTGRES_PASSWORD`     | Password to use for PostgreSQL                           | Can be anything; see "Secrets"    |
| `POSTGRES_USER_ID`      | Not used                                                 | Doesn't matter                    |
| `RECAPTCHA_PRIVATE_KEY` | Private API key for the reCAPTCHA service                | Provided; see "Secrets"           |
| `RECAPTCHA_PUBLIC_KEY`  | Public API key for the reCAPTCHA service                 | Provided; see "Secrets"           |
| `SIGNING_KEY`           | Hash input for creating session IDs, etc.                | Can be anything; see "Secrets"    |
| `USER`                  | Username to ssh into on `WEBSERVER`                      | `edrn`                            |
| `WEBSERVER`             | Hostname where the software is deployed                  | See below                         |

Some notes on the above:

- The `FINAL_HOSTNAME` is either `edrn.nci.nih.gov` (for production, and in the future `edrn.cancer.gov`), `edrn-stage.nci.nih.gov` (staging tier), or `edrn-dev.nci.nih.gov` (development tier).
- The `WEBSERVER` is `nciws-d2094-c.nci.nih.gov` (development), `nciws-s2101-c.nci.nih.gov` (staging), `nciws-p2102-c.nci.nih.gov` (prodcution); for OL8, these names will change.
- See the following section on "Secrets" for additional details.

There are also two environment variables that are used in the development and staging tiers:

- `NIH_USERNAME`, a NED username (currently set to `kellysc`, Sean Kelly's NED username)
- `NIH_PASSWORD`, the password for the `NIH_USERNAME`

The production host has a daily cron job that copies its database (a PostgreSQL `.sql` dump file and the media blobs) to https://edrn.nci.nih.gov/database-access so that the development and staging tiers have a baseline of production data that can be used to build new versions of the portal. (This is not needed in production because the database is already present in production.) Access to https://edrn.nci.nih.gov/database-access is limited to NED users via `NIH_USERNAME` and `NIH_PASSWORD`. These variables should be set in [NCI Drupal Jenkins](https://nci-drupal-jenkins.nci.nih.gov/jenkins/login?from=%2Fjenkins%2F) using the Jenkins credential manager—and should be updated whenever the `NIH_PASSWORD` is rotated.


### Secrets

The portal uses several secrets in its operation. Some of these are arbitrary values that and some are provided and must be kept secret at all times (while viewing Jenkins, in the `.env` files, during transfer from one person to another, etc.).


#### Arbitrary Secrets

The portal uses two arbitrary secrets; when updating the Jenkins properties, you can use any random text for these, but high-entropy strings of mixed letters and numbers are recommended. These can and should be changed with each deployment.
 
- `POSTGRES_PASSWORD` is used to create and to connect to the portal database in PostgreSQL.
- `SIGNING_KEY` is used to sign secure data, such as for signing session cookies and generating cross-site request forgery (CRSF) tokens for forms. It should be unique per portal installation and kept secret once created. 


#### Provided Secrets

The portal uses three secrets that are maintained by JPL and must be provided to any new instance in a secure method, such as using encrypted email or entered directly into Jenkins by a JPL representative. These secrets aid in the operation of the portal and are as follows:

- `LDAP_BIND_PASSWORD` is used to authenticate a "service" account in the EDRN Directory at `ldaps://edrn-ds.jpl.nasa.gov`. This is used to look up users and groups in the portal when a user is not logged into the portal.
- `RECAPTCHA_PUBLIC_KEY` and `RECAPTCHA_PRIVATE_KEY` are the public and private API keys for the [reCAPTCHA](https://developers.google.com/recaptcha) service, which is used to protect against abuse of several web forms provided on the portal.


### Deprecated Properties

The following properties may still appear in the Jenkins configuration, however, they are no longer used:

- `EDRN_LITE`
- `NCIDOCKERHUB_USER`
- `POSTGRES_USER_ID`
 

## Docker Images

The portal's `docker-compose.yaml` file uses several images in order to start the composed set of container-based services that run the software. The third-party images in use are:

- `postgres:17.6-alpine` — database for portal content; the container writes to a persistent bind-based volume
- `redis:7.0.11-alpine3.18` — cache and message broker service
- `elasticsearch:8.10.2` — full text indexing and search service

The `edrndocker/edrn-portal` image is the actual portal software, based on the [Wagtail 7](https://wagtail.org/org) content management system, the [Django 5](https://www.djangoproject.com/) web framework, and the [Python 3.13](https://www.python.org/) programming language. The `edrndocker/edrn-portal` image has two main "flavors" of version tags:

- `edrndocker/edrn-portal:X.Y.Z-uid26013` or `edrndocker/edrn-portal:latest-uid26013` — a Linux-based image that uses user ID 26013 internally
- `edrndocker/edrn-portal:X.Y.Z-uid500` or `edrndocker/edrn-portal:latest-uid500` — a Linux-based image that uses user ID 500 internally

`X.Y.Z` refers to the major, minor, and micro version numbers. User ID 26013 was historically the `edrn` user on CBIIT-based machines at NCI and is required to run on `nciws-d2094-c.nci.nih.gov`, `nciws-s2101-c.nci.nih.gov`, and `nciws-p2102-c.nci.nih.gov`. User ID 500 is used at JPL.

👉 **Note:** To deploy the portal at NCI, use the `-uid26013` version tags.


## Deployment

The remainder of this document tells how to deploy the portal to the development, staging, and production tiers. All deployment is accomplished with [NCI Drupal Jenkins](https://nci-drupal-jenkins.nci.nih.gov/jenkins/login?from=%2Fjenkins%2F). This enables "one-click" deployment for the most part—although a review and rotation of the `POSTGRES_PASSWORD` and `SIGNING_KEY` properties is recommended. The production tier should be backed-up first, as well, but that is described below.


### Development and Staging Tiers

To deploy the portal to the development and staging tiers, do the following:

1.  Visit NCI Drupal Jenkins and locate the job for the desired tier (development or staging).
2.  Click the "Run Now ▶️" button (after updating the Properties, if necessary).
3.  When prompted for the version of the image, enter the desired version tag:
    -   For development, this is typically `latest-uid26013`
    -   For staging, it's typically whatever the next official release will be, `X.Y.Z-uid26013`
4.  Monitor the deployment the console output. The deployment script will output progress messages as it executes each step. The entire process typically takes 15–30 minutes. If the deployment appears to hang for more than 45 minutes, abort and investigate.
5. Verify the deployment. Once complete, verify that the portal is accessible at the expected URL (https://edrn-dev.nci.nih.gov/ for development or https://edrn-stage.nci.nih.gov/ for staging).


### Production Tier

To deploy the portal to the production tier, first backup the data as follows:

1.  Remove any old backups.
2.  Make fresh backups of the following folders:
    - `/local/content/edrn/database-access`
    - `/local/content/edrn/docker`
    - `/local/content/edrn/media`
    - `/local/content/edrn/postgresql`
    - `/local/content/edrn/static`

Then, proceed as follows:

1.  Visit NCI Drupal Jenkins and locate the job for the production tier.
2.  Click the "Run Now ▶️" button (after updating the Properties, if necessary).
3.  When prompted for the version of the image, enter the desired version tag of the form `X.Y.Z-uid26013`.
4.  Monitor the deployment the console output. The deployment script will output progress messages as it executes each step. The entire process typically takes 15–30 minutes. If the deployment appears to hang for more than 45 minutes, abort and investigate.
5.  Verify the deployment. Once complete, verify that the portal is accessible at the expected URL (https://edrn.nci.nih.gov, or in the future, https://edrn.cancer.gov/).
