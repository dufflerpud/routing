//////////////////////////////////////////////////////////////////////////
//	Software for using routing features of maps.Apple.com.		//
//////////////////////////////////////////////////////////////////////////


//////////////////////////////////////////////////////////////////////////
//	Invoke the Apple maps web site to show the entire route.	//
//////////////////////////////////////////////////////////////////////////
//checkpoint("00036 function goto");
function goto_Apple_map()
    {
    debug_out( "functions", "function start goto_Apple_map()");
    var ret = new Array( "maps:https://maps.Apple.com/?dirflg=d" );
    let {namelist,preflist,addrlist,cordlist} = split_out("Apple");

    debug_out( "flow", "daddr logic length="+preflist.length+", ret length="+ret.length);
    if( preflist.length > 0 )
	{
	let {preflist_compressed,namelist_compressed} =
	    navigable_list( preflist, namelist, 14 );
	ret.push( "daddr=" +
	    encodeURIComponent_array( preflist_compressed ).join("&daddr=") );
	}
    debug_out( "flow",
	"now daddr logic length="+preflist.length
	+", ret length="+ret.length);

    debug_out( "url", "URL is [ "+ret.join("&")+" ]");
    return ret.join("&");
    }
map_handlers.Apple = goto_Apple_map;
