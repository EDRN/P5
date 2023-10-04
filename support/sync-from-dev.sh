#!/bin/sh
#
# Sync NCI Operations
# ===================
#
# This syncs the P5 database from JPL dev host "tumor" to the local directory.
#

WORKSPACE=${WORKSPACE:-${PWD:-`pwd`}}


# Here We Go
# ----------

echo "ℹ️ Syncing P5 database and blobs to «${WORKSPACE}»" 1>&2

media=${WORKSPACE}/media
source=tumor.jpl.nasa.gov:/usr/local/edrn/portal/ops-nci


# PostgreSQL Database
# -------------------
#
# We always assume this thing is changing and frequently, so we delete our
# local copy and get a fresh one every time.

echo "📈 Retrieving database" 1>&2
rm -f "edrn.sql.bz2"
scp -p $source/edrn.sql.bz2 ${WORKSPACE}

if [ \! -f "edrn.sql.bz2" ]; then
    echo "Failed to get $source/edrn.sql.bz2" 1>&2
    exit 1
fi


# Media Blobs
# -----------
#
# There are 7+ gigabytes worth of blobs and they hardly change, so we
# definitely take advantage of the timestamping and mirroring features of
# ``rsync`` in order to speed things up on subsequent runs.

echo "📀 Retrieving blobs" 1>&2
[ -d "$media" ] || mkdir -p "$media"
rsync --checksum --no-motd --recursive --delete --progress $source/media ${WORKSPACE}

echo "😌 All done" 1>&2
exit 0
