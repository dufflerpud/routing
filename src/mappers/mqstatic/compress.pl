#!/usr/bin/perl -w
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

my $PRECISION = 5;

#########################################################################
# Stolen directly (though re-indented) from				#
# https://developer.mapquest.com/documentation/common/encode-decode/	#
#########################################################################
sub decompress
    {
    my($precision,$encoded_str) = @_;
    my @encoded = split(//,$encoded_str);
    my $precision_divider = 10.00 ** $precision;
    my @decoded;
    my $latlong_ind = 0;	#0=Latitude 1=Longitude
    my @latlong = (0,0);
    my $len = scalar(@encoded);
    for( my $index=0; $index<$len; $latlong_ind=1-$latlong_ind )
	{
	my $b;
	my $vshift = 0;
	my $result = 0;
	do  {
	    $b = ord($encoded[$index++]) - 63;
	    $result |= ($b & 0x1f) << $vshift;
	    $vshift += 5;
	    } while ($b >= 0x20);
	$latlong[$latlong_ind] += ( ($result & 1) ? -($result>>1)-1 : ($result>>1));
	push( @decoded, $latlong[$latlong_ind] / $precision_divider );
	}
    return @decoded;
    }

#########################################################################
#	Compress a series of points into a string.			#
#########################################################################
sub compress
    {
    my($precision,@points) = @_;
    my $precision_multiplier = 10 ** $precision;
    my @encoded;
    my $latlong_ind = 0;
    my @last_latlong = ( 0, 0 );
    foreach my $point ( @points )
	{
	## Round to N decimal places
	my $latlong = int( $point * $precision_multiplier );

	## Encode the differences between the points
	push( @encoded, &encodeNumber($latlong - $last_latlong[$latlong_ind]) );

	## Update our concept of last latitude or longitude
	$last_latlong[$latlong_ind] = $latlong;
	$latlong_ind = 1 - $latlong_ind;
	}
    return join("",@encoded);
    }

#########################################################################
#	Return a string that is an encoded version of the number.	#
#########################################################################
sub encodeNumber
    {
    my($num) = @_;
    #$num = $num << 1;
    $num *= 2;
    $num = ~($num) if ($num < 0);
    my @encoded;
    while ($num >= 0x20)
	{
	push( @encoded, chr( (0x20 | ($num & 0x1f)) + 63 ) );
	$num >>= 5;
	#$num = int( $num / 0x20 );
	}
    push( @encoded, chr($num+63) );
    return join("",@encoded);
    }

my $s = &compress
	(
	$PRECISION,
	45.967, -83.928700032549,
	55, -83.928420000,
	35, -83.97948699748273,
	25.000000, -83.000000,
	15.00000000000, -83.9279400000,
	0.9600, -83.9275623435,
	35.90, -0.90,
	35.900, -83.00,
	35.000, -83.000,
	35.90000, -83.0000,
	35.00000, -83.00000,
	35.000004190, -83.00000123490,
	);
my @points = &decompress( $PRECISION, $s );
print $s, " =>\n[", join(",",@points), "]\n";
