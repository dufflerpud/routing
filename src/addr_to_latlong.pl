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
use LWP::Simple; # from CPAN
use JSON qw( decode_json ); # from CPAN

sub getLatLong()
    {
    my ($address) = @_;

    my $format = "json"; #can also to 'xml'

    my $geocodeapi = "https://maps.googleapis.com/maps/api/geocode/";

    my $url = $geocodeapi . $format . "?sensor=false&address=" . $address;

    print "URL=[$url]\n";
    my $json = get($url);

    my $d_json = decode_json( $json );

    my $lat = $d_json->{results}->[0]->{geometry}->{location}->{lat};
    my $lng = $d_json->{results}->[0]->{geometry}->{location}->{lng};

    return ($lat, $lng);
    }

my( $alat, $alng ) = &getLatLong( join(",",@ARGV) );
print "alat=$alat alng=$alng\n";
