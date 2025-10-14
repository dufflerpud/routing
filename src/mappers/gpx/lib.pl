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
package main;

my $DRIVER={};
$DRIVER->{name} = "GPX format";
$DRIVER->{minmaps} = 1;
$DRIVER->{maxmaps} = 100;

our @MAPCOLORS;

#########################################################################
#########################################################################
#$DRIVER->{expected} = sub
#    {
#    my( $title, $input_p ) = @_;
#    return &cpi_template::template(
#        $DRIVER->{template},
#        "%%CREATOR%%", ?
#        "%%ACTUAL_DATA%%", ? );
#    };

my @GPX_COLORS;
#########################################################################
#	Return trkpt string from progress GPS list.			#
#########################################################################
$DRIVER->{progress_to_trkpts} = sub
    {
    my( $title, $input_p ) = @_;
    my @ret;

    @GPX_COLORS = &colors_by("Name") if( ! @GPX_COLORS );

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
$DRIVER->{stops_to_waypoints} = sub
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
$DRIVER->{progress} = sub
    {
    my( $title, @input_ps ) = @_;

    my @pieces;
    foreach my $input_p ( @input_ps )
        {
	push( @pieces,
	    &indent(__LINE__,
	    &{$DRIVER->{progress_to_trkpts}}( $input_p->{title}, $input_p ),
	    &{$DRIVER->{stops_to_waypoints}}( $input_p->{title}, $input_p ) ) );
	}

    return &cpi_template::template(
	$DRIVER->{template},
	"%%CREATOR%%", ucfirst( $cpi_vars::PROG ),
	"%%ACTUAL_DATA%%", join("",@pieces) );
    };

1;
