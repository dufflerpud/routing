#!/usr/local/bin/perl -w
#
#indx#	lib.pl - Routines for using Mapquest routing and mapping
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
#doc#	lib.pl - Routines for using Mapquest routing and mapping
########################################################################

use strict;

package main;
use lib "/usr/local/lib/perl";
use cpi_drivers qw( get_drivers device_debug get_driver );

my $driverp = &get_driver(__FILE__);

#$driverp->{KEY}		= 'Key should be in the database';
$driverp->{minmaps}		= 1;
$driverp->{maxmaps}		= 100;
$driverp->{STATICURL}		= "https://www.mapquestapi.com/staticmap/v5/map";
$driverp->{SHAPE_PARMS}		= "fill:ffffff88|width:7mi|weight:4";

$driverp->{PRECISION}		= 5;
@{$driverp->{BOUNDS_ORDER}}	= ("maxlat","maxlng","minlat","minlng");
$driverp->{destext}		= "html";
$driverp->{mime}		= "text/html";
$driverp->{tobrowser}		= 1;
$driverp->{name}		= "Mapquest browser map";
$driverp->{URL}			= "http://www.mapquestapi.com/directions/v2";
$driverp->{MQAPI}		= "https://www.mapquestapi.com";
$driverp->{STATIC}		= "$driverp->{MQAPI}/staticmap/v5/map";
$driverp->{GEOCODING_URL}	= "$driverp->{MQAPI}/geocoding/v1/batch";
$driverp->{ROUTEMATRIX_URL}	= "$driverp->{MQAPI}/directions/v2/routematrix";
$driverp->{ROUTING_URL}		= "$driverp->{URL}/optimizedroute";
$driverp->{SHAPE_URL}		= "$driverp->{URL}/routeshape";
$driverp->{V1_ADDR}		= "country/state/town/street";
$driverp->{V2_ADDR}		= "street,town,state";

#########################################################################
# Stolen directly (though re-indented) from				#
# https://developer.mapquest.com/documentation/common/encode-decode/	#
#########################################################################
$driverp->{decompress} = sub
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
    };

#########################################################################
#	Compress a series of points into a string.			#
#########################################################################
$driverp->{compress} = sub
    {
    my($precision,@points) = @_;
    #$precision_multiplier = Math.pow(10, $precision);
    my $precision_multiplier = 10 ** $precision;
    my @encoded;
    my $latlong_ind = 0;
    my @last_latlong = ( 0, 0 );
    foreach my $point ( @points )
	{
	## Round to N decimal places
	my $latlong = int( $point * $precision_multiplier );

	## Encode the differences between the points
	push( @encoded, &{$driverp->{encode_number}}($latlong - $last_latlong[$latlong_ind]) );

	## Update our concept of last latitude or longitude
	$last_latlong[$latlong_ind] = $latlong;
	$latlong_ind = 1 - $latlong_ind;
	}
    return join("",@encoded);
    };

#########################################################################
#	Return a string that is an encoded version of the number.	#
#########################################################################
$driverp->{encode_number} = sub
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
    };

#########################################################################
#	Unused testing							#
#########################################################################
$driverp->{test_compress} = sub
    {
    my $s = &{$driverp->{compress}}
	(
	$driverp->{PRECISION},
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
    my @points = &{$driverp->{decompress}}( $driverp->{PRECISION}, $s );
    print $s, " =>\n[", join(",",@points), "]\n";
    };

#########################################################################
#	Return trkpt string from progress GPS list.			#
#########################################################################
$driverp->{progress_to_tracks} = sub
    {
    my( $title, $input_p ) = @_;
    return &{$driverp->{tracks}}(
	$title,
	( $input_p->{color} || ( $input_p->{done} ? "blue" : "green" ) ),
	@{$input_p->{progress_p}} );
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

    my @ret = ( "<table style='border: solid black' border=1 cellspacing=0>" );

    foreach my $stop ( map { $stops->[$_] } @{$display_order} )
	{
	next if( ! $stop->{coords} );
	if ( $stop->{when} && $stop->{when} =~ /(\d+):(\d+)/ )
	    { $hour=$1; $min=$2; }
	my( $ind, @others ) = split( /,/, $stop->{patrons} );
	push( @ret, &{$driverp->{stop}}({
	    ind		=>	$ind,
	    time	=>	timelocal(0,$min,$hour,$mday,$month,$year),
	    status	=>	($stop->{status}||""),
	    note	=>	($stop->{notes}||"")
	    } ) );
	}
    push( @ret, "</table>\n" );

    return join("",@ret);
    };

#########################################################################
#	$progress_p is a pointer to array of hashes containing		#
#	time, latitude and longitude.  Only want array of 2-member	#
#	arrays.								#
#########################################################################
$driverp->{just_latlng} = sub
    {
    my( $input_p ) = @_;
    return map{($_->{lat},$_->{lng})} @{$input_p->{progress_p}};
    };

#########################################################################
#	Return a string with an encoded JPEG file.			#
#########################################################################
$driverp->{progress_to_pic} = sub
    {
    my( $base, $bounds, $compressed_string, $uncompressed_string ) = @_;
#    print "CMC progress_to_pic, base=$base bounds=",$bounds,
#	" cs=",length($compressed_string),".<br>\n";
    my $res = &cpi_cache::cache({
	query=>"$main::CACHEDIR/$base.txt",
	result=>"$main::CACHEDIR/$base.b64",
	http=>$driverp->{STATICURL},
	method=>"POST",
	args=>
	    [
	    "key=$driverp->{KEY}",
	    "type=map",
	    "imagetype=jpeg",
	    "declutter=false",
	    "traffic=4",
	    #"shapeformat=cmp","shape=".$driverp->{SHAPE_PARMS}."|cmp|enc:$compressed_string",
	    "shape=".$driverp->{SHAPE_PARMS}."|$uncompressed_string",
	    "boundingBox=$bounds",
	    "size=\@2x" ]
	} );
    #print "l now [",($res?length($res):"UNDEF"),"].<br>\n";
    return $res;
    };

#########################################################################
#	Return a mq file from the GPS list and the various stops.	#
#########################################################################
$driverp->{progress} = sub
    {
    my( $title, @input_ps ) = @_;

    print STDERR "order_query progress = $input_ps[0]->{distributor} .\n";
    $driverp->{KEY} = &main::DBget( $input_ps[0]->{distributor}, "Mapquest_key" );

    my @routes;
    foreach my $input_p ( @input_ps )
	{
	my %route_info =
	    (	name		=>	$input_p->{title},
		color		=>	$input_p->{color},
	    );

	@{$route_info{progress}}
	    = map { [ $_->{lat}, $_->{lng} ] } @{$input_p->{progress_p}}
		if( $input_p->{progress_p} );

	@{$route_info{STOPS}} = @{$input_p->{stops}} if( $input_p->{stops} );

	push( @routes, \%route_info );
	}

    return &cpi_template::template( $driverp->{template},
	"%%TITLE%%",		$title||"UNDEF",
	"%%RRGGBB_COLORS%%",	encode_json( [ &main::colors_by("rrggbb") ] ),
	"%%NAME_COLORS%%",	encode_json( [ &main::colors_by("Name") ] ),
        "%%STATUS_STYLES%%",	encode_json( \%main::STATUS_STYLES ),
	'%%ROUTES%%',		encode_json( \@routes ),
	'%%MAPQUEST_KEY%%',	$driverp->{KEY}
	);
    };

#########################################################################
#	Returns mqeese text for a stop but takes times, stati & note.	#
#########################################################################
$driverp->{stop} = sub
    {
    my( $stop_argp )		= @_;
    my $ind			= $stop_argp->{ind};
    my $global_time_str		= &cpi_time::time_string( $main::GLOBAL_TIME_FMT, $stop_argp->{time} );

    $global_time_str =~ s/T/ /g;
    $global_time_str =~ s/\.\d\d\d[A-Z]$//g;

    my $addrtxt = &main::DBget($ind,"Address");
    if( $addrtxt )
	{ $addrtxt =~ s+^(.*?),(.*)+<nobr>$1</nobr><br>$2+; }
    else
	{ $addrtxt = "No address"; }

    my( $lat, $lon )		= split(/,/, (&main::DBget($ind,"Coords")||"UNDEF") );

    my $status = ($stop_argp->{status}||"No Status");
    my $status_style = $main::STATUS_STYLES{$status} || "";
    return join("",
    	"<tr style='$status_style'>\n",
    	"<th valign=top align=left>",(&main::DBget($ind,"Name")||"UNDEF"),"</th>\n",
    	"<td valign=top>$global_time_str</td>\n",
    	"<td valign=top>",
    	( ($_=&main::DBget($ind,"Phone"))
	    ? "<nobr><a href='tel:$_'><nobr>$_</a></nobr>"
	    : "No phone" ), "</td>\n",
    	"<td valign=top>",
    	( $lat
	    ? "<a href='http://maps.google.com/maps?q=$lat,$lon'>$addrtxt</a>"
	    : $addrtxt ), "</td>\n",
    	"<td valign=top>", $status, "</td>\n",
    	"<td valign=top>", ($stop_argp->{note}||""), "</td>\n",
    	"</tr>\n" );
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
	   "<styleUrl>#$linecolor</styleUrl>\n",
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
##	Creates a Mapquest pieces for each waypoint in expected route.	#
##########################################################################
#$driverp->{waypoints_from_expected} = sub
#    {
#    my( $title, $route_ind, @patron_order ) = @_;
#    print "CMC waypoints_from_expected.\n";
#    my @ret = ( "<table border=1>" );
#    foreach my $ind ( @patron_order )
#	{
#	push( @ret, &{$driverp->{stop}}({
#	    ind		=>	$ind,
#	    time	=>	time(),
#	    status	=>	(&main::DBget($ind,"Status")||"No Status"),
#	    note	=>	(&main::DBget($ind,"Last_note")||"")
#	    }) );
#	}
#    push( @ret, "</table>\n" );
#    return join("",@ret);
#    };
#
##########################################################################
##	Creates a Mapquest file for the route specified.  Not		#
##	necessarily route driver actually took, but something to	#
##	compare against.						#
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
#	    "%%STATUS_STYLES%%", encode_json( \%main::STATUS_STYLES ),
#	    "%%RRGGBB_COLORS%%", encode_json( [ &main::colors_by("rrggbb") ] ),
#	    "%%NAME_COLORS%%", encode_json( [ &main::colors_by("Name") ] ),
#	    "%%ACTUAL_DATA%%",
#		join("",
#		    &{$driverp->{tracks}}( $title, "red", @main::rt_coords ),
#		    &{$driverp->{waypoints_from_expected}}( $title, $route_ind, @order)))
#	);
#    };

#our $cpi_vars::CACHEDIR;
#our @main::rt_coords;
#our %stop;
#our $main::current_route;
#our $main::total_time;
#our $main::total_distance;

#########################################################################
#	Cute way of mapping routing standard address to different	#
#	Mapquest standards.						#
#########################################################################
$driverp->{remapper} = sub
    {
    my( $addr, $fmt ) = @_;
    my $res = $addr;
    if( $addr !~ /^[\-\.\d]+,[\-\.\d]+$/ )
	{
	my $res = $fmt;
	my @toks = split(/,\s*/,$addr);
	my %fld =
	    (
	    "street"	=>	shift(@toks),
	    "town"	=>	shift(@toks),
	    "state"	=>	shift(@toks)||"ME",
	    "zip"	=>	shift(@toks)||"",
	    "country"	=>	shift(@toks)||"US"
	    );
	foreach my $k ( keys %fld ) 	{ $res =~ s/$k/Q$k/g; }
	foreach my $k ( keys %fld )	{ $res =~ s/Q$k/$fld{$k}/; }
	}
    print STDERR "remapper($addr with $fmt) returns [$res]\n";
    return $res;
    };

#########################################################################
#	Generate a URL to Mapquest maps from a route.			#
#########################################################################
$driverp->{route_to_url} = sub
    {
    my( $map_start, $map_end, @loc_list ) = @_;
    my @res = ( "https://www.mapquest.com/directions" );
    #push( @res, "/from/near-$map_start" ) if( $map_start );
    #push( @res, ( map { "/to/near-$_" } ( @loc_list, $map_end ) ) );
    push( @res,
	"/from/".&{$driverp->{remapper}}($map_start,$driverp->{V1_ADDR}) )
	if( $map_start );
    push( @res,
	( map
	    { "/to/".&{$driverp->{remapper}}($_,$driverp->{V1_ADDR}) }
	    ( @loc_list, $map_end )
	) );
    return join("",@res);
    };

#########################################################################
#	Try to print a useful mapquest error message.
#########################################################################
$driverp->{fatal} = sub
    {
    my ( $msg, $mq_res ) = @_;
    &cpi_file::autopsy("Mapquest failure for $msg, with no results") if( ! $mq_res );
    &cpi_file::autopsy("Mapquest failure for $msg with no useful failure diagnostics")
	if( ! $mq_res->{info} || ! $mq_res->{info}{messages} );
    &cpi_file::autopsy("Mapquest failure for $msg with:".join("\n",@{$mq_res->{info}{messages}}) );
    };

#########################################################################
#	Constructs query to mapquest.  Turn query into filename.	#
#	If file exists, it is the cached results, use those.  Else,	#
#	actually run the query and put results in the cache.		#
#########################################################################
$driverp->{order_query} = sub
    {
    my( @stoplist ) = @_;

    print STDERR "order_query distributor = $main::current_distributor .\n";
    $driverp->{KEY} = &main::DBget( $main::current_distributor, "Mapquest_key" );
    print STDERR "k=$driverp->{KEY}.\n";
    print STDERR "stoplist=((",Dumper(\@stoplist),"))\n";

    my @mapquest_locations;
    #my @debug_list;
    #print "mq_order_query( ", join(",",@stoplist), " ).<br>\n";
    foreach my $stopind ( @stoplist )
	{
	my $locstr =
	    ( $main::stop{$stopind}{coords}
	    ?	$main::stop{$stopind}{coords}
	    :	&{$driverp->{remapper}}(
	    	    $main::stop{$stopind}{address},
		    $driverp->{V2_ADDR} ) );
	push( @mapquest_locations, $locstr );
	#push( @debug_list, $main::stop{$stopind}{name_string} . ": " . $locstr );
	}

    #my $begin_address	= $mapquest_locations[0];
    #my @waypoints	= @mapquest_locations[1..$#mapquest_locations-1];
    #my $end_address	= $mapquest_locations[$#mapquest_locations];

    my $jsonpart =
	"{" . join(",",
	    #"beginpoint:'$begin_address'",
	    #"endpoint:'$end_address'",
	    #"locations:['".join("','",@waypoints)."']"
	    '"fullShape":"true"',
	    '"shapeFormat":"raw"',
	    '"locations":["'.join('","',@mapquest_locations).'"]'
	    #'"debug":["'.join('","',@debug_list).'"]'
	    ) . "}";
    &cpi_file::write_file( $cpi_vars::CACHEDIR."/JSON.json", $jsonpart );

    &cpi_file::autopsy("No route defined.  Dying.") if( ! $main::current_route );

    my $mqorp = &http_json(
	&cpi_filename::text_to_filename($main::current_route).".%s.ord",
	"$driverp->{ROUTING_URL}?key=$driverp->{KEY}",
	$jsonpart
	);

    &{$driverp->{fatal}}("obtaining route",$mqorp)
	if( ! $mqorp || ! $mqorp->{route} );
    &{$driverp->{fatal}}("obtaining locationSequence",$mqorp)
	if( ! $mqorp->{route}{locationSequence} );
    my @sequence = @{$mqorp->{route}{locationSequence} };

    my $last_time = 0;
    my $last_distance = 0;

    my $update_patron_gps = 0;
    for( my $i=0; $i<scalar(@sequence); $i++ )
        {
	my $stop_name = $stoplist[$sequence[$i]];
	#$main::stop{time_to} = $last_time;
	$main::stop{$stop_name}{time_to} = $last_time;
	$main::stop{$stop_name}{distance_to} = $last_distance;
	$main::total_time += $last_time;
	$main::total_distance += $last_distance;
	$main::stop{$stop_name}{total_time_to} = $main::total_time;
	$main::stop{$stop_name}{total_distance_to} = $main::total_distance;
	my $lp = $mqorp->{route}{legs}[$i];
        foreach my $patron_ind ( @{ $main::stop{$stop_name}{patrons} } )
	    {
	    if( ! &main::DBget( $patron_ind, "Coords" ) )
		{
		&DBwrite() if( ! $update_patron_gps++ );
		&DBput( $patron_ind, "Coords",
		    $lp->{maneuvers}[0]{startPoint}{lat} . "," .
		    $lp->{maneuvers}[0]{startPoint}{lng} );
		print 
		    "Setting <b>", &main::DBget($patron_ind,"Name"),
		    "</b> at <b>", &main::DBget($patron_ind,"Address"),
		    "</b> to <b>", &main::DBget($patron_ind,"Coords"),
		    "</b>.<br>\n";
		}
	    }
	$last_time = $lp->{time};
	$last_distance = int( ($lp->{distance}||0) * 10 + 0.5 ) / 10.0;
	}
    &DBpop() if( $update_patron_gps );

    my $mqshp = &http_json(
	&cpi_filename::text_to_filename($main::current_route).".%s.gps",
	"$driverp->{SHAPE_URL}?key=$driverp->{KEY}&sessionId=".$mqorp->{route}{sessionId}."&fullShape=true");

    &{$driverp->{fatal}}("obtaining route",$mqorp)
	if( ! $mqorp || ! $mqorp->{route} );

    my @mq_coords = @{$mqshp->{route}{shape}{shapePoints}};
    while( @mq_coords )
	{ push(@main::rt_coords,{lat=>shift(@mq_coords),lng=>shift(@mq_coords)}); }

    return map { $stoplist[$_] } @{$mqorp->{route}{locationSequence}};
    };

#########################################################################
#	Actual geocoding interface to mapquest.				#
#########################################################################
$driverp->{geocode_batch} = sub
    {
    my( @addresses ) = @_;
    my @ret;
    my $jsonpart = encode_json(
	{
	locations	=>	[ @addresses ],
	options		=>
		{
		maxResults		=>	-1,
		thumbMaps		=>	"false",
		ignoreLatLngInput	=>	"false"
		}
	} );
    &cpi_file::autopsy("Refusing to geocode:  " . join("; ",@addresses));
    my $mq_geocode_res = &http_json(
	"batched_geocodes",
	"$driverp->{GEOCODING_URL}?key=$driverp->{KEY}",
	$jsonpart
	);
    &{$driverp->{fatal}}("obtaining geocoding",$mq_geocode_res)
        if( ! $mq_geocode_res || ! $mq_geocode_res->{results} );
    for( my $addrind=0; $addrind<scalar(@addresses); $addrind++ )
	{
	my $lat = $mq_geocode_res->{results}[$addrind]{locations}[0]{latLng}{lat};
	my $lng = $mq_geocode_res->{results}[$addrind]{locations}[0]{latLng}{lng};
	#my $fromaddr = $mq_geocode_res->{results}[$addrind]{providedLocation}{street};
	#print "Addresses[$addrind] = $lat,$lng from $fromaddr.<br>\n";
	push( @ret, "$lat,$lng" );
	}
    return @ret;
    };

#########################################################################
#	Query mapquest to get relative costs of routes from the origin	#
#	and any of the coordinates.					#
#########################################################################
our $cost_origin;
$driverp->{costs_batch} = sub
    {
    my( @coords ) = @_;
    my @ret;
    my $jsonpart = encode_json(
    	{
	allToAll	=>	"false",
	manyToOne	=>	"true",
	locations	=>	[ $cost_origin, @coords ]
	} );
    #print "jsonpart=[$jsonpart]\n";
    #&cpi_file::autopsy("Refusing to batch costs:  ". join("; ",$cost_origin,@coords) );
    print "Costing [ $cost_origin and ", join(" ",@coords), "]<br>\n";
    my $mq_costs_res = &http_json(
	"batched_costs",
	"$driverp->{ROUTEMATRIX_URL}?key=$driverp->{KEY}",
	$jsonpart
	);
    #print "Post call...<br>\n";
    &{$driverp->{fatal}}("obtaining cost matrix",$mq_costs_res)
        if( ! $mq_costs_res || ! $mq_costs_res->{distance} );
    #print "Post error check...<br>\n";
    for( my $coordind=0; $coordind < scalar(@coords); $coordind++ )
        {
	my $d = $mq_costs_res->{distance}[$coordind+1];
	my $t = $mq_costs_res->{time}[$coordind+1];
	&cpi_file::autopsy("undef coords[$coordind]=$coords[$coordind]]")
	    if( !defined($t) || !defined($d) );
	#print "d($coords[$coordind]) = $d.  t=$t.<br>\n";
	print "d=0 at coords[$coordind]=$coords[$coordind].<br>\n"
	    if( ! $d );
	push( @ret, $d );
	}
    return @ret;
    };

#########################################################################
#	Existence will stop the main program from creating the		#
#	expected list.  We do this because the expected route will be	#
#	created by the javascript.					#
#########################################################################
$driverp->{expected} = sub
    {
    };

#########################################################################
#	Return the javascript with any substitutions.			#
#########################################################################
$driverp->{js} = sub
    {
    my( $dist ) = @_;
    $driverp->{KEY} = &main::DBget( $dist, "Mapquest_key" );
    return &cpi_template::template( $driverp->{dir}."/lib.js",
        "%%MAPQUEST_KEY%%", $driverp->{KEY} );
    };

1;
