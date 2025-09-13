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
