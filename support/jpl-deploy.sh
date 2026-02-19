#!/bin/sh -e
#
# Deploy the EDRN public portal onto edrn-docker for testing purposes.
#
# Expect to run this in /usr/local/labcas/portal.

if [ ! -f "docker-compose.yaml" -o ! -f ".env" ]; then
    echo "🚨 Run this from the /usr/local/labcas/portal directory" 1>&2
    echo "You should have a docker-compose.yaml and a .env file in the current directory" 1>&2
    exit 1
fi
if [ `whoami` != "edrn" ]; then
    echo "🚨 Run this as user edrn" 1>&2
    exit 1
fi
if [ ! -f "${HOME}/.ssh/tumor-access" ]; then
    echo "🚨 The tumor-access key pair isn't in ${HOME}/.ssh/tumor-access" 1>&2
    echo "Please create it and add the public key to ~edrn/.ssh/authorized_keys on tumor" 1>&2
    exit 1
fi
if [ ! -x "sync-from-dev.sh" ]; then
    echo "🚨 The sync-from-dev.sh script isn't in the current directory" 1>&2
    echo "Please download it from https://github.com/EDRN/P5/raw/refs/heads/main/support/sync-from-dev.sh" 1>&2
    echo "And make it executable by running: chmod +x sync-from-dev.sh" 1>&2
    exit 1
fi

compose() {
    docker compose --project-name portal --profile tls "$@"
}

echo "🛑 Stopping and removing any existing containers and services" 1>&2
compose down --remove-orphans --volumes

# Rather than this:
# compose run --rm --volume ${PWD}/docker-data:/mnt --no-TTY --entrypoint /bin/rm db -rf /mnt/postgresql || :
# Let's try this:
docker container run --privileged --user root --rm --volume ${PWD}/docker-data:/mnt/dd --entrypoint rm busybox -r /mnt/dd/postgresql || :

# Then clean up the rest:
[ -d docker-data ] || mkdir docker-data
for sub in media postgresql; do
    echo "🧹 Removing docker-data/$sub directory" 1>&2
    rm -rf docker-data/$sub
    mkdir docker-data/$sub
done

echo "📄 ➡️ 📄📄 Getting latest database and media blobs from tumor"
eval `ssh-agent`
ssh-add ${HOME}/.ssh/tumor-access
${PWD}/sync-from-dev.sh

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
    compose exec -T db psql --username=postgres --dbname=edrn --echo-errors --quiet

echo "🏢 Applying new portal DB structure"
compose exec portal /app/bin/django-admin migrate --no-input

echo "📺 Collecting static files and so forth"
compose exec portal /app/bin/django-admin fixtree
compose exec portal /app/bin/django-admin collectstatic --no-input --clear

echo "🆙 Applying upgrades"
compose exec portal /app/bin/django-admin edrn_upgrade

echo "🔍 Ingesting RDF"
compose exec portal /app/bin/django-admin rdfingest  # Also rebuilds the Wagtail indexes in Elasticsearch

echo "🧹 Resetting to development environment"
compose exec portal /app/bin/django-admin edrndevreset

echo "🎉 Done!"
exit 0
