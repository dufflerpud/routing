#!/usr/local/bin/perl -w
#
#indx#	htmls_to_times.pl - OBSOLETE:  Get timing info from log entries
#@HDR@	$Id$
#@HDR@
#@HDR@	Copyright (c) 2024-2026 Christopher Caldwell (Christopher.M.Caldwell0@gmail.com)
#@HDR@
#@HDR@	Permission is hereby granted, free of charge, to any person
#@HDR@	obtaining a copy of this software and associated documentation
#@HDR@	files (the "Software"), to deal in the Software without
#@HDR@	restriction, including without limitation the rights to use,
#@HDR@	copy, modify, merge, publish, distribute, sublicense, and/or
#@HDR@	sell copies of the Software, and to permit persons to whom
#@HDR@	the Software is furnished to do so, subject to the following
#@HDR@	conditions:
#@HDR@	
#@HDR@	The above copyright notice and this permission notice shall be
#@HDR@	included in all copies or substantial portions of the Software.
#@HDR@	
#@HDR@	THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY
#@HDR@	KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE
#@HDR@	WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE
#@HDR@	AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT
#@HDR@	HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY,
#@HDR@	WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
#@HDR@	FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR
#@HDR@	OTHER DEALINGS IN THE SOFTWARE.
#
#hist#	2026-02-10 - Christopher.M.Caldwell0@gmail.com - Created
########################################################################
#doc#	htmls_to_times.pl - OBSOLETE:  Get timing info from log entries
########################################################################

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
