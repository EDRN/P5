#!/bin/sh -e
#
# CBIIT deployment script for EDRN — for PRODUCTION use
# Although you can do it on edrn-stage as well.
#
# Originally by Cuong Nguyen.
# Modified by @nutjob4life
# Updated to work directly on the target server instead of over ssh from Jenkins.
#

PATH=/usr/local/bin:/usr/bin:/bin/usr/local/sbin:/usr/sbin:/sbin
export PATH

if [ ! -f ".env" ]; then
    echo "🚨 No .env file!" 1>&2
    echo "Please create it and set the environment variables as described in the docs/nci-deployment.md" 1>&2
    exit 1
fi

# Parse command-line arguments
production="false"
for arg in "$@"; do
    if [ "$arg" = "-p" ] || [ "$arg" = "--production" ]; then
        production="true"
    fi
done

: "NIH_USERNAME=${NIH_USERNAME:?The variable NIH_USERNAME must be set}"
: "NIH_PASSWORD=${NIH_PASSWORD:?The variable NIH_PASSWORD must be set}"

curl --silent --fail --location --remote-name https://raw.githubusercontent.com/EDRN/P5/refs/heads/main/docker/docker-compose.yaml
curl --silent --fail --location --remote-name https://raw.githubusercontent.com/EDRN/P5/refs/heads/main/support/sync-from-ops.sh
chmod +x sync-from-ops.sh

compose() {
    docker compose --project-name edrn "$@"
}

echo "📀 Retrieving production database"
./sync-from-ops.sh

echo "🛑 Stopping and removing any existing containers and services"
compose down --remove-orphans --volumes

echo "🪢 Pulling latest images"
compose pull


echo "🚢 Creating containers and starting composition in detached mode" 1>&2
compose up --detach --quiet-pull --remove-orphans

echo "⏱️ Waiting a ½ minute for things to stabilize…" 1>&2
sleep 30

echo "❌ Destroying any existing portal database" 1>&2
compose exec db dropdb --force --if-exists --username=postgres edrn
echo "🫄 Creating a new empty portal database"
compose exec db createdb --username=postgres --encoding=UTF8 --owner=postgres edrn

echo "Loading latest production database"
bzip2 --decompress --stdout edrn.sql.bz2 | \
    compose exec --no-TTY db psql --username=postgres --dbname=edrn --echo-errors --quiet

echo "🏢 Applying new portal DB structure"
compose exec portal /app/bin/django-admin migrate --no-input

echo "📺 Collecting static files and so forth"
compose exec portal /app/bin/django-admin fixtree
compose exec portal /app/bin/django-admin collectstatic --no-input --clear
compose exec portal /app/bin/django-admin edrndevreset

# Additional upgrade steps go here

echo "🎉 Done!"
exit 0
