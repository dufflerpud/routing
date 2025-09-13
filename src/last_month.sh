#!/bin/sh
#
PROG=`basename $0 .sh`
PROJECT=routing
PROJECT_DIR=/usr/local/projects/$PROJECT
REPORTS_LIST=$PROJECT_DIR/monthly_reports
LOGDIR=/var/log/$PROJECT/$PROJECT
DISTUSER_TO_PDF=$PROJECT_DIR/bin/distuser_to_pdf
LAST_MONTH=`date --date='last month' +%Y-%m`

echodo()
    {
    echo "+ $@"
    "$@"
    }

while read distributor driver dest_user ; do
    echodo $DISTUSER_TO_PDF	\
	-m $LAST_MONTH		\
	-u $driver		\
	-d $distributor		\
	-o $dest_user
done < $REPORTS_LIST
