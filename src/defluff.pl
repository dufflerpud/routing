#!/usr/local/bin/perl -w
#
#indx#	defluff.pl - OBSOLETE:  Read http log files to make error messages more readable
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
#doc#	defluff.pl - OBSOLETE:  Read http log files to make error messages more readable
########################################################################
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
