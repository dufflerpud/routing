#!/usr/local/projects/routing/help/html_filter.pl
<style type="text/css">
<!--
    	input.fixed_width_button	{width:300px;}
	td input.fixed_width_button	{width:300px;}

-->
</style>
<meta http-equiv="Content-Type" content="text/html; charset=UTF-8">
<script>
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
//	routing_header.js						//
//	Javascript used for routing.cgi.				//
//	Chris Caldwell, 04/29/2022					//
//////////////////////////////////////////////////////////////////////////

//////////////////////////////////////////////////////////////////////////
//	Short hand for setting a display element on or off.		//
//////////////////////////////////////////////////////////////////////////
function setdisplay( name, flag )
    {
    // (document.getElementById(name)).style.display = ( flag ? "" : "none" );

    var p = document.getElementById(name);
    if( !p )
        { alert("Cannot find ["+name+"] to set to "+(flag?"on.":"off.")); }
    else
	{ p.style.display = ( flag ? "" : "none" ); }
    }

//////////////////////////////////////////////////////////////////////////
// Submit the page with form variable "func" set to the specified	//
// string.								//
//////////////////////////////////////////////////////////////////////////
function submit_func( func0, arg0 )
    {
    // alert("submit_func("+(func0||"U")+","+(arg0||"U")+")");
    with( window.document.form )
	{
	if( typeof(func0) != "undefined" )	{ func.value = func0; }
	if( typeof(arg0)  != "undefined" )	{ arg.value  = arg0; }
	submit();
	}
    }

//////////////////////////////////////////////////////////////////////////
//	User has selected a different carrier (phone company) for a	//
//	"Notify".  Look for the appropriate address and update the	//
//	corresponding input type=text.					//
//////////////////////////////////////////////////////////////////////////
function change_carrier( selectptr, variableptr )
    {
    if( selectptr.value )
	{
	if( /^([\d\(\)-]+)$/.test( variableptr.value )
	 || /^([\d\(\)-]+)@(.+)$/.test( variableptr.value ) )
	    {
	    var phone = RegExp.$1;
	    phone = phone.replace(/[^\d]/g,"");
	    variableptr.value = phone + "@" + selectptr.value;
	    }
	}
    }

//////////////////////////////////////////////////////////////////////////
//	Show user what examples match what's in the current text field.	//
//////////////////////////////////////////////////////////////////////////
function show_matching( tblname, fieldname, fld )
    {
    var s = "";
    var patt = new RegExp( fld.value, "i" );
    var matches = new Array();
    for( const k in SEARCH_TABLE )
	{
	if( patt.test( k ) ) { matches.push( k ); }
	}
    if( matches.length > 0 )
	{
	var count = 0;
	for( const k of matches )
	    {
	    if( count++ > 20 )
		{
		s += "<br>...";
		break;
		}
	    s += "<br><a href='javascript:submit_func(\""
		+ SEARCH_TABLE[k]
		+ "\");'>" + k + "</a>";
	    }
	}
    (document.getElementById("search_"+fieldname)).innerHTML = s;
    }

//////////////////////////////////////////////////////////////////////////
//	User has changed a "type=text" or textarea.  Fix it up as	//
//	required for the datatype.  In practice, this means make phone	//
//	numbers all adhere to the same format and allow the user to	//
//	get the last value by typing "!!".				//
//////////////////////////////////////////////////////////////////////////
function fixtext( tptr, ttype, lastval )
    {
    if( tptr.value=="!!" || tptr.value=='"' ) { tptr.value = lastval; }

    while( 1 )
	{
	if( ttype == "Phone" || ttype == "Notify" )
	    {
	    if( /^[^\d]*(\d\d\d)[^\d]*(\d\d\d)[^\d]*(\d\d\d\d)[^\d]*$/.test(tptr.value) )
		{
		tptr.value = "(" + RegExp.$1 + ")" + RegExp.$2 + "-" + RegExp.$3;
		}
	    }

	var label_ptr = document.getElementById( ttype+"_label_id" );
	if ( tptr.checkValidity() )
	    {
	    label_ptr.style.color = "";
	    enable_update();
	    return false;
	    }
	label_ptr.style.color = "red";
	var msg = new Array();
	if( tptr.title ) { msg.push( tptr.title ); }
	msg.push("Incorrect format, try again:");
	tptr.value = prompt( msg.join("\n"), lastval );
	lastval = tptr.value;
	enable_update();
	}
    }

//////////////////////////////////////////////////////////////////////////
//	User requested an item be moved one up (-1) or one down (1) in	//
//	the list.							//
//////////////////////////////////////////////////////////////////////////
var order_items;
var order_texts;
var order_p;
var order_focus_range = -1;
var order_focus_ind = -1;
function order_swap( direction )
    {
    if( (order_focus_range==0 && (order_focus_ind+direction)==0)
     || (order_focus_range==2 && (order_focus_ind+direction)==order_ranges[order_focus_range].length-1) )
         { return; }

    if( order_focus_ind >= 0 )
	{
	var swp;
	var success = 0;
	if( order_focus_range != 1 )
	    {
	    var new_ind = order_focus_ind + direction;
	    if( new_ind >= 0 && new_ind < order_ranges[order_focus_range].length )
		{
		swp = order_ranges[order_focus_range][order_focus_ind];
		order_ranges[order_focus_range][order_focus_ind] = order_ranges[order_focus_range][new_ind];
		order_ranges[order_focus_range][new_ind] = swp;
		order_focus_ind = new_ind;
		success = 1;
		}
	    }
	if( ! success )
	    {
	    var swp = order_ranges[order_focus_range][order_focus_ind];
	    order_ranges[order_focus_range].splice( order_focus_ind, 1 );
	    // delete order_ranges[order_focus_range][order_focus_ind];
	    order_focus_range += direction;
	    if( direction < 0 )
		{
		order_ranges[order_focus_range].push( swp );
		order_focus_ind = order_ranges[order_focus_range].length - 1;
		}
	    else
		{
		order_ranges[order_focus_range].unshift( swp );
		order_focus_ind = 0;
		}
	    }
	order_redraw();
	order_p.update.disabled=false;
	}
    return false;
    }

var RANGE_INFO =
    [
    { name:"Start with",	style:"background-color:white" },
    { name:"Optimize",		style:"background-color:#b0ffd0" },
    { name:"End with",		style:"background-color:white" }
    ];

//////////////////////////////////////////////////////////////////////////
//	To handle hitting arrow keys					//
//////////////////////////////////////////////////////////////////////////
function keyed(e)
    {
    var ch = e.keyCode;
    if( ch==38 || ch==75 )
        { order_swap(-1); }
    else if( ch=40 || ch==74 )
        { order_swap( 1); }
    }

//////////////////////////////////////////////////////////////////////////
//	Redraw the table with the ordered list (and arrows)		//
//////////////////////////////////////////////////////////////////////////
function order_redraw()
    {
    var s = Array( "<table border=0 cellspacing=1>" );
    for( var range=0; range<order_ranges.length; range++ )
	{
	for( var i=0; i<order_ranges[range].length; i++ )
	    {
	    s.push("<tr "
		+"style='"+
		( range==order_focus_range && i==order_focus_ind
		    ? "background-color:#d0ffff" : "" )
		+"'");
	    if( (range==0 && i==0)
	     || (range==2 && i==order_ranges[range].length-1 ) )
	        {}
	    else
	        {
		s.push( 
		    " onClick='order_focus_range="+range+";order_focus_ind="+i+";order_redraw();'");
		}
	    s.push(">");
	    if( i==0 )
	        {
		s.push(
		    "<th rowspan="+order_ranges[range].length
		    +" style='"+RANGE_INFO[range].style+"'>"
		    + RANGE_INFO[range].name
		    + "</th>" );
		}
	    var itm = order_ranges[range][i];
	    // s.push( "<td>" + itm + "</td>" + order_texts[itm] +"</tr>" );
	    // s.push( "<td>" + itm + "</td>" );
	    s.push( order_texts[itm] +"</tr>" );
	    }
	}
    s.push( "<tr><th colspan=3>",
	"<input type=button width=100% onClick='order_swap(-1);' value='&uarr;'>",
	"<input type=button width=100% onClick='order_swap( 1);' value='&darr;'>",
	"</th></tr>",
	"</table>" );
    // alert("s="+s.join(""));
    order_p.list.innerHTML = s.join("");
    order_ranges_strings = new Array();
    for( var range=0; range<3; range++ )
        { order_ranges_strings.push( order_ranges[range].join(",") ); }
    order_p.var.value = order_ranges_strings.join(':');
    window.onkeydown=function(e){keyed(e);};
    }

//////////////////////////////////////////////////////////////////////////
//	Setup an ordered list on the specified element.			//
//////////////////////////////////////////////////////////////////////////
function order_setup( id_base, ranges_arg, texts_arg )
    {
    order_ranges = ranges_arg;
    order_texts = texts_arg;
    order_p =
        {
	list:		document.getElementById(id_base+"_list_id"),
	var:		document.getElementById(id_base+"_id"),
	update:		document.getElementById(id_base+"_update_id"),
	};
    order_focus_ind = -1;
    order_focus_range = -1;
    order_redraw();
    }

//////////////////////////////////////////////////////////////////////////
//	If all the required fields are field out, enable the "update"	//
//	button.								//
//////////////////////////////////////////////////////////////////////////
function enable_update()
    {
    var disabled=false;
    for( var to_check of CHECK_ON_UPDATE )
    	{
	var lupv = (document.getElementsByName( to_check ))[0];
	if( ! lupv )
	    { alert("Cannot find variable for ["+to_check+"]"); }
	else if( ! lupv.value )
	    {
	    disabled=true;
	    (document.getElementById(to_check+"_label_id")).style.color="red";
	    }
	else
	    {
	    (document.getElementById(to_check+"_label_id")).style.color="";
	    }
	}
    (document.getElementById("update_id")).disabled = disabled;
    }

</script>
</head><body bgcolor="#d0e0f0" link="#c02030" vlink="#10e030">
<div id="body_id">
<form name="form" method="post">
<input type="hidden" name="func">
<input type="hidden" name="arg">
<input type="hidden" name="SID" value="3ctYQpdBU">
<input type="hidden" name="USER" value="chris">
<center>


    <style rel="stylesheet" incsrc="/var/www/routing/sto/routes/common/all.css">
body			{
			background-color: #ddd;
			color: #222;
			font-family: Helvetica;
			font-size: 14px;
			margin: 0;
			padding: 0;
			}
#header			{
			background-color: #ccc;
			background-image: -webkit-gradient(linear, left top, left bottom, from(#ccc), to(#999));
			border-color: #666;
			border-style: solid;
			border-width: 0 0 1px 0;
			}
#header h1		{
			color: #222;
			font-size: 20px;
			font-weight: bold;
			margin: 0 auto;
			padding: 10px 0;
			text-align: center;
			text-shadow: 0px 1px 0px #fff;
			}
ul			{
			list-style: none;
			margin: 10px;
			padding: 0;
			}
ul li a			{
			background-color: #FFF;
			border: 1px solid #999;
			color: #222;
			display: block;
			font-size: 17px;
			font-weight: bold;
			margin-bottom: -1px;
			padding: 12px 10px;
			text-decoration: none;
			}
ul li:first-child a	{
			-webkit-border-top-left-radius: 8px;
			-webkit-border-top-right-radius: 8px;
			}
ul li:last-child a	{
			-webkit-border-bottom-left-radius: 8px;
			-webkit-border-bottom-right-radius: 8px;
			}
ul li a:active,ul li a:hover	{
			background-color:blue;
			color:white;
			}
td			{
			font-size: 14px;
			}
th			{
			font-size: 18px;
			}
button			{
			qfont-size: 35px;
			font-size: 20px;
			// -webkit-appearance: button;
			border-radius: 20px;
			}
#content		{
			padding: 10px;
			text-shadow: 0px 1px 0px #fff;
			}
#content a		{
			color: blue;
			}

.bigbutt		{
			width:	100px;
			height:	100px;
			border-radius: 100px;
			}
select			{
			qfont-size: 35px;
			font-size: 20px;
			}
.bigtext		{
			font-size: 250%;
			}
.fixedtable		{
			position:	absolute;
			qposition:	fixed;
			height:		100%;
			width:		100%;
			top:		0px;
			left:		0px;
			right:		0px;
			bottom:		0px;
			}
.fixedleft		{
			position:	absolute;
			qposition:	fixed;
			height:		100%;
			top:		0px;
			bottom:		0px;
			left:		0px;
			}
.fixedright		{
			position:	absolute;
			qposition:	fixed;
			height:		100%;
			top:		0px;
			bottom:		0px;
			right:		0px;
			}

@media print
{    
    .no-print, .no-print *
			{
			display:	none !important;
			}
}

</style>

    <style rel="stylesheet" media="all and (max-device-width: 600px)" incsrc="/var/www/routing/sto/routes/common/mobile.css">
html		{
		-webkit-text-size-adjust: none;
		touch-action: pan-y; /*prevent user scaling*/
		}

*		{
		-webkit-text-size-adjust: none;
		text-size-adjust: none;
		}

</style>

    <style rel="stylesheet" media="all and (min-device-width: 600px)" incsrc="/var/www/routing/sto/routes/common/desktop.css">

</style>


<style type="text/css">
@media print {
    .no-print, .no-print * { display: none !important; }
    a, a:visited { color: #000 !important; text-decoration:none; }
    }
@media not print {
    .only-print, .only-print * { display: none !important; }

.medbut		{
			font-size: 30px;
			text-align:	left;
			}
</style>

<script type="text/javascript">
//{ INIT
var ROUTE_LENGTH='77';
var ROUTE_NAME='DC Hot spots';
var SECRET='1tuJwz';
var route_types = [];
var stops = [{"patrons":"D_2iG","prefs":"","time_to":"","coords":"38.89879,-77.03364","distance_ref":"","ind":"A","navrules":"","name":"Test Distributor","phone":"(202)000-0000","address":"1600 Pennsylvania Avenue NW, Washington, DC 20500","addrtxt":"1600 Pennsylvania Avenue NW, Washington, DC 20500","pickups":"","total_time_to":"","time_ref":"","distance_to":"","type":"Distributor","total_distance_to":"","note":""},{"ind":"B","distance_ref":"","coords":"38.8898,-77.00589","time_to":"","prefs":"&lt;span style=&sbquo;color:black;background-color:#d0ffff !important;border:1px solid #d0ffff;&sbquo;&gt;New patron&lt;/span&gt;","patrons":"P_2iI","phone":"(202)000-0001","name":"John Capital","navrules":"","total_time_to":5307,"pickups":"","addrtxt":"E Capitol St. and 1st St. NE Washington, DC 20004","address":"E Capitol St. and 1st St. NE Washington, DC 20004","note":"","type":"Patron","total_distance_to":38.5,"distance_to":"","time_ref":""},{"name":"Marion Librarian","phone":"(202)000-0006","navrules":"","patrons":"P_2iN","time_to":62,"prefs":"&lt;span style=&sbquo;color:black;background-color:#d0ffff !important;border:1px solid #d0ffff;&sbquo;&gt;New patron&lt;/span&gt;","distance_ref":0.2,"ind":"C","coords":"38.88763,-77.00474","type":"Patron","total_distance_to":38.7,"time_ref":62,"distance_to":0.2,"note":"","addrtxt":"101 Independence Ave SE, Washington, DC 20540","address":"101 Independence Ave SE, Washington, DC 20540","pickups":"","total_time_to":5369},{"coords":"38.887853,-77.040587","distance_ref":1.9,"ind":"D","patrons":"P_2iR","time_to":442,"prefs":"&lt;span style=&sbquo;color:black;background-color:#d0ffff !important;border:1px solid #d0ffff;&sbquo;&gt;New patron&lt;/span&gt;","navrules":"","name":"Dwight Eisenhour","phone":"(202)000-0010","pickups":"","total_time_to":5811,"address":"1750 Independence Ave SW, Washington, DC 20024","addrtxt":"1750 Independence Ave SW, Washington, DC 20024","note":"","time_ref":442,"distance_to":1.9,"total_distance_to":40.6,"type":"Patron"},{"phone":"(202)000-0003","name":"George Washington","navrules":"","distance_ref":0.6,"ind":"E","coords":"38.88898,-77.032958","patrons":"P_2iK","time_to":140,"prefs":"&lt;span style=&sbquo;color:black;background-color:#d0ffff !important;border:1px solid #d0ffff;&sbquo;&gt;New patron&lt;/span&gt;","note":"","total_distance_to":41.2,"type":"Patron","distance_to":0.6,"time_ref":140,"pickups":"","total_time_to":5951,"addrtxt":"2 15th St NW, Washington, DC 20024","address":"2 15th St NW, Washington, DC 20024"},{"navrules":"","name":"Thomas MaGoo","phone":"(202)000-0005","coords":"38.89871,-77.03364","distance_ref":0.7,"ind":"F","time_to":245,"prefs":"&lt;span style=&sbquo;color:black;background-color:#d0ffff !important;border:1px solid #d0ffff;&sbquo;&gt;New patron&lt;/span&gt;","patrons":"P_2iM","note":"","distance_to":0.7,"time_ref":245,"type":"Patron","total_distance_to":41.9,"total_time_to":6196,"pickups":"","address":"500 Pennsylvania Avenue NW #1428, Washington, DC 20220","addrtxt":"500 Pennsylvania Avenue NW #1428, Washington, DC 20220"},{"pickups":"","total_time_to":6511,"addrtxt":"511 10th St NW, Washington, DC 20004","address":"511 10th St NW, Washington, DC 20004","note":"Balconies not available.  Deliver in the front.","total_distance_to":42.5,"type":"Patron","distance_to":0.6,"time_ref":315,"distance_ref":0.6,"ind":"G","coords":"38.89659,-77.02598","patrons":"P_2iP","prefs":"&lt;span style=&sbquo;color:black;background-color:#c0c0ff !important;border:1px solid #c0c0ff;&sbquo;&gt;USDA box&lt;/span&gt;, &lt;span style=&sbquo;color:black;background-color:#ffb0b0 !important;border:1px solid #ffb0b0;&sbquo;&gt;Special meal&lt;/span&gt;, &lt;span style=&sbquo;color:black;background-color:#d0ffff !important;border:1px solid #d0ffff;&sbquo;&gt;New patron&lt;/span&gt;","time_to":315,"name":"John Ford","phone":"(202)000-0008","navrules":""},{"total_time_to":6768,"pickups":"","addrtxt":"Constitution Ave. NW, Washington, DC 20565","address":"Constitution Ave. NW, Washington, DC 20565","note":"","type":"Patron","total_distance_to":43.1,"distance_to":0.6,"time_ref":257,"ind":"H","distance_ref":0.6,"coords":"38.892206,-77.018777","time_to":257,"prefs":"&lt;span style=&sbquo;color:black;background-color:#ffb0b0 !important;border:1px solid #ffb0b0;&sbquo;&gt;No frozen bag&lt;/span&gt;, &lt;span style=&sbquo;color:black;background-color:#d0ffff !important;border:1px solid #d0ffff;&sbquo;&gt;New patron&lt;/span&gt;","patrons":"P_2iQ","phone":"(202)000-0009","name":"Monty Picasso","navrules":""},{"phone":"(202)000-0002","name":"Abraham Lincoln","navrules":"","ind":"I","distance_ref":0.4,"coords":"38.89482,-77.01756","patrons":"P_2iJ","prefs":"&lt;span style=&sbquo;color:black;background-color:#30ffff !important;border:1px solid #30ffff;&sbquo;&gt;2 dogs&lt;/span&gt;, &lt;span style=&sbquo;color:black;background-color:#d0ffff !important;border:1px solid #d0ffff;&sbquo;&gt;New patron&lt;/span&gt;","time_to":118,"note":"","type":"Patron","total_distance_to":43.5,"time_ref":118,"distance_to":0.4,"pickups":"","total_time_to":6886,"addrtxt":"451 Indiana Ave NW, Washington, DC 20001","address":"451 Indiana Ave NW, Washington, DC 20001"},{"time_to":2159,"prefs":"&lt;span style=&sbquo;color:black;background-color:#d0ffff !important;border:1px solid #d0ffff;&sbquo;&gt;New patron&lt;/span&gt;","patrons":"P_2iL","distance_ref":17.4,"ind":"J","coords":"38.711032,-77.088291","phone":"(202)000-0004","name":"Martha Washington","navrules":"","addrtxt":"3200 Mount Vernon Memorial Hwy, Mt Vernon, VA 22121","address":"3200 Mount Vernon Memorial Hwy, Mt Vernon, VA 22121","total_time_to":9045,"pickups":"","total_distance_to":60.9,"type":"Patron","time_ref":2159,"distance_to":17.4,"note":""},{"patrons":"P_2iO","time_to":1569,"prefs":"&lt;span style=&sbquo;color:black;background-color:#d0ffff !important;border:1px solid #d0ffff;&sbquo;&gt;New patron&lt;/span&gt;","coords":"38.883913,-77.064892","ind":"K","distance_ref":16.1,"navrules":"","name":"Robert E. Lee","phone":"(202)000-0007","address":"1 Memorial Ave. Arlington, Virginia 22211","addrtxt":"1 Memorial Ave. Arlington, Virginia 22211","pickups":"","total_time_to":10614,"distance_to":16.1,"time_ref":1569,"type":"Patron","total_distance_to":77,"note":""},{"note":"","total_distance_to":"","type":"Distributor","distance_to":"","time_ref":"","total_time_to":"","pickups":"","addrtxt":"1600 Pennsylvania Avenue NW, Washington, DC 20500","address":"1600 Pennsylvania Avenue NW, Washington, DC 20500","name":"Test Distributor","phone":"(202)000-0000","navrules":"","ind":"L","distance_ref":"","coords":"38.89879,-77.03364","time_to":"","prefs":"","patrons":"D_2iG"}];
var route_pickup_list = [];
var bag_types = [ 'Big', 'Small' ];
//} INIT
</script>

<script type="text/javascript" incsrc="/var/www/routing/sto/routes/common/routes.js">
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
//	Javascript included in .cgi files with routes sent to drivers.	//
//	Chris Caldwell, 04/29/2022					//
//////////////////////////////////////////////////////////////////////////
//
//////////////////////////////////////////////////////////////////////////
//	Used for testing.  Settable by ?debug=1				//
//////////////////////////////////////////////////////////////////////////
var DEBUG =
    {
    checkpointing:	0,
    functions:		0,
    flow:		0,
    //position:		1,
    debug:		0,
    applewp:		"DADDR",	// vs "WAYPOINTS"
    rest_of_trip:	1
    };

</script><script>if(DEBUG.checkpointing) {alert("00000 /var/www/routing/sto/routes/common/routes.js@0031");}</script><script>
var MAPQUEST_KEY	= "dxMEhIJ2eQ1jS8098HjxwiUj8W0xjJwH";
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
//	We use Apple maps to tell us how to get to the next stop	//
//	because it interfaces nicely with Carplay.			//
//	Maybe changed by browser_dependent()				//
//////////////////////////////////////////////////////////////////////////
var ROUTE_HANDLER		= "Mapquest";
var DESTINATION_HANDLER		= "Google";

//////////////////////////////////////////////////////////////////////////
//	Global variables.						//
//////////////////////////////////////////////////////////////////////////
var map_handlers = new Array();	// Hash of handlers names to routines
</script><script>if(DEBUG.checkpointing) {alert("00001 /var/www/routing/sto/routes/common/routes.js@0080");}</script><script>
var display_order;		// Array of order to display stops
</script><script>if(DEBUG.checkpointing) {alert("00002 /var/www/routing/sto/routes/common/routes.js@0082");}</script><script>
var current_position;		// Which stop we are currently at
</script><script>if(DEBUG.checkpointing) {alert("00003 /var/www/routing/sto/routes/common/routes.js@0084");}</script><script>

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
</script><script>if(DEBUG.checkpointing) {alert("00004 /var/www/routing/sto/routes/common/routes.js@0099");}</script><script>

//////////////////////////////////////////////////////////////////////////
//	If flag set, write message some place useful.			//
//////////////////////////////////////////////////////////////////////////
function debug_out( flag, msg )
    {
    if( flag ) { alert( msg ); }
    }

//////////////////////////////////////////////////////////////////////////
//	Overwritten code to decide what browser to operate as.		//
//	All evil browser dependence is supposed to end up here.		//
//////////////////////////////////////////////////////////////////////////
var BROWSERS =
    {
    "Firefox":	"Firefox",
    "Chrome":	"Chrome",
    "Safari":	"Safari",
    "Opera":	"Opera",
    "MSIE":	"MSIE",
    "Trident":	"MSIE",
    "Edge":	"Edge"
    };
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
	    CURRENT_BROWSER = try_browser;
	    break;
	    }
	}
    if( CURRENT_BROWSER == "Safari" )
        {
	GPS_TIMEOUT = 5000;
	DESTINATION_HANDLER = "Apple";
	}
    if( DEBUG.flow )
	{
	alert(
	    "CURRENT_BROWSER="+CURRENT_BROWSER+
	    "\nGPS_TIMEOUT="+GPS_TIMEOUT+
	    "\nDESTINATION_HANDLER="+DESTINATION_HANDLER+
	    "\nROUTE_HANDLER="+ROUTE_HANDLER);
	}
    }

//////////////////////////////////////////////////////////////////////////
//	Return a hash of hashes with order available.			//
//////////////////////////////////////////////////////////////////////////
function indexed_hash( array_of_hashes, flds )
    {
    debug_out( DEBUG.functions, "function start indexed_hash()");
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
</script><script>if(DEBUG.checkpointing) {alert("00005 function sanity /var/www/routing/sto/routes/common/routes.js@0209");}</script><script>
function sanity(n)		// Currently uncalled.
    {				// Change as needed.
    debug_out( DEBUG.functions, "function start sanity()");
    for( var i=0; i<stops.length; i++ )
	{
        if( stops[i].status == undefined )
	{ alert("At "+n+" i="+i+" has seen insanity!!!"); }
	}
    }

//////////////////////////////////////////////////////////////////////////
//	Print an error message and die with a stack trace.		//
//////////////////////////////////////////////////////////////////////////
</script><script>if(DEBUG.checkpointing) {alert("00006 function fatal /var/www/routing/sto/routes/common/routes.js@0223");}</script><script>
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
</script><script>if(DEBUG.checkpointing) {alert("00007 function ebid /var/www/routing/sto/routes/common/routes.js@0235");}</script><script>
function ebid( id )
    {
    // debug_out( DEBUG.functions, "function start ebid()");
    return document.getElementById(id) ||
	fatal("Cannot find element for id ["+id+"]");
    }

//////////////////////////////////////////////////////////////////////////
//	Draw a one-of prompt.						//
//////////////////////////////////////////////////////////////////////////
</script><script>if(DEBUG.checkpointing) {alert("00008 function oneof /var/www/routing/sto/routes/common/routes.js@0246");}</script><script>
function oneof( asking, prompt_text, answers )
    {
    debug_out( DEBUG.functions, "function start oneof()");
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
</script><script>if(DEBUG.checkpointing) {alert("00009 function reset /var/www/routing/sto/routes/common/routes.js@0274");}</script><script>
function reset_route( arg )
    {
    debug_out( DEBUG.functions, "function start reset_route()");
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
</script><script>if(DEBUG.checkpointing) {alert("00010 function bake /var/www/routing/sto/routes/common/routes.js@0322");}</script><script>
function bake_cookie( called_from )
    {
    debug_out( DEBUG.functions, "function start bake_cookie()");
    // alert("Bake_cookie called from "+called_from);
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
    // alert("Bake_cookie("+called_from+") with "+dough.length+" creates ["+c+"]");
    // document.cookie = c;
    //alert("localStorage.setItem("+COOKIE_NAME+","+v+")");
    localStorage.setItem( COOKIE_NAME, v );
    }

//////////////////////////////////////////////////////////////////////////
//	Called when cookie found.  Eat it!  (interpret it)		//
//////////////////////////////////////////////////////////////////////////
</script><script>if(DEBUG.checkpointing) {alert("00011 /var/www/routing/sto/routes/common/routes.js@0349");}</script><script>
</script><script>if(DEBUG.checkpointing) {alert("00012 function eat /var/www/routing/sto/routes/common/routes.js@0350");}</script><script>
function eat_cookie( c )
    {
    debug_out( DEBUG.functions, "function start eat_cookie()");
    var dough = c . split( SEP );
    // alert("eat_cookie dough.length="+dough.length+", c = ["+c+"]");
    if( dough.shift() == SECRET )
	{	// Eat that cookie!
	current_stop = dough.shift();
	// alert("Eating ["+dough.join(",")+"]");
	for( var stop_number=0; stop_number<stops.length; stop_number++ )
	    {
	    for( const v of RECIPE )
		{
		var from_dough = dough.shift();
	        // alert("cookie["+stop_number+","+v+"]=["+(from_dough||"?")+"]");
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
</script><script>if(DEBUG.checkpointing) {alert("00013 function find /var/www/routing/sto/routes/common/routes.js@0383");}</script><script>
function find_cookie()
    {
    debug_out( DEBUG.functions, "function start find_cookie()");
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
    debug_out( DEBUG.functions, "function find_cookie() done.");
    return false;	// No suitable cookie found, return hungry.
    }

//////////////////////////////////////////////////////////////////////////
//	Try to cut down on size of data being sent upstream.		//
//////////////////////////////////////////////////////////////////////////
</script><script>if(DEBUG.checkpointing) {alert("00014 function compact /var/www/routing/sto/routes/common/routes.js@0410");}</script><script>
function compact_string( s )
    {
    debug_out( DEBUG.functions, "function start compact_string()");
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
</script><script>if(DEBUG.checkpointing) {alert("00015 function setup /var/www/routing/sto/routes/common/routes.js@0426");}</script><script>
function setup_map_order( first_stop, last_stop )
    {
    debug_out( DEBUG.functions, "function start setup_map_order()");
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
</script><script>if(DEBUG.checkpointing) {alert("00016 function coord /var/www/routing/sto/routes/common/routes.js@0458");}</script><script>
function coord_string( c )
    {
    debug_out( DEBUG.functions, "function start coord_string()");
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
</script><script>if(DEBUG.checkpointing) {alert("00017 function same /var/www/routing/sto/routes/common/routes.js@0473");}</script><script>
function same_pos( p0, p1 )
    {
    debug_out( DEBUG.functions, "function start same_pos()");
    return ( coord_string(p0) == coord_string(p1) );
    }

//////////////////////////////////////////////////////////////////////////
//	Many of the mappers need separate arrays for name, address and	//
//	GPS coordinates.  Avoids replicating code all over the place.	//
//////////////////////////////////////////////////////////////////////////
</script><script>if(DEBUG.checkpointing) {alert("00018 function split /var/www/routing/sto/routes/common/routes.js@0484");}</script><script>
function split_out(for_platform)
    {
    debug_out( DEBUG.functions, "function start split_out()");
    var latlong_string = for_platform.toLowerCase() + " uses latlong";

    var namelist	=new Array();
    var preflist	=new Array();
    var nrlist		=new Array();
    var addrlist	=new Array();
    var cordlist	=new Array();
    for( var stop_number=0; stop_number<map_order.length; stop_number++ )
	{
	var order_ind = map_order[stop_number];
	// alert("map_order["+stop_number+"] is ["+order_ind+"]");
	var nr = "";
	if( order_ind < 0 )
	    {
	    namelist.push( "Current position" );
	    addrlist.push( "Current position" );
	    cordlist.push( current_position.latitude+
		","+current_position.longitude );
	    nrlist.push( latlong_string );
	    // alert("Pushing latlong_string ["+latlong_string+"]");
	    }
	else
	    {
	    namelist.push( stops[map_order[stop_number]].pretty  );
	    addrlist.push( stops[map_order[stop_number]].address );
	    cordlist.push( stops[map_order[stop_number]].coords  );
	    nrlist.push( stops[map_order[stop_number]].navrules  );
	    // alert("Pushing navrules");
	    }
	if( nrlist[nrlist.length-1] == latlong_string )
	    { preflist.push( cordlist[cordlist.length-1] ); }
	else
	    { preflist.push( addrlist[addrlist.length-1] ); }
	}
    if( DEBUG.flow )
	{
	var SP2 = "\n  ";
	var SP4 = "\n    ";
	var to_print =
	    "split_out("+for_platform+") returning"
	    + SP2+"namelist:"+SP4+namelist.join(SP4)
	    + SP2+"preflist:"+SP4+preflist.join(SP4)
	    + SP2+"nrlist:"+SP4+nrlist.join(SP4)
	    + SP2+"addrlist:"+SP4+addrlist.join(SP4)
	    + SP2+"cordlist:"+SP4+cordlist.join(SP4)
	    ;
	alert( to_print );
	}
    return {namelist,preflist,nrlist,addrlist,cordlist};
    }

//////////////////////////////////////////////////////////////////////////
//	Return a string escaped properly so it can be used as a URL.	//
//////////////////////////////////////////////////////////////////////////
</script><script>if(DEBUG.checkpointing) {alert("00019 function safe /var/www/routing/sto/routes/common/routes.js@0542");}</script><script>
function safe_url( str )
    {
    debug_out( DEBUG.functions, "function start safe_url()");
    str = str.replace(/United States,.*/,"United States");
    // str = str.replace(/[^A-Za-z0-9\.\- ]+/g,"_");
    str = str.replace(/ /g,"+");
    return str;
    }

//////////////////////////////////////////////////////////////////////////
//	Get *ALL* properties from an object including inherited ones.	//
//////////////////////////////////////////////////////////////////////////
</script><script>if(DEBUG.checkpointing) {alert("00020 function list /var/www/routing/sto/routes/common/routes.js@0555");}</script><script>
function list_all_properties(o)
    {
    debug_out( DEBUG.functions, "function start list_all_properties()");
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
</script><script>if(DEBUG.checkpointing) {alert("00021 function hash /var/www/routing/sto/routes/common/routes.js@0570");}</script><script>
function hash_to_string_recurse( comflag, indent, txt, v )
    {
    debug_out( DEBUG.functions, "function start hash_to_string_properties()");
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
</script><script>if(DEBUG.checkpointing) {alert("00022 function hash /var/www/routing/sto/routes/common/routes.js@0612");}</script><script>
function hash_to_string( txt, v )
    {
    debug_out( DEBUG.functions, "function start hash_to_string()");
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

//////////////////////////////////////////////////////////////////////////
//	Beginning of mapquest specific routines.			//
//////////////////////////////////////////////////////////////////////////
//	Called by createMap() for each waypoint to show what is there.	//
//	(goto_map_better_Mapquest helper)				//
//////////////////////////////////////////////////////////////////////////
</script><script>if(DEBUG.checkpointing) {alert("00023 function anyMarker /var/www/routing/sto/routes/common/routes.js@0635");}</script><script>
function anyMarker( location, stopNumber )
    {
    debug_out( DEBUG.functions, "function start anyMarker()");
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
</script><script>if(DEBUG.checkpointing) {alert("00024 function update /var/www/routing/sto/routes/common/routes.js@0673");}</script><script>
function update_map_for_Mapquest()
    {
    debug_out( DEBUG.functions, "function start update_map_for_Mapquest()");
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
</script><script>if(DEBUG.checkpointing) {alert("00025 function callback /var/www/routing/sto/routes/common/routes.js@0715");}</script><script>
function callback_for_Mapquest_route( err, response )
    {
    debug_out( DEBUG.functions, "function start callback_for_Mapquest_route()");
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
</script><script>if(DEBUG.checkpointing) {alert("00026 function start /var/www/routing/sto/routes/common/routes.js@0745");}</script><script>
function start_getting_Mapquest_route( optimize_flag, need_map_flag )
    {
    debug_out( DEBUG.functions, "function start start_getting_Mapquest_route()");
    for( var stop_number=0; stop_number<stops.length; stop_number++ )
	{
	var stopping = need_to_visit( stop_number );
	if( stops[stop_number].oldstatus != stopping )
	    {	// Something has changed, last route worthless
	    last_route_response=0;
	    }
	stops[stop_number].oldstatus = stopping;
	}
       
    let {namelist,preflist,nrlist,addrlist,cordlist} = split_out("Mapquest");
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
//	Return true if stop specified stop.				//
//////////////////////////////////////////////////////////////////////////
</script><script>if(DEBUG.checkpointing) {alert("00027 function need /var/www/routing/sto/routes/common/routes.js@0789");}</script><script>
function need_to_visit( stopnum )
    {
    // debug_out( DEBUG.functions, "function start need_to_visit()");
    return(	stops[stopnum].status=="Untouched"
	||	stops[stopnum].status=="Unvisited" );
    }

//////////////////////////////////////////////////////////////////////////
//	Put debugging information in the debugging sub window.		//
//////////////////////////////////////////////////////////////////////////
</script><script>if(DEBUG.checkpointing) {alert("00028 function position /var/www/routing/sto/routes/common/routes.js@0800");}</script><script>
function position_trail()
    {
    debug_out( DEBUG.functions, "function start position_trail()");
    // if( DEBUG.position )
    var s = "<center><table bgcolor='#ffffc0' border=1 style='border-collapse:collapse;'>"
		+ "<tr><th>Ind</th><th>Where</th><th>When</th></tr>\n";
    var l = route_history.length;
    for( var i=0; i<l; i++ )
	{
	if( i<3 || i>l-5 )
	    {
	    var d = new Date(route_history[i].when);
	    s += "<tr>"
		+ "<td align=right>" + i + "</td>"
		+ "<td>" + coord_string(route_history[i]) + "</td>"
		+ "<td>" + d.toUTCString() + "</td></tr>\n";
	    }
	else if( i == 3 )
	    {
	    s += "<tr><th colspan=3>...</th></tr>\n";
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
</script><script>if(DEBUG.checkpointing) {alert("00029 function drop /var/www/routing/sto/routes/common/routes.js@0836");}</script><script>
function drop_a_pin()
    {
    debug_out( DEBUG.functions, "function start drop_a_pin()");
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
		    // alert("We are not moving, l-1="+(l-1)+", now="+route_history[l-1].when);
		    return;
		    }
		}
	    }
	// alert("We are moving, now="+now);
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
</script><script>if(DEBUG.checkpointing) {alert("00030 function move /var/www/routing/sto/routes/common/routes.js@0874");}</script><script>
function move_some()
    {
    debug_out( DEBUG.functions, "function start move_some()");
    for( const axis of [ "latitude", "longitude" ] )
	{
	TEST_POSITION[axis]+=( Math.random()*JITTER[axis] - JITTER[axis]/2.0 );
	current_position[axis] = TEST_POSITION[axis];
	}
    // alert("New position ["+current_position.latitude+","+current_position.longitude+"]");
    drop_a_pin();
    }

//////////////////////////////////////////////////////////////////////////
//	Get the current position
//////////////////////////////////////////////////////////////////////////
var last_current_position_callback;
</script><script>if(DEBUG.checkpointing) {alert("00031 function get /var/www/routing/sto/routes/common/routes.js@0891");}</script><script>
function get_current_position( current_position_callback )
    {
    debug_out( DEBUG.functions, "function start get_current_position()");
    last_current_position_callback = current_position_callback;
    if( geoposition_timer >= 0 ) { clearTimeout( geoposition_timer ); }
    navigator.geolocation.getCurrentPosition
	(
	function(position)
	    {
	    current_position =
		( ( DEBUG.debug || ! position.coords.latitude )
		?	TEST_POSITION
		:	{    latitude:		position.coords.latitude,
			     longitude:		position.coords.longitude } );
	    // alert("Position="+position.coords.latitude+","+position.coords.longitude);
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
//	    alert("getCurrentPosition failed:  "+evt.message
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
    debug_out( DEBUG.functions, "function get_current_position returning()");
    }

//////////////////////////////////////////////////////////////////////////
//	Something has changed and user wants to figure out what best	//
//	route should be now.  For now, display new map.			//
//////////////////////////////////////////////////////////////////////////
</script><script>if(DEBUG.checkpointing) {alert("00032 function reroute /var/www/routing/sto/routes/common/routes.js@0938");}</script><script>
function reroute()
    {
    debug_out( DEBUG.functions, "function start Reroute()");
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
//	Return list with redundant entries removed.			//
//////////////////////////////////////////////////////////////////////////
</script><script>if(DEBUG.checkpointing) {alert("00033 function remove /var/www/routing/sto/routes/common/routes.js@0963");}</script><script>
function remove_redundancies( old_list )
    {
    debug_out( DEBUG.functions, "function start remove_redundancies()");
    var last_val;
    var ret = new Array();
    for( const old_val of old_list )
	{
	if( typeof(last_val)==='undefined' || old_val!=last_val )
	    {
	    ret.push( old_val );
	    last_val = old_val;
	    }
	}
    return ret;
    }

//////////////////////////////////////////////////////////////////////////
//	Update the html element with id=map to contain complete route.	//
//////////////////////////////////////////////////////////////////////////
</script><script>if(DEBUG.checkpointing) {alert("00034 function goto /var/www/routing/sto/routes/common/routes.js@0983");}</script><script>
function goto_Mapquest_map()
    {
    debug_out( DEBUG.functions, "function goto_Mapquest_map()");
    // Assume already optimized, draw map
    start_getting_Mapquest_route(false,true);
    return false;
    }
map_handlers.Mapquest = goto_Mapquest_map;

//////////////////////////////////////////////////////////////////////////
//	Invoke the Google maps web site to show the entire route.	//
//////////////////////////////////////////////////////////////////////////
</script><script>if(DEBUG.checkpointing) {alert("00035 function goto /var/www/routing/sto/routes/common/routes.js@0996");}</script><script>
function goto_Google_map()
    {
    debug_out( DEBUG.functions, "function start goto_Google_map()");
    var ret = new Array( "https://www.Google.com/maps/dir/?api=1" );
    let {namelist,preflist,nrlist,addrlist,cordlist} = split_out("Google");

    if( preflist.length > 0 )
	{
	ret.push(
	    "destination_place_id=" + namelist[ namelist.length-1 ],
	    "destination=" + preflist[ preflist.length-1 ] );
	}
    if( preflist.length > 1 )
	{
	ret.push(
	    "origin_place_id=" + namelist[ 0 ],
	    "origin=" + preflist[ 0 ] );
	}
    if( preflist.length > 2 )
	{
	ret.push(
	    "waypoint_place_ids=" +
		namelist.slice( 1, namelist.length-2 ).join("%7c"),
	    "waypoints=" +
		preflist.slice( 1, preflist.length-2 ).join("%7c") );
	}

    return ret.join("&");
    }
map_handlers.Google = goto_Google_map;

//////////////////////////////////////////////////////////////////////////
//	Invoke the Apple maps web site to show the entire route.	//
//////////////////////////////////////////////////////////////////////////
</script><script>if(DEBUG.checkpointing) {alert("00036 function goto /var/www/routing/sto/routes/common/routes.js@1031");}</script><script>
function goto_Apple_map()
    {
    debug_out( DEBUG.functions, "function start goto_Apple_map()");
    var ret = new Array( "https://maps.Apple.com/?dirflg=d" );
    let {namelist,preflist,nrlist,addrlist,cordlist} = split_out("Apple");

    if( DEBUG.flow )
	{
	var output = "preflist.length = " + preflist.length;
	for( var i=0; i<preflist.length; i++ )
	    { output += ("\n" + i + ": " + preflist[i]); }
	alert(output);
	}

    var source_supplied;
    var start_dest_from = 0;
    // if( preflist.length>1 && namelist[0]!="Current position" )
    if( 0 )
	{
	source_supplied = preflist[0];
	start_dest_from = 1;
	}
    if( DEBUG.flow )
        { alert("source_supplied=["+source_supplied+"], start_dest_from="+start_dest_from); }
    if( DEBUG.applewp=="DADDR" )
	{
	if( source_supplied )
	    { ret.push( "saddr=" + source_supplied ); }
	if( DEBUG.flow )
	    { alert("daddr logic length="+preflist.length+", ret length="+ret.length); }
	if( preflist.length > 0 )
	    {
	    ret.push( "daddr=" +
		remove_redundancies(
		    preflist.slice( start_dest_from, preflist.length )
		).join("&daddr=") );
	    if( DEBUG.flow )
		{ alert("last entry was ["+preflist[preflist.length-1]+"]"); }
	    }
	if( DEBUG.flow )
	    { alert("now daddr logic length="+preflist.length+", ret length="+ret.length); }
	}
    else	// if( DEBUG.applewp=="WAYPOINTS" ) now default
	{
	if( preflist.length > 0 )
	    { ret.push( "daddr=" + preflist[ preflist.length-1 ] ); }
	if( source_supplied )
	    { ret.push( "saddr=" + source_supplied ); }
	if( preflist.length > 2 )
	    {
	    ret.push( "waypoints=" +
		preflist.slice( start_dest_from, preflist.length-1 ).join("%7c") );
	    }
	}

    if( DEBUG.flow )
	{ alert("URL is [ "+ret.join("&")+" ]"); }
    return ret.join("&");
    }
map_handlers.Apple = goto_Apple_map;

//////////////////////////////////////////////////////////////////////////
//	Figure out which mapper we're using it and invoke it.		//
//////////////////////////////////////////////////////////////////////////
</script><script>if(DEBUG.checkpointing) {alert("00037 function map /var/www/routing/sto/routes/common/routes.js@1096");}</script><script>
function map_dispatcher( handler )
    {
    debug_out( DEBUG.functions, "function start map_dispatcher()");
    if( DEBUG.flow )
	{ alert("map_dispatcher("+handler+")"); }
    if( map_handlers[handler] )
	{ return (map_handlers[handler])(); }

    alert("map_dispatcher called with " + (handler?handler:"UNDEFINED") );
    }

//////////////////////////////////////////////////////////////////////////
//	Create arrays to call an appropriate system dependent route	//
//	mapper, figure out which one to call, and call it.		//
//////////////////////////////////////////////////////////////////////////
var goto_map_ind;
var goto_map_handler;
</script><script>if(DEBUG.checkpointing) {alert("00038 function goto /var/www/routing/sto/routes/common/routes.js@1114");}</script><script>
function goto_map_callback()
    {
    debug_out( DEBUG.functions, "function start goto_map_callback()");
    var ind = goto_map_ind;
    var handler = goto_map_handler;
    var save_map_order = map_order;
    if( DEBUG.rest_of_trip )
        { setup_map_order( (ind>=0?ind:0), stops.length-1 ); }
    else
        { setup_map_order( (ind>=0?ind:0), (ind>=0?ind:stops.length-1) ); }

    // alert("goto_map_callback(handler="+handler+"), ROUTE_HANDLER="+ROUTE_HANDLER+", DESTINATION_HANDLER="+DESTINATION_HANDLER+", len="+map_order.length);
    var use_mapper =
        ( handler		? handler
	: map_order.length <= 2	? DESTINATION_HANDLER
	// : DEBUG.rest_of_trip	? "Apple"
	:			  DESTINATION_HANDLER );
    var url = map_dispatcher( use_mapper );
    // alert("url=["+url+"]");

    if( url )
	{
	if( DEBUG.flow ) { alert("url="+url); }
	var win = window.open( url, "map_window" );
	if( win )
	    { win.focus(); }
	// window.focus();
	}
    map_order = save_map_order;
    return true;
    }

</script><script>if(DEBUG.checkpointing) {alert("00039 function goto /var/www/routing/sto/routes/common/routes.js@1147");}</script><script>
function goto_map( ind, handler )
    {
    debug_out( DEBUG.functions, "function start goto_map()");
    if( DEBUG.destination_handler )
	{ DESTINATION_HANDLER = DEBUG.destination_handler; }
    if( DEBUG.route_handler )
	{ ROUTE_HANDLER = DEBUG.route_handler; }
    if( ind < 0 && ! handler  )
	{
	// alert("CMC not Ignoring...");
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
</script><script>if(DEBUG.checkpointing) {alert("00040 function make /var/www/routing/sto/routes/common/routes.js@1169");}</script><script>
function make_call( ind )
    {
    debug_out( DEBUG.functions, "function start make_call()");
    document.location.href = "tel:" + stops[ind].phone;
    }

//////////////////////////////////////////////////////////////////////////
//	Invoked when user wants to call person at stop.			//
//////////////////////////////////////////////////////////////////////////
</script><script>if(DEBUG.checkpointing) {alert("00040a function make /var/www/routing/sto/routes/common/routes.js@1179");}</script><script>
function make_text( ind )
    {
    debug_out( DEBUG.functions, "function start make_text()");
    document.location.href = "sms:" + stops[ind].phone;
    }

//////////////////////////////////////////////////////////////////////////
//	Call to emphasize or not emphasize (and colorize) the specified	//
//	id.  Used to show which stop on the route we're at.		//
//////////////////////////////////////////////////////////////////////////
</script><script>if(DEBUG.checkpointing) {alert("00041 function emphasize /var/www/routing/sto/routes/common/routes.js@1190");}</script><script>
function emphasize( elemid, emphasis_flag, col )
    {
    debug_out( DEBUG.functions, "function start emphasize()");
    var p = (ebid(elemid)).style;
    p.backgroundColor = col;

//	Turns out the following is not that useful.  Color is more useful.
//	p.fontWeight	= ( emphasis_flag ? "bold"	: "" );
//	p.fontStyle	= ( emphasis_flag ? "italic"	: "" );
    }

//////////////////////////////////////////////////////////////////////////
//	Assume we're somewhere in 50 United States			//
//////////////////////////////////////////////////////////////////////////
</script><script>if(DEBUG.checkpointing) {alert("00042 function short /var/www/routing/sto/routes/common/routes.js@1205");}</script><script>
function short_address( a )
    {
    // debug_out( DEBUG.functions, "function start short_address()");
    return	( /(.*,\w\w),(|\d\d\d\d\d|\d\d\d\d\d-\d\d\d\d),(US|United States)/.test(a)
		? RegExp.$1 : a );
    }

//////////////////////////////////////////////////////////////////////////
//	Return a link which goes nowhere.				//
//////////////////////////////////////////////////////////////////////////
</script><script>if(DEBUG.checkpointing) {alert("00043 function null /var/www/routing/sto/routes/common/routes.js@1216");}</script><script>
function null_link( txt )
    {
    // debug_out( DEBUG.functions, "function start null_link()");
    return "<a href='javascript:void(0);'>" + txt + "</a>";
    }

//////////////////////////////////////////////////////////////////////////
//	Return list of steps in most useful order.			//
//////////////////////////////////////////////////////////////////////////
var last_display_order;
</script><script>if(DEBUG.checkpointing) {alert("00044 function get /var/www/routing/sto/routes/common/routes.js@1227");}</script><script>
function get_display_order()
    {
    debug_out( DEBUG.functions, "function start get_display_order()");
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
 	    // alert("sequence_ind="+sequence_ind+", map_order_ind="+map_order_ind+", stop_ind="+stop_ind+", last_from="+last_from+", sequence_length="+last_route_response.route.locationSequence.length+", legs.length="+last_route_response.route.legs.length);
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
		// alert("Setting "+stops[stop_ind].name+".route_from to "+stops[stop_ind].route_from);
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
</script><script>if(DEBUG.checkpointing) {alert("00045 function distance /var/www/routing/sto/routes/common/routes.js@1303");}</script><script>
function distance_string(d)
    {
    debug_out( DEBUG.functions, "function start distance_string()");
    return ( d ? Math.floor(d*10.0+0.5)/10.0 : "?" );
    }

//////////////////////////////////////////////////////////////////////////
//	Return HH:MM:SS from a javascript time.				//
//////////////////////////////////////////////////////////////////////////
</script><script>if(DEBUG.checkpointing) {alert("00046 function time /var/www/routing/sto/routes/common/routes.js@1313");}</script><script>
function time_string(t)
    {
    debug_out( DEBUG.functions, "function start time_string()");
    return ( t ? new Date(1000*t).toISOString().substr(11,8) : "?" );
    }

//////////////////////////////////////////////////////////////////////////
//	Return name of stop by stop number.				//
//////////////////////////////////////////////////////////////////////////
</script><script>if(DEBUG.checkpointing) {alert("00047 function stop /var/www/routing/sto/routes/common/routes.js@1323");}</script><script>
function stop_string( n )
    {
    debug_out( DEBUG.functions, "function start stop_string()");
    // return	( (typeof(n)=='undefined'||n=="")	? "?"
    return	( typeof(n)=='undefined'		? ""
		: n < 0					? "start"
		:					stops[n].name );
    }

//////////////////////////////////////////////////////////////////////////
//	Set position to coordinates specified (instead of whatever GPS	//
//	says) or if they are already that, let them float again.	//
//////////////////////////////////////////////////////////////////////////
</script><script>if(DEBUG.checkpointing) {alert("00048 function set /var/www/routing/sto/routes/common/routes.js@1337");}</script><script>
function set_test_pos( new_coords )
    {
    debug_out( DEBUG.functions, "function start set_test_pos()");
    var old_test_position = coord_string( TEST_POSITION );
    if( same_pos( TEST_POSITION, new_coords ) )
	{ TEST_POSITION = 0; }
    else
	{ TEST_POSITION = new_coords; }
    alert("old TEST_POSITION="+old_test_position
	+ ", new_position="+coord_string( new_coords )
	+ ", TEST_POSITION now = "+coord_string( TEST_POSITION )
	+ "." );
    }

//////////////////////////////////////////////////////////////////////////
//	Set all the attributes we change for all of the screens.	//
//	Note that this does not choose which screen we happen to be	//
//	showing.							//
//////////////////////////////////////////////////////////////////////////
</script><script>if(DEBUG.checkpointing) {alert("00049 function real /var/www/routing/sto/routes/common/routes.js@1357");}</script><script>
function real_update_screen( called_from )
    {
    debug_out( DEBUG.functions, "function start update_screen()");
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
	// alert("stops["+active.name+"].route_from=" + stop_string(active.route_from))
	(ebid("id_distance_to")).innerHTML =
	    ( !active.distance_to ? "" : distance_string( active.distance_to ) )
	 // +  ( !active.distance_ref ? "" : " ("+distance_string(active.distance_ref)+")" )
	 +  ( !active.distance_to ? "" : " miles from " )
	 +  stop_string(active.route_from)
	     ;
	(ebid("id_phone")).innerHTML = active.phone;
	var addr_to_display = short_address( active.addrtxt );
	(ebid("id_addrtxt")).innerHTML = addr_to_display;
	var txt =
	    ( active.note ? active.note.replace(/\n/g,"<br>")+"<br>" : "" ) +
	    ( active.notes ? active.notes.replace(/\n/g,"<br>") : "" );
	(ebid("id_patron_issue")).innerHTML =
	    ( txt ? txt : "(Create issue)" );
	(ebid("id_prefs")).innerHTML =
	    active.prefs.replace(/&lt;/g,'<').replace(/&gt;/g,'>').replace(/&sbquo;/g,"'");
	(ebid("id_status")).innerHTML
	    = (active.status?(active.status):"(Set status)");
	(ebid("id_odometer")).innerHTML
	    = (active.odometer?("Odometer at "+active.odometer):"(Set odometer)");
	(ebid("id_donation")).innerHTML
	    = (active.donation?("Donation of $"+active.donation+" "+active.donation_type):"(Create donation)");
	(ebid("id_route_type")).innerHTML
	    = (active.route_type?("Route type of "+active.route_type):"(Create route type)");

	if( current_stop==undefined )
	    { alert("Current_stop is not defined."); }
	else if( stops[current_stop]==undefined )
	    { alert("stops[current_stop="+current_stop+"] is not defined."); }
	else if( stops[current_stop].status==undefined )
	    { alert("stops[current_stop="+current_stop+"].status is not defined."); }
	(ebid("id_small_screen")).style.backgroundColor =
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
	    { alert("stop_number is not defined."); }
	else if( stops[stop_number]==undefined )
	    { alert("stops[stop_number="+stop_number+"] is not defined."); }
	else if( stops[stop_number].status==undefined )
	    { alert("stops[stop_number="+stop_number+"].status is not defined."); }
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
		( ! DEBUG.debug ? "" :
		    "<input type=button onClick='set_test_pos(\""+stops[stop_number].coords+"\");' value='" ),
	        ( stop_number==current_stop ? "&rarr;" : "" ),
		( ! DEBUG.debug ? "" :
		    "'>" ),
		"</td>", 
	    "<th valign=top align=left style='border-bottom:1px solid;qwhite-space: nowrap;'>",
		stops[stop_number].name, "</th>",
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
    debug_out( DEBUG.functions, "function end update_screen()");
    return true;
    }

</script><script>if(DEBUG.checkpointing) {alert("00050 function update /var/www/routing/sto/routes/common/routes.js@1468");}</script><script>
function update_screen( called_from )
    {
    var update_screen_return;
    try
	{ update_screen_return = real_update_screen(called_from); }
      catch(estack)
	{ alert("update_screen failed:\n" + estack.stack ); }
    return update_screen_return;
    }

//////////////////////////////////////////////////////////////////////////
//	Short hand for setting a display element on or off.		//
//////////////////////////////////////////////////////////////////////////
</script><script>if(DEBUG.checkpointing) {alert("00051 function setdisplay /var/www/routing/sto/routes/common/routes.js@1482");}</script><script>
function setdisplay( name, flag )
    {
    debug_out( DEBUG.functions, "function start setdisplay()");
    (ebid(name)).style.display = ( flag ? "" : "none" );
    }

//////////////////////////////////////////////////////////////////////////
//	At the end of user's input, if this variable is set, change	//
//	the focus.							//
//////////////////////////////////////////////////////////////////////////
var should_be_focused;
</script><script>if(DEBUG.checkpointing) {alert("00052 function check /var/www/routing/sto/routes/common/routes.js@1494");}</script><script>
function check_focus()
    {
    debug_out( DEBUG.functions, "function start check_focus()");
    // alert("check_focus()!");
    if( should_be_focused )
	{
	var p = document.getElementById(should_be_focused);
	if( p )
	    {
	    // alert("Trying again to focus on "+should_be_focused);
	    p.focus();
	    should_be_focused = 0;
	    }
	}
    }

//////////////////////////////////////////////////////////////////////////
//////////////////////////////////////////////////////////////////////////
var focus_timer;
</script><script>if(DEBUG.checkpointing) {alert("00053 function set /var/www/routing/sto/routes/common/routes.js@1514");}</script><script>
function set_focus( id_name )
    {
    debug_out( DEBUG.functions, "function start set_focus()");
    // alert("set_focus("+(p||"UNDEF")+")");
    if( id_name )
	{
	var p = document.getElementById(id_name);
	if( p )
	    {
	    // alert("Trying initial setfocus...");
	    p.focus();
	    }
	should_be_focused = id_name;
	focus_timer = setTimeout( check_focus, 800 );
	// alert("Focus verify scheduled.");
	}
    }

//////////////////////////////////////////////////////////////////////////
//	Make sure the screens are all up-to-date, light up named one	//
//	and darken all the others.					//
//////////////////////////////////////////////////////////////////////////
</script><script>if(DEBUG.checkpointing) {alert("00054 function lightup /var/www/routing/sto/routes/common/routes.js@1537");}</script><script>
function lightup( tolight, called_from )
    {
    debug_out( DEBUG.functions, "function start lightup()");
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
</script><script>if(DEBUG.checkpointing) {alert("00055 function get /var/www/routing/sto/routes/common/routes.js@1554");}</script><script>
function get_field( field, constraint, constraint_text )
    {
    debug_out( DEBUG.functions, "function start get_field()");
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
</script><script>if(DEBUG.checkpointing) {alert("00056 function set /var/www/routing/sto/routes/common/routes.js@1570");}</script><script>
function set_status( new_status, already_displaying )
    {
    debug_out( DEBUG.functions, "function start set_status()");
    if( new_status == "Untouched" )
	{
	// var err = new Error();
	// alert("Trace:  "+err.stack);
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
	// alert("Setting current_stop="+current_stop+" status to "+new_status);
	stops[current_stop].status = new_status;

	// alert("About to do test:  current_stop="+current_stop+", status="+new_status+", length="+stops.length);
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

	if( new_note )
	    { stops[current_stop].notes = new_note.replace(/_/g," "); }
	else if(new_status == "Normal"
	    ||  new_status == "Unvisited"
	    ||  new_status == "Untouched" )
	    { stops[current_stop].notes = ""; }
	else
	    {
	    // stops[current_stop].notes ||= "";
	    if( ! stops[current_stop].notes )
		{ stops[current_stop].notes = ""; }
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
</script><script>if(DEBUG.checkpointing) {alert("00057 function set /var/www/routing/sto/routes/common/routes.js@1643");}</script><script>
function set_donation_type( new_value, continue_flag )
    {
    debug_out( DEBUG.functions, "function start set_donation_type()");
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
</script><script>if(DEBUG.checkpointing) {alert("00058 function set /var/www/routing/sto/routes/common/routes.js@1660");}</script><script>
function set_route_type( new_value, continue_flag )
    {
    debug_out( DEBUG.functions, "function start set_route_type()");
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
</script><script>if(DEBUG.checkpointing) {alert("00059 function real /var/www/routing/sto/routes/common/routes.js@1677");}</script><script>
function real_set_active( ind_base, offset )
    {
    debug_out( DEBUG.functions, "function real_start set_active()");
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
	    { alert("Cannot find active + "+offset); }
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
    setdisplay("id_pickup_line",stops[current_stop].type=="Pickup");	//	// Only ask for pickup info on pickup.
    setdisplay("id_notes_line",true);					// Notes for everybody
    setdisplay("id_route_type_line",current_stop==0);
    setdisplay("id_status_line",true);

    if( stops[ current_stop ].status != "Untouched" )
        { return set_status( stops[current_stop].status ); }
    else
        {
	oneof("set_status", "<table cellpadding=5 cellspacing=5 width=100%>"
	    + "<tr><th class=bigtext>Visit the following stop?</th></tr>"
	    + "<tr><td class=bigtext>"+(stops[current_stop].name||"") + "</td></tr>"
	    + "<tr><td>"+(stops[current_stop].addrtxt||"") + "</td></tr>"
	    + "<tr><td>"+(stops[current_stop].phone||"") + "</td></tr>"
	    + "</table>", [
	    { value:"Unvisited", txt:"Visit the stop", color:STATES.Unvisited.color  },
	    { value:"Skipped_Hospital", txt:"In hospital", color:STATES.Skipped.color },
	    { value:"Skipped_Deceased", txt:"Deceased", color:STATES.Skipped.color },
	    { value:"Skipped_Suspend", txt:"Suspended", color:STATES.Skipped.color },
	    { value:"Skipped_Every_Other", txt:"Every Other", color:STATES.Skipped.color },
	    { value:"Skipped_Different_Route", txt:"Different Route", color:STATES.Skipped.color },
	    { value:"Skipped", txt:"Do not visit the stop", color:STATES.Skipped.color } ] );
	}
    }
</script><script>if(DEBUG.checkpointing) {alert("00060 function set /var/www/routing/sto/routes/common/routes.js@1744");}</script><script>
function set_active( ind_base, offset )
    {
    var set_active_return;
    try
	{ set_active_return = real_set_active(ind_base,offset); }
      catch(estack)
	{ alert("set_active failed:\n" + estack.stack ); }
    return set_active_return;
    }

//////////////////////////////////////////////////////////////////////////
//	Called when user wants to note an issue with a patron.		//
//////////////////////////////////////////////////////////////////////////
</script><script>if(DEBUG.checkpointing) {alert("00061 function set /var/www/routing/sto/routes/common/routes.js@1758");}</script><script>
function set_attribute( fld, val, ok_to_proceed )
    {
    debug_out( DEBUG.functions, "function start setattribute()");
    // alert("Setattribute("+fld+","+val+","+ok_to_proceed+")");
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
</script><script>if(DEBUG.checkpointing) {alert("00062 function date /var/www/routing/sto/routes/common/routes.js@1780");}</script><script>
function date_to_HHMM( d )
    {
    debug_out( DEBUG.functions, "function start date_to_HHMM()");
    return new Date(d).toLocaleTimeString( [],
	    { hour12:false, hour:'2-digit', minute:'2-digit' } );
    }

var DIGITS_RESERVED="'\"!,:+-%=\\;`".split('');
var digits = new Array();
var digits_offset;
//////////////////////////////////////////////////////////////////////////
//////////////////////////////////////////////////////////////////////////
</script><script>if(DEBUG.checkpointing) {alert("00063 function convert /var/www/routing/sto/routes/common/routes.js@1793");}</script><script>
function convert_base( n )
    {
    debug_out( DEBUG.functions, "function start convert_base()");
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
</script><script>if(DEBUG.checkpointing) {alert("00064 function progress /var/www/routing/sto/routes/common/routes.js@1810");}</script><script>
function progress_logged( done, timestr, arg_last_serial_received )
    {
    debug_out( DEBUG.functions, "function start progress_logged()");
    last_serial_received = arg_last_serial_received;
    var rcvmsg = timestr + " logged"
	    +" serial="+last_serial_received
	    +" \n";
    rcvmsg = "";
    if( done )
        {
	rcvmsg +=
	    	'Your route has been recorded.\n'
	    +	'Close page to turn off Geolocation.\n'
	    +	'Thank you!\n';
	}
    if( rcvmsg ) { alert( rcvmsg ); }
    }

//////////////////////////////////////////////////////////////////////////
//	Compute progress from route history.				//
//////////////////////////////////////////////////////////////////////////
</script><script>if(DEBUG.checkpointing) {alert("00065 function compute /var/www/routing/sto/routes/common/routes.js@1832");}</script><script>
function compute_progress()
    {
    debug_out( DEBUG.functions, "function start compute_progress()");
    var offsets = { when:0, latitude:0, longitude:0 };
    var last_mode = 0;

    var progress = new Array( digits.join('') );

    for( var i=0; i<route_history.length; i++ )
	{
	var diff;
	for( var ind in offsets )	// Order of keys preserved, I promise!
	    {
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
</script><script>if(DEBUG.checkpointing) {alert("00066 function min /var/www/routing/sto/routes/common/routes.js@1880");}</script><script>
function min3(a, b, c)
    {
    // debug_out( DEBUG.functions, "function start min3()");
    if (a <= b && a <= c) return a;
    if (b <= a && b <= c) return b;
    return c;
    }

//////////////////////////////////////////////////////////////////////////
//	Return the index of the minimum value in an array.		//
//////////////////////////////////////////////////////////////////////////
</script><script>if(DEBUG.checkpointing) {alert("00067 function minind /var/www/routing/sto/routes/common/routes.js@1892");}</script><script>
function minind( ar )
    {
    // debug_out( DEBUG.functions, "function start minind()");
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
</script><script>if(DEBUG.checkpointing) {alert("00068 function minv /var/www/routing/sto/routes/common/routes.js@1908");}</script><script>
function minv( ar )
    {
    // debug_out( DEBUG.functions, "function start minv()");
    return ar[ minind( ar ) ];
    }

//////////////////////////////////////////////////////////////////////////
//	Return a string representing instructions to convert the first	//
//	string into the second.  Reduces data to send upstring which	//
//	already has previous instance (and minimal stuff has changed)	//
//////////////////////////////////////////////////////////////////////////
</script><script>if(DEBUG.checkpointing) {alert("00069 function Make_Edit_String /var/www/routing/sto/routes/common/routes.js@1920");}</script><script>
function Make_Edit_String(str1, str2)
    {
    debug_out( DEBUG.functions, "function start Make_Edit_String()");
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
    // alert("Debug length="+msg.length+"\n"+msg.join("\n"));
    return res.join('`');
    }

//////////////////////////////////////////////////////////////////////////
//	Post form containing update information.			//
//////////////////////////////////////////////////////////////////////////
</script><script>if(DEBUG.checkpointing) {alert("00070 function generate /var/www/routing/sto/routes/common/routes.js@2020");}</script><script>
function generate_update( doneflag )
    {
    debug_out( DEBUG.functions, "function start generate_update()");
    if( doneflag )
	{
	var problems = new Array();
	if( stops[0].odometer == undefined )
	    { problems.push( "Odometer for route start not set." ); }
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
			    "Log "
			+   travelled_pretty + " miles from "
			+   stops[0].odometer + " to "
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

    var route_status = JSON.stringify(
	{
	STAFF:			"S_6",
	DISTRIBUTOR:		"D_2iG",
	USER:			"anonymous",
	ROUTE_NAME:		"DC Hot spots",
	stops:			stops,
	display_order:		display_order,
	done:			doneflag||0,
	progress:		compute_progress()
	} );
    if( route_status != last_route_status ) { current_serial++; }

    // alert("CMC pre make_edit_string logic, last_serial="+last_serial_received+", current_serial="+current_serial);
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
    // alert("CMC post make_edit_string logic...");
    last_route_status = route_status;

    window.document.form.route_status_edit.value = edit_string;
    window.document.form.route_status_serial.value = current_serial;
    if( window.document.form["route_status_debug"] )
        {	//If debugging, send entire thing upstream anyways
	window.document.form.route_status_debug.value = route_status;
	}

    window.document.form.submit();
    // alert("Applied ["+window.document.form.route_status_edit.value+"] to ["+current_serial+"]");
//    alert("Generate_update("
//	+"done="+doneflag
//	+", serial="+current_serial
//	+", sending="+window.document.form.progress.value.length
//	+")");
    // alert("generate_update("+doneflag+") complete.");
    }

//////////////////////////////////////////////////////////////////////////
//      Get pointer to an ID but give a reasonable message if it does   //
//      not exist.  "should never happen".  Uh huh.                     //
//////////////////////////////////////////////////////////////////////////
</script><script>if(DEBUG.checkpointing) {alert("00071 function ebid /var/www/routing/sto/routes/common/routes.js@2123");}</script><script>
function ebid( id )
    {
    // debug_out( DEBUG.functions, "function start ebid()");
    return document.getElementById(id) ||
        fatal("Cannot find element for id ["+id+"]");
    }

//////////////////////////////////////////////////////////////////////////
//	Pack into string from convenient hash pickup_list.		//
//////////////////////////////////////////////////////////////////////////
</script><script>if(DEBUG.checkpointing) {alert("00072 function pickup /var/www/routing/sto/routes/common/routes.js@2134");}</script><script>
function pickup_list_to_text()
    {
    debug_out( DEBUG.functions, "function start pickup_list_to_text()");
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
</script><script>if(DEBUG.checkpointing) {alert("00073 function text /var/www/routing/sto/routes/common/routes.js@2165");}</script><script>
function text_to_pickup_list()
    {
    debug_out( DEBUG.functions, "function start text_to_pickup_list()");
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
</script><script>if(DEBUG.checkpointing) {alert("00074 function modify /var/www/routing/sto/routes/common/routes.js@2201");}</script><script>
function modify_pickup( pickup_ind, bag_type, field )
    {
    debug_out( DEBUG.functions, "function start modify_pickup()");
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
</script><script>if(DEBUG.checkpointing) {alert("00075 function draw /var/www/routing/sto/routes/common/routes.js@2219");}</script><script>
function draw_pickups()
    {
    debug_out( DEBUG.functions, "function start draw_pickups()");
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
    // alert( s );
    (ebid("pickup_table_id")).innerHTML = s.join("\n");
    }

//////////////////////////////////////////////////////////////////////////
//	Various options to help debug this monster.			//
//////////////////////////////////////////////////////////////////////////
</script><script>if(DEBUG.checkpointing) {alert("00076 function debug /var/www/routing/sto/routes/common/routes.js@2272");}</script><script>
function debug_page()
    {
    debug_out( DEBUG.functions, "function start debug_page()");
    var s = new Array( '<table border=1 style="border-collapse:collapse">' );
    for ( const flag in DEBUG )
	{
	s.push('<tr><th align=left>'+flag+'</th>');
	s.push('<td onClick=\'DEBUG.'+flag+'=prompt("Enter '+flag+':",DEBUG.'+flag+');debug_page();\'>');
	s.push(DEBUG[flag]+'</td></tr>');
	}
    s.push( '</table>' );
    (ebid("id_debug_data")).innerHTML = s.join("\n");
    lightup('debug');
    }

//////////////////////////////////////////////////////////////////////////
//	Setup_page							//
//	Called when .cgi file loaded to do any javascript setup.	//
//	Obviously will not get called when javascript is not running	//
//	(which is to say, when result is being printed).		//
//////////////////////////////////////////////////////////////////////////
</script><script>if(DEBUG.checkpointing) {alert("00077 function setup /var/www/routing/sto/routes/common/routes.js@2294");}</script><script>
function setup_page()
    {
    debug_out( DEBUG.functions, "function start setup_page()");
    browser_dependent();
    var caller_pieces = window.location.href.split('?');
    if( caller_pieces.length > 1 )
	{
	caller_pieces = caller_pieces[1].split('&');
	for( const piece of caller_pieces )
	    {
	    if( /(.*)=(.*)/.test(piece) )
	        { DEBUG[ RegExp.$1 ] = RegExp.$2; }
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

    if( DEBUG.debug )
	{	// Extra buttons for test routes!
	alert("CMC enabling debug display.");
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

</script>

<title>DC Hot spots route</title>
<meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">


<input type="hidden" name="SID" value="RT_1tuJwz">
<input type="hidden" name="status_file" value="Test_Distributor/Chris_Caldwell/2025-03-17-DC_Hot_spots">
<input type="hidden" name="route_status_debug">
<input type="hidden" name="route_status_edit">
<input type="hidden" name="route_status_serial">
<input type="hidden" name="progress">                 
<center><table id="id_small_screen" qborder="5" style="display:none" class="fixedtable">
<tbody><tr><td width="100%" height="100%"><table class="fixedleft">
    <tbody><tr>
	<th align="left" valign="top" colspan="2">
	<div align="left" id="id_ind" class="bigtext">id_ind</div>
	<div align="left" id="id_name" class="bigtext">id_name</div>
	<div align="left" id="id_time_to" qclass="bigtext">id_time_to</div>
	<div align="left" id="id_distance_to" qclass="bigtext">id_distance_to</div>
	</th></tr>
    <tr><th align="left" valign="center" width="1px">
	<button onclick="make_call(current_stop);"><img src="sample_route_sheet_files/phone.jpg" style="height:50px;"></button><br>
	<button onclick="make_text(current_stop);"><img src="sample_route_sheet_files/texting.jpg" style="height:50px;"></button>
	</th>
	<td id="id_phone" valign="center" style="font-size:175%">Phone number</td></tr>
    <tr><th align="left" valign="center" onclick="goto_map(current_stop);" width="1px">
	<button type="button"><img src="sample_route_sheet_files/map.jpg" style="height:50px;"></button></th>
	<td id="id_addrtxt" valign="center" onclick="goto_map(current_stop);" style="font-size:175%">Map location</td></tr>
	<tr><th colspan="2" align="left" id="id_prefs"></th></tr>
	<tr id="id_route_type_line" style="display:none">
	    <th colspan="2" align="left" id="id_route_type" onclick='lightup("route_type");'>
	    (Set route type)</th></tr>
	<tr id="id_notes_line" style="display:none">
	    <th colspan="2" align="left" id="id_patron_issue" onclick='lightup("patron_issue");'>
	    (Set notes)</th></tr>
	<tr id="id_odometer_line" style="display:none">
	    <th colspan="2" align="left" id="id_odometer" onclick='lightup("odometer");'>
	    (Set odometer)</th></tr>
	<tr id="id_donation_line" style="display:none">
	    <th colspan="2" align="left" id="id_donation" onclick='lightup("donation");'>
	    (Set donation)</th></tr>
	<tr id="id_pickup_line" style="display:none">
	    <th colspan="2" align="left" id="id_pickup" onclick='lightup("pickup");'>
	    (Set pickups)</th></tr>
	<tr id="id_status_line" style="display:none">
	    <th colspan="2" align="left" id="id_status" onclick='lightup("status");'>
	    (Set status)</th></tr>
    </tbody></table></td>
    <td width="100%" height="100%"><table class="fixedright">
        <tbody><tr><td align="right" valign="top" onclick="set_active(current_stop,-1);">
	    <button type="button" class="bigbutt">↑</button></td></tr>
        <tr><td align="right" valign="center" onclick="set_active(-1,0);">
	    <button type="button" class="bigbutt">←</button></td></tr>
        <tr><td align="right" valign="bottom" onclick="set_active(current_stop,1);">
	    <button type="button" class="bigbutt">↓</button></td></tr>
    </tbody></table></td></tr></tbody></table>

<div id="id_patron_issue_screen" style="display:none">
    Notes:<br>
    <textarea name="patron_issue" id="id_patron_issue_value" rows="14" cols="60" autofocus="" onchange='set_attribute("notes",this.value,1);'></textarea>
    <button type="button" onclick='lightup("small");'>←</button>
    </div>
<table id="id_route_type_screen" style="display:none">
    <tbody><tr>	<th>Set route type</th></tr>
    <tr><td>
	<input type="hidden" id="id_route_type_value" name="current_route_type">
	
    </td></tr>
</tbody></table>
<table id="id_status_screen" style="display:none">
    <tbody><tr>	<th>Set status</th></tr>
    <tr><td>
	<input type="hidden" id="current_status" name="current_status">
	<button class="medbut" id="Untouched" onclick='set_status("Untouched",false);'>Untouched</button><br>
	<button class="medbut" id="Unvisited" onclick='set_status("Unvisited",false);'>Unvisited</button><br>
	<button class="medbut" id="Normal" onclick='set_status("Normal",false);'>Normal</button><br>
	<button class="medbut" id="Normal_dropoff" onclick='set_status("Normal_dropoff",false);'>Normal dropoff</button><br>
	<button class="medbut" id="Skipped" onclick='set_status("Skipped",false);'>Skipped</button><br>
	<button class="medbut" id="Skipped_Hospital" onclick='set_status("Skipped_Hospital",false);'>Skipped Hospital</button><br>
	<button class="medbut" id="Skipped_Suspended" onclick='set_status("Skipped_Suspended",false);'>Skipped Suspended</button><br>
	<button class="medbut" id="Skipped_Different_Route" onclick='set_status("Skipped_Different_Route",false);'>Skipped Different Route</button><br>
	<button class="medbut" id="Skipped_Every_Other" onclick='set_status("Skipped_Every_Other",false);'>Skipped Every Other</button><br>
	<button class="medbut" id="Problems" onclick='set_status("Problems",false);'>Problems</button><br>
	<button class="medbut" id="Problems_Does_not_answer_phone_or_knock" onclick='set_status("Problems_Does_not_answer_phone_or_knock",false);'>Problems Does not answer phone or knock</button><br>
	<button class="medbut" id="Issues" onclick='set_status("Issues",false);'>Issues</button><br>
    </td></tr>
</tbody></table>
<table id="id_odometer_screen" style="display:none">
    <tbody><tr>	<th>Enter odometer:</th></tr>
    <tr>	<td><input type="number" min="10.0" max="1000000.0" inputmode="decimal" autofocus="" id="id_odometer_value" name="odometer" size="8" onchange='set_attribute("odometer",this.value,1)&amp;&amp;false;'></td></tr>
    <tr>	<td><button type="button" onclick='lightup("small");'>
		    ←</button></td></tr></tbody></table>
<table id="id_donation_screen" style="display:none">
    <tbody><tr>	<th align="left">Donation:</th>
    		<td>$<input type="number" min="0.01" max="1000000.00" inputmode="decimal" autofocus="" id="id_donation_value" name="donation" size="8" onchange='set_attribute("donation",this.value,0);'></td></tr>
    <tr>	<th align="left">Type:</th>
		<th>
		    <input type="hidden" name="donation_type" id="id_donation_type_value">
		    <button id="id_Cash_button" onclick='set_donation_type("Cash",1);'>Cash</button>
		    <button id="id_Check_button" onclick='set_donation_type("Check",1);'>Check</button>
		</th></tr></tbody></table>
<div id="id_debug_screen" style="display:none">
    <button type="button" onclick='lightup("big");'>Dismiss</button>
    <button type="button" onclick="generate_update(0);">Snapshot</button>
    <button type="button" onclick="move_some();">Drive!</button>
    <div id="id_debug_data"></div>
</div>
<table id="id_pickup_screen" style="display:none">
    <tbody><tr>	<th>Enter pickup:</th></tr>
    <tr>	<td id="pickup_table_id"></td></tr>
    <tr>	<td><button type="button" onclick='lightup("small");'>
		    ←</button></td></tr></tbody></table>
<table id="id_big_screen" frame="box" cellspacing="0" cellpadding="2">
<tbody><tr><th>
    <table width="100%" border="0">
        <tbody><tr class="no-print" id="go_live_id"><th colspan="5">
	    <a href="https://routing.brightsands.com/sto/routes/Test_Distributor/DC_Hot_spots.1tuJwz.cgi">Take <em>DC Hot spots</em> route live</a></th></tr>
        <tr class="only-print" id="go_live_id">
	    <th rowspan="5"><img src="data:image/jpeg;base64,/9j/4AAQSkZJRgABAQAAAQABAAD/2wBDAAgGBgcGBQgHBwcJCQgKDBQNDAsLDBkSEw8UHRofHh0a
HBwgJC4nICIsIxwcKDcpLDAxNDQ0Hyc5PTgyPC4zNDL/2wBDAQkJCQwLDBgNDRgyIRwhMjIyMjIy
MjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjL/wAARCABeAF4DASIA
AhEBAxEB/8QAHwAAAQUBAQEBAQEAAAAAAAAAAAECAwQFBgcICQoL/8QAtRAAAgEDAwIEAwUFBAQA
AAF9AQIDAAQRBRIhMUEGE1FhByJxFDKBkaEII0KxwRVS0fAkM2JyggkKFhcYGRolJicoKSo0NTY3
ODk6Q0RFRkdISUpTVFVWV1hZWmNkZWZnaGlqc3R1dnd4eXqDhIWGh4iJipKTlJWWl5iZmqKjpKWm
p6ipqrKztLW2t7i5usLDxMXGx8jJytLT1NXW19jZ2uHi4+Tl5ufo6erx8vP09fb3+Pn6/8QAHwEA
AwEBAQEBAQEBAQAAAAAAAAECAwQFBgcICQoL/8QAtREAAgECBAQDBAcFBAQAAQJ3AAECAxEEBSEx
BhJBUQdhcRMiMoEIFEKRobHBCSMzUvAVYnLRChYkNOEl8RcYGRomJygpKjU2Nzg5OkNERUZHSElK
U1RVVldYWVpjZGVmZ2hpanN0dXZ3eHl6goOEhYaHiImKkpOUlZaXmJmaoqOkpaanqKmqsrO0tba3
uLm6wsPExcbHyMnK0tPU1dbX2Nna4uPk5ebn6Onq8vP09fb3+Pn6/9oADAMBAAIRAxEAPwD3+iiv
H/EHiDxF/wAJf4x/4rj/AIR7RNC+xf8AMJju/wDXxj23ff8Ar97sBQB7BRXz/qHjDxF/wiGsa/oH
xU/tf+yvI86D/hHo7f8A1sgRfmdf948A9O2a9A1D4jeHfC3i/WLLX/Fn/PDydP8A7Ok/0P8Adgt+
8RT5m/crc/d6UAegUV84Wnxo8ZeK9Y1HSfDthsvtS8r+y4vOhP2Py13S8ugEm8Kx+Yjb2ou/jFqM
3w4065tvGv2fxTB5v2uz/stX+1bpsJ85TYm2Pnjr0PNAH0fRXh938aNR8KaPp0lzYf8ACSWN55v2
TXPOWz+2bG+f9wEJj2FtnP3tu4da6D4hfFjUfh/rCW1z4U+0WM+fsl5/aKp5+1UL/IEYrtL4569R
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
jzz06CtCiigD/9k=
"></th><td valign="middle" rowspan="5">Take <em>DC Hot spots</em> route live
	    </td><td></td><th align="left">Driver name:</th><td></td></tr>
	    <tr class="only-print"><td></td><th align="left">Van number:</th><td></td></tr>
	    <tr class="only-print"><td></td><th align="left">Site:</th><td>Test Distributor</td></tr>
	    <tr class="only-print"><td></td><th align="left">Agency name:</th><td></td></tr>
	    <tr class="only-print"><td></td><th align="left">Provider:</th><td>Spectrum Generations CMAAA</td></tr>
        <tr id="map_opts_id" style="display:none"><th align="left" colspan="5">
	    <button type="button" onclick="goto_map(-1);">DC Hot spots route map</button>
        </th></tr>
	</tbody></table>
    </th></tr>
<tr><td id="id_big_screen_inset"><table border="0" cellspacing="0" cellpadding="2" width="100%"><tbody><tr><th align="center" width="16%" style="color:black;background-color:#c0ffc0 !important;border:1px solid #c0ffc0;">Provisioning</th><th align="center" width="16%" style="color:black;background-color:#d0ffff !important;border:1px solid #d0ffff;">New patron</th><th align="center" width="16%" style="color:black;background-color:#c0c0ff !important;border:1px solid #c0c0ff;">USDA box</th><th align="center" width="16%" style="color:black;background-color:#ffb0b0 !important;border:1px solid #ffb0b0;">No frozen bag</th><th align="center" width="16%" style="color:black;background-color:#ffb0b0 !important;border:1px solid #ffb0b0;">Special meal</th><th align="center" width="16%" style="color:black;background-color:#30ffff !important;border:1px solid #30ffff;">Dogs</th></tr>
<tr><td align="center" style="color:black;background-color:#c0ffc0 !important;border:1px solid #c0ffc0;">10</td><td align="center" style="color:black;background-color:#d0ffff !important;border:1px solid #d0ffff;">10</td><td align="center" style="color:black;background-color:#c0c0ff !important;border:1px solid #c0c0ff;">1</td><td align="center" style="color:black;background-color:#ffb0b0 !important;border:1px solid #ffb0b0;">1</td><td align="center" style="color:black;background-color:#ffb0b0 !important;border:1px solid #ffb0b0;">1</td><td align="center" style="color:black;background-color:#30ffff !important;border:1px solid #30ffff;">2</td></tr>
</tbody></table><table frame="box" cellspacing="0" cellpadding="2"><tbody><tr>
	<th valign="top" align="left" bgcolor="white" style="border-top:1px solid;" rowspan="2"><span class="only-print"><img src="data:image/jpeg;base64,/9j/4AAQSkZJRgABAQAAAQABAAD/2wBDAAgGBgcGBQgHBwcJCQgKDBQNDAsLDBkSEw8UHRofHh0a
HBwgJC4nICIsIxwcKDcpLDAxNDQ0Hyc5PTgyPC4zNDL/2wBDAQkJCQwLDBgNDRgyIRwhMjIyMjIy
MjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjL/wAARCACeAJ4DASIA
AhEBAxEB/8QAHwAAAQUBAQEBAQEAAAAAAAAAAAECAwQFBgcICQoL/8QAtRAAAgEDAwIEAwUFBAQA
AAF9AQIDAAQRBRIhMUEGE1FhByJxFDKBkaEII0KxwRVS0fAkM2JyggkKFhcYGRolJicoKSo0NTY3
ODk6Q0RFRkdISUpTVFVWV1hZWmNkZWZnaGlqc3R1dnd4eXqDhIWGh4iJipKTlJWWl5iZmqKjpKWm
p6ipqrKztLW2t7i5usLDxMXGx8jJytLT1NXW19jZ2uHi4+Tl5ufo6erx8vP09fb3+Pn6/8QAHwEA
AwEBAQEBAQEBAQAAAAAAAAECAwQFBgcICQoL/8QAtREAAgECBAQDBAcFBAQAAQJ3AAECAxEEBSEx
BhJBUQdhcRMiMoEIFEKRobHBCSMzUvAVYnLRChYkNOEl8RcYGRomJygpKjU2Nzg5OkNERUZHSElK
U1RVVldYWVpjZGVmZ2hpanN0dXZ3eHl6goOEhYaHiImKkpOUlZaXmJmaoqOkpaanqKmqsrO0tba3
uLm6wsPExcbHyMnK0tPU1dbX2Nna4uPk5ebn6Onq8vP09fb3+Pn6/9oADAMBAAIRAxEAPwD3+iiv
H/EHiDxF/wAJf4x/4rj/AIR7RNC+xf8AMJju/wDXxj23ff8Ar97sBQB7BRXz/qHjDxF/wiGsa/oH
xU/tf+yvI86D/hHo7f8A1sgRfmdf948A9O2a9Q8V/ELTvDmj+ILm2T7ffaH9n+12eWi2+cyhPnKk
Hg54z0wcUAdhRXl/xC1XUfDmsJc3PxM/sCxvc/ZLP+wVutuxUD/OASeTnnH3sDpWfqHif4h6j/bF
loFn/wATv9x52n+bb/8AEj6Ff3jjbc+cgZuP9X060AewUV8//wDCxvEXjH974U8WfY9buv8Aj28L
/wBnRybdvDf6VIoU5RWl59dvWjwT8RvEXj37DoH/AAln9h63H5n7/wDs6O5/tLO5/u7VWHy0THX5
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
"></span></th><th valign="top" align="left" bgcolor="white" style="border-top:1px solid;Qwhite-space: nowrap;">Test Distributor</th><th valign="top" align="left" bgcolor="white" style="border-top:1px solid;Qwhite-space: nowrap;"><a href="callto:(202)000-0000">(202)000-0000</a></th>
	<td valign="top" bgcolor="white" style="border-top:1px solid" onclick="goto_map(0);"><a target="map" href="https://www.google.com/maps/dir/?api=1&amp;waypoints=38.89879,-77.03364|38.8898,-77.00589|38.88763,-77.00474|38.887853,-77.040587|38.88898,-77.032958|38.89871,-77.03364|38.89659,-77.02598|38.892206,-77.018777|38.89482,-77.01756|38.711032,-77.088291|38.883913,-77.064892&amp;destination=38.89879,-77.03364%3Ca">1600 Pennsylvania Avenue NW<br> Washington, DC 20500</a></td></tr><tr><td bgcolor="white" colspan="4" align="right" valign="bottom"><table bgcolor="white" class="only-print"><tbody><tr><th bgcolor="white">▢</th><td bgcolor="white">Failed to deliver</td></tr><tr><th bgcolor="white">▢</th><td bgcolor="white">Needs to be called</td></tr></tbody></table></td></tr>
<tr>
	<th valign="top" align="left" bgcolor="white" style="border-top:1px solid;" rowspan="2"><span class="only-print"><img src="data:image/jpeg;base64,/9j/4AAQSkZJRgABAQAAAQABAAD/2wBDAAgGBgcGBQgHBwcJCQgKDBQNDAsLDBkSEw8UHRofHh0a
HBwgJC4nICIsIxwcKDcpLDAxNDQ0Hyc5PTgyPC4zNDL/2wBDAQkJCQwLDBgNDRgyIRwhMjIyMjIy
MjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjL/wAARCACWAJYDASIA
AhEBAxEB/8QAHwAAAQUBAQEBAQEAAAAAAAAAAAECAwQFBgcICQoL/8QAtRAAAgEDAwIEAwUFBAQA
AAF9AQIDAAQRBRIhMUEGE1FhByJxFDKBkaEII0KxwRVS0fAkM2JyggkKFhcYGRolJicoKSo0NTY3
ODk6Q0RFRkdISUpTVFVWV1hZWmNkZWZnaGlqc3R1dnd4eXqDhIWGh4iJipKTlJWWl5iZmqKjpKWm
p6ipqrKztLW2t7i5usLDxMXGx8jJytLT1NXW19jZ2uHi4+Tl5ufo6erx8vP09fb3+Pn6/8QAHwEA
AwEBAQEBAQEBAQAAAAAAAAECAwQFBgcICQoL/8QAtREAAgECBAQDBAcFBAQAAQJ3AAECAxEEBSEx
BhJBUQdhcRMiMoEIFEKRobHBCSMzUvAVYnLRChYkNOEl8RcYGRomJygpKjU2Nzg5OkNERUZHSElK
U1RVVldYWVpjZGVmZ2hpanN0dXZ3eHl6goOEhYaHiImKkpOUlZaXmJmaoqOkpaanqKmqsrO0tba3
uLm6wsPExcbHyMnK0tPU1dbX2Nna4uPk5ebn6Onq8vP09fb3+Pn6/9oADAMBAAIRAxEAPwD3+iiv
H/EHiDxF/wAJf4x/4rj/AIR7RNC+xf8AMJju/wDXxj23ff8Ar97sBQB7BRXz/qHjDxF/wiGsa/oH
xU/tf+yvI86D/hHo7f8A1sgRfmdf948A9O2a7D4hfELUYdYTwX4LT7R4pnzubKp9l2qko4lXY+6P
f/Fx9cCgD1CiuP0TW9Rh1iDwxJcf2/fWW7+2tS2La/Zd6mSD91jD7h8vyE425PWuP1f4u/8ACHeE
PDl75v8Awln9p/af+Jht+wbvLkA/1ew4xu29vuZ5zQB7BRWfaXeozaxqNtc6X9nsYPK+yXn2hX+1
bly/yDlNp4569RXj/g3xX4yvtY1vwX4n8Sf2X4pfyP7Ob7DDP5eFaWXiMbDmML95uM8cjFAHuFFc
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
igD/2Q==
"></span></th><th valign="top" align="left" bgcolor="white" style="border-top:1px solid;Qwhite-space: nowrap;">John Capital</th><th valign="top" align="left" bgcolor="white" style="border-top:1px solid;Qwhite-space: nowrap;"><a href="callto:(202)000-0001">(202)000-0001</a><br><span style="color:black;background-color:#d0ffff !important;border:1px solid #d0ffff;">New patron</span></th>
	<td valign="top" bgcolor="white" style="border-top:1px solid" onclick="goto_map(1);"><a target="map" href="https://www.google.com/maps/dir/?api=1&amp;waypoints=38.8898,-77.00589|38.88763,-77.00474|38.887853,-77.040587|38.88898,-77.032958|38.89871,-77.03364|38.89659,-77.02598|38.892206,-77.018777|38.89482,-77.01756|38.711032,-77.088291|38.883913,-77.064892&amp;destination=38.89879,-77.03364%3Ca">E Capitol St. and 1st St. NE Washington<br> DC 20004</a></td></tr><tr><td bgcolor="white" colspan="4" align="right" valign="bottom"><table bgcolor="white" class="only-print"><tbody><tr><th bgcolor="white">▢</th><td bgcolor="white">Failed to deliver</td></tr><tr><th bgcolor="white">▢</th><td bgcolor="white">Needs to be called</td></tr></tbody></table></td></tr>
<tr>
	<th valign="top" align="left" bgcolor="white" style="border-top:1px solid;" rowspan="2"><span class="only-print"><img src="data:image/jpeg;base64,/9j/4AAQSkZJRgABAQAAAQABAAD/2wBDAAgGBgcGBQgHBwcJCQgKDBQNDAsLDBkSEw8UHRofHh0a
HBwgJC4nICIsIxwcKDcpLDAxNDQ0Hyc5PTgyPC4zNDL/2wBDAQkJCQwLDBgNDRgyIRwhMjIyMjIy
MjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjL/wAARCACWAJYDASIA
AhEBAxEB/8QAHwAAAQUBAQEBAQEAAAAAAAAAAAECAwQFBgcICQoL/8QAtRAAAgEDAwIEAwUFBAQA
AAF9AQIDAAQRBRIhMUEGE1FhByJxFDKBkaEII0KxwRVS0fAkM2JyggkKFhcYGRolJicoKSo0NTY3
ODk6Q0RFRkdISUpTVFVWV1hZWmNkZWZnaGlqc3R1dnd4eXqDhIWGh4iJipKTlJWWl5iZmqKjpKWm
p6ipqrKztLW2t7i5usLDxMXGx8jJytLT1NXW19jZ2uHi4+Tl5ufo6erx8vP09fb3+Pn6/8QAHwEA
AwEBAQEBAQEBAQAAAAAAAAECAwQFBgcICQoL/8QAtREAAgECBAQDBAcFBAQAAQJ3AAECAxEEBSEx
BhJBUQdhcRMiMoEIFEKRobHBCSMzUvAVYnLRChYkNOEl8RcYGRomJygpKjU2Nzg5OkNERUZHSElK
U1RVVldYWVpjZGVmZ2hpanN0dXZ3eHl6goOEhYaHiImKkpOUlZaXmJmaoqOkpaanqKmqsrO0tba3
uLm6wsPExcbHyMnK0tPU1dbX2Nna4uPk5ebn6Onq8vP09fb3+Pn6/9oADAMBAAIRAxEAPwD3+iiv
H/EHiDxF/wAJf4x/4rj/AIR7RNC+xf8AMJju/wDXxj23ff8Ar97sBQB7BRXz/qHjDxF/wiGsa/oH
xU/tf+yvI86D/hHo7f8A1sgRfmdf948A9O2a7D4heK9Rh1hLbRPEn9jWOk5/4SC8+wrcfZfNVDbf
Iwy+45H7vOM5bGKAPUKK8f8AG3xN8RaF4vvv7N0jz9E8N+X/AGr/AKTGv2j7RGvk/eQsm1yfu5z3
wKz7T4xadNo+o6Jc+Nfs99B5X2TxH/ZbP9q3Nvf/AEYJhNo/d8nn7woA9worw+7+KWo+N/iPp3hj
wXrP9l2L+bu1L7Ks/wBoxD5g/dSoCu0q69ec57Ci01XxlN8R9R8F3PxM+z30HlfZG/sGF/tW6HzX
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
KKACiiigAooooAKKKKACiiigAooooA//2Q==
"></span></th><th valign="top" align="left" bgcolor="white" style="border-top:1px solid;Qwhite-space: nowrap;">Marion Librarian</th><th valign="top" align="left" bgcolor="white" style="border-top:1px solid;Qwhite-space: nowrap;"><a href="callto:(202)000-0006">(202)000-0006</a><br><span style="color:black;background-color:#d0ffff !important;border:1px solid #d0ffff;">New patron</span></th>
	<td valign="top" bgcolor="white" style="border-top:1px solid" onclick="goto_map(2);"><a target="map" href="https://www.google.com/maps/dir/?api=1&amp;waypoints=38.88763,-77.00474|38.887853,-77.040587|38.88898,-77.032958|38.89871,-77.03364|38.89659,-77.02598|38.892206,-77.018777|38.89482,-77.01756|38.711032,-77.088291|38.883913,-77.064892&amp;destination=38.89879,-77.03364%3Ca">101 Independence Ave SE<br> Washington, DC 20540</a></td></tr><tr><td bgcolor="white" colspan="4" align="right" valign="bottom"><table bgcolor="white" class="only-print"><tbody><tr><th bgcolor="white">▢</th><td bgcolor="white">Failed to deliver</td></tr><tr><th bgcolor="white">▢</th><td bgcolor="white">Needs to be called</td></tr></tbody></table></td></tr>
<tr>
	<th valign="top" align="left" bgcolor="white" style="border-top:1px solid;" rowspan="2"><span class="only-print"><img src="data:image/jpeg;base64,/9j/4AAQSkZJRgABAQAAAQABAAD/2wBDAAgGBgcGBQgHBwcJCQgKDBQNDAsLDBkSEw8UHRofHh0a
HBwgJC4nICIsIxwcKDcpLDAxNDQ0Hyc5PTgyPC4zNDL/2wBDAQkJCQwLDBgNDRgyIRwhMjIyMjIy
MjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjL/wAARCACOAI4DASIA
AhEBAxEB/8QAHwAAAQUBAQEBAQEAAAAAAAAAAAECAwQFBgcICQoL/8QAtRAAAgEDAwIEAwUFBAQA
AAF9AQIDAAQRBRIhMUEGE1FhByJxFDKBkaEII0KxwRVS0fAkM2JyggkKFhcYGRolJicoKSo0NTY3
ODk6Q0RFRkdISUpTVFVWV1hZWmNkZWZnaGlqc3R1dnd4eXqDhIWGh4iJipKTlJWWl5iZmqKjpKWm
p6ipqrKztLW2t7i5usLDxMXGx8jJytLT1NXW19jZ2uHi4+Tl5ufo6erx8vP09fb3+Pn6/8QAHwEA
AwEBAQEBAQEBAQAAAAAAAAECAwQFBgcICQoL/8QAtREAAgECBAQDBAcFBAQAAQJ3AAECAxEEBSEx
BhJBUQdhcRMiMoEIFEKRobHBCSMzUvAVYnLRChYkNOEl8RcYGRomJygpKjU2Nzg5OkNERUZHSElK
U1RVVldYWVpjZGVmZ2hpanN0dXZ3eHl6goOEhYaHiImKkpOUlZaXmJmaoqOkpaanqKmqsrO0tba3
uLm6wsPExcbHyMnK0tPU1dbX2Nna4uPk5ebn6Onq8vP09fb3+Pn6/9oADAMBAAIRAxEAPwD3+iiv
H/EHiDxF/wAJf4x/4rj/AIR7RNC+xf8AMJju/wDXxj23ff8Ar97sBQB7BRXz/qHjDxF/wiGsa/oH
xU/tf+yvI86D/hHo7f8A1sgRfmdf948A9O2a9A8T+Nv7L8X2vlah5WiaNv8A+Ek/c7vJ86MfZf4S
zZc/8s84/iwKAPQKK4+08V6d8QNH1G28F+JPs99B5W68+ws/kbmyPklChtwRx7dfSuP8Mf8AC5bj
7Vpuv/6H9q2eTq/+hyfYduWb9yn+s3/KnJ+XOaAPYKK8/wBI0j4h/wDFR6bqXij/AJ9v7K1f7Bb+
7TfuVP0T5j7ivMIvil4y8OaP4V8T6trP9s2Orfa/M037LDb7fKbyx+9VCTyQ3AHTHOaAPo+ivH9X
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
"></span></th><th valign="top" align="left" bgcolor="white" style="border-top:1px solid;Qwhite-space: nowrap;">Dwight Eisenhour</th><th valign="top" align="left" bgcolor="white" style="border-top:1px solid;Qwhite-space: nowrap;"><a href="callto:(202)000-0010">(202)000-0010</a><br><span style="color:black;background-color:#d0ffff !important;border:1px solid #d0ffff;">New patron</span></th>
	<td valign="top" bgcolor="white" style="border-top:1px solid" onclick="goto_map(3);"><a target="map" href="https://www.google.com/maps/dir/?api=1&amp;waypoints=38.887853,-77.040587|38.88898,-77.032958|38.89871,-77.03364|38.89659,-77.02598|38.892206,-77.018777|38.89482,-77.01756|38.711032,-77.088291|38.883913,-77.064892&amp;destination=38.89879,-77.03364%3Ca">1750 Independence Ave SW<br> Washington, DC 20024</a></td></tr><tr><td bgcolor="white" colspan="4" align="right" valign="bottom"><table bgcolor="white" class="only-print"><tbody><tr><th bgcolor="white">▢</th><td bgcolor="white">Failed to deliver</td></tr><tr><th bgcolor="white">▢</th><td bgcolor="white">Needs to be called</td></tr></tbody></table></td></tr>
<tr>
	<th valign="top" align="left" bgcolor="white" style="border-top:1px solid;" rowspan="2"><span class="only-print"><img src="data:image/jpeg;base64,/9j/4AAQSkZJRgABAQAAAQABAAD/2wBDAAgGBgcGBQgHBwcJCQgKDBQNDAsLDBkSEw8UHRofHh0a
HBwgJC4nICIsIxwcKDcpLDAxNDQ0Hyc5PTgyPC4zNDL/2wBDAQkJCQwLDBgNDRgyIRwhMjIyMjIy
MjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjL/wAARCACOAI4DASIA
AhEBAxEB/8QAHwAAAQUBAQEBAQEAAAAAAAAAAAECAwQFBgcICQoL/8QAtRAAAgEDAwIEAwUFBAQA
AAF9AQIDAAQRBRIhMUEGE1FhByJxFDKBkaEII0KxwRVS0fAkM2JyggkKFhcYGRolJicoKSo0NTY3
ODk6Q0RFRkdISUpTVFVWV1hZWmNkZWZnaGlqc3R1dnd4eXqDhIWGh4iJipKTlJWWl5iZmqKjpKWm
p6ipqrKztLW2t7i5usLDxMXGx8jJytLT1NXW19jZ2uHi4+Tl5ufo6erx8vP09fb3+Pn6/8QAHwEA
AwEBAQEBAQEBAQAAAAAAAAECAwQFBgcICQoL/8QAtREAAgECBAQDBAcFBAQAAQJ3AAECAxEEBSEx
BhJBUQdhcRMiMoEIFEKRobHBCSMzUvAVYnLRChYkNOEl8RcYGRomJygpKjU2Nzg5OkNERUZHSElK
U1RVVldYWVpjZGVmZ2hpanN0dXZ3eHl6goOEhYaHiImKkpOUlZaXmJmaoqOkpaanqKmqsrO0tba3
uLm6wsPExcbHyMnK0tPU1dbX2Nna4uPk5ebn6Onq8vP09fb3+Pn6/9oADAMBAAIRAxEAPwD3+iiv
H/EHiDxF/wAJf4x/4rj/AIR7RNC+xf8AMJju/wDXxj23ff8Ar97sBQB7BRXz/qHjDxF/wiGsa/oH
xU/tf+yvI86D/hHo7f8A1sgRfmdf948A9O2a6D4u/Eb+wvMstA8Wf2frdhjztP8A7O837Rv8sr+8
dSqbULNxnOcdaAPYKK8f1C58RaX/AGx9t+MHlf2N5H2//imo28nzseX0zuzkfdzjvis/W/ix4y8E
axPc+J/Cmyx1Lb/Z1n/aMJ+z+WoEvzxoS24sp+bGOgoA9wory/xl4706bR9E1bSfiB/YFje+f5cv
9jNdfatjKp4ZcptORyBnd7Vx+n/HTxFoXhDR73X/AA5/aH2/z/J1D7dHF9o2SEN+7SM7NuVXnGcZ
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
+a7CiigD/9k=
"></span></th><th valign="top" align="left" bgcolor="white" style="border-top:1px solid;Qwhite-space: nowrap;">George Washington</th><th valign="top" align="left" bgcolor="white" style="border-top:1px solid;Qwhite-space: nowrap;"><a href="callto:(202)000-0003">(202)000-0003</a><br><span style="color:black;background-color:#d0ffff !important;border:1px solid #d0ffff;">New patron</span></th>
	<td valign="top" bgcolor="white" style="border-top:1px solid" onclick="goto_map(4);"><a target="map" href="https://www.google.com/maps/dir/?api=1&amp;waypoints=38.88898,-77.032958|38.89871,-77.03364|38.89659,-77.02598|38.892206,-77.018777|38.89482,-77.01756|38.711032,-77.088291|38.883913,-77.064892&amp;destination=38.89879,-77.03364%3Ca">2 15th St NW<br> Washington, DC 20024</a></td></tr><tr><td bgcolor="white" colspan="4" align="right" valign="bottom"><table bgcolor="white" class="only-print"><tbody><tr><th bgcolor="white">▢</th><td bgcolor="white">Failed to deliver</td></tr><tr><th bgcolor="white">▢</th><td bgcolor="white">Needs to be called</td></tr></tbody></table></td></tr>
<tr>
	<th valign="top" align="left" bgcolor="white" style="border-top:1px solid;" rowspan="2"><span class="only-print"><img src="data:image/jpeg;base64,/9j/4AAQSkZJRgABAQAAAQABAAD/2wBDAAgGBgcGBQgHBwcJCQgKDBQNDAsLDBkSEw8UHRofHh0a
HBwgJC4nICIsIxwcKDcpLDAxNDQ0Hyc5PTgyPC4zNDL/2wBDAQkJCQwLDBgNDRgyIRwhMjIyMjIy
MjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjL/wAARCACGAIYDASIA
AhEBAxEB/8QAHwAAAQUBAQEBAQEAAAAAAAAAAAECAwQFBgcICQoL/8QAtRAAAgEDAwIEAwUFBAQA
AAF9AQIDAAQRBRIhMUEGE1FhByJxFDKBkaEII0KxwRVS0fAkM2JyggkKFhcYGRolJicoKSo0NTY3
ODk6Q0RFRkdISUpTVFVWV1hZWmNkZWZnaGlqc3R1dnd4eXqDhIWGh4iJipKTlJWWl5iZmqKjpKWm
p6ipqrKztLW2t7i5usLDxMXGx8jJytLT1NXW19jZ2uHi4+Tl5ufo6erx8vP09fb3+Pn6/8QAHwEA
AwEBAQEBAQEBAQAAAAAAAAECAwQFBgcICQoL/8QAtREAAgECBAQDBAcFBAQAAQJ3AAECAxEEBSEx
BhJBUQdhcRMiMoEIFEKRobHBCSMzUvAVYnLRChYkNOEl8RcYGRomJygpKjU2Nzg5OkNERUZHSElK
U1RVVldYWVpjZGVmZ2hpanN0dXZ3eHl6goOEhYaHiImKkpOUlZaXmJmaoqOkpaanqKmqsrO0tba3
uLm6wsPExcbHyMnK0tPU1dbX2Nna4uPk5ebn6Onq8vP09fb3+Pn6/9oADAMBAAIRAxEAPwD3+iiv
H/EHiDxF/wAJf4x/4rj/AIR7RNC+xf8AMJju/wDXxj23ff8Ar97sBQB7BRXz/qHjDxF/wiGsa/oH
xU/tf+yvI86D/hHo7f8A1sgRfmdf948A9O2a7D4hfFLTvCmsJHbazvvtNz9r0P7Kw+2eYqbP35Qi
PYG38Z3fdNAHqFFfP8/xG8Rf8Ih4Evb3xZ/ZH9q/2h9v1D+zo7j/AFUmI/3YX6L8uOuTnFaFp8WP
GUOj6j40ufCn2jwtP5X2Rf7RhT7Ltbyn5Cb33Seq8duOaAPcKK8f1D4jfY/7Ystf8Wf8Ixrc3keT
p/8AZ323+y8YLfvEXbN5qFW5+5ux1Fc//wALt/4Rb/mYf+E4+0/9OX9mfY9v/bM+Zv3f8B2e9AH0
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
"></span></th><th valign="top" align="left" bgcolor="white" style="border-top:1px solid;Qwhite-space: nowrap;">Thomas MaGoo</th><th valign="top" align="left" bgcolor="white" style="border-top:1px solid;Qwhite-space: nowrap;"><a href="callto:(202)000-0005">(202)000-0005</a><br><span style="color:black;background-color:#d0ffff !important;border:1px solid #d0ffff;">New patron</span></th>
	<td valign="top" bgcolor="white" style="border-top:1px solid" onclick="goto_map(5);"><a target="map" href="https://www.google.com/maps/dir/?api=1&amp;waypoints=38.89871,-77.03364|38.89659,-77.02598|38.892206,-77.018777|38.89482,-77.01756|38.711032,-77.088291|38.883913,-77.064892&amp;destination=38.89879,-77.03364%3Ca">500 Pennsylvania Avenue NW #1428<br> Washington, DC 20220</a></td></tr><tr><td bgcolor="white" colspan="4" align="right" valign="bottom"><table bgcolor="white" class="only-print"><tbody><tr><th bgcolor="white">▢</th><td bgcolor="white">Failed to deliver</td></tr><tr><th bgcolor="white">▢</th><td bgcolor="white">Needs to be called</td></tr></tbody></table></td></tr>
<tr>
	<th valign="top" align="left" bgcolor="white" style="border-top:1px solid;" rowspan="3"><span class="only-print"><img src="data:image/jpeg;base64,/9j/4AAQSkZJRgABAQAAAQABAAD/2wBDAAgGBgcGBQgHBwcJCQgKDBQNDAsLDBkSEw8UHRofHh0a
HBwgJC4nICIsIxwcKDcpLDAxNDQ0Hyc5PTgyPC4zNDL/2wBDAQkJCQwLDBgNDRgyIRwhMjIyMjIy
MjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjL/wAARCAB+AH4DASIA
AhEBAxEB/8QAHwAAAQUBAQEBAQEAAAAAAAAAAAECAwQFBgcICQoL/8QAtRAAAgEDAwIEAwUFBAQA
AAF9AQIDAAQRBRIhMUEGE1FhByJxFDKBkaEII0KxwRVS0fAkM2JyggkKFhcYGRolJicoKSo0NTY3
ODk6Q0RFRkdISUpTVFVWV1hZWmNkZWZnaGlqc3R1dnd4eXqDhIWGh4iJipKTlJWWl5iZmqKjpKWm
p6ipqrKztLW2t7i5usLDxMXGx8jJytLT1NXW19jZ2uHi4+Tl5ufo6erx8vP09fb3+Pn6/8QAHwEA
AwEBAQEBAQEBAQAAAAAAAAECAwQFBgcICQoL/8QAtREAAgECBAQDBAcFBAQAAQJ3AAECAxEEBSEx
BhJBUQdhcRMiMoEIFEKRobHBCSMzUvAVYnLRChYkNOEl8RcYGRomJygpKjU2Nzg5OkNERUZHSElK
U1RVVldYWVpjZGVmZ2hpanN0dXZ3eHl6goOEhYaHiImKkpOUlZaXmJmaoqOkpaanqKmqsrO0tba3
uLm6wsPExcbHyMnK0tPU1dbX2Nna4uPk5ebn6Onq8vP09fb3+Pn6/9oADAMBAAIRAxEAPwD3+iiv
H/EHiDxF/wAJf4x/4rj/AIR7RNC+xf8AMJju/wDXxj23ff8Ar97sBQB7BRXz/qHjDxF/wiGsa/oH
xU/tf+yvI86D/hHo7f8A1sgRfmdf948A9O2a9A8T/E3+y/F9r4U0DSP7c1uTf51r9p+zeTiMSL87
oVbKFjweNuOpoA9Aorw+0+NGo61o+o+J7aw+xWPh/wAr7XpvnLJ/aHnt5afvSgMXlkbuAd2cHFeg
aJaeMl1iC21bVN9jpu7zLz7PCP7Y8xSR8i82/knA4zv60AdhRXh+q/FLUb7R/iFq3h3Wd9jpv9m/
2XL9lUeX5jBZeHTJyQw+YHHatD/hJ/iHceL/ADdNs/tn2X/kK+F/Nt4/sO6PEP8ApTD95v5l+X7u
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
"></span></th><th valign="top" align="left" bgcolor="white" style="border-top:1px solid;Qwhite-space: nowrap;">John Ford</th><th valign="top" align="left" bgcolor="white" style="border-top:1px solid;Qwhite-space: nowrap;"><a href="callto:(202)000-0008">(202)000-0008</a><br><span style="color:black;background-color:#c0c0ff !important;border:1px solid #c0c0ff;">USDA box</span>, <span style="color:black;background-color:#ffb0b0 !important;border:1px solid #ffb0b0;">Special meal</span>, <span style="color:black;background-color:#d0ffff !important;border:1px solid #d0ffff;">New patron</span></th>
	<td valign="top" bgcolor="white" style="border-top:1px solid" onclick="goto_map(6);"><a target="map" href="https://www.google.com/maps/dir/?api=1&amp;waypoints=38.89659,-77.02598|38.892206,-77.018777|38.89482,-77.01756|38.711032,-77.088291|38.883913,-77.064892&amp;destination=38.89879,-77.03364%3Ca">511 10th St NW<br> Washington, DC 20004</a></td></tr><tr><td bgcolor="white" colspan="4" align="right" valign="bottom"><table bgcolor="white" class="only-print"><tbody><tr><th bgcolor="white">▢</th><td bgcolor="white">Failed to deliver</td></tr><tr><th bgcolor="white">▢</th><td bgcolor="white">Needs to be called</td></tr></tbody></table></td></tr>
<tr><td bgcolor="white" colspan="4">Balconies not available.  Deliver in the front.</td></tr>
<tr>
	<th valign="top" align="left" bgcolor="white" style="border-top:1px solid;" rowspan="2"><span class="only-print"><img src="data:image/jpeg;base64,/9j/4AAQSkZJRgABAQAAAQABAAD/2wBDAAgGBgcGBQgHBwcJCQgKDBQNDAsLDBkSEw8UHRofHh0a
HBwgJC4nICIsIxwcKDcpLDAxNDQ0Hyc5PTgyPC4zNDL/2wBDAQkJCQwLDBgNDRgyIRwhMjIyMjIy
MjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjL/wAARCAB+AH4DASIA
AhEBAxEB/8QAHwAAAQUBAQEBAQEAAAAAAAAAAAECAwQFBgcICQoL/8QAtRAAAgEDAwIEAwUFBAQA
AAF9AQIDAAQRBRIhMUEGE1FhByJxFDKBkaEII0KxwRVS0fAkM2JyggkKFhcYGRolJicoKSo0NTY3
ODk6Q0RFRkdISUpTVFVWV1hZWmNkZWZnaGlqc3R1dnd4eXqDhIWGh4iJipKTlJWWl5iZmqKjpKWm
p6ipqrKztLW2t7i5usLDxMXGx8jJytLT1NXW19jZ2uHi4+Tl5ufo6erx8vP09fb3+Pn6/8QAHwEA
AwEBAQEBAQEBAQAAAAAAAAECAwQFBgcICQoL/8QAtREAAgECBAQDBAcFBAQAAQJ3AAECAxEEBSEx
BhJBUQdhcRMiMoEIFEKRobHBCSMzUvAVYnLRChYkNOEl8RcYGRomJygpKjU2Nzg5OkNERUZHSElK
U1RVVldYWVpjZGVmZ2hpanN0dXZ3eHl6goOEhYaHiImKkpOUlZaXmJmaoqOkpaanqKmqsrO0tba3
uLm6wsPExcbHyMnK0tPU1dbX2Nna4uPk5ebn6Onq8vP09fb3+Pn6/9oADAMBAAIRAxEAPwD3+iiv
H/EHiDxF/wAJf4x/4rj/AIR7RNC+xf8AMJju/wDXxj23ff8Ar97sBQB7BRXz/qHjDxF/wiGsa/oH
xU/tf+yvI86D/hHo7f8A1sgRfmdf948A9O2a6D4m/F3/AIQ7xfpdlpsv2z7L5v8Aaun7fL3bo0MP
7xkOMbi3y+mDQB7BRXl93rfjLxXrGnaTolx/wjd9Z+b/AMJBFshvPse9d1tywAk3hSf3Z+Xd83Ss
/V/ib4i/4RDw54903SP+JJ/pP9q2P2mP/noIYf3jJu+/lvlX2PHNAHsFFfP/AIC+LviL/hEPFuv6
/L/a/wDZX2PyYNsdv/rZGRvmRP8AdPIPTtmuw8G+MvGWr/EfW9J1bQPs9jB5HmRfbIX/ALN3Qsw5
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
"></span></th><th valign="top" align="left" bgcolor="white" style="border-top:1px solid;Qwhite-space: nowrap;">Monty Picasso</th><th valign="top" align="left" bgcolor="white" style="border-top:1px solid;Qwhite-space: nowrap;"><a href="callto:(202)000-0009">(202)000-0009</a><br><span style="color:black;background-color:#ffb0b0 !important;border:1px solid #ffb0b0;">No frozen bag</span>, <span style="color:black;background-color:#d0ffff !important;border:1px solid #d0ffff;">New patron</span></th>
	<td valign="top" bgcolor="white" style="border-top:1px solid" onclick="goto_map(7);"><a target="map" href="https://www.google.com/maps/dir/?api=1&amp;waypoints=38.892206,-77.018777|38.89482,-77.01756|38.711032,-77.088291|38.883913,-77.064892&amp;destination=38.89879,-77.03364%3Ca">Constitution Ave. NW<br> Washington, DC 20565</a></td></tr><tr><td bgcolor="white" colspan="4" align="right" valign="bottom"><table bgcolor="white" class="only-print"><tbody><tr><th bgcolor="white">▢</th><td bgcolor="white">Failed to deliver</td></tr><tr><th bgcolor="white">▢</th><td bgcolor="white">Needs to be called</td></tr></tbody></table></td></tr>
<tr>
	<th valign="top" align="left" bgcolor="white" style="border-top:1px solid;" rowspan="2"><span class="only-print"><img src="data:image/jpeg;base64,/9j/4AAQSkZJRgABAQAAAQABAAD/2wBDAAgGBgcGBQgHBwcJCQgKDBQNDAsLDBkSEw8UHRofHh0a
HBwgJC4nICIsIxwcKDcpLDAxNDQ0Hyc5PTgyPC4zNDL/2wBDAQkJCQwLDBgNDRgyIRwhMjIyMjIy
MjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjL/wAARCAB2AHYDASIA
AhEBAxEB/8QAHwAAAQUBAQEBAQEAAAAAAAAAAAECAwQFBgcICQoL/8QAtRAAAgEDAwIEAwUFBAQA
AAF9AQIDAAQRBRIhMUEGE1FhByJxFDKBkaEII0KxwRVS0fAkM2JyggkKFhcYGRolJicoKSo0NTY3
ODk6Q0RFRkdISUpTVFVWV1hZWmNkZWZnaGlqc3R1dnd4eXqDhIWGh4iJipKTlJWWl5iZmqKjpKWm
p6ipqrKztLW2t7i5usLDxMXGx8jJytLT1NXW19jZ2uHi4+Tl5ufo6erx8vP09fb3+Pn6/8QAHwEA
AwEBAQEBAQEBAQAAAAAAAAECAwQFBgcICQoL/8QAtREAAgECBAQDBAcFBAQAAQJ3AAECAxEEBSEx
BhJBUQdhcRMiMoEIFEKRobHBCSMzUvAVYnLRChYkNOEl8RcYGRomJygpKjU2Nzg5OkNERUZHSElK
U1RVVldYWVpjZGVmZ2hpanN0dXZ3eHl6goOEhYaHiImKkpOUlZaXmJmaoqOkpaanqKmqsrO0tba3
uLm6wsPExcbHyMnK0tPU1dbX2Nna4uPk5ebn6Onq8vP09fb3+Pn6/9oADAMBAAIRAxEAPwD3+iiv
H/EHiDxF/wAJf4x/4rj/AIR7RNC+xf8AMJju/wDXxj23ff8Ar97sBQB7BRXz/qHjDxF/wiGsa/oH
xU/tf+yvI86D/hHo7f8A1sgRfmdf948A9O2a9Q1vW9Rm1iePwxcfb77Q9v8AaOh7Fi+1eco8r9/I
MJtG5/lznG04oA7CivH9I+I39l+EPEev/wDCWf8ACZ/2f9m/cf2d/Z3k+ZIU+9tO7Oc9DjZ71yGi
fGLUbHR4Nb1bxr/al8m7zPDn9lrB5mWKD/SVTAwCJOBzjb3oA+j6K+cNE+PGoro8Fzq17vvtN3eZ
Z+Uo/tjzGIHzrHi38kYPGd/St/wp8eNOh0fw/beIr37RfT/aP7UvPKZPsu1mMXyJHh9w2j5enU0A
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
AFFFFABRRRQAUUUUAf/Z
"></span></th><th valign="top" align="left" bgcolor="white" style="border-top:1px solid;Qwhite-space: nowrap;">Abraham Lincoln</th><th valign="top" align="left" bgcolor="white" style="border-top:1px solid;Qwhite-space: nowrap;"><a href="callto:(202)000-0002">(202)000-0002</a><br><span style="color:black;background-color:#30ffff !important;border:1px solid #30ffff;">2 dogs</span>, <span style="color:black;background-color:#d0ffff !important;border:1px solid #d0ffff;">New patron</span></th>
	<td valign="top" bgcolor="white" style="border-top:1px solid" onclick="goto_map(8);"><a target="map" href="https://www.google.com/maps/dir/?api=1&amp;waypoints=38.89482,-77.01756|38.711032,-77.088291|38.883913,-77.064892&amp;destination=38.89879,-77.03364%3Ca">451 Indiana Ave NW<br> Washington, DC 20001</a></td></tr><tr><td bgcolor="white" colspan="4" align="right" valign="bottom"><table bgcolor="white" class="only-print"><tbody><tr><th bgcolor="white">▢</th><td bgcolor="white">Failed to deliver</td></tr><tr><th bgcolor="white">▢</th><td bgcolor="white">Needs to be called</td></tr></tbody></table></td></tr>
<tr>
	<th valign="top" align="left" bgcolor="white" style="border-top:1px solid;" rowspan="2"><span class="only-print"><img src="data:image/jpeg;base64,/9j/4AAQSkZJRgABAQAAAQABAAD/2wBDAAgGBgcGBQgHBwcJCQgKDBQNDAsLDBkSEw8UHRofHh0a
HBwgJC4nICIsIxwcKDcpLDAxNDQ0Hyc5PTgyPC4zNDL/2wBDAQkJCQwLDBgNDRgyIRwhMjIyMjIy
MjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjL/wAARCABuAG4DASIA
AhEBAxEB/8QAHwAAAQUBAQEBAQEAAAAAAAAAAAECAwQFBgcICQoL/8QAtRAAAgEDAwIEAwUFBAQA
AAF9AQIDAAQRBRIhMUEGE1FhByJxFDKBkaEII0KxwRVS0fAkM2JyggkKFhcYGRolJicoKSo0NTY3
ODk6Q0RFRkdISUpTVFVWV1hZWmNkZWZnaGlqc3R1dnd4eXqDhIWGh4iJipKTlJWWl5iZmqKjpKWm
p6ipqrKztLW2t7i5usLDxMXGx8jJytLT1NXW19jZ2uHi4+Tl5ufo6erx8vP09fb3+Pn6/8QAHwEA
AwEBAQEBAQEBAQAAAAAAAAECAwQFBgcICQoL/8QAtREAAgECBAQDBAcFBAQAAQJ3AAECAxEEBSEx
BhJBUQdhcRMiMoEIFEKRobHBCSMzUvAVYnLRChYkNOEl8RcYGRomJygpKjU2Nzg5OkNERUZHSElK
U1RVVldYWVpjZGVmZ2hpanN0dXZ3eHl6goOEhYaHiImKkpOUlZaXmJmaoqOkpaanqKmqsrO0tba3
uLm6wsPExcbHyMnK0tPU1dbX2Nna4uPk5ebn6Onq8vP09fb3+Pn6/9oADAMBAAIRAxEAPwD3+iiv
H/EHiDxF/wAJf4x/4rj/AIR7RNC+xf8AMJju/wDXxj23ff8Ar97sBQB7BRXz/qHjDxF/wiGsa/oH
xU/tf+yvI86D/hHo7f8A1sgRfmdf948A9O2a9A8T+IP7U8X2vhTQPHH9h63Hv861/sn7T52YxIvz
uAq4QMeDzux1FAHoFFfP/wDwt3xF4a/0LxXL5Wt6N/x86ftjb+1vO5X95GhWDykZW4zv6cGvQPDH
/Cw9L8IXWpa//wATzW5Nnk6R/o9t5OJCrfvkyrZQq/I4246mgD0CivP9P+I3h3xT4v0ey0DxZ/z3
87T/AOzpP9M/dkr+8dR5ezazcfe6V5//AMNNf9Sj/wCVL/7VQB9AUV5/qGoeIvFPi/WNA0DXP+Ee
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
"></span></th><th valign="top" align="left" bgcolor="white" style="border-top:1px solid;Qwhite-space: nowrap;">Martha Washington</th><th valign="top" align="left" bgcolor="white" style="border-top:1px solid;Qwhite-space: nowrap;"><a href="callto:(202)000-0004">(202)000-0004</a><br><span style="color:black;background-color:#d0ffff !important;border:1px solid #d0ffff;">New patron</span></th>
	<td valign="top" bgcolor="white" style="border-top:1px solid" onclick="goto_map(9);"><a target="map" href="https://www.google.com/maps/dir/?api=1&amp;waypoints=38.711032,-77.088291|38.883913,-77.064892&amp;destination=38.89879,-77.03364%3Ca">3200 Mount Vernon Memorial Hwy<br> Mt Vernon, VA 22121</a></td></tr><tr><td bgcolor="white" colspan="4" align="right" valign="bottom"><table bgcolor="white" class="only-print"><tbody><tr><th bgcolor="white">▢</th><td bgcolor="white">Failed to deliver</td></tr><tr><th bgcolor="white">▢</th><td bgcolor="white">Needs to be called</td></tr></tbody></table></td></tr>
<tr>
	<th valign="top" align="left" bgcolor="white" style="border-top:1px solid;" rowspan="2"><span class="only-print"><img src="data:image/jpeg;base64,/9j/4AAQSkZJRgABAQAAAQABAAD/2wBDAAgGBgcGBQgHBwcJCQgKDBQNDAsLDBkSEw8UHRofHh0a
HBwgJC4nICIsIxwcKDcpLDAxNDQ0Hyc5PTgyPC4zNDL/2wBDAQkJCQwLDBgNDRgyIRwhMjIyMjIy
MjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjL/wAARCABmAGYDASIA
AhEBAxEB/8QAHwAAAQUBAQEBAQEAAAAAAAAAAAECAwQFBgcICQoL/8QAtRAAAgEDAwIEAwUFBAQA
AAF9AQIDAAQRBRIhMUEGE1FhByJxFDKBkaEII0KxwRVS0fAkM2JyggkKFhcYGRolJicoKSo0NTY3
ODk6Q0RFRkdISUpTVFVWV1hZWmNkZWZnaGlqc3R1dnd4eXqDhIWGh4iJipKTlJWWl5iZmqKjpKWm
p6ipqrKztLW2t7i5usLDxMXGx8jJytLT1NXW19jZ2uHi4+Tl5ufo6erx8vP09fb3+Pn6/8QAHwEA
AwEBAQEBAQEBAQAAAAAAAAECAwQFBgcICQoL/8QAtREAAgECBAQDBAcFBAQAAQJ3AAECAxEEBSEx
BhJBUQdhcRMiMoEIFEKRobHBCSMzUvAVYnLRChYkNOEl8RcYGRomJygpKjU2Nzg5OkNERUZHSElK
U1RVVldYWVpjZGVmZ2hpanN0dXZ3eHl6goOEhYaHiImKkpOUlZaXmJmaoqOkpaanqKmqsrO0tba3
uLm6wsPExcbHyMnK0tPU1dbX2Nna4uPk5ebn6Onq8vP09fb3+Pn6/9oADAMBAAIRAxEAPwD3+iiv
H/EHiDxF/wAJf4x/4rj/AIR7RNC+xf8AMJju/wDXxj23ff8Ar97sBQB7BRXz/qHjDxF/wiGsa/oH
xU/tf+yvI86D/hHo7f8A1sgRfmdf948A9O2a9A8T+Nvs/i+10bQNQ+2a3a7/ADvD3k+X9u3Rhl/0
l12x7E3ScH5sbetAHoFFfP8Aq/xN+IfgX/hHP+Er0j/n5+0/6Tb/APEx6bf9WjeV5e5en3q7Dwbr
fjKbR9b1aO4/4TCxPkf2LLsh0/7V8zLPxjKbTx8452cdaAPUKK8P1uX4qaRrE+kx+MPtF9Pt/sWL
+zLVP7S2qGn55EPlg5+c/N2roPiFrfjLwR8OEktrj+1L5M/a9c2QwfZ8zJs/cEENuDbOOmNx60Ae
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
ACiiigAooooAKKKKACiiigAooooAKKKKAP/Z
"></span></th><th valign="top" align="left" bgcolor="white" style="border-top:1px solid;Qwhite-space: nowrap;">Robert E. Lee</th><th valign="top" align="left" bgcolor="white" style="border-top:1px solid;Qwhite-space: nowrap;"><a href="callto:(202)000-0007">(202)000-0007</a><br><span style="color:black;background-color:#d0ffff !important;border:1px solid #d0ffff;">New patron</span></th>
	<td valign="top" bgcolor="white" style="border-top:1px solid" onclick="goto_map(10);"><a target="map" href="https://www.google.com/maps/dir/?api=1&amp;waypoints=38.883913,-77.064892&amp;destination=38.89879,-77.03364%3Ca">1 Memorial Ave. Arlington<br> Virginia 22211</a></td></tr><tr><td bgcolor="white" colspan="4" align="right" valign="bottom"><table bgcolor="white" class="only-print"><tbody><tr><th bgcolor="white">▢</th><td bgcolor="white">Failed to deliver</td></tr><tr><th bgcolor="white">▢</th><td bgcolor="white">Needs to be called</td></tr></tbody></table></td></tr>
<tr>
	<th valign="top" align="left" bgcolor="white" style="border-top:1px solid;" rowspan="2"><span class="only-print"><img src="data:image/jpeg;base64,/9j/4AAQSkZJRgABAQAAAQABAAD/2wBDAAgGBgcGBQgHBwcJCQgKDBQNDAsLDBkSEw8UHRofHh0a
HBwgJC4nICIsIxwcKDcpLDAxNDQ0Hyc5PTgyPC4zNDL/2wBDAQkJCQwLDBgNDRgyIRwhMjIyMjIy
MjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjL/wAARCABeAF4DASIA
AhEBAxEB/8QAHwAAAQUBAQEBAQEAAAAAAAAAAAECAwQFBgcICQoL/8QAtRAAAgEDAwIEAwUFBAQA
AAF9AQIDAAQRBRIhMUEGE1FhByJxFDKBkaEII0KxwRVS0fAkM2JyggkKFhcYGRolJicoKSo0NTY3
ODk6Q0RFRkdISUpTVFVWV1hZWmNkZWZnaGlqc3R1dnd4eXqDhIWGh4iJipKTlJWWl5iZmqKjpKWm
p6ipqrKztLW2t7i5usLDxMXGx8jJytLT1NXW19jZ2uHi4+Tl5ufo6erx8vP09fb3+Pn6/8QAHwEA
AwEBAQEBAQEBAQAAAAAAAAECAwQFBgcICQoL/8QAtREAAgECBAQDBAcFBAQAAQJ3AAECAxEEBSEx
BhJBUQdhcRMiMoEIFEKRobHBCSMzUvAVYnLRChYkNOEl8RcYGRomJygpKjU2Nzg5OkNERUZHSElK
U1RVVldYWVpjZGVmZ2hpanN0dXZ3eHl6goOEhYaHiImKkpOUlZaXmJmaoqOkpaanqKmqsrO0tba3
uLm6wsPExcbHyMnK0tPU1dbX2Nna4uPk5ebn6Onq8vP09fb3+Pn6/9oADAMBAAIRAxEAPwD3+iiv
H/EHiDxF/wAJf4x/4rj/AIR7RNC+xf8AMJju/wDXxj23ff8Ar97sBQB7BRXz/qHjDxF/wiGsa/oH
xU/tf+yvI86D/hHo7f8A1sgRfmdf948A9O2a9Qu/FenTfEfTvDtt4k+z30Hm/a9K+ws/2rdDvT98
RhNo+bg89DQB2FFef+PfE/iLQvF/hKy0Cz/tD7f9s87T/Nji+0bI1K/vHB2bcs3GM4xR4g/4WH/x
WP8AY3/Tl/YP/Hv7faPvfj9//gNAHoFFfOF38YtR1fWNOubbxr/YFje+b9rs/wCy1uv7N2LhPnKA
zeYRnjG3dg9Kv6h8RvEVn4Q1i90DxZ/wk/k+R52of2dHZf2XmQBf3br++83LLx9zbnvQB9AUV4/4
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
"></span></th><th valign="top" align="left" bgcolor="white" style="border-top:1px solid;Qwhite-space: nowrap;">Test Distributor</th><th valign="top" align="left" bgcolor="white" style="border-top:1px solid;Qwhite-space: nowrap;"><a href="callto:(202)000-0000">(202)000-0000</a></th>
	<td valign="top" bgcolor="white" style="border-top:1px solid" onclick="goto_map(11);"><a target="map" href="https://www.google.com/maps/dir/?api=1&amp;destination=38.89879,-77.03364%3Ca">1600 Pennsylvania Avenue NW<br> Washington, DC 20500</a></td></tr><tr><td bgcolor="white" colspan="4" align="right" valign="bottom"><table bgcolor="white" class="only-print"><tbody><tr><th bgcolor="white">▢</th><td bgcolor="white">Failed to deliver</td></tr><tr><th bgcolor="white">▢</th><td bgcolor="white">Needs to be called</td></tr></tbody></table></td></tr>
</tbody></table><center class="no-print"><table width="100%"><tbody><tr><th width="33"><a target="Google_interactive" href="https://www.google.com/maps/dir/?api=1&amp;origin=38.89879,-77.03364&amp;waypoints=38.8898,-77.00589|38.88763,-77.00474|38.887853,-77.040587|38.88898,-77.032958|38.89871,-77.03364|38.89659,-77.02598|38.892206,-77.018777|38.89482,-77.01756|38.711032,-77.088291|38.883913,-77.064892&amp;destination=38.89879,-77.03364">Google map</a></th><th width="33"><a target="Mapquest_interactive" href="http://www.mapquest.com/directions/from/near-38.89879,-77.03364/to/near-38.8898,-77.00589/to/near-38.88763,-77.00474/to/near-38.887853,-77.040587/to/near-38.88898,-77.032958/to/near-38.89871,-77.03364/to/near-38.89659,-77.02598/to/near-38.892206,-77.018777/to/near-38.89482,-77.01756/to/near-38.711032,-77.088291/to/near-38.883913,-77.064892/to/near-38.89879,-77.03364">Mapquest map</a></th><th width="33"><a target="Apple_interactive" href="https://beta.maps.apple.com/?dirflg=d&amp;saddr=38.89879,-77.03364&amp;daddr=38.8898,-77.00589&amp;daddr=38.88763,-77.00474&amp;daddr=38.887853,-77.040587&amp;daddr=38.88898,-77.032958&amp;daddr=38.89871,-77.03364&amp;daddr=38.89659,-77.02598&amp;daddr=38.892206,-77.018777&amp;daddr=38.89482,-77.01756&amp;daddr=38.711032,-77.088291&amp;daddr=38.883913,-77.064892&amp;daddr=38.89879,-77.03364">Apple map</a></th></tr></tbody></table></center></td></tr>
<tr id="reset_id" style="display:none;"><th>
    <button type="button" value="Update boss" onclick="generate_update(1);">Done</button>
    <button type="button" value="Reroute" onclick="reroute();">Re-route</button>
    <button type="button" value="Reset route" onclick="reset_route(1);">Reset route</button>
    <button type="button" id="Debug_id" style="display:none;" onclick="debug_page();">Debug</button>
    </th></tr>
    <tr><td id="position_trail"></td></tr>
</tbody></table>

<iframe width="500px" height="500px" name="query_frame" style="display:none;background-color:white">Not updated</iframe>

<div id="id_oneof_screen" style="display:none"></div>

<table id="id_map_screen" border="0" style="display:none;">
    <tbody><tr><th valign="middle" onclick='lightup("big");'>
        <button type="button">←</button></th>
	<td id="map" style="width: 100%; height: 530px;"></td></tr></tbody></table>

</center>
<center class="no-print">
    <input type="button" onclick="window.print();" value="Print route sheet">
</center>
