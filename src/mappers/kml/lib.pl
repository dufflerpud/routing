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

package main;
use lib "/usr/local/lib/perl";
use cpi_drivers qw( get_drivers device_debug get_driver );

my $driverp = &get_driver(__FILE__);

$driverp->{name} = "Google KML format";
$driverp->{minmaps} = 1;
$driverp->{maxmaps} = 100;

#########################################################################
#	Generate a bunch of styles with color definitions.		#
#########################################################################
$driverp->{generate_colors} = sub
    {
    my @AABBGGRR = &main::colors_by("AABBGGRR");
    my @PADDLES = &main::colors_by("Paddle");
    #my @COLOR_NAMES = &main::colors_by("Name");
    return join("",
        #( map {"<Style id='line_$_'><LineStyle><color>$AABBGGRR[$_]</color><width>4</width></LineStyle></Style><Style id='mark_$_'><IconStyle><Icon><href>http://routing.brightsands.com/sto/icons/kml/$COLOR_NAMES[$_]-paddle.png</href></Icon></IconStyle></Style>\n"} 0 .. $#COLOR_NAMES ) );
        ( map {"<Style id='line_$_'><LineStyle><color>$AABBGGRR[$_]</color><width>4</width></LineStyle></Style><Style id='mark_$_'><IconStyle><Icon><href>http://maps.google.com/mapfiles/kml/paddle/$PADDLES[$_]-circle.png</href></Icon></IconStyle></Style>\n"} 0 .. $#PADDLES ) );
    };

#########################################################################
#	Return trkpt string from progress GPS list.			#
#########################################################################
$driverp->{progress_to_tracks} = sub
    {
    my( $title, $input_p ) = @_;
    my @res;
    foreach my $latlng_p ( $input_p->{progress_p}, $input_p->{expected_p} )
	{
	push( @res, &{$driverp->{tracks}}(
	    $title,
	    ( defined($input_p->{color})
		? $input_p->{color}
		: $input_p->{done}
		? 0
		: 1 ),
	    @{$input_p->{progress_p}} ) )
		if( $latlng_p );
	}
    return @res;
    };

#########################################################################
#	Add the stops to the event_list as waypoints			#
#########################################################################
$driverp->{stops_to_waypoints} = sub
    {
    my( $title, $input_p )			= @_;
    my($sec,$min,$hour,$mday,$month,$year)	= localtime($main::now);
    my $stops					= $input_p->{stops};
    my $display_order				= $input_p->{display_order};
    my @ret;

    foreach my $stop
	( $display_order
	    ? (map { $stops->[$_] } @{$display_order} )
	    : @{$stops} )
	{
	if( $stop->{coords} )
	    {
	    if ( $stop->{when} && $stop->{when} =~ /(\d+):(\d+)/ )
		{ $hour=$1; $min=$2; }
	    my( $ind, @others ) = split( /,/, $stop->{patrons} );
	    $stop->{ind} = $ind;
	    if( defined( $input_p->{color} ) )
		{ $stop->{color} = $input_p->{color}; }
	    elsif( $stop->{done} )
		{ $stop->{color} = 0; }
	    else
		{ $stop->{color} = 1; }
	    $stop->{time} ||= timelocal(0,$min,$hour,$mday,$month,$year);
	    push( @ret, &{$driverp->{stop}}($stop));
	    }
	}

    return join("",
	"<Folder>\n",
	&indent(__LINE__,
   	    "<name>Waypoints for $title</name>\n",
   	    "<description>A list of waypoints for $title</description>\n",
   	    "<visibility>1</visibility>",
   	    "<open>0</open>\n",
	    @ret),
	"</Folder>\n");
    };

#########################################################################
#	Return a kml file from the GPS list and the various stops.	#
#########################################################################
$driverp->{progress} = sub
    {
    my( $title, @input_ps ) = @_;

    my @pieces;
    foreach my $input_p ( @input_ps )
        {
	push( @pieces,
	    &indent(__LINE__,
		&indent(__LINE__,&{$driverp->{progress_to_tracks}}($input_p->{title},$input_p)),
		&indent(__LINE__,&{$driverp->{stops_to_waypoints}}($input_p->{title},$input_p)))
	    )
	}

    return &cpi_template::template( $driverp->{template},
	"%%TITLE%%", $title,
	"%%COLORS%%", &{$driverp->{generate_colors}}(),
	"%%ACTUAL_DATA%%", join("",@pieces )
	);
    };

#########################################################################
#	Returns kmleese text for a stop but takes times, stati & note.	#
#########################################################################
$driverp->{stop} = sub
    {
    my( $stop_argp )	= @_;
    my $ind			= $stop_argp->{ind};
    my $markcolor		= $stop_argp->{color};
    my $global_time_str		= &cpi_time::time_string( $main::GLOBAL_TIME_FMT, $stop_argp->{time} );
    my( $lat, $lon )		= split(/,/, ($stop_argp->{coords}||&DBget($ind,"Coords")||"UNDEF") );
    return join("",
       "<Placemark>\n",
	&indent(__LINE__,
	    "<name>",($stop_argp->{name}||&DBget($ind,"Name")||"UNDEF"),"</name>\n",
	   "<styleUrl>#mark_$markcolor</styleUrl>\n",
	    "<visibility>1</visibility><open>0</open>\n",
	    "<TimeStamp><when>$global_time_str</when></TimeStamp>\n",
	    "<description>",
	    &indent(__LINE__,
		($stop_argp->{address}||&DBget($ind,"Address")||"No address"), "\n",
		($stop_argp->{phone}||&DBget($ind,"Phone")||"No Phone"), "\n",
		($stop_argp->{status}||"No Status"), "\n",
		($stop_argp->{note}||"No Note"), "\n"
	    ),
	    "</description>\n",
	    "<LookAt>\n",
	    &indent(__LINE__,
		"<longitude>$lon</longitude>\n",
		"<latitude>$lat</latitude>\n",
		"<range>500</range><tilt>45</tilt><heading>0</heading>"
		),
	    "</LookAt>\n",
	    "<Point><coordinates>$lon,$lat</coordinates></Point>"),
	"</Placemark>\n",
	);
    };

#########################################################################
#########################################################################
$driverp->{tracks} = sub
    {
    my( $title, $linecolor, @coordlist ) = @_;
    return
	(
	"<Folder>\n",
	 &indent(__LINE__,
	  "<name>Tracks for $title</name>\n",
	  "<description>A list of tracks for $title</description>\n",
	  "<visibility>1</visibility><open>0</open>\n",
	  "<Placemark>\n",
	  &indent(__LINE__,
	   "<visibility>0</visibility><open>0</open>\n",
	   "<styleUrl>#line_$linecolor</styleUrl>\n",
	   "<name>The only track for $title</name>\n",
	   "<description>The only track for $title</description>\n",
	   "<LineString>",
	   &indent(__LINE__,
	    "<extrude>true</extrude>\n",
	    "<tessellate>true</tessellate>\n",
	    "<altitudeMode>clampToGround</altitudeMode>\n",
	    "<coordinates>\n",
	    &indent(__LINE__,
	     join(" ",map{("$_->{lng},$_->{lat}")}@coordlist)),
	    "</coordinates>\n"),
	   "</LineString>\n"),
	  "</Placemark>\n"),
	"</Folder>\n"
	);
    };

##########################################################################
##	Creates a KML pieces for each waypoint in expected route.	#
##########################################################################
#$driverp->{waypoints_from_expected} = sub
#    {
#    my( $title, $route_ind, @patron_order ) = @_;
#    my @ret;
#    #debugout(__LINE__,"Waypoints_from_expected($route_ind) starting...");
#    foreach my $ind ( @patron_order )
#	{
#	push( @ret, &{$driverp->{stop}}({
#	    ind		=>	$ind,
#	    time	=>	time(),
#	    status	=>	(&DBget($ind,"Status")||"No Status"),
#	    note	=>	(&DBget($ind,"Last_note")||"")
#	    }) );
#	}
#    #debugout(__LINE__,"Waypoints_from_expected($route_ind) middle...");
#    my $foo = join("",
#	"<Folder>\n",
#	&indent(__LINE__,
#   	    "<name>Waypoints for $title</name>\n",
#   	    "<description>A list of waypoints for $title</description>\n",
#   	    "<visibility>1</visibility>",
#   	    "<open>0</open>\n",
#	    @ret),
#	"</Folder>\n");
#    #debugout(__LINE__,"Waypoints_from_expected($route_ind) ending...");
#    return $foo;
#    };
#
##########################################################################
##	Creates a KML file for the route specified.  Not necessarily	#
##	route driver actually took, but something to compare against.	#
##########################################################################
#$driverp->{expected} = sub
#    {
#    my( $route_ind,
#	$distributor_ind,
#	$distributor_name,
#	$route_name,
#	$title,
#	@order ) = @_;
#
#    &setup_file( ">" .
#	join("/",
#	    $EXPECTED_DIR,
#	    &cpi_filename::text_to_filename($distributor_name),
#	    &cpi_filename::text_to_filename($route_name).".".$driverp->{extension} ),
#	&cpi_template::template( $driverp->{template},
#	    "%%TITLE%%", $title,
#	    "%%COLORS%%", &{$driverp->{generate_colors}}(),
#	    "%%ACTUAL_DATA%%",
#		join("",
#		    &{$driverp->{tracks}}( $title, "red", @rt_coords ),
#		    &{$driverp->{waypoints_from_expected}}( $title, $route_ind, @order)))
#	);
#    };

1;
