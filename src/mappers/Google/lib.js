//////////////////////////////////////////////////////////////////////////
//	Software for using routing features of maps.Google.com.		//
//									//
//	Note that this will get used by Android users and potentially	//
//	by Apple users running with Chrome.				//
//////////////////////////////////////////////////////////////////////////

var USE_GOOGLE_PLACE_IDS = 1;

//////////////////////////////////////////////////////////////////////////
//	Invoke the Google maps web site to show the entire route.	//
//////////////////////////////////////////////////////////////////////////
//checkpoint("00035 function goto");
function goto_Google_map()
    {
    debug_out( "functions", "function start goto_Google_map()");
    var ret = new Array( "https://maps.Google.com/maps" );
    let {namelist,preflist,addrlist,cordlist} = split_out("Google");

    if( preflist.length )
	{
	// This horrible thing is to force the last stop to always
	// be on its own.  This is because Google maps seems to wig out
	// if you have waypoints but you are already at the destination.
	var use_len =
	    (
//	    ( preflist.length>2 && /Mac OS/.test(navigator.userAgent) ) ? 2 :
	    ( preflist.length > 10 )
	    ?	10
//	    : ( preflist.length > 1 )		// Due to Google maps bug
//	    ?	(preflist.length-1)		// Due to Google maps bug
	    :	preflist.length );
	// use_len = 1;	// I give up.  Androids suck.
	let {preflist_compressed,namelist_compressed} =
	    navigable_list( preflist, namelist, use_len );

//	// Due to Android Auto bug on Rav-4.  This is why we can't have nice things.
//	if( preflist_compressed.length > 1 && /Android/.test(navigator.userAgent) )
//	    {
//	    alert(
//	        "XL(With some cars and Androids,\nyou should now make sure any\nAndroid Auto is disconnected\nbefore proceeding.\n\nNote that you can reconnect it\nafter Google Maps has\nplotted a route.)"
//	    );
//	    }

	// Strictly speaking, we could put the destination first, but it
	// actually makes it harder to debug for some reason.
	
	if( DEBUG.Google_API.value == "Old" )
	    {
	    ret.push("/dir/Your+location/");
	    ret.push(encodeURIComponent_array( preflist_compressed, "/" ));
	    }
	else if( DEBUG.Google_API.value == "saddr" )
	    {
	    ret.push("?dirflg=d");
	    ret.push("&saddr=Your+location");
	    ret.push("&daddr="+encodeURIComponent_array(preflist_compressed,"+to:"));
	    }
	else if( DEBUG.Google_API.value == "New" )
	    {
	    var endwith = new Array();
	    ret.push("/dir/?api=1");
	    if( preflist_compressed.length )
		{
		endwith.push("&destination="+encodeURIComponent(preflist_compressed.pop()));
		if( USE_GOOGLE_PLACE_IDS )
		    { endwith.push("&destination_place_id="+encodeURIComponent(namelist_compressed.pop())); }
		}
	    if( preflist_compressed.length )
		{
		ret.push(
		    "&waypoints=" +
			encodeURIComponent( preflist_compressed.join("|") ) );
			// encodeURIComponent_array( preflist_compressed ).join("|") );
		ret.push( "&optimizewaypointorder=false" );
		if( USE_GOOGLE_PLACE_IDS )
		    {
		    ret.push(
			"&waypoint_place_ids=" +
			    encodeURIComponent( namelist_compressed.join("|") ) );
			    // encodeURIComponent_array( namelist_compressed ).join("|") );
		    }
		}
	    ret = ret.concat( endwith );
	    }
	}
    debug_out("url","Returning ["+ret.join("")+"]");
    return ret.join("");
    }
map_handlers.Google = goto_Google_map;

