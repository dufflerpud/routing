//indx#	lib.js - Javascript portion of Apple mapping software
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
//doc#	lib.js - Javascript portion of Apple mapping software
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
