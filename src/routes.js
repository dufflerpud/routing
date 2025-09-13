//@HDR@	$Id$
//@HDR@		Copyright 2024 by
//@HDR@		Christopher Caldwell/Brightsands
//@HDR@		P.O. Box 401, Bailey Island, ME 04003
//@HDR@		All Rights Reserved
//@HDR@
//@HDR@	This software comprises unpublished confidential information
//@HDR@	of Brightsands and may not be used, copied or made available
//@HDR@	to anyone, except in accordance with the license under which
//@HDR@	it is furnished.
//////////////////////////////////////////////////////////////////////////
//	routes.js							//
//	Javascript included in .html files with routes sent to drivers.	//
//	Chris Caldwell, 04/29/2022					//
//////////////////////////////////////////////////////////////////////////
//
//////////////////////////////////////////////////////////////////////////
//	Used for testing.  Configurable by adding ?debug=1 to URL.	// 
//////////////////////////////////////////////////////////////////////////
var DEBUG =
    {
    "debug":		{ value:0,	values:["0=Off","1=On"] },
    "update":		{ value:1,	values:["0=No Update","1=Update"] },
    "position":		{ value:0,	values:["0=Off","1=On"] },
    "browser":		{ value:0,	values:["0=Quiet","1=Show"] },
    "checkpointing":	{ value:0,	values:["0=Quiet","1=Show"] },
    "functions":	{ value:0,	values:["0=Quiet","1=Show"] },
    "cookies":		{ value:0,	values:["0=Quiet","1=Show"] },
    "flow":		{ value:0,	values:["0=Quiet","1=Show"] },
    "split_out":	{ value:0,	values:["0=Quiet","1=Show"] },
    "url":		{ value:0,	values:["0=Quiet","1=Show"] },
    "pref_ctl":		{ value:0,	values:["0=Auto","Coordinates","Addresses"] },
    "route_handler":	{ value:0,	values:["0=Auto","Apple","Google","Mapquest"] },
    "dest_handler":	{ value:0,	values:["0=Auto","Apple","Google","Mapquest"] },
    "Google_API":	{ value:"New",	values:["Old","saddr","New"] },
    "Android":		{ value:0,	values:["0=Quiet","1=Show"] }
    };

var COOKIE_NAME		= ROUTE_NAME + "_route";
var GPS_DIGITS		= 1000000.0;
var BAG_COLORS		= [ "#e0e0ff", "e0ffff" ];
var JITTER		= { latitude: 0.0001, longitude: 0.0001 };

var GPS_TIMEOUT		= 100000;	// May get adjusted by browser_dependent

var SCREENS =
	[ "debug", "oneof", "big", "small", "map", "patron_issue",
	  "odometer", "donation", "pickup", "route_type", "status" ];

var BAG_TYPE_VALUES	= [ "Received", "Expected" ];

var CURRENT_BROWSER = "unknown";
var current_stop = -1;
var route_history = new Array();
var geoposition_timer = -1;
var update_timer = -1;
var last_route_status = "";
var current_serial = 0;
var last_recorded = 0;
var last_serial_received = current_serial++;
// var caller_vars = new Array();

// var TEST_POSITION	= { latitude:44.632301, longitude:-70.196667 };
var TEST_POSITION;

//////////////////////////////////////////////////////////////////////////
//	Unused as we now send completed trips via CGI form, not email.	//
//////////////////////////////////////////////////////////////////////////
var OBSOLETE_COMPLETED_EMAIL	= "crm@brightsands.com";
var OBSOLETE_DRIVER_EMAIL	= "chris.interim@gmail.com";

//////////////////////////////////////////////////////////////////////////
//	At least for now, we generate multi-step routes on the fly	//
//	using Mapquest.  Since Mapquest is falling out of favor, we	//
//	may end up changing this, but it seems to work OK for now.	//
//	On Safari, we use Apple maps to tell us how to get to the	//
//	next stop because it interfaces nicely with Carplay.		//
//	On EVERYTHING ELSE, we use Google maps which may or may not	//
//	place nice with Carplay and/or Android Auto.			//
//	Maybe changed by browser_dependent()				//
//////////////////////////////////////////////////////////////////////////
var ROUTE_HANDLER		= "Mapquest";
var DEST_HANDLER		= "Google";

//////////////////////////////////////////////////////////////////////////
//	Global variables.						//
//////////////////////////////////////////////////////////////////////////
var map_handlers = new Array();	// Hash of handlers names to routines
var display_order;		// Array of order to display stops
var current_position;		// Which stop we are currently at

var doind = 1;
var time_constant =
    {
    MILLISECOND:	doind *= 1,
    SECOND:		doind *= 1000,
    MINUTE:		doind *= 60,
    HOUR:		doind *= 60,
    DAY:		doind *= 24
    };

time_constant.POSITION_POLL	= 10   * time_constant.SECOND;
time_constant.UPDATE_INTERVAL	= 1    * time_constant.MINUTE;
time_constant.PAGE_LIFETIME	= 1    * time_constant.DAY;

//////////////////////////////////////////////////////////////////////////
//	If flag set, write message some place useful.			//
//////////////////////////////////////////////////////////////////////////
//checkpoint("00000 function debug_out");
function debug_out( flag, msg )
    {
    if( DEBUG[flag].value ) { alert( "DEBUG "+flag+":\n" + msg ); }
    }

//////////////////////////////////////////////////////////////////////////
//	Return a URI encoded array from an array of arbitrary strings.	//
//////////////////////////////////////////////////////////////////////////
//checkpoint("00000 function encodeURIComponent_array");
function encodeURIComponent_array( array_in, joiner )
    {
    var array_out = new Array();
    for( var i=0; i<array_in.length; i++ )
        {
	array_out.push( encodeURIComponent( array_in[i] ) );
        }
    // alert("encodeURIComponent_array("+array_in.join(",")+") returns ["+array_out.join(",")+"]");
    return ( joiner? array_out.join(joiner) : array_out );
    }

//////////////////////////////////////////////////////////////////////////
//	Overwritten code to decide what browser to operate as.		//
//	All evil browser dependence is supposed to end up here.		//
//////////////////////////////////////////////////////////////////////////
var BROWSERS =
    {
    "Firefox":	"Firefox",
    "FxiOS":	"Firefox",
    "Chrome":	"Chrome",
    "CriOS":	"Chrome",
    "Safari":	"Safari",
    "Opera":	"Opera",
    "MSIE":	"MSIE",
    "Trident":	"MSIE",
    "Edge":	"Edge"
    };
//checkpoint("00000 function browser_dependent");
function browser_dependent()
    {
    if( ! /https:/.test( window.location ) )
	{
	if( ! /http:/.test( window.location ) )
            {
	    alert("Incorrect invocation:  "+window.location+"\n"+
	        "Invoke with https:");
	    }
	var new_invocation = window.location.replace("http:","https:");
	alert("Incorrect invocation:  "+window.location+"\n"+
	    "Reinvoking with:"+new_invocation);
	window.location = new_invocation;
	}
    const agent = navigator.userAgent;
    for( const try_browser in BROWSERS )
        {
	if( agent.indexOf(try_browser)>-1 )
	    {
	    CURRENT_BROWSER = BROWSERS[try_browser];
	    break;
	    }
	}
    debug_out( "url", "Agent=["+agent+"] Browser=["+CURRENT_BROWSER+"]" );
    if( CURRENT_BROWSER == "Safari" )
        {
	GPS_TIMEOUT = 5000;
	DEST_HANDLER = "Apple";
	}
    if( DEBUG.dest_handler.value )
	{ DEST_HANDLER = DEBUG.dest_handler.value; }
    }

//////////////////////////////////////////////////////////////////////////
//	Return a hash of hashes with order available.			//
//////////////////////////////////////////////////////////////////////////
//checkpoint("00000 function indexed_hash");
function indexed_hash( array_of_hashes, flds )
    {
    debug_out( "functions", "function start indexed_hash()");
    var hash_of_hashes = Array.from( array_of_hashes );

    var seen = new Array();
    for( const hash of array_of_hashes )
	{
	for( const ind in hash )
	    { seen[ind]=1; }
	}
    hash_of_hashes.fields = Object.keys( seen );

    if( ! flds )
        { flds = hash_of_hashes.fields; }
    else if( typeof(flds) != "object" )
    	{ flds = [flds]; }

    for( const fld of flds )
        {
	var fldind = fld + "s";
	hash_of_hashes[fldind] = new Array();
	for( const hash of array_of_hashes )
	    {
	    hash_of_hashes[fldind].push( hash[fld] );
	    hash_of_hashes[ hash[fld] ] = hash;
	    }
	}
    return hash_of_hashes;
    }
var STATES = indexed_hash([
	{ "name": "Untouched",	"color": "#ffffff" },
	{ "name": "Unvisited",	"color": "#ffffd0" },
	{ "name": "Skipped",	"color": "#d0e8ff" },
	{ "name": "Problems",	"color": "#ffd0d0" },
	{ "name": "Issues",	"color": "#ffff00" },
	{ "name": "Normal",	"color": "#d0ffd0" }
	], "name" );

//////////////////////////////////////////////////////////////////////////
//	Check sanity of world (will vary over time).			//
//	When in use, will probably be called from variety of places.	//
//	Argument "n" specifies from where called.			//
//	Can be any string you like (maybe a line number).		//
//////////////////////////////////////////////////////////////////////////
//checkpoint("00000 function sanity");
function sanity(n)		// Currently uncalled.
    {				// Change as needed.
    debug_out( "functions", "function start sanity()");
    for( var i=0; i<stops.length; i++ )
	{
        if( stops[i].status == undefined )
	{ alert("At "+n+" i="+i+" has seen insanity!!!"); }
	}
    }

//////////////////////////////////////////////////////////////////////////
//	Print an error message and die with a stack trace.		//
//////////////////////////////////////////////////////////////////////////
//checkpoint("00000 function fatal");
function fatal( msg )
    {
    try		{ throw new Error(); }
    catch(e)	{ alert( msg + "\n" + e.stack ); }
    return undefined;
    }

//////////////////////////////////////////////////////////////////////////
//	Get pointer to an ID but give a reasonable message if it does	//
//	not exist.  "should never happen".  Uh huh.			//
//////////////////////////////////////////////////////////////////////////
//checkpoint("00000 function ebid");
function ebid( id )
    {
    // debug_out( "functions", "function start ebid()");
    return document.getElementById(id) ||
	fatal("Cannot find element for id ["+id+"]");
    }

//////////////////////////////////////////////////////////////////////////
//	User has hit a help button.					//
//////////////////////////////////////////////////////////////////////////
var help_window;
//checkpoint("00000 function show_help");
function show_help( help_page )
    {
    var url = "/sto/help/" + help_page;

    // Cannot use ebid() because not finding help_id is not fatal.
    var p = document.getElementById('help_id');
    if( p )
	{
	p.src = url;
	p.style.display = "";
	}
    else
        {
	help_window = window.open( url, '_help' );
	help_window.focus();
	}

    return false;
    }

//////////////////////////////////////////////////////////////////////////
//	One of the onXXXX happened.  Figure out which.			//
//////////////////////////////////////////////////////////////////////////
var touchstart_at;
//checkpoint("00000 function help_event");
function help_event( e, help_page )
    {
    if( e.type == "contextmenu" )
        {
	show_help( help_page );
	if( e.preventDefault ) { e.preventDefault(); }
	e.stopImmediatePropagation();
	}
    else if( e.type == "touchstart" )
        {
	touchstart_at = new Date().getTime();
	}
    else if( e.type == "touchend"
		&& ((new Date().getTime()) - touchstart_at) > 2000 )
        {
	show_help( help_page );
	if( e.preventDefault ) { e.preventDefault(); }
	e.stopImmediatePropagation();	// Not exactly redundant!
	}
    }

//////////////////////////////////////////////////////////////////////////
//	User is done with the help page (which was in an iframe).	//
//	Just make it invisible.						//
//////////////////////////////////////////////////////////////////////////
//checkpoint("00000 function done_help");
function done_help()
    {
    (ebid('help_id')).style.display = "none";
    }


//////////////////////////////////////////////////////////////////////////
//	Draw a one-of prompt.						//
//////////////////////////////////////////////////////////////////////////
//checkpoint("00000 function oneof");
function oneof( asking, prompt_text, answers )
    {
    debug_out( "functions", "function start oneof()");
    var s = "<table border=1 class=fixedtable>"
        + "<tr><th width=100%>"+prompt_text+"</th></tr>";

    for( const a of answers )
        {
	var value = a;
	var txt = a;
	var color = "";
	if( typeof( a ) == "object" )
	    { value=a.value; txt=a.txt||a.value; color=a.color||""; }
	s += "<tr><td>"
	  +  "<input type=button style='background-color:"+color+"'"
	  +  " onClick='"+asking+"(\""+ value+"\");'"
	  +  " class=bigtext value='"+txt+"'/></td></tr>";
	}
    s += "</table>";
    (ebid("id_oneof_screen")).innerHTML = s;
    return lightup("oneof");
    }

//////////////////////////////////////////////////////////////////////////
//	Starting over, reset everything we've changed since the page	//
//	was loaded.							//
//////////////////////////////////////////////////////////////////////////
//checkpoint("00000 function reset_route");
function reset_route( arg )
    {
    debug_out( "functions", "function start reset_route()");
    if( arg == "no_reset" )
	{
	}
    else if( arg == "reset_route" )
	{
	current_stop = 0;
	display_order = new Array();
	for( var stop_number=0; stop_number<stops.length; stop_number++ )
	    {
	    stops[stop_number].status = "Untouched";
	    stops[stop_number].modified = 0;
	    stops[stop_number].notes = "";
	    stops[stop_number].odometer = "";
	    stops[stop_number].donation = "";
	    stops[stop_number].donation_type = "";
	    stops[stop_number].route_type = "Reimbursable";
	    stops[stop_number].distance_to = stops[stop_number].distance_ref;
	    stops[stop_number].time_to = stops[stop_number].time_ref;
	    stops[stop_number].route_from = stop_number - 1;
	    display_order.push( stop_number );
	    }
	last_route_response = 0;
	}
    else
	{
        return oneof("reset_route","Reset the route?", [
	    { value:"reset_route", txt:"Reset the route", color:"red" },
	    { value:"no_reset", txt:"Do not reset the route" } ] );
	}

    document.cookie=
	COOKIE_NAME+"=;expires="+new Date(0).toUTCString()+";path=/";
    lightup( "big", "/reset_route" );
    if( arg == "reset_route" ) { reroute(); }
    }

//////////////////////////////////////////////////////////////////////////
//	Create/update a cookie called COOKIE_NAME with everything we've	//
//	changed so the page can be safely reloaded.			//
//////////////////////////////////////////////////////////////////////////
var RECIPE =
	[ "status", "notes", "pickups", "modified", "odometer",
	  "donation", "donation_type", "route_type" ];
var SEP = '-!';
//checkpoint("00000 function bake_cookie");
function bake_cookie( called_from )
    {
    debug_out( "functions", "function start bake_cookie()");
    var dough = new Array( SECRET, current_stop );
    for( var stop_number=0; stop_number<stops.length; stop_number++ )
        {
	for( const v of RECIPE )
	    { dough.push( stops[stop_number][v]||"" ); }
	}
    dough.push(".");	// Something so last chunk not confused w/trailer

    d = new Date(0);
    d.setTime( d.getTime() + d.PAGE_LIFETIME );
    var v = encodeURIComponent(dough.join(SEP))
	+ ";SameSite=Lax;expires=" + d.toUTCString() + ";path=/";
    var c = COOKIE_NAME + "=" + v;
    // debug_out("cookies","Bake_cookie("+called_from+") with "+dough.length+" creates ["+c+"]");
    // document.cookie = c;
    //debug_out("flow","localStorage.setItem("+COOKIE_NAME+","+v+")");
    localStorage.setItem( COOKIE_NAME, v );
    }

//////////////////////////////////////////////////////////////////////////
//	Called when cookie found.  Eat it!  (interpret it)		//
//////////////////////////////////////////////////////////////////////////
//checkpoint("00000 function eat_cookie");
function eat_cookie( c )
    {
    debug_out( "functions", "function start eat_cookie()");
    var dough = c . split( SEP );
    debug_out("cookies","eat_cookie dough.length="+dough.length+", c = ["+c+"]");
    if( dough.shift() == SECRET )
	{	// Eat that cookie!
	current_stop = dough.shift();
	debug_out("cookies","Eating ["+dough.join(",")+"]");
	for( var stop_number=0; stop_number<stops.length; stop_number++ )
	    {
	    for( const v of RECIPE )
		{
		var from_dough = dough.shift();
	        debug_out("cookies","cookie["+stop_number+","+v+"]=["+(from_dough||"?")+"]");
		if( from_dough == undefined )
		    {
		    alert("Cook dough["+stop_number+","+v+"] is UNDEFINED!");
		    }
		stops[stop_number][v] = from_dough;
		}
	    }
	lightup( "big", "/eat_cookie" );
	return true;
	}
    return false;
    }

//////////////////////////////////////////////////////////////////////////
//	Look for the cookie after a reload.  If we can't find it, we're	//
//	starting over.							//
//////////////////////////////////////////////////////////////////////////
//checkpoint("00000 function find_cookie");
function find_cookie()
    {
    debug_out( "functions", "function start find_cookie()");
    var storage = localStorage.getItem( COOKIE_NAME );
    if( storage != undefined )
        {
	storage = decodeURIComponent(storage);
	eat_cookie( storage );
	return true;
	}
    else if( document.cookie )
	{
	for( const c of (decodeURIComponent(document.cookie)).split(';') )
	    {
	    if( /\s*(\w+)=(.*)/ms.test(c)
		&& RegExp.$1 == COOKIE_NAME
		&& eat_cookie( RegExp.$2 ) ) { return true; }
	    }
	}
    debug_out( "functions", "function find_cookie() done.");
    return false;	// No suitable cookie found, return hungry.
    }

//////////////////////////////////////////////////////////////////////////
//	Try to cut down on size of data being sent upstream.		//
//////////////////////////////////////////////////////////////////////////
//checkpoint("00000 function compact_string");
function compact_string( s )
    {
    debug_out( "functions", "function start compact_string()");
    return s;	// Or not!
    // https://cdn.jsdelivr.net/gh/pieroxy/lz-string/libs/lz-string.js ?
    }

//////////////////////////////////////////////////////////////////////////
//	Setup the variable map_order.					//
//	List of things we're going to display on the map.		//
//	* CAN BE A SUBSET OF ALL STOPS or EVEN JUST ONE STOP *		//
//	Would rather this be a local variable passed in through each	//
//	routine but we needs to be seen by callback handlers.		//
//////////////////////////////////////////////////////////////////////////
var map_order;
//checkpoint("00000 function setup_map_order");
function setup_map_order( first_stop, last_stop )
    {
    debug_out( "functions", "function start setup_map_order()");
    var stop_number;
    for( stop_number=0; stop_number<stops.length; stop_number++ )
        {
	stops[stop_number].pretty =
	    stops[stop_number].name + ", " + stops[stop_number].phone;
	// if( stops[stop_number].coords )
	//     { stops[stop_number].coords.replace( /:/, "," ); }
	}

    map_order = new Array();

    if( stops[0].modified && current_position && current_position.latitude )
	{
	// We don't make our current position the start of the route if
	// we haven't gotten to the first stop, else the re-routing logic
	// will potentially change order of place where we pick up food
	// to some place other than #1.
	map_order.push( -1 );
	}
    for( stop_number=first_stop; stop_number<=last_stop; stop_number++ )
	{
	if( need_to_visit(stop_number) ) { map_order.push( stop_number ); }
	}
    }

//////////////////////////////////////////////////////////////////////////
//	Return string form of coordinates (in whatever form they came)	//
//////////////////////////////////////////////////////////////////////////
//checkpoint("00000 function coord_string");
function coord_string( c )
    {
    debug_out( "functions", "function start coord_string()");
    if( ! c )
	{ return "UNSET"; }
    else if( c.latitude )
	{ return c.latitude + "," + c.longitude; }
    else
	{ return "" + c; }
    }

//////////////////////////////////////////////////////////////////////////
//	Return true if two coordinates are the same.			//
//////////////////////////////////////////////////////////////////////////
//checkpoint("00000 function same_pos");
function same_pos( p0, p1 )
    {
    debug_out( "functions", "function start same_pos()");
    return ( coord_string(p0) == coord_string(p1) );
    }

//////////////////////////////////////////////////////////////////////////
//	Many of the mappers need separate arrays for name, address and	//
//	GPS coordinates.  Avoids replicating code all over the place.	//
//	Note for mapping purposes (only), we discard addresses or	//
//	coordinates we have seen before.				//
//////////////////////////////////////////////////////////////////////////
//checkpoint("00000 function split_out");
function split_out(for_platform)
    {
    debug_out( "functions", "function start split_out()");
    var latlong_string = for_platform.toLowerCase() + " uses latlong";

    var pref_logic = DEBUG.pref_ctl.value;
    if( ! pref_logic )
	{		// Auto
	if( for_platform=="XGoogle" )
	    { pref_logic = "Coordinates"; }
	else
	    { pref_logic = "Addresses"; }
	}

    var namelist	=new Array();
    var preflist	=new Array();
    var addrlist	=new Array();
    var cordlist	=new Array();
    debug_out("split_out","Map order is:\n    "+map_order.join("\n    "));
    for( var stop_number=0; stop_number<map_order.length; stop_number++ )
	{
	var order_ind = map_order[stop_number];
	// debug_out("url","map_order["+stop_number+"] is ["+order_ind+"]");
	var nr = "";
	if( order_ind < 0 )
	    {
	    debug_out("flow","stop_number="+stop_number+", order_ind="+order_ind
	      +"\nMap order is:\n    "+map_order.join("\n    "));
	    // namelist.push( "Current position" );
	    // addrlist.push( "Current position" );
	    // cordlist.push( coord_string(current_position) );
	    // debug_out("url","Pushing latlong_string ["+latlong_string+"]");
	    continue;
	    }
	else
	    {
	    namelist.push( stops[order_ind].pretty  );
	    addrlist.push( stops[order_ind].address );
	    cordlist.push( stops[order_ind].coords  );
	    }
	preflist.push(
	    ( pref_logic=="Coordinates"
	    ? cordlist[cordlist.length-1]||addrlist[addrlist.length-1]
	    : addrlist[addrlist.length-1] ) );
	if( DEBUG.flow.value )
	    {
	    var SP2 = "\n  ";
	    var SP4 = "\n    ";
	    var to_print =
		"split_out("+for_platform+") with order_ind="
		+ order_ind
		+ SP2+"namelist:"+SP4+namelist.join(SP4)
		+ SP2+"preflist:"+SP4+preflist.join(SP4)
		+ SP2+"addrlist:"+SP4+addrlist.join(SP4)
		+ SP2+"cordlist:"+SP4+cordlist.join(SP4)
		;
	    debug_out( "flow", to_print );
	    }
	}
    return {namelist,preflist,addrlist,cordlist};
    }

//////////////////////////////////////////////////////////////////////////
//	Allow driver to specify how many stops to plot.			//
//	Default to as many as possible.					//
//////////////////////////////////////////////////////////////////////////
//checkpoint("00000 function how_many_stops");
function how_many_stops( namelist, max_stops, starting_from, last_stop )
    {
    var proposed_num_stops = last_stop - starting_from + 1;
    var stops_after = last_stop - starting_from;
    debug_out("flow","HMS:  namelist=["+namelist.join(":")+"]\nmax_stops="+max_stops+" starting_from="+starting_from+" last_stop="+last_stop);
    if( stops_after < 1 )
        { return starting_from; }
    else
	{
	var quest;
	var ret;
	var maxval;

	if( proposed_num_stops <= max_stops )
	    { maxval = proposed_num_stops; }
	else
	    { maxval = max_stops; }
	quest = ( proposed_num_stops==1
	    	    ? "XL(The following stop remains):\n    "
		    : ("XL(The following) "
		    	+proposed_num_stops+" XL(stops remain):\n    ") )
	    +	namelist.join("\n    ") + "\n";
	quest = quest
	    +	"XL(Program GPS with how many stops [1 to) "
	    +	maxval + "]?";
	var msg = "";
	do  {
	    ret = ( maxval<=0 ? "1" : prompt( msg + quest, maxval ) );
	    if( ! /^\d+$/.test(ret) )
	        { msg = "XL(Number of stops must be a decimal integer.)\n\n"; }
	    else
	        {
		ret -= 0;	// Convert from string to int
		if( ret < 1 )
		    { msg = "XL(Number of stops must be at least 1.)\n\n"; }
		// else if( ret > maxval )
		else if( ret > 30 )
		    { msg = "XL(Number of stops can be no more than) "+maxval+".\n\n"; }
		else
		    { msg = ""; }
		}
	    } while( msg );
	return starting_from + ret - 1;
	}
    }

//////////////////////////////////////////////////////////////////////////
//	Given a list of addresses (and names), remove redundancies	//
//	and bound it by whatever limitation environment requires.	//
//////////////////////////////////////////////////////////////////////////
//checkpoint("00000 function navigable_list");
function navigable_list( preflist, namelist, max_stops )
    {
    var inds = unique_stops( preflist );

    if( DEBUG.flow.value )
	{
	var output = "preflist.length = " + preflist.length;
	for( var i=0; i<preflist.length; i++ )
	    { output += ("\n" + i + ": " + preflist[i]); }
	debug_out("flow",output);
	}
    var preflist_compressed = selected_inds( preflist, inds );
    var namelist_compressed = selected_inds( namelist, inds );
    // alert("namelist_compressed=["+namelist_compressed.join("//")+"]");

    var endstop = how_many_stops( namelist_compressed, max_stops, 0, preflist_compressed.length-1 )
    preflist_compressed = preflist_compressed.slice( 0, endstop+1 );
    namelist_compressed = namelist_compressed.slice( 0, endstop+1 );
    return { preflist_compressed, namelist_compressed };
    }

//////////////////////////////////////////////////////////////////////////
//	Return a string escaped properly so it can be used as a URL.	//
//////////////////////////////////////////////////////////////////////////
//checkpoint("00000 function safe_url");
function safe_url( str )
    {
    debug_out( "functions", "function start safe_url()");
    str = str.replace(/United States,.*/,"United States");
    // str = str.replace(/[^A-Za-z0-9\.\- ]+/g,"_");
    str = str.replace(/ /g,"+");
    return str;
    }

//////////////////////////////////////////////////////////////////////////
//	Get *ALL* properties from an object including inherited ones.	//
//////////////////////////////////////////////////////////////////////////
//checkpoint("00000 function list_all_properties");
function list_all_properties(o)
    {
    debug_out( "functions", "function start list_all_properties()");
    var ret = new Array();
    for( ; o !== null; o=Object.getPrototypeOf(o) )
	{ ret = ret.concat( Object.getOwnPropertyNames(o) ); }
    return ret;
    }

//////////////////////////////////////////////////////////////////////////
//	Return contents of variable as string (the recursive part).	//
//	Hopefully only used for debugging.				//
//////////////////////////////////////////////////////////////////////////
var hash_to_string_lines;
//checkpoint("00000 function hash_to_string_recurse");
function hash_to_string_recurse( comflag, indent, txt, v )
    {
    debug_out( "functions", "function start hash_to_string_properties()");
    var t = typeof(v);
    var vartxt = comflag + '"'+txt+'"';
    // var typetxt = " " + t;
    var typetxt = "";
    var valtxt = '"'+v+'"';

    if( t == "object" )
        {
	if( txt == "" )
	    { hash_to_string_lines.push( indent + "{" ); }
	else
	    { hash_to_string_lines.push( indent + vartxt + typetxt + ":{" ); }
	// for( const k in v )
	var needcomma = "";
	for( const k of list_all_properties(v) )
	    {
	    if( k != "__proto__" )
	        {
		hash_to_string_recurse( needcomma, indent+"\t", k, v[k] );
		needcomma = ",";
		}
	    }
	hash_to_string_lines.push( indent + "}" );
	}
    else if( t != "function" )
	{
	//valtxt = valtxt.replace(/\n/g,'\\n"+'+indent+'\t'+'"');
	valtxt = valtxt.replace(/\r/g,'');
	valtxt = valtxt.replace(/\n/g,'\\n');
	hash_to_string_lines.push(indent + vartxt + typetxt + ":" + valtxt);
	}
    else if( ! /native code/.test(v) )
	{ hash_to_string_lines.push(indent + vartxt + typetxt + ":" + valtxt); }
    }

//////////////////////////////////////////////////////////////////////////
//	Return contents of variable as string.				//
//////////////////////////////////////////////////////////////////////////
//checkpoint("00000 function hash_to_string");
function hash_to_string( txt, v )
    {
    debug_out( "functions", "function start hash_to_string()");
    hash_to_string_lines = new Array();
    hash_to_string_recurse( "", "", txt, v )
    for( var i=1; i<hash_to_string_lines.length; i++ )
	{
	if( /^\t*,/.test(hash_to_string_lines[i]) )
	    {
	    hash_to_string_lines[i] = hash_to_string_lines[i].replace(/,/,"");
	    hash_to_string_lines[i-1] += ",";
	    }
	}
    return( hash_to_string_lines.join("\n") );
    }

%%MAPPERSJS%%

//////////////////////////////////////////////////////////////////////////
//	Return true if stop specified stop.				//
//////////////////////////////////////////////////////////////////////////
//checkpoint("00000 function need_to_visit");
function need_to_visit( stopnum )
    {
    // debug_out( "functions", "function start need_to_visit()");
    return(	stops[stopnum].status=="Untouched"
	||	stops[stopnum].status=="Unvisited" );
    }

//////////////////////////////////////////////////////////////////////////
//	Put debugging information in the debugging sub window.		//
//////////////////////////////////////////////////////////////////////////
//checkpoint("00000 function position_trail");
function position_trail()
    {
    debug_out( "functions", "function start position_trail()");
    // if( DEBUG.position.value )
    var s = "<center><table bgcolor='#ffffc0' border=1 style='border-collapse:collapse;'>"
		+ "<tr><th>Ind</th><th>Where</th><th>When</th></tr>\n";
    var l = route_history.length;
    var do_dots = false;
    for( var i=0; i<l; i++ )
	{
	if( i<3 || i>l-5 )
	    {
	    var d = new Date(route_history[i].when);
	    s += "<tr>"
		+ "<td align=right>" + i + "</td>"
		+ "<td>" + coord_string(route_history[i]) + "</td>"
		+ "<td>" + d.toUTCString() + "</td></tr>\n";
		// + "<td>" + route_history[i].when + "</td></tr>\n";
	    do_dots = true;
	    }
	else if( do_dots )
	    {
	    s += "<tr><th colspan=3>...</th></tr>\n";
	    do_dots = false;
	    }
	}
    s += "</table></center>\n";
    (ebid("position_trail")).innerHTML = s;
    }

//////////////////////////////////////////////////////////////////////////
//	If current position has changed from the last, push position.	//
//	Else if current position is same as previous two, update time	//
//	on last.  Else push current position (again) but with new time.	//
//									//
//	Thus, if we stay some place a long time, we'll have when we	//
//	arrived, and right before when we leave but not all times in	//
//	between.							//
//////////////////////////////////////////////////////////////////////////
//checkpoint("00000 function drop_a_pin");
function catch_drop_a_pin()
    {
    var ret_drop_a_pin;
    try
	{ var ret_drop_a_pin = real_drop_a_pin(); }
      catch(estack)
	{ alert("XL(drop_a_pin failed):\n" + estack.stack ); }
    return ret_drop_a_pin;
    }

function drop_a_pin()
    {
    debug_out( "functions", "function start drop_a_pin()");
    if( current_position )
	{
        var d = new Date();
	var now = d.getTime();
	var l = route_history.length;
	if( l >= 2 )
	    {
	    var pos = route_history[ l-1 ];
	    if( same_pos( pos, current_position ) )
	        {
		pos = route_history[ l-2 ];
	        if( same_pos( pos, current_position ) )
		    {
		    route_history[ l-1 ].when = now;
		    position_trail();
		    // debug_out("flow","We are not moving, l-1="+(l-1)+", now="+route_history[l-1].when);
		    return;
		    }
		}
	    }
	// debug_out("flow","We are moving, now="+now);
	route_history.push(
	    {
	    latitude:	current_position.latitude,
	    longitude:	current_position.longitude,
	    when:	now
	    } );
	position_trail();
	}
    }

//////////////////////////////////////////////////////////////////////////
//	Pretend the car/iphone is moving.				//
//////////////////////////////////////////////////////////////////////////
//checkpoint("00000 function move_some");
function move_some()
    {
    debug_out( "functions", "function start move_some()");
    for( const axis of [ "latitude", "longitude" ] )
	{
	TEST_POSITION[axis]+=( Math.random()*JITTER[axis] - JITTER[axis]/2.0 );
	current_position[axis] = TEST_POSITION[axis];
	}
    // debug_out("flow","New position ["+current_position.latitude+","+current_position.longitude+"]");
    drop_a_pin();
    }

//////////////////////////////////////////////////////////////////////////
//	Get the current position
//////////////////////////////////////////////////////////////////////////
var last_current_position_callback;
//checkpoint("00000 function get_current_position");
function get_current_position( current_position_callback )
    {
    debug_out( "functions", "function start get_current_position()");
    last_current_position_callback = current_position_callback;
    if( geoposition_timer >= 0 ) { clearTimeout( geoposition_timer ); }
    navigator.geolocation.getCurrentPosition
	(
	function(position)
	    {
	    current_position =
		( ( DEBUG.position.value || ! position.coords.latitude )
		?	TEST_POSITION
		:	{    latitude:		position.coords.latitude,
			     longitude:		position.coords.longitude } );
	    debug_out("position","Position="+position.coords.latitude+","+position.coords.longitude);
	    drop_a_pin();
	    if( last_current_position_callback )
		{last_current_position_callback();}
	    geoposition_timer = setTimeout
		(
		function() { get_current_position(0); },
		time_constant.POSITION_POLL
		);
	    },
	function(evt)
	    {
//	    current_position = TEST_POSITION;
//	    debug_out("flow","getCurrentPosition failed:  "+evt.message
//		+"\nUsing test position");
//	    if( last_current_position_callback )
//		{last_current_position_callback();}
	    geoposition_timer = setTimeout
		(
		function() { get_current_position(0); },
		time_constant.POSITION_POLL
		);
	    },
	{ enableHighAccuracy:true, timeout:GPS_TIMEOUT }
	);
    debug_out( "functions", "function get_current_position returning()");
    }

//////////////////////////////////////////////////////////////////////////
//	Something has changed and user wants to figure out what best	//
//	route should be now.  For now, display new map.			//
//////////////////////////////////////////////////////////////////////////
//checkpoint("00000 function reroute");
function reroute()
    {
    debug_out( "functions", "function start Reroute()");
    if( 0 && need_to_visit(0) )
	{	// If we haven't been to the first stop, go there first
	setup_map_order( 0, stops.length-1 );
	start_getting_Mapquest_route(true,true);
	}
    else
	{	// If we have been to the first stop, presumably we have
		// all the goods to distribute so we need to figure out
		// the best route based on where we are NOW.
	get_current_position(
	    function()
	        {
		setup_map_order( 0, stops.length-1 );
		start_getting_Mapquest_route(true,true);
		});
	}
    }

//////////////////////////////////////////////////////////////////////////
//	Returns elements array in first specified in second array.	//
//////////////////////////////////////////////////////////////////////////
//checkpoint("00000 function selected_inds");
function selected_inds( arr, arrinds )
    {
    var ret = new Array();
    for( var i=0; i<arrinds.length; i++ )
        {
	ret.push( arr[ arrinds[i] ] );
	}
    // alert("selected_inds returns ["+ret.join(",")+"]");
    return ret;
    }

//////////////////////////////////////////////////////////////////////////
//	Return the indices of the address and coordinate lists that	//
//	are actually unique.  First and last are always unique as	//
//	driver's routes are circular.					//
//////////////////////////////////////////////////////////////////////////
//checkpoint("00000 function unique_stops");
function unique_stops( addrlist )
    {
    var ret = new Array();
    var last_val = -2;	// Not going to happen naturally
    for( var i=0; i<addrlist.length; i++ )
        {
	if( addrlist[i] != last_val )
	    {
	    ret.push( i );
	    last_val = addrlist[i];
	    }
	}
    debug_out("flow","unique_stops("+addrlist.join("\n")+") returns ["+ret.join(",")+"]");
    return ret;
    }

//////////////////////////////////////////////////////////////////////////
//	Figure out which mapper we're using it and invoke it.		//
//////////////////////////////////////////////////////////////////////////
//checkpoint("00000 function map_dispatcher");
function map_dispatcher( handler )
    {
    debug_out( "functions", "function start map_dispatcher()");
    debug_out( "flow", "map_dispatcher("+handler+")");
    if( map_handlers[handler] )
	{ return (map_handlers[handler])(); }

    debug_out( "flow", "map_dispatcher called with " + (handler?handler:"UNDEFINED") );
    }

//////////////////////////////////////////////////////////////////////////
//	Create arrays to call an appropriate system dependent route	//
//	mapper, figure out which one to call, and call it.		//
//////////////////////////////////////////////////////////////////////////
var goto_map_ind;
var goto_map_handler;
//checkpoint("00000 function goto_map_callback");
function goto_map_callback()
    {
    debug_out( "functions", "function start goto_map_callback()");
    var handler = goto_map_handler;
    var save_map_order = map_order;
    var ind = goto_map_ind;
    if( ind < 0 )
        { setup_map_order( 0, stops.length-1 ); }
    else
        { setup_map_order( ind, stops.length-1 ); }

    debug_out("flow","goto_map_callback(handler="+handler+"), ROUTE_HANDLER="+ROUTE_HANDLER+", DEST_HANDLER="+DEST_HANDLER+", len="+map_order.length);
    var use_mapper =
        ( handler		? handler
	: map_order.length <= 2	? DEST_HANDLER
	:			  DEST_HANDLER );
    var url = map_dispatcher( use_mapper );
    // debug_out( "url", "url=["+url+"]" );

    if( url )
	{
	debug_out( "flow" || "url", "url="+url );
	var win = window.open( url, "map_window" );
	if( win )
	    { win.focus(); }
	// window.focus();
	}
    map_order = save_map_order;
    return true;
    }

//checkpoint("00000 function goto_map");
function goto_map( ind, handler )
    {
    debug_out( "functions", "function start goto_map()");
    if( DEBUG.dest_handler.value )
	{ DEST_HANDLER = DEBUG.dest_handler.value; }
    if( DEBUG.route_handler.value )
	{ ROUTE_HANDLER = DEBUG.route_handler.value; }
    debug_out( "flow",
	"DH="+DEST_HANDLER+".  Debug="+DEBUG.dest_handler.value+".");
    if( ind < 0 && ! handler  )
	{
	// debug_out( "flow", "Not Ignoring...");
	// return false;
	}
    goto_map_ind = ind;
    goto_map_handler = handler;
    get_current_position( function() { goto_map_callback(); } );
    return true;
    }

//////////////////////////////////////////////////////////////////////////
//	Invoked when user wants to call person at stop.			//
//////////////////////////////////////////////////////////////////////////
//checkpoint("00000 function make_call");
function make_call( ind )
    {
    debug_out( "functions", "function start make_call()");
    document.location.href = "tel:" + stops[ind].phone;
    }

//////////////////////////////////////////////////////////////////////////
//	Invoked when user wants to call person at stop.			//
//////////////////////////////////////////////////////////////////////////
//checkpoint("00000 function make_text");
function make_text( ind )
    {
    debug_out( "functions", "function start make_text()");
    document.location.href = "sms:" + stops[ind].phone;
    }

//////////////////////////////////////////////////////////////////////////
//	Call to emphasize or not emphasize (and colorize) the specified	//
//	id.  Used to show which stop on the route we're at.		//
//////////////////////////////////////////////////////////////////////////
//checkpoint("00000 function emphasize");
function emphasize( elemid, emphasis_flag, col )
    {
    debug_out( "functions", "function start emphasize()");
    var p = (ebid(elemid)).style;
    p.backgroundColor = col;

//	Turns out the following is not that useful.  Color is more useful.
//	p.fontWeight	= ( emphasis_flag ? "bold"	: "" );
//	p.fontStyle	= ( emphasis_flag ? "italic"	: "" );
    }

//////////////////////////////////////////////////////////////////////////
//	Assume we're somewhere in 50 United States			//
//////////////////////////////////////////////////////////////////////////
//checkpoint("00000 function short_address");
function short_address( a )
    {
    // debug_out( "functions", "function start short_address()");
    return	( /(.*,\w\w),(|\d\d\d\d\d|\d\d\d\d\d-\d\d\d\d),(US|United States)/.test(a)
		? RegExp.$1 : a );
    }

//////////////////////////////////////////////////////////////////////////
//	Return a link which goes nowhere.				//
//////////////////////////////////////////////////////////////////////////
//checkpoint("00000 function null_link");
function null_link( txt )
    {
    // debug_out( "functions", "function start null_link()");
    return "<a href='javascript:void(0);'>" + txt + "</a>";
    }

//////////////////////////////////////////////////////////////////////////
//	Return list of steps in most useful order.			//
//////////////////////////////////////////////////////////////////////////
var last_display_order;
//checkpoint("00000 function get_display_order");
function get_display_order()
    {
    debug_out( "functions", "function start get_display_order()");
    var already_done = new Array();
    var to_route_to = new Array();

    if( last_display_order ) { return last_display_order; }

    display_order = new Array();

    for( var stop_number=0; stop_number<stops.length; stop_number++ )
	{
	stops[stop_number].time_to = stops[stop_number].time_ref;
	stops[stop_number].distance_to = stops[stop_number].distance_ref;
	stops[stop_number].route_from = stop_number - 1;
	if( need_to_visit( stop_number ) )
	    { to_route_to.push(stop_number); }
	else
	    { already_done.push(stop_number); }
	}

    if( already_done.length > 0 )
        {
	for( const stop_ind of already_done )
	    {
	    stops[stop_ind].time_to = undefined
	    stops[stop_ind].distance_to = undefined
	    stops[stop_ind].route_from = undefined;
	    }
	display_order = display_order.concat(
	    already_done.sort(
		function(a,b)
		    { return stops[a].modified - stops[b].modified; }
		)
	    );
	}

    if( ! last_route_response
     || last_route_response.route.locationSequence.length <= 0 )
        { display_order = display_order.concat( to_route_to ); }
    else
        {
	//for( const sequence_ind of last_route_response.route.locationSequence )
	var last_from = -1;
	for( const sequence_ind in last_route_response.route.locationSequence )
	    {
	    var map_order_ind =
	        last_route_response.route.locationSequence[sequence_ind];
	    var stop_ind = map_order[ map_order_ind ];
 	    // debug_out( "flow", "sequence_ind="+sequence_ind+", map_order_ind="+map_order_ind+", stop_ind="+stop_ind+", last_from="+last_from+", sequence_length="+last_route_response.route.locationSequence.length+", legs.length="+last_route_response.route.legs.length);
	    if( stop_ind >= 0 )
	        {
		display_order.push( stop_ind );
		stops[stop_ind].time_to =
		    ( sequence_ind>0
		    ? last_route_response.route.legs[sequence_ind-1].time
		    : "" );
		stops[stop_ind].distance_to =
		    ( sequence_ind>0
		    ? last_route_response.route.legs[sequence_ind-1].distance
		    : "" );
		stops[stop_ind].route_from = last_from;
		// debug_out( "flow", "Setting "+stops[stop_ind].name+".route_from to "+stops[stop_ind].route_from);
		last_from = stop_ind;
		}
	    }
	}

    last_display_order = display_order;
    return display_order;
    }

//////////////////////////////////////////////////////////////////////////
//	Return value displayed to nearest 0.1				//
//////////////////////////////////////////////////////////////////////////
//checkpoint("00000 function distance_string");
function distance_string(d)
    {
    debug_out( "functions", "function start distance_string()");
    return ( d ? Math.floor(d*10.0+0.5)/10.0 : "?" );
    }

//////////////////////////////////////////////////////////////////////////
//	Return HH:MM:SS from a javascript time.				//
//////////////////////////////////////////////////////////////////////////
//checkpoint("00000 function time_string");
function time_string(t)
    {
    debug_out( "functions", "function start time_string()");
    return ( t ? new Date(1000*t).toISOString().substr(11,8) : "?" );
    }

//////////////////////////////////////////////////////////////////////////
//	Return name of stop by stop number.				//
//////////////////////////////////////////////////////////////////////////
//checkpoint("00000 function stop_string");
function stop_string( n )
    {
    debug_out( "functions", "function start stop_string()");
    // return	( (typeof(n)=='undefined'||n=="")	? "?"
    return	( typeof(n)=='undefined'		? ""
		: n < 0					? "start"
		:					stops[n].name );
    }

//////////////////////////////////////////////////////////////////////////
//	Set position to coordinates specified (instead of whatever GPS	//
//	says) or if they are already that, let them float again.	//
//////////////////////////////////////////////////////////////////////////
//checkpoint("00000 function set_test_pos");
function set_test_pos( new_coords )
    {
    debug_out( "functions", "function start set_test_pos()");
    var old_test_position = coord_string( TEST_POSITION );
    if( same_pos( TEST_POSITION, new_coords ) )
	{ TEST_POSITION = 0; }
    else
	{ TEST_POSITION = new_coords; }
    debug_out( "flow", "old TEST_POSITION="+old_test_position
	+ ", new_position="+coord_string( new_coords )
	+ ", TEST_POSITION now = "+coord_string( TEST_POSITION )
	+ "." );
    }

//////////////////////////////////////////////////////////////////////////
//	User has found a good parking place, remember the coordinates	//
//	of it.								//
//////////////////////////////////////////////////////////////////////////
//checkpoint("00000 function park");
function park( e, flag )
    {
    var msg =
        ( flag
        ? "Best coordinates at " + current_position.latitude + "," + current_position.longitude
	: "" );
    var res = stops[current_stop].notes || "";
    if( ! res )
        { res = msg; }
    else if( /Best coordinates/.test(res) )
        {
	const sands = /Best coordinates at [0-9,\.\-]*.*/;
	res = res.replace( sands, msg );
	}
    else
	{ res += ( "\n" + msg ); }
    (ebid("id_patron_issue_value")).value = res;
    stops[current_stop].notes = res;
    e.preventDefault();
    e.stopPropagation();
    update_screen("/park");
    return false;
    }

//////////////////////////////////////////////////////////////////////////
//	Set all the attributes we change for all of the screens.	//
//	Note that this does not choose which screen we happen to be	//
//	showing.							//
//////////////////////////////////////////////////////////////////////////
//checkpoint("00000 function real_update_screen");
function real_update_screen( called_from )
    {
    debug_out( "functions", "function start update_screen()");
    var active = stops[current_stop];
    if( active )
	{
	for( const fld of ["ind","name"] )
	    {
	    (ebid("id_"+fld)).innerHTML=(active[fld]||"");
	    }
	(ebid("id_time_to")).innerHTML =
	    ( !active.time_to ? "" : time_string(active.time_to) )
	 // +  ( !active.time_ref ? "" : ' ('+time_string(active.time_ref)+')')
	    ;
	// debug_out( "flow", "stops["+active.name+"].route_from=" + stop_string(active.route_from))
	(ebid("id_distance_to")).innerHTML =
	    ( !active.distance_to ? "" : distance_string( active.distance_to ) )
	 // +  ( !active.distance_ref ? "" : " ("+distance_string(active.distance_ref)+")" )
	 +  ( !active.distance_to ? "" : " XL(miles from) " )
	 +  stop_string(active.route_from)
	     ;
	(ebid("id_phone")).innerHTML = active.phone;
	var addr_to_display = short_address( active.addrtxt );
	(ebid("id_addrtxt")).innerHTML = addr_to_display;
	var txt =
	    ( active.note ? active.note.replace(/\n/g,"<br>")+"<br>" : "" ) +
	    ( active.notes ? active.notes.replace(/\n/g,"<br>") : "" );
	(ebid("id_patron_issue")).innerHTML =
	    ( txt ? txt : "XL(Create issue)" ) +
	    ( /Best coordinates at/.test(txt)
		? "<br><input type=button value='Exclude parking location' onClick='park(event,0);'>"
		: "<br><input type=button value='Include parking location' onClick='park(event,1);'>" );
	(ebid("id_prefs")).innerHTML =
	    active.prefs.replace(/&lt;/g,'<').replace(/&gt;/g,'>').replace(/&sbquo;/g,"'");
	(ebid("id_status")).innerHTML =
	    ( ! active.status
		?	"XL(Set status)"
	    : (active.status=="Unvisited" || active.status=="Untouched")
		?	active.status+" - XL(set status)"
	    :		active.status );
	(ebid("id_odometer")).innerHTML
	    = (active.odometer?("Odometer at "+active.odometer):"XL(Note odometer)");
	(ebid("id_donation")).innerHTML
	    = (active.donation?("Donation of $"+active.donation+" "+active.donation_type):"XL(Create donation)");
	(ebid("id_route_type")).innerHTML
	    = (active.route_type?("Route type of "+active.route_type):"XL(Select route type)");

	if( current_stop==undefined )
	    { alert("XL(Current_stop is not defined.)"); }
	else if( stops[current_stop]==undefined )
	    { alert("stops[current_stop="+current_stop+"] XL(is not defined.)"); }
	else if( stops[current_stop].status==undefined )
	    { alert("stops[current_stop="+current_stop+"].status XL(is not defined.)"); }

//	(ebid("id_small_screen")).style.backgroundColor =
	document.body.style.background =
	    STATES[ stops[current_stop].status ].color;

	for( const stnm of STATES.names )
	    {
	    (ebid(stnm)).style.backgroundColor = STATES[stnm].color;
	    var idlist = document.querySelectorAll('[id^='+stnm+'_]')
	    for( ps of idlist )
		{ ps.style.backgroundColor = STATES[stnm].color; }
	    // { emphasize( stnm, active.status == stnm, STATES[stnm].color ); }
	    }
	}
    var id_big_screen_inset = new Array(
        "<table frame=box cellspacing=0 cellpadding=2>");

    var st;
    for( const stop_number of get_display_order() )
	{
	if( stop_number==undefined )
	    { alert("XL(stop_number is not defined.)"); }
	else if( stops[stop_number]==undefined )
	    { alert("stops[stop_number="+stop_number+"] XL(is not defined.)"); }
	else if( stops[stop_number].status==undefined )
	    { alert("stops[stop_number="+stop_number+"].status XL(is not defined.)"); }
	st = stops[stop_number].status;
	id_big_screen_inset.push(
	    "<tr bgcolor='", STATES[st].color, "' id=tr", stop_number,
		" onClick='set_active(", stop_number, ", 0 );'>", 
	    //"<td align=right valign=top>", stops[stop_number].ind, "</td>", 
	    "<td style='border-bottom:1px solid' align=right valign=top>",
		// stop_number,
		// " t=", time_string( stops[stop_number].time_to ),
		// " d=", distance_string( stops[stop_number].distance_to ),
		// " f=", stops[stop_number].route_from,
		( ! DEBUG.debug.value ? "" :
		    "<input type=button onClick='set_test_pos(\""+stops[stop_number].coords+"\");' value='" ),
	        ( stop_number==current_stop ? "&rarr;" : "" ),
		( ! DEBUG.debug.value ? "" :
		    "'>" ),
		"</td>", 
	    "<th valign=top align=left style='border-bottom:1px solid;qwhite-space: nowrap;'>",
	        // "<button style='width:100%; height:100%; border-radius:1px; text-align:left;'>",
		"<a href='javascript:'>",
		stops[stop_number].name,
		//"</button>",
		"</a>",
		"</th>",
	    "<th valign=top align=left style='border-bottom:1px solid;qwhite-space: nowrap;' onClick='make_call(",stop_number,");'>", 
	    null_link(stops[stop_number].phone), "</th>", 
	    "<th style='border-bottom:1px solid' valign=top align=left onClick='goto_map(",stop_number,");'>", 
	    null_link(short_address(stops[stop_number].address)), "</th>", 
	    "</tr>" );
	// emphasize( "tr"+i, i==current_stop, STATES[st].color );
	}
    id_big_screen_inset.push("</table>");

    (ebid("id_big_screen_inset")).innerHTML =
	id_big_screen_inset.join("");

    setdisplay("go_live_id",0);
    setdisplay("map_opts_id",1);
    setdisplay("reset_id",1);

    if( current_stop >= 0 ) { draw_pickups(); }

    bake_cookie( called_from+"/bake_cookie" );	// If something changed, remember it for next load
    debug_out( "functions", "function end update_screen()");
    return true;
    }

//checkpoint("00000 function update_screen");
function update_screen( called_from )
    {
    var update_screen_return;
    try
	{ update_screen_return = real_update_screen(called_from); }
      catch(estack)
	{ alert("XL(update_screen failed):\n" + estack.stack ); }
    return update_screen_return;
    }

//////////////////////////////////////////////////////////////////////////
//	Short hand for setting a display element on or off.		//
//////////////////////////////////////////////////////////////////////////
//checkpoint("00000 function setdisplay");
function setdisplay( name, flag )
    {
    debug_out( "functions", "function start setdisplay()");
    (ebid(name)).style.display = ( flag ? "" : "none" );
    }

//////////////////////////////////////////////////////////////////////////
//	At the end of user's input, if this variable is set, change	//
//	the focus.							//
//////////////////////////////////////////////////////////////////////////
var should_be_focused;
//checkpoint("00000 function check_focus");
function check_focus()
    {
    debug_out( "functions", "function start check_focus()");
    if( should_be_focused )
	{
	var p = document.getElementById(should_be_focused);
	if( p )
	    {
	    // debug_out("flow","XL(Trying again to focus on) "+should_be_focused);
	    p.focus();
	    should_be_focused = 0;
	    }
	}
    }

//////////////////////////////////////////////////////////////////////////
//////////////////////////////////////////////////////////////////////////
var focus_timer;
//checkpoint("00000 function set_focus");
function set_focus( id_name )
    {
    debug_out( "functions", "function start set_focus()");
    if( id_name )
	{
	var p = document.getElementById(id_name);
	if( p )
	    {
	    // debug_out( "flow", "XL(Trying initial setfocus)...");
	    p.focus();
	    }
	should_be_focused = id_name;
	focus_timer = setTimeout( check_focus, 800 );
	// debug_out( "flow", "XL(Focus verify scheduled.)");
	}
    }

//////////////////////////////////////////////////////////////////////////
//	Make sure the screens are all up-to-date, light up named one	//
//	and darken all the others.					//
//////////////////////////////////////////////////////////////////////////
//checkpoint("00000 function lightup");
function lightup( tolight, called_from )
    {
    debug_out( "functions", "function start lightup()");
    update_screen( called_from + "/lightup" );

    for( const idname of SCREENS )
        {
	setdisplay( "id_"+idname+"_screen", tolight==idname );
	}
    set_focus("id_"+tolight+"_value");
    return true;
    }

//////////////////////////////////////////////////////////////////////////
//	Smart prompt for a field.					//
//////////////////////////////////////////////////////////////////////////
//checkpoint("00000 function get_field");
function get_field( field, constraint, constraint_text )
    {
    debug_out( "functions", "function start get_field()");
    var msg = "";
    var ans = stops[current_stop][field] || "";
    do  {
	ans = prompt( msg + "Enter "+field+":", ans );
	msg = "Must be blank or in "+constraint_text+" format.\n\n";
	} while( ans!="" && ! constraint.test(ans) )
    stops[current_stop][field] = ans;
    }

//////////////////////////////////////////////////////////////////////////
//	Set the current stop's status to the argument.			//
//////////////////////////////////////////////////////////////////////////
//checkpoint("00000 function set_status");
function set_status( new_status, already_displaying )
    {
    debug_out( "functions", "function start set_status()");
    if( new_status == "Untouched" )
	{
	// var err = new Error();
	// debug_out( "flow", "XL(Trace):  "+err.stack);
	return;
	}
    var new_note;
    if( /^([^_]*)_(.*)$/.test( new_status ) )
	{
	new_status = RegExp.$1;
	new_note = RegExp.$2;
	already_displaying = 0;
	}
    var p = ebid("current_status");
    p.value = new_status;
    p.style.backgroundColor = STATES[p.value].color;

    if( stops[current_stop].status != new_status )
	{
	// debug_out( "flow", "XL(Setting) current_stop="+current_stop+" XL(status to) "+new_status);
	stops[current_stop].status = new_status;

	// debug_out( "flow", "XL(About to do test):  current_stop="+current_stop+", status="+new_status+", length="+stops.length);
//	if( new_status && new_status!="Unvisited" && new_status!="Untouched"
//	    && (current_stop==0 || current_stop==stops.length-1 ) )
//	    { get_field("odometer",/^\d+\.\d$/,"nn.n"); }

	// set_active( current_stop, 1 );
	stops[current_stop].modified = new Date();
	get_current_position(
	    function()
		{
		stops[current_stop].coords =
		    current_position.latitude +"," + current_position.longitude;
		});

	if( ! stops[current_stop].notes )
	    { stops[current_stop].notes = ""; }
	if( new_note )
	    {
	    if( stops[current_stop].notes )
	        { stops[current_stop].notes += "\n"; }
	    stops[current_stop].notes += new_note.replace(/_/g," ");
	    }
	else if(new_status == "Normal"
	    ||  new_status == "Unvisited"
	    ||  new_status == "Untouched" )
	    {}
	else
	    {
	    (ebid("id_patron_issue_value")).value
	        = stops[current_stop].notes.replace(/\n/,"<br>");
	    return set_status_ret = lightup("patron_issue","/set_status");
	    }

	if( stops[current_stop].type == "Distributor"
	    && ! stops[current_stop].odometer
	    && new_status != "Unvisited"
	    && new_status != "Untouched" )
	    {
	    return set_status_ret = lightup("odometer","/set_status");
	    }
	}

    if( already_displaying )
        { return update_screen( "/set_status" ); }
    else
        { return lightup( "small", "/set_active-3" ); }
    }

//////////////////////////////////////////////////////////////////////////
//////////////////////////////////////////////////////////////////////////
//checkpoint("00000 function set_donation_type");
function set_donation_type( new_value, continue_flag )
    {
    debug_out( "functions", "function start set_donation_type()");
    var new_donation_type_colors = { Cash:'', Check:'' };
    if( new_value )
	{ new_donation_type_colors[ new_value ] = "#c0ffff"; }
    for ( const donation_type in new_donation_type_colors )
	{
	(ebid("id_"+donation_type+"_button")).style.backgroundColor =
	    new_donation_type_colors[ donation_type ];
	}
    set_attribute("donation_type",new_value,continue_flag);
    }

//////////////////////////////////////////////////////////////////////////
//////////////////////////////////////////////////////////////////////////
//checkpoint("00000 function set_route_type");
function set_route_type( new_value, continue_flag )
    {
    debug_out( "functions", "function start set_route_type()");
    for ( const route_type of route_types )
	{
	(ebid("id_"+route_type+"_button")).style.backgroundColor =
	    ( route_types == new_value ? "#c0ffff" : "" );
	}
    set_attribute("route_type",new_value,continue_flag);
    }

//////////////////////////////////////////////////////////////////////////
//	Set which stop we're looking at.				//
//	If we try to specify a nonexistent stop, show all stops.	//
//////////////////////////////////////////////////////////////////////////
var in_trace = 1;
//checkpoint("00000 function real_set_active");
function real_set_active( ind_base, offset )
    {
    debug_out( "functions", "function real_start set_active()");
    if( ind_base < 0 || ind_base >= stops.length )
        { return lightup( "big", "/set_active-1" ); }

    if( ! display_order || offset == 0 )
	{ current_stop = ind_base + offset; }
    else
	{
	var display_ind = -1;
	for( var i=0; display_ind<0 && i<display_order.length; i++)
	    {
	    if( display_order[ i ] == ind_base )
		{ display_ind = i; }
	    }
	if( display_ind < 0 )
	    { alert("XL(Cannot find active) + "+offset); }
	else
	    {
	    var i = display_ind + offset;
	    if( i < 0 || i >= display_order.length )
		{ return lightup( "big", "/set_active-2" ); }
	    else
		{ current_stop = display_order[i]; }
	    }
	}

    for( const vname of ["odometer","donation","donation_type","route_type"] )
	{
	(ebid("id_"+vname+"_value")).value
	    = (stops[current_stop][vname]||"");
	}

    set_donation_type( stops[current_stop].donation_type, 0 );
    // set_route_type( stops[current_stop].route_type, 0 );

    (ebid("id_patron_issue_value")).value
	= (stops[current_stop].notes||"").replace(/\n/,"<br>");

    setdisplay("id_odometer_line",stops[current_stop].type=="Distributor");	// Only ask odometer at centers.
    setdisplay("id_donation_line",stops[current_stop].type=="Patron");	// Only ask donations at patrons.
    setdisplay("id_pickup_line",stops[current_stop].type=="Pickup");	// Only ask for pickup info on pickup.
    setdisplay("id_notes_line",current_stop>0);				// Notes for everybody but start
    setdisplay("id_route_type_line",current_stop==0);
    setdisplay("id_status_line",true);

    if( stops[ current_stop ].status != "Untouched" )
        { return set_status( stops[current_stop].status ); }
    else
        {
	oneof("set_status", "<table cellpadding=5 cellspacing=5 width=100%>"
	    + "<tr><th class=bigtext>XL(Visit the following stop?)</th></tr>"
	    + "<tr><td class=bigtext>"+(stops[current_stop].name||"") + "</td></tr>"
	    + "<tr><td>"+(stops[current_stop].addrtxt||"") + "</td></tr>"
	    + "<tr><td>"+(stops[current_stop].phone||"") + "</td></tr>"
	    + "</table>", [
	    { value:"Unvisited", txt:"XL(Visit the stop)", color:STATES.Unvisited.color  },
	    { value:"Skipped_Hospital", txt:"XL(In hospital)", color:STATES.Skipped.color },
	    { value:"Skipped_Deceased", txt:"XL(Deceased)", color:STATES.Skipped.color },
	    { value:"Skipped_Suspend", txt:"XL(Suspended)", color:STATES.Skipped.color },
	    { value:"Skipped_Every_Other", txt:"XL(Every Other)", color:STATES.Skipped.color },
	    { value:"Skipped_Different_Route", txt:"XL(Different Route)", color:STATES.Skipped.color },
	    { value:"Skipped", txt:"XL(Do not visit the stop)", color:STATES.Skipped.color } ] );
	}
    }
//checkpoint("00000 function set_active");
function set_active( ind_base, offset )
    {
    var set_active_return;
    try
	{ set_active_return = real_set_active(ind_base,offset); }
      catch(estack)
	{ alert("set_active XL(failed):\n" + estack.stack ); }
    return set_active_return;
    }

//////////////////////////////////////////////////////////////////////////
//	Called when user wants to note an issue with a patron.		//
//////////////////////////////////////////////////////////////////////////
//checkpoint("00000 function set_attribute");
function set_attribute( fld, val, ok_to_proceed )
    {
    debug_out( "functions",
	"function start setattribute("+fld+","+val+","+ok_to_proceed+")");
    if( fld == "notes" && val )
        {
	val = val.replace(/[^A-Za-z0-9\.\-,?:;/!@#$%^&_\*\(\)\+\=\{\}\[\]\n ]+/g,"?");
	val = val.replace(/\r/g,"");
	}
    stops[current_stop][fld] = val;
    stops[current_stop].modified = new Date();
    if( ok_to_proceed )
	{
	update_screen( "/set_attribute_"+fld );
	return lightup("small");
	}
    }

//////////////////////////////////////////////////////////////////////////
//	Return a date as a readable string.				//
//////////////////////////////////////////////////////////////////////////
//checkpoint("00000 function date_to_HHMM");
function date_to_HHMM( d )
    {
    debug_out( "functions", "function start date_to_HHMM()");
    return new Date(d).toLocaleTimeString( [],
	    { hour12:false, hour:'2-digit', minute:'2-digit' } );
    }

var DIGITS_RESERVED="'\"!,:+-%=\\;`".split('');
var digits = new Array();
var digits_offset;
//////////////////////////////////////////////////////////////////////////
//////////////////////////////////////////////////////////////////////////
//checkpoint("00000 function convert_base");
function convert_base( n )
    {
    debug_out( "functions", "function start convert_base()");
    var ret = new Array();
    do  {
	ret.push( digits[ n % digits.length ] );
	n = Math.floor(n / digits.length);
	} while( n );
    return ret.reverse().join('');
    }

//////////////////////////////////////////////////////////////////////////
//	Server updates what last thing was recorded.			//
//	Reduces length of packets we transmit since we try to transmit	//
//	only new stuff.							//
//////////////////////////////////////////////////////////////////////////
//checkpoint("00000 function progress_logged");
function progress_logged( done, timestr, arg_last_serial_received, set_last_recorded )
    {
    debug_out( "functions", "function start progress_logged()");
    last_serial_received = arg_last_serial_received;

    // If the server claims that it has received previous data, simply
    // forget all the GPS information up to that last time.
    // Intent is to reduce size of upstream packet.
    last_recorded = set_last_recorded;
    while( route_history.length && route_history[0].when > last_recorded )
        { route_history.shift(); }
    var rcvmsg = timestr + " logged"
	    +" serial="+last_serial_received
	    +" \n";
    rcvmsg = "";
    if( done )
        {
	rcvmsg +=
	    	'XL(Your route log has been recorded.)\n'
	    +	'XL(This page is closing.)\n'
	    +	'\n'
	    +	'XL(If it does not close, close it manually.)\n'
	    +	'\n'
	    +	'XL(Thank you!)\n';
	}
    if( rcvmsg ) { alert( rcvmsg ); }
    if( done ) { window.close(); }
    }

//////////////////////////////////////////////////////////////////////////
//	Compute progress from route history.				//
//////////////////////////////////////////////////////////////////////////
//checkpoint("00000 function compute_progress");
function compute_progress()
    {
    debug_out( "functions", "function start compute_progress()");
    var offsets = { when:0, latitude:0, longitude:0 };
    var last_mode = 0;

    var progress = new Array( digits.join('') );

    for( var i=0; i<route_history.length; i++ )
	{
	for( var ind in offsets )	// Order of keys preserved, I promise!
	    {
	    var diff;
	    if( ind=="when" )
		{
		diff = (route_history[i][ind]-offsets[ind])
			/ time_constant.SECOND;
		}
	    else if( ind=="latitude" || ind=="longitude" )
		{
		diff = (route_history[i][ind]*GPS_DIGITS)
		     - (offsets[ind]*GPS_DIGITS);
		}
	    offsets[ind] = route_history[i][ind];
	    diff = Math.floor(diff);
	    if( ind=="when" && diff < digits.length )
		{
		if( last_mode++ == 0 ) { progress.push(":"); }
		progress.push( digits[diff] );
		}
	    else if (ind!="when" && diff>=-digits_offset && diff<digits_offset )
		{
		if( last_mode++ == 0 ) { progress.push(":"); }
		progress.push( digits[diff+digits_offset] );
		}
	    else
		{
		if( diff < 0 )
		    { progress.push( "-"+convert_base(-diff) ); }
		else
		    { progress.push( "+"+convert_base(diff) ); }
		last_mode = 0;
		}
	    }
	}
    return progress.join("");
    }

//checkpoint("00000 function min3");
function min3(a, b, c)
    {
    // debug_out( "functions", "function start min3()");
    if (a <= b && a <= c) return a;
    if (b <= a && b <= c) return b;
    return c;
    }

//////////////////////////////////////////////////////////////////////////
//	Return the index of the minimum value in an array.		//
//////////////////////////////////////////////////////////////////////////
//checkpoint("00000 function minind");
function minind( ar )
    {
    // debug_out( "functions", "function start minind()");
    var answer = 0
    for( var i=1; i<ar.length; i++ )
	{
	if( ar[i] < ar[answer] )
	    { answer=i; }
	}
    return answer;
    }

//////////////////////////////////////////////////////////////////////////
//	Return the minimum value in an array.				//
//////////////////////////////////////////////////////////////////////////
//checkpoint("00000 function minv");
function minv( ar )
    {
    // debug_out( "functions", "function start minv()");
    return ar[ minind( ar ) ];
    }

//////////////////////////////////////////////////////////////////////////
//	Return a string representing instructions to convert the first	//
//	string into the second.  Reduces data to send upstring which	//
//	already has previous instance (and minimal stuff has changed)	//
//////////////////////////////////////////////////////////////////////////
//checkpoint("00000 function Make_Edit_String");
function Make_Edit_String(str1, str2)
    {
    debug_out( "functions", "function start Make_Edit_String()");
    //var msg = new Array();
    var res = new Array();
    const m = str1.length;
    const n = str2.length;
    const dp = new Array(m + 1).fill(null).map(() => new Array(n + 1).fill(0));

    for (let i = 0; i <= m; i++)
	{
	for (let j = 0; j <= n; j++)
	    {
	    dp[i][j] =
		( (i === 0)			? j
		: (j === 0)			? i
		: (str1[i-1] === str2[j-1])	? dp[i-1][j-1]
		: ( 1 + minv([dp[i][j-1], dp[i-1][j], dp[i-1][j-1]]) )
		);
	    }
	}

    let i = m;
    let j = n;

    while (i > 0 || j > 0)
	{
	//msg.push("--------------- i="+i+", j="+j);
	var lastind = res.length - 1;
	var lastloc = '?';
	var lastcmd = '?';
	var lastarg = '?';
	if( lastind >= 0 && (/(\d+)(.)(.*)/.test(res[lastind]) ) )
	    {
	    lastloc = parseInt(RegExp.$1);
	    lastcmd = RegExp.$2;
	    lastarg = RegExp.$3;
	    //msg.push("lastloc=("+lastloc+"), lastcmd=("+lastcmd+"), lastarg=("+lastarg+")");
	    if( lastcmd=='d' )
		{ lastarg = ( lastarg ? parseInt(lastarg) : 1 ); }
	    }
	if (i === 0)
	    {
	    const cmd='i';
	    if( lastcmd==cmd && i==lastloc )
	        { res[lastind] = `${i}${cmd}${str2[--j]}${lastarg}`; }
	    else
	        { res.push(`${i}${cmd}${str2[--j]}`); }
	    }
	else if (j === 0)
	    {
	    const cmd='d';
	    if( lastcmd==cmd && (lastloc==i) )
		{ res[lastind]=`${--i}${cmd}${lastarg+1}`; }
	    else
		{ res.push(`${--i}${cmd}`); }
	    }
	else if (str1[i - 1] === str2[j - 1])
	    { i--; j--; }
	else
	    {
	    const k = minind( [dp[i][j-1], dp[i-1][j], dp[i-1][j-1]] );
	    if (k === 2)
		{
		const cmd='r';
		if( lastcmd==cmd && i==lastloc )
		    { res[lastind] = `${--i}${cmd}${str2[--j]}${lastarg}`; }
		else
		    { res.push(`${--i}${cmd}${str2[--j]}`); }
		}
	    else if (k === 1)
		{
		const cmd='d';
		if( lastcmd==cmd && (lastloc==i) )
		    { res[lastind]=`${--i}${cmd}${lastarg+1}`; }
		else
		    { res.push(`${--i}${cmd}`); }
		}
	    else	// k == 0
		{
		const cmd='i';
		if( lastcmd==cmd && i==lastloc )
		    { res[lastind] = `${i}${cmd}${str2[--j]}${lastarg}`; }
		else
		    { res.push(`${i}${cmd}${str2[--j]}`); }
		}
	    }
	//msg.push("ind="+lastind+", loc="+lastloc+", cmd="+lastcmd+", arg="+lastarg+" result="+res[ res.length-1 ] );
	}

    // return dp[m][n];
    // return res.join("<br>");
    // debug_out( "flow", "Debug length="+msg.length+"\n"+msg.join("\n"));
    return res.join('`');
    }

//////////////////////////////////////////////////////////////////////////
//	Post form containing update information.			//
//////////////////////////////////////////////////////////////////////////
//checkpoint("00000 function generate_update");
function generate_update( doneflag )
    {
    debug_out( "functions", "function start generate_update()");
    if( doneflag )
	{
	var problems = new Array();
	if( stops[0].odometer == undefined )
	    { problems.push( "Odometer for route start not set." ); }
	if( stops[0].route_type == undefined ||
	    stops[0].route_type == "Unknown" )
	    { problems.push( "Route type not set." ); }
	if( stops[ stops.length-1 ].odometer == undefined )
	    { problems.push( "Odometer for route completion not set." ); }
	if( problems.length == 0 )
	    {
	    var travelled = stops[ stops.length-1 ].odometer - stops[0].odometer;
	    if( travelled < 0 )
	        {
		problems.push(
		    "Odometer for route completion ("+stops[ stops.length-1 ].odometer
		    + ") before route start (" + stops[0].odometer + ")." );
		}
	    else
		{
	        var travelled_pretty = (travelled + 0.05).toFixed(1);
		if( ! confirm(
			    "XL(Log) "
			+   travelled_pretty + " XL(miles from) "
			+   stops[0].odometer + " XL(to) "
			+   stops[ stops.length-1 ].odometer
			+   "?"  ) )
		    { return 0; }
		}
	    }
	if( problems.length )
	    {
	    alert( problems.join("\n") );
	    return 1;
	    }
	}
    for( var stop_number=0; stop_number<stops.length; stop_number++ )
	{
	if( stops[stop_number].modified )
	    {
	    stops[stop_number].when =
		date_to_HHMM(stops[stop_number].modified);
	    }
	}

    var now = new Date(0);
    var route_status = JSON.stringify(
	{
	STAFF:			"%%STAFF%%",
	DISTRIBUTOR:		"%%DISTRIBUTOR%%",
	USER:			"%%USER%%",
	ROUTE_NAME:		"%%ROUTE_NAME%%",
	SECRET:			SECRET,
	stops:			stops,
	display_order:		display_order,
	done:			doneflag||0,
	update_time:		now.getTime(),
	progress:		compute_progress()
	} );
    if( route_status != last_route_status ) { current_serial++; }

    // debug_out( "flow", ("CMC pre make_edit_string logic, last_serial="+last_serial_received+", current_serial="+current_serial);
    var edit_string = "";	// Assume nothing has changed

    if( current_serial == last_serial_received )
	// If serial hasn't changed, no need to update server copy
	{ edit_string = ""; }

    else if( current_serial != (last_serial_received+1) )
	// If serial has changed by any more than one, clear and resend all
	{ edit_string = "0c"+route_status; }
    else
	// If serial has only changed by one, figure out min update to send
	{
	edit_string = Make_Edit_String(last_route_status,route_status);

	if( edit_string.length > route_status.length )
	    // Simpler just to replace entire server copy
	    { edit_string = "0c"+route_status; }
	}
    // debug_out("flow","CMC post make_edit_string logic...");
    last_route_status = route_status;

    window.document.form.route_status_edit.value = edit_string;
    window.document.form.route_status_serial.value = current_serial;
    if( window.document.form["route_status_debug"] )
        {	//If debugging, send entire thing upstream anyways
	window.document.form.route_status_debug.value = route_status;
	}

    if( DEBUG.update.flow || doneflag )
	{
	window.document.form.submit();
//	debug_out("flow","Generate_update("
//	+"done="+doneflag
//	+", serial="+current_serial
//	+", sending="+window.document.form.progress.value.length
//	+")");
//	debug_out("flow","generate_update("+doneflag+") complete.");
	}
    }

//////////////////////////////////////////////////////////////////////////
//      Get pointer to an ID but give a reasonable message if it does   //
//      not exist.  "should never happen".  Uh huh.                     //
//////////////////////////////////////////////////////////////////////////
//checkpoint("00000 function ebid");
function ebid( id )
    {
    // debug_out( "functions", "function start ebid()");
    return document.getElementById(id) ||
        fatal("Cannot find element for id ["+id+"]");
    }

//////////////////////////////////////////////////////////////////////////
//	Pack into string from convenient hash pickup_list.		//
//////////////////////////////////////////////////////////////////////////
//checkpoint("00000 function pickup_list_to_text");
function pickup_list_to_text()
    {
    debug_out( "functions", "function start pickup_list_to_text()");
    var s = new Array;
    for( const route_name of route_pickup_list )
	{
	var bag_list = new Array();
	var can_skip = 1;
	for( const bag_type of bag_types )
	    {
	    var new_bag_attributes = new Array();
	    for( const piece of ["Received","Expected"] )
		{
		var p = pickup_list[route_name][bag_type][piece];
		if( p )
		    { can_skip=0; }
		else
		    { p=0; }
		new_bag_attributes.push( p );
		}
	    bag_list.push( bag_type + " " + new_bag_attributes.join('/') );
	    }
	if(!can_skip) {s.push(route_name + ": " + bag_list.join(", ") + "\n");}
	}
    stops[current_stop].pickups = s.join("");
    }

//////////////////////////////////////////////////////////////////////////
//	Unpack string from stops into more convenient hash pickup_list.	//
//////////////////////////////////////////////////////////////////////////
//checkpoint("00000 function text_to_pickup_list");
function text_to_pickup_list()
    {
    debug_out( "functions", "function start text_to_pickup_list()");
    pickup_list = new Array();
    for ( const route_name of route_pickup_list )
	{
	pickup_list[route_name] = {};
	for( const bag_type of bag_types )
	    { pickup_list[route_name][bag_type] = {"Received":0,"Expected":0}; }
	}
    for ( const ln of stops[current_stop].pickups.split("\n") )
	{
	if( /^\s*(.*?)\s*:\s*(.*)$/.test( ln ) )
	    {
	    var route_name = RegExp.$1;
	    var bag_string = RegExp.$2;

	    if( pickup_list[route_name] )
		{
		for( const bagtxt of bag_string.split(',') )
		    {
		    if( /^\s*(.*?)\s*(\d+)\s*\/\s*(\d+)\s*$/.test(bagtxt) )
			{
			pickup_list[route_name][RegExp.$1].Received = RegExp.$2;
			pickup_list[route_name][RegExp.$1].Expected = RegExp.$3;
			}
		    }
		}
	    }
	}
    }

//////////////////////////////////////////////////////////////////////////
//	Prompt for and modify a field and redraw the screen.		//
//////////////////////////////////////////////////////////////////////////
//checkpoint("00000 function modify_pickup");
function modify_pickup( pickup_ind, bag_type, field )
    {
    debug_out( "functions", "function start modify_pickup()");
    if( field == "Received" )
	{ pickup_list[pickup_ind][bag_type][field]++; }
    var ret =
	prompt( pickup_ind + " " + bag_type + " " + field + ":",
	    pickup_list[pickup_ind][bag_type][field] );
    pickup_list[pickup_ind][bag_type][field] = ret;

    pickup_list_to_text();
    draw_pickups();
    }

//////////////////////////////////////////////////////////////////////////
//	Redraw the screen.						//
//////////////////////////////////////////////////////////////////////////
//checkpoint("00000 function draw_pickups");
function draw_pickups()
    {
    debug_out( "functions", "function start draw_pickups()");
    var s = new Array();

    text_to_pickup_list();

    s.push( "<table style='border-collapse:collapse;' cellpadding=0 cellspacing=0 border=1><tr><th>" );
    s.push( "<table style='border-collapse:collapse;' cellpadding=2 cellspacing=0 border=0 width=100%>" );
    for( var bag_type_ind in bag_types )
	{
	var bag_type = bag_types[bag_type_ind];
	var trcolor=" bgcolor='"+BAG_COLORS[bag_type_ind%BAG_COLORS.length]+"'";
	s.push( "<tr"+trcolor+"><th align=left>"+bag_type+"</th>" );
	for( var bag_type_value of BAG_TYPE_VALUES )
	    { s.push( "<th>"+bag_type_value+"</th>" ); }
	for( var pickup_ind of route_pickup_list )
	    {
	    s.push( "</tr><tr"+trcolor+">" );
	    s.push( "<th align=left>" + pickup_ind + "</th>" );
	    for( var bag_type_value of BAG_TYPE_VALUES )
		{
		var color = "white";
		if( bag_type_value == "Received" )
		    {
		    if(!pickup_list[pickup_ind][bag_type][bag_type_value])
			{ pickup_list[pickup_ind][bag_type][bag_type_value]=0; }
		    color = (
			pickup_list[pickup_ind][bag_type][bag_type_value] ==
			pickup_list[pickup_ind][bag_type].Expected
			? "#d0ffd0"
			: "#ffd0d0" );
		    }
		s.push( "<th>",
		    "<button "+
		    "style='width:100%;text-align:right;background-color:"+
		    color+
		    "' onClick='modify_pickup("+
		    "\""+pickup_ind+"\",\""+bag_type+"\",\""+bag_type_value+"\");'"+
		    ">"+pickup_list[pickup_ind][bag_type][bag_type_value]+
		    "</button></th>" );
		}
	    }
	}
    s.push( "</tr></table></th></tr></table>" );
    // debug_out("flow", s );
    (ebid("pickup_table_id")).innerHTML = s.join("\n");
    }

//////////////////////////////////////////////////////////////////////////
//	Various options to help debug this monster.			//
//////////////////////////////////////////////////////////////////////////
//checkpoint("00000 function debug_page");
function debug_page()
    {
    debug_out( "functions", "function start debug_page()");
    var s = new Array( '<table border=0 style="border-collapse:collapse">' );
    for ( const flag in DEBUG )
	{
	s.push('<tr><th align=left valign=top>'+flag+':</th>');
	if( ! DEBUG[flag].values )
	    {
	    s.push('<td onClick=\'DEBUG.'+flag+'.value=prompt("Enter '+flag+':",DEBUG.'+flag+'.value);debug_page();\'>');
	    s.push(DEBUG[flag].value+'</td>');
	    }
	else
	    {
	    s.push('<td>');
	    for( var posval=0; posval<DEBUG[flag].values.length; posval++ )
	        {
		var text=DEBUG[flag].values[posval];
		var val=DEBUG[flag].values[posval];
		if( /(.*)=(.*)/.test( DEBUG[flag].values[posval] ) )
		    { val=RegExp.$1; text=RegExp.$2; }
		var valstring = '"'+val+'"';
		if( /^\d+$/.test(val) )
		    {
		    val = val - 0;
		    valstring = val;
		    }
		var style=
		    ( val == DEBUG[flag].value
		    ? "style='background-color:cyan'"
		    : "style='background-color:gray'" );
		s.push( '<button '+style+' onClick=\'DEBUG.'+flag+'.value='+
		    valstring+';debug_page();\'>' + text + '</button>' );
		}
	    s.push('</td>');
	    }
	s.push('</tr>');
	}
    s.push( "<tr><td colspan=2 bgcolor=black width=100%>&nbsp;</th></tr>" );
    for( const varname of [
        "navigator.userAgent",
	"CURRENT_BROWSER",
	"GPS_TIMEOUT",
	"DEST_HANDLER",
	"ROUTE_HANDLER" ] )
	{
	s.push( "<tr><th align=left>"
	    +varname+":</th><td>"+eval(varname)
	    +"</td></tr>" );
	}
    s.push( '</table>' );
    (ebid("id_debug_data")).innerHTML = s.join("\n");
    lightup('debug');
    }

//////////////////////////////////////////////////////////////////////////
//	Setup_page							//
//	Called when .html file loaded to do any javascript setup.	//
//	Obviously will not get called when javascript is not running	//
//	(which is to say, when result is being printed).		//
//////////////////////////////////////////////////////////////////////////
//checkpoint("00000 function setup_page");
function setup_page()
    {
    debug_out( "functions", "function start setup_page()");
    browser_dependent();
    var caller_pieces = window.location.href.split('?');
    if( caller_pieces.length > 1 )
	{
	caller_pieces = caller_pieces[1].split('&');
	for( const piece of caller_pieces )
	    {
	    if( /(.*)=([0-9]+)$/.test(piece) )
	        { DEBUG[ RegExp.$1 ].value = parseInt( RegExp.$2 ); }
	    else if( /(.*)=(.*)$/.test(piece) )
	        { DEBUG[ RegExp.$1 ].value = RegExp.$2; }
	    }
	}

//    document.cookie=
//	COOKIE_NAME+"=;expires="+new Date(0).toUTCString()+";path=/";

    //	Compute digits for the best possible base we can do with
    //	printable characters not in DIGITS_RESERVED.
    for( var ci=33; ci<127; ci++ )	// Generate a list of usable digits
	{				// 90 or so digits for compression!
	var c=String.fromCharCode(ci);	// Used in convert_base()
	if( DIGITS_RESERVED.indexOf(c)<0 ) { digits.push(c); }
	}
    digits_offset = Math.floor( digits.length / 2 );

    for( var i=1; i<stops.length; i++ )
        {
	if( stops[i].status==undefined )
	    {
	    if( i==0 || i == stops.length-1 )
		{ stops[i].status="Unvisited"; }
	    else
		{ stops[i].status="Untouched"; }
	    }
	stops[i].route_from = i - 1;
	}
    if( ! stops[0].status )
	{ stops[0].status = "Unvisited"; }
    stops[0].route_from = -1;
    if( ! stops[stops.length-1].status )
	{ stops[stops.length-1].status = "Unvisited"; }

    find_cookie();
    get_current_position(0);

    if( DEBUG.debug.value )
	{	// Extra buttons for test routes!
	(ebid("Debug_id")).style.display = "";
	}

    update_screen("/setup_page");
    update_timer = setInterval
	(
	function() { generate_update(0); },
	time_constant.UPDATE_INTERVAL
	);
    document.body.ontouchend = function() { check_focus(); }
    }
