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
    with( window.document.$FORMNAME )
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
var DITTOS = ["*","!!","*","+","#"];
function fixtext( tptr, ttype, lastval )
    {
    if( DITTOS.indexOf( tptr.value ) >= 0 ) { tptr.value = lastval; }

    while( 1 )
	{
	if( ttype == "Phone" || ttype == "Notify" )
	    {
	    if( tptr.value == "0" ) { tptr.value = lastval; }
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
    {	name:	"Start with",
	help:	" help='route_order_start_with'",
	style:	" style='background-color:white'" },
    {	name:	"Optimize",
	help:	" help='route_order_optimize'",
	style:	" style='background-color:#b0ffd0'" },
    {	name:	"End with",
	help:	" help='route_order_end_with'",
	style:	" style='background-color:white'" }
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
    s.push("<tr><th>Order<br>group</th><th>Patron</th><th>Address</th></tr>\n");
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
		    + RANGE_INFO[range].style
		    + RANGE_INFO[range].help
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
	"<input type=button help='route_order_up' width=100% onClick='order_swap(-1);' value='&uarr;'>",
	"<input type=button help='route_order_down' width=100% onClick='order_swap( 1);' value='&darr;'>",
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

//////////////////////////////////////////////////////////////////////////
//	User checked or un-checked a route run indicating whether	//
//	or not to include in the end map.				//
//////////////////////////////////////////////////////////////////////////
function maps_list_changed()
    {
    var num_checked = 0;
    var check_boxes = document.getElementsByName( 'maps' );
    for( var i=0; i<check_boxes.length; i++ )
        { if( check_boxes[i].checked ) { num_checked++; } }
    var p = document.getElementById( 'opt_download_ext' );
    if( p )
	{
	if( num_checked <= 0 )
	    {
	    p.innerHTML = seltext[0];
	    p.selected = true;
	    }
	else
	    {
	    p.innerHTML = seltext[1];
	    p.selected = true;
	    }

	for( var ext in minmaps )
	    {
	    var p = document.getElementById( 'opt_'+ext );
	    p.disabled =
		( num_checked < minmaps[ext] || num_checked > maxmaps[ext] );
	    }
	}
    }
