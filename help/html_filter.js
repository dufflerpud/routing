function reset_sbs()
    {
    for ( var e of document.getElementsByClassName("sb") )
        {
	if( e.nodeName=="BLOCKQUOTE" || e.nodeName=="DIV" || e.nodeName=="SPAN" )
	    { e.style.display = "none"; }
	else if( e.nodeName=="INPUT" )
	    { e.checked = false; }
	}
    for ( var e of document.getElementsByTagName("DETAILS") )
        {
	e.open = false;
	}
    }

function showblock( block_name )
    {
    var checked = (document.getElementById( "cb_"+block_name )).checked;
    reset_sbs();
    var pieces = block_name.split('_');
    var endat = ( checked ? pieces.length : pieces.length-1 );
    var id = "";
    for( var i=0; i<endat; i++ )
        {
	id += ("_"+pieces[i]);
	(document.getElementById( "sb"+id )).style.display = 'block';
	(document.getElementById( "cb"+id )).checked = true;
	}
    }

var iframe_contents = new Array();
var current_url;
var detail_element;
function update_details( text )
    {
    if( /.*(<summary>.*?<\/summary>)/ms.test( detail_element.innerHTML ) )
        { detail_element.innerHTML = RegExp.$1 + text; }
    }

function iframe_loaded( frame_element )
    {
    var new_details = frame_element.contentDocument.body.innerHTML;
    if( new_details )
        {
	iframe_contents[current_url] = new_details;
	update_details( iframe_contents[current_url] );
	}
    }

function setup_include( set_detail_element, set_current_url )
    {
    detail_element = set_detail_element;
    current_url = set_current_url;
    if( iframe_contents[current_url] )
        { return update_details( iframe_contents[current_url] ); }

    var span_id = document.getElementById(current_url);
    if( span_id )
        {
	iframe_contents[current_url] = span_id.innerHTML;
	return update_details( iframe_contents[current_url] );
	}
    (document.getElementById("loading_frame")).src = current_url + "/embedded";
    }

function old_setup_include( detail_element, id_name )
    {
    if( /.*(<summary>.*?<\/summary>)/ms.test( detail_element.innerHTML ) )
        {
	detail_element.innerHTML
	    = RegExp.$1 + document.getElementById(id_name).innerHTML;
	}
    }
