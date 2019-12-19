#!/bin/sh
#
# Sync my database to JPL

if [ ! -d "var/blobstorage" -o ! -d "var/filestorage" ]; then
    echo "Run this from the right directory; there should be var/blobstorage, var/filestorage" 1>&2
    exit 1
fi

/usr/bin/rsync \
    --checksum \
    --recursive \
    --relative \
    --sparse \
    --delete \
    --force \
    --prune-empty-dirs \
    --stats \
    --human-readable \
    --progress \
    var/blobstorage \
    var/filestorage \
    edrn-labcas:
