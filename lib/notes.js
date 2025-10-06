<script>
var note_pieces		= new Array();
var note_piece_type	= new Array();
var last_ind		= new Array();
var open_pic		= new Array();
var note_id		= new Array();

var stream;
var notes_video_id;
var notes_canvas_id;
var notes_snap_id;
var notes_cancel_id;
var master_table_id;
var last_camera;

function setup_notes( current_note )
    {
    if( ! notes_video_id )
	{
	notes_video_id	= document.getElementById('notes_video_id');
	notes_canvas_id	= document.getElementById('notes_canvas_id');
	notes_snap_id	= document.getElementById('notes_snap_id');
	notes_cancel_id	= document.getElementById('notes_cancel_id');
	master_table_id	= document.getElementById('master_table_id');
	start_camera();
	}
    note_pieces[current_note] = new Array();
    note_piece_type[current_note] = new Array();
    last_ind[current_note] = -1;
    open_pic[current_note] = -1;
    note_id[current_note] = document.getElementById(current_note+'_div');
    redraw_note(current_note);
    }

async function start_camera()
    {
    try {
	stream = await navigator.mediaDevices.getUserMedia(
	    { 
	    video: { facingMode: 'environment' } 
	    });
	notes_video_id.srcObject = stream;
	}
    catch (err)
	{
	console.error("Error accessing the camera", err);
	alert("Error accessing the camera: " + err.message);
	}
    }

function stop_camera()
    {
    if( stream )
        {
	notes_video_id.srcObject = null;
	stream = undefined;
	}
    }

function snap_photo()
    {
    current_note = last_camera;
    notes_canvas_id.width = notes_video_id.videoWidth;
    notes_canvas_id.height = notes_video_id.videoHeight;
    notes_canvas_id.getContext('2d').drawImage(notes_video_id,
	0, 0,
	notes_canvas_id.width, notes_canvas_id.height);
    var data = notes_canvas_id.toDataURL('image/jpeg')
    note_pieces[current_note] ||= new Array();
    note_pieces[current_note].splice( open_pic[current_note], 0, data);
    note_piece_type[current_note] ||= new Array();
    note_piece_type[current_note].splice( open_pic[current_note], 0, 'pic' );

    // stop_camera();	// Naw, don't
    notes_video_id.style.display='none';
    notes_snap_id.style.display='none';
    notes_cancel_id.style.display='none'

    for( current_note in note_pieces )
        {
	last_ind[current_note] = -1;
	redraw_note( current_note );
	}
    master_table_id.style.display = '';
    }

function cancel_photo()
    {
    notes_video_id.style.display='none';
    notes_snap_id.style.display='none';
    notes_cancel_id.style.display='none';
    master_table_id.style.display = '';
    }

function htmlify( s )
    {
    return s;
    }

function doEdit( current_note, ind, addflag, typeflag )
    {
    note_pieces[current_note] ||= new Array();
    note_piece_type[current_note] ||= new Array();
    if( ! addflag )
        { note_piece_type[current_note][ind] = typeflag; }
    else
	{
	note_pieces[current_note].splice( ind, 0, "" );
	note_piece_type[current_note].splice( ind, 0, typeflag );
	}
    last_ind[current_note] = ind;	// Meaningless for pic
    redraw_note(current_note);
    }

function doPic( current_note, current_pic )
    {
    open_pic[current_note] = current_pic;
    notes_video_id.style.display='';
    notes_snap_id.style.display='';
    notes_cancel_id.style.display='';
    master_table_id.style.display = 'none';
    last_camera = current_note;
    // start_camera();
    }

function doDelete( current_note, ind )
    {
    note_pieces[current_note].splice( ind, 1 );
    note_piece_type[current_note].splice( ind, 1 );
    last_ind[current_note] = -1;
    redraw_note(current_note);
    }

function doCloseNote( current_note )
    {
    last_ind[current_note] = -1;
    redraw_note(current_note);
    }

function redraw_note(current_note)
    {
    var s = new Array(
        "<table width=100%>"
	+"<input name=\""+current_note
	    +"\" id=\""+current_note
	    +"_id\" type=hidden>"
	);
    for( var note_ind=0; note_ind<note_pieces[current_note].length+1; note_ind++ )
        {
	s.push('<tr><th colspan=2>');
	s.push("<input type=button value='Add note'"
	    +" onClick='doEdit(\""+current_note+"\","+note_ind+",1,\"note\");'>");
	s.push("<input type=button value='Add pic'"
	    +" onClick='doPic(\""+current_note+"\","+note_ind+");'>");
	s.push('</th></tr>')
	if( note_ind <  note_pieces[current_note].length )
	    {
	    s.push("<input type=hidden name=note_"+note_ind+">");
	    s.push("<tr><th width=1px>");
	    s.push("<input type=button value='Delete'"
		+" onClick='doDelete(\""+current_note+"\","+note_ind+");'>");
	    if( note_piece_type[current_note][note_ind] == 'pic' )
		{
		s.push( "</th><td><img width=90% src='"
		    + note_pieces[current_note][note_ind] + "'>" );
		}
	    else if( last_ind[current_note] != note_ind )
		{
		s.push("<br><input type=button value='Edit'"
		    +" onClick='doEdit(\""+current_note+"\","+note_ind+",0,\"note\");'>");
		s.push("</th><td>");
		s.push("<pre>"+htmlify(note_pieces[current_note][note_ind]||"")+"</pre>");
		}
	    else
		{
		s.push("<br><input type=button value='Close'"
		    +" onClick='doCloseNote(\""+current_note+"\");'>");
		s.push("</th><td>");
		s.push("<textarea cols=60 placeholder='Add text here' onChange='"
		    +"note_pieces[\""+current_note+"\"]["+note_ind+"]=this.value;'>"+(note_pieces[current_note][note_ind]||"")
		    +"</textarea>");
		}
	    s.push("</td></tr>\n");
	    }
	}
    s.push('</table>');
    note_id[current_note].innerHTML = s.join("");
    }

function do_submit()
    {
    for( var current_note in note_pieces )
	{
        (document.getElementById(current_note+"_id")).value =
	    note_pieces[current_note].join("~~~");
	}
    window.document.form.submit();
    }
</script>
