#!/bin/sh
#
# CBIIT deployment script for EDRN.
#
# Called by Jenkins to deploy the EDRN application to edrn-dev.nci.nih.gov,
# edrn-stage, and edrn (production) too.
#
# Originally by Cuong Nguyen.
# Modified by @nutjob4life

echo ""
echo "👉 pwd"
pwd

echo ""
echo "👉 Directory listing:"
ls

echo ""
echo "👉 What docker (and version) are we using"
ssh -q $USER@$WEBSERVER "which docker ; docker --version" || exit 1

echo "🏃 Begin deployment to $WEBSERVER"

echo ""
echo "👉 Here is what is on $WEBSERVER in $WEBROOT"

ssh -q $USER@$WEBSERVER "ls -l $WEBROOT"

echo ""
echo "🧹Cleaning up remote workspace"

ssh -q $USER@$WEBSERVER "sudo chown -R $USER:$USER /local/content/edrn &&\
rm -rf $WEBROOT/docker-compose.yaml $WEBROOT/../media $WEBROOT/../static $WEBROOT/../postgresql $WEBROOT/.env &&\
mkdir $WEBROOT/../media $WEBROOT/../static $WEBROOT/../postgresql &&\
ls -lF $WEBROOT"

echo ""
echo "🍃 Making a .env file"

rm -f .env
cat >.env <<EOF
ALLOWED_HOSTS=$ALLOWED_HOSTS
EDRN_DATA_DIR=$EDRN_DATA_DIR
EDRN_PUBLISHED_PORT=$EDRN_PUBLISHED_PORT
EDRN_VERSION=$EDRN_VERSION
LDAP_BIND_PASSWORD=$LDAP_BIND_PASSWORD
POSTGRES_PASSWORD=$POSTGRES_PASSWORD
POSTGRES_USER_ID=$POSTGRES_USER_ID
SIGNING_KEY=$SIGNING_KEY 
EOF
ls -la .env

echo ""
echo "© Copying .env file to $WEBROOT"
scp .env $USER@$WEBSERVER:$WEBROOT

echo ""
echo "👉 Fetching the latest docker-compose.yaml"

ssh -q $USER@$WEBSERVER "cd $WEBROOT &&\
curl --silent --fail --location --remote-name https://github.com/EDRN/P5/raw/main/docker/docker-compose.yaml" || exit 1

echo ""
echo "👉 Update ownership and check directory listing:"

ssh -q $USER@$WEBSERVER "chown -R $USER:$USER $WEBROOT ; \
cd $WEBROOT ; \
head -4 docker-compose.yaml ; \
ls -la $WEBROOT" || exit 1

echo ""
echo "👉 Use Docker compose to bring down all the containers"
ssh -q $USER@$WEBSERVER "cd $WEBROOT && \
docker compose --project-name edrn down --remove-orphans &&\
docker compose rm --force --stop --volumes &&\
docker container ls" || exit 1

echo ""
echo "🪢 Pulling the images anonymously"
ssh -q $USER@$WEBSERVER "cd $WEBROOT ; \
docker logout ncidockerhub.nci.nih.gov && docker logout &&\
docker compose --project-name edrn pull --include-deps --quiet" || exit 1

echo ""
echo "👉 Use Docker compose to bring up all the containers, and list what's running once complete."

ssh -q $USER@$WEBSERVER "cd $WEBROOT ; \
docker compose --project-name edrn up --detach &&\
docker container ls" || exit 1

echo ""
echo "⏱ Giving processes a little time to warm up"
sleep 17

echo ""
echo "🕵️ Checking on containers"
ssh -q $USER@$WEBSERVER "cd $WEBROOT && docker compose --project-name edrn ps"


echo ""
echo "👷‍♀️ Initial database schema and population"

ssh -q $USER@$WEBSERVER "cd $WEBROOT ; \
docker compose --project-name edrn exec db createdb --username=postgres --encoding=UTF8 --owner=postgres edrn &&\
docker compose --project-name edrn exec portal django-admin migrate &&\
docker compose --project-name edrn run --volume $WEBROOT/../exports:/mnt/zope --volume $WEBROOT/../blobstorage:/mnt/blobs \
    --entrypoint /usr/bin/django-admin --no-deps portal importfromplone \
    http://nohost/edrn/ /mnt/zope/edrn.json /mnt/zope/export_defaultpages.json /mnt/blobs &&\
docker compose --project-name edrn exec portal django-admin collectstatic --no-input &&\
docker compose --project-name edrn exec portal django-admin edrnbloom $EDRN_LITE --hostname $FINAL_HOSTNAME &&\
docker compose --project-name edrn exec portal django-admin investigator_addresses --import" || exit 1

echo ""
echo "🔐 Doing LDAP group sync"
ssh -q $USER@$WEBSERVER "cd $WEBROOT ; \
docker compose --project-name edrn exec portal django-admin ldap_group_sync
" || exit 1


# Disabling for now; can do this TTW
#
# echo ""
# echo "📀 Initial ingest … hold onto your hats"

# ssh -q $USER@$WEBSERVER "cd $WEBROOT ; \
# docker compose --project-name edrn exec --detach --no-TTY portal django-admin rdfingest" || exit 1

echo ""
echo "📓 Populating main menus"

ssh -q $USER@$WEBSERVER "cd $WEBROOT ; \
docker compose --project-name edrn exec portal django-admin autopopulate_main_menus" || exit 1

echo ""
echo "👉 Restart Apache"

ssh -q $USER@$WEBSERVER "sudo systemctl restart apache" || exit 1

echo ""
echo "👉 Done with $WEBSERVER"

echo ""
