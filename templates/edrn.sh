#!/bin/sh
#
# EDRN init
#
# Starts and stops the supervisor for the EDRN site
#
# Note that templates/init.sh generates parts/templates/init. Are you
# editing the correct file?
#
# chkconfig: 345 88 11
# description: EDRN Site Supervisor

home="${buildout:directory}"
bin="${dollar}{home}/bin"
supervisord="${dollar}{bin}/supervisord"
supervisorctl="${dollar}{bin}/supervisorctl"

PATH=/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
export PATH
TZ=UTC
export TZ

case "${dollar}1" in
start)
        echo "Starting EDRN Supervisor"
        ${dollar}supervisord
        ;;
stop)
        echo "Stopping EDRN Supervisor"
        ${dollar}supervisorctl shutdown
        ;;
restart)
        echo "Restarting EDRN Supervisor"
        ${dollar}supervisorctl shutdown
        /bin/sleep 5
        ${dollar}supervisord
        ;;
graceful)
        echo "Restarting EDRN processes under existing Supervisor"
        ${dollar}supervisorctl restart all
        ;;
status)
        ${dollar}supervisorctl status
        ;;
*)
        echo "Usage: ${dollar}0 {start|stop|restart|graceful|status}" 1>&2
        ;;
esac
exit 0
