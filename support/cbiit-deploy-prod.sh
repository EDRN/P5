#!/bin/sh
#
# CBIIT deployment script for EDRN — for PRODUCTION use
# Although you can do it on edrn-stage as well.
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
echo "🧹Cleaning up remote production workspace and keeping the media dir around"

ssh -q $USER@$WEBSERVER "sudo chown -R $USER:$USER /local/content/edrn &&\
rm -rf $WEBROOT/docker-compose.yaml $WEBROOT/../static $WEBROOT/../postgresql $WEBROOT/.env &&\
mkdir $WEBROOT/../static $WEBROOT/../postgresql &&\
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
RECAPTCHA_PRIVATE_KEY=$RECAPTCHA_PRIVATE_KEY
RECAPTCHA_PUBLIC_KEY=$RECAPTCHA_PUBLIC_KEY
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
docker image rm --force nutjob4life/edrn-portal:$EDRN_VERSION &"

# The `docker image rm` step can take a long time, and sshd will time out the
# idle connection because it's a despotic and horrible server.
sleep 400

ssh -q $USER@$WEBSERVER "cd $WEBROOT ; \
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
echo "👷‍♀️ Upgrading production DB"

ssh -q $USER@$WEBSERVER "cd $WEBROOT ; \
docker compose --project-name edrn exec db dropdb --force --if-exists --username=postgres edrn &&\
docker compose --project-name edrn exec db createdb --username=postgres --encoding=UTF8 --owner=postgres edrn" || exit 1
ssh -q $USER@$WEBSERVER "cd $WEBROOT ; \
[ -f /local/content/edrn/database-access/edrn.sql.bz2 ] &&\
bzip2 --decompress --stdout /local/content/edrn/database-access/edrn.sql.bz2 | \
    docker compose --project-name edrn exec --no-TTY db psql --username=postgres --dbname=edrn --echo-errors --quiet" || exit 1


echo ""
echo "📀 Initial database setup"
ssh -q $USER@$WEBSERVER "cd $WEBROOT ; \
docker compose --project-name edrn exec portal django-admin fixtree &&\
docker compose --project-name edrn exec portal django-admin makemigrations &&\
docker compose --project-name edrn exec portal django-admin migrate &&\
docker compose --project-name edrn exec portal django-admin collectstatic --no-input --clear" || exit 1

echo ""
echo "🤷‍♀️ Restarting the portal and stopping search engine"
ssh -q $USER@$WEBSERVER "cd $WEBROOT ; \
docker compose --project-name edrn stop portal &&\
docker compose --project-name edrn stop search &&\
sleep 60 &&\
docker compose --project-name edrn start portal" || exit 1

echo ""
echo "🆙 Applying upgrades"
ssh -q $USER@$WEBSERVER "cd $WEBROOT ; \
docker compose --project-name edrn exec portal django-admin edrnnewforms" || exit 1

echo ""
echo "🤷‍♀️ Final portal restart and restart of search engine"
ssh -q $USER@$WEBSERVER "cd $WEBROOT ; \
docker compose --project-name edrn stop portal &&\
sleep 60 &&\
docker compose --project-name edrn start search &&\
docker compose --project-name edrn start portal" || exit 1

echo ""
echo "👉 Restart Apache"
ssh -q $USER@$WEBSERVER "sudo systemctl stop apache ; sudo systemctl start apache" || exit 1

echo ""
echo "👉 Done with $WEBSERVER"

echo ""
