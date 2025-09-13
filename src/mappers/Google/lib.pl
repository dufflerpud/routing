#!/usr/local/bin/perl -w
use strict;

#our %mappers;
my $mapperp = $mappers{'%%THIS%%'};

$mapperp->{name}	= "Google route format";
$mapperp->{which_api}	= "Old"; # Old, saddr and New all work as of 06/14/2025

#We don't use Googleapis.com (yet)
$mapperp->{KEY}		= "AIzaSyBWmcffdTO2QrtWTRylCdYCSRcOVfqIabY";
#https://maps.googleapis.com/maps/api/js?key=$mapperp->{KEY}&callback=initMap

#########################################################################
#	Generate a URL to Google maps from a route.			#
#########################################################################
$mapperp->{route_to_url} = sub
    {
    my( $map_start, $map_end, @loc_list ) = @_;
    my @res = ( "https://maps.Google.com/maps" );
    if( $mapperp->{which_api} eq "Old" )
        {
	push( @res, "/dir" );
	push( @res, "/$map_start" ) if( $map_start );
	push( @res, map { "/$_" } ( @loc_list, $map_end ) );
	}
    elsif( $mapperp->{which_api} eq "saddr" )
        {
	push( @res, "?" );
	push( @res, "saddr=$map_start&" ) if( $map_start );
	push( @res, "daddr=", join("+to:",@loc_list,$map_end) );
	}
    elsif( $mapperp->{which_api} eq "New" )
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
        { &fatal("Unsupport Google API ".($mapperp->{which_api}||"UNDEF")."."); }
    return join("",@res);
    };

#########################################################################
#	Return the javascript with any substitutions.			#
#########################################################################
$mapperp->{js} = sub
    {
    my( $dist ) = @_;
    my $mapperp = $mappers{'%%THIS%%'};
    return &COMMON::template( $mapperp->{dir}."/lib.js",
        "%%GOOGLE_KEY%%", $mapperp->{KEY} );
    };

1;
