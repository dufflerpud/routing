#!/usr/local/bin/perl -w
use strict;
package main;

my $DRIVER={};
$DRIVER->{name} = "Bing route format";

#########################################################################
#	The address format used by the Bing url.  Silly.		#
#########################################################################
sub bing_addr
    {
    my( $addr ) = @_;
    return ( ($addr=~/^([\d\.\-]+),([\d\.\-]+)$/)
	? "pos.$1_$2"
	: "adr.$addr" );
    }

#########################################################################
#	Generate a URL to Bing maps from a route.			#
#########################################################################
$DRIVER->{route_to_url} = sub
    {
    my( $map_start, $map_end, @loc_list ) = @_;
    my @res = ( "https://bing.com/maps/default.aspx?" );
    push( @res, "&rtp=", &bing_addr($map_start) ) if( $map_start );
    push( @res, ( map { "~".&bing_addr($_) } @loc_list, $map_end ) );
    return join("",@res);
    };
