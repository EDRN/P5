#!/bin/sh
#
# Sync NCI Operations
# ===================
#
# This syncs the P5 database from NCI operations to the local directory.
#
# It expects the NIH_PASSWORD environment variable set to the password allowed
# access to the NCI operations database over HTTP.
#
# Set Up
# ------
#
# Get our environment and check things before we go.

# Inherit settings from environment
NIH_USERNAME=${NIH_USERNAME:-kellysc}
NIH_PASSWORD=${NIH_PASSWORD:-}
WORKSPACE=${WORKSPACE:-/usr/local/edrn/portal/ops-nci}

# Check the password
if [ \! -n "$NIH_PASSWORD" ]; then
    echo "❌ The NIH_PASSWORD environment must be set" 1>&2
    exit 1
fi

echo "The username I'm using is $(echo $NIH_USERNAME | tr 'A-Za-z' 'N-ZA-Mn-za-m')" 1>&2
echo "The password is $(echo $NIH_PASSWORD | tr 'A-Za-z' 'N-ZA-Mn-za-m')" 1>&2

# Here We Go
# ----------

echo "ℹ️ Syncing with username «${NIH_USERNAME}» to «${WORKSPACE}» in local directory" 1>&2

db=${WORKSPACE}/db
media=${WORKSPACE}/media
source=https://edrn.cancer.gov/database-access


# PostgreSQL Database
# -------------------
#
# We always assume this thing is changing and frequently, so we delete our
# local copy and get a fresh one every time.

echo "📈 Retrieving database" 1>&2
database_name="edrn-$(date -u '+%Y-%m-%d').sql.bz2"
database="${db}/${database_name}"
[ -d "$db" ] || mkdir --parents "$db"
wget \
    --quiet \
    --execute robots=off \
    --no-check-certificate \
    --output-document="$database" \
    --user="$NIH_USERNAME" \
    --password="$NIH_PASSWORD" \
    "$source/edrn.sql.bz2"
if [ \! -f "$database" ]; then
    echo "Failed to get $source/edrn.sql.bz2" 1>&2
    exit 1
fi
rm --force "${db}/edrn.sql.bz2"
ln --symbolic "$database_name" "${db}/edrn.sql.bz2"
find "$db" \
    -type f \
    -name 'edrn-[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9].sql.bz2' \
    -mtime +20 \
    -delete

# Media Blobs
# -----------
#
# There are 7+ gigabytes worth of blobs and they hardly change, so we
# definitely take advantage of the timestamping and mirroring features of
# ``wget`` in order to speed things up on subsequent runs.

echo "📀 Retrieving blobs" 1>&2
[ -d "$media" ] || mkdir -p "$media"
for media_type in documents images original_images; do
    [ -d "$media/$media_type" ] || mkdir -p "$media/$media_type"
    cd "$media/$media_type"
    wget \
        --quiet \
        --execute robots=off \
        --cut-dirs=2 \
        --reject='index.html*' \
        --no-host-directories \
        --mirror \
        --no-parent \
        --relative \
        --timestamping \
        --no-check-certificate \
        --recursive \
        --user="$NIH_USERNAME" \
        --password="$NIH_PASSWORD" \
        "$source/$media_type/"
done

echo "😌 All done" 1>&2
exit 0
