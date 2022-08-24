#!/bin/sh -e
#
# This runs as user `kelly` on `cancer`. It should run *after* the `deploy.sh` job runs on the
# host `edrn-docker`, as that job will make the `static` and `media` files ready. It cannot run as
# user `edrn` though since that user is not allowed to use an ssh key to run commands on `edrn-docker`
# from `cancer`.
#
# A third job, `static-media-installation`, must then run *after* this script as user `edrn` to put
# the files in the right place. UGH.
#
# I blame the system admins for these onerous hoops.

PATH=/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin
export PATH

source=edrn-docker:/usr/local/labcas/portal/renaissance/data
target=${HOME}/Documents/Clients/JPL/Cancer/Portal/Renaissance

[ -d $target ] || mkdir -p $target

for kind in media static; do
    rsync --quiet --no-motd --checksum --recursive --inplace --times $source/$kind $target
done
