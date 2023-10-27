#!/bin/sh
#
# Build the wheels

if [ \! -d src -a \! -d docker ]; then
    echo "🧐 Not finding the src or docker directories… are you running this in the right place?" 1>&2
    exit 1
fi

echo "🧻 Erasing any existing distributions and wheels" 1>&2
if [ -d dist ]; then
    find dist -type f -delete
else
    mkdir dist
fi

for src_dir in src/*; do
    echo "🧱 Building $src_dir" 1>&2
    find $src_dir -name __pycache__ -type d -exec rm -r {} +
    docker container run --rm --volume ${PWD}:/mnt edrndocker/python-build:3.11 --outdir /mnt/dist /mnt/$src_dir
done

echo "👋 All done" 1>&2
exit 0
