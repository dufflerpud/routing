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
use JSON;

my $DRIVER={};
$DRIVER->{name} = "GeoJSON format";
$DRIVER->{minmaps} = 1;
$DRIVER->{maxmaps} = 100;
@{$DRIVER->{COLORS}} = &colors_by("rrggbb");
@{$DRIVER->{labels}} = ( 'A'..'Z', '0'-'9', 'a'-'z' );
$DRIVER->{label_ind} = 0;

#########################################################################
#	Return trkpt string from progress GPS list.			#
#########################################################################
$DRIVER->{progress_to_tracks} = sub
    {
    my( $title, $input_p ) = @_;
    my @ret;
    foreach my $latlng_p ( $input_p->{progress_p}, $input_p->{expected_p} )
	{
	push( @ret, &{$DRIVER->{tracks}}(
	    $title,
	    ( defined($input_p->{color})
		? $DRIVER->{COLORS}[$input_p->{color}]
		: $DRIVER->{COLORS}[$input_p->{done}]
		? 0
		: 1 ),
		@{$latlng_p} ) )
		if( $latlng_p );
	}
    return @ret;
    };

#########################################################################
#	Add the stops to the event_list as waypoints			#
#########################################################################
$DRIVER->{stops_to_waypoints} = sub
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
	    push( @ret, &{$DRIVER->{stop}}($stop));
	    }
	}

    return @ret;
    };

#########################################################################
#	Return a GeoJSON file from the GPS list and the various stops.	#
#########################################################################
$DRIVER->{progress} = sub
    {
    my( $title, @input_ps ) = @_;

    my $feature =
        {
	type		=>	"FeatureCollection",
	};
    foreach my $input_p ( @input_ps )
        {
	push( @{$feature->{features}},
	    &{$DRIVER->{progress_to_tracks}}($input_p->{title},$input_p),
	    &{$DRIVER->{stops_to_waypoints}}($input_p->{title},$input_p) );
	}

    #return encode_json( $feature );
    return JSON->new->pretty->encode($feature);
    };

#########################################################################
#	Returns GeoJSON-eese text for a stop but takes times,		#
#	stati & note.							#
#########################################################################
$DRIVER->{stop} = sub
    {
    my( $stop_argp )	= @_;
    my $ind			= $stop_argp->{ind};
    my $markcolor		= $DRIVER->{COLORS}[$stop_argp->{color}];
    my $global_time_str		= &cpi_time::time_string( $main::GLOBAL_TIME_FMT, $stop_argp->{time} );
    my( $lat, $lon )		= split(/,/, ($stop_argp->{coords}||&DBget($ind,"Coords")||"UNDEF") );
    return
        {
	"type"		=>	"Feature",
	"geometry"	=>
	    {
	    "type"	=>	"Point",
	    "coordinates"	=>	[ $lon-0.0, $lat-0.0 ]
	    },
	"properties"	=>
	    {
	    "icon"	=>	"bubble",
	    "marker-color"	=>	"#".$markcolor,
	    "text-color"	=>	"#".$markcolor,
#	    "label"	=>	$DRIVER->{labels}[ $DRIVER->{labelind}++ ],
#	    "Name"	=>	
#		($stop_argp->{name} || &DBget($ind,"Name") ||"No name"),
	    "label"	=>	
		($stop_argp->{name} || &DBget($ind,"Name") ||"No name"),
	    "Phone"	=>
		($stop_argp->{phone} || &DBget($ind,"Phone") ||"No phone"),
	    "Address"	=>
		($stop_argp->{address} || &DBget($ind,"Address") ||"No address"),
	    "Status"	=> ($stop_argp->{status} || "No status"),
	    "Note"	=> ($stop_argp->{note} || "No note"),
	    "Visited"	=> $global_time_str
	    }
	};
    };

#########################################################################
#	Returns a pointer to a structure suitable for encoding to JSON	#
#	showing the track somebody took.				#
#########################################################################
$DRIVER->{tracks} = sub
    {
    my( $title, $linecolor, @coordlist ) = @_;
    return
	{	"type"			=>	"Feature",
		"properties"		=>
		    {
		    "description"	=>	"Tracks for $title",
		    "stroke"		=>	"#".$DRIVER->{COLORS}[$linecolor]
		    },
		"geometry"		=>
		    {
		    "type"		=>	"LineString",
		    "coordinates"	=>
		         [ map{ [ $_->{lng}, $_->{lat} ]} @coordlist ]
		    }
	};
    };

##########################################################################
##	Creates json piece for each waypoint in expected route.		#
##########################################################################
#$DRIVER->{waypoints_from_expected} = sub
#    {
#    my( $title, $route_ind, @patron_order ) = @_;
#    my @ret;
#    #debugout(__LINE__,"Waypoints_from_expected($route_ind) starting...");
#    foreach my $ind ( @patron_order )
#	{
#	push( @ret, &{$DRIVER->{stop}}({
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
#$DRIVER->{expected} = sub
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
#	    &cpi_filename::text_to_filename($route_name).".".$DRIVER->{extension} ),
#	&cpi_template::template( $DRIVER->{template},
#	    "%%TITLE%%", $title,
#	    "%%COLORS%%", &{$DRIVER->{generate_colors}}(),
#	    "%%ACTUAL_DATA%%",
#		join("",
#		    &{$DRIVER->{tracks}}( $title, "red", @rt_coords ),
#		    &{$DRIVER->{waypoints_from_expected}}( $title, $route_ind, @order)))
#	);
#    };

1;
