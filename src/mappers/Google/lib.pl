#!/usr/local/bin/perl -w
use strict;

package main;
use lib "/usr/local/lib/perl";
use cpi_drivers qw( get_drivers device_debug get_driver );

my $driverp = &get_driver(__FILE__);

$driverp->{name}		= "Google route format";
$driverp->{which_api}	= "Old"; # Old, saddr and New all work as of 06/14/2025

#We don't use Googleapis.com (yet)
#$driverp->{KEY}		= "Your key should be in the database";
#https://maps.googleapis.com/maps/api/js?key=$driverp->{KEY}&callback=initMap

#########################################################################
#	Generate a URL to Google maps from a route.			#
#########################################################################
$driverp->{route_to_url} = sub
    {
    my( $map_start, $map_end, @loc_list ) = @_;
    my @res = ( "https://maps.Google.com/maps" );
    if( $driverp->{which_api} eq "Old" )
        {
	push( @res, "/dir" );
	push( @res, "/$map_start" ) if( $map_start );
	push( @res, map { "/$_" } ( @loc_list, $map_end ) );
	}
    elsif( $driverp->{which_api} eq "saddr" )
        {
	push( @res, "?" );
	push( @res, "saddr=$map_start&" ) if( $map_start );
	push( @res, "daddr=", join("+to:",@loc_list,$map_end) );
	}
    elsif( $driverp->{which_api} eq "New" )
	{
	push( @res, "/dir/?api=1" );
	push( @res, "&origin=", $map_start ) if( $map_start );
	push( @res,
	    "&waypoints=",
	    join("|",@loc_list),
	    "&optimizewaypointorder=false" )
	    if( scalar(@loc_list) > 0 );
	push( @res, "&destination=", $map_end );
	}
    else
        { &cpi_file::fatal("Unsupport Google API ".($driverp->{which_api}||"UNDEF")."."); }
    return join("",@res);
    };

#########################################################################
#	Return the javascript with any substitutions.			#
#########################################################################
$driverp->{js} = sub
    {
    my( $dist ) = @_;
    return &cpi_template::template( $driverp->{dir}."/lib.js",
        "%%GOOGLE_KEY%%", $driverp->{KEY} );
    };

1;
