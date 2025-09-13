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
// Stolen directly (though re-indented) from				//
// https://developer.mapquest.com/documentation/common/encode-decode/	//
//////////////////////////////////////////////////////////////////////////
function decompress (encoded, precision)
    {
    precision = Math.pow(10, -precision);
    var decoded = [];
    for(var latlong_ind=0,	//0=Latitude 1=Longitude
	    latlong=[0,0],
	    len=encoded.length,
	    index=0;
        index<len;
	latlong_ind=1-latlong_ind )
	{
	var b, shift = 0, result = 0;
	do  {
	    b = encoded.charCodeAt(index++) - 63;
	    result |= (b & 0x1f) << shift;
	    shift += 5;
	    } while (b >= 0x20);
	latlong[latlong_ind] += ((result & 1) ? ~(result>>1) : (result>>1));
	decoded.push( latlong[latlong_ind] );
	}
    return decoded;
    }

function compress(points, precision)
    {
    precision = Math.pow(10, precision);
    var encoded = '';
    for(var latlong_ind=0,
	    last_latlong=[0,0],
	    len=points.length,
	    index=0;
        index<len;
	latlong_ind=1-latlong_ind )
	{
	// Round to N decimal places
	var latlong = Math.round(points[index++] * precision);

	// Encode the differences between the points
	encoded += encodeNumber(latlong - last_latlong[latlong_ind);

	// Update our concept of last latitude or longitude
	last_latlong[latlong_ind] = latlong;
	}
    return encoded;
    }

function encodeNumber(num)
    {
    var num = num << 1;
    if (num < 0) { num = ~(num); }
    var encoded = '';
    while (num >= 0x20)
	{
	encoded += String.fromCharCode((0x20 | (num & 0x1f)) + 63);
	num >>= 5;
	}
    return encoded + String.fromCharCode(num + 63);
    }

//////////////////////////////////////////////////////////////////////////
//	End stolen code.  Bugs are probably mine (Chris Caldwell), not	//
//	theirs.								//
//////////////////////////////////////////////////////////////////////////

%%
