<html><head><script>
//
//indx#	template.js - Used for creating mapquest map
//@HDR@	$Id$
//@HDR@
//@HDR@	Copyright (c) 2024-2026 Christopher Caldwell (Christopher.M.Caldwell0@gmail.com)
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
//doc#	template.js - Used for creating mapquest map
////////////////////////////////////////////////////////////////////////
</script>
    <script src="https://api.mqcdn.com/sdk/mapquest-js/v1.3.2/mapquest.js"></script>
    <link type="text/css" rel="stylesheet" href="https://api.mqcdn.com/sdk/mapquest-js/v1.3.2/mapquest.css"/>

    <script type="text/javascript">
    var ROUTES = %%ROUTES%%;
    var STATUS_STYLES = %%STATUS_STYLES%%;
    var NAME_COLORS = %%NAME_COLORS%%;
    var RRGGBB_COLORS = %%RRGGBB_COLORS%%;

    var waypoints = new Array();
    var end_pt = new Array();
    var directions = new Array();
    var DirectionsLayerWithCustomMarkers = new Array();
    var start_pt = new Array();
    var plines = new Array();
    var waypts = new Array();
    var bounds;

    function my_marker( route_ind, ind )
        {
	// alert("route_ind=["+(route_ind||"?")+"] ind=["+(ind||"?")+"]");
	return {
	    draggable:	false,
	    text:	ROUTES[route_ind].STOPS[ind].name,
	    type:	'marker',
	    icon:	{
			primaryColor:	'#'+RRGGBB_COLORS[ROUTES[route_ind].color],
			// secondaryColor:	'#3B5998',
			size:		'sm',
			shadow:		true,
			symbol:		ind
			}
	    };
	}

    for( var route_ind=0; route_ind<ROUTES.length; route_ind++ )
        {
	waypoints[route_ind] = new Array();
	for( var ind=0; ind<ROUTES[route_ind].STOPS.length; ind++ )
	    {
	    var stp = ROUTES[route_ind].STOPS[ind];
	    /(.*),(.*)/.test( stp.coords );
	    stp.latLng = [ parseFloat( RegExp.$1 ), parseFloat( RegExp.$2 ) ];
	    // alert( ROUTES[route_ind].name + " ("+ stp.name + ") at "+stp.latLng[0]+","+stp.latLng[1]+".");
	    if( ! bounds )
	        {
		bounds =
		    {
		    minlat:	stp.latLng[0],
		    maxlat:	stp.latLng[0],
		    minlng:	stp.latLng[1],
		    maxlng:	stp.latLng[1]
		    };
		}
	    else
	        {
		if( stp.latLng[0]<bounds.minlat )
		    { bounds.minlat = stp.latLng[0]; }
		else if( stp.latLng[0]>bounds.maxlat )
		    { bounds.maxlat = stp.latLng[0]; }
		if( stp.latLng[1]<bounds.minlng )
		    { bounds.minlng = stp.latLng[1]; }
		else if( stp.latLng[1]>bounds.maxlng )
		    { bounds.maxlng = stp.latLng[1]; }
		}
	    waypoints[route_ind].push( stp.address );
	    }
	start_pt[route_ind] = waypoints[route_ind].shift();
	end_pt[route_ind] = waypoints[route_ind].pop();
	}
    bounds.midlat = (bounds.minlat+bounds.maxlat)/2.0;
    bounds.midlng = (bounds.minlng+bounds.maxlng)/2.0;

    function setup_mapper()
	{
	L.mapquest.key = '%%MAPQUEST_KEY%%';

	var map = L.mapquest.map('map',
	    {
	    center:	[ bounds.midlat, bounds.midlng ],
	    layers:	L.mapquest.tileLayer('map'),
	    zoom:	12
	    });

	for( var route_ind=0; route_ind<ROUTES.length; route_ind++ )
	    {
	    directions[route_ind] = L.mapquest.directions();
	    directions[route_ind].route(
		{
		start:		start_pt[route_ind],
		waypoints:	waypoints[route_ind],
		end:		end_pt[route_ind],
		options:	{ route_ind: route_ind }
		}, createRoute);

	    function createRoute(err, response) {
		var cr_ind = response.route.options.route_ind;
		directionsLayer = new L.mapquest.DirectionsLayer({
		    startMarker:	{ icon:'via' },
		    endMarker:		{ icon:'via' },
		    waypointMarker:	{ icon:'via' },
		    routeRibbon:	{
					color: '#'+RRGGBB_COLORS[ROUTES[cr_ind].color],
					opacity: 0.50,
					showTraffic: false
					},
		    directionsResponse: response
		    }).addTo(map);
		}

	    if( ROUTES[route_ind].progress )
		{
		plines[route_ind] =
			L.polyline(
			    ROUTES[route_ind].progress,
			    {color: NAME_COLORS[ROUTES[route_ind].color]}
			    ).addTo(map);
		}
	    }
	
	for( var route_ind=0; route_ind<ROUTES.length; route_ind++ )
	    {
	    for( var ind=0; ind<ROUTES[route_ind].STOPS.length; ind++ )
		{
		L.mapquest.textMarker(
		    ROUTES[route_ind].STOPS[ind].latLng,
		    my_marker( route_ind, ind )
		    ).addTo(map);
		}
	    }
	}

    function create_table()
	{
	var s = new Array( "<table style='border: solid black' border=1 cellspacing=0>");
	
	for( var route_ind=0; route_ind<ROUTES.length; route_ind++ )
	    {
	    s.push( "<tr><th colspan=6>", ROUTES[route_ind].name, "</th>",
		"<tr><th>Map index</th>", "<th>Name</th>", "<th>Status</th>",
		"<th>Updated</th>", "<th>Phone</th>", "<th>Address</th>" );
	    for( var ind=0; ind<ROUTES[route_ind].STOPS.length; ind ++ )
		{
		var stop_style = STATUS_STYLES[ ROUTES[route_ind].STOPS[ind].status ];
		s.push(
		    "</tr>\n<tr style='", stop_style, "'>",
		    "<th>", ind, "</th>",
		    "<td>", ROUTES[route_ind].STOPS[ind].name, "</td>",
		    "<td>", ROUTES[route_ind].STOPS[ind].status, "</td>",
		    "<td>", ROUTES[route_ind].STOPS[ind].when, "</td>",
		    "<td><nobr><a href='tel:", ROUTES[route_ind].STOPS[ind].phone, "'>",
			ROUTES[route_ind].STOPS[ind].phone, "</a></nobr></td>" );
		if( ! ROUTES[route_ind].STOPS[ind].coords )
		    { s.push( "<td>", ROUTES[route_ind].STOPS[ind].addrtxt, "</td>" ); }
		else
		    {
		    s.push( "<td><a target=stop_map href='http://maps.google.com/maps?q=",
			ROUTES[route_ind].STOPS[ind].coords, "'>",ROUTES[route_ind].STOPS[ind].addrtxt,"</a></td>" );
		    }
		if( ROUTES[route_ind].STOPS[ind].notes )
		    {
		    s.push( "</tr><tr style='",
			stop_style, "'><td></td><td colspan=5>",
			ROUTES[route_ind].STOPS[ind].notes,
			"</td>" );
		    }
		}
	    s.push( "</tr>\n" );
	    }
	s.push( "</table>" );
	(document.getElementById("tbl")).innerHTML = s.join("");
	}

    window.onload = function()
	{
	setup_mapper();
	create_table();
	}
    </script>
<title>%%TITLE%%</title>
</head><body style="border: 0; margin: 0;"><center>
    <center><b>%%TITLE%%</b></center>
    <div id="map" style="width: 100%; height: 530px;"></div>
    <div id="tbl"></div>
</center></body>
</html>
