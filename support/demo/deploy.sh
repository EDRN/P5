#!/bin/sh
#
# Deploy the P5 Renaissance demonstration portal to its demo platform
#
#
# Constants
# ---------
#
# Just the port number so far, EDRN_PUBLISHED_PORT.
#
# You can also override the INSTALLD_DIR; it defaults to /usr/local/labcas/portal/renaissance. In addition
# the following variables **must** be set:
#
# - POSTGRES_PASSWORD … a password to use for PostgreSQL
# - SIGNING_KEY … a key with which to sign HTTP sessions
# - LDAP_BIND_PASSWORD … password to the EDRN LDAP service account

export EDRN_PUBLISHED_PORT=${EDRN_PUBLISHED_PORT:-4136}

: ${POSTGRES_PASSWORD:?✋ The environment variable POSTGRES_PASSWORD is required}
: ${SIGNING_KEY:?✋ The environment variable SIGNING_KEY is required}
: ${LDAP_BIND_PASSWORD:?✋ The environment variable LDAP_BIND_PASSWORD is required}


# Execution Path
# --------------
#
# Use only our "trusted" locations for executables.

PATH=/usr/local/bin:/usr/bin:/usr/sbin:/bin:/sbin
export PATH


# Set up Installation Directory
# -----------------------------
#
# Docker on edrn-docker leaves behind turds we cannot delete so find a new directory in which to store our
# stuff. 

home=${INSTALL_DIR:-/usr/local/labcas/portal/renaissance}
[ -d $home/volumes ] || mkdir --parents $home/volumes
index=0
while [ -d ${home}/volumes/data.${index} ]; do
    echo "💁‍♀️ Old data directory «${home}/volumes/data.${index}» found and may be deleted" 1>&2
    # Go ahead and try to delete as much as we can of the old dir
    rm --recursive --force ${home}/volumes/data.${index} >/dev/null 2>&1
    index=`expr $index + 1`
done
export EDRN_DATA_DIR="${home}/volumes/data.${index}"
if ! mkdir --parents $EDRN_DATA_DIR; then
    echo "Cannot make new data directory «${EDRN_DATA_DIR}»; giving up " 1>&2
    exit 1
fi
rm --force $home/data && ln -s $EDRN_DATA_DIR $home/data


# Compose Detection
# -----------------
#
# Can we use `docker compose` or must we stick with `docker-compose`?

docker compose >/dev/null 2>&1
if [ $? -ne 0 ]; then
    compose="`which docker-compose` --project-name renaissance --file ${home}/docker-compose.yaml"
else
    compose="`which docker` compose --project-name renaissance --file ${home}/docker-compose.yaml"
fi

# From here down, failures should be fatal
set -e


# Cleanup
# -------
#
# Start with a clean slate. Note that as we go along we might save time by preserving things between
# deployments. But for now, nice and clean.

$compose down --remove-orphans
for d in media postgresql static elasticsearch; do
    rm --recursive --force $EDRN_DATA_DIR/$d
    mkdir $EDRN_DATA_DIR/$d
done


# Launch
# ------
#
# We update the images as well.

export EDRN_VERSION='latest'
export ALLOWED_HOSTS='edrn.jpl.nasa.gov,localhost'
export SECURE_COOKIES='True'
export BASE_URL='https://edrn.jpl.nasa.gov/portal/5/renaissance/'    
export STATIC_URL='/renaissance/static/'
export MEDIA_URL='/renaissance/media/'
export FORCE_SCRIPT_NAME='/renaissance'
$compose pull --quiet
$compose up --detach


# Populate
# --------
#
# We need to make the database, apply the schema, and load the data. We also need to wait sufficient time
# for the serivces to start up.
#
# Would prefer `--no-tty` over `-T`` but Compose version on edrn-docker is old 😩

sleep 17
$compose exec -T db createdb --username postgres --encoding=UTF-8 --owner=postgres --no-password edrn
$compose exec -T portal django-admin migrate --no-input
for cmd in edrnbloom rdfingest autopopulate_main_menus; do
    $compose exec -T portal django-admin $cmd
done


# Static Files & Media
# --------------------
#
# The portal image contains the static files (css, images, js) needed to deliver a complete application. We
# extract those so the front-end web server can provide those directly.

$compose exec -T portal /bin/tar -cOh -C /app static | tar -x -C $EDRN_DATA_DIR -f -


# Done
# ----
#
# 🤔 Should we include a health check here?

exit 0
