#!/usr/local/bin/perl -w
use strict;

package main;
use lib "/usr/local/lib/perl";
use cpi_drivers qw( get_drivers device_debug get_driver );

my $driverp = &get_driver(__FILE__);

$driverp->{name} = "Apple route format";

#########################################################################
#	Generate a URL to Apple maps from a route.			#
#########################################################################
$driverp->{route_to_url} = sub
    {
    my( $map_start, $map_end, @loc_list ) = @_;
    my @res = ( "https://beta.maps.Apple.com/?dirflg=d" );
    push( @res, "&saddr=", $map_start ) if( $map_start );
    push( @res, ( map { "&daddr=$_" } @loc_list, $map_end ) );
    return join("",@res);
    };

#########################################################################
#	Return the javascript with any substitutions.			#
#########################################################################
$driverp->{js} = sub
    {
    my( $dist ) = @_;
    return &cpi_template::template( $driverp->{dir}."/lib.js" );
    };

1;
