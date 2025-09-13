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

#our %mappers;
my $mapperp = $mappers{'%%THIS%%'};
$mapperp->{name} = "Perl object";
$mapperp->{minmaps} = 1;
$mapperp->{maxmaps} = 100;

#########################################################################
#	Return a perl object the GPS list and the various stops.	#
#########################################################################
$mapperp->{progress} = sub
    {
    my( $title, @input_ps ) = @_;
    return Data::Dumper->Dump( [ \@input_ps ], [ '*routes' ] );
    #return Dumper( \@input_ps );
    };

1;
