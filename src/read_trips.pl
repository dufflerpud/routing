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

use lib "/usr/local/lib/perl";
#package main;
use COMMON;
&COMMON::setup();

use strict;

# Put constants here

my $PROJECT		= "routing";
my $CLIENT		= "Consumers";
$COMMON::PROG		= ( $_ = $0, s+.*/++, $_ );
$COMMON::BASEDIR	= "/usr/local/projects/$PROJECT";

my $EMBED_IMAGES	= "$COMMON::BASEDIR/bin/embed_images";
my $CONVERT		= "/usr/local/bin/nene";
my $WKHTMLTOPDFBIN	= "/usr/local/bin/wkhtmltopdf";
my $WKHTMLTOPDFCMD	= "$WKHTMLTOPDFBIN --log-level none";
#my $WKHTMLTOPDFCMD	= $WKHTMLTOPDFBIN;
#my $STANDARD_ROUTES	= "lib/standard_routes";
my $TO_MOW		= "Unknown";

my %EXTMAP		= ( "pdf"=>"o", "trips"=>"i", "htm"=>"h", "html"=>"h" );
my $generated_date	= `date +%m/%d/%Y`; chomp($generated_date);
my $TABLE_ARGS		= <<EOF;
    style='border-collapse:collapse;border-style:solid;display:table-inline;margin:0'
    width=100% cellspacing=2 cellpadding=2
EOF

my %ONLY_ONE_DEFAULTS =
    (
    "r"	=>	"",
    "i"	=>	"/dev/stdin",
    "h"	=>	"$COMMON::BASEDIR/public_html/mow.html",
    "o"	=>	"/dev/stdout",
    "d"	=>	"MOW",
    "u"	=>	"Unknown driver",	# Unused
    "a" =>	"0.00",
    "f"	=>	"",
    "V" =>	0.05,		# 5%
    "v"	=>	""
    );

# Put variables here.

my @problems;
my %ARGS;
my @files;
#my %standard_routes;

# Put interesting subroutines here

#########################################################################
#	Print usage message and die.					#
#########################################################################
sub usage
    {
    &COMMON::fatal( join("\n", @_, "",
	"Usage:  $COMMON::PROG <possible arguments>","",
	"where <possible arguments> is:",
	"    -i <trip file>",
	"    -d <Distributor>",
	"    -u <Driver>",
	"    -h <HTML file to generate>",
	"    -o <PDF made from HTML file>",
	"    -t <template containing look and feel>",
	"    -r <rate_string>"
	), 0 );
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
	elsif( $arg =~ /^-(t)(.*)$/ )
	    {
	    my $val = ( $2 ? $2 : shift(@ARGV) );
	    if( $#files <= 0 )
	        {
		if( defined($files[$#files]->{$1}) )
		    {
		    push( @problems,
			$files[$#files]->{name} .
			    " -$1 specified multiple times." );
		    }
		else
		    { $files[$#files]->{$1} = $val; }
		}
	    elsif( defined( $ARGS{$1} ) )
		{ push( @problems, "-$1 specified multiple times." ); }
	    else
		{ $ARGS{$1} = $val; }
	    }
	elsif( $arg =~ /^-.*/ )
	    { push( @problems, "Unknown argument 1 [$arg]" ); }
	elsif( $arg =~ /.*\.([a-z]+)$/ && defined($EXTMAP{$1}) )
	    {
	    if( $ARGS{$EXTMAP{$1}} )
	        { push(@problems,
		    "-$EXTMAP{$1} already specified multiple times." ); }
	    else
	        { $ARGS{$EXTMAP{$1}} = $arg; }
	    }
	else
	    #{ push( @files, { name=>$arg, title=>&file_to_name($arg) } ); }
	    { push(@problems,"Unknown argument 2 [$arg]."); }
	}

    #push( @problems, "No files specified" ) if( ! @files );
    &usage( @problems ) if( @problems );

    # Put interesting code here.

    grep( $ARGS{$_}=(defined($ARGS{$_})?$ARGS{$_}:$ONLY_ONE_DEFAULTS{$_}),
	keys %ONLY_ONE_DEFAULTS );
    }

#########################################################################
#	Make sure comma separated list is always in same order.		#
#########################################################################
sub standardize_route
    {
    my( $ratestr ) = @_;
    return join(", ", sort split(/, */,$_[0]) );
    }

#########################################################################
#	Return the database index of something with the supplied name.	#
#	Third argument is a flag with what to return if failed.	#
#	Undefined causes fatal error.					#
#########################################################################
sub map_name_to_ind
    {
    my( $table, $name, $retval ) = @_;
    foreach my $ind ( &COMMON::dbget($COMMON::DB,$table) )	# Who doesn't like a nice linear search?
	{
	my $checkname = &COMMON::dbget($COMMON::DB, $ind, "Name" );

	return $ind
	    if( $checkname eq $name
	     || &COMMON::text_to_filename($checkname) eq $name );
	}
    return $retval if( defined($retval) );
    &fatal("Cannot map $name to an index in the $table table.");
    }


#########################################################################
#	Filter the data							#
#########################################################################
sub filter
    {
#    open( INF, $STANDARD_ROUTES ) || &COMMON::fatal("Cannot read ${STANDARD_ROUTES}:  $!");
#    while( $_ = <INF> )
#        {
#	chomp( $_ );
#	my( $dist, $routestr ) = split(/\t+/);
#	$standard_routes{ &standardize_route( $routestr ) } = $dist;
#	}
#    close( INF );
#
##    foreach $_ ( sort keys %standard_routes )
##	{ print "Dist=$standard_routes{$_} [$_]\n"; }

    my %total_elapsed_per_category;
    my %total_distance_per_category;
    my %total_cost_per_category;
    my $total_elapsed = 0;
    my $total_distance = 0;
    my $total_cost = 0;
    my %rates;
    my $donation_percentage = 0;
    my $donation_maximum;
    if( ! $ARGS{r} || $ARGS{r} !~ /\d/ )
	{
	&COMMON::dbread( $COMMON::DB ) || &COMMON::fatal("Cannot opendb($COMMON::DB):  $!");
	my $distributor_ind = &map_name_to_ind( "Distributor", $ARGS{d} );
	my $staff_ind = &map_name_to_ind( "Staff", $ARGS{u} );
	$ARGS{r} =
	    &COMMON::dbget( $COMMON::DB, $distributor_ind, "Reimbursement" );
	$donation_percentage =
	    &COMMON::dbget( $COMMON::DB, $staff_ind, "Donation_percentage" )
	    || 0;
	$donation_maximum =
	    &COMMON::dbget( $COMMON::DB, $staff_ind, "Donation_maximum" )
	    || 0;
	&COMMON::dbclose( $COMMON::DB );
	}

    open( INF, "$COMMON::BASEDIR/Distributors/$ARGS{d}/invoice.pl" )
	|| &COMMON::fatal("Cannot read $COMMON::BASEDIR/Distributors/$ARGS{d}/invoice.pl:  $!");
    my $PAGE_CONTENTS = join("",<INF>);
    close( INF );

    open( INF, $ARGS{i} ) || &COMMON::fatal("Cannot read $ARGS{i}:  $!");

    &COMMON::fatal("Cannot write $ARGS{f}:  $!")
        if( $ARGS{f} && ! open(OUT,">$ARGS{f}") );

    foreach $_ ( split(/,/,$ARGS{r}) )
	{
	if( $_ !~ /(.*)=(.*)/ )
	    { print STDERR "Ignoring rate [$_].\n"; }
	else
	    {
	    $rates{$1}=$2;
	    $total_elapsed_per_category{$1}=$total_distance_per_category{$1}=$total_cost_per_category{$1}=0;
	    }
	}

    my @chart_data = ();
    while( $_ = <INF> )
        {
	s/[\r\n]//g;
	my ($dt,$da,$de,$diststring,$townlist) = split(/\t+/);
	my( $distance, $stype ) =
	    ( $diststring =~ /^([0-9\.]+)@([A-Za-z].+)/
	    ? ($1,$2)
	    : ($diststring,"Unknown") );
	if( $dt =~ m:(\d+)/(\d+)/(\d+): )
            { $dt = sprintf("%04d-%02d-%02d",$3,$1,$2) }
	elsif( $dt =~ m:(20\d\d)(\d\d)(\d\d): )
            { $dt = sprintf("%04d-%02d-%02d",$1,$2,$3) }
	$distance = sprintf("%.1f",$distance+$ARGS{a});
	$diststring = $distance.$stype;
	print OUT "$dt\t$da\t$diststring\t$townlist\n" if( $ARGS{f} );
	my $othercost = 0;
	print STDERR "distance=",($distance||"UNDEF"),
		" stype=",($stype||"UNDEF"),
		" rates=",($rates{$stype}||"UNDEF"), ".\n";
	my $cost = sprintf("%.2f", $distance * $rates{$stype} + $othercost );
	if( $ARGS{d} eq "MOW_Sagadahoc" )
	    { push( @chart_data,
	    "<tr><td valign=top>",			$dt,
	    "</td><td valign=top align=right>",		$de,
	    "</td><td valign=top>",			"$townlist route",
	    "</td><td valign=top align=right>",		$distance,
	    "</td><td valign=top align=right>\$",	sprintf("%.2f",$rates{$stype}),
	    "</td><td valign=top align=right>\$",	sprintf("%.2f",$cost),
	    "</td></tr>\n" ); }
	else
	    { push( @chart_data,
	    "<tr><td valign=top>",			$dt,
	    "</td><td valign=top>",			$CLIENT,
	    "</td><td valign=top>",			$townlist,
	    "</td><td valign=top align=right>",		sprintf("%.1f",0),
	    "</td><td valign=top align=right>",		$distance,
	    "</td><td valign=top align=right>",		$diststring,
	    "</td><td valign=top align=right>\$",	sprintf("%.2f",$othercost),
	    "</td><td valign=top align=right>\$",	sprintf("%.2f",$cost),
	    "</td><td>",				"&nbsp",
	    "</td></tr>\n" ); }
	my( $elapsed ) = ( $de =~ /(\d+):(\d+)/ ? $1*60+$2 : $de );
	$total_distance_per_category{$stype} += $distance;	$total_distance += $distance;
	$total_cost_per_category{$stype} += $cost;		$total_cost += $cost;
	$total_elapsed_per_category{$stype} += $elapsed;	$total_elapsed += $elapsed;
	my $lll = $total_elapsed_per_category{$stype};
	#my $lll = 123;
	}
    close( INF );
    close( OUT ) if( $ARGS{f} );

    foreach my $stype ( keys %total_distance_per_category )
	{
	next if( ! $total_distance_per_category{$stype} );
	$total_cost_per_category{$stype} = sprintf( "%.2f", $total_cost_per_category{$stype} );
	if( $ARGS{d} eq "MOW_Sagadahoc" )
	    { push( @chart_data, "<tr><th>".&COMMON::filename_to_text(${stype})." totals</th>",
		"<td align=right>",
		    sprintf("%d:%02d",$total_elapsed_per_category{$stype}/60,$total_elapsed_per_category{$stype}%60),"</td>",
		"<td></td>",
		"<td align=right><b>",
		    sprintf("%.1f",$total_distance_per_category{$stype}),
		    "</b></td>",
		"<td align=right></td>",
		"<td align=right><b>\$", $total_cost_per_category{$stype}, "</b></td>",
		"</tr>\n" ); }
	else
	    { push( @chart_data, "<tr><th>Totals</th>",
		"<td></td><td></td><td></td><td></td>",
		"<td align=right><b>",
		    sprintf("%.1f",$total_distance_per_category{$stype}), "</b></td>",
		"<td></td>",
		"<td align=right><b>\$", $total_cost_per_category{$stype}, "</b></td>",
		"<td></td></tr>\n" ); }
	}

    my $chart_data_string = join("",@chart_data);
    my $donation = $total_cost * $donation_percentage / 100;
    $donation = sprintf("%.2f",
	$donation>$donation_maximum ? $donation_maximum : $donation );
    my $net_request = sprintf("%.2f",$total_cost - $donation);
    my $page = eval( $PAGE_CONTENTS );
    #print "Error was [$@]\n";
    #print STDERR "errmessage=[$@]\n" if( $ARGS{v} );

    open( OUT, "| $EMBED_IMAGES > $ARGS{h}" )
	|| &COMMON::fatal("Cannot write $ARGS{h}:  $!");
    print OUT $page;
    close( OUT );

    #&echodo("$CONVERT $ARGS{h} $ARGS{o}");
    &echodo("$WKHTMLTOPDFCMD $ARGS{h} $ARGS{o}");
    }

#########################################################################
#	Main								#
#########################################################################

&parse_arguments();

#print join("\n\t","Args:",map{"$_:\t$ARGS{$_}"} sort keys %ARGS), "\n";

&filter();

&COMMON::cleanup(0);
