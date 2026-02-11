#!/usr/local/bin/perl -w
#
#indx#	lib.pl - Routines for using GPX mapping
#@HDR@	$Id$
#@HDR@
#@HDR@	Copyright (c) 2024-2026 Christopher Caldwell (Christopher.M.Caldwell0@gmail.com)
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
#doc#	lib.pl - Routines for using GPX mapping
########################################################################

use strict;

package main;
use lib "/usr/local/lib/perl";
use cpi_drivers qw( get_drivers device_debug get_driver );

my $driverp = &get_driver(__FILE__);

$driverp->{name} = "GPX format";
$driverp->{minmaps} = 1;
$driverp->{maxmaps} = 100;

our @MAPCOLORS;

#########################################################################
#########################################################################
#$driverp->{expected} = sub
#    {
#    my( $title, $input_p ) = @_;
#    return &cpi_template::template(
#        $driverp->{template},
#        "%%CREATOR%%", ?
#        "%%ACTUAL_DATA%%", ? );
#    };

my @GPX_COLORS;
#########################################################################
#	Return trkpt string from progress GPS list.			#
#########################################################################
$driverp->{progress_to_trkpts} = sub
    {
    my( $title, $input_p ) = @_;
    my @ret;

    @GPX_COLORS = &main::colors_by("Name") if( ! @GPX_COLORS );

    # Add the GPS points to the event_list as trkpts
    foreach my $latlng_p ( $input_p->{progress_p}, $input_p->{expected_p} )
	{
	if( $latlng_p )
	    {
	    my @pcs;
	    foreach my $sptp ( @{$latlng_p} )
		{
		push( @pcs, &indent(__LINE__,
		    "<trkpt", " lat=\"$sptp->{lat}\"", " lon=\"$sptp->{lng}\">\n",
		    &indent(__LINE__, " <time>",
		    &cpi_time::time_string($main::GLOBAL_TIME_FMT,$sptp->{when}), "</time>"),
		    "</trkpt>"
		    ) );
		}
	    push( @ret,
		join("", "<trk><name>$title</name>",
		    "<extensions><mmp:color>",
			$GPX_COLORS[ $input_p->{color} ],
		    "</mmp:color></extensions>\n",
		    &indent(__LINE__,"<trkseg>\n",@pcs,"</trkseg>"),
		    "</trk>\n" ) );
	    }
	}
    return join("",@ret);
    };

#########################################################################
#	Add the stops to the event_list as wpts				#
#########################################################################
$driverp->{stops_to_waypoints} = sub
    {
    my( $title, $input_p ) = @_;
    my($sec,$min,$hour,$mday,$month,$year) = localtime($main::now);
    my $stops = $input_p->{stops};
    my $display_order = $input_p->{display_order};
    my @ret = ();
    foreach my $stop
	( $display_order
	    ? map { $stops->[$_] } @{$display_order}
	    : @{ $stops } )
	{
	if ( $stop->{when} && $stop->{when} =~ /(\d+):(\d+)/ )
	    { $hour=$1; $min=$2; }
	my $ind = ($stop->{patrons} || "");
	my $tbl = &rec_type( $ind );
	my $gpxtim = timelocal(0,$min,$hour,$mday,$month,$year);
	my $global_time_str = &cpi_time::time_string( $main::GLOBAL_TIME_FMT, $gpxtim );
	my ($lat,$lon) = split(/,/,$stop->{coords}||"0,0");
	push( @ret,
	    "<wpt lat=\"$lat\" lon=\"$lon\">\n",
	    &indent(__LINE__,
	        "<name>", $stop->{name}||"UNDEF", "</name>\n",
	        "<time>", $global_time_str, "</time>",
		    "<desc>\n",
		    &indent(__LINE__,
		        ( $stop->{status}
			    ?  $stop->{status} . " at $global_time_str\n"
			    : "" ),
			( $stop->{address}
			    ?  $stop->{address} . "\n"
			    : "" ),
		        ( $stop->{phone}
			    ?  $stop->{phone} . "\n"
			    : "" ),
		        ( $stop->{note}
			    ?  $stop->{note}
			    : "" ) ),
		    "</desc>\n",
	        "<url>","$main::PROG_URL?func=/Search,$tbl,$ind","</url>"),
	    "</wpt>\n"
	    );
	}
    return join("",@ret);
    };

#########################################################################
#	Return a GPX file from the GPS list and the various stops.	#
#########################################################################
$driverp->{progress} = sub
    {
    my( $title, @input_ps ) = @_;

    my @pieces;
    foreach my $input_p ( @input_ps )
        {
	push( @pieces,
	    &indent(__LINE__,
	    &{$driverp->{progress_to_trkpts}}( $input_p->{title}, $input_p ),
	    &{$driverp->{stops_to_waypoints}}( $input_p->{title}, $input_p ) ) );
	}

    return &cpi_template::template(
	$driverp->{template},
	"%%CREATOR%%", ucfirst( $cpi_vars::PROG ),
	"%%ACTUAL_DATA%%", join("",@pieces) );
    };

1;
