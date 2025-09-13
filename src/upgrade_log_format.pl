#!/usr/bin/perl -w

use strict;

my $work_flag = 1;
while( $_ = <STDIN> )
    {
    chomp( $_ );
    # Thomas White: Brunswick East	2024-08-14 10:17	Normal
    if( /^([A-Z].*?):\s*(.*?)\s+(\d\d\d\d-\d\d-\d\d\s+\d\d:\d\d)\s*(.*)$/ )
        {
	print "Seen $3 by Chris Caldwell on $2 route:\t$4\n";
	$work_flag = 0;
	}
    else
        { print $_, "\n"; }
    }

exit( $work_flag );
