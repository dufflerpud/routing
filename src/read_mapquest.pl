#!/usr/local/bin/perl -w
#
#indx#	read_mapquest.pl - OBSOLETE - Dump results of a mapquest query
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
#doc#	read_mapquest.pl - OBSOLETE - Dump results of a mapquest query
#doc#	read_mapquest.pl - (Replace with more full explanation of what this file is or does
#doc#	spread across multiple lines)
########################################################################

use strict;
use JSON;

# Put constants here

my $PROG = ( $_ = $0, s+.*/++, s/\.[^\.]*$//, $_ );
my $TMP = "/tmp/$PROG.$$";
my $CACHEDIR = "/usr/local/projects/MOW/cache";
my %ONLY_ONE_DEFAULTS =
    (
    "i"	=>	"../cache/x.result.json",
    "o"	=>	"/dev/stdout"
    );

# Put variables here.

my @problems;
my %ARGS;
my @files;

# Put interesting subroutines here

#########################################################################
#	Print message and die.						#
#########################################################################
sub fatal
    {
    print STDERR join("\n",@_), "\n";
    exit(1);
    }

#########################################################################
#	Print usage message and die.					#
#########################################################################
sub usage
    {
    &fatal( @_, "", "Usage:  $PROG -i json_obj -o output_file" );
    }

#########################################################################
#	Parse the arguments						#
#########################################################################
sub parse_arguments
    {
    my $arg;
    while( defined($arg = shift(@ARGV) ) )
	{
	# Put better argument parsing here.

	if( $arg =~ /^-(.)(.*)$/ && defined($ONLY_ONE_DEFAULTS{$1}) )
	    {
	    if( defined($ARGS{$1}) )
		{ push( @problems, "-$1 specified multiple times." ); }
	    else
		{ $ARGS{$1} = ( $2 ne "" ? $2 : shift(@ARGV) ); }
	    }
	elsif( $arg =~ /^-.*/ )
	    { push( @problems, "Unknown argument [$arg]" ); }
	else
	    { push( @problems, "Unknown argument [$arg]" ); }
	}

    &usage( @problems ) if( @problems );

    # Put interesting code here.

    grep( $ARGS{$_}=(defined($ARGS{$_})?$ARGS{$_}:$ONLY_ONE_DEFAULTS{$_}),
	keys %ONLY_ONE_DEFAULTS );

    if( -r $ARGS{i} )
        {}
    elsif ( -r ($_="$CACHEDIR/$ARGS{i}.result.json") )
        { $ARGS{i} = $_; }
    elsif ( -r ($_="$CACHEDIR/$ARGS{i}") )
        { $ARGS{i} = $_; }
    }

#########################################################################
#	Print a command and then execute it.				#
#########################################################################
sub echodo
    {
    my( $cmd ) = @_;
    print "+ $cmd\n";
    return system( $cmd );
    }

#########################################################################
#	Read an entire file and return the contents.			#
#	If open fails and a return value is not specified, fail.	#
#########################################################################
sub read_file
    {
    my( $fname, $ret ) = @_;
    if( open(INF,$fname) )
        {
	$ret = do { local $/; <INF> };
	close( INF );
	}
    elsif( scalar(@_) < 2 )
        { &fatal("Cannot open ${fname}:  $!"); }
    return $ret;
    }

#########################################################################
#	Read an entire file and return the contents.			#
#########################################################################
sub write_file
    {
    my( $fname, @contents ) = @_;
    open( OUT, "> $fname" ) || &fatal("Cannot write ${fname}:  $!");
    print OUT @contents;
    close( OUT );
    }

#########################################################################
#	Handle undefined with sprintf.					#
#########################################################################
sub msprintf
    {
    my( $fld, $val ) = @_;
    if( defined($val) )
        { return sprintf( $fld, $val ); }
    elsif( $fld =~ /^%(.*)\.(.*)[a-zA-Z]$/ || $fld =~ /^%(.*)[a-zA-Z]$/ )
        { return sprintf( "%$1.$1s", "Undefined" ); }
    else
        { return "Undefined"; }
    }

#########################################################################
#	Return select fields in a printable format.			#
#	Deliberately vague.  Sue me.					#
#########################################################################
sub write_select_fields
    {
    my( $refp, $fname ) = @_;
    open( OUT, ">$fname" ) || &fatal("Cannot write ${fname}:  $!");

    printf OUT ( "%3s %-30s %-25s %9s %8s\n",
        "i", "Street", "Town", "Distance", "Time" );
    my @sequence = @{$refp->{route}{locationSequence}};
    my $miles_so_far = 0;
    my $time_so_far = 0;
    for( my $i=0; $i<scalar(@sequence); $i++ )
        {
	my $s = $sequence[$i];
	#my $locp = $refp->{route}{locations}[$s];
	my $locp = $refp->{route}{locations}[$i];
	my $legp = $refp->{route}{legs}[$i];
	print OUT join(" ",
	    &msprintf( "%3d",		$i			),
	    &msprintf( "%-30.30s",	$locp->{street}		),
	    &msprintf( "%-25.25s",	$locp->{adminArea5}	),
	    &msprintf( "%9.4f",		$legp->{distance}	),
	    &msprintf( "%8s",		$legp->{formattedTime}	) ),
	    "\n";
	$miles_so_far += ( $legp->{distance} || 0 );
	$time_so_far += ( $legp->{time} || 0 );
	}
    printf OUT ("%-60s %9.4f %02d:%02d:%02d\n",
	" ", $miles_so_far,
	$time_so_far/3600, ($time_so_far/60)%60, $time_so_far%60 );
    close( OUT );
    }

#########################################################################
#	Main								#
#########################################################################

&parse_arguments();

&write_select_fields( decode_json( &read_file( $ARGS{i} ) ), $ARGS{o} );

exit(0);
