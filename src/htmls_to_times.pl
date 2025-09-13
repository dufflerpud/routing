#!/usr/local/bin/perl -w
#@HDR@	$Id$
#@HDR@		Copyright 2024 by
#@HDR@		Christopher Caldwell/Brightsands
#@HDR@		P.O. Box 401, Bailey Island, ME 04003
#@HDR@		All Rights Reserved
#@HDR@
#@HDR@	This software comprises unpublished confidential information
#@HDR@	of Brightsands and may not be used, copied or made available
#@HDR@	to anyone, except in accordance with the license under which
#@HDR@	it is furnished.

use strict;

my $INDIR = "/var/log/routing/trip_htmls/MOW_Sagadahoc/Chris_Caldwell";
my $OUTDIR = "/var/log/routing/trips/MOW_Sagadahoc/Chris_Caldwell";

opendir( D, $INDIR ) || die("Cannot opendir($INDIR):  $!");
foreach my $fn ( grep( /.html/, readdir(D) ) )
    {
    my @times;
    my $ifn = "$INDIR/$fn";
    open( INF, $ifn ) || die("Cannot open($ifn):  $!");
    while( $_ = <INF> )
	{
	push( @times, $1*60 + $2 ) if( /(\d+):(\d+)/ );
	}
    close( INF );
    if( $times[0] && $times[$#times] )
	{
	my $diff = $times[$#times] - $times[0];
        if( $fn =~ /(.*)\.html$/ )
	    {
	    my $base = $1;
	    my $ofn = "$OUTDIR/$base";
	    if( ! -e $ofn )
	    	{ print "$ofn does not exist.\n"; }
	    else
	        {
		my $diffstr = sprintf("%02d:%02d",$diff/60,$diff%60);
		print "Putting $diffstr in $ofn\n";
		open( INF, $ofn ) || die("Cannot open($ofn):  $!");
		$_ = <INF>;
		close( INF );

		s/0:00/$diffstr/;

		open( OUT, ">$ofn" ) || die("Cannot write($ofn):  $!");
		print OUT $_;
		close( OUT );
		}
	    }
	}
    }
closedir( D );
exit(0);
