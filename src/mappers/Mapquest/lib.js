//indx#	lib.js - Javascript portion of Mapquest routing
//@HDR@	$Id$
//@HDR@
//@HDR@	Copyright (c) 2026 Christopher Caldwell (Christopher.M.Caldwell0@gmail.com)
//@HDR@
//@HDR@	Permission is hereby granted, free of charge, to any person
//@HDR@	obtaining a copy of this software and associated documentation
//@HDR@	files (the "Software"), to deal in the Software without
//@HDR@	restriction, including without limitation the rights to use,
//@HDR@	copy, modify, merge, publish, distribute, sublicense, and/or
//@HDR@	sell copies of the Software, and to permit persons to whom
//@HDR@	the Software is furnished to do so, subject to the following
//@HDR@	conditions:
//@HDR@	
//@HDR@	The above copyright notice and this permission notice shall be
//@HDR@	included in all copies or substantial portions of the Software.
//@HDR@	
//@HDR@	THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY
//@HDR@	KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE
//@HDR@	WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE
//@HDR@	AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT
//@HDR@	HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY,
//@HDR@	WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
//@HDR@	FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE
//@HDR@	OR OTHER DEALINGS IN THE SOFTWARE.
//
//hist#	2026-02-10 - Christopher.M.Caldwell0@gmail.com - Created
////////////////////////////////////////////////////////////////////////
//doc#	lib.js - Javascript portion of Mapquest routing
//////////////////////////////////////////////////////////////////////////

var MAPQUEST_KEY	= "%%MAPQUEST_KEY%%";

//////////////////////////////////////////////////////////////////////////
//	Called by createMap() for each waypoint to show what is there.	//
//	(goto_map_better_Mapquest helper)				//
//////////////////////////////////////////////////////////////////////////
//checkpoint("00023 function anyMarker");
function anyMarker( location, stopNumber )
    {
    debug_out( "functions", "function start anyMarker()");
    // var stop_ind = stopNumber; // convert_stopNumber_to_stop_ind();
    var stop_ind =
	map_order[ last_route_response.route.locationSequence[stopNumber-1] ];

    var pretty_name =
	( stop_ind < 0
	// ? "(Current location @"+location.latLng.lat+","+location.latLng.lng+")"
	? "(Current location)"
	: stops[stop_ind].pretty.replace(/,\s*/g,"<br>") );

    return L.mapquest.textMarker( location.latLng,
	{
	draggable: false,
	//text: location['street']+' ('+location['sideOfStreet']+')',
	text:  pretty_name,
	type: 'marker',
	icon:
	    {
	    primaryColor:	'#22407F',
	    secondaryColor:	'#3B5998',
	    size:		'sm',
	    shadow:		true,
	    symbol:		stopNumber-1
	    }
	});
    }

//////////////////////////////////////////////////////////////////////////
//	Have a response to a route request, update the map.		//
//////////////////////////////////////////////////////////////////////////
var last_route_response = 0;
var last_need_map_flag;
var mapptr;
var directionsLayer;
//checkpoint("00024 function update");
function update_map_for_Mapquest()
    {
    debug_out( "functions", "function start update_map_for_Mapquest()");
    if( ! mapptr )
	{
	mapptr = L.mapquest.map('map',
	    {
	    center:	[0, 0],
	    layers:	L.mapquest.tileLayer('map'),
	    zoom:	12
	    });
	}

    DirectionsLayerWithCustomMarkers =
	L.mapquest.DirectionsLayer.extend(
	    {
	    createStartMarker:		function(loc,stopnum)
					    { return anyMarker(loc,stopnum); },
	    createWaypointMarker:	function(loc,stopnum)
					    { return anyMarker(loc,stopnum); },
	    createEndMarker:		function(loc,stopnum)
					    { return anyMarker(loc,stopnum); }
	    });

    if( directionsLayer )
        { mapptr.removeLayer(directionsLayer); }
    directionsLayer = new DirectionsLayerWithCustomMarkers(
	{ directionsResponse: last_route_response }
	).addTo(mapptr);

    return true;
    }

//////////////////////////////////////////////////////////////////////////
//	Called either by response from Mapquest directions.route()	//
//	or directly from start_getting_Mapquest_route() if nothing	//
//	changed since last time route was asked for.			//
//									//
//	If start_getting_Mapquest_route was called with need_map_flag	//
//	true, go do that with last response.				//
//////////////////////////////////////////////////////////////////////////
//checkpoint("00025 function callback");
function callback_for_Mapquest_route( err, response )
    {
    debug_out( "functions", "function start callback_for_Mapquest_route()");
    if( ! response )
	{
	alert( hash_to_string("callback_for_Mapquest_route error",err) );
	//alert( "callback_for_Mapquest_route error:  " + JSON.stringify(err) );
	}
    else
	{
	last_route_response = response;
	last_display_order = 0;
	if( last_need_map_flag )
	    { update_map_for_Mapquest( last_route_response ); }

	// update_stops_with_new_route();
	}
    return true;
    }

//////////////////////////////////////////////////////////////////////////
//	Get a route (optimized if optimize_flag is true) and update	//
//	the flag if need_map_flag is true.				//
//									//
//	If we already have an appropriate cached route, just call	//
//	route handler as if returning from the callback, otherwise	//
//	invoke route software with a callback to the route handler.	//
//////////////////////////////////////////////////////////////////////////
var cache_stops;
//checkpoint("00026 function start");
function start_getting_Mapquest_route( optimize_flag, need_map_flag )
    {
    debug_out( "functions", "function start start_getting_Mapquest_route()");
    for( var stop_number=0; stop_number<stops.length; stop_number++ )
	{
	var stopping = need_to_visit( stop_number );
	if( stops[stop_number].oldstatus != stopping )
	    {	// Something has changed, last route worthless
	    last_route_response=0;
	    }
	stops[stop_number].oldstatus = stopping;
	}
       
    let {namelist,preflist,addrlist,cordlist} = split_out("Mapquest");
    last_need_map_flag = need_map_flag;

    if( last_route_response && !optimize_flag )
        { callback_for_Mapquest_route( 0, last_route_response ); }
    else
	{
	L.mapquest.key = MAPQUEST_KEY;

	var addrcord = new Array();
	for( var i=0; i<addrlist.length; i++ )
	    { addrcord.push( cordlist[i] || addrlist[i] ); }

	var directions = L.mapquest.directions();
	var resp = directions.route(
	    {
	    start:		addrcord[0],
	    end:		addrcord[ addrcord.length-1 ],
	    waypoints:		addrcord.slice( 1, addrcord.length-1 ),
	    optimizeWaypoints:	optimize_flag
	    }, callback_for_Mapquest_route );
	}
    if( last_need_map_flag )
        { lightup( "map", "/goto_map_better_mapquest" ); }
    return true;
    }

//////////////////////////////////////////////////////////////////////////
//	Update the html element with id=map to contain complete route.	//
//////////////////////////////////////////////////////////////////////////
//checkpoint("00034 function goto");
function goto_Mapquest_map()
    {
    debug_out( "functions", "function goto_Mapquest_map()");
    // Assume already optimized, draw map
    start_getting_Mapquest_route(false,true);
    return false;
    }
map_handlers.Mapquest = goto_Mapquest_map;
