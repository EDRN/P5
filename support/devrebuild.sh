#!/bin/sh -e
#
# Devrebuild
# ==========
#
# Download the latest production database, apply migrations, and get ready to rock and roll.


jpl_sys_ipv4=172.16.16.10


# Argument check

if [ $# -ne 0 ]; then
    echo "😩 This program takes no arguments; try again?" 1>&2
    exit 1
fi


# Sentinel files check

if [ \! -f "manage.sh" ]; then
    echo "🤔 Not finding the manage.sh file; are you in the right directory?" 1>&2
    exit 1
fi


# Warning

cat <<EOF
❗️ This program will wipe out your local "edrn" PostgreSQL database, copy the
latest operations database, and then upgrade it to the current development
software you have in this working directory. If you have any local changes to
your content database or media blobs you want to preserve, abort now!

⏱️ You have 5 seconds.
EOF

sleep 5
trap 'echo "😲 Interrupted" 1>&2; exit 1' SIGINT


# Let's go

echo "🏃‍♀️Here we go"
dropdb --force --if-exists "edrn"
createdb "edrn" 'P5 for the Early Detection Research Network'
# Must use --checksum here because the nightly refresh from NCI to tumor munges all the timestamps
# rsync --checksum --no-motd --recursive --delete --progress tumor.jpl.nasa.gov:/usr/local/edrn/portal/ops-nci/media .
rsync --checksum --no-motd --recursive --delete --progress $jpl_sys_ipv4:/Users/kelly/P6/media .
touch media/.nobackup
scp $jpl_sys_ipv4:/Users/kelly/P6/edrn.sql.bz2 .
bzip2 --decompress --stdout edrn.sql.bz2 | psql --dbname=edrn --echo-errors --quiet

./manage.sh makemigrations
./manage.sh migrate
./manage.sh copy_daily_hits_from_wagtailsearch  # Wagtail 5
./manage.sh collectstatic --no-input --clear --link
./manage.sh edrndevreset

# Add additional upgrade steps here:
#
# Currently for 6.11 there is just this
# ./manage.sh edrn_biomarker_submission
# For 6.13 there's nothing yet

# This may be optional if you want to save time:
./manage.sh rdfingest
./manage.sh clear_cache --all

echo '🏁 Done! You can start it with:'
echo './manage.sh runserver 6468'

exit 0


# For 6.0.5, the commands we used to run were:
# ./manage.sh edrnpromotesearch
# ./manage.sh importpaperless ../P5/var/zope-debug/edrn.json ../P5/var/blobstorage
# ./manage.sh translatetables
# ./manage.sh rewritereferencesets
# ./manage.sh installdataqualityreports
# ./manage.sh rebuild_references_index
