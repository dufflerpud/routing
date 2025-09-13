#!/usr/local/bin/perl -w
use strict;

#our %mappers;
my $mapperp = $mappers{'%%THIS%%'};
$mapperp->{name} = "Apple route format";

#########################################################################
#	Generate a URL to Apple maps from a route.			#
#########################################################################
$mapperp->{route_to_url} = sub
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
$mapperp->{js} = sub
    {
    my( $dist ) = @_;
    my $mapperp = $mappers{'%%THIS%%'};
    return &COMMON::template( $mapperp->{dir}."/lib.js" );
    };

1;
