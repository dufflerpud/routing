#!/usr/bin/perl -w
#@HDR@	$Id: app.cgi,v 1.1 2020/08/12 21:17:31 chris Exp chris $
#@HDR@		Copyright 2024 by
#@HDR@		Christopher Caldwell/Brightsands
#@HDR@		P.O. Box 401, Bailey Island, ME 04003
#@HDR@		All Rights Reserved
#@HDR@
#@HDR@	This software comprises unpublished confidential information
#@HDR@	of Brightsands and may not be used, copied or made available
#@HDR@	to anyone, except in accordance with the license under which
#@HDR@	it is furnished.
#########################################################################
#	routing.cgi							#
#		2024-04-18	c.m.caldwell@alumni.unh.edu		#
#									#
#	Create routes for drivers for meal delivery service.		#
#									#
#	Tested with:							#
#		Meals-on-wheels						#
#		Harpswell Aging	at Home					#
#########################################################################

#########################################################################
#	Perl startup.							#
#########################################################################
use strict;
use MIME::Lite;
use Time::Local;
use JSON;
use Data::Dumper;
use List::Util qw(min max);

use lib "/usr/local/lib/perl";
use cpi_compress_integer qw(compress_integer);
use cpi_qrcode_of qw(qrcode_of);
use cpi_translate qw(xlate xlfatal xprint);
use cpi_user qw(in_group logout_select can_admin);
use cpi_cache qw(cache);
use cpi_hash qw(hashof);
use cpi_drivers qw(get_drivers);
use cpi_setup qw(setup);
use cpi_help qw(help_strings);
use cpi_inlist qw(inlist);
use cpi_template qw(subst_list template);
use cpi_send_file qw(sendmail);
use cpi_english qw(nword plural);
use cpi_db qw(dbadd dbdel dbdelkey dbget dbnewkey dbpop dbput dbread dbwrite
 DBread DBwrite DBpop DBget DBput DBdelkey DBadd DBdel DBnewkey);
use cpi_file qw(autopsy cleanup fatal files_in read_file read_lines
 tempfile write_file echodo );
use cpi_filename qw(filename_to_text text_to_filename);
use cpi_time qw(time_string);
use cpi_cgi qw(CGIheader note_to_html safe_html show_vars);
use cpi_mime qw( mime_string );
use cpi_vars;

$cpi_vars::TABLE_TAGS	= "bgcolor=\"#c0c0d0\"";
$cpi_vars::TABLE_TAGS	= "USECSS";

#print "Content-type:  text/plain\n\n";
#close( STDOUT );	open( STDOUT, "> /stdout" );
#close( STDERR );	open( STDERR, ">> /var/log/routing/stderr" );

my $old_fh = select(STDERR);
$| = 1;
select($old_fh);

#package main;
#do "./common.pl";

package main;

&setup(
	stderr=>"routing",
	Qrequire_captcha=>1,
	Qpreset_language=>"en",
	anonymous_funcs=>"map_with_custom_header,export_with_custom_header,anonymous_new_record,anonymous_add_record,anonymous_new_form"
	);

print STDERR <<EOF;
PROG=$cpi_vars::PROG
BASEDIR=$cpi_vars::BASEDIR
EOF

#########################################################################
#	Constant declarations.						#
#########################################################################

my $LIB 		= $cpi_vars::BASEDIR."/lib";
my $SRC 		= $cpi_vars::BASEDIR."/src";
my $PRETTY_PROG		= ucfirst( (split(/\//,$cpi_vars::BASEDIR))[-1] );

my %TEMPLATES =		# This used to be much larger
    (
    "html"		=> $LIB."/template.html"
    );

my $ROUTINGJS 		= $LIB."/${cpi_vars::PROG}_header.js";
my $ROUTEORDERJS	= $LIB."/${cpi_vars::PROG}_order.js";
my $COLOR_MAP_FILE	= $LIB."/colors";
my $MAPPER_DIR		= $SRC."/mappers";
my $PORTING_DIR		= $SRC."/porting";

our $FORMNAME		= "form";
$cpi_vars::CACHEDIR 	= "$cpi_vars::BASEDIR/cache";
my $DEST_DIR		= "routes";
my $DEST_HTTP		= "/var/www/routing$cpi_vars::OFFSET/$DEST_DIR";
$cpi_vars::DOMAIN	= "Brightsands.com";
my $MAILSRC		= "routing\@$cpi_vars::DOMAIN";
my $BASE_URL		= "http://routing.$cpi_vars::DOMAIN$cpi_vars::OFFSET";
my $BASES_URL		= "https://routing.$cpi_vars::DOMAIN$cpi_vars::OFFSET";
#my $GOOGLE_KML		= "$BASE_URL/google_kml.html";
$cpi_vars::URL			= "$BASES_URL/$DEST_DIR";
#our $PROG_URL		= $BASES_URL.($ENV{SCRIPT_NAME}||($cpi_vars::PROG.".cgi"));
our $PROG_URL		= $BASES_URL."/index.cgi";
$PROG_URL = $BASES_URL."/index-test.cgi" if(($ENV{SCRIPT_NAME}||"") =~ /-test/);
my $PROJLONG		= "Routing";
my $PROJECT		= "Routing";
my $LOGDIR		= "/var/log/$PROJECT";
my $PATRON_DIR		= "$LOGDIR/patrons";
my $TRIPS_DIR		= "$LOGDIR/trips";
my $HTML_DIR		= "$LOGDIR/html";
my $PROGRESS_DIR	= "$LOGDIR/progress";
my $ASSESSMENT_DIR	= "$LOGDIR/assessments";
my $PROGRESS_URL	= "$BASE_URL/progress";
my $DISABLED		= "$cpi_vars::BASEDIR/disabled.html";
my $DISTRIBUTOR_DIR	= "$cpi_vars::BASEDIR/Distributors";
my $EXPECTED_DIR	= "$LOGDIR/expected";
my $EXPECTED_URL	= "$BASE_URL/expected";
my $INDENT_JSON		= "/usr/local/bin/indent_json";
my $INVOICES_DIR	= "$cpi_vars::BASEDIR/invoices";
my $DISTUSER_TO_PDF	= "$cpi_vars::BASEDIR/bin/distuser_to_pdf";
my $INDENTATION		= " ";
my $ALLOW_RESET_WINDOW	= 1;
my @DECODE_ORDER	= ( "when", "lat", "lng" );
my $STANDARD_DATE_FMT	= "%04d-%02d-%02d";
our $GLOBAL_TIME_FMT	= "%04d-%02d-%02dT%02d:%02d:%02d.000Z";
my $WKHTMLTOPDF		= "/usr/local/bin/wkhtmltopdf";

my $COSTSDIR		= $cpi_vars::BASEDIR."/costs";

my $EXIT_FILE		= $cpi_vars::BASEDIR."/exit_reason.txt";
my $FORM_URL		= "$BASES_URL/forms";
my $FORM_DIR		= "/var/www/routing$cpi_vars::OFFSET/forms";
    
# This used to decode FORM{progress} everytime the driver's
# browser updated, but since users only rarely track the
# driver, we simply leave the compacted json string in the
# file and uncompress/decode it only when somebody reads it.

my %ARGS =		# Right now, no way to change these default values.
    (
    "r"			=>	"mapquest",
    "l"			=>	"/var/www/routing$cpi_vars::OFFSET/routes"
    );

my %PHONE_HANDLERS =
    (
    "(Regular Email)"			=> "",

    "ATT"				=> "mms.att.net",
    "mms.att.net"			=> \&generate_email,
    "txt.att.net"			=> \&generate_text,

    "T-Mobile"				=> "tmomail.net",
    "tmomail.net"			=> \&generate_email,

    "Verizon"				=> "vzwpix.com",
    "vzwpix.com"			=> \&generate_email,
    "vtext.com"				=> \&generate_text,

    "Xfinity"				=> "mypixmessages.com",
    "mypixmessages.com"			=> \&generate_email,

    "Red Pocket"			=> "vtext.com",
    "vtext.com"				=> \&generate_text,

    "Page Plus"				=> "vtext.com",
    "vtext.com"				=> \&generate_text,

    "Sprint"				=> "pm.sprint.com",
    "pm.sprint.com"			=> \&generate_email,
    "messaging.sprintpcs.com"		=> \&generate_text,

    "Virgin Mobile"			=> "vmpix.com",
    "vmpix.com"				=> \&generate_email,
    "vmobl.com"				=> \&generate_text,

    "Tracfone"				=> "mmst5.tracfone.com",
    "mmst5.tracfone.com"		=> \&generate_email,

    "Simple Mobile"			=> "smtext.com",
    "smtext.com"			=> \&generate_text,

    "Mint Mobile"			=> "mailmyombile.net",
    "mailmymobile.net"			=> \&generate_text,

    "Metro PCS"				=> "mymetropcs.com",
    "mymetropcs.com"			=> \&generate_email,

    "Boost Mobile"			=> "myboostmobile.com",
    "myboostmobile.com"			=> \&generate_email,
    "sms.myboostmobile.com"		=> \&generate_text,

    "Cricket"				=> "mms.cricketwireless.net",
    "mms.cricketwireless.net"		=> \&generate_email,
    "sms.cricketwireless.net"		=> \&generate_text,

    "Republic Wireless"			=> "text.republicwireless.com",
    "text.republicwireless.com"		=> \&generate_text,

    "Google FI"				=> "msg.fi.google.com",
    "msg.fi.google.com"			=> \&generate_email,

    "US Cellular"			=> "mms.uscc.net",
    "mms.uscc.net"			=> \&generate_email,
    "email.uscc.net"			=> \&generate_text,

    "Ting"				=> "message.ting.com",
    "message.ting.com"			=> \&generate_text,

    "Consumer Cellular"			=> "mailmyobile.net",
    "mailmymobile.net"			=> \&generate_text,

    "C-Spire"				=> "cspire1.com",
    "cspire1.com"			=> \&generate_text
    );

my %DEFAULT_HEADER =
    (
    "from"	=> "$PROJLONG route update <$PROJECT\@$cpi_vars::DOMAIN>",
    "to0"	=> "dalward\@seniorsplus.org",
    "to1"	=> "treed\@spectrumgenerations.org",
    "to2"	=> "erowe\@spectrumgenerations.org",
    "to"	=> "chris.interim\@gmail.com",
    #"to"	=> "dufflerpud\@yahoo.com",
    "subject"	=> "$PROJLONG route update"
    );

sub BLACK_ON { return "color:black;background-color:$_[0] !important;border:1px solid $_[0];"; }

our %STATUS_STYLES =
    (
    "Untouched"	=> &BLACK_ON("white"),
    "Unvisited"	=> &BLACK_ON("#ffffd0"),
    "Skipped"	=> &BLACK_ON("#d0e8ff"),
    "Problems"	=> &BLACK_ON("#ffd0d0"),
    "Issues"	=> &BLACK_ON("#ffff00"),
    "Normal"	=> &BLACK_ON("#d0ffd0")
    );
$cpi_vars::SENDMAIL		= "/usr/lib/sendmail";

my @DAY_NAMES = ("Sun","Mon","Tue","Wed","Thu","Fri","Sat");

my $LOCAL_INPUT		= 0;	# For debugging purposes.
my $LOCAL_OUTPUT	= 0;

our $AGENT		= $ENV{HTTP_USER_AGENT};
our @LEGAL_LABELS	= ("A".."Z","0".."9","a".."z");

my $HEADER_SPACE	= "- ";
my @TABLE_NAMES		= ( "Distributor", "Staff", "Route", "Patron" );
my %TABLE_FIELDS =
    (
    Distributor =>
	{
	fields 	=>
	    [ {	Name		=> "Name",
		Required	=> 1,
		Searchable	=> 1,
		handler		=> \&Field_Text,
		typearg		=> "Distributor",
		example		=> "Livermore Meals on Wheels",
		header		=> "Distributor name" },
	      {	Name		=> "Address",
		Required	=> 1,
		Searchable	=> 1,
		handler		=> \&Field_Text },
	      {	Name		=> "Phone",
		Searchable	=> 1,
		handler		=> \&Field_Text },
	      {	Name		=> "Contact",
		#Required	=> 1,
		Searchable	=> 1,
		handler		=> \&Field_SelectFromDb,
		db		=> "Staff",
		count		=> 3 },
	      {	Name		=> "Bags",
		typearg		=> "Bags",
		handler		=> \&Field_Text },
#	      For now, this stuff is known only by the driver and not kept on
#	      a distributor-by-distributor basis.
	      {	Name		=> "Mapquest_key",
	      	header		=> "Mapquest developer key",
		typearg		=> "Mapquest_key",
		handler		=> \&Field_Text },
	      {	Name		=> "Reimbursement",
		typearg		=> "Reimbursement",
		header		=> "Reimbursement rates",
		Searchable	=> 1,
		handler		=> \&Field_Text } ]
	},
    Staff 	=>
	{
	fields 	=>
	    [ {	Name		=> "Name",
		Required	=> 1,
		Searchable	=> 1,
		handler		=> \&Field_Text,
		typearg		=> "Staff",
		example		=> "Jan Doe",
		onsearch	=> "Name,Route,Phone,Address",
		header		=> "Staffer name" },
	      {	Name		=> "Distributor",
		Required	=> 1,
		Searchable	=> 1,
		handler		=> \&Field_SelectFromDb,
		db		=> "Distributor" },
	      {	Name		=> "Status",
		Searchable	=> 1,
		handler		=> \&Field_SelectFromList },
	      {	Name		=> "Email",
		Required	=> 1,
		Searchable	=> 1,
		handler		=> \&Field_Text },
	      {	Name		=> "Phone",
		Searchable	=> 1,
		handler		=> \&Field_Text },
	      {	Name		=> "Notify",
		Searchable	=> 1,
		handler		=> \&Field_Notify },
	      {	Name		=> "Address",
		handler		=> \&Field_Text },
	      {	Name		=> "Donation_percentage",
	      	header		=> "Donation percentage (%)",
	      	handler		=> \&Field_Text },
	      {	Name		=> "Donation_maximum",
	      	header		=> "Donation maximum (\$)",
	      	handler		=> \&Field_Text },
	      {	Name		=> "User",
		header		=> ucfirst($PRETTY_PROG) . " user",
		anoninvisible	=> 1,
		handler		=> \&Field_Text },
	      {	Name		=> "Emergency_contact_0",
		header		=> "Emergency contact",
		handler		=> \&Field_Text },
	      {	Name		=> "Emergency_relationship_0",
		header		=> $HEADER_SPACE."Relationship",
		handler		=> \&Field_Text },
	      {	Name		=> "Emergency_phone_0",
		header		=> $HEADER_SPACE."Phone",
		handler		=> \&Field_Text },
	      {	Name		=> "Emergency_contact_1",
		header		=> "Emergency contact",
		handler		=> \&Field_Text },
	      {	Name		=> "Emergency_relationship_1",
		header		=> $HEADER_SPACE."Relationship",
		handler		=> \&Field_Text },
	      {	Name		=> "Emergency_phone_1",
		header		=> $HEADER_SPACE."Phone",
		handler		=> \&Field_Text },
	      {	Name		=> "Preferred_hospital",
		handler		=> \&Field_Text },
	      {	Name		=> "Maximum_patrons",
		handler		=> \&Field_Text },
	      {	Name		=> "Weight_limit",
		header		=> "Weight limit (kgs)",
		handler		=> \&Field_Text },
	      {	Name		=> "Times_available",
		handler		=> \&Field_Text } ]
	},
    Route 	=>
	{
	fields 	=>
	    [ {	Name		=> "Name",
		Required	=> 1,
		Searchable	=> 1,
		handler		=> \&Field_Text,
		typearg		=> "Route",
		example		=> "Wilton",
		header		=> "Route name" },
	      {	Name		=> "Distributor",
		Required	=> 1,
		Searchable	=> 1,
		handler		=> \&Field_SelectFromDb,
		db		=> "Distributor" },
	      {	Name		=> "Driver",
		Searchable	=> 1,
		handler		=> \&Field_SelectFromDb,
		db		=> "Staff",
		count		=> 3 },
	      {	Name		=> "Expires",
		handler		=> \&Field_Text },
	      {	Name		=> "Coordinator_note",
		header		=> "Coordinator's note",
		handler		=> \&Field_Textarea },
	      {	Name		=> "Driver_note",
		header		=> "Driver's note",
		handler		=> \&Field_Textarea },
	      {	Name		=> "Pickups",
		typearg		=> "Pickups",
		Searchable	=> 0,
		app_ro		=> 1,
		handler		=> \&Field_Textarea },
	      {	Name		=> "Source",
		Searchable	=> 1,
		handler		=> \&Field_SelectFromDb,
		db		=> "Route",
		count		=> 1 },
	      {	Name		=> "Route_starts_with",
		Searchable	=> 0,
		handler		=> \&Field_SelectFromDb,
		db		=> "Patron",
		app_ro		=> 1,
		count		=> 5 },
	      {	Name		=> "Route_ends_with",
		Searchable	=> 0,
		handler		=> \&Field_SelectFromDb,
		db		=> "Patron",
		app_ro		=> 1,
		count		=> 5 } ]
	},
    Patron 	=>
	{
	fields 	=>
	    [ {	Name		=> "Name",
		Required	=> 1,
		Searchable	=> 1,
		handler		=> \&Field_Text,
		typearg		=> "Patron",
		example		=> "John Doe",
		onsearch	=> "Name,Route,Phone,Address",
		header		=> "Patron name" },
	      {	Name		=> "Distributor",
		Required	=> 1,
		Searchable	=> 1,
		handler		=> \&Field_SelectFromDb,
		db		=> "Distributor" },
	      {	Name		=> "Route",
		Searchable	=> 1,
		handler		=> \&Field_SelectFromDb,
		anoninvisible	=> 1,
		db		=> "Route",
		count		=> 4 },
	      {	Name		=> "Email",
		handler		=> \&Field_Text },
	      {	Name		=> "Phone",
		Required	=> 1,
		Searchable	=> 1,
		handler		=> \&Field_Text },
	      {	Name		=> "Notify",
		handler		=> \&Field_Notify },
	      {	Name		=> "Address",
		Required	=> 1,
		Searchable	=> 1,
		handler		=> \&Field_Text },
	      {	Name		=> "Coords",
		Searchable	=> 0,
		anoninvisible	=> 1,
		handler		=> \&Field_Text },
	      {	Name		=> "Status",
		Searchable	=> 1,
		handler		=> \&Field_SelectFromList },
	      {	Name		=> "Emergency_contact_0",
		header		=> "Emergency contact",
		handler		=> \&Field_Text },
	      {	Name		=> "Emergency_relationship_0",
		header		=> $HEADER_SPACE."Relationship",
		handler		=> \&Field_Text },
	      {	Name		=> "Emergency_phone_0",
		header		=> $HEADER_SPACE."Phone",
		handler		=> \&Field_Text },
	      {	Name		=> "FoodPrefs",
		Searchable	=> 1,
		header		=> "Preferences",
		handler		=> \&Field_SelectFromList,
		allownone	=> 1,
		count		=> 4 },
	      { Name		=> "Cats",
		handler		=> \&Field_SelectFromList },
	      { Name		=> "Dogs",
		handler		=> \&Field_SelectFromList },
	      {	Name		=> "Times_receiving",
		handler		=> \&Field_Text },
	      {	Name		=> "Coordinator_note",
	        header		=> "Coordinator's note",
		anoninvisible	=> 1,
		handler		=> \&Field_Textarea },
	      {	Name		=> "Assessor_note",
		header		=> "Assessor's note",
		handler		=> \&Field_Textarea },
	      {	Name		=> "Driver_note",
	        header		=> "Driver's note",
		anoninvisible	=> 1,
		handler		=> \&Field_Textarea },
	      {	Name		=> "Last_seen",
		Searchable	=> 1,
		app_ro		=> "1",
		anoninvisible	=> 1,
		handler		=> \&Field_Text },
	      {	Name		=> "Last_seen_by",
		Searchable	=> 1,
		app_ro		=> "1",
		anoninvisible	=> 1,
		header		=> $HEADER_SPACE."Last seen by",
		handler		=> \&Field_SelectFromDb,
		db		=> "Staff" },
	      {	Name		=> "Last_route",
		app_ro		=> "1",
		anoninvisible	=> 1,
		header		=> $HEADER_SPACE."Last route",
		handler		=> \&Field_SelectFromDb,
		db		=> "Route" },
	      {	Name		=> "Last_note",
		app_ro		=> "1",
		anoninvisible	=> 1,
		header		=> $HEADER_SPACE."Last note",
		handler		=> \&Field_Textarea },
	      {	Name		=> "Last_assessment",
		app_ro		=> "1",
		anoninvisible	=> 1,
		header		=> $HEADER_SPACE."Last assessment",
		handler		=> \&Field_Textarea } ]
	}
    );

my %TEXTARGS =
    (
    "User"		=> "size=10 title='User login name' placeholder=chris".
			    " pattern='^([A-Za-z0-9]){3,10}\$'",
    "Phone"		=> "size=13 placeholder='(202)555-1212'" .
			    " type=tel inputmode=tel" .
			    " title='Phone must be in format: (nnn)nnn-nnnn' " .
			    " pattern='^\\(\\d\\d\\d\\)\\d\\d\\d-\\d\\d\\d\\d\$'",
    "Emergency_phone_0"	=> "size=13 placeholder='(202)555-1212'" .
			    " type=tel inputmode=tel" .
			    " title='Phone must be in format: (nnn)nnn-nnnn' " .
			    " pattern='^\\(\\d\\d\\d\\)\\d\\d\\d-\\d\\d\\d\\d\$'",
    "Emergency_phone_1"	=> "size=13 placeholder='(202)555-1212'" .
			    " type=tel inputmode=tel" .
			    " title='Phone must be in format: (nnn)nnn-nnnn' " .
			    " pattern='^\\(\\d\\d\\d\\)\\d\\d\\d-\\d\\d\\d\\d\$'",
    "Email"		=> "size=13 placeholder='user\@domain.com'" .
			    " type=email inputmode=email" .
			    " title='Email must be in format: user\@domain' " .
			    " pattern='^.+\@.+\\..+\$'",
    "Address"		=> "size=40 pattern='^..........*\$'" .
			    " title='Address must have at least 10 characters'" .
			    " placeholder='123 Mulberry Street, Seuseville, MA 04002'",
    "Notify"		=> "placeholder='email\@domain.com or (nnn)nnn-nnnn'" .
			    " type=email inputmode=email" .	# This works because phones match
			    " title='Can only send text to phone number or e-mail an address'" .
			    " pattern='^((.+\@.+\\..+)|".
			    "(\\d\\d\\d\\d\\d\\d\\d\\d\\d\\d)|".
			    "(\\(\\d\\d\\d\\)\\d\\d\\d-\\d\\d\\d\\d))\$'",
    "Last_seen"		=> "size=16" .
			    " placeholder='2022-12-25 01:01'" .
			    " pattern=" .
			    "'^\\d\\d\\d\\d-\\d\\d-\\d\\d \\d\\d:\\d\\d'",
    "Coords"		=> "size=13 placeholder='45.232568,-70.534987'" .
			    " title='Coordinates must be in format: [-]nnn.nnnnnn,[-]nnn.nnnnnn' " .
			    " pattern='^[\\d\\-]\\d+\.\\d+,[\\d\\-]\\d+\.\\d+\$'",
    "Reimbursement"	=> "size=40 placeholder='Volunteer Car Driver=0.46'" .
			    " title='Reimbursement must be in format: type=n.nn,type=n.nn,type=nn...' " .
			    " pattern='^([^=]+=\\d+\\.\\d\\d)(,[^=]+=\\d+\\.\\d\\d)*\$'",
    "Mapquest_key"	=> "size=34 placeholder='34 random letters and digits'" .
			    " title='Key used for Mapquest billing purposes' " .
			    " pattern='^[a-zA-Z0-9]+\$'",
    "Maximum_patrons"	=> "size=4 placeholder='nn'" .
			    " title='Number of patrons driver can handle.'" .
			    " pattern='^[1-9]\\d*\$'",
    "Weight_limit"	=> "size=4 placeholder='nn'" .
			    " title='Maximum pounds patrons a driver can left.'" .
			    " pattern='^[1-9]\\d*\$'",
    "Expires"		=> "size=10 placeholder='yyyy-mm-dd'" .
    			    " title='Last day route will be selectable'" .
			    " pattern='^(20[23456789]\\d-[01]\\d-[0123]\\d|today|tomorrow)\$'",
    "Donation_percentage"=> "size=3 placeholder='nnn' pattern='^\\d\\d*\$'",
    "Donation_maximum"	=>  "size=4 placeholder='nnnn' pattern='^\\d\\d*\$'"
    );

my %TEXTAREAARGS =
    (
    "Driver_note"	=> "rows=10 cols=40",
    "Assessor_note"	=> "rows=10 cols=40",
    "Coordinator_note"	=> "rows=10 cols=40",
    "Pickups"		=> "rows=10 cols=40",
    "Last_note"		=> "rows=10 cols=40",
    "Last_assessment"	=> "rows=10 cols=40"
    );

my %SELECT_FROM_LIST =
    (
    Cats =>
	[   { name=>"",			style=>&BLACK_ON("")		},
	    { name=>"1 cat",		style=>&BLACK_ON("#ffff30")	},
	    { name=>"2 cats",		style=>&BLACK_ON("#ffff30")	},
	    { name=>"3 cats",		style=>&BLACK_ON("#ffff30")	},
	    { name=>"4 cats",		style=>&BLACK_ON("#ffff30")	},
	    { name=>"5 cats",		style=>&BLACK_ON("#ffff30")	} ],
    Dogs =>
	[   { name=>"",			style=>&BLACK_ON("")		},
	    { name=>"1 dog",		style=>&BLACK_ON("#30ffff")	},
	    { name=>"2 dogs",		style=>&BLACK_ON("#30ffff")	},
	    { name=>"3 dogs",		style=>&BLACK_ON("#30ffff")	},
	    { name=>"4 dogs",		style=>&BLACK_ON("#30ffff")	},
	    { name=>"5 dogs",		style=>&BLACK_ON("#30ffff")	} ],
    Status =>
	[   { name=>"Pending",		style=>&BLACK_ON("#ffffff")	},
	    { name=>"Active",		style=>&BLACK_ON("#c0ffc0")	},
	    { name=>"Suspended",	style=>&BLACK_ON("#ffc0c0")	},
	    { name=>"Hospital",		style=>&BLACK_ON("#c0c0ff")	},
	    { name=>"Deceased",		style=>&BLACK_ON("#8090a0")	},
	    { name=>"Unknown",		style=>&BLACK_ON("#ffffc0")	} ], 
    FoodPrefs =>
	[
	    { name=>"7 pack",		style=>&BLACK_ON("#a0c0ff")	},
	    { name=>"CSFP box",		style=>&BLACK_ON("#c0c0ff")	},
	    { name=>"No frozen bag",	style=>&BLACK_ON("#ffb0b0")	},
	    { name=>"No beverage bag",	style=>&BLACK_ON("#ffb0b0")	},
	    { name=>"Special meal",	style=>&BLACK_ON("#ffb0b0")	},
	    { name=>"Mask required",	style=>&BLACK_ON("#ff0000")	},
	    { name=>"ENAP",		style=>&BLACK_ON("#80ffff")	}
	    ]
    );

my %OTHER_STYLES=
    (	"Provisioning"	=>&BLACK_ON("#c0ffc0"),
	"New patron"	=>&BLACK_ON("#d0ffff") );

my $DEFAULT_MAPPER = 'Google';
my $DEFAULT_ROUTER = "Mapquest";

my %SELECT_FROM_LIST_HASH;
foreach my $f0 ( keys %SELECT_FROM_LIST )
    {
    foreach my $pp ( @{$SELECT_FROM_LIST{$f0}} )
	{
	grep($SELECT_FROM_LIST_HASH{$f0}{$pp->{name}}{$_}=$pp->{$_}, keys %{$pp});
	}
    }

my $DEFAULT_WINDOW_SEARCH_MAX = 40;

#########################################################################
#	Variable declarations.						#
#########################################################################
our $base;
our $form_top;
my $here = "";			# Got to start somewhere!
my %mail_header;		# Fields to setup before invoking sendmail
our %mappers;			# Variables from different types of output maps

# Beware there are both global and local versions of these variables
our $current_route;		#
my $current_staff;		#
our $current_distributor;	# Used by mappers (to get keys)
our $total_distance;		#
our $total_time;		#

my %route;			#
our %stop;			# Indexed by following and then a unique index:
				#  address, coords, distance_to,
				#  name_string, note, time_to,
				#  total_distance_to, total_time_to, pickups;
our @rt_coords;			# Array of {lat=>,lng=>} for expected route

my $allow_reset_window		= $ALLOW_RESET_WINDOW;
our $now			= time();

my %porting;			# Used for sucking in & writing databases of other formats

print STDERR "--- "
	. &time_string("%04d-%02d-%02d %02d:%02d:%02d",$now)
	. " pid=$$ ---\n";
#print STDERR join("\n    ","Form:",
#	map { "$_=[$cpi_vars::FORM{$_}]" } sort keys %cpi_vars::FORM ), "\n"
#	if( %cpi_vars::FORM );

#########################################################################
#	Used by the common administrative functions.			#
#########################################################################
sub footer
    {
    my( $mode ) = @_;

    $mode = "admin" if( !defined($mode) );

    my @toprint = (<<EOF );
<script>
function footerfunc( func0 )
    {
    with( window.document.footerform )
	{
	func.value = func0;
	submit();
	}
    }
</script>
<form name=footerform method=post>
<input type=hidden name=func>
<input type=hidden name=SID value="$cpi_vars::SID">
<input type=hidden name=USER value="$cpi_vars::USER">
<center class='no-print'><table $cpi_vars::TABLE_TAGS border=1>
<tr><th><table $cpi_vars::TABLE_TAGS><tr><th
EOF
    push( @toprint,
	"><input type=button help='index' onClick='show_help(\"index.cgi\");' value='XL(Help)'" );
    foreach my $button (
	( map {"${_}:XL(".&plural($_).")"} @TABLE_NAMES ) )
        {
	my( $butdest, $buttext ) = split(/:/,$button);
	push( @toprint, "><input type=button onClick='footerfunc(\"Search,$butdest,\");'",
	    " help='search_$butdest'",
	    ( ($butdest eq $mode) ? " style='background-color:#50a0c0'" : "" ),
	    " value=\"$buttext\"\n" );
	}
    push( @toprint, ">",
	&logout_select(
	    ($mode eq "admin" ? "form" : "footerform"),
	    "footerfunc"
	    ),<<EOF);
	</th></tr>
	</table></th></tr></table></center></form></div>
EOF
    &xprint( @toprint );
    }

#########################################################################
#	Return true if we need a CGI header (almost always true).	#
#########################################################################
sub check_if_app_needs_header
    {
    #return 1;
    #my $res = ($cpi_vars::FORM{func}!~/(stickers|vcf|html|log|invoices|local)/);
    my $res = ($cpi_vars::FORM{func}!~/with_custom_header/);
    #print "check_if_app_needs_header($cpi_vars::FORM{func}) = ",($res||0),".\n";
    return $res;
    }

#########################################################################
#	Display the HTML file for the route, substituting as required.	#
#########################################################################
sub show_route
    {
    my $fname = $cpi_vars::URL;
    $fname = $cpi_vars::URL;	# Get rid of only seen once error above
    $fname =~ s+/[^/]*$+/$cpi_vars::FORM{arg}.html+;
    &xprint( &template( $fname, "%%USER%%", $cpi_vars::USER ) );
    &cleanup( 0 );
    }

#########################################################################
#	Someday we may be indexed.  For now, just do a linear search.	#
#########################################################################
sub findkeys
    {
    my( $tbl, $fld, $val ) = @_;
    my @inds = &DBget($tbl);
    my @rets = grep( (&DBget($_,$fld)||"") eq $val, @inds );
    return ( wantarray ? @rets : @rets ? $rets[0] : undef );
    }

#########################################################################
#	Didn't want to encode anything interesting in the URL so let's	#
#	grab it from the database.					#
#########################################################################
sub authenticate
    {
    &fatal("Incorrectly formatted URL.")
        if( ! $cpi_vars::FORM{auth} || $cpi_vars::FORM{auth} !~ /(.*):(.*)/ );
    my( $secret_type, $secret_value ) = ( $1, $2 );
    my $auth_string = &DBget( "A_$secret_type" );
    my( $compare, $stored ) = ( $auth_string =~ /^(.*?):(.*)/ ? ($1,$2) : ("","") );
    #print "auth=$cpi_vars::FORM{auth} st=$secret_type sv=$secret_value cv=$compare.<br>\n";
    &fatal("URL has incorrect or old authenticator."
	. "  Get a new QR code from your coordinator.",0)
	if( !$compare || $compare ne $secret_value );
    foreach my $pc ( split(/&/,$stored) )
	{
	$cpi_vars::FORM{$1}=$2 if( $pc=~/^(.*?)=(.*)$/ );
	}
    }

#########################################################################
#	Create an auth token.						#
#########################################################################
sub create_auth
    {
    my( @args ) = @_;
    if( ! $cpi_vars::FORM{auth} )
	{
	my @to_store_pieces;
	while( my $arg = shift(@args) )
	    {
	    push( @to_store_pieces, "$arg=".shift(@args) );
	    }
	my $to_store = join("&",@to_store_pieces);
	my $secret_type = &hashof( $to_store );
	my $secret_cookie = &secret_id();
	#print "CREATING NEW AUTH for [$secret_type]:  $secret_cookie.<br>\n";
	&DBwrite();
	&DBput( "A_$secret_type", $secret_cookie . ":" . $to_store );
	&DBpop();
	$cpi_vars::FORM{auth} = "${secret_type}:${secret_cookie}";
	}
    return $cpi_vars::FORM{auth};
    }

#########################################################################
#	Map the user to entry in staff database.			#
#########################################################################
my $user_staffind;
sub user_to_staffind
    {
    return $user_staffind if( $user_staffind );

    foreach my $checkind ( &DBget("Staff") )
	{
	if( (&DBget($checkind,"User")||"") eq $cpi_vars::USER )
	    {
	    print STDERR "user_to_staffind() returns $checkind.\n";
	    return $user_staffind = $checkind;
	    }
	}

    &autopsy("Cannot find the user "
	. ($cpi_vars::USER||"UNDEF") . " in the staff database.");
    }

#########################################################################
#	Patrons should probably have Distributor as a field but	for now	#
#	figure it out from their route(s).				#
#########################################################################
sub patron_to_distributor
    {
    my( $patron_ind, $default_distributor ) = @_;

    my $need_update;
    my $ret = &DBget( $patron_ind, "Distributor" );
    if( ! $ret )
	{
	$need_update = 1;
	if( my $route_string = &DBget( $patron_ind, "Route" ) )
	    {
	    foreach my $route_ind ( split( /,/, $route_string ) )
		{
		last if( $ret = &DBget( $route_ind, "Distributor" ) )
		}
	    }
#	&autopsy(
#	    "None of patron ".&DBget($patron_ind,"Name")."'s routes"
#	    . " ($route_string) have a distributor.") if( ! $ret );
	}
    if( ! $ret )
        {
	my @parse_here = grep( /^Show,Distributor,D_/, split(/\//,$here) );
	$ret = $1
	    if( @parse_here && $parse_here[$#parse_here] =~ /^Show,Distributor,(D_\w+)/ );
	}
    $ret ||= $default_distributor;
    &autopsy(
        "Cannot determine distributor for ".
	(&DBget($patron_ind,"Name")||"UNDEF").", here=[$here].")
        if( ! $ret );
    if( $need_update )
        {
        &DBwrite();
	&DBput( $patron_ind, $ret );
	&DBpop();
	}
    return $ret;
    }

#########################################################################
#	Returns true if current user is a member of the contact team	#
#	of the supplied distributor.					#
#########################################################################
sub user_in_record_list
    {
    my( $ind, $fld ) = @_;

    return 1 if( $cpi_vars::USER eq "anonymous" );

    my $ret = 0;
    if( my $commalist = &DBget($ind,$fld) )
        { $ret = ( &inlist( &user_to_staffind(), split( /,/, $commalist ) ) ); }
    print STDERR "user_in_record_list( ",
        "ind=", ( $ind || "?" ),
	", fld=", ( $fld || "?" ),
	" )", " user_staffind=", ( $user_staffind || "?" ),
	" returns ", ( defined($ret) ? $ret : "?" ), ".\n";
    return $ret;
    }

#########################################################################
#	Return the type of a record if no check specified.		#
#	Otherwise only return 
#########################################################################
sub rec_type
    {
    my( $rec, $check ) = @_;
    return undef if( $rec !~ /^([SPDR])_/ );
    my $ret =
        {	S=>"Staff",
		P=>"Patron",
		D=>"Distributor",
		R=>"Route"	} -> { $1 };
    return $ret if( ! $check || $ret eq $check );
    return undef;
    }

#########################################################################
#	Stubs for permissions.						#
#									#
#	if( &i_can(__LINE__,"w","Distributor","D_3","Contact") ) {}	#
#########################################################################
sub i_can
    {
    my( $line_num, $prm, $tbl, $ind, $fld ) = @_;
    my $ret = 0;
    my $distributor_ind;

    # All hail the programmer.  Bow down before me ...
    if( &can_admin() )
        { $ret = 1; }
    elsif ( $tbl eq "Staff" && ! $ind )
        { $ret = 1; }
    elsif ( $tbl eq "Staff" && ! &DBget( $ind, "Distributor" ) )
        { $ret = 1; }
    else
	{
	$distributor_ind =
	    ( &rec_type($ind,"Distributor")
	    ? $ind
	    : &DBget( $ind, "Distributor" ) )
	    if( $ind );
	if( ! $distributor_ind )
	    {
	    $distributor_ind = $1 if( $here =~ m:.*Distributor,([^,/]+).*?$: );
	    }
	if( &user_in_record_list( $distributor_ind, "Contact" ) )
	    { $ret = 1; }
	elsif( $prm eq "r" )
	    {
	    my $route_ind = ( &DBget( $ind, "Route" ) || $ind );
	    $ret = 1 if( &user_in_record_list( $route_ind, "Driver" ) );
	    }
	}

#    print STDERR "$line_num i_can(",
#        " prm=", ( $prm || "?" ),
#	", tbl=", ( $tbl || "?" ),
#	", ind=", ( $ind || "?" ),
#	", fld=", ( $fld || "?" ),
#	" ) di=", ( $distributor_ind || "?" ),
#	" here=", $here,
#	" ret=", ( defined($ret) ? $ret : "?" ),
#	".\n";

    return $ret;
    }

#########################################################################
#	Return the fields associated with a particular table.		#
#########################################################################
sub fields_of
    {
    my( $tbl ) = @_;
    return @{$TABLE_FIELDS{$tbl}->{fields}};
    }

#########################################################################
#	Update a record if there is new information.			#
#########################################################################
sub update_record
    {
    my( $tbl, $ind ) = @_;
    &DBwrite();
    &DBadd( $tbl, $ind );
    print STDERR "update_record($tbl,$ind)\n";
    my @tbl_fields =
	map { $_->{Name}}
		grep( !($_->{app_ro}), &fields_of($tbl) );
    print STDERR map {"$ind.$_ = $cpi_vars::FORM{$_}<br>\n"} @tbl_fields;

    if( $cpi_vars::FORM{Expires} )
        {
	if( $cpi_vars::FORM{Expires} eq "today" )
	    { $cpi_vars::FORM{Expires} = &time_string("%04d-%02d-%02d"); }
	elsif( $cpi_vars::FORM{Expires} eq "tomorrow" )
	    {
	    $cpi_vars::FORM{Expires}
		= &time_string("%04d-%02d-%02d",time()+(60*60*24));
	    }
	$cpi_vars::FORM{Name} =~ s/ on \d\d\d\d-\d\d-\d\d$//;
	$cpi_vars::FORM{Name} .= " on $cpi_vars::FORM{Expires}";
	}
    foreach my $fld ( @tbl_fields )
	{
	my $v = $cpi_vars::FORM{$fld};
	if( ! defined($v) )
	    { $v=""; }
	else
	    { $v =~ s/BlAnK,*//g; }
	if( $fld eq "Reimbursement" )
	    {
	    my @pieces;
	    foreach my $p0 ( split(/,/,$v) )
		{
		push( @pieces, "$1=$2" )
		    if( $p0 =~ /^\s*(.*?)\s*=\s*(.*?)\s*$/ );
		}
	    $v = join(",",@pieces);
	    $v =~ s/ +/_/g;
	    }
        &DBput( $ind, $fld, $v );
        &DBput( "Last", $cpi_vars::USER, $fld, $v );
	}
    &DBput( $ind, "Distributor", $1 )
        if( $tbl eq "Patron" && ! &DBget( $ind, "Distributor" ) &&
	    $here =~ m:.*Distributor,(.*?)/.*?$: );
    &DBpop();
    }

#########################################################################
#	Include patrons from other routes on this one.			#
#########################################################################
sub include_patrons_from_routes
    {
    my( $tbl, $ind, @routes_to_include ) = @_;
    &DBwrite();
    #print "include_patrons_from_routes($tbl,$ind,",join(",",@routes_to_include),")<br>\n";
    foreach my $patron_ind ( grep( &i_can(__LINE__,"w","Patron",$_), &DBget("Patron") ) )
	{
	my %on_routes =
	    map { ($_,1) } split(/,/,&DBget($patron_ind,"Route"));
	#print "Looking at $patron_ind:  ",join(",",keys %on_routes),".<br>\n";
	if( grep( $on_routes{$_}, @routes_to_include ) )
	    {
	    $on_routes{$ind} = 1;
	    &DBput( $patron_ind, "Route", join(",",sort keys %on_routes) );
	    #print "Routes{$patron_ind}=",&DBget($patron_ind,"Route"),"<br>\n";
	    }
	}
    &DBpop();
    }

#########################################################################
#	Delete a record.						#
#########################################################################
sub delete_record
    {
    my( $tbl, $ind ) = @_;
    &DBwrite();
    &DBdel( $tbl, $ind );
    grep( &DBdelkey( $ind, $_->{Name} ), &fields_of($tbl) );
    if( $tbl eq "Route" )
	{
	foreach my $patron_ind ( &DBget("Patron") )
	    {
	    my @on_routes = split(/,/,&DBget($patron_ind,"Route"));
	    if( @on_routes && $on_routes[0] )
		{
		my @new_routes = grep( $_ ne $ind, @on_routes );
		&DBput( $patron_ind, "Route", join(",",@new_routes) )
		    if( scalar(@new_routes) != scalar(@on_routes) );
		}
	    }
	}
    &DBpop();
    }

#########################################################################
#	Create a unique key, but leave some clues as to what type of	#
#	table it goes to.						#
#########################################################################
sub new_tagged_key
    {
    my( $tbl ) = @_;
    my $ret = substr($tbl,0,1) . "_" . &DBnewkey();
    #&xprint( "Creating new $tbl key:  $ret<br>\n" );
    my $checkname = &DBget($ret,"Name");
    &autopsy(
	"new_tagged_key($tbl) created $ret which already exists ($checkname)")
	if( $checkname );
    return $ret;
    }

#########################################################################
#	Return a pretty message if specified.				#
#########################################################################
sub pretty_message
    {
    my( $msg ) = @_;
    return "" if( ! $msg );
    return "<table frame=box cellspacing=0 cellpadding=2><tr><th bgcolor=#ffd0d0>$msg</th></tr></table>";
    }

#########################################################################
#	Return a string representing selecting from input.		#
#########################################################################
sub select_list
    {
    my(	$fp, $varval, @values ) = @_;

    my $fieldname	= $fp->{Name};
    #print STDERR "select_list($fieldname,",($varval||"UNDEF"),",[",join(",",@values),"])\n";
    my $fieldhdr	= "XL(".( $fp->{header} || &filename_to_text($fieldname )).")";
    my $allownone	= $fp->{allownone} ;
    my $count		= ( $fp->{count} || 1 );

    my $nvalues		= scalar(@values) / 3;
    my $sep		= "";
    my @curvals		= split(/,/,$varval);

    my @toprint;
    my %flags;

    my $varname		= $fieldname;
    my $onchange	= "";

    if( $fieldname =~ /otify/ )
	{
	$varname = "${fieldname}_select";
	$onchange = " onChange='change_carrier(this,window.document.${FORMNAME}.${fieldname});'";
	}

    if( $allownone )
        { grep( $flags{$_}=" checked", @curvals ); }
    else
	{
	my $showvalues	= ($nvalues > 9 ? 10 : $nvalues+1);
	my $selectarg	= ($count>1?" multiple size=$showvalues":"");
	push( @toprint, "<select name=$varname$selectarg$onchange>\n",
	    "<option disabled=disabled value='BlAnK'>",
		"Select $fieldhdr</option>\n" );

        grep( $flags{$_}=" selected", @curvals );
	}

    while ( @values )
	{
	my $val		=	shift( @values );
	my $txt		=	shift( @values );
	my $style	= 	shift( @values );

	my $styleflag	=	( $style ? " style='$style'" : "");

	if( $allownone )
	    {
	    push( @toprint, $sep,
		"<nobr><label$styleflag>",
		"<input type=checkbox name='$varname' value='$val'$onchange",
		    ( $flags{$val} || "" ),
		    ">XL($txt)</label></nobr>" );
	    $sep = "&nbsp;&nbsp;&nbsp;\n";
	    }
	else
	    {
	    push( @toprint, 
	        "<option value='$val'$styleflag",
		    ( $flags{$val} || "" ),
		    ">XL($txt)</option>\n" );
	    }
	}
    push( @toprint, ( $allownone ? "\n" : "</select>\n" ) );
    return @toprint;
    }

#########################################################################
#########################################################################
sub dbsort
    {
    return sort { &DBget( $a, "Name" ) cmp &DBget($b,"Name") } @_;
    }

#########################################################################
#	Reduces wordiness of code:  Map an id in the database to its	#
#	associated filename by taking its name and changing FS hostile	#
#	characters to underscores.					#
#########################################################################
sub filename_of
    {
    my( $ind ) = @_;
    my $name_of_ind = &DBget($ind,"Name");
    &autopsy("Filename_of($ind) fails due to lack of name.")
        if( ! defined($name_of_ind) );
    return &text_to_filename( $name_of_ind );
    }

#########################################################################
#	Field is actually a pointer to another database.		#
#########################################################################
sub Field_SelectFromDb
    {
    my($mod,$tbl,$ind,$fp,$val,$lastval)	= @_;
    my @toprint;
    if( $mod eq "r" )
	{
	if( $val )
	    {
	    foreach my $sfdind ( split(/,/,$val) )
		{
		push( @toprint,
		    "<a href='javascript:submit_func(\"$here/Show,",
			$fp->{db}, ",$sfdind\");'>",
		    &filename_to_text( &DBget( $sfdind, "Name" ) || ""),
		    "</a><br>" );
		}
	    }
	}
    else
	{
	$val = $1
	    if( (!defined($val) || $val eq "")
	     && $fp->{db} eq "Distributor"
	     && $here =~ m:.*Distributor,(.*?)/.*?$: );
	push( @toprint,
	    &select_list(
		$fp,
		$val,
		( map { (
		    $_,
		    &filename_to_text(&DBget($_,"Name") || ""),
		    "" ) }
		    &dbsort( &ordered_list($fp->{db},&DBget($fp->{db})) ) ) ) );
	}
    return join("",@toprint);
    }

#########################################################################
#	Field is select from a static list.				#
#########################################################################
sub Field_SelectFromList
    {
    my($mod,$tbl,$ind,$fp,$val,$lastval)	= @_;
    my $typearg = ( $fp->{typearg} || $fp->{Name} );
    my @toprint;
    if( $mod eq "r" )
	{
	my @toprint0;
	if( $val )
	    {
	    foreach my $v ( split(/,/,$val) )
		{
		my $prettyv = &filename_to_text($v);
		my $style = $SELECT_FROM_LIST_HASH{$typearg}{$v}{style};
		push( @toprint0,
		    ( $style
		    ? "<span style='$style'>$prettyv</span>"
		    : $prettyv ) );
		}
	    push( @toprint, join("<br>",@toprint0) );
	    }
	}
    else
        {
	my $tfield		= ( $fp->{typearg} || $fp->{Name} );
	my @entries		= @{$SELECT_FROM_LIST{$tfield}};
	push( @toprint,
	    &select_list(
	        (
		$fp,
		$val,
		( map { (
		    $_->{name},
		    &filename_to_text($_->{name}),
		    $_->{style} ) } @entries )
		) ) );
	}
    return join("",@toprint);
    }

#########################################################################
#	Return URL to directions to the specified address.		#
#########################################################################
sub address_to_url
    {
    my( $addr ) = @_;
    return "http://maps.google.com/maps?q=$addr";
    }

#########################################################################
#	Return URL to call a phone number.				#
#########################################################################
sub phone_to_url
    {
    my( $phone ) = @_;
    my $clean = $phone;
    $clean =~ s/[^\d]//g;
    return "tel:$clean";
    }

#########################################################################
#	Field is a type=text.						#
#########################################################################
sub Field_Text
    {
    my($mod,$tbl,$ind,$fp,$val,$lastval)	= @_;
    my $fieldname		= $fp->{Name};
    my $typearg			= ( $fp->{typearg} || $fp->{Name} );
    my $required_flag		= ( $fp->{Required} ? "required" : "" );
    my @toprint;
    if( $mod eq "w" )
        {
	push( @toprint, "<input type=text $required_flag name=$fieldname id=$fieldname onChange='fixtext(this,\"$fieldname\",\"$lastval\");' ",
	    ($TEXTARGS{$typearg}||""),
	    ( ! $fp->{onsearch} ? "" :
		" autofill=off autocomplete=off oninput='show_matching(\"$tbl\",\"$fieldname\",this,\"".$fp->{onsearch}."\");'" ),
	    " value='$val'>",
	    "<span id=search_$fieldname></span>",
	    );
	}
    else
	{
	#&autopsy("$fieldname is null") if( ! defined($val) );
	$val = "" if( ! defined($val) );
        my $html_safe_val	= &safe_html($val);
	if( $TABLE_FIELDS{$typearg} )
	    {
	    push( @toprint,
		"<a href='javascript:submit_func(\"$here/Show,$tbl,$ind\");'>", 
		$html_safe_val,
		"</a>" );
	    }
	elsif( $typearg eq "Email" )
	    { push( @toprint, "<a href=mailto:$html_safe_val>$val</a>" ); }
	elsif( &inlist($typearg,"Phone","Emergency_phone_0","Emergency_phone_1") )
	    {
	    my $phonelinknum = $val;
	    $phonelinknum =~ s/[^\d]//g;
	    push( @toprint, "<a href=tel:$phonelinknum>$html_safe_val</a>" );
	    }
	elsif( $typearg eq "Address" )
	    {
	    # See https://gearside.com/easily-link-to-locations-and-directions-using-the-new-google-maps/
	    push( @toprint, "<a target=routemap href='",
	        &address_to_url($val),"'>" );
	    if( $val =~ /^(.*),\s*([^,]+),\s*([A-Z][A-Z]),\s*(.*?)$/gms )
		{
		my( $pretown, $town, $state, $poststate ) = ( $1, $2, $3, $4 );
		$pretown =~ s/,/<br>/gms;
		push( @toprint, "<nobr>$pretown<br>$town,$state,$poststate</nobr>" );
		}
	    elsif( $val =~ /^(.*),\s*([^,]+),\s*([A-Z][A-Z])\s*$/gms )
		{
		my( $pretown, $town, $state ) = ( $1, $2, $3 );
		$pretown =~ s/,/<br>/gms;
		push( @toprint, "<nobr>$pretown<br>$town,$state</nobr>" );
		}
	    else
	        { push( @toprint, $val ); }
	    push( @toprint, "</a>" );
	    }
#	This stuff is now gotten through tables of maps.  I hope.
#	elsif( $typearg eq "!Map" )
#	    {
#	    my ( $driver_ind, $route_date ) = split(/,/,$val);
#	    push( @toprint,
#		"<a target='${PROG}_map' href='$GOOGLE_KML?",
#		    join(",",
#		        &text_to_filename(&DBget($ind,"Distributor")),
#			&filename_of($ind),
#			&filename_of($driver_ind),
#			$route_date), "'>",
#		&DBget( $driver_ind, "Name" ), " on $route_date",
#		"</a>", "<br> arf arf arf<br>",
#		"<a target='${PROG}_map' href='$PROG_URL?watch=$ind,$val'>",
#		    &DBget( $driver_ind, "Name" ), " on $route_date",
#		"</a>" );
#	    }
#	elsif( $typearg eq "Map" )
#	    {
#	    my($route_filename) = &filename_of($ind);
#	    my $distributor_filename = &filename_of( &DBget($ind,"Distributor") );
#
#	    my $last_date = 0;
#	    my $last_driver_filename;
#	    my $dirname0 = "$PROGRESS_DIR/$distributor_filename";
#	    if( opendir(D0,$dirname0) )
#		{
#		foreach my $driver_filename ( grep( /^[A-Z].*/, readdir(D0) ) )
#		    {
#		    my $dirname1 = "$dirname0/$driver_filename";
#		    if( opendir(D1,$dirname1) )
#			{
#			foreach my $progress_filename ( readdir(D1) )
#			    {
#			    if( $progress_filename =~
#				/^(\d\d\d\d-\d\d-\d\d)-$route_filename.kml$/ )
#				{
#				next if( $1 le $last_date );
#				$last_date = $1;
#				$last_driver_filename = $driver_filename;
#				}
#			    }
#			closedir(D1);
#			}
#		    }
#		closedir(D0);
#		}
#
#	    if( $last_driver_filename )
#		{
#		my $driver_name = $last_driver_filename;
#		$driver_name =~ s/_/ /g;
#		push( @toprint,
#		    "<a target='${PROG}_map' href='$GOOGLE_KML?",
#			join(",",
#			    $distributor_filename,
#			    $route_filename,
#			    $last_driver_filename,
#			    $last_date), "'>",
#		    "$driver_name on $last_date",
#		    "</a><br>",
#		    "<a target='${PROG}_map' href='$PROG_URL?watch=",
#			join(",",
#			    $distributor_filename,
#			    $route_filename,
#			    $last_driver_filename,
#			    $last_date), "'>",
#		    "$driver_name on $last_date",
#		    "</a>" );
#		}
#	    }
	else
	    {
	    push( @toprint, $val );	# Dunno what else to do with it.
	    }
	}
    return join("",@toprint);
    }

#########################################################################
#	Field is a type=text.						#
#########################################################################
sub Field_Textarea
    {
    my($mod,$tbl,$ind,$fp,$val,$lastval)	= @_;
    my $fieldname		= $fp->{Name};
    my $typearg			= ( $fp->{typearg} || $fp->{Name} );
    my @toprint;
    if( $mod eq "w" )
        {
	push( @toprint, "<textarea name=$fieldname id=$fieldname ",
	    "onChange='fixtext(this,\"$fieldname\",",
	    #"\"$lastval\");' ",	# Quoting would cause problems
	    "\"\");' ",			# Shouldn't repeat a note anyways
	    ($TEXTAREAARGS{$typearg}||""), ">", $val, "</textarea>" );
	}
    else
    	{
        my $html_safe_val	= &safe_html($val);
	if( $fieldname eq "Last_note" )
	    {
	    if( 0 && ! $html_safe_val )
	        { push(@toprint,"None"); }
	    else
	        {
		push( @toprint,
		    "<a href='javascript:submit_func(\"$here/log_with_custom_header,$tbl,$ind\");'>", ( $html_safe_val || "List" ), "</a>" );
		}
	    }
	elsif( $fieldname eq "Last_assessment" )
	    {
	    push( @toprint, &get_assessment_list($tbl,$ind) );
	    }
	elsif( $fieldname eq "Pickups" )
	    { push( @toprint, &pickups_table( $val ) ); }
	else
	    {
	    push( @toprint, $html_safe_val );	# Dunno what else to do with it.
	    }
	}
    return join("",@toprint);
    }

#########################################################################
#	Field is a type Notify.						#
#########################################################################
sub Field_Notify
    {
    my($mod,$tbl,$ind,$fp,$val,$lastval)	= @_;
    my $fieldname		= $fp->{Name};
    my $typearg			= ( $fp->{typearg} || $fp->{Name} );
    my @toprint;

    if( $mod eq "r" )
        { push( @toprint, "<a href=mailto:$val>$val</a>" ); }
    elsif( 1 )
	{	# Needs to be two form variables, won't work.
	my $dom = ( $val =~ /^(.*)@(.*)$/ ? $2 : "" );
	push( @toprint,
	    "<input type=text name=$fieldname onChange='fixtext(this,\"$fieldname\",\"$lastval\");'",
		($TEXTARGS{$typearg}||""),
		" value='$val'>\n",
	    &select_list(
		$fp,
		$dom,
		( map { (
		    $PHONE_HANDLERS{$_},
		    $_,
		    ""
		    ) }
		    sort grep( ref( $PHONE_HANDLERS{$_} ) ne "CODE",
		        keys %PHONE_HANDLERS ) )
		)
	    );

	}
    else
        {
	push( @toprint,
	    "<input type=text name=$fieldname id=$fieldname onChange='fixtext(this,\"$fieldname\",\"$lastval\");'",
		($TEXTARGS{$typearg}||""),
		" value='$val'>" );

	my $dom = ( $val =~ /^(.*)@(.*)$/ ? $2 : "" );
	my @carrier_names =
	    sort grep( ref( $PHONE_HANDLERS{$_} ) ne "CODE",
		keys %PHONE_HANDLERS );
	push( @toprint,
	    "\n<select name=${fieldname}_carrier",
		" onChange='change_carrier(this,document.getElementById(\"$fieldname\"));'>\n",
	    "<option disabled=disabled value='BlAnK'>Select carrier</option>\n",
	    "<option value=Email",
		( $PHONE_HANDLERS{$dom} ? "" : " selected" ),
		">XL(Email)</option>\n");
	foreach my $carrier ( @carrier_names )
	    {
	    push( @toprint,
		"<option value='$PHONE_HANDLERS{$carrier}'",
		    ( $dom eq $PHONE_HANDLERS{$carrier} ? " selected" : "" ),
		    ">", $carrier, "</option>\n" );
	    }
	push( @toprint, "</select>\n" );
	}
    return @toprint;
    }

#########################################################################
#	Produce field dependent HTML code for input and output.		#
#########################################################################
sub Field_Dispatch
    {
    my($mod,$tbl,$ind,$fp,$val)	= @_;
    
    my $lastval = (&DBget("Last",$cpi_vars::USER,$fp->{Name}) || "");
     
    return
        #(( $mod eq "r" && (!defined($val)||($val eq "")) )
        (( $mod eq "X" && (!defined($val)||($val eq "")) )
	? ""
	: &{$fp->{handler}}( $mod, $tbl, $ind, $fp, $val, $lastval )
	);
    }

#########################################################################
#	Turns a list of database IDs into a list of names.		#
#########################################################################
sub list_to_names
    {
    my( $ind, $fld ) = @_;
    my @ret;
    foreach my $pt ( split(/,\s*/,&DBget($ind,$fld)) )
	{
	if( $pt =~ /^\s*$/ )
	    { }
	elsif( $pt !~ /^[A-Z]_.*/ )
	    { push( @ret, $pt ); }
	else
	    { push( @ret, &DBget($pt,"Name") ); }
	}
    return @ret;
    }

#########################################################################
#	Generate a select list for importing either Dist or Route	#
#########################################################################
sub import_list_select
    {
    my ( $tblname, $ind ) = @_;
    %porting = &get_drivers( $PORTING_DIR ) if( ! %porting );
    return join("",
	"<select help='file_import' onchange='import_select_arg0=\"$here/import_patrons,$tblname,$ind,\"+this.value;this.selectedIndex=0;(document.getElementById(\"file_import_id\")).click();'>",
	    "<option disabled selected>XL(Import patrons)</option>\n",
	    "<option value=psf>XL(Pipe separated fields)</option>",
	    ( map {"<option value=$_>$porting{$_}{name}</option>\n"}
		grep( $porting{$_}{exporter}, keys %porting)
	    ),
	"</select>");
    #return "import_list_select($distind,".($routeind||"UNDEF").")";
    }

#########################################################################
#	Generate a select list for exporting either Dist or Route	#
#########################################################################
sub export_list_select
    {
    my ( $tblname, $ind ) = @_;
    %porting = &get_drivers( $PORTING_DIR ) if( ! %porting );
    return join("",
	"<select help='file_export' onchange='submit_func(\"$here/export_with_custom_header,$tblname,$ind,\"+this.value);this.selectedIndex=0;'>",
	    "<option disabled selected>XL(Export patrons)</option>\n",
	    "<option value=psf>XL(Pipe separated fields to file)</option>",
	    ( map {"<option value=$_>$porting{$_}{name}</option>\n"}
		grep( $porting{$_}{exporter}, keys %porting)
	    ),
	    "<option value=pdf>XL(PDF)</option>",
	    "<option value=html>XL(HTML)</option>",
	"</select>");
    #return "export_list_select($distind,".($routeind||"UNDEF").")";
    }

#########################################################################
#	Display a record allowing the user to change it.		#
#########################################################################
sub show_record
    {
    my( %args ) = @_;
    $args{ind} = "" if( ! defined($args{ind}) );
    print STDERR "show tbl=$args{tbl} ind=",($args{ind}||"UNDEF"),".<br>\n";
    my @fields = &fields_of( $args{tbl} );

    # my %defaults = map { (split(/=/,$_) ) } grep( $_, split(/;/,$args{defvals}) );
    my %defaults;
    %defaults = map { (split(/=/,$_) ) } grep( $_, split(/;/,$args{defvals}) )
	if( $args{defvals} );
    #print "defaults: ", join( ",", map { "$_=$defaults{$_}" } sort keys %defaults ), "<br>\n";

    $args{ind} = &new_tagged_key( $args{tbl} ) if( ! $args{ind} );

    my @toprint = ( $form_top, <<EOF );
<input type=hidden name=tbl value="$args{tbl}">
<input type=hidden name=ind value="$args{ind}">
EOF

    if( $cpi_vars::FORM{auth} || $args{anonmode} )
        {
	$cpi_vars::FORM{auth} =
	    &create_auth(
		"rectype", $args{tbl},
		"distind", $defaults{Distributor} )
	    if( ! $cpi_vars::FORM{auth} );
	push(@toprint,
	    "<input type=hidden name=auth value='$cpi_vars::FORM{auth}'>\n");
	}

    push( @toprint, &pretty_message( $args{msg} ) );

    if( $args{anonmode} )
	{
	my $live_url = join("&",
	    "$PROG_URL?func=anonymous_new_record",
	    "auth=$cpi_vars::FORM{auth}");
	my $live_qrcode = &cpi_qrcode_of::qrcode_of( $live_url, {encoding=>"image"} );
	push( @toprint, &template(
	    "$DISTRIBUTOR_DIR/".&filename_of($defaults{Distributor})."/$args{tbl}.html",
	    "%%LIVE_URL%%", $live_url,
	    "%%LIVE_QRCODE%%", $live_qrcode ) );
#	push( @toprint,
#	    "<center><span Qclass='only-print'><a href='$live_url'>",
#	    $live_url, "<br>",
#	    &cpi_qrcode_of::qrcode_of( $live_url, {encoding=>"image"} ),
#	    "</a></span></center>\n" );
	}

    push( @toprint,
	"<span id=record_screen_id>",
	"<table border=1 cellspacing=1 cellpadding=5 style='border-collapse:collapse;border:solid;'>\n" );
    my %could = ( update=>0, edit=>0 );
    my @search_fields;
    my @check_on_update;
    my $started_good = "";
    foreach my $fp ( @fields )
	{
	next if( $fp->{anoninvisible} && $args{anonmode} );

	my $fieldname = $fp->{Name};
	next if( ! &i_can(__LINE__,"r",$args{tbl},$args{ind},$fieldname) );

	my $val;
	if( $fieldname ne "Pickups" )
	    { $val = &DBget($args{ind},$fieldname); }
	else
	    {	# Obviously, this needs to be re-written.
		# How many pickups do we have per route?
	    foreach my $patron_ind ( &DBget($args{ind},$fieldname) )
		{
	        $val = &DBget($args{ind},$fieldname,$patron_ind);
	        last;
		}
	    }

	my $writeable = &i_can(__LINE__,"w", $args{tbl}, $args{ind}, $fieldname );
	my $show_ro = ( !$args{editmode} || !$writeable || $fp->{app_ro} );

	$val = $defaults{$fieldname}
	    if( ! $show_ro && (! defined($val) || $val eq "" ));
	$val = ( $args{anonmode} ? "Pending" : "Active" )
	    if( ! $val && $fieldname eq "Status" );
	push( @check_on_update, $fieldname ) if( $fp->{Required} );
	my $answer_needed = ( $fp->{Required} && ! $val );
	$started_good = " disabled" if( $answer_needed );
	push( @toprint,
	    "<tr help='field_$args{tbl}_$fieldname'>",
	    "<th id=",$fp->{Name},"_label_id valign=top align=left",
	    ( $answer_needed ? " style='color:red'" : "" ),
	    ">XL(",$fp->{header}||&filename_to_text($fp->{Name}), "):",
	    "</th><td>");

	if( $show_ro )
	    {
	    push(@toprint,&Field_Dispatch("r",$args{tbl},$args{ind},$fp,$val));
	    $could{edit} = 1 if( $writeable );
	    }
	else
	    {
	    push(@toprint,&Field_Dispatch("w",$args{tbl},$args{ind},$fp,$val));
	    $could{update} = 1;
	    }
	push( @toprint, "</td></tr>\n" );
	@search_fields = split(/,/,$fp->{onsearch}) if( $fp->{onsearch} );
	}

    push( @toprint,
	"<script>\n",
	"var CHECK_ON_UPDATE=[",join(",",(map{"'$_'"}@check_on_update)),"]\n",
	"</script>\n" );

    if( $args{anonmode} )
	{
	push( @toprint,
	    "<tr><th colspan=2 class='no-print'>",
	    "<input type=button help='button_anonymous_add_record' id='update_id' onClick='submit_func(\"anonymous_add_record,$args{tbl},$args{ind}\");' disabled value='XL(Done)'>\n",
	    "<input type=button help='button_anonymous_print' onClick='window.print();' value='XL(Print)'>",
	    "</th></tr></table>\n" );
	}
    else
        {
	if( @search_fields )
	    {
	    my @entries;
	    if( $here =~ m:(.*)/Add,$args{tbl},[^/]*$: )
		{
		my $before = $1;
		for my $sind ( grep( &i_can(__LINE__,"r",$args{tbl},$_,"Name"), &DBget($args{tbl}) ) )
		    {
		    my $lnk = "$before/Show,$args{tbl},$sind/Edit,$args{tbl},$sind";
		    my $txt = join(", ", map{&list_to_names($sind,$_)} @search_fields);
		    $txt =~ s:':\\':g;
		    push( @entries, "'$txt': '$lnk'" );
		    }
		}
	    push( @toprint, "<script>\nvar SEARCH_TABLE =\n    {\n\t",
		join(",\n\t",@entries),
		"\n    };\n</script>\n" );
	    }

    #my $staffinds = ( $args{Route} ? &DBget( $args{Route}, "Driver" ) : undef );
	my $staffinds;
	if( $args{tbl} eq "Patron" )
	    {
	    my $distind = &patron_to_distributor( $args{ind} );
	    $staffinds = join(",",
		grep( &staff_from_distributor($_,$distind), &DBget("Staff") ) );
	    }

	push( @toprint, "<tr><th colspan=2>",
	    ( $here !~ /\// ? ""
	    : "<input type=button help='button_larr' class='no-print' onClick='submit_func(\"$here/Back\");' value='&larr;'>\n" ),
	    "<input type=file help='file_Import' id=file_import_id name=file_contents onChange='submit_func(import_select_arg0);' style='display:none;'>\n",
	    ( $could{update} ? "<input type=button help='button_Update_record' id='update_id' onClick='submit_func(\"$here/Update,$args{tbl},$args{ind}\");' $started_good value='XL(Update)'>\n"
	    : $could{edit} ? "<input type=button help='button_Edit' onClick='submit_func(\"$here/Edit,$args{tbl},$args{ind}\");' value='XL(Edit)'>\n" : "" ),
	    ( &i_can(__LINE__,"w",$args{tbl}) ? "<input type=button help='button_Delete' onClick='confirm(\"Are you sure?\") && submit_func(\"$here/Delete\");' value='XL(Delete)'>\n" : "" ),
	    ( ($args{tbl} ne "Patron" && $args{tbl} ne "Staff") ? () :
		( "<input type=button help='button_Download_contact' onClick='submit_func(\"$here/vcf_with_custom_header,$args{tbl},$args{ind}\");' value='XL(Download contact)'>\n" ) ),
	    ( $args{tbl} ne "Patron" ? () :
		&routing_select( $args{tbl}, "assessment", "assessment", $staffinds ) ),
	    ( $args{tbl} ne "Staff" ? () :
		( "<input type=button help='button_Download_invoices' onClick='submit_func(\"$here/invoices_with_custom_header,$args{tbl},$args{ind}\");' value='XL(Download invoices)'>\n" ) ),
	    ( $args{tbl} ne "Distributor" ? () :
		( "<input type=button disabled help='button_Rebalance' onClick='submit_func(\"$here/rebalance_routes,$args{tbl},$args{ind}\");' value='XL(Rebalance routes)'>\n",
		&import_list_select( $args{tbl}, $args{ind} ),
		&export_list_select( $args{tbl}, $args{ind} ),
		"<select help='select_print_data' onchange='submit_func(\"$here/new_record_sheet,$args{tbl},$args{ind},\"+this.value);this.selectedIndex=0;'>",
		    "<option disabled selected>XL(Print)</option>\n",
		    "<option value=Staff>XL(Staff sheet)</option>\n",
		    "<option value=Patron>XL(Patron sheet)</option>\n",
		"<select>" ) ),
	    ( $args{tbl} ne "Route" ? () :
	    	( &import_list_select( $args{tbl}, $args{ind} ),
		&export_list_select( $args{tbl}, $args{ind} ) ) ),
	    ( $args{tbl} eq "Patron" ? () :
		( "<input type=button help='button_Route_runs' onClick='submit_func(\"$here/list_route_runs,$args{tbl},$args{ind}\");' value='XL(List route runs)'>\n" ) ),
	    "</th></tr>\n",
	    "</th></tr>\n",
	    "</table>" );

	my $search_table =
	    ( $args{tbl} eq "Distributor"	? "Route"
	    : $args{tbl} eq "Route"		? "Patron"
	    : undef );

	push( @toprint, &show_search(tbl=>$search_table,lvl=>1,defvals=>"$args{tbl}=$args{ind}",$args{tbl}=>$args{ind}) )
	    if( ! $args{editmode}
	     && $search_table && ($cpi_vars::FORM{"S_$args{tbl}"}=&DBget($args{ind},"Name")) );

	push( @toprint, "</span>\n" );

	if( !$args{editmode}
	    && $args{tbl} eq "Route"
	    && &i_can(__LINE__,"w",$args{tbl},$args{ind}) )
	    {
	    my @select_routes = grep(
		    ($_ ne $args{ind}
		    && &DBget( $_, "Name" ) ne "No route"
		    && &i_can(__LINE__, "Route", $_, "r" )),
		&DBget("Route") );
	    my $select_size = scalar(@select_routes);
	    $select_size=10 if( $select_size > 10 );

	    push( @toprint, <<EOF );
<table id=add_routes_id style='display:none'>
<tr><th><select name=add_routes multiple size=$select_size>
<option disabled=disabled selected value=BlAnK>
    XL(Select route to include)
</option>
EOF

	    push( @toprint,
		map {("<option value=$_>", &DBget($_,"Name"), "</option>\n")}
		    &dbsort( @select_routes ) );

	    push( @toprint, <<EOF );
</select></th></tr>
<tr><th>
    <input type=button value="XL(Include)" onClick='submit_func(\"$here/Include,$args{tbl},$args{ind}\");'>
    <input type=button value="XL(Cancel)" onClick='setdisplay("record_screen_id",1);setdisplay("add_routes_id",0);'",
</th></tr></table>
EOF
	    }
	}
    push( @toprint, "</center></form>\n" );
    &xprint( @toprint );
    &footer($args{tbl}) if( ! $args{anonmode} );
    &cleanup( 0 );
    }

#########################################################################
#	Probably a new driver.						#
#########################################################################
sub anonymous_new_record
    {
    my( $tbl, $distind, $new_tbl ) = @_;
    &show_record( tbl=>$new_tbl, ind=>"", editmode=>1, anonmode=>1,
        defvals=>"Distributor=$distind" );
    }

#########################################################################
#	Cache a http request for information in JSON format.		#
#	Return pointer to perl structure equivalent of that JSON.	#
#########################################################################
sub http_json
    {
    my( $base, $site, $contents ) = @_;
    #print STDERR "CMC http_json( $site ) with args [<br>", join(",<br>",@args), "]<br>\n";
    my $result = &cache(
	$contents
	? {
	query		=>"$cpi_vars::CACHEDIR/$base.q.json",
	result		=>"$cpi_vars::CACHEDIR/$base.r.json",
	check		=>":",
	http		=>$site,
	contents	=>$contents,
	method		=>"POST" }
	: {
	query		=>"$cpi_vars::CACHEDIR/$base.q.json",
	result		=>"$cpi_vars::CACHEDIR/$base.r.json",
	check		=>":",
	http		=>$site,
	method		=>"POST"
	} );
    #print STDERR "CMC returned [$result]<br>\n";
    #print "query in $cpi_vars::CACHEDIR/$base.q.json, results in $cpi_vars::CACHEDIR/$base.r.json .<br>\n";
    return ( $result ? decode_json( $result ) : undef );
    }

#########################################################################
#	Call named routine with maxitem sized chunks of @args.		#
#########################################################################
sub batch
    {
    my( $routine, $max_items, @args ) = @_;
    my $to_return=scalar(@args);	# Expecting one result per arg
    my @ret;				# So far no results to return

    my $num_got;
    for( my $from_index=0; $from_index < $to_return; $from_index += $num_got )
        {
	print "from_index=$from_index.<br>\n";
	my $to_get = min( $to_return - $from_index, $max_items );
	my @res = &{$routine}( @args[$from_index..($from_index+$to_get-1)] );
	$num_got = scalar(@res);
	&autopsy("Batch tried to get $to_get results and only got $num_got.")
	    if( scalar(@res) != $to_get );
	push( @ret, @res );
	print "to_return=$to_return to_get=$to_get num_got=$num_got.<br>\n";
	}
    $num_got = scalar(@ret);
    &autopsy("batch expecting $to_return but returning $num_got.")
        if( $to_return != $num_got );
    #exit(1);
    return @ret;
    }

#########################################################################
#	Batch geocoding requests to small manageable chunks.		#
#########################################################################
my $MAX_GEOCODE_SIZE = 50;	# Doc says this can be as high as 100
sub geocode
    {
    return &batch( \&geocode_batch, $MAX_GEOCODE_SIZE, @_ );
    }

#########################################################################
#	Update patrons' latitudes and longitudes, batching so that	#
#	Mapquest doesn't throw a giblet.				#
#########################################################################
my %patrons_needing_coords;
my %addr_to_coord;
sub geocode_ids
    {
    my( @ids ) = @_;
    my %writes;
    foreach my $patron_ind ( @ids )
	{
	my $addr = &DBget( $patron_ind, "Address" );
	my $coord = &DBget( $patron_ind, "Coords" );
	if( $coord )
	    { $addr_to_coord{$addr} = $coord; }
	else
	    { push( @{ $patrons_needing_coords{$addr} }, $patron_ind ); }
	}
    my @addresses_to_lookup;
    foreach my $addr ( keys %patrons_needing_coords )
	{
	if( ! $addr_to_coord{$addr} )
	    { push( @addresses_to_lookup, $addr ); }
	else
	    {
	    foreach my $patron_ind ( @{ $patrons_needing_coords{$addr} } )
		{ $writes{$patron_ind} = $addr_to_coord{$addr}; }
	    }
	}
    if( @addresses_to_lookup )
	{
	my @coords = &geocode( @addresses_to_lookup );
	foreach my $addr ( @addresses_to_lookup )
	    {
	    my $coord = shift(@coords);
	    foreach my $patron_ind ( @{ $patrons_needing_coords{$addr} } )
		{ $writes{$patron_ind} = $coord; }
	    }
	}
    return %writes;
    }

#########################################################################
#	Sort helper which sorts on basis of names of people at stop.	#
#########################################################################
sub mow_sort
    {
    my ( $a, $b ) = @_;
    #print STDERR "mow_sort($a=>$a,$b=>$b)\n";
    my $an = $stop{$a}{name_string};
    $an = ( $an =~/MOW [^\d]+ (\d[\dA-Za-z]*)/ ? $1 : $an );
    my $bn = $stop{$b}{name_string};
    $bn = ( $bn =~/MOW [^\d]+ (\d[\dA-Za-z]*)/ ? $1 : $bn );
    return ( $an cmp $bn );
    }

#########################################################################
#	Get list of stops prior to ordering.				#
#########################################################################
sub make_stop_list
    {
    my @sort0 = keys %stop;
    my $sst = ($route{beginpoint} || "");
    my $sen = ($route{endpoint} || "");
    my @sort1 =
        (
	( $sst ? $sst : () ),
	( sort { &mow_sort($a,$b) } grep($_ ne $sst && $_ ne $sen, @sort0) ),
	( $sen ? $sen : () )
	);
    return @sort1;
    }

#########################################################################
#	Return stops ordered by name but 1st key will be start of route	#
#	and last key will be end of route.				#
#########################################################################
sub optimize_order
    {
    my( @stoplist ) = @_;
    #print "reorder(",join(",",@stoplist),").<br>\n";
    if( $ARGS{r} =~ /mapquest/i )
        { return &order_query(@stoplist); }
    elsif( $ARGS{r} )
        { print STDERR "Do not know how to do a $ARGS{r} sort.\n"; }
    return @stoplist;
    }

#########################################################################
#	Handle the fields that produce indices into other records.	#
#########################################################################
sub indirect_get
    {
    my( $ind, $fp )	= @_;
    my $ret		= ( &DBget( $ind, $fp->{Name} ) || "" );

    if( $fp->{db} )
        {
        my @rets = grep( $_, split(/,/,$ret) );
        $ret = join(",",map { &DBget($_,"Name")||"" } @rets );
	}
    #print "indirect_get($ind,$fp->{Name}) returns [$ret]<br>\n";
    return $ret;
    }

#########################################################################
#	Figure out appropriate routing software and call it.		#
#	For right now, it's only Mapquest.				#
#########################################################################
sub geocode_batch
    {
    &setup_mappers_list();
    return &{ $mappers{$DEFAULT_ROUTER}{geocode_batch} }( @_ );
    }
sub costs_batch
    {
    &setup_mappers_list();
    return &{ $mappers{$DEFAULT_ROUTER}{costs_batch} }( @_ );
    }
sub order_query
    {
    &setup_mappers_list();
    print STDERR "DEFAULT_ROUTER=$DEFAULT_ROUTER, mappers=::", &Dumper(\%mappers), "::\nfq_drivers=::",
        &Dumper( \%cpi_drivers::fq_drivers ), "::\n";
    my @res = &{ $mappers{$DEFAULT_ROUTER}{order_query} }( @_ );
    return @res;
    }

#########################################################################
#	Turn a route into a URL to display it.				#
#########################################################################
sub route_to_url
    {
    my( $maptype, @rest ) = @_;
    &setup_mappers_list();
    return &{$mappers{$maptype}->{route_to_url}}( @rest );
    }

#########################################################################
#	Return <img> of qrcode of URL of route.				#
#########################################################################
sub coords_to_qrcode
    {
    my $url = &route_to_url( $DEFAULT_MAPPER, @_ );
    #return $url . "<br>" . &cpi_qrcode_of::qrcode_of( $url, {encoding=>"image"} );
    return
        "<span class='only-print'>"
      .	&cpi_qrcode_of::qrcode_of( $url, {encoding=>"image"} )
      .	"</span>";
    }

#########################################################################
#	Make the text appear clickable but assume we're already in	#
#	something that's clickable.					#
#########################################################################
sub fake_link
    {
    return "<a href='javascript:void(0);'>$_[0]</a>";
    }

#########################################################################
#	Return a reasonably efficient readable javascript string for	#
#	a field in a JSON record.					#
#########################################################################
sub jdata
    {
    my( $txtname, $txtdata ) = @_;
    $txtdata =~ s/[\r\n]//gs;		# Get rid of a hard problem
    $txtdata =~ s/'/\\'/gs;
    return $txtname . ":" .
	( !defined($txtdata) ? "''"
	: ( ($txtdata eq "0") || ($txtdata =~ /^[1-9]\d*$/) ) ? $txtdata
	: "'" . $txtdata . "'" );
    }

#########################################################################
#	Make a a pretty pickups table from the string.			#
#########################################################################
sub pickups_table
    {
    my ( $pickup_string ) = @_;
    my $need_header = 1;
    my @s = ();
    foreach my $line ( split(/\n/ms, $pickup_string) )
	{
	if( $line =~ /^\s*(.*?)\s*:\s*(.*?)\s*$/ )
	    {
	    my $route_name = $1;
	    my $item_line = $2;
	    my $need_line = 0;
	    my @row;
	    my @fields;
	    foreach my $per_item_type ( split(/\s*,\s*/,$item_line) )
		{
		if( $per_item_type =~ m:^\s*(.*?)\s+(\d+)/(\d+)$: )
		    {
		    my( $item_type, $rcvd, $expd ) = ( $1, $2, $3 );
		    $need_line += $rcvd;
		    $need_line += $expd;
		    push( @fields, "<th>$item_type</th>" );
		    push( @row,
			"<td align=right>",
			    ( $rcvd!=$expd
			    ? "<font color=red>$rcvd/$expd</font>"
			    : $rcvd ), "</td>" );
		    }
		}
	    if( $need_line )
	        {
		push( @s, "<center><table><tr><th>Bags for route</th>",
		    @fields, "</tr>" ) if( $need_header );
		$need_header = 0;
 		push( @s, "<tr><th align=left>", $route_name, "</th>",
		    @row, "</tr>\n" );
		}
	    }
	}
    push( @s, "</table></center>" ) if( ! $need_header );
    return join("",@s);
    }

#########################################################################
#	One entry (including header)					#
#########################################################################
my @jtable;
sub one_entry
    {
    my( $stopind, $patronslist, $trind, $ind, @coords_left ) = @_;

    push( @jtable,
	{
	"patrons"		=> $patronslist||"",
	"ind"			=> $ind||"",
	"type"			=> $stop{$stopind}{type}||"",
        "name"			=> $stop{$stopind}{name}||"",
        "phone"			=> $stop{$stopind}{phone}||"",
        "addrtxt"		=> $stop{$stopind}{addrtxt}||"",
        "address"		=> $stop{$stopind}{address}||"",
	"time_to"		=> $stop{$stopind}{time_to}||"",
	"distance_to"		=> $stop{$stopind}{distance_to}||"",
	"time_ref"		=> $stop{$stopind}{time_to}||"",
	"distance_ref"		=> $stop{$stopind}{distance_to}||"",
	"total_time_to"		=> $stop{$stopind}{total_time_to}||"",
	"total_distance_to"	=> $stop{$stopind}{total_distance_to}||"",
        "coords"		=> $stop{$stopind}{coords}||"",
	"prefs"			=> $stop{$stopind}{prefs}||"",
	"note"			=> $stop{$stopind}{note}||"",
	"pickups",		=> $stop{$stopind}{pickups}||""
	} );

    my $pretty_address =
	( ( $stop{$stopind}{address} =~ /^(.*?)\s*,(.*)$/ )
	? "$1<br>$2"
	: $stop{$stopind}{address} );
    my @toprint;
    #my $border_where = "border-bottom";
    my $border_where = "border-top";
    my $bgcolor = "white";	# "#d0f6ff";

    my $rows = 2 + ( $stop{$stopind}{note} ? 1 : 0 ) + ( $stop{$stopind}{pickups} ? 1 : 0 );
    push( @toprint,
	"<tr>",	"\n\t",
	"<th valign=top align=left bgcolor='$bgcolor' style='${border_where}:1px solid;' rowspan=$rows>",
	&coords_to_qrcode( undef, $coords_left[$#coords_left], @coords_left[0..$#coords_left-1] ), "</th>",
	"<th valign=top align=left bgcolor='$bgcolor' style='${border_where}:1px solid;Qwhite-space: nowrap;'>",
	$stop{$stopind}{name}, "</th>",
	"<th valign=top align=left bgcolor='$bgcolor' style='${border_where}:1px solid;Qwhite-space: nowrap;'>",
	    "<a href='callto:$stop{$stopind}{phone}'>$stop{$stopind}{phone}</a>",
	    ( $stop{$stopind}{preferences} ? "<br>".&prefs_to_html( $stop{$stopind}{preferences} ) : "" ),
"</th>",			"\n\t",
	"<td valign=top bgcolor='$bgcolor' style='${border_where}:1px solid' onClick='goto_map($trind);'>",
	    "<a target=map href=".
	        &route_to_url( $DEFAULT_MAPPER, undef, $coords_left[$#coords_left], @coords_left[0..$#coords_left-1] ),
	    &fake_link( $pretty_address ),
	    "</a></td>",
	"</tr><tr><td bgcolor='$bgcolor' colspan=4 align=right valign=bottom>",
	"<table bgcolor='$bgcolor' class='only-print'>",
	"<tr><th bgcolor='$bgcolor'>&#9634;</th><td bgcolor='$bgcolor'>Failed to deliver</td></tr>",
	"<tr><th bgcolor='$bgcolor'>&#9634;</th><td bgcolor='$bgcolor'>Needs to be called</td></tr></table>",
	"</td></tr>\n" );
    push( @toprint, "<tr><td bgcolor='$bgcolor' colspan=4>$stop{$stopind}{note}</td></tr>\n" )
	if( $stop{$stopind}{note} );
    push( @toprint, "<tr><td bgcolor='$bgcolor' colspan=4>",
	&pickups_table($stop{$stopind}{pickups}), "</td></tr>\n" )
	if( $stop{$stopind}{pickups} );
    return join("",@toprint);
    }

#########################################################################
#	Generate a quasi-difficult to guess id.  Could be much more	#
#	difficult.  No requirement for it to be unique.			#
#########################################################################
sub secret_id
    {
    return &cpi_compress_integer::compress_integer($now);
    }

#########################################################################
#	Make a stop from a database record.  Note that the record may	#
#	not necessarily be a patron.					#
#########################################################################
sub make_stop
    {
    my( $stop_name, $ind, $current_route ) = @_;
    $stop_name = $ind;
    if( ! $stop{$stop_name} )
	{
	push( @{$stop{$stop_name}{patrons}}, $ind );
	$stop{$stop_name}{address}	= &DBget($ind,"Address");
	$stop{$stop_name}{addrtxt} =
	    ( $stop{$stop_name}{address} =~ /(.*),US$/
	    ? $1 : $stop{$stop_name}{address} );
	$stop{$stop_name}{distributor}	= &DBget($ind,"?");
	$stop{$stop_name}{coords}	= &DBget($ind,"Coords");
	my $foodprefs = &DBget($ind,"FoodPrefs");
	my @prefs = ( $foodprefs ? split(/,/,$foodprefs) : () );
	push( @prefs, $_ ) if( $_ = &DBget($ind,"Dogs" ) );
	push( @prefs, $_ ) if( $_ = &DBget($ind,"Cats" ) );
	push( @prefs, "New patron" )
	    if( &rec_type($ind,"Patron") && ! &DBget($ind,"Last_seen") );
	$stop{$stop_name}{preferences}	= join(",",@prefs);
	$stop{$stop_name}{prefs} =
	    &safe_html(&prefs_to_html( $stop{$stop_name}{preferences}));
	$stop{$stop_name}{prefs} 	=~ s/'/&sbquo;/g;
	$stop{$stop_name}{note}		= &DBget($ind,"Driver_note");
	$stop{$stop_name}{pickups}	= &DBget($current_route,"Pickups",$ind);
	$stop{$stop_name}{pickups} =~ s:\d+/:0/:gms
	    if( $stop{$stop_name}{pickups} );	# Clear out last time
	$stop{$stop_name}{new_patron} =
	    ( &DBget($ind,"Last_seen") ? 0 : 1 );
	$stop{$stop_name}{type} =
	    ( &rec_type($ind,"Distributor")		? "Distributor"
	    : (&DBget($ind,"Name") eq "Hallowell" )	? "Pickup"
	    : "Patron" );
	push( @{$stop{$stop_name}{names}},
	    (&DBget($ind,"Name")||"").(&DBget($ind,"Phone")||"") );
	}
    }

#########################################################################
#	Make sure we have information on all the stops on a route.	#
#########################################################################
sub setup_stops
    {
    my ( $current_route, @patron_inds ) = @_;
    undef %stop;
    foreach my $patron_ind ( @patron_inds )
	{
	&make_stop( $patron_ind, $patron_ind, $current_route );
	}
    }

#########################################################################
#	Get route order for list of patrons.				#
#########################################################################
sub get_patron_order
    {
    my( $route_ind ) = @_;
    my %points;

    print STDERR __LINE__, ": get_patron_order($route_ind)\n";
    $current_route		= &DBget( $route_ind, "Name" );
    $current_staff		= &DBget( $route_ind, "Driver" );
    $current_distributor	= &DBget( $route_ind, "Distributor" );
    my @patrons			= &patrons_on( $route_ind );
    &setup_stops( $current_route, @patrons );

    foreach my $patron ( @patrons )
	{
	#my $stop_name = &DBget($patron,"Address");
	my $stop_name = $patron;
	&make_stop( $stop_name, $patron, $route_ind );
	push( @{ $route{way}}, $stop_name );
	}

    if( ! $points{beginend} )
        {
	my $stop_name = $current_distributor;
        &make_stop( $stop_name, $current_distributor, $route_ind );
	push( @{$points{distributor}}, $stop_name )
	}

    if( ! $points{beginend} )
        {
	# No endpoints or distributor points?  Used to make guess.
	&fatal( "No MOW Staff or MOW Staff specified.\n" .
	    	"You probably want to add one before proceeding.\n" )
	    if( ! $points{distributor} );

	$route{beginpoint} = $route{endpoint} = $points{distributor}[0];
	}
    elsif( scalar(@{$points{beginend}}) >= 2 )
	{
	$route{beginpoint}=$points{beginend}[0];
	$route{endpoint}=$points{beginend}[1];
	}
    elsif( ! $points{mow} )
	{ $route{beginpoint} = $route{endpoint} = $points{beginend}[0]; }
    else
	{
	$route{beginpoint}=$points{mow}[0];
	$route{endpoint}=$points{beginend}[0];
	}

    foreach my $stopind ( keys %stop )
	{
	my %last_name_to_names;
	my %last_name_to_phone;
	my @building;
	foreach my $name ( @{$stop{$stopind}{names}} )
	    {
	    if( $name =~ m/^(.*) (\w+) (\(.*\).*)$/ )
	        {
		push( @{ $last_name_to_names{$2} }, $1 );
		$last_name_to_phone{$2} = $3;
		}
	    elsif( $name =~ m/^(.*) (\w+)$/ )
	        {
		push( @{ $last_name_to_names{$2} }, $1 );
		$last_name_to_phone{$2} = "UNKNOWN";
		}
	    else
	        { push( @building, $name ); }
	    }
	foreach my $last_name ( sort keys %last_name_to_names )
	    {
	    push( @building,
		join(" & ", @{$last_name_to_names{$last_name}} ) .
		" " . $last_name .
		" " . $last_name_to_phone{$last_name} );
	    }
	$stop{$stopind}{name} = $stop{$stopind}{name_string} = join(", ",@building);
	if( $stop{$stopind}{name}
	    =~ /^(.*?)\s*(\(\d*?\)\s*[\d][\s\d\-]*)(.*)$/ )
	    {
	    $stop{$stopind}{phone} ||= $2;
	    $stop{$stopind}{name} =~ s/\s*\(\d+\)[\s\d\-]*//g;	# Remove any phone numbers
	    }
	}
    my @stoplist = &make_stop_list();

    if( !&DBget($route_ind,"Route_starts_with")
     && !&DBget($route_ind,"Route_ends_with") )
        { return &optimize_order(@stoplist); }
    else
    	{
	#my @ranges = &get_route_ranges( $_, $route_ind );
	my @ranges = &get_route_ranges( $route_ind );
	my $begin_optimize = pop( @{$ranges[0]} );
	my $end_optimize = shift( @{$ranges[2]} );
	return
	    (
	    @{$ranges[0]},
	    &optimize_order($begin_optimize,@{$ranges[1]},$end_optimize),
	    @{$ranges[2]}
	    );
	}
    }

#########################################################################
#	Return a list of routes to pickup				#
#########################################################################
sub route_to_routes_to_pickup
    {
    my( $current_route ) = @_;
    my @route_routes;

    #my $pickup_types = &DBget($current_route,"Pickup");
    #if( $pickup_types && $pickup_types =~ /\w/ )
	{
#	print "ROUTES=[", join(",",&DBget("Route")),"]<br>\n";
#	print "current=[",
#	    join(",",grep((&DBget($_,"Source")||"") eq $current_route,
#		&DBget("Route") ) ), "]<br>\n";
#	print "sorted=[",
#	    join(",",&dbsort( grep((&DBget($_,"Source")||"") eq $current_route,
#		&DBget("Route") ) ) ), "]<br>\n";
	foreach my $route_ind ( 
	    &dbsort( ( grep((&DBget($_,"Source")||"") eq $current_route,
		    &DBget("Route") ) ) ) )
	    {
	    push( @route_routes, &DBget($route_ind,"Name")||"" )
		if( $route_ind ne $current_route );
	    }
	}
    return encode_json( \@route_routes );
    }

#########################################################################
#	Traverses data looking min and max lattitude and longitude.	#
#########################################################################
sub bounds
    {
    #print STDERR "CMC Bounds called.\n";
    my( $input_p ) = @_;
    my @coords_list = @{$input_p->{progress_p}};
    my $first_p = shift( @coords_list );
    my %ret =
	(
	minlat	=> $first_p->{lat},
	maxlat	=> $first_p->{lat},
	minlng	=> $first_p->{lng},
	maxlng	=> $first_p->{lng}
	);
    foreach my $p ( @coords_list )
	{
	if(    $p->{lat} < $ret{minlat} ) { $ret{minlat} = $p->{lat}; }
	elsif( $p->{lat} > $ret{maxlat} ) { $ret{maxlat} = $p->{lat}; }
	if(    $p->{lng} < $ret{minlng} ) { $ret{minlng} = $p->{lng}; }
	elsif( $p->{lng} > $ret{maxlng} ) { $ret{maxlng} = $p->{lng}; }
	}
    print STDERR join(",",map{"$_=$ret{$_}"} keys %ret), ".\n";
    return \%ret;
    }

#########################################################################
#	Go read in all the mappers dependent files and see what mappers	#
#	are available for the specified function.			#
#########################################################################
sub setup_mappers_list
    {
    if( ! %mappers )
	{
	%mappers = &get_drivers( $MAPPER_DIR, "lib.pl" );
	foreach my $fmt ( keys %mappers )
	    {
	    my $mapperp			= $mappers{$fmt};
	    $mapperp->{lib}		||= $1;
	    $mapperp->{extension}	||= $fmt;
	    $mapperp->{destext}		||= $fmt;
	    $mapperp->{mime}		||= "application/fmt";
	    $mapperp->{tobrowser}	||= 0;
	    $mapperp->{template}	= $_
		if( -r ($_="$mapperp->{dir}/template") );
	    }
	}
    }

#########################################################################
#	Find me extensions in mappers that have desired property.	#
#########################################################################
sub mappers_list
    {
    my( $looking_for ) = @_;
    &setup_mappers_list();
    my @ret = sort grep( $mappers{$_}{$looking_for}, keys %mappers );
    return @ret;
    }

#########################################################################
#	Read in the color map file.					#
#########################################################################
my %COLORMAP;
sub read_colormap
    {
    my @lines = &read_lines( $COLOR_MAP_FILE );
    my ( @field_names ) = split(/\s+/,shift(@lines));
    while( $_ = shift(@lines) )
	{
	my @toks = split(/\s+/);
	my %rec = map { ($_, shift(@toks)) } @field_names;
	grep( $COLORMAP{ $rec{$_} } = \%rec, @field_names );
	}
    }

#########################################################################
#	Return an array of colors in the form given by $color_type	#
#########################################################################
sub colors_by
    {
    my( $color_type, @colors_to_map ) = @_;
    my @ret;
    &read_colormap if( ! %COLORMAP );
    if( @colors_to_map )
        { @ret = map { $COLORMAP{$_}{$color_type} } @colors_to_map; }
    else
	{
	for( my $ind=0; defined( $COLORMAP{$ind}{$color_type} ); $ind++ )
	    { push( @ret, $COLORMAP{$ind}{$color_type} ); }
	}
    return @ret;
    }

#########################################################################
#	Generate all of the expected route maps.			#
#########################################################################
sub all_expected
    {
    my( $route_ind, @reordered_stops ) = @_;
    my $distributor_ind		= &DBget( $route_ind, "Distributor" );
    my $distributor_name	= &DBget( $distributor_ind, "Name" );
    my $route_name		= &DBget( $route_ind, "Name" );
    my $title			= "Expected $route_name route";

    foreach my $fmt ( &mappers_list("expect") )
	{
	&{$mappers{$fmt}->{expect}}
	    (
	    $route_ind,
	    $distributor_ind,
	    $distributor_name,
	    $route_name,
	    $title,
	    @reordered_stops );
	}
    }

#########################################################################
#	Prune a list of stops to just the patrons (no distributor)	#
#########################################################################
sub stops_to_patrons
    {
    my @patrons = grep( &rec_type($_,"Patron"), @_ );
    &autopsy("Route has no patrons on it yet.") if( ! @patrons );
    return @patrons;
    }

#########################################################################
#	Process db to a html route sheet.				#
#########################################################################
sub contacts_to_html
    {
    my( $route_ind, $staffind, @ordered_stops ) = @_;

    &all_expected( $route_ind, @ordered_stops );

    #my $TITLE = $current_route . " route ($total_distance miles)";
    my $TITLE = $current_route . " route";

    my $trind = 0;
    my $ind = 'A';

    my $map_start;
    my $map_end;
    my @loc_list;

    my %pref_ctrs;
    my @others = ( "Dogs", "Cats" );
    print STDERR "ordered_stops=[",join("::",@ordered_stops),"]\n";
    foreach my $stopind ( &stops_to_patrons( @ordered_stops ) )
        {
	grep( $pref_ctrs{$_}++, split(/,/,(&DBget($stopind,"FoodPrefs")||"")) );
	foreach my $oth ( @others )
	    {
	    $pref_ctrs{$oth}+=$1 if((&DBget($stopind,$oth)||"") =~ /(\d+)/);
	    }
	$pref_ctrs{"New patron"}++ if( ! &DBget($stopind,"Last_seen") );
	$pref_ctrs{Provisioning}++;
	}

    my @columns = map { $_->{name} } @{$SELECT_FROM_LIST{FoodPrefs}};
    my %styles = map { ($_, $SELECT_FROM_LIST_HASH{FoodPrefs}{$_}{style}) } @columns;
    grep( $styles{$_} = $SELECT_FROM_LIST{$_}[1]{style}, @others );
    grep( $styles{$_} = $OTHER_STYLES{$_}, "New patron", "Provisioning" );
    @columns = ("Provisioning","New patron",@columns,@others);
    my $width = int( 100 / scalar( keys %pref_ctrs ) );

    my @id_big_screen = ( "<table border=0 cellspacing=0 cellpadding=2 width=100%>",
    	"<tr><th colspan=",scalar(@columns),">", &DBget($route_ind,"Driver_note"),"</th></tr>\n",
	"<tr>",
        (map { "<th align=center width=$width% style='$styles{$_}'>$_</th>" } grep( $pref_ctrs{$_}, @columns )),
	"</tr>\n<tr>",
        ( map { "<td align=center style='$styles{$_}'>$pref_ctrs{$_}</td>" } grep( $pref_ctrs{$_}, @columns )),
	"</tr>\n</table>" );

    push( @id_big_screen, "<table width=100% frame=box cellspacing=0 cellpadding=2>" );

    my @coords_to_end = map { $stop{$_}{coords} } @ordered_stops;

    foreach my $stopind ( @ordered_stops )
        {
	my $patron_ind = $stop{$stopind}{patrons}[0];
	push( @id_big_screen,
	    &one_entry(
		$stopind,
		join(",",@{$stop{$stopind}{patrons}}),
		$trind++, $ind++,
		@coords_to_end ) );
	#my $marker = "|flag-$trind";
	my $marker = "";
	if( $trind==1 )
	    { $map_start = $stop{$stopind}{coords} . $marker; }
	elsif( $trind > $#ordered_stops )
	    { $map_end = $stop{$stopind}{coords} . $marker; }
	else
	    { push( @loc_list, $stop{$stopind}{coords} . $marker ); }
	shift( @coords_to_end );
	}
    push( @id_big_screen, "</table>" );

    if( my @maptypes = &mappers_list( "route_to_url" ) )
	{
	push( @id_big_screen, "<center class='no-print'><table width=100%><tr>" );
	my $pct = int( 100 / scalar(@maptypes) );
	foreach my $maptype ( @maptypes )
	    {
	    push( @id_big_screen,
		"<th align=center width=$pct>",
		"<a target=${maptype}_interactive href='",
		&route_to_url( $maptype, $map_start, $map_end, @loc_list ),
		"'>$maptype map</a></th>" );
	    }
	push( @id_big_screen, "</tr></table></center>" );
	}

    my $route_pickup_list = &route_to_routes_to_pickup( $route_ind );

    my $dist = &DBget($route_ind,"Distributor");
    my $route_type_list = &DBget($dist,"Reimbursement");
    $route_type_list = "Unknown=$1" if($route_type_list=~/^(\d+\.\d\d)$/);
    $route_type_list =~ s/=[^,]*//g;
    $route_type_list = join(",",map {"'$_'"} split(/,/,$route_type_list));

    my $bag_types = ( &DBget($dist,"Bags") || "Bag" );

    $bag_types =
	join(", ",
	    map{ "'".&text_to_filename($_)."'" }
		split(/,/,$bag_types) );

    my $jtable_json = &encode_json( \@jtable );
    my $INIT = join("\n",
	"//{ INIT",
	"var ROUTE_LENGTH='$total_distance';",
        "var ROUTE_NAME=\"$current_route\";",
	"var SECRET='" . &secret_id() . "';",
	"var route_types = [$route_type_list];",
	"var stops = $jtable_json;",
	"var route_pickup_list = $route_pickup_list;",
	"var bag_types = [ $bag_types ];",
	"//} INIT" );

    my @jscripts =
        map { &{$mappers{$_}{js}}($dist) }
	    sort &mappers_list("js");
    my $template = &template( $TEMPLATES{html},
        "%%ROUTESJS%%", 	&read_file( "$SRC/routes.js" ),
	"%%MAPPERSJS%%",	join("",@jscripts) );

    if( $ARGS{l} )
        {
	while( 1 )
	    {
	    my @bpieces =
	        grep( defined($_),
		    split( m~(<script)([^>]*)src="([^:">]*)"([^>]*)>(.*?)</script>|(<link)([^>]*)href="([^:">]*)"([^>]*?)/*>~ims, $template)
		);
	    last if( scalar(@bpieces) <= 1 );

	    my @epieces = ();
	    my ( $tag, $preincsrc, $incsrc, $postincsrc, $tagbody );
	    while( my $pc = shift(@bpieces) )
		{
		undef $tag;
		if( $pc eq "<script" )
		    {
		    ( $tag, $preincsrc, $incsrc, $postincsrc, $tagbody ) =
			( "script", shift(@bpieces), "$ARGS{l}/".shift(@bpieces), shift(@bpieces), shift(@bpieces) );
		    }
		elsif( $pc eq "<link" )
		    {
		    ( $tag, $preincsrc, $incsrc, $postincsrc, $tagbody ) =
			( "style", shift(@bpieces), "$ARGS{l}/".shift(@bpieces), shift(@bpieces), "" );
		    }
		if( ! $tag )
		    { push( @epieces, $pc ); }
		else
		    {
		    open( INCSRC, $incsrc )
			|| &autopsy("Cannot read ${incsrc}:  $!");
		    my @incsrc_lines;
		    my $incsrc_ln;
		    my $incsrc_lno=0;
		    while( defined($incsrc_ln = <INCSRC>) )
			{
			if( 0 )
			    { $incsrc_ln =~ s+checkpoint\("(.*)"\);++; }
			else
			    {
			    my $str = sprintf("%s\@%04d",$incsrc,++$incsrc_lno);
			    $incsrc_ln =~ s+checkpoint\("(.*)"\);+</script><script>if(DEBUG.checkpointing.value) {alert("$1 $str");}</script><script>+;
			    }
			push( @incsrc_lines, $incsrc_ln );
			}
		    close( INCSRC );
		    my $inc_src_contents = join("",@incsrc_lines);

		    push( @epieces,
			"<$tag", $preincsrc, "incsrc='", $incsrc, "'",
			$postincsrc, ">\n",
			#&read_file( $incsrc ),
			$inc_src_contents,
			$tagbody, "\n",
			"</$tag>\n" );
		    }
		}
	    $template = join("",@epieces);
	    }
	}

    $_ = &DBget( $dist, "Reimbursement" );
    s/=[^,]*//g;
    my $route_type_buttons = join( "",
	map {
	    "<button class=medbut id=id_${_}_button " .
	    " onClick='set_route_type(\"$_\",1);'>" .
	    &filename_to_text($_) . "</button><br>\n"
	    } split(/,/) );

    $current_staff =
        ( $staffind			? $staffind
	: $current_staff =~ /^(.*?),.*/	? $1
	: $current_staff );
    my $current_distributor_name = &DBget($current_distributor,"Name");
    print STDERR "ind=$ind current_staff = $current_staff.  current_distributor=$current_distributor.\n";
    my $current_staff_name = &DBget($current_staff,"Name");
    my $secret = &secret_id();
    my $status_file = sprintf( "%s/%s-%s-%s-%s",
	&text_to_filename( $current_distributor_name ),
	&time_string($STANDARD_DATE_FMT,$now),
	&text_to_filename($current_route),
	&text_to_filename($current_staff_name),
	$secret
	);
	
    return &subst_list( &help_strings( &xlate( $template ) ),
	"%%SID%%",			"RT_".$secret,
	"%%USER%%",			"anonymous",
	"%%FORMNAME%%",			$FORMNAME,
	"%%HELP_IFRAME%%",		$cpi_vars::HELP_IFRAME,
	"%%INIT%%",			$INIT,
	"%%TITLE%%",			$TITLE,
	"%%ROUTE_TYPE_BUTTONS%%",	$route_type_buttons,
	"%%ROUTE_NAME%%",		$current_route,
	"%%STAFF%%",			$current_staff,
	"%%STAFF_NAME%%",		$current_staff_name,
	"%%DISTRIBUTOR%%",		$current_distributor,
	"%%DISTRIBUTOR_NAME%%",		$current_distributor_name,
	"%%STATUS_FILE%%",		$status_file,
	"%%BIG_TABLE%%",		join("",@id_big_screen),
	"%%COMPLETED_CGI%%",		$PROG_URL);
    }

#########################################################################
#	Staff member works for distributor.				#
#########################################################################
sub staff_from_distributor
    {
    my( $staff_ind, $dist_ind ) = @_;
    return &inlist($staff_ind,split(/,/,&DBget($dist_ind,"Contact")));
    }

#########################################################################
#	Returns true if patron is on this route.			#
#########################################################################
sub patron_from_route
    {
    my( $patron_ind, $route_ind ) = @_;
    return &inlist($route_ind,split(/,/,&DBget($patron_ind,"Route")));
    }

#########################################################################
#	Return a list of all the patrons on the specified route.	#
#########################################################################
sub patrons_on
    {
    my( $route_ind ) = @_;
    my @ret =
        grep( &DBget($_,"Status") eq "Active" && &patron_from_route($_,$route_ind),
	    &DBget("Patron") );
    print STDERR __LINE__, " patrons_on($route_ind) = [", join(",",@ret), "]\n";
    return @ret;
    }

#########################################################################
#	Return a list of ll the patrons belonging to a distributor.	#
#########################################################################
sub patrons_of_distributor
    {
    my( $distind ) = @_;
    my @ret =
        grep( &DBget($_,"Status") eq "Active" && &DBget($_,"Distributor") eq $distind,
	    &DBget("Patron") );
    return @ret;
    }

#########################################################################
#	Return the database index of something with the supplied name.	#
#	If not found and 3rd argument is undefined, have a fatal error.	#
#	If argument is not "", return that value.			#
#	If argument is "", add to the table.				#
#########################################################################
sub map_name_to_ind
    {
    my( $table, $name, $retval ) = @_;
    foreach my $ind ( &DBget($table) )	# Who doesn't like a nice linear search?
	{
	return $ind if( $ind eq $name || &DBget($ind,"Name") eq $name );
	}
    if( ! defined( $retval ) )
        {
	&autopsy("Cannot map ".($name||"UNDEF")
	    ." to an index in the $table table.");
	}
    if( $retval eq "" )
	{
	&DBadd( $table, $retval=&new_tagged_key( $table ) );
	&DBput( $retval, "Name", $name );
	}
    return $retval;
    }

#########################################################################
#	Do one route run from the command line.				#
#	Since route runs are customized to the person who drives the	#
#	run, that is now the second argument.				#
#	If no destination is specified, e-mail it to that person.	#
#	If that isn't set up, dump it to a file.			#
#########################################################################
sub do_one_route
    {
    my( $route_name, $staff_name, $dest ) = @_;

    &DBread();
    my $route_ind = &map_name_to_ind("Route",$route_name);
    my $staff_ind = &map_name_to_ind("Staff",$staff_name);

    $dest ||= &DBget( $staff_ind, "Notify" );
    $dest ||= "/tmp/$route_name.html";

    print STDERR "route_ind=$route_ind, ", &DBget($route_ind,"Name"), ".\n";
    my( $html_table ) =
	&contacts_to_html($route_ind,undef,&get_patron_order($route_ind));
    if( $dest !~ /\@/ )
	{
	print "Writing $route_name to $dest.\n";
	&write_file($dest,$html_table);
	}
    else
        {
	&cpi_send_file::sendmail(
	    $MAILSRC,
	    $dest,
	    "$route_name generated for $dest",
	    $html_table );
	}
    &cleanup(0);
    }

#########################################################################
#	Return a string in VCF format.					#
#########################################################################
sub rec_to_vcf
    {
    my( $ind ) = @_;
    my @ret;
    my( @firstlast )			= split(/\s+/,&DBget($ind,"Name"));
    my( $lastname )			= pop( @firstlast );
    my( $firstname )			= join(" ",@firstlast);
    my( $phone )			= &DBget($ind,"Phone");
    my( $address )			= &DBget($ind,"Address");
    my( $routeind )			= &DBget($ind,"Route");
    my( $route )			= &DBget($routeind,"Name");
    my( $emergency_contact_0 )		= &DBget($ind,"Emergency_contact_0");
    my( $emergency_relationship_0 )	= &DBget($ind,"Emergency_relationship_0");
    my( $emergency_phone_0 )		= &DBget($ind,"Emergency_phone_0");
    my( $emergency_contact_1 )		= &DBget($ind,"Emergency_contact_1");
    my( $emergency_relationship_1 )	= &DBget($ind,"Emergency_relationship_1");
    my( $emergency_phone_1 )		= &DBget($ind,"Emergency_phone_1");
    my( $preferred_hospital )		= &DBget($ind,"Preferred_hospital");

    $address =~ s/,/;/g;

    push( @ret, <<EOF );
BEGIN:VCARD
VERSION:3.0
PRODID:-//Apple Inc.//iPhone OS 15.3.1//EN
DBID:$ind
EOF

    push( @ret, <<EOF ) if( $firstname && $lastname );
N:$lastname;$firstname;;;
FN:$firstname $lastname
EOF

    push( @ret, <<EOF ) if( $route );
ORG:MOW $route
EOF

    push( @ret, <<EOF ) if( $phone );
TEL;type=CELL;type=VOICE;type=pref:$phone
EOF

    push( @ret, <<EOF ) if( $address );
item1.ADR;type=HOME;type=pref:;;$address
item1.X-ABADR:us
EOF

    push( @ret, <<EOF ) if( $preferred_hospital );
item2.X-ABLabel:Preferred hospital
item2.X-ABRELATEDNAMES:$preferred_hospital
EOF

    if( $emergency_contact_1 )
	{
	push( @ret, <<EOF );
item3.X-ABLabel:Emergency contact 0
item3.X-ABRELATEDNAMES:$emergency_contact_0 ($emergency_relationship_0)
item3.TEL;type=CELL;type=VOICE:$emergency_phone_0
item4.X-ABLabel:Emergency contact 1
item4.X-ABRELATEDNAMES:$emergency_contact_1 ($emergency_relationship_1)
item4.TEL;type=CELL;type=VOICE:$emergency_phone_1
EOF
	}
    elsif( $emergency_contact_0 )
	{
	push( @ret, <<EOF );
item3.X-ABLabel:Emergency contact
item3.X-ABRELATEDNAMES:$emergency_contact_0 ($emergency_relationship_0)
item3.TEL;type=CELL;type=VOICE:$emergency_phone_0
EOF
	}

    push( @ret, <<EOF );
END:VCARD

EOF
    return join("",@ret);
    }

#########################################################################
#	Return a string containing a VCF file of all the contacts.	#
#########################################################################
sub contacts_to_vcf
    {
    return join( "\n", map { &rec_to_vcf($_) } &stops_to_patrons(@_) );
    }

#########################################################################
#	Convert food preferences to nice HTML string.			#
#########################################################################
sub prefs_to_html
    {
    my( $prefstring ) = @_;
    my @ret;
    foreach my $pref ( split(/,/,$prefstring) )
	{
	push( @ret, "<span style='" .
	    (
	    $SELECT_FROM_LIST_HASH{FoodPrefs}{$pref}{style}	||
	    $SELECT_FROM_LIST_HASH{Dogs}{$pref}{style}		||
	    $SELECT_FROM_LIST_HASH{Cats}{$pref}{style}		||
	    $OTHER_STYLES{$pref}				||
	    ""
	    ) . "'>$pref</span>" );
	}
    my $retstring = join( ', ', @ret );
    print STDERR "prefs_to_html($prefstring) returns [$retstring]\n";
    return $retstring;
    }

#########################################################################
#	Return an html string useful for generating  sticker.		#
#	EXPERIMENTAL							#
#########################################################################
sub rec_to_sticker
    {
    my ( $stopind ) = @_;
    my @res;
    foreach my $ind ( @{$stop{$stopind}{patrons}} )
	{
	my( $firstlast )	= &DBget($ind,"Name");
	my( $phone )		= &DBget($ind,"Phone");
	my( $address )		= &DBget($ind,"Address");
	my( $routeind )		= &DBget($ind,"Route");
	my( $route )		= &DBget($routeind,"Name");
	my $prefstring		= &prefs_to_html( &DBget($ind,"FoodPrefs") );

        push( @res, <<EOF );
<tr><td>
<em>$firstlast</em><br>
$phone<br>
$address<br>
$prefstring
</td><td>
<em>$firstlast</em><br>
$phone<br>
$address<br>
$prefstring
</td></tr>
EOF
	}
    return @res;
    }

#########################################################################
#	Takes either an html file or html text, uses an external	#
#	utility to convert it to pdf.  Basically no error checking.	#
#########################################################################
sub html_to_pdf
    {
    my( $html_contents ) = @_;
    my $html_file;
    my @to_remove;
    if( $html_contents !~ /</ )		# Nobody will embed a < in a filename
        { $html_file = $html_contents; }
    else
	{
	$html_file = &tempfile(".html");
	&write_file( $html_file, $html_contents );
	}
    my $ret = &read_file(
	"$WKHTMLTOPDF --print-media-type $html_file - 2>/dev/null |" );
    }

#########################################################################
#	Return a string containing a stickers file of all the contacts.	#
#	EXPERIMENTAL							#
#########################################################################
sub contacts_to_stickers
    {
    return &html_to_pdf(
	join("\n",
	    "<html><head></head><body>",
	    "<table width=100% border=1 style='border-collapse:collapse'>",
	    "<tr><th width=50%><font size=+2>Food stickers</size></th>",
	    "<th width=50%><font size=+2>Beverage stickers</size></th></tr>",
	    ( map { &rec_to_sticker($_) } &stops_to_patrons(@_) ),
	    "</table></body></html>\n" ) );
    }

#########################################################################
#	Create a assessment form from a template.			#
#########################################################################
sub dump_assessment
    {
    my( $fnc, $tbl, $ind ) = @_;
    my $pass;
    my $contents = &read_file( "$cpi_vars::BASEDIR/lib/assessment.html" );

    my $staffind;
    my $distind;
    my $dest_type = "display";
    my $hashedval;

    if( $fnc &&
	$fnc =~ /(assessment)_(with_custom_header|with_normal_header|to_email)/)
        {
	$pass = "need_javascript";
	$dest_type = $2;
	$distind = &DBget($ind,"Distributor");
	$staffind = $1 if( $cpi_vars::FORM{func}=~/,,(S_.*?)$/ );
	}
    elsif( ($ENV{HTTP_REFERER}||"") =~ m:/(\w+),(\w+),(\w+),(\w+)\.html$: )
        {
	$pass = "use_form";
	$dest_type = "filled_out";
	$distind = $1;
	$ind = $2;
	$staffind = $3;
	$hashedval = $4;
	&DBread();
	}

#    print join("<br>\n",
#	"pass="		.($pass			||"UNDEF"),
#       "distind="	.($distind		||"UNDEF"),
#       "ind="		.($ind			||"UNDEF"),
#       "staffind="	.($staffind		||"UNDEF"),
#	"func="		.($cpi_vars::FORM{func}	||"UNDEF"),
#       "hashedval="	.($hashedval		||"UNDEF"),
#	"");

    my @pieces;
    foreach my $piece ( split(/(%%P_.+?%%|%%S_.+?%%)/,$contents) )
        {
	if( $piece !~ /%%(P|S)_(.+?)%%/ )
	    { push( @pieces, $piece ); }
	else
	    {
	    my $dbtype = $1;
	    my $field = $2;
	    my $val =
	        ( $dbtype eq "P"
	        ? &dbget( $cpi_vars::DB, $ind, $field )
		: $staffind
		? &dbget( $cpi_vars::DB, $staffind, $field )
		: "" );
	    if( ! defined($val) )
		{ print "$dbtype $field came back undefined with ind=$ind.<br>\n"; }
	    elsif( $val =~ /\d\d\d-\d\d\d\d/ )
	        {
		push( @pieces, "<a href='", &phone_to_url($val), "'>$val</a>" );
		}
	    elsif( $field =~ /ddress/ )
	        {
		push( @pieces,
		    "<a href='",&address_to_url($val),"'>",$val,"</a><br>",
		    &cpi_qrcode_of::qrcode_of(
		        &address_to_url( $val ),
			    {encoding=>"image"} ) );
		}
	    else
		{
		$val =~ s/\n/<br>/gms;
		push( @pieces, $val );
		}
	    }
	}
    my $js =
	( $pass eq "need_javascript"
	? &read_file( "$cpi_vars::BASEDIR/lib/notes.js" )
	: "" );
    $contents = &subst_list( join("",@pieces),
	"%%JAVASCRIPT%%", $js,
	"%%FORM_ACTION%%", $PROG_URL );
    if( 1 )
	{
	my @pieces;
	foreach my $piece ( split( m:(<input.*?>|<textarea.*?</textarea>|<select.*?>.*?</select>):ms, $contents ) )
	    {
	    if( $pass eq "need_javascript" )
	        {
		if( $piece !~ /^<input\b.*?type=note\b/
		 || $piece !~ /^<input\b.*?name=(\w+)/ )
		    { push( @pieces, $piece ); }
		else
		    {
		    push( @pieces,
			"<input type=hidden name='$1' id='${1}_id'>",
			"<div id='${1}_div'></div>" );
		    }
		}
	    else
		{
		if( $piece =~ /^<input\b.*?name=(\w+)/ )
		    {
		    my $varname = $1;
		    if( $piece =~ /^<input\b.*?type=hidden/ )
		        {}
		    elsif( $piece !~ /^<input\b.*?type=note/ )
		        { push( @pieces, "<b>",$cpi_vars::FORM{$varname}||"UNDEF","</b>" ); }
		    else
		    	{
			push( @pieces,
			    &note_to_html( $cpi_vars::FORM{$varname} ));
			}
		    }
		elsif( $piece =~ /^<textarea[^>]+name=(\w+)/ )
		    { push( @pieces, "<b>",$cpi_vars::FORM{$1}||"UNDEF","</b>" ); }
		elsif( $piece =~ /^<select[^>]+name=(\w+)/ )
		    { push( @pieces, "<b>",$cpi_vars::FORM{$1}||"UNDEF","</b>" ); }
		else
		    { push( @pieces, $piece ); }
		}
	    }
	$contents = join("",@pieces);
	@pieces = ();
	for( my $ind=0; defined($cpi_vars::FORM{"note_$ind"}); $ind++ )
	    {
	    my $formv = $cpi_vars::FORM{"note_$ind"};
	    if( $formv =~ /base64/ )
		{ push( @pieces, "<img src='$formv'><br>\n" ); }
	    else
		{ push( @pieces, "<pre>$formv</pre>\n" ); }
	    }
	my $debug_string = join("\n",
	    map {"<dd>$_=$cpi_vars::FORM{$_}</dd>"} keys %cpi_vars::FORM );
	$contents = &subst_list(
	    $contents,
	    "%%NOTES%%", join("",@pieces),
	    "%%DEBUG%%", $debug_string );
	}

    my $distributorname = &DBget($distind,"Name");
    my $patronname = &DBget( $ind, "Name" );

    my $distributorfilename = &text_to_filename($distributorname);
    my $filename;
    my $fullfilename;
    my $live_url_txt = "";
    my $live_qrcode_txt = "";
    if( $pass eq "need_javascript" )
        {
	$filename = "$distributorfilename/$distind,$ind,"
		. ( $staffind||"")
		. "," . &hashof($contents).".html";
        $fullfilename = $FORM_DIR."/".$filename;
	my $todo = " to fill out assent form for $patronname";
	my $live_url = join("/",$BASES_URL,"forms",$filename);
	$live_url_txt = join("",
	    "<div class=no-print>",
	    "<a href='$live_url'>Click</a> $todo",
	    "</div>");
	$live_qrcode_txt = join("",
	    "<div class=only-print>",
	    &cpi_qrcode_of::qrcode_of( $live_url, {encoding=>"image"} ),
	    "<br>$todo</div>");
	}
    else
        {
	my $patronfilename = &text_to_filename($patronname);
	$filename = join("/",$distributorfilename,$patronfilename,
	    &time_string("%04d-%02d-%02d.html") );
	$fullfilename = $ASSESSMENT_DIR."/".$filename;
	}
    &setup_file( $fullfilename,
        &subst_list(
	    $contents,
	    "%%LIVE_URL%%", "",
	    "%%LIVE_QRCODE%%", "" ) );
    $contents = &subst_list(
        $contents,
	"%%LIVE_URL%%", $live_url_txt,
	"%%LIVE_QRCODE%%", $live_qrcode_txt );
    $contents =~ s:<script.*</script>::ms;
    if( $dest_type eq "to_email" && $staffind )
        {
	my $notify = &DBget($staffind,"Notify");
	my $emailsrc = "$distributorname router <$MAILSRC>";
	&cpi_send_file::sendmail( $emailsrc, $notify,
	    "Assessment to fill out",
	    $contents );
	return "Form notification sent to $notify.";
	}
    elsif( $dest_type eq "filled_out" )
        {
	&xprint(
	    "<center>",
	    "<h1>XL(Form submitted, thank you!)</h1>",
	    "<h2>XL(Results are in: )", $fullfilename, "</center>");
	my $emailsrc = "$distributorname router <$MAILSRC>";
	&cpi_send_file::sendmail( $emailsrc, "dufflerpud\@yahoo.com",
	    "$patronname assessment completed by ".&DBget($staffind,"Name"),
	    &read_file( $fullfilename ) );
	&cleanup(0);
	}
    else
        {
	print "Content-type:  text/html\n\n",$contents;
	&cleanup(0);
	}
    }

#########################################################################
#	Dump the route in a useful format.				#
#########################################################################
sub dump_route
    {
    my( $fnc, $tbl, $ind ) = @_;
    my @indlist;
    my @toprint;
    my $route_ind;

    my $tind = $cpi_vars::FORM{ind};
    my $report_name = ( $tind ? &DBget($tind,"Name") : "People" );
    my $pretty_name = &filename_to_text( $report_name );
    my $filename = &text_to_filename( $report_name );

    print STDERR __LINE__, ": fnc=[",$fnc||"UNDEF","] tbl=[",$tbl||"UNDEF","] ind=[",$ind||"UNDEF","]\n";
    
#    print "Content-type:  text/html\n\n",
#	"fnc=[", ($fnc||"UNDEF"), "], tbl=[", ($tbl||"UNDEF"), "], ind=[", ($ind||"UNDEF"), "]<br>\n";
    print STDERR "Tbl=[$cpi_vars::FORM{tbl}] Route=[$cpi_vars::FORM{ind}] filename=[$filename]<br>\n";

    if( $cpi_vars::FORM{tbl} eq "Route" )
	{
	@indlist = &get_patron_order( $route_ind=$tind );
	#print "get_patron_order($route_ind) returned [",join(",",@indlist),"]<br>\n";
	}
    elsif( $tbl eq "Patron" )
	{
	@indlist = grep( &i_can(__LINE__,"r",$tbl,$_),
	    ( $tind ? $tind : &DBget($tbl) ) );
	$route_ind = &DBget( $indlist[0], "Route" );
	$route_ind =~ s/,.*//;
	}
    elsif( $tbl eq "Staff" )
	{
	@indlist = grep( &i_can(__LINE__,"r",$tbl,$_),
	    ( $tind ? $tind : &DBget($tbl) ) );
	$route_ind = undef;
	}

    $fnc =~ /(stickers|vcf|html)_(with_custom_header|with_normal_header|to_email)/;
    #print "fnc=[$fnc]<br>\n";
    my( $what, $mode ) = ( $1, $2 );
    print STDERR "what=[$what] and mode=[$mode].<br>\n";
    my %request =
	( $what eq "stickers"
	?  (	type	=> "pdf",
		mime	=> "application/pdf",
		subject	=> "$pretty_name stickers",
		data	=> &contacts_to_stickers(@indlist) )
	: $what eq "vcf"
	?  (	type	=> $what,
		mime	=> "text/vcard",
		subject	=> "$pretty_name contacts",
		data	=> &contacts_to_vcf(@indlist) )
	: $what eq "html"
	?  (	type	=> $what,
		mime	=> "text/html",
		subject	=> "$pretty_name route",
		data	=> &contacts_to_html($route_ind,$ind,@indlist) )
	: () );
    if( $mode eq "with_custom_header" )
	{
	my $mimetype = ( $request{type} eq "pdf" ? "application" : "text" ) . "/$request{type}";
	if( $request{type} eq "qhtml" )
#	    {	# Probably won't do what you want with so lets use postscript.
#	    print "Content-type:  application/pdf\n\n",
#	        &html_to_pdf( $request{data} );
#	    }
	    {
	    my $without_headers = $request{data};
	    $without_headers =~ s/.*<body.*?>//g;
	    print $form_top, $without_headers;
	    &footer( $tbl );
	    &cleanup(0);
	    }
	else
	    {
	    print join("\n",
		"Content-type:  $request{mime}",
		#"Content-disposition:  attachment; filename=\"$filename.$request{type}\"",
		"",
		$request{data} );
	    }
	&cleanup(0);	# Will not return to create footer etc.
	}
    else
	{	# to_email:  Sending e-mail.  Print status to browser.
	opendir(D,$DEST_HTTP) ||
	    &autopsy("Cannot opendir($DEST_HTTP):  $!");
	unlink(
	    map { "$DEST_HTTP/$_" }
		grep( /^$filename\..*\.$request{type}$/,
		    readdir(D) ) );
	closedir( D );
	my $secure_name = join(".",$filename,&secret_id(),$request{type});
	my $distributorind = &DBget( $tind, "Distributor" );
	my $distributorname = ( $distributorind ? &DBget($distributorind,"Name") : "Unknown" );
	my $distributorfilename = &text_to_filename($distributorname);
	my $local_dir = "$DEST_HTTP/$distributorfilename";

	if( ! -d $local_dir )
	    { system("mkdir -p $local_dir; chmod 755 $local_dir; ln -s ../common $local_dir/common; ln $local_dir/../index.cgi $local_dir/index.cgi"); }
	else
	    {
	    opendir(D,$local_dir) ||
		&autopsy("Cannot opendir($local_dir):  $!");
	    unlink(
		map { "$local_dir/$_" }
		    grep( /^$filename\..*\.$request{type}$/,
			readdir(D) ) );
	    closedir( D );
	    }

	my $live_url = join("/",$cpi_vars::URL,$distributorfilename,$secure_name);
	my $live_qrcode = &cpi_qrcode_of::qrcode_of( $live_url, {encoding=>"image"} );
	my $help_qrcode = &cpi_qrcode_of::qrcode_of( "$BASES_URL/help/Driver.cgi", {encoding=>"image"} );
	$request{data} =~ s/%%LIVE_JAVASCRIPT%%/onLoad='setup_page();'/gms;
	$request{data} =~ s/%%LIVE_URL%%/$live_url/gms;
	$request{data} =~ s/%%LIVE_QRCODE%%/$live_qrcode/gms;
	$request{data} =~ s/%%HELP_QRCODE%%/$help_qrcode/gms;
	my $local_file = &setup_file("$local_dir/$secure_name",$request{data});
	if( $mode eq "to_email" )
	    {
	    my $emailsrc = "$distributorname router <$MAILSRC>";
	    my $staffinds = &DBget( $tind, "Driver" );
	    foreach my $staffind ( split(/,/,$staffinds) )
		{
		next if( $staffind ne $ind );
		my $notify = &DBget( $staffind, "Notify" );
		if( $notify )
		    {
		    if( &inlist($what,"vcf") )	# VCF attachment works great
			{				# but HTML/javascript won't.
			&cpi_send_file::sendmail( $emailsrc, $notify, $request{subject},
			    $request{subject}, $local_file );
			unlink( $local_file );
			push( @toprint, "$request{subject} XL(sent to) $notify." );
			}
		    else				# We actually have to leave
			{				# file and send him a pointer
						    # to it.
			&cpi_send_file::sendmail( $emailsrc, $notify, $request{subject},
			    # "$request{subject} in $live_url",
			    &read_file($local_file),
			    $local_file );
			push(@toprint, "$request{subject}",
			    " XL(sent to) $notify",
			    "<br> XL(as pointer to) ",
			    "<a target=${filename}_route href='$live_url'>$live_url</a>");
			}
		    }
		}
	    }
	else
	    {
	    my $without_headers = $request{data};
	    $without_headers =~ s/.*<body.*?>//g;
	    print $form_top, $without_headers;
	    }
	}
    my $ret = join("",@toprint);
    return join("",@toprint) if( $mode ne "with_normal_header" );
    push( @toprint, <<EOF );
<center class='no-print'>
    <input type=button onClick='window.print();' value='XL(Print route sheet)'>
</center>
EOF
    &xprint( @toprint );
    &cleanup(0)
    }

#########################################################################
#	Dump a patron's log file as plain/text.				#
#########################################################################
sub dump_patron_log
    {
    my( $fnc, $tbl, $ind ) = @_;
    #print &CGIheader();
    print "Content-type:  text/html\n\n";
    &autopsy("Insufficient permissions to read log file.")
	if( ! &i_can(__LINE__,"r","Patron",$ind) );
    my $rind = &DBget($ind,"Route");
    $rind =~ s/,.*//;
    my $dind = &DBget($rind,"Distributor");

    my $driver_name = &DBget($ind,"Name");
    my $fname = &text_to_filename( $driver_name ) . ".log";
    my $dname = &text_to_filename( &DBget($dind,"Name") );

    my @entries;
    print "<center>";
    if( ! -r "$PATRON_DIR/$dname/$fname" )
        {
	print "<h1>No notes available.</h1>";
	}
    else
	{
	my $contents = &read_file("$PATRON_DIR/$dname/$fname");
	$contents =~ s/\n\t/qqqq/gms;
	my $last_ind = "";
	foreach my $line ( split(/\n/,$contents) )
	    {
	    #print "Seen $3 by Chris Caldwell on $2 route:\t$4\n";
	    if( $line =~ /^Seen (\d\d\d\d-\d\d-\d\d|\?) (\d\d:\d\d|\?) by (.*?) on (.*?) route:\s+(.*)/ms )
		{
		my $ind = "$1-$2-$3";
		my %entry =
		    (
		    ymd		=>	$1,
		    hourmin	=>	$2,
		    driver	=>	$3,
		    route	=>	$4
		    );
		my( $disposition, @comments ) = split(/qqqq/ms,$5);
		$entry{disposition} = $disposition;
		$entry{comments} = ( @comments ? join("<br>",@comments) : "" );
		if( $ind eq $last_ind )
		    { $entries[$#entries] = \%entry; }
		else
		    {
		    push( @entries, \%entry );
		    $last_ind = $ind;
		    }
		}
	    }

	print "Content-type:  text/html\n",
		#"Content-disposition:  attachment; filename=\"$fname\"\n",
		"\n<html><head></head><body>\n",
		"<center><table border=1 style='border-collapse:collapse;border:solid;'>\n",
		"<tr><th colspan=5>Driver comments for ",
		    $driver_name, "</th></tr>\n",
		"<tr><th>When</th><th>Driver</th><th>Route</th><th>Disposition</th><th>Comments</th></tr>\n";
	foreach my $e ( reverse @entries )
	    {
	    print "<tr style='", $STATUS_STYLES{$e->{disposition}}, "'>",
		"<th valign=top>", $e->{ymd}." ".$e->{hourmin},
		"</th>",
	        "<td align=left valign=top>", $e->{driver}, "</td>",
	        "<td align=left valign=top>", $e->{route}, "</td>",
		"<td valign=top>", $e->{disposition}, "</td><td valign=top>",
		$e->{comments}, "</td></tr>\n";
	    }
	print "</table>";
	}
    print "</center></body></html>\n";
    &cleanup(0);
    }

#########################################################################
#	Return a list of assessments for the specified patron.		#
#########################################################################
sub get_assessment_list
    {
    my( $tbl, $ind ) = @_;
    my $distind = &patron_to_distributor($ind);
    my $distributor_name = &DBget($distind,"Name");
    my $distributor_filename
	= &text_to_filename( $distributor_name );
    my $patron_name = &DBget($ind,"Name");
    my $patron_filename =
	&text_to_filename( $patron_name );
    my $dirname = join("/",$ASSESSMENT_DIR,$distributor_filename,$patron_filename);
    my @ret;
    if( ! -d $dirname )
        { push( @ret, "None" ); }
    else
        {
	foreach my $fname ( reverse sort &files_in($dirname) )
	    {
	    my $filedate = $fname;
	    $filedate =~ s/\.html$//;
	    push( @ret,
		"<a href='javascript:submit_func(\"$here/assessment_list,$tbl,$ind,$filedate\");'>",
	        $filedate, "</a>" );
	    }
	}
    return join(" ",@ret);
    }

#########################################################################
sub dump_assessment_list
    {
    my( $fnc, $tbl, $ind, @rest ) = @_;
    my $distind = &patron_to_distributor($ind);
    my $distributor_name = &DBget($distind,"Name");
    my $distributor_filename
	= &text_to_filename( $distributor_name );
    my $patron_name = &DBget($ind,"Name");
    my $patron_filename =
	&text_to_filename( $patron_name );
    my $dirname = join("/",$ASSESSMENT_DIR,$distributor_filename,$patron_filename);
    my @s = ( $form_top );
    if( ! -d $dirname )
        {
	push( @s,
	    "<h2 align=center>XL(There are no assessments for) $patron_name</h2>" );
	}
    elsif( @rest )
        {
	push( @s, &read_file("$dirname/$rest[0].html") );
	}
    else
	{
	push( @s, "<center><h2>XL(Assessments for) ${patron_name}:</h2>" );
	push( @s, "<table>\n" );
	foreach my $fname ( reverse sort &files_in($dirname) )
	    {
	    my $filedate = $fname;
	    $filedate =~ s/\.html$//;
	    push( @s, "<tr><th align=left>",
		"<a href='javascript:submit_func(\"$here/assessment_list,$tbl,$ind,$filedate\");'>",
	        $filedate, "</a>",
		"</th></tr>\n" );
	    }
	push( @s, "</table></center>" );
	}
    &xprint( @s );
    #&footer( $tbl );
    &cleanup( 0 );
    }

#########################################################################
#	Dump a staffers's invoices as a pdf file.			#
#########################################################################
sub dump_invoices
    {
    my( $fnc, $tbl, $ind ) = @_;
    #print "Content-type:  text/html\n\n";
    &fatal("Insufficient permissions to read log file.")
	if( ! &i_can(__LINE__,"r","Staff",$ind) );
    my $dind = &DBget($ind,"Distributor");
    my $rates = &DBget($dind,"Reimbursement");

    my $fname = &filename_of( $ind );
    my $dname = &filename_of( $dind );

    my $pdftemp = &tempfile("pdf");
    system( join(" ",
	$DISTUSER_TO_PDF,
	"-i",	"$TRIPS_DIR/$dname/$fname.log",
	"-d",	$dname,
	"-u",	$fname,
	"-r", 	$rates,
	"-o",	$pdftemp,
	">/tmp/fun.log 2>&1"
	) );
    if( ! -s $pdftemp )
	{ print "Content-type:  text/html\n\nCould not build $INVOICES_DIR/$dname/$fname/*.pdf.\n"; }
    else
	{
	print "Content-text:  application/pdf\n",
	    "Content-disposition:  attachment; filename=\"$fname.pdf\"\n\n",
	    &read_file( $pdftemp );
	}
    #print "Content-type:  plain/text\n\nind=$ind dind=$dind\nRead $INVOICES_DIR/$dname/$fname\n";
    &cleanup(0);
    }

#########################################################################
#	Return the name of a patron in sort order.			#
#########################################################################
sub sort_patron
    {
    my( $ind ) = @_;
    my( @name_parts ) = split(/\s+/,&DBget($ind,"Name"));
#    print STDERR "ind=[$ind] status=",
#        (&DBget($ind,"Status")||"UNDEF"),
#	" name_parts=[",join(",",@name_parts),"]\n";
    return join(", ",&DBget($ind,"Status"),pop(@name_parts),join(" ",@name_parts));
    }

#########################################################################
#	Return ordered list of things we can actually see.		#
#########################################################################
sub ordered_list
    {
    my( $tbl, @inds ) = @_;
    my @unsorted;
    my $today = &time_string("%04d-%02d-%02d");
    foreach my $ind ( grep( &i_can(__LINE__,"r",$tbl,$_), @inds ) )
        {
	push( @unsorted, $ind )
	    if( &DBget($ind,"Name") !~ / on (\d\d\d\d-\d\d-\d\d)$/
	     || $1 ge $today );
	}

    my @sorted = ( $tbl eq "Patron"
		? sort { &sort_patron($a) cmp &sort_patron($b) } @unsorted
		: &dbsort(@unsorted)
	);
    print STDERR __LINE__, ": ordered_list($tbl,[",join(",",@inds),
	"] unsorted [",join(",",@unsorted),
        "] returns [",join(",",@sorted),"]\n";
    return @sorted;
    }

#########################################################################
#	Returns true if specified field of index contains value.	#
#########################################################################
sub field_contains
    {
    my( $ind, $fp, $lookfor, $exact_match ) = @_;
    my $indi_val = &indirect_get($ind,$fp)||"";
    if( $exact_match )
        { return grep( $lookfor eq $_, split(/,/,$indi_val) ); }
    else
        { return ( $indi_val =~ /$lookfor/ ); }
    }

#########################################################################
#	Create a <select> with the options available for sending data.	#
#########################################################################
sub routing_select
    {
    my( $tbl, $what, $pretty_text, $staffinds ) = @_;
    my $cap_pretty_text = ucfirst( $pretty_text );
    my @to_print;
    my @toprint =
	( "<select",
	" help='select_$cap_pretty_text'",
	" onChange='submit_func(this.value,\"$tbl\");this.selectedIndex=0;'>",
	"<option selected>XL(".ucfirst($cap_pretty_text),
	#" (tbl=$tbl what=$what)",
	")</option>" );
    push( @toprint,
	"<option value='",
	    ( $what eq "html"
		? "$here/${what}_with_normal_header"
		: "$here/${what}_with_custom_header" ),
			"'>XL(Download/print $pretty_text)",
	    #"tbl=$tbl what=$what",
	    "</option>" )
	#if( $tbl ne "Patron" );
	if( &inlist( $what, "stickers", "vcf", "assessment" ) );
	#if( $what eq "stickers" || $what eq "vcf" );
    if( $staffinds )
	{
	my %staff_todos;
	foreach my $staffind ( split(/,/,$staffinds) )
	    {
	    my $destname = &DBget( $staffind, "Name" );
	    push( @{$staff_todos{"Download/print $pretty_text for"}},
	        { text=>$destname, value=>
		    ( $what eq "html"
			? "$here/${what}_with_normal_header,,$staffind"
			: "$here/${what}_with_custom_header,,$staffind" ) } )
		if( $tbl eq "Patron"
		 && $what ne "stickers" && $what ne "vcf" );
	    if( my $notify = &DBget( $staffind, "Notify" ) )
		{
		my $verb =
		    ( $notify =~ /^(\d+)@(.*+)$/ && $PHONE_HANDLERS{$2}
		    ? "Text" : "Email" );
		push( @{$staff_todos{"$verb $pretty_text to"}},
		    { text=>$destname, value=>
			"$here/${what}_to_email,,$staffind" } );
		}
	    }
	foreach my $medium ( sort keys %staff_todos )
	    {
	    my $big_group = ( scalar( @{ $staff_todos{$medium} } ) > 1 );
	    push( @toprint, "<optgroup label='XL($medium)'>\n" )
	        if( $big_group );
	    foreach my $optp ( @{ $staff_todos{$medium} } )
	        {
		push( @toprint, "<option value='$optp->{value}'>",
		    ( $big_group
		    ? $optp->{text}
		    : "XL($medium) $optp->{text}" ),
		    "</option>\n" );
		}
	    push( @toprint, "</optgroup>\n" )
	        if( $big_group );
	    }
	}
    push( @toprint,
        "<option value='$here/display_route_order'>",
	    "XL(View or re-order route)" )
	if( $pretty_text eq "route" );

    push( @toprint, "</select>\n" );
    return @toprint;
    }

#########################################################################
#	Return a list of router software with default first.		#
#########################################################################
sub router_list
    {
    my @extlist = sort &mappers_list( "progress" );
    if( grep( $_ eq $DEFAULT_ROUTER, @extlist ) )	# Force Mapquest to be first
	{
	@extlist = grep( $_ ne $DEFAULT_ROUTER, @extlist );
	unshift( @extlist, $DEFAULT_ROUTER );
	}
    return @extlist;
    }

#########################################################################
#	Show all routes a user can see.					#
#########################################################################
sub show_search
    {
    my %args = @_;
    my @fields = grep($_->{Searchable}, &fields_of( $args{tbl} ));
    $cpi_vars::FORM{window_start}=0 if( ! defined($cpi_vars::FORM{window_start}) );
    my @toprint;
    push( @toprint, $form_top ) if( $args{lvl} == 0 );

    my @extlist = &router_list();
    my %minmaps_list = map { ($_,$mappers{$_}->{minmaps}) } @extlist;
    my %maxmaps_list = map { ($_,$mappers{$_}->{maxmaps}) } @extlist;
    push( @toprint,
	"<script>\n",
	    "var seltext = ['XL(Check routes to map first)',\n",
	    "    'XL(Check routes to map or select format to download)'];\n",
	    "var minmaps = ", encode_json( \%minmaps_list ), ";\n",
	    "var maxmaps = ", encode_json( \%maxmaps_list ), ";\n",
	    "window.addEventListener( 'pageshow', maps_list_changed );\n",
	"</script>\n" );

    push( @toprint, <<EOF );
<input type=hidden name=window_start value="$cpi_vars::FORM{window_start}">
EOF
    #print "show_search here = [",($here||"UNDEF"),"]<br>\n";
    #print "tbl=$args{tbl}<br>\n";

    my $counter = 0;
    my $seen = 0;
    my $window_start = $cpi_vars::FORM{window_start} || 0;

    my $nfields = scalar(@fields);
    $nfields++ if( $args{tbl} eq "Route" );
    push( @toprint, &pretty_message($args{msg}),
        "<table border=1 cellspacing=1 cellpadding=5 style='border-collapse:collapse;border:solid;'>\n" );
        #"<table border=1 cellspacing=0 cellpadding=0 style='border-collapse:collapse;border:solid;'>\n" );

    $cpi_vars::FORM{window_size} = $DEFAULT_WINDOW_SEARCH_MAX
	if( ! defined($cpi_vars::FORM{window_size}) );
    #push( @toprint, "<tr><th>", $window_start, "</th></tr>\n" );
    push( @toprint, "<tr><th style='padding:0px;border-width:0px;'>",
	( $here !~ /\// ? ""
        : "<input type=button help='button_larr' class='no-print' onClick='submit_func(\"$here/Back\");' value='&larr;'>\n" ),
	"</th>");
    $cpi_vars::FORM{"S_Status"} ||= "Active";
    foreach my $fp ( @fields )
	{
	my $fname = $fp->{Name};
	my $fheader = "XL(" . ( $fp->{header} || &filename_to_text($fp->{Name}) ) . ")";
	my $fv = ( $cpi_vars::FORM{"S_$fname"} || "" );
	push( @toprint,
	    "<th valign=top",
	    " help='search_$args{tbl}'>",
	    "<a href='javascript:window.document.${FORMNAME}[\"S_$fname\"].value=prompt(\"Enter ${fheader} to search for\");submit_func(\"$here\");'>",
	    $fheader,
	    "</a>",
	    ($fv ? "<br>$fv" :""),
	    "<input type=hidden name=S_$fname value='$fv'>",
	    "</th>\n" );
	}
    push( @toprint, "<th>XL(Select)</th>" ) if( $args{tbl} eq "Route" );
    push( @toprint, "</tr>\n" );
    my @search_results;
    foreach my $exact_flag ( 1, 0 )
	{
	foreach my $ind ( &ordered_list( $args{tbl}, &DBget( $args{tbl} ) ) )
	    {
	    my $cutout = 0;
	    foreach my $fp ( @fields )
		{
		my $field = $fp->{Name};
		$cutout = "Test 1", last
		    if( grep( $field eq $_, "Distributor", "Route", "Staff" )
		     && $args{$field}
		     && ! &field_contains($ind,$fp,&DBget($args{$field},"Name"),$exact_flag) );
		$cutout = "Test 2", last
		    if( $cpi_vars::FORM{"S_$field"}
		     && ! &field_contains($ind,$fp,$cpi_vars::FORM{"S_$field"},$exact_flag) );
		}
	    #print "ind=$ind cutout=$cutout<br>\n";
	    push( @search_results, $ind ) if( ! $cutout );
	    }
	last if( @search_results );
	}

    foreach my $ind ( @search_results )
        {
	if( $counter >= $window_start && $counter < $window_start+$cpi_vars::FORM{window_size} )
	    {
	    my $current_status = ( &DBget($ind,"Status") || "Active" );
	    my ( $status_vp ) = grep( $_->{name} eq $current_status,
					@{ $SELECT_FROM_LIST{Status}} );
	    my $stylearg =
		( $status_vp
		? " style='".$status_vp->{style}."'"
		: "" );
	    push( @toprint, "<tr><th style='padding:0px;border-width:0px;'>" );
	    if( $counter && $counter == $window_start )
		{ push( @toprint, "<input type=button help='button_uarr' class='no-print' onClick='submit_func(\"$here/SearchWindow,up\");' value='&uarr;'>\n" ); }
	    elsif( $counter && $counter == $window_start+1 )
		{ push( @toprint, "<input help='input_size' class='no-print' type=number min=3 max=10000 size=4 name=window_size value='$cpi_vars::FORM{window_size}' onChange='submit_func(\"$here/SearchWindow,size\");'>" ); }
	    elsif( $counter == $window_start+$cpi_vars::FORM{window_size}-1 )
		{ push( @toprint, "<input type=button help='button_darr' class='no-print' onClick='submit_func(\"$here/SearchWindow,down\");' value='&darr;'>\n" ); }
	    push( @toprint, "</th>\n",
		( map {(
		    "    <td valign=top$stylearg",
		    " help='field_$args{tbl}_$_->{Name}'>",
		    &Field_Dispatch("r",$args{tbl},$ind,$_,
		        &DBget($ind,$_->{Name})),
		    "</td>\n" )} @fields ) );
	    push( @toprint,
		"<th valign=top$stylearg help='select_routes_to_map'>",
		"<input type=checkbox name=maps help='select_routes_to_map' value=$ind onChange='maps_list_changed();'></th>" )
		if( $args{tbl} eq "Route" );
	    push( @toprint, "</tr>\n" );
	    $seen++;
	    }
	$counter++;
	}

    push( @toprint, "<input type=hidden name=window_last value='$counter'>\n",
        "<tr><th style='padding:0px;border-width:0px;'>" );

    print STDERR __LINE__, ":  CMC tbl=$args{tbl}.\n";
    #if( $args{tbl} eq "Staff" || &i_can(__LINE__,"w",$args{tbl},$args{ind}) )
    if( &i_can(__LINE__,"w",$args{tbl},$args{ind}) )
	{
	push( @toprint,
	    "<input type=button help='button_plus' onClick='submit_func(\"$here/Add,$args{tbl},",
	        ( $args{defvals}||""), "\");' value='+'>" );
	push( @toprint,
	    "<input type=button help='button_include' onClick='setdisplay(\"record_screen_id\",0);setdisplay(\"add_routes_id\",1);'",
	        " value='I'>" )
	    if( $args{tbl} eq "Patron" );
	}
    push( @toprint,
	"</th><th colspan=$nfields style='padding:0px;border-width:0px;'>",
	    "<table class='no-print' border=0 width=100%><tr><th>" );
    my $staffinds = ( $args{Route} ? &DBget( $args{Route}, "Driver" ) : undef );
    push( @toprint,
	&routing_select( $args{tbl}, "vcf", "contacts", $staffinds ) )
	if( $args{tbl} eq "Patron" || $args{tbl} eq "Staff" );
    push( @toprint,
	&routing_select( $args{tbl}, "stickers", "stickers", $staffinds ),
	&routing_select( $args{tbl}, "html", "route", $staffinds ) )
	if( $staffinds );
    if( $args{tbl} eq "Route" )
	{
	push( @toprint,
	    "<select help='select_route_map_format' onChange='javascript:submit_func(\"map_with_custom_header\",this.value);this.selectedIndex=0;'>\n",
	    "<option selected disabled id=opt_download_ext>",
		"XL(Check routes to map or select format to download)",
	    "</option>" );
	foreach my $ext ( @extlist )
	    {
	    push( @toprint, "\n<option id=opt_$ext disabled value='$ext'>", $mappers{$ext}{name}, "</option>" );
	    }
	push( @toprint, "</select>" );
	}

    my $lcpluralized = &nword(lc($args{tbl}),$seen);
    my $matches = ( $counter!=$seen ? "matching" : $seen==1 ? "matches" : "match" );
    push( @toprint, "</th><th align=right>",
        ( $seen != $counter
	    ? "XL(Showing) XL($lcpluralized of) $counter XL("
	    : "XL($lcpluralized" ),
	" $matches description)</th></tr>\n",
	"</table></th></table>\n" );
    if( $args{lvl} > 0 )
	{ return join("",@toprint); }
    else
	{
        push( @toprint, "</center></form>" );
        &xprint( @toprint );
        &footer($args{tbl});
	&cleanup( 0 );
        }
    }

##########################################################################
##	Generate a simple table for debugging.				#
##########################################################################
#sub debug_html_table
#    {
#    my @vvars;
#    my @vvals;
#    while( defined($_ = shift(@_)) )
#	{ push(@vvars,$_); push(@vvals,shift(@_)); }
#    my @toprint = ( "<table border=1 cellspacing=3 cellpadding=3 style='border-collapse:collapse;border:solid;'>" );
#    if( 1 )
#	{
#	push( @toprint, "<tr>", ( map {"<th>$_</th>"} @vvars ), "</tr>\n",
#		"<tr>",
#		( map {"<td>".($_||"UNDEF")."</td>" } @vvals ),
#		"</tr>\n" );
#	}
#    else
#	{
#	push( @toprint, ( map {
#	     "<tr><th align=left>${_}:</th>"
#	     . "<td>".(shift(@vvals)||"UNDEF")."</td></tr>\n" } @vvars ) );
#	}
#    push( @toprint, "</table>" );
#    return join("",@toprint);
#    }

#########################################################################
#	Handle regular user commands					#
#########################################################################
sub interactive_handler
    {
    my( $msg, @so_far ) = @_;
    print STDERR "interactive_handler[",$msg||"UNDEF","]\n";
    my( $fnc, $tbl, $ind, @rest );
    my( $prevfnc, $prevtbl, $prevind );

    push( @so_far, "Search,Distributor," ) if( ! @so_far );
    @so_far = grep($_,@so_far);
    $here = join("/",@so_far);

    my @so_far_text;
    foreach my $t ( @so_far )
	{
	( $fnc, $tbl, $ind, @rest ) = split(/,/,$t);
	push( @so_far_text,
	    join(",",
                $fnc||"UNDEF",
		($tbl||"UNDEF"),
		defined($ind)?$ind.":".(&DBget($ind,"Name")||"UNDEF"):""
	    ));
	}
    my $heretext = join("/",@so_far_text);
    
    ( $fnc, $tbl, $ind, @rest ) = split(/,/,pop(@so_far));
    ( $prevfnc, $prevtbl, $prevind ) = split(/,/,$so_far[$#so_far])
	if( $so_far[$#so_far] );
    &debugout(__LINE__," interactive_handler",
	" fnc=",($fnc||"UNDEF"),
	" tbl=",($tbl||"UNDEF"),
	" ind=",($ind||"UNDEF"),
	"    prev:  ",
	" prevfnc=",($prevfnc||"UNDEF"),
	" prevtbl=",($prevtbl||"UNDEF"),
	" ind=".($prevind||"UNDEF") );

#    &xprint( &debug_html_table(
#	"msg", $msg,
#	"heretext", $heretext,
#	"fnc", $fnc,
#	"tbl", $tbl,
#	"ind", $ind,
#	"prevfnc", $prevfnc,
#	"prevtbl", $prevtbl,
#	"prevind", $prevind
#	);

    if( $fnc eq "SearchWindow" )
	{ $allow_reset_window = 0; }
    elsif( $allow_reset_window )
	{ $cpi_vars::FORM{window_start} = 0; }

    if( $fnc eq "Back" )
	{
	pop( @so_far );
	&interactive_handler( "", @so_far );
	}
    elsif( $fnc eq "Update" )
	{
	&update_record( $tbl, $ind );
	pop( @so_far );
	&interactive_handler( &DBget($ind,"Name")." XL(updated.)", @so_far );
	}
    elsif( $fnc eq "Include" )
	{
	&include_patrons_from_routes(
	    $tbl, $ind, split(/,/,$cpi_vars::FORM{"add_routes"}) );
	&interactive_handler( &DBget($ind,"Name")." XL(updated.)", @so_far );
	}
    elsif( $fnc eq "Delete" )
	{
	my $name = &DBget( $prevind, "Name" );
	&delete_record($prevtbl,$prevind);
	pop( @so_far );
	&interactive_handler( "$name XL(deleted.)", @so_far );
	}
    elsif( $fnc eq "Show" )
	{ &show_record( msg=>$msg, tbl=>$tbl, ind=>$ind, editmode=>0 ); }
    elsif( $fnc eq "Edit" )
	{ &show_record( msg=>$msg, tbl=>$tbl, ind=>$ind, editmode=>1 ); }
    elsif( $fnc eq "Add" )
	{ &show_record( msg=>$msg, tbl=>$tbl, defvals=>$ind, editmode=>1 ); }
    elsif( $fnc eq "Search" )
	{
	if( $TABLE_FIELDS{$tbl} )
	    { &show_search( msg=>$msg, tbl=>$tbl, lvl=>0 ); }
	else
	    { &interactive_handler("Unknown table to search",@so_far); }
	}
    elsif( $fnc eq "SearchWindow" )
	{
	$cpi_vars::FORM{window_size} = $DEFAULT_WINDOW_SEARCH_MAX
	    if( ! defined($cpi_vars::FORM{window_size}) );
	if( $tbl eq "up" )
	    {
	    $cpi_vars::FORM{window_start} -= $cpi_vars::FORM{window_size};
	    $cpi_vars::FORM{window_start} = 0 if( $cpi_vars::FORM{window_start} < 0 );
	    }
	elsif( $tbl eq "down" )
	    {
	    $cpi_vars::FORM{window_start} += $cpi_vars::FORM{window_size};
	    $cpi_vars::FORM{window_start} = 0
		if( $cpi_vars::FORM{window_start} >= $cpi_vars::FORM{window_last} );
	    }
	elsif( $tbl eq "size" )
	    {
	    }
	&interactive_handler( "", @so_far );
	}
    elsif( $fnc eq "anonymous_new_form" )
        {
	&dump_assessment();
	}
    elsif( $fnc eq "anonymous_new_record" )
        { &anonymous_new_record( $tbl, $cpi_vars::FORM{distind}, $cpi_vars::FORM{rectype}); }
    elsif( $fnc eq "anonymous_add_record" )
	{
	&update_record( $tbl, $ind );
	&xprint( "</head><body>",
	    "<center>",
	    "<h1>XL($tbl record submitted.)</h1>\n",
	    "<h2>XL(We will get back to you shortly!)</h2>\n",
	    "</center>",
	    "<script>\nwindow.close();\n</script>\n",
	    "</body></html>" );
	&cleanup( 0 );
        }
    elsif( $fnc =~ /(assessment|stickers|vcf|html)_(with_custom_header|with_normal_header|to_email)/ )
    #elsif( &inlist( $fnc, "stickers_with_custom_header", "vcf_with_custom_header", "vcf_to_email", "html_with_custom_header", "html_to_email" ) )
	{
	print STDERR "Calling dump_*(",$fnc||"UNDEF",",",$tbl||"UNDEF",",",$ind||"UNDEF",")\n";
	$msg =
	    ( $1 eq "assessment"
	    ? &dump_assessment($fnc,$prevtbl,$prevind)
	    : &dump_route($fnc,$tbl,$ind) );
	print STDERR "Calling interactive_handler( ",$msg||"UNDEF", join(",",@so_far), " )\n";
	&interactive_handler( $msg, @so_far );
	}
    elsif( $fnc eq "map_with_custom_header" )
	{ &dump_map( $cpi_vars::FORM{arg} ); }
    elsif( $fnc =~ /(\w*)_route_order/ )
        { &modify_route_order($1); }
    elsif( $fnc eq "list_route_runs" )
	{ &list_route_runs($tbl,$ind,@rest); }
    elsif( $fnc eq "rebalance_routes" )
	{ &rebalance_routes($tbl,$ind,@rest); }
    elsif( $fnc eq "import_patrons" )
	{ &interactive_handler( &import_patrons($tbl,$ind,@rest), @so_far ); }
    elsif( $fnc eq "export_with_custom_header" )
	{ &export_with_custom_header($tbl,$ind,@rest); }
    elsif( $fnc eq "new_record_sheet" )
	{ &anonymous_new_record($tbl,$ind,@rest); }
    elsif( $fnc eq "log_with_custom_header" )
	{ &dump_patron_log($fnc,$tbl,$ind); }
    elsif( $fnc eq "assessment_list" )
	{ &dump_assessment_list($fnc,$tbl,$ind,@rest); }
    elsif( $fnc eq "invoices_with_custom_header" )
	{ &dump_invoices($fnc,$tbl,$ind); }
    elsif( $fnc ne "" && $fnc ne "dirmode" && $fnc ne "dologin" )
	{ &interactive_handler("XL(Unrecognized function)",@so_far); }
    }

#########################################################################
#	Convert a number from a base 
#########################################################################
my @dig_list;		# Set in decode_progress
my %dig_map;
my $dig_radix;
sub convert_base
    {
    my ( @digs ) = split(//,$_[0]);
    my $n = 0;
    my $d;
    #print "dig_list=[",join(",",@dig_list),"]<br>\n";
    while( defined($d = shift(@digs)) )
	{
	#print "d($d) maps to [",$dig_map{$d},"].<br>\n";
	$n = $n*$dig_radix + $dig_map{$d};
	}
    #print "convert_base($_[0]) returns [$res]<br>\n";
    return $n;
    }

#########################################################################
#	Return an array of progress points from a string.		#
#########################################################################
sub decode_progress
    {
    my( $progress_string ) = @_;
    my $decode_order_length = scalar(@DECODE_ORDER);
    my $opcode;
    my $opval;

    return undef if( ! $progress_string );
    my @pieces = ( grep( $_ ne "", split(/([\n\+\-:])/,$progress_string)) );
    return undef if( ! @pieces );
    @dig_list = split(//,shift(@pieces));
    %dig_map = map { ($dig_list[$_],$_) } ( 0 .. $#dig_list );
    $dig_radix = scalar(@dig_list);

    my $dig_offset = int($dig_radix/2);
    my @new_pieces;

    while( defined( $opcode = shift(@pieces) ) )
	{
	$opval = shift(@pieces);
	if( $opval eq "\n" )
	    { push( @new_pieces, "reset" ); }
	elsif( $opcode eq "+" )
	    { push( @new_pieces,  &convert_base( $opval ) ); }
	elsif( $opcode eq "-" )
	    { push( @new_pieces, -&convert_base( $opval ) ); }
	elsif( $opcode eq ":" )
	    {
	    foreach my $c ( split(//,$opval) )
		{
		if( scalar(@new_pieces) % $decode_order_length == 0 )
		    { push( @new_pieces, $dig_map{$c} ); }
		else
		    { push( @new_pieces, $dig_map{$c}-$dig_offset ); }
		}
	    }
	}

    my %decode_offsets = map { ( $_, 0 ) } @DECODE_ORDER;
    my %decode_tbl;
    my @decode_ret = ();
    my $decode_ind = 0;
    foreach $opval ( @new_pieces )
	{
	if( $opval eq "reset" )
	    {
	    %decode_offsets = map { ( $_, 0 ) } @DECODE_ORDER;
	    }
	else
	    {
	    my $indtxt = $DECODE_ORDER[$decode_ind];
	    $decode_offsets{ $indtxt } += $opval;
	    $decode_tbl{$indtxt} = $decode_offsets{ $indtxt };
	    $decode_tbl{$indtxt} /= 1000000.0 if( $decode_ind );

	    if( ++$decode_ind >= $decode_order_length )
		{
		my %topush = %decode_tbl;
		push( @decode_ret, \%topush );
		%decode_tbl = ();
		$decode_ind = 0;
		}
	    }
	}

    return \@decode_ret;
    }

#########################################################################
#	Modify a string to a new value according to a (very simple)	#
#	instruction string.  Hopefully this replaces network bandwidth	#
#	with CPU on both sender and receiver's part.			#
#########################################################################
sub apply_edit_string
    {
    my ($base_string, $instructions) = @_;
    print STDERR "CMC applying [$instructions] to [$base_string].\n";
    my $modified_string = $base_string;

    for my $piece (split /`/, $instructions)
	{
        if ($piece !~ /^(\d+)([idrc])(.*)/)
	    { print "Bad instruction [$piece]\n"; }
	else
	    {
	    my( $loc, $cmd, $arg ) = ( $1, $2, $3 );
	    print STDERR "loc=$loc cmd=$cmd arg=[$arg]\n";

	    $modified_string =
		( $cmd eq 'i' ?		# Insert
		    substr($modified_string, 0, $loc)
		    . $arg . substr($modified_string, $loc)
		: $cmd eq 'r' ?		# Replace
		    substr($modified_string, 0, $loc)
		    . $arg . substr($modified_string, $loc + length($arg))
	        : $cmd eq 'd' ?		# Delete
		    substr($modified_string, 0, $loc)
		    . substr($modified_string, $loc + ($arg||1))
		: $cmd eq 'c' ?		# Clear/replace to end of string
		    substr($modified_string, 0, $loc )
		    . $arg
		: undef );
	    print STDERR "creates [$modified_string]\n";
	    }
	}

    my $route_status_debug = $cpi_vars::FORM{route_status_debug};
    if( $route_status_debug && ($route_status_debug ne $modified_string) )
	{
	print STDERR	"Applying    <$instructions>\n",
			"      to    <$base_string>\n",
			" created    <$modified_string>\n",
			" instead of <$route_status_debug>\n";
	$modified_string = $route_status_debug;
	}
    else
        { print STDERR "Result [$modified_string]\n"; }
    return $modified_string;
    }

#########################################################################
##	Parse incoming form.						#
#########################################################################
sub parse_trip_form
    {
    my $jsonfile = sprintf("%s/%s.json",
    	$PROGRESS_DIR,$cpi_vars::FORM{status_file});
    my $old_route_status_string = &read_file( $jsonfile, "" );
    my $new_route_status_string =
        &apply_edit_string(
	    $old_route_status_string,
	    $cpi_vars::FORM{route_status_edit});

    my $route_status;
    eval { $route_status = &decode_json($new_route_status_string); };
    
    if( ! $route_status )
	{	# Apparently above didn't create legal JSON.  Don't update
		# the old file, but leave result around for debugging.
	print STDERR "decode_json() failed, update in $jsonfile.bogus.\n";
	&write_file( "$jsonfile.bogus", $new_route_status_string );
	return undef;
	}

    &setup_file( $jsonfile, $new_route_status_string );

    $mail_header{from}	=
	"$PROJLONG $route_status->{ROUTE_NAME} <$PROJECT\@$cpi_vars::DOMAIN>";
    $mail_header{subject} =
	"$PROJLONG $route_status->{ROUTE_NAME} route update";

    my %ret =
	(
	user		=>	$route_status->{USER},
	staff		=>	$route_status->{STAFF},
	distributor	=>	$route_status->{DISTRIBUTOR},
	route_name	=>	$route_status->{ROUTE_NAME},
	secret		=>	$route_status->{SECRET},
	stops		=>	$route_status->{stops},
    	display_order	=>	$route_status->{display_order},
	done		=>	$route_status->{done},
	update_time	=>	$route_status->{update_time},
	progress_string	=>	$route_status->{progress},
	serial		=>	$cpi_vars::FORM{route_status_serial}
	);

    return \%ret;
    }

#########################################################################
#	Figure out what type of input we're getting and			#
#	call appropriate parser.					#
#########################################################################
sub parse_trip_input
    {
    my $input_p = &parse_trip_form();

    my $stops = $input_p->{stops};
    my $display_order = $input_p->{display_order};

    my @mileage;
    my @whens;
    my @whenminutes;
    $input_p->{donation} = 0.0;
    foreach my $display_order_ind ( 0 .. $#{$display_order} )
	{
	my $stop_p = $stops->[$display_order->[$display_order_ind]];
	push( @mileage, $stop_p->{odometer} ) if( $stop_p->{odometer} );
	push( @whens, $stop_p->{when} );
	if( $stop_p->{when} )
	    {
	    push( @whens, $stop_p->{when} );
	    push( @whenminutes, $1*60+$2 ) if($stop_p->{when} =~ /(\d+):(\d+)/);
	    }
	$input_p->{donations} += $stop_p->{donation} if( $stop_p->{donation} );
	}
    if( scalar(@mileage) >= 2 )
        {
	@mileage = sort @mileage;
	my $miledif = $mileage[$#mileage]-$mileage[0];
	$input_p->{mileage} = sprintf("%.1f",$miledif);
	}

    if( scalar(@whenminutes) >= 2 )
        {
	@whenminutes = sort @whenminutes;
	my $whendiff = $whenminutes[$#whenminutes]-$whenminutes[0];
	$input_p->{elapsed} = sprintf("%d:%02d",$whendiff/60, $whendiff % 60 );
	}

    $input_p->{route_ind} ||= &findkeys("Route","Name",$input_p->{route_name});
    $input_p->{driver_ind} = $input_p->{staff};
    if( $input_p->{user} ne "%%USER%%" )
	{
	my $driver_ind = &findkeys("Staff","User",$input_p->{user});
	$input_p->{driver_ind} = $driver_ind if( $driver_ind );
	}
    $input_p->{distributor_name} = &DBget( $input_p->{distributor}, "Name" );
    $input_p->{distributor_filename} =
	&text_to_filename( $input_p->{distributor_name} );
    $input_p->{driver_name} = &DBget( $input_p->{driver_ind}, "Name" );
    $input_p->{driver_filename} =
	&text_to_filename( $input_p->{driver_name} );
    $input_p->{route_filename} = &text_to_filename( $input_p->{route_name} );

    $input_p->{date}=&time_string($STANDARD_DATE_FMT,$now);
    $input_p->{wday}=$DAY_NAMES[(localtime($now))[6]];

    return $input_p;
    }

#########################################################################
#	Generate table							#
#########################################################################
sub generate_html
    {
    my( $input_p ) = @_;
    my $stops = $input_p->{stops};
    my $display_order = $input_p->{display_order};
    my $print_route_type = $stops->[0]{route_type}||"";
    $print_route_type =~ s+_+ +g;

    my @ret = ( <<EOF );
<html><head></head><body><center>
<table width=90% style='border: solid black' border=0 cellspacing=0>
    <tr><th width=100% align=left>$print_route_type<br>Stops</th>
	<th align=left>Status</th>
	<th align=right>When</th>
	<th align=right>Odometer<br>(miles)</th>
	<th align=right>Donation<br>(type)</th></tr>
EOF

    #my @addressparts = ( "http://maps.google.com/maps/dir" );
    foreach my $display_order_ind ( 0 .. $#{$display_order} )
	{
	my $stop_p = $stops->[$display_order->[$display_order_ind]];
	#push( @addressparts, $stop_p->{address} );
	push( @ret,
	    "    <tr style=", $STATUS_STYLES{$stop_p->{status}}, ">",
	    "<th style='border-top:1px solid blue' align=left>",
	        $stop_p->{name}, "</th>\n",
	    "\t<td style='border-top:1px solid blue' align=left>",
	        $stop_p->{status}, "</td>\n",
	    "\t<td style='border-top:1px solid blue' align=right>",
	        $stop_p->{when}||"", "</td>\n",
	    "\t<td style='border-top:1px solid blue' align=right>",
	        $stop_p->{odometer}||"", "</td>\n",
	    "\t<td style='border-top:1px solid blue' align=right>",
		( $stop_p->{donation}
		    ? sprintf("%s \$%4.2f",
			$stop_p->{donation_type},$stop_p->{donation})
		    : "" ),
		#"",
		"</td>\n",
	    "</tr>\n");
	if( $stop_p->{notes} )
	    {
	    my $notes = $stop_p->{notes};
	    $notes =~ s+\n+<br>\n+gs;
	    push( @ret,
	        "    <tr style=", $STATUS_STYLES{$stop_p->{status}}, ">",
	        "<td colspan=5>", $notes, "</td>",
	        "</tr>\n" );
	    }
	if( $stop_p->{pickups} )
	    {
	    push( @ret,
	        "    <tr style='border-top:1px solid blue'>",
	        "<td colspan=5>", &pickups_table($stop_p->{pickups}), "</td>",
	        "</tr>\n" );
	    }
	}
    push( @ret, "    <tr><th align=left colspan=2",
	" style='border-top:3px solid blue'>Totals:</th>",
	"<td align=right style='border-top:3px solid blue'>",
	sprintf("%s",$input_p->{elapsed}||""),
	"</td><td align=right style='border-top:3px solid blue'>",
	sprintf("%.1f",$input_p->{mileage}||0.0),
	"</td><td align=right style='border-top:3px solid blue'>",
	sprintf("\$%.2f",$input_p->{donations}||0.0),
	"</td></tr>\n" );

    push( @ret, "</table>\n",
		"<a target=completed_route_map href='$BASES_URL?",
		    "func=map_with_custom_header&arg=",
		    join(':',
			$input_p->{distributor}||"UNDEF",
			$input_p->{driver_ind}||"UNDEF",
			$input_p->{route_ind}||"UNDEF",
			$input_p->{date}||"UNDEF",
			$input_p->{secret}||"UNDEF",
			$DEFAULT_ROUTER), "'>",
		$input_p->{route_name},
		" route map</a>",
    		"</center></body></html>\n" );
    return join("",@ret);
    }

#########################################################################
#	Get range arrays from route order.				#
#########################################################################
sub get_route_ranges
    {
    my( $route_ind ) = @_;
    my $distributor_ind = &DBget( $route_ind, "Distributor" );
    my @patrons_to_route = &patrons_on( $route_ind );
    print STDERR __LINE__, ":  patrons_to_route=[",join(",",@patrons_to_route),"]\n";
    my @patron_ranges = ();
    my $order_string = &db_to_order_string( $route_ind );
    print STDERR __LINE__, ":  order_string=[$order_string]\n";
    $current_route = &DBget( $route_ind, "Name" );
    if( ! $order_string || $order_string eq "::" )
	{
	@patron_ranges =
	    (
	    [ $distributor_ind ],
	    [ &stops_to_patrons(
		&optimize_order($distributor_ind, @patrons_to_route, $distributor_ind)
		) ],
	    [ $distributor_ind ]
	    );
	}
    else
	{
	# Start with old route minus people no longer on route
	print STDERR __LINE__, ":  patrons_to_route now =[",join(",",@patrons_to_route),"]\n";
	my %somewhere_on_route =
	    map {($_,1)} ( @patrons_to_route, $distributor_ind );
	my @range_strings = split( /:/, $order_string );
	my %ordered_so_far;
	foreach my $range ( 0, 2 )
	    {
	    $patron_ranges[$range] =
		[ grep( $somewhere_on_route{$_},
		    split(/,/,$range_strings[$range]) ) ];
	    grep( $ordered_so_far{$_}=1, @{$patron_ranges[$range]} );
	    }
	my $starts_at = $patron_ranges[0][$#{$patron_ranges[0]}];
	my $ends_at = $patron_ranges[2][0];
	my @to_optimize = grep( ! $ordered_so_far{$_}, @patrons_to_route );
	my @optimized = &optimize_order(
	    $starts_at, 
	    @to_optimize,
	    $ends_at );
	shift( @optimized );
	pop( @optimized );
	$patron_ranges[1] = [ @optimized ];
	}
    #print "patron_ranges[0] = ", join(",",@{$patron_ranges[0]}), ".<br>\n";
    #print "patron_ranges[1] = ", join(",",@{$patron_ranges[1]}), ".<br>\n";
    #print "patron_ranges[2] = ", join(",",@{$patron_ranges[2]}), ".<br>\n";
    return @patron_ranges;
    }

#########################################################################
#	Convert from database id to form we use with javascript.	#
#########################################################################
sub db_to_order_string
    {
    my( $route_ind ) = @_;
    my $ret = join(":",
    	&DBget( $route_ind, "Route_starts_with" )||"",
	"",
    	&DBget( $route_ind, "Route_ends_with" )||"" );
    print STDERR "db_to_order_string($route_ind) returns [$ret]\n";
    return $ret;
    }

#########################################################################
#	Convert from javascript to form we can put in the database.	#
#########################################################################
sub order_string_to_db
    {
    my( $route_ind, $order_string ) = @_;
    if( $order_string && $order_string =~ /(.*):(.*):(.*)/ )
        {
	&DBput( $route_ind, "Route_starts_with", $1 );
	&DBput( $route_ind, "Route_ends_with", $3 );
	}
    else
        {
	&DBput( $route_ind, "Route_starts_with", undef );
	&DBput( $route_ind, "Route_ends_with", undef );
	}
    }

#########################################################################
#	Put up a page with the current route and allow him to set the	#
#	order.								#
#########################################################################
sub modify_route_order
    {
    my( $fnc ) = @_;	# display, optimize or update
    my $modified = 0;
    if( $here =~ m:(.*)/Show,Route,(.*?)/${fnc}_route_order: )
        {
	my $caller = "$1/Show,Route,$2";
	my $route_ind = $2;
	my $route_name = &DBget($route_ind,"Name");
	my @patron_ranges;
	my $order_string = &db_to_order_string($route_ind);
	$current_distributor = &DBget($route_ind,"Distributor");
	my @patrons_to_route = ( $current_distributor, &patrons_on( $route_ind ) );
	&setup_stops( $route_ind, @patrons_to_route );
	if( $fnc eq "update" )
	    {
	    &DBwrite();
	    &order_string_to_db( $route_ind, $order_string=$cpi_vars::FORM{route_order} );
	    &DBpop();
	    }
	@patron_ranges = &get_route_ranges( $route_ind );
	my %patron_texts
	    = map { ($_, "<th align=left>".&DBget($_,"Name")."</th><td>".&DBget($_,"Address")."</td>") }
	    	@patrons_to_route;
	&xprint(
	    $form_top,
	    "<center>Specified order of the $route_name route:</center>",
	    "<center id=route_order_list_id></center>",
	    "<input type=hidden id='route_order_id' name='route_order'/>",
	    "<input type=button help='button_larr' value='&larr;'",
	    " onClick='submit_func(\"$caller\");'/>",
	    "<input type=button help='button_Update_order' id=route_order_update_id disabled value='XL(Update)'",
	    " onClick='submit_func(\"$caller/update_route_order\");'/>",
	    "</form>\n",
	    "<script>\n",
	    "order_setup('route_order',",
		encode_json( \@patron_ranges ), ",",
		encode_json( \%patron_texts ), " );\n",
	    "</script>\n" );
	}
    &footer("Route");
    &cleanup(0);
    }

#########################################################################
#	Hack to make generated output have consistant indenting.	#
#########################################################################
sub indent
    {
    my( $line_number, @strings ) = @_;
    my @toprint;
    my $err = 0;
    foreach my $q ( @strings )
	{
	if( defined($q) )
	    { push( @toprint, $q ); }
	else
	    {
	    push( @toprint, "--UNDEF--" );
	    $err = 1;
	    }
	}
    print "Problem on line $line_number [", join("##",@toprint), "]\n" if( $err );
    @strings = split(/\n/s,join("",@strings));
    return join( "", map {"$INDENTATION$_\n"} @strings );
    }

#########################################################################
#	Convert time since the epoch in seconds to gpx time string.	#
##########################################################################
#sub global_time
#    {
#    return &time_string( $GLOBAL_TIME_FMT ,$now);
#    }

#########################################################################
#	Append results for each patron to their file.			#
#########################################################################
sub update_databases
    {
    my( $input_p )		= @_;
    my $stops			= $input_p->{stops};
    my $display_order		= $input_p->{display_order};
    my $driver_ind		= $input_p->{driver_ind};
    my $driver_name		= ($driver_ind?&DBget($driver_ind,"Name"):"?");

    # We do this in two different loops because it would decrease a fatality
    # from leaving the database locked.
    foreach my $display_order_ind ( 0 .. $#{$display_order} )
	{
	my $stop_p = $stops->[$display_order->[$display_order_ind]];

	&setup_file( ">>" .
	    join("/",
	        $PATRON_DIR, $input_p->{distributor_filename},
		&text_to_filename($stop_p->{name}).".log" ) );
	    
	print OUT
	    "Seen ",$input_p->{date}||"?",
	    " ",$stop_p->{when}||"?",
	    " by ",$driver_name||"?",
	    " on ",$input_p->{route_name}||""," route:\t",
	    $stop_p->{status}, "\n";
	print OUT "\t", join("\n\t",split(/\n/s,$stop_p->{notes})), "\n"
	    if( $stop_p->{notes} );
	print OUT "\t", join("\n\t",split(/\n/s,$stop_p->{pickups})), "\n"
	    if( $stop_p->{pickups} );
	close( OUT );
	}

    &DBwrite();
    my $route_ind=&findkeys("Route","Name",$input_p->{route_name});
    foreach my $display_order_ind ( 0 ... $#{$display_order} )
	{
	my $stop_p = $stops->[$display_order->[$display_order_ind]];
	foreach my $patron_ind ( split(/,/,$stop_p->{patrons}) )
	    {
	    my $patind_type = &rec_type($patron_ind);
	    if( $patind_type eq "Patron" )
		{
		&DBput( $patron_ind, "Last_seen",
		    $input_p->{date}." ".($stop_p->{when}||"?") );
		&DBput( $patron_ind, "Last_seen_by", $driver_ind||"" );
		&DBput( $patron_ind, "Last_route", $route_ind||"" );
		&DBput( $patron_ind, "Last_note", $stop_p->{notes} );
		&DBadd( $route_ind, "Pickups", $patron_ind );
		&DBput( $route_ind, "Pickups", $patron_ind, $stop_p->{pickups} );
		}
	    elsif( $patind_type eq "Distributor" )
		{
		# We silently ignore attempts to update Distributors
		}
	    else
		{ print STDERR "Problem updating patron database, patron_ind=[$patron_ind]\n"; }
	    }
	}
    &DBpop();
    }

#########################################################################
#	Just dump what we got with no HTML.				#
#########################################################################
sub dump_trip
    {
    my( $stops, $display_order ) = @_;

    foreach my $display_order_ind ( 0..$#{$display_order} )
	{
	my $stop_p = $stops->[$display_order->[$display_order_ind]];
	print $stop_p->{name}||"UNDEF",
	    " ",$stop_p->{when}||"UNDEF",
	    " ",$stop_p->{status}||"UNDEF",
	    ( $ENV{SCRIPT_NAME}?"<br>":"" ),
	    "\n";
	}
    }

#########################################################################
#	Send some debug information to a place it won't get deleted.	#
#########################################################################
sub debugout
    {
    my( @msg ) = @_;
    print STDERR "DEBUG:  ", join("",@msg,"\n");
    }

#########################################################################
#	Figure out what directories need to be made to create file.	#
#	If you have the contents, go ahead and just do it.		#
#########################################################################
sub setup_file
    {
    my ( $outarg, @contents ) = @_;
    my( $openfnc, $fn ) =
        ( $outarg=~/^([>]+)\s*(.*?)$/
	? ( $1, $2 )
	: ( ">", $outarg ) );
    my( @pieces ) = split(/\//,$fn);
    pop( @pieces );
    push( @pieces, "." ) if( ! @pieces );
    my $dirname = join("/",@pieces);
    #return undef if( ! -d $dirname && ! system("mkdir -p '$dirname'") );
    system("mkdir -p '$dirname'") if( ! -d $dirname );
    open( OUT, "$openfnc $fn" ) 
        || &autopsy("Cannot $openfnc to ${fn}:  $!");
    binmode OUT;		# Avoid "Wide character in print" error messages
    if( @contents )
        {
	print OUT @contents;
	close( OUT );
	}
    return $fn;
    }

#########################################################################
#	Update trips files.						#
#########################################################################
sub update_trips
    {
    my( $input_p, $html ) = @_;

    my $trip_string = join("\t",
	$input_p->{date},
	$input_p->{wday},
	$input_p->{elapsed}||"",
        (($input_p->{mileage}||"0")."@".($input_p->{stops}->[0]{route_type}||"Unknown")),
	$input_p->{route_name} ) . "\n";

    my $trip_base = join("/", $TRIPS_DIR,
	$input_p->{distributor_filename}, $input_p->{driver_filename} );

    &setup_file(">>$trip_base.log",$trip_string);

    &setup_file(
	join("/", $HTML_DIR,
	    $input_p->{distributor_filename}, $input_p->{driver_filename},
	    "$input_p->{date}-$input_p->{route_filename}.html" ),
	$html );
    }

#########################################################################
#	Returns the title from an active route.  Just centralizes the	#
#	format.								#
#########################################################################
sub progress_title
    {
    my( $input_p ) = @_;
    return $input_p->{title} ||= join("",
    	'"', $input_p->{route_name}, '" route',
	" driven ",	$input_p->{date},
	" by ",		$input_p->{driver_name}
	);
    }

#########################################################################
#	Update progress maps						#
#########################################################################
sub update_progress
    {
    my( $input_p ) = @_;

    my $progbase = join('/',$PROGRESS_DIR,$cpi_vars::FORM{status_file});
    my $progfile = "$progbase.progress";
    if( $input_p->{progress_string} =~ /^([^\+\-:]*)(.*)$/ )
        {
	my( $prefix, $data ) = ( $1, $2 );
	if( ! -r $progfile )
	    { &setup_file( ">$progfile", $prefix, "\n", $data, "\n" ); }
	else
	    { &setup_file( ">>$progfile", $data, "\n" ); }
	}
    &setup_file( "$progbase.po", Dumper( $input_p ) );
    }

#########################################################################
#	Unused update progress maps.					#
#########################################################################
sub old_update_progress
    {
    my( $input_p ) = @_;
    my $title = &progress_title($input_p);

    my $progbase = join('/',$PROGRESS_DIR,$cpi_vars::FORM{status_file});
    $input_p->{progress_p}
	||= &decode_progress( $input_p->{progress_string}||"" );
    undef( $input_p->{progress_string} ) if( $input_p->{progress_p} );
    my $old_p = ( -r "$progbase.po" ? &eval_po("$progbase.po") : undef );
    print STDERR "CMC $old_p->{secret} vs $input_p->{secret}\n" if( $old_p );
    if( $old_p && $old_p->{secret} && $old_p->{secret} eq $input_p->{secret} )
        {
	print STDERR "Combining progress strings.\n";
	$old_p->{progress_p}
	    ||= &decode_progress( $old_p->{progress_string}||"" );
	if( $old_p->{progress_p} )
	    {
	    if( @{$old_p->{progress_p}} )
	        {
		my $records_before = scalar( @{$old_p->{progress_p}} );
		my $latest_entry = $old_p->{progress_p}->[-1];
		my $last_recorded = $latest_entry->{when};

	        my $size_of_update = scalar( @{$input_p->{progress_p}} );
        	print STDERR "Adding $size_of_update to end of $records_before data ending at $last_recorded.\n";

		# Skip data from driver that we already have
		my $cur_ind = 0;
		while( $cur_ind < $size_of_update
		    && $input_p->{progress_p}->[$cur_ind]{when} <= $last_recorded )
		    {
		    my $current_entry = $input_p->{progress_p}->[$cur_ind];
		    if( abs($latest_entry->{lat}-$current_entry->{lat}) > 0.5
		     || abs($latest_entry->{lng}-$current_entry->{lng}) > 0.5 )
		        {
			print STDERR "CMC Huge leap from previous entry (",
			    join(",",$latest_entry->{when},$latest_entry->{lat},$latest_entry->{lng}),
			    ") and entry $cur_ind (",
			    join(",",$current_entry->{when},$current_entry->{lat},$current_entry->{lng}),
			    ".\n";
			}
		    $latest_entry = $current_entry;
		    $cur_ind++;
		    }
		print STDERR "CMC skipped $cur_ind entries.\n";

		# Copy the rest of the data (newer than what we already had)
		while( $cur_ind < $size_of_update )
		    {
		    push( @{$old_p->{progress_p}},
			$input_p->{progress_p}[ $cur_ind++ ] );
		    }
		$input_p->{progress_p} = $old_p->{progress_p};
		print STDERR "CMC length now $cur_ind.\n";
		}
	    }
	}

    foreach my $fmt ( &mappers_list( "progress" ) )
	{
	next if( $fmt ne "po" );	# Little point in doing conversions
	&setup_file( "$progbase.$fmt",
	    &{$mappers{$fmt}{progress}}($title,$input_p) );
	}

    my $route_ind = &findkeys("Route","Name",$input_p->{route_name});
    my $map_str = join(",", $input_p->{driver_ind}, $input_p->{date} );
    #
    # We used to update the database with each incoming update but it
    # created too many dead lock files.  Now we only do it when the
    # route is first generated.
    #&DBwrite();
    #&DBput( $route_ind, "Map", $map_str );
    #&DBpop();
    #print STDERR "Just put ", &DBget($route_ind,"Map"),
    #    " in $route_ind.<br>\n";

    return $input_p->{serial};
    }

#########################################################################
#	Check if administrator wants updating windows to stop.		#
#########################################################################
sub stop_updates_if_needed
    {
    if( my $reason = &read_file($EXIT_FILE,"") )
	{
	$reason =~ s/\n/\\n/g;
	print "<script>\nalert('$reason');\nparent.window.close();\n</script>\n";
	&cleanup( 0 );
	}
    }

#########################################################################
#	Somebody has completed a route and is sending in what happened.	#
#########################################################################
sub trip_update
    {
    $ENV{PATH}="/sbin:/bin:/usr/sbin:/usr/bin:/usr/local/bin:/opt/aws/bin";

    &stop_updates_if_needed();

    %mail_header = map { $_, $DEFAULT_HEADER{$_} } keys %DEFAULT_HEADER;

    my( $input_p ) = &parse_trip_input();

    my $timestr = &time_string("%04d-%02d-%02d %02d:%02d",$now);
    my $progress_received;
    my( $done ) = $input_p->{done};
    if( $done )
	{
	my $html_table = &generate_html( $input_p );
	&update_trips( $input_p, $html_table );
	&update_databases( $input_p );

	&cpi_send_file::sendmail(
	    $mail_header{from},
	    $mail_header{to},
	    $mail_header{subject},
	    $html_table
	    ) if( ! $LOCAL_OUTPUT );
	}

#    $input_p->{progress_p} ||= &decode_progress( $input_p->{progress_string} )
#        if( $input_p->{progress_string} );
#    delete $input_p->{progress_string} if( $input_p->{progress_p} );

    &update_progress( $input_p );
    #my $last_recorded = ( $input_p->{progress_p}->[-1]{when} || 0 );
    my $last_recorded = $input_p->{update_time};
    print "<script>\n",
	"parent.progress_logged($done,'$timestr',$cpi_vars::FORM{route_status_serial},$last_recorded);\n",
	"</script>\n";
    print STDERR
	"parent.progress_logged($done,'$timestr',$cpi_vars::FORM{route_status_serial},$last_recorded);\n";

    if( ! $LOCAL_INPUT )
	{
	close( STDOUT );
	close( STDERR );
	}

    &cleanup(0);
    }

#########################################################################
#	Return a pointer to a structure from a JSON file.		#
#	Is basically	decode_json( &read_file( $_[0] ) );		#
#########################################################################
sub eval_json
    {
    my $ret;
    my( $fn ) = @_;
    my $file_contents = &read_file( $fn );
    eval { $ret = decode_json( $file_contents ); };
    &autopsy("Cannot evaluate json contents of ${fn}.") if( ! $ret );
    return $ret;
    }

#########################################################################
#	Perl objects have the format $VAR1 = something.  Evaluate named	#
#	file and return it.						#
#########################################################################
sub eval_po
    {
    my( $fn ) = @_;
    my $file_contents = &read_file( $fn );
    my $VAR1;
    eval( $file_contents );
    &autopsy( "Cannot evaluate perl contents of ${fn}.") if( ! $VAR1 );
    return $VAR1;
    }

#########################################################################
#	Make error messages more readable.				#
#########################################################################
sub and_list
    {
    my( @list ) = @_;
    return $list[0] if( scalar(@list) == 1 );
    my $last_item = pop( @list );
    return join(", ",@list) . " and " . $last_item;
    }

#########################################################################
#	Convert a list of progress po files and/or routes to a file	#
#	suitable for display in a format given by the last argument.	#
#	If the last argument is a filename, use its extension to	#
#	determine the output driver. "-.Mapquest" means Mapquest file	#
#	to standard out.						#
#									#
#	By the time we are here, all inputs are thought accessible.	#
#########################################################################
sub pomap
    {
    my( @pomap_args ) = @_;
    my $output = pop( @pomap_args );

    my $output_file;
    my $output_type;

    &setup_mappers_list();
    if( $mappers{$output} )
	{ $output_type=$output; $output_file=undef; }
    elsif( $output =~ /^-\.(.*?)$/ && $mappers{$1} )
	{ $output_type=$1; $output_file="/dev/stdout"; }
    elsif( $output =~ /^(.*)\.(.*?)$/ && $mappers{$2} )
	{ $output_type=$2; $output_file=$output; }
    else
	{ &autopsy("[$output] is not in the correct format."); }

    print STDERR "output=[$output] output_type=[$output_type]\n";

    my @input_ps;
    my @titles;
    my $color_index = 0;
    foreach my $input_thing ( @pomap_args )
	{
	my $input_p;
	print STDERR "Processing [$input_thing]...\n";
	if( $input_thing =~ /(.*)\.po$/ )
	    {
	    print STDERR "Processing po [$input_thing]...\n";
	    $input_p = &eval_po( $input_thing );
	    $input_p->{title} = &progress_title( $input_p );
	    print STDERR "Setting title to [$input_p->{title}]\n";
	    my $progress_file = "$1.progress";
	    if( -r $progress_file )
	        { $input_p->{progress_p} = &decode_progress( &read_file( $progress_file ) ); }
	    elsif( !$input_p->{progress_p} && $input_p->{progress_string} )
	        { $input_p->{progress_p} = &decode_progress( $input_p->{progress_string} ); }
	    }
	else
	    {
	    my $route_ind;
	    if( &rec_type($input_thing,"Route") )
	        { $route_ind = $input_thing; }
	    else
		{
		&DBread();
		$route_ind = &map_name_to_ind( "Route", $input_thing, "" );
		}
	    if( $route_ind )
		{
		print STDERR "Processing route $input_thing ($route_ind).\n";
		$input_p = { "title" => &DBget($route_ind,"Name") . " route" };

		foreach my $stop_ind ( &get_patron_order( $route_ind ) )
		    {
		    my %local_stop = %{$stop{$stop_ind}};
		    push( @{$input_p->{stops}}, \%local_stop );
		    }
		}
	    else
		{
		&autopsy("Do not know how to translate '$input_thing'.");
		}
	    }
	$input_p->{color} = $color_index++;
	push( @input_ps, $input_p );
	push( @titles, $input_p->{title} );
	}
    my $title = &and_list( @titles );

    &DBread();
    print STDERR "mapper name = [ ", $mappers{$output_type}{name}, " ].<br>\n";
    my $res = &{$mappers{$output_type}{progress}}($title,@input_ps);
    &DBpop();

    &write_file( $output_file, $res ) if( $output_file );
    return $res;
    }

#########################################################################
#	Export the specified recs.					#
#########################################################################
sub export_recs
    {
    my( $argp, @inds ) = @_;
    my $tbl = $argp->{table};
    my @field_ptrs = &fields_of( $tbl );
    my @fields = map { $_->{Name} } @field_ptrs;
    # print "setup_eximport tbl=$tbl fields=[",join(",",@fields),"]<br>\n";
    my @toprint = ( join("|",@fields) );
    foreach my $ind ( @inds )
        {
	my @new_vals;
	foreach my $local_fp ( @field_ptrs )
	    {
	    my $local_field_name = $local_fp->{Name};
	    my $display_val;
	    if ( $local_fp->{db} )
		{
		$display_val =
		    join(", ",&list_to_names($ind,$local_field_name));
		}
	    elsif( ! defined($display_val=&DBget($ind,$local_field_name)) )
		{ $display_val = ""; }
	    $display_val =~ s/\r//g;
	    $display_val =~ s/\n/ /gms;
	    push( @new_vals, $display_val );
	    }
	push( @toprint, join("|",@new_vals) );
	}
    &write_file( $argp->{filename}, join("\n",@toprint,"") );
    }

#########################################################################
#	Export the entire database.					#
#########################################################################
sub export_all
    {
    my( $export_dir ) = @_;
    &DBread();
    foreach my $distributor_ind ( &DBget("Distributor") )
        {
	my $prefix = join("/",$export_dir,&filename_of($distributor_ind));
	&echodo("mkdir -p $prefix") if( ! -d $prefix );
	foreach my $tbl ( "Distributor", "Staff", "Route" )
	    {
	    my @inds;
	    if( $tbl eq "Distributor" )
	        { @inds = ( $distributor_ind ); }
	    elsif( $tbl eq "Staff" )
	        { @inds = split(/,/,&DBget($distributor_ind,"Contact") ); }
	    elsif( $tbl eq "Route" )
		{
		@inds = grep(
		    &DBget($_,"Distributor") eq $distributor_ind,
		    &DBget($tbl) );
		foreach my $route_ind ( @inds )
		    {
		    my @patrons =
			grep( &patron_from_route($_,$route_ind), DBget("Patron") );
		    &export_recs({
			table		=> "Patron",
			filename	=> join("/",$prefix,
						&filename_of($route_ind).".psf" )
			}, @patrons );
		    }
		}
	    &export_recs({
	    	table		=> $tbl,
		filename	=> "$prefix/$tbl.psf"
		}, @inds );
	    }
	}
    &DBpop();
    }

#########################################################################
#	Imprt a particular table					#
#########################################################################
sub import_recs
    {
    my( $filename, $tbl ) = @_;
    print STDERR "[Importing $tbl from $filename]\n";

    my @field_ptrs = &fields_of( $tbl );
    #my @fields = map { $_->{Name} } @field_ptrs;
    my @lines = &read_lines( $filename );
    my( @fields ) = split(/\|/,shift(@lines));
    while( @lines )
        {
	my @pieces = split(/\|/,shift(@lines));
	my %record = map {($_,shift @pieces)} @fields;
	my $ind = &map_name_to_ind($tbl,$record{Name},"");
	foreach my $local_fp ( @field_ptrs )
	    {
	    my $local_field_name = $local_fp->{Name};
	    #print STDERR "$local_field_name ptr:  (", Dumper( $local_fp ), ")\n";
	    if( $local_fp->{db} )
		{
		my $oldval = &DBget( $ind, $local_field_name );
	        my %seenid;
		grep( $seenid{$_}=1, split(/,/,$oldval) ) if( $oldval );
		if( $record{$local_field_name} )
		    {
		    foreach my $piece (split(/\s*,\s*/,$record{$local_field_name}))
			{
			$seenid{&map_name_to_ind($local_fp->{db},$piece,"")}=1;
			}
		    }
		$record{$local_field_name} = join(",",sort keys %seenid);
		}
	    &debput( $ind, $local_field_name, $record{ $local_field_name } );
	    }
	}
    }

#########################################################################
#	Import anything in the named directory.				#
#########################################################################
sub import_all
    {
    my( $import_dir ) = @_;
    print STDERR "import_dir=[$import_dir]...\n";
    &DBwrite();
    foreach my $distributor_filename ( &files_in( $import_dir ) )
        {
	print STDERR "df=$distributor_filename.\n";
	my $distributor_name = &filename_to_text( $distributor_filename );
	my $prefix = join("/",$import_dir,$distributor_filename);
	print STDERR "prefix=$prefix.\n";
	my $try_file;
	my @routing_files = &files_in( $prefix, ".psf\$" );
	foreach my $tbl ( "Distributor", "Staff", "Route" )
	    {
	    print STDERR "tbl=[$tbl]\n";
	    &import_recs($try_file,$tbl) if(-e ($try_file="$prefix/$tbl.psf"));
	    @routing_files = grep( $_ ne "$tbl.psf", @routing_files );
	    }
	foreach my $routing_file ( @routing_files )
	    {
	    &import_recs("$prefix/$routing_file","Patron");
	    }
	}
    &DBpop();
    }

#########################################################################
#	We're not a web program.  Triage!				#
#########################################################################
sub non_CGI_handler
    {
    my @problems;
    if( ! defined($ARGV[0]) )
	{ push(@problems,"No arguments specified."); }
    elsif( $ARGV[0] eq "route" )	{ &do_one_route( @ARGV[1..3] );	}
    elsif( $ARGV[0] eq "reindex" )	{ reindex( $ARGV[1] );		}
    elsif( $ARGV[0] eq "print" )	{ dump_indices();		}
    elsif( $ARGV[0] eq "sanity" )	{ sanity();			}
    elsif( $ARGV[0] eq "trip" )		{ &trip_update();		}
    elsif( $ARGV[0] eq "pomap" )	{ &pomap( @ARGV[1..$#ARGV] );	}
    elsif( $ARGV[0] eq "export" )	{ &export_all( $ARGV[1]);	}
    elsif( $ARGV[0] eq "import" )	{ &import_all( $ARGV[1]);	}
    else
	{ push(@problems,"Unknown argument '$ARGV[0]' specified."); }

    &xlfatal("XL(Usage):  $cpi_vars::PROG.cgi (dump|dumpaccounts|dumptranslations|undump|undumpaccounts|undumptranslations) [ dumpname ]")
   	 if( @problems );
    }

#########################################################################
#	Return the top of the page.					#
#########################################################################
sub routing_page_top
    {
    my $jsfile = &read_file($ROUTINGJS);
    $jsfile =~ s+\$FORMNAME+$FORMNAME+g;

    return <<EOF;
<script>
$jsfile
</script>
</head><body $cpi_vars::BODY_TAGS>
$cpi_vars::HELP_IFRAME
<div id=body_id>
<form name=$FORMNAME method=post ENCTYPE="multipart/form-data">
<input type=hidden name=func>
<input type=hidden name=arg>
<input type=hidden name=SID value="$cpi_vars::SID">
<input type=hidden name=USER value="$cpi_vars::USER">
<center>
EOF
    }

#########################################################################
#	Read in all the maps that match the arguments.			#
#########################################################################
my %runs;
sub read_maps
    {
    my %revmap;	# Eww ... thankfully we don't do "Patron"!
    foreach my $tbl ( "Distributor", "Route", "Staff" )
	{
	grep( $revmap{$tbl}{&filename_of($_)} = $_, &DBget( $tbl ) );
	}

    open( INF, "find $PROGRESS_DIR -name '*.po' -print |" ) ||
	&autopsy("Cannot find $PROGRESS_DIR:  $!");
    my( $route_ind, $driver_ind, $distributor_ind );

    my $s4date		= ( $cpi_vars::FORM{date}		|| "" );
    my $s4route		= ( $cpi_vars::FORM{Route}	|| "" );
    my $s4distributor	= ( $cpi_vars::FORM{Distributor}	|| "" );
    my $s4driver	= ( $cpi_vars::FORM{Staff}	|| "" );

    while( $_ = <INF> )
	{
	chomp( $_ );
	my $fn = $_;
	$fn =~ s+^$PROGRESS_DIR/++;
	if( $fn =~ m:(\w+)/(\d\d\d\d-\d\d-\d\d)-(\w+)-(\w+)-(\w+)\.(\w+)$: )
	    {
	    my ( $distributor_file, $date, $route_file, $driver_file, $secret, $ext )
		= ( $1, $2, $3, $4, $5, $6 );

	    if( ($s4date eq "" || $s4date eq $date)

	     && ($route_ind = $revmap{Route}{$route_file})
	     && &i_can(__LINE__,"r","Route",$route_ind)
	     && grep($_ eq $s4route, "",
		$route_ind, $route_file, &DBget($route_ind,"Name") )

	     && ($driver_ind = $revmap{Staff}{$driver_file})
	     && &i_can(__LINE__,"r","Staff",$driver_ind)
	     && grep($_ eq $s4driver, "",
		$driver_ind, $driver_file, &DBget($driver_ind,"Name") )

	     && ($distributor_ind = $revmap{Distributor}{$distributor_file})
	     && &i_can(__LINE__,"r","Distributor",$distributor_ind)
	     && grep($_ eq $s4distributor, "",
		$distributor_ind, $distributor_file,
		    &DBget($distributor_ind,"Name") ) )
		{
		$runs
		    {$distributor_ind}
		    {$date}
		    {$route_ind}
		    {$driver_ind}
		    {$secret}
		    = $ext;
		}
	    }
	}
    close( INF );
    }
    
#########################################################################
#	Return HTML to get to the thing specified in the table.		#
#########################################################################
sub map_entry
    {
    my( $tbl, $ind ) = @_;
    return join("",
	"\n<td><a href='javascript:submit_func(\"$here/Show,",
	$tbl,",",$ind,"\");'>",
	&DBget($ind,"Name"),
	"</a></td>" );
    }

#########################################################################
#	Show all the maps that we read in.				#
#########################################################################
sub list_route_runs
    {
    my ( $tbl, $ind, $date ) = @_;
    #print STDERR "CMC list_route_runs($tbl,$ind,$date)<br>\n";
    $cpi_vars::FORM{$tbl} = $ind if( $tbl && $ind );
    $cpi_vars::FORM{date} = $date;
    &read_maps();

    my @extlist = &router_list();
    my %minmaps_list = map { ($_,$mappers{$_}->{minmaps}) } @extlist;
    my %maxmaps_list = map { ($_,$mappers{$_}->{maxmaps}) } @extlist;
    my @s = (
        $form_top,
	"<script>\n",
	    "var seltext = ['XL(Check route runs to map first)',\n",
	    "    'XL(Check route runs to map or select format to download)'];\n",
	    "var minmaps = ", encode_json( \%minmaps_list ), ";\n",
	    "var maxmaps = ", encode_json( \%maxmaps_list ), ";\n",
	    "window.addEventListener( 'pageshow', maps_list_changed );\n",
	"</script>\n",
	#"<input type=hidden name=tbl value=''>",
	#"<input type=hidden name=ind value=''>",
	"<table border=1 cellspacing=3 cellpadding=3 style='border-collapse:collapse;border:solid;'>\n",
	"<tr><th colspan=6>",
	"<select help='select_route_run_map_format' onChange='javascript:submit_func(\"map_with_custom_header\",this.value);this.selectedIndex=0;'>\n",
	"<option selected disabled id=opt_download_ext>",
	    "XL(Check route runs to map or select format to download)",
	"</option>" );
    foreach my $ext ( @extlist )
	{
	push( @s, "\n<option id=opt_$ext disabled value='$ext'>", $mappers{$ext}{name}, "</option>" );
	}
    push( @s, "</select></td></tr>\n<tr>",
	"<th>Distributor</th>",
	"<th>Date</th>",
	"<th>Route</th>",
	"<th>Driver</th>",
	"<th>Index</th>",
	"<th colspan=",scalar(@extlist),">",
	    "XL(Select)</th>" );

    foreach my $distributor_ind ( &dbsort( keys %runs ) )
        {
	my $distributor_text = &map_entry("Distributor",$distributor_ind);
	foreach my $date ( reverse sort keys %{$runs{$distributor_ind}} )
	    {
	    my $date_text = $distributor_text
		. "\n<td><a href='javascript:submit_func(\"$here,$date\");'>"
		. "$date</a></td>";
	    foreach my $route_ind
		( &dbsort( keys %{$runs{$distributor_ind}{$date}} ) )
	        {
		my $route_text = $date_text . &map_entry("Route",$route_ind);
		foreach my $driver_ind
		    ( &dbsort(keys %{$runs{$distributor_ind}{$date}{$route_ind}} ) )
		    {
		    my $driver_text = $route_text . &map_entry("Staff",$driver_ind);
		    foreach my $secret ( sort keys %{$runs{$distributor_ind}{$date}{$route_ind}{$driver_ind}} )
			{
			my $pretty_secret = ( $secret eq "XXXXXX" ? "" : $secret );
			my $secret_text = $driver_text . "<td>$pretty_secret</td>";
			push( @s, "</tr>\n<tr>", $secret_text );
			push( @s, "\n<th><input type=checkbox help='select_route_runs_to_map' name=maps value='${distributor_ind}:${route_ind}:${driver_ind}:${date}:${secret}' onChange='maps_list_changed();'></th>" );
			}
		    }
		}
	    }
	}
    push( @s, "</tr></table></center></form>\n" );
    &xprint( @s );
    &footer( $tbl );
    }

#########################################################################
#	Allow user to download the file, converting as needed.		#
#	$arg is the format (typically Mapquest), a known mapping	#
#	file extension of mappers.					#
#########################################################################
sub dump_map
    {
    my ( $arg ) = @_;

    my @input_routes;
    my @input_po_files;
    my %distributor_files;
    my %route_files;
    my %driver_files;
    my %dates;
    my @list_of_maps;
    my $ext;

    if( $arg =~ /[,:]/ )
        {
	my @args = split( /[,:]/, $arg );	# commas are for backwards compatibility
	$ext = pop( @args );
	push( @list_of_maps, join(":",@args) );	# Force it to be colons
	}
    else
    	{
	$ext = $arg;
	@list_of_maps = split(/,/,$cpi_vars::FORM{maps});
	}

    # By the time we are here, $ext contains what we're going to output
    # and @list_of_maps consists either of filenames containing route runs
    # or route indices themselves (e.g. "R_xxx").

    &setup_mappers_list();
    foreach my $input_piece ( @list_of_maps )
	{
	if( &rec_type($input_piece,"Route") )
	    {
	    my $route_ind = $input_piece;	# Let's use a better name
	    if( $cpi_vars::ANONYMOUS || &i_can(__LINE__,"r","Route",$route_ind) )
		{
		push( @input_routes, $route_ind );
		$route_files{&filename_of($route_ind)} = 1;
		$distributor_files{&filename_of(&DBget($route_ind,"Distributor"))}=1;
		}
	    }
	else
	    {
	    my($distributor_ind,$route_ind,$driver_ind);
	    my $date = "*";
	    my $secret = "*";
	    foreach my $str ( split(/:/,$input_piece) )
		{
		my $strectype = &rec_type( $str );
		if( $strectype eq "Distributor" )	{ $distributor_ind=$str; }
		elsif( $strectype eq "Staff" )		{ $driver_ind=$str; }
		elsif( $strectype eq "Route" )		{ $route_ind=$str; }
		elsif( $str =~ /^\d\d\d\d-\d\d-\d\d$/ )	{ $date=$str; }
		else					{ $secret=$str; }
		}
	    #print "dump_map($distributor_ind,$driver_ind,$route_ind,$date)<br>\n";
	    my $can_do;
	    $can_do ||= $cpi_vars::ANONYMOUS;	# CMC clearly THIS is wrong
	    $can_do ||=
		(   &i_can(__LINE__,"r","Distributor",$distributor_ind)
		 && &i_can(__LINE__,"r","Staff",$driver_ind)
		 && &i_can(__LINE__,"r","Route",$route_ind) );
	    if( $can_do )
		{
		my $distributor_file = &filename_of($distributor_ind);
		$distributor_files{$distributor_file} = 1;
		my $route_file = &filename_of($route_ind);
		$route_files{$route_file} = 1;
		my $driver_file = &filename_of($driver_ind);
		$driver_files{$driver_file} = 1;
		$dates{$date} = 1;
		my $fn =
		    sprintf("%s/%s/%s-%s-%s-%s.po",
			$PROGRESS_DIR,$distributor_file,$date,$route_file,$driver_file,$secret);
		if( ! -r $fn )
		    {
		    $fn = (glob( $fn )) [ 0 ];	# Just use first file that matches
		    }
		push( @input_po_files, $fn );
		}
	    }
	}
    print "Content-type:  ", $mappers{$ext}{mime}, "\n";
    my @filename_pieces;
    push( @filename_pieces, join(",",sort keys %dates) )
	if( %dates );
    #push( @filename_pieces, join(",",sort keys %distributor_files ) )
	#if( %distributor_files );
    push( @filename_pieces, join(",",sort keys %route_files ) )
	if( %route_files );
    push( @filename_pieces, join(",",sort keys %driver_files ) )
	if( %driver_files );
    print
	"Content-disposition:  attachment; filename=\"",
	join( "-", @filename_pieces ),
	".", $mappers{$ext}{destext}, "\"\n"
	if( ! $mappers{$ext}{tobrowser} );
    #print "\n", ( $ext eq "json" ? &read_file($fn) : &pomap( @input_po_files, $ext ) );

    # If we are here, @input_po_files contains list of .pos that contain route runs
    # that we want to map, and @input_routes contains list of routes that we want
    # to map.  For now, just hope pomap knows the difference.
    print "\n", &pomap( @input_routes, @input_po_files, $ext );
    }

#########################################################################
#	Go see if the PO file exists, and if so, make HTML out of it.	#
#########################################################################
sub watch_a_route
    {
    my( $form_arg ) = @_;
    my( $distributor, $route, $driver, $date_driven ) = split(/,/,$form_arg);
    my( $fn ) = join('/',
	$PROGRESS_DIR,
	$distributor,
	$driver,
	"$date_driven-$route.po");
    &pomap( $fn, $DEFAULT_ROUTER );
    &cleanup(0);
    }

#########################################################################
#	Skim through database making sure that each route and patron	#
#	has a distributor, and perhaps take action to fix.		#
#########################################################################
sub sanity
    {
    my( $fix_flag ) = @_;
    my $ret = 1;

    my %route_map;
    my %bad_route_refs;
    my %confused_patron_routes;
    my @distributorless_patrons;
    my @old_new_patrons;
    my %set_patron_dist;
    my @patrons_without_coords;
    my @bad_routes;
    my $total_routes = 0;
    my $total_patrons = 0;

    &DBread();

    foreach my $route_ind ( &DBget("Route") )
	{
	my $dist = &DBget($route_ind,"Distributor");
	if( ! $dist )
	    { push( @bad_routes, $route_ind ); }
	else
	    {
	    $route_map{$route_ind} = $dist;
	    $total_routes++;
	    }
	}

    foreach my $patron_ind ( &DBget("Patron") )
	{
	my $coords = DBget( $patron_ind, "Coords" );
	push( @patrons_without_coords, $patron_ind )
	    if( ! $coords || $coords !~ /,/ );

	my $guess_dist;
	my $guess_route;
	my $route_string = &DBget($patron_ind,"Route");
	if( $route_string )
	    {
	    foreach my $route_ind ( split( /,/, $route_string ) )
		{
		if( ! $route_map{$route_ind} )
		    { push( @{$bad_route_refs{$patron_ind}}, $route_ind ); }
		else
		    {
		    if( ! $guess_dist )
			{ $guess_dist = $route_map{$guess_route=$route_ind}; }
		    elsif( $guess_dist ne $route_map{$route_ind} )
			{
			$confused_patron_routes{$patron_ind}{$guess_route}
			    = $guess_dist;
			$confused_patron_routes{$patron_ind}{$route_ind}
			    = $route_map{$route_ind};
			}
		    }
		}
	    }
	my $old_dist = &DBget($patron_ind,"Distributor");
	if( ! $guess_dist )
	    {
	    if( ! $old_dist )
		{ push( @distributorless_patrons, $patron_ind ); }
	    }
	elsif( ! $old_dist )
	    { $set_patron_dist{$patron_ind} = $guess_dist; }
	elsif( $guess_dist ne $old_dist )
	    { push( @old_new_patrons, "${patron_ind}'s $guess_dist vs $old_dist" ); }
	$total_patrons++;
	}

    my @s = (
	"<center>",
    	"<table border=1 cellspacing=1 cellpadding=5 style='border-collapse:collapse;border:solid;'>",
	"<tr><th align=left>XL(Routes out of) ${total_routes} XL(with no distributors):</th>",
    		"<td>", ( @bad_routes ? join(" ",@bad_routes) : "NONE" ),
		"</td></tr>\n",
	"<tr><th align=left>XL(Patrons out of) $total_patrons XL(with non-existant routes):</th>",
    		"<td>" );
    if( ! %bad_route_refs )
    	{ push( @s, "NONE" ); }
    else
    	{
	foreach my $patron_ind ( keys %bad_route_refs )
	    {
	    push( @s, $patron_ind, ": ",
	        join(" ",@{$bad_route_refs{$patron_ind}}), "<br>\n" );
	    }
	}
    push( @s, "</td></tr>\n",
	"<tr><th align=left>XL(Patrons with routes from multipe distributors):</th>",
        "<td>" );
    if( ! %confused_patron_routes )
        { push( @s, "NONE" ); }
    else
        {
	foreach my $patron_ind ( keys %confused_patron_routes )
	    {
	    push( @s, $patron_ind, ": ",
	        ( map { "$_/$confused_patron_routes{$patron_ind}{$_}" }
		    keys %{$confused_patron_routes{$patron_ind}} ),
		"<br>" );
	    }
	}

    push( @s, "<tr><th align=left>XL(Patrons that we cannot figure out distributors):</th>",
        "<td>",
	( @distributorless_patrons ? join(" ",@distributorless_patrons) : "NONE" ),
	"</td></tr>\n",
    "<tr><th align=left>XL(Patrons where guessed distributor is not set distributor):</th>",
        "<td>",
        ( @old_new_patrons ? join("<br>",@old_new_patrons) : "NONE" ),
	"</td></tr>\n",
    "<tr><th align=left>XL(Patrons to update distributor):</th>",
        "<td>",
	( %set_patron_dist
	    ? ( map { " $_=$set_patron_dist{$_}" } keys %set_patron_dist )
	    : "NONE" ),
	"</td></tr>\n",
    "<tr><th align=left>XL(Patrons without coordinates):</th>",
    		"<td>", scalar(@patrons_without_coords), "</td></tr>\n" );

    my %writes;
    %writes = &geocode_ids(@patrons_without_coords)
	if( @patrons_without_coords );
    &DBpop();

    if(	@bad_routes
     ||	%bad_route_refs
     ||	%confused_patron_routes
     ||	@distributorless_patrons
     ||	@old_new_patrons )
	{
	push( @s, "<tr><th colspan=2>XL(No patrons updated due to errors)</th></tr>\n" );
	$ret = 0;
	}
    elsif( scalar(%set_patron_dist)==0 && scalar(%writes)==0 )
        {
	push( @s, "<tr><th colspan=2>XL(No patron updates for Distributor or Coords required.)</th></tr>\n" );
	}
    elsif( ! $fix_flag )
    	{
	push( @s, "<tr><th colspan=2>",
	    "XL(Distributions for) ",
	    &nword("patron",scalar(%set_patron_dist)),
	    " XL(and Coordinates for) ",
	    &nword("patron",scalar(%writes)),
	    " XL(to update.)",
	    "</th></tr>\n" );
	}
    else
	{
	&DBwrite();
	grep( &DBput($_,"Distributor",$set_patron_dist{$_}),
	    keys %set_patron_dist );
	grep( &DBput($_,"Coords",$writes{$_}),
	    keys %writes );
	&DBpop();
	push( @s, "<tr><th colspan=2>",
	    "XL(Distributions for) ",
	    &nword("patron",scalar(%set_patron_dist)),
	    " XL(and Coordinates for) ",
	    &nword("patron",scalar(%writes)),
	    " XL(updated.)",
	    "</th></tr>\n" );
	}
    push( @s, "</table></center>" );
    &xprint( @s );
    return $ret;
    }

#########################################################################
#	Read costs in from a square matrix.				#
#	Note these won't be readable as both the width and height will	#
#	be the number of patrons to route.				#
#########################################################################
my %costs;
sub read_costs
    {
    my( $fname ) = @_;
    if( ! -f $fname )
        { %costs = (); }
    elsif( $fname =~ /\.po$/ )
        { eval( &read_file( $fname ) ); }
    else
        {
	open( INF, $fname ) || &autopsy("Cannot read ${fname}:  $!");
	my $line = <INF>;
	chomp( $line );
	my( $noise, @coords_x ) = split(/\s+/,$line);
	while( $line = <INF> )
	    {
	    chomp( $line );
	    my ( $coord_y, @toks ) = split(/\s+/,$line);
	    foreach my $coord_x ( @coords_x )
	        { $costs{$coord_x,$coord_y} = shift( @toks ); }
	    }
	close( INF );
	}
    }

#########################################################################
#	Write costs out to a square matrix.				#
#########################################################################
sub write_costs
    {
    my( $fname, @coords ) = @_;
    if( $fname =~ /\.po$/ )
        {
	&write_file( $fname, Data::Dumper->Dump( [\%costs], [ '*costs' ] ) );
	}
    else
	{
	if( ! @coords )
	    {
	    my %seen_coord;
	    my @hashinds = keys %costs;
	    s/$;.*// foreach @hashinds;
	    grep( $seen_coord{$_}=1, @hashinds );
	    @hashinds = keys %costs;
	    s/.*$;// foreach @hashinds;
	    grep( $seen_coord{$_}=1, @hashinds );
	    @coords = keys %seen_coord;
	    }
	open( OUT, ">$fname" ) || &autopsy("Cannot write ${fname}:  $!");
	print OUT join(" ","-",@coords),"\n";
	foreach my $c ( @coords )
	    {
	    print OUT join(" ",$c,(map { defined($costs{$c,$_})?$costs{$c,$_}:"?" } @coords)), "\n";
	    }
	}
    }

#########################################################################
#	Get the costs.  Read in info if available, but otherwise, we	#
#	have to go ask Mapquest.					#
#########################################################################
my %required_coords_patrons;
our $cost_origin;
my $MAX_COSTS_SIZE = 75;
sub get_costs
    {
    my( $fname, $distind ) = @_;
    &read_costs( $fname );

    # Create a list of patrons that we need to create routes for
    my @required_patrons =
        grep (  &DBget($_,"Distributor") eq $distind &&
		&DBget($_,"Status") eq "Active", &DBget("Patron") );

    # Create a hash of arrays indexed by coordinates of all those patrons
    my %required_costs_patrons;
    foreach my $patron_ind ( @required_patrons )
        {
	push( @{ $required_coords_patrons{ &DBget($patron_ind, "Coords") } },
	    $patron_ind )
	}
    # Add in the distributor's coordinates (doh!)
    push( @{ $required_coords_patrons{ &DBget($distind, "Coords") } },
        $distind );

    # For each coordinate that we care about, check to see if we know the
    # cost to every other coordinate, putting together a list of coordinates
    # that we need costs for and then batching reqests to get that information.
    my @required_coords = keys %required_coords_patrons;
    my $counter = 0;
    foreach $cost_origin ( @required_coords )
	{
	if( my @cost_origin_list =
	    grep( ! defined( $costs{$cost_origin,$_} ),
	        @required_coords ) )
	    {
	    print "counter=$counter.<br>\n";
	    my $cost_ind = 0;
	    foreach my $cost
		( &batch(\&costs_batch, $MAX_COSTS_SIZE, @cost_origin_list) )
	        {
		#print "Setting $cost_origin and $cost_origin_list[$cost_ind] to $cost.\n";
		$costs{ $cost_origin, $cost_origin_list[$cost_ind] } = $cost;
		$costs{ $cost_origin_list[$cost_ind], $cost_origin } = $cost;
		$cost_ind++;
		}
	    #last if( $counter++ >= 3 );
	    }
	}
    }

#########################################################################
#	Makes sure %costs variable is up to date.  Basically just	#
#	an easy way of calling get_costs and write_costs with correct	#
#	extensions.							#
#########################################################################
sub update_costs
    {
    my( $filebase, $distind ) = @_;
    #&get_costs( $filebase.".po", $distind );
    &get_costs( $filebase.".tbl", $distind );
    &write_costs( $filebase.".tbl" );
    &write_costs( $filebase.".po" );
    return 1;
    }

#########################################################################
#	Print out a table to hand off to mesh.pl.			#
#########################################################################
sub print_table
    {
    my( $filename, @data ) = @_;
    my @fields;
    while( $data[0] && $data[0] !~ /^\w_/ )
        { push( @fields, shift(@data) ); }
    open( OUT, "> $filename" ) || &autopsy("Cannot write ${filename}:  $!");
    print OUT join("\t","Id",@fields),"\n";
    foreach my $checkind ( @data )
	{
	print OUT $checkind;
	foreach my $f ( @fields )
	    {
	    my $v = &DBget( $checkind, $f );
	    $v = "" if( ! defined($v) );
	    $v =~ s/\s+/_/g;
	    print OUT "\t", ( ( $v =~ /^_*$/ ) ? "*" : $v );
	    }
	print OUT "\n";
	}
    close( OUT );
    }

#########################################################################
#	Create the datasets for a hard problem - redistributing patrons	#
#	across all the drivers for this distributor.			#
#########################################################################
sub rebalance_routes
    {
    my( $tbl, $distind, @rest ) = @_;
    my $filebase="$COSTSDIR/".&filename_of($distind,"Name");
    if( &sanity( 1 ) && &update_costs( "${filebase}_costs", $distind ) )
	{
	my @s = (
	    "<center>",
	    "<table border=1 cellspacing=1 cellpadding=5 style='border-collapse:collapse;border:solid;'>",
		"<tr><th colspan=2>XL(Redistribution of patrons over drivers for) ",
		    &DBget($distind,"Name"), "</th></tr>\n");
	&print_table( "${filebase}_distributor.txt",
	    "Coords", "Name", "Address",
	    $distind );

	my @staff =
	    grep( &DBget($_,"Distributor") eq $distind,
		&DBget("Staff") );
	&print_table( "${filebase}_staff.txt",
	    "Maximum_Patrons", "Weight_limit", "Times_available",
	    "Notify", "Email", "Phone", "Name",
	    @staff );
	push( @s, "<tr><th align=left>Drivers:</th>",
	    "<td align=right>", scalar(@staff), "</td></tr>\n" );

	my @patrons =
	    grep(
		&DBget($_,"Distributor") eq $distind
	     && &DBget($_,"Status") eq "Active",
	        &DBget("Patron"));
	&print_table( "${filebase}_patrons.txt",
	    "Times_receiving", "Coords", "Status", "Address", "Name",
	    @patrons );
	push( @s, "<tr><th align=left>Patrons:</th>",
	    "<td align=right>", scalar(@patrons), "</td></tr>\n" );
	push( @s, "</table>\n" );
	&xprint( @s );
	}
    &footer( $tbl );
    }

#########################################################################
#	Escape meta characters before splitting.			#
#########################################################################
sub dumb_split
    {
    my( $delimeter, $tosplit ) = @_;
    $delimeter =~ s/([\(\)\+\[\]\$\|\.\*\\])/\\$1/g;
    return split( $delimeter, $tosplit );
    }

#########################################################################
#	Trying to make sure the port files only have what is		#
#	interesting in them.  In this case, we can create a servicable	#
#	port variable from whole cloth!					#
#########################################################################
sub setup_eximport
    {
    my( $distind, $tbl ) = @_;
    my %eximport =
        (
	record_separator	=>	"\n",
	field_separator		=>	"|",
	dir	=>	$DISTRIBUTOR_DIR."/".&filename_of($distind,"Name"),
	lookup	=>	sub
	    {
	    my ( %record ) = @_;
	    my $res = &map_name_to_ind("Patron",$record{Name});
	    # print "lookup($record{Name}) returns [$res].<br>\n";
	    return $res;
	    }
	);
    my $eipp = \%eximport;

    eval( &read_file( "$eipp->{dir}/eximport.pl" ) )
	if( -r "$eipp->{dir}/eximport.pl" );

    if( ! $eipp->{field_list} )
        {
	my @field_ptrs = &fields_of( $tbl );
	my @fields = map { $_->{Name} } @field_ptrs;
	# print "setup_eximport tbl=$tbl fields=[",join(",",@fields),"]<br>\n";
	$eipp->{field_list} = [ map { {local=>$_,remote=>$_} } @fields ];
	}

    # Make it so we don't have to access field information by field number
    # but can use its name.  Would do this at the beginning of time except
    # it is only used for importing and exporting, at least so far.
    foreach my $tbl ( %TABLE_FIELDS )
        {
	grep( $TABLE_FIELDS{$tbl}{$_->{Name}}=$_,
	    @{$TABLE_FIELDS{$tbl}{fields}} );
	}

    #&write_file( $eipp->{dir}."/eximport.dump", Dumper( $eipp ) );

    return $eipp;
    }

#########################################################################
#	DBput for debugging import_patrons.				#
#########################################################################
sub debput
    {
    my( $ind, $fld, $val ) = @_;
    print STDERR __LINE__, ":  ind=$ind fld=$fld val=[",($val||"UNDEF"),"].\n";
    return &DBput( $ind, $fld, $val );
    }

#########################################################################
#	Receive a file from the distributor source (probably Wellsky).	#
#	The format of this file is as of yet unknown.			#
#########################################################################
sub import_patrons
    {
    my( $argtbl, $ind, $format ) = @_;
    my $distind;
    my $routeind;

    if( $argtbl eq "Distributor" )
        {
	$distind = $ind;
	}
    elsif( $argtbl eq "Route" )
        {
	$distind = &DBget( $ind, "Distributor" );
	$routeind = $ind;
	}
    my $tbl = "Patron";
    my $eipp = &setup_eximport( $distind, $tbl );

    my $contents = $cpi_vars::FORM{file_contents};

    # We do this in memory, but it's nice to have a copy
    &write_file( $eipp->{dir}."/import", $contents );

    %porting = &get_drivers( $PORTING_DIR ) if( ! %porting );
    my $distname = &DBget( $distind, "Name" );
    my $routename = ( $routeind ? &DBget( $routeind, "Name" ) : "" );
    $contents = &{ $porting{$format}{importer} }( $contents, $distname, $routename )
        if( $porting{$format}{importer} );

    $contents =~ s/\r//gms;
    my( @records ) =
	&dumb_split( $eipp->{record_separator}, $contents );
    my( @remote_field_names ) =
	&dumb_split( $eipp->{field_separator}, shift(@records) );
#	map { $eipp->{field_list}[$_]{remote} }
#		@{$eipp->{field_list}};
    my $recs_uploaded = 0;

    &DBwrite();
    while( my $rec_string = shift(@records) )
        {
	my @field_vals = &dumb_split( $eipp->{field_separator}, $rec_string );
	my %record = map { ( $_, shift(@field_vals) ) } @remote_field_names;
	my $ind = &{$eipp->{lookup}}( %record );
	if( $ind )
	    {
	    print STDERR "lookup($record{Name}) returned $ind (updating).\n";
	    }
	else
	    {
	    &DBadd( $tbl, $ind=&new_tagged_key( $tbl ) );
	    print STDERR "lookup($record{Name}) added $ind to $tbl.\n";
	    }
	foreach my $fp ( @{ $eipp->{field_list} } )
	    {
	    if( $fp->{import_func} )
	        { &{$fp->{import_func}}( $ind, $record{ $fp->{remote} } ); }
	    elsif( my $local_fp = $TABLE_FIELDS{$tbl}{$fp->{local}} )
		{
		if( ! $local_fp->{db} )
		    { &debput( $ind, $fp->{local}, $record{ $fp->{remote} } ); }
		else
		    {
		    if( $local_fp->{db} eq "Distributor" && $distind )
		        { &debput( $ind, $fp->{local}, $distind ); }
		    elsif( $local_fp->{db} eq "Route" && $routeind )
		        { &debput( $ind, $fp->{local}, $routeind ); }
		    else
			{
		        my %seenid;
			my $oldval = &DBget( $ind, $fp->{local} );
			grep( $seenid{$_}=1, split(/,/,$oldval) ) if( $oldval );
			if( $record{$fp->{remote}} )
			    {
			    foreach my $piece (split(/\s*,\s*/,$record{$fp->{remote}}))
				{
				if( $local_fp->{db} eq "Distributor" && $distind )
				    { $piece = $distind; }
				elsif( $local_fp->{db} eq "Route" && $routeind )
				    { $piece = $routeind; }
				else
				    { $piece = &map_name_to_ind( $local_fp->{db}, $piece, "" ); }
				$seenid{$piece}=1;
				}
			    }
			&debput( $ind, $fp->{local}, join(",",sort keys %seenid) );
			}
		    }
		}
	    else
	        {
		print "Do not know how to import [$fp->{local}].<br>\n";
		}
	    }
	$recs_uploaded++;
	}
    &DBpop();
    return"$recs_uploaded records of width ". scalar(@remote_field_names). " uploaded.";
#    &show_record(
#	msg=>"$recs_uploaded records of width ". scalar(@remote_field_names). " uploaded.",
#	tbl=>$tbl,
#	ind=>$distind,
#	editmode=>0 );
    }

#########################################################################
#	Create a file from the distributor source.			#
#########################################################################
sub export_with_custom_header
    {
    my( $argtbl, $ind, $format ) = @_;

    my $routeind;
    my $distind;
    my @patrons;

    my $export_file = "/var/log/routing/export.$format";
    my $export_html = "/var/log/routing/export.html";
    #print "Content-type:  text/plain\n\nArgs:  ",join(", ",@_), "\n\n";

    if( $argtbl eq "Distributor" )
        {
	$distind = $ind;
	@patrons = &patrons_of_distributor( $distind );
	#print __LINE__, ": Distributor [",join(",",@patrons),"]\n";
	}
    elsif( $argtbl eq "Route" )
    	{
	$routeind = $ind;
	@patrons = &patrons_on( $routeind );
	$distind = &DBget( $routeind, "Distributor" );
	#print __LINE__, ": Route [",join(",",@patrons),"]\n";
	}
    else
        {
	print __LINE__, ": Unknown argtbl = [$argtbl]\n";
	}

    my $tbl = "Patron";
    my $eipp = &setup_eximport( $distind, $tbl );

    my @remote_field_names = map { $_->{remote} } @{$eipp->{field_list}};
    my @records = ( join( $eipp->{field_separator}, @remote_field_names ) );

    foreach my $ind ( @patrons )
	{
	my @new_vals;
	foreach my $fp ( @{ $eipp->{field_list} } )
	    {
	    my $local_field_name = $fp->{local};
	    if( $fp->{export_func} )
		{ push( @new_vals, &{$fp->{export_func}}($ind) ); }
	    elsif( my $local_fp = $TABLE_FIELDS{$tbl}{$local_field_name} )
		{
		my $display_val;
		if ( $local_fp->{db} )
		    {
		    $display_val =
			join(", ",&list_to_names($ind,$local_field_name));
		    }
		elsif( ! defined($display_val=&DBget($ind,$local_field_name)) )
		    { $display_val = ""; }
		$display_val =~ s/\r//g;
		$display_val =~ s/\n/ /gms;
		push( @new_vals, $display_val );
		}
	    else
		{ &autopsy("No $local_field_name in $tbl."); }
	    }
	push( @records, join( $eipp->{field_separator}, @new_vals ) );
	}
    my $contents = join( $eipp->{record_separator}, @records, "" );
    my $remote_name = &filename_of( $distind )
        . ( $routeind ? "_".&filename_of($routeind) : "" )
	. ".$format";
    if( $format eq "psf" )
	{
	print
	    "Content-type:  text/plain\n",
	    "Content-disposition:  attachment; filename=\"$remote_name\"\n\n",
	    $contents;
	}
    else
        {
	%porting = &get_drivers( $PORTING_DIR ) if( ! %porting );
        if( $porting{$format}{exporter} )
	    { print &{ $porting{$format}{exporter} }( $contents ); }
	else
	    {
	    my $TABLE_FUN="SCRIPT_NAME='' SCRIPT_FILENAME='' /usr/local/bin/table_fun";
	    my @table_formats = &read_lines( "$TABLE_FUN -show=outputs |" );
	    print "Content-type:  ", &mime_string( $export_file ), "\n\n";
	    my $cmd = "$TABLE_FUN -it=psf" .
		( &inlist( $format, @table_formats )
		? " -ot=$format"
		: " -of=$export_html; /usr/local/bin/nene $export_html $export_file; cat $export_file" );
	    open( OUT, "| $cmd" ) || &autopsy("Cannot write to pipe ${cmd}:  $!");
	    print OUT $contents;
	    close( OUT );
	    }
	}
    &cleanup(0);
    }

#########################################################################
#	We've decided we're a web program.  Triage!			#
#########################################################################
sub CGI_handler
    {
    &authenticate()
	if( $cpi_vars::USER eq "anonymous" 
	 && $cpi_vars::FORM{func} ne "map_with_custom_header"
	 && $cpi_vars::FORM{func} ne "anonymous_new_form" );
    #&show_vars()
        #if( ! &inlist(($cpi_vars::FORM{func}||""),"download","view") );

    #print "Content-type:  text/html\n\nFORM=$cpi_vars::FORM{USER} USER=$cpi_vars::USER.<br>";
    $cpi_vars::USER ||= "anonymous";
    $form_top = &routing_page_top();

    if( $cpi_vars::FORM{watch} )
	{ &watch_a_route( $cpi_vars::FORM{watch} ); }
    elsif( $cpi_vars::FORM{route_status_edit} )
	{ &trip_update(); }
    elsif( $cpi_vars::FORM{func} eq "dologin" )
	{ &interactive_handler( undef, () ); }
    else
	{
	&interactive_handler( undef, split(/\//,($cpi_vars::FORM{func}||"") ) );
	}
    }

#########################################################################
#	Main								#
#########################################################################

$Data::Dumper::Sortkeys = 1;
if( ! defined($ENV{SCRIPT_NAME}) || $ENV{SCRIPT_NAME} eq "" )
    { &non_CGI_handler(); }
elsif( $ENV{SCRIPT_NAME}!~/.*-test/ && -r $DISABLED )
    { print &read_file( $DISABLED ); }
else
    { &CGI_handler(); }
&cleanup(0);
