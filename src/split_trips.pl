#!/usr/local/bin/perl -w
#
#indx#	split_trips.pl - Split trips up by user, route, month
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
#doc#	split_trips.pl - Split trips up by user, route, month
########################################################################

use strict;

use lib "/usr/local/lib/perl";

use cpi_file qw( fatal cleanup );
use cpi_arguments qw( parse_arguments );

# Put constants here

my $PROG = ( $_ = $0, s+.*/++, s/\.[^\.]*$//, $_ );
my $TMP = "/tmp/$PROG.$$";
my $DEFAULT_DISTRIBUTOR="MOW_Sagadahoc";
my $DEFAULT_USER="Chris_Caldwell";
my $BASE = "/var/log/routing/trips/$DEFAULT_DISTRIBUTOR/$DEFAULT_USER";

our %ONLY_ONE_DEFAULTS =
    (
    "input_file"	=>	"$BASE.log",
    "output_directory"	=>	$BASE,
    "verbosity"		=>	0
    );

# Put variables here.

our @problems;
our %ARGS;
our @files;
our $exit_stat = 0;

#########################################################################
#	Print usage message and die.					#
#########################################################################
sub usage
    {
    &fatal( @_, "",
	"Usage:  $PROG <possible arguments>","",
	"where <possible arguments> is:",
	"    -i <input file>",
	"    -o <output directory>"
	);
    }

#########################################################################
#	Swallow directory of individual trip files and generate		#
#	files aggreated by route and month.				#
#########################################################################
sub process_trip_files
    {
    my %entries;
    my @fnames;

    if( ! -d $ARGS{input_file} )
	{ push( @fnames, $ARGS{input_file} ); }
    else
	{
	opendir( D, $ARGS{input_file} ) || &fatal("Cannot open $ARGS{input_file}:  $!");
	push( @fnames,
	    map { "$ARGS{input_file}/$_" }
		grep( /^\d\d\d\d\d\d\d\d-.*/, readdir(D) ) );
	closedir( D );
	}

    foreach my $fn ( @fnames )
	{
	print "Reading [$fn]\n" if( $ARGS{verbosity} );
	# 20220316	Wed	0:00	26.3	Brunswick Towers
	open( INF, $fn ) || die("Cannot open ${fn}:  $!");
	while( $_ = <INF> )
	    {
	    chomp( $_ );
	    my( $when, $day, $elapsed, $mileage, $route ) = split(/\t/);

	    # By storing it this way, all but the last entry on a particular year-month-day on a
	    # particular route are ignored.  This allows the system to handle somebody writing
	    # out the their route update multiple times.
	    my $year;
	    my $month;
	    my $monthday;
	    if( $when =~ m:^(\d\d\d\d)(\d\d)(\d\d): || $when =~ m:^(\d\d\d\d)-(\d\d)-(\d\d): )
		{ $year=$1; $month=$2; $monthday=$3; }
	    elsif( $when =~ m:^(\d\d)/(\d\d)/(20\d\d): )
		{ $year=$3; $month=$1; $monthday=$2; }
	    else
		{ &fatal("Do not know how to read when=[$when]"); }
	    $entries{"$year-$month"}{$monthday}{$_} = $_;
	    }
	}

    system("mkdir -p $ARGS{output_directory}") if( ! -d $ARGS{output_directory} );

    foreach my $yearmo ( sort keys %entries )
	{
	my @days = sort keys %{$entries{$yearmo}};
	my $lastday = $days[$#days];
	my $fn = "$ARGS{output_directory}/trips/$yearmo-$lastday";
	system("mkdir -p $ARGS{output_directory}/trips") if( ! -d "$ARGS{output_directory}/trips" );
	print "Creating [$fn]\n" if( $ARGS{verbosity} );
	open( OUT, "> $fn" ) || die("Cannot write ${fn}:  $!");
	foreach my $day ( @days )
	    {
	    print OUT ( map { $entries{$yearmo}{$day}{$_}."\n" }
		sort keys %{$entries{$yearmo}{$day}} );
	    }
	close( OUT );
	}
    }

#########################################################################
#	Main								#
#########################################################################

if( 0 && $ENV{SCRIPT_NAME} )
    { &CGI_arguments(); }
else
    { &parse_arguments(); }

#print join("\n\t","Args:",map{"$_:\t$ARGS{$_}"} sort keys %ARGS), "\n";

&process_trip_files();

&cleanup($exit_stat);
