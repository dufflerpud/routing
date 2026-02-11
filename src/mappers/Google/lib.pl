#!/usr/local/bin/perl -w
#
#indx#	lib.pl - Routines for using Google routing and mapping
#@HDR@	$Id$
#@HDR@
#@HDR@	Copyright (c) 2026 Christopher Caldwell (Christopher.M.Caldwell0@gmail.com)
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
#doc#	lib.pl - Routines for using Google routing and mapping
########################################################################
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
