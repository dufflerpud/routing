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

use lib "/usr/local/lib/perl";
use cpi_vars;
use cpi_file qw( fatal cleanup read_file write_file read_lines );
use cpi_arguments qw( parse_arguments );
use cpi_reorder qw( orderer );
use cpi_config qw( read_map );
use cpi_filename qw( just_ext_of );
use cpi_drivers qw( get_driver );

my $driverp = &get_driver(__FILE__);

# Put constants here

$driverp->{name} = "psf - Pipe Separated Fields";

#########################################################################
#	Input a PSF database from its route sheets.			#
#########################################################################
$driverp->{importer} = sub
    {
    my( $contents, $distributor_name, $route_name ) = @_;
    return $contents;
    };

#########################################################################
#	Output a PSF database (which is how we keep things internally	#
#	so so just dump it out.						#
#########################################################################
$driverp->{exporter} = sub
    {
    my( $contents) = @_;
    print "Content-type:  text/plain\n\n", $contents;
    };
1;
