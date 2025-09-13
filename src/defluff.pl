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
#
use strict;

my $INFILE = "/var/log/httpd/routing/ssl_error_log";

my $ind = 0;
my %MOMAP = map { ($_, ++$ind ) }
    split(/,/,"Jan,Feb,Mar,Apr,May,Jun,Jul,Aug,Sep,Oct,Nov,Dec");

open( INF, $INFILE ) || die("Cannot read ${INFILE}:  $!");
while ( $_ = <INF> )
    {
    chomp( $_ );
    # [Tue Dec 12 20:17:00.022634 2023] [cgi:error] [pid 30965] [client 70.16.209.218:33176] AH01215: .: /var/www/routing/sto/routing.cgi, referer: https://routing.brightsands.com/sto/routing.cgi
    if( /^\[....(...) (\d\d) (\d\d):(\d\d):(\d\d)\.(\d+) (20\d\d)\].*\] AH\d+:(.*), referer: (.*)$/ )
	{
	my( $mo, $day, $hr, $mn, $sec, $frac, $year, $msg, $refer )
	    = ($1,$2,$3,$4,$5,$6,$7,$8,$9);
	$refer =~ s+.*/++;
	my $ymd = sprintf("%04d-%02d-%02d", $year, $MOMAP{$mo}, $day );
	my $hms = sprintf("%02d:%02d:%02d", $hr, $mn, $sec );
	#printf( "%s %s.%05d (%s): %s\n", $ymd, $hms, $frac, $refer, $msg );
	printf( "%s.%05d: %s\n", $hms, $frac, $msg );
	}
    }
close( INF );
