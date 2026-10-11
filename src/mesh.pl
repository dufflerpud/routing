#!/usr/local/bin/perl -w
########################################################################
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
########################################################################
#	(Replace with brief explanation of what this file is or does)
#
#	2024-04-20 - c.m.caldwell@alumni.unh.edu - Created
########################################################################

use strict;
use lib "/usr/local/lib/perl";
use cpi_file qw( fatal read_file write_file read_lines cleanup );
use cpi_arguments qw( parse_arguments );
use cpi_cgi qw( CGIreceive CGIheader );
use cpi_inlist qw( abbrev );
use cpi_vars;

use List::Util qw(min max);

# Put constants here

my $TMP		= "/tmp/$cpi_vars::PROG.$$";
#my $TMP	= "/tmp/$cpi_vars::PROG";

my $INPUT_DIR	= "/var/log/routing";
my $INPUT_BASE	= "/usr/local/projects/mesh/tests/MOW_Sagadahoc";
my $INFINITY	= 999999999999;	# If a route costs more than this we're sunk

our %ONLY_ONE_DEFAULTS =
    (
    #"input_file"	=>	"/dev/stdin",
    "output_file"	=>	"/dev/stdout",
    "staff_file"	=>	"${INPUT_BASE}_staff.txt",
    "number_staff"	=>	0,
    "distributor_file"	=>	"${INPUT_BASE}_distributor.txt",
    #"patron_file"	=>	"${INPUT_BASE}_Woolwich.txt",
    "patron_file"	=>	"${INPUT_BASE}_patrons.txt",
    "number_patrons"	=>	0,
    "costs_file"	=>	"${INPUT_BASE}_costs.tbl",
    "needs_file"	=>	"${INPUT_BASE}_needs.txt",
    "mode"		=>	{ oneof=>["route","dump","single"] },
    "output_format"	=>	{ oneof=>["human-readable","url","update","browser"] },
    "verbosity"		=>	0
    );

# Put variables here.

our @problems;
our %ARGS;
our @files;
our $exit_stat = 0;

#########################################################################
#	Setup arguments if CGI.						#
#########################################################################
sub CGI_arguments
    {
    &CGIreceive();
    }

#########################################################################
#	Print usage message and die.					#
#########################################################################
sub usage
    {
    &fatal( @_, "",
	"Usage:  $cpi_vars::PROG <possible arguments>","",
	"where <possible arguments> is:",
	"    -output_file <file>	( Output file )",
	"    -staff_file <file>		( $ONLY_ONE_DEFAULTS{s} )",
	"    -number_staff <n>		( Number of patrons to use )",
	"    -patron_file <file>	( $ONLY_ONE_DEFAULTS{p} )",
	"    -number_patrons <n>	( Number of staff to use )",
	"    -costs_file <file>		( $ONLY_ONE_DEFAULTS{c} )",
	"    -needs_file <file>		( $ONLY_ONE_DEFAULTS{needs_file} )",
	"    -mode <mode>		( one of dump, route )",
	"    -output_format <format>	( one of human-readable, url, browser or update )",
	"    -verbosity <n>		( 0=quiet or 1=verbose )"
	);
    }

#########################################################################
#	Read file into fields (stripping away blanks and comments)	#
#########################################################################
sub read_fields
    {
    my( $fname, @fields ) = @_;
    print STDERR "Reading [$fname]...\n" if( $ARGS{verbosity} );
    my( @ret );
    foreach my $ln ( &read_lines($fname) )
	{
	if( my @toks = split(/\s+/,$ln) )
	    {
	    if( ! @fields )
		{ @fields = @toks; }
	    else
		{
		my %hash = map { $_, shift(@toks) } @fields;
		push( @ret, \%hash );
		}
	    }
	}
    return @ret;
    }

#########################################################################
#	Dump the records trying to be sensible about widths.		#
#########################################################################
sub dump_table
    {
    my( @data ) = @_;
    my @fields;
    if( ref( $data[0] ) )
	{ @fields = sort keys %{ $data[0] }; }
    else
	{
        push( @fields, shift(@data) )
	    while ( ! ref( $data[0] ) );
	}

    my %lengths = map { $_, length($_) } @fields;

    foreach my $p ( @data )
	{
	foreach my $f ( @fields )
	    {
	    if( ! defined( $p->{$f} ) )
		{ $p->{$f} = "[]"; }
	    else
		{
		my $l = length( $p->{$f} );
		$lengths{$f} = $l if( $lengths{$f} < $l );
		}
	    }
	}
    foreach my $f ( @fields )
	{
	printf(
	    ( $f eq $fields[$#fields] ? "%s\n" : "%-$lengths{$f}s " ),
	    $f );
	}
    foreach my $p ( @data )
	{
	foreach my $f ( @fields )
	    {
	    printf(
	        ( $f eq $fields[$#fields] ? "%s\n" : "%-$lengths{$f}s " ),
		$p->{$f} );
	    }
	}
    }

#########################################################################
#	Read in the list of car/cars with their restrictions.		#
#	Read in the list of places to be delivered to			#
#	Read in directions from all the places.				#
#########################################################################
my $distributor_coords;
my @distributors;
my @staff;
my %staff_map;
my @staff_ids;
my @patrons;
my %costs;
my %routes_to_patrons;
my @all_patrons_coords;
sub read_problem
    {
    my( $fname ) = @_;
    @distributors	= &read_fields( $ARGS{distributor_file} );
    @staff		= &read_fields( $ARGS{staff_file} );
    @patrons		= &read_fields( $ARGS{patron_file} );

    @staff		= @staff  [ 0 .. $ARGS{number_staff}-1 ]	if( $ARGS{number_staff} );
    @patrons		= @patrons[ 0 .. $ARGS{number_patrons}-1 ]	if( $ARGS{number_patrons} );

    print STDERR "Reading [$ARGS{costs_file}]...\n" if( $ARGS{verbosity} );
    open( INF, $ARGS{costs_file} ) || &fatal("Cannot read $ARGS{costs_file}:  $!");
    my $header = <INF>;
    chomp( $header );
    my ( $noise, @coords ) = split(/\s+/,$header);
    foreach my $c0 ( @coords )
	{
	my $inline = <INF>;
	chomp( $inline );
	my( $noise, @costs_for_c0 ) = split(/\s+/,$inline);
	foreach my $c1 ( @coords )
	    { $costs{$c0,$c1} = $costs{$c1,$c0} = shift(@costs_for_c0); }
	}
    $distributor_coords = $distributors[0]->{Coords};
    foreach my $patronp ( @patrons )
	{
	push( @{ $routes_to_patrons{ $patronp->{Coords} } }, $patronp );
	}
    @all_patrons_coords = sort keys %routes_to_patrons;
    }

#########################################################################
#	Print out everything we've read in.				#
#########################################################################
sub dump_tables
    {
    &dump_table( @distributors );
    &dump_table( @staff );
    &dump_table( @patrons );
    }

#########################################################################
#########################################################################
my @current_route;
my @best_route_so_far;
my $best_cost_so_far;
sub route_recurse
    {
    my( $level, $cost_so_far, $came_from, @todo ) = @_;

    my $spc = sprintf("%*s",$level+1," ");
    print "${spc}$best_cost_so_far route_recurse(L$level,C$cost_so_far,F$came_from,",join(" ",@todo),")","\n"
	if( $ARGS{verbosity} > 1 );
    #my @ordered_todo = sort { $costs{$a,$came_from} <=> $costs{$b,$came_from} } @todo;
    #foreach my $next_stop ( @ordered_todo )
    foreach my $next_stop ( @todo )
	{
	push( @current_route, $next_stop );
	my $cost_to_next_stop = $cost_so_far + $costs{$came_from,$next_stop};
	if( $cost_to_next_stop < $best_cost_so_far )
	    {
	    if( my @rest = grep( $_ ne $next_stop, @todo ) )
		{ &route_recurse( $level+1, $cost_to_next_stop, $next_stop, @rest ); }
	    else
	        {
		my $cost_to_end = $cost_to_next_stop
		    + $costs{$next_stop,$distributor_coords};
		if( $cost_to_end < $best_cost_so_far )
		    {
		    @best_route_so_far = @current_route;
		    $best_cost_so_far = $cost_to_end;
		    print STDERR "best_cost_so_far=$best_cost_so_far.\n"
			if( $ARGS{verbosity} );
		    }
		}
	    }
	pop( @current_route );
	}
    print "${spc}end(L$level,C$cost_so_far,F$came_from,",join(" ",@todo),")","\n"
	if( $ARGS{verbosity} > 1 );
    }

#########################################################################
#	Given a list of routes, returns the cost and the best order.	#
#########################################################################
sub optimize_route
    {
    my( @stops ) = @_;

    # Globals used in recursion
    @current_route = ();
    @best_route_so_far = ();
    $best_cost_so_far = $INFINITY;
    $distributor_coords = $distributors[0]->{Coords};

    # Let her rip!
    &route_recurse( 0, 0, $distributor_coords, @stops );
    return ( $best_cost_so_far, @best_route_so_far );
    }

#########################################################################
#	Print out a route and make columns line up.			#
#########################################################################
sub print_one_route
    {
    my( @route ) = @_;
    my @fields = ( "Id", "Coords", "Address", "Name" );
    my %lengths = map { $_, length($_) } @fields;
    foreach my $coords ( @route )
        {
	my @patrons_at_stop = @{ $routes_to_patrons{$coords} };
	foreach my $patron ( @patrons_at_stop )
	    {
	    foreach my $field ( @fields )
		{
		if( ! defined( $patron->{$field} ) )
		    {
		    print "patron->{$field} undefined for $patron.\n";
		    }
		else
		    {
		    my $l = length( $patron->{$field} );
		    $lengths{$field} = $l if( $l > $lengths{$field} );
		    }
		}
	    }
	}
    foreach my $coords ( @route )
        {
        my %lastv = map { ($_,"XXX") } @fields;
	my @patrons_at_stop = @{ $routes_to_patrons{$coords} };
	foreach my $patron ( @patrons_at_stop )
	    {
	    foreach my $field ( @fields )
		{
		my $v =
		    ( ( $patron->{$field} ne $lastv{$field} ) 
		    ? $patron->{$field}
		    : "" );
		$lastv{$field} = $patron->{$field};
		if( $field eq $fields[$#fields] )
		    { printf("%s\n",$v); }
		else
		    { printf("%-$lengths{$field}s ",$v); }
		}
	    }
	}
    }

#########################################################################
#	Print a routing solution.					#
#########################################################################
sub print_routes
    {
    my( %staff_routes ) = @_;

    my @fields = ( "Id", "Coords", "Address", "Name" );
    my %lengths = map { $_, length($_) } @fields;

    foreach my $staff_ind ( keys %staff_routes )
	{
	my( $cost, @route ) = @{ $staff_routes{$staff_ind} };
	foreach my $coords ( @route )
	    {
	    my @patrons_at_stop = @{ $routes_to_patrons{$coords} };
	    foreach my $patron ( @patrons_at_stop )
		{
		foreach my $field ( @fields )
		    {
		    if( ! defined( $patron->{$field} ) )
			{
			print "patron->{$field} undefined for $patron.\n";
			}
		    else
			{
			my $l = length( $patron->{$field} );
			$lengths{$field} = $l if( $l > $lengths{$field} );
			}
		    }
		}
	    }
	}

    print " ";
    foreach my $f ( @fields )
	{
	printf(
	    ( $f eq $fields[$#fields] ? "%s\n" : "%-$lengths{$f}s " ),
	    $f );
	}

    my $ctr = 0;
    foreach my $staff_ind ( sort keys %staff_routes )
	{
	my( $cost, @route ) = @{ $staff_routes{$staff_ind} };
	print "\n" if( $ctr++ );
	print $staff_map{$staff_ind}->{Name}, " with cost ${cost}:\n";
	foreach my $coords ( @route )
	    {
	    my @patrons_at_stop = @{ $routes_to_patrons{$coords} };
	    my %lastv = map { ($_,"XXX") } @fields;
	    foreach my $patron ( @patrons_at_stop )
		{
		print " ";
		foreach my $field ( @fields )
		    {
		    my $v =
			( ( $patron->{$field} ne $lastv{$field} ) 
			? $patron->{$field}
			: "" );
		    $lastv{$field} = $patron->{$field};
		    if( $field eq $fields[$#fields] )
			{ printf("%s\n",$v); }
		    else
			{ printf("%-$lengths{$field}s ",$v); }
		    }
		}
	    }
	}
    }


#########################################################################
#	Return a string containing a Google maps URL to show the route.	#
#########################################################################
sub generate_one_url
    {
    my( @stops ) = @_;
    my @ret = ( "https://www.Google.com/maps/dir/?api=1" );
    push( @ret, "origin=$distributor_coords" );
    #push( @ret, "origin_place_id=Distributor" );
    push( @ret, "waypoints=".join("|",@stops) );
    #push( @ret, "waypoints_place_ids=..." );
    push( @ret, "destination=$distributor_coords" );
    #push( @ret, "destination_place_id=Distributor" );
    return join("&",@ret);
    }

#########################################################################
#	Loop through all patrons trying them with all staff.		#
#	Clearly not good for any real solution.				#
#########################################################################
my %coord_to_staff;
my %staff_list;
my %routes;
my $best_staff_cost;
my %best_staff_routes;
sub staff_recurse
    {
    my( @coords_to_do ) = @_;
    my $current_coord = shift( @coords_to_do );
    foreach my $s0 ( @staff_ids )
        {
	push( @{ $staff_list{$s0} }, $current_coord );
	if( @coords_to_do )
	    { &staff_recurse( @coords_to_do ); }
	else
	    {
	    my $costliest_route_cost = 0;
	    my %staff_routes;
	    foreach my $s1 ( grep( $staff_list{$_}, @staff_ids ) )
	        {
		my $route_tok = join(" ",@{$staff_list{$s1}});
		@{$routes{$route_tok}} = &optimize_route( @{$staff_list{$s1}} )
		    if( ! $routes{$route_tok} );
		@{$staff_routes{$s1}} = @{$routes{$route_tok}};
		$costliest_route_cost = $routes{$route_tok}[0]
		    if( $routes{$route_tok}[0] > $costliest_route_cost )
		}
	    if( $costliest_route_cost < $best_staff_cost )
		{
		$best_staff_cost = $costliest_route_cost;
		%best_staff_routes = ();
		print "New best route:  ${best_staff_cost}:\n" if( $ARGS{verbosity} > 1 );
	        foreach my $s1 ( grep( $staff_routes{$_}, @staff_ids ) )
		    {
		    @{$best_staff_routes{$s1}} = @{$staff_routes{$s1}};
		    print " ", $staff_map{$s1}->{Name}, " at ",
			$best_staff_routes{$s1}[0], " with ",
			scalar( @{$best_staff_routes{$s1}} ), " stops.\n"
			if( $ARGS{verbosity} > 1 );
		    }
		}
	    }
	pop( @{ $staff_list{$s0} } );
	}
    }

#########################################################################
#########################################################################
sub split_routes
    {
    my( $num_staff ) = @_;
    my ( @coordlist ) = ( $distributor_coords );
    for( my $staffind=0; $staffind < $num_staff; $staffind++ )
	{
	}
    }

#########################################################################
#	Start the recursion process across all drivers.			#
#########################################################################
sub optimize_routes
    {
    $best_staff_cost = $INFINITY;
    %staff_map = map { ( $_->{Id}, $_ ) } @staff;
    @staff_ids = map { $_->{Id} } @staff;
    &staff_recurse( @all_patrons_coords );
    return %best_staff_routes;
    }

#########################################################################
#	Find the best routes for the one driver.			#
#########################################################################
sub solve_one
    {
    #print "Solve: ", join(" ",@all_patrons_coords), ".\n";
    my $start = time();
    my( $cost, @best_route ) = &optimize_route( @all_patrons_coords );
    my $took = time() - $start;
    print STDERR "Test took $took seconds.\n" if( $ARGS{verbosity} );
    &print_one_route( @best_route );
    system("firefox '".&generate_one_url( @best_route )."'");
    }

#########################################################################
#	Print the URLs based on the routes.				#
#########################################################################
sub print_url
    {
    my ( %route_solutions ) = @_;
    my @toprint;
    foreach my $staff_ind ( sort keys %route_solutions )
	{
	my( $cost, @route ) = @{ $route_solutions{$staff_ind} };
	push( @toprint, &generate_one_url( @route ), "\n" );
	}
    &write_file( $ARGS{output_file}, @toprint );
    }

#########################################################################
#	Print the URLs based on the routes.				#
#########################################################################
sub browser_cmd
    {
    my ( %route_solutions ) = @_;
    foreach my $staff_ind ( sort keys %route_solutions )
	{
	my( $cost, @route ) = @{ $route_solutions{$staff_ind} };
	system("firefox '" . &generate_one_url( @route ) . "'");
	}
    }

#########################################################################
#	Print in format routing software needs to see the new route	#
#	definition.							#
#########################################################################
sub update
    {
    my ( %route_solutions ) = @_;
    my @toprint;
    foreach my $id ( sort keys %route_solutions )
	{
	my( $cost, @route ) = @{ $route_solutions{ $id } };
	push( @toprint, join(" ",$id,
	    ( map { map { $_->{Id} } @{$routes_to_patrons{$_}} }
		@route) ), "\n" );
	}
    &write_file( $ARGS{output_file}, @toprint );
    }

#########################################################################
#	Find the best routes for the given staff.  Magic!		#
#########################################################################
sub solve_many
    {
    my %route_solutions = &optimize_routes();

    foreach my $output_type ( split(/,/,$ARGS{output_format}) )
	{
	my $piece_output_type = &abbrev( $output_type,
	    "human-readable", "url", "browser", "update" );
	if( $piece_output_type eq "human-readable" )
	    { &print_routes( %route_solutions ); }
	elsif( $piece_output_type eq "url" )
	    { &print_url( %route_solutions ); }
	elsif( $piece_output_type eq "browser" )
	    { &browser_cmd( %route_solutions ); }
	elsif( $piece_output_type eq "update" )
	    { &update( %route_solutions ); }
	else
	    { &fatal("Don't know what to make of output type [$output_type]"); }
	}
    }

#########################################################################
#	Main								#
#########################################################################

if( 0 && $ENV{SCRIPT_NAME} )
    { &CGI_arguments(); }
else
    { &parse_arguments(); }

#print join("\n\t","$cpi_vars::PROG args:",map{"$_:\t$ARGS{$_}"} sort keys %ARGS), "\n";

&read_problem();

my $mode = &abbrev($ARGS{mode},"dump","route","single");
if   ( $mode eq "dump" )		{ &dump_tables(); }
elsif( $mode eq "single" )		{ &solve_one(); }
elsif( $mode eq "route" )		{ &solve_many(); }
else
    { &fatal("Unknown mode [$ARGS{mode}]"); }

system("rm -rf $TMP");
&cleanup( $exit_stat );
