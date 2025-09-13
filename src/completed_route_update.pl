#!/usr/local/bin/perl -w
#@HDR@	$Id$
#@HDR@		Copyright 2024 by
#@HDR@		Christopher Caldwell/Brightsands
#@HDR@		P.O. Box 401, Bailey Island, ME 04003
#@HDR@		All Rights Reserved
#@HDR@
#@HDR@	This software comprises unpublished confidential information
#@HDR@	of Brightsands and may not be used, copied or made available
#@HDR@	to anyone, except in accordance with the license under which
#@HDR@	it is furnished.

use strict;
use MIME::Lite;
use JSON;

my $PROJECT = "MOW";
my $PROG = ( $_=$0, s+.*/++g, s/\..*//, $_ );
my $LOGDIR = "/var/log/$PROG";
my $DOMAIN = "Brightsands.com";
my %DEFAULT_HEADER =
    (
    "from"	=> "Meals on Wheels route update <$PROJECT\@$DOMAIN>",
    "to0"	=> "dalward\@seniorsplus.org",
    "to1"	=> "treed\@spectrumgenerations.org",
    "to"	=> "dufflerpud\@yahoo.com",
    "subject"	=> "Meals on Wheels route update"
    );

my %COLORS =
    (
    "Untouched"	=> "white",
    "Unvisited"	=> "#ffffd0",
    "Skipped"	=> "#d0e8ff",
    "Problems"	=> "#ffd0d0",
    "Issues"	=> "#ffff00",
    "Normal"	=> "#d0ffd0"
    );
my $SENDMAIL = "/usr/lib/sendmail";

my @DAY_NAMES = ("Sun","Mon","Tue","Wed","Thu","Fri","Sat");

my $LOCAL_INPUT = 0;
my $LOCAL_OUTPUT = 0;

my %header;

#########################################################################
#	Print a header if need be.					#
#########################################################################
my $hdrcount = 0;
sub CGIheader
    {
    print "Content-type:  text/html\n\n" if( $hdrcount++ == 0 );
    }

#########################################################################
#	Print an error message and die.					#
#########################################################################
sub fatal
    {
    &CGIheader if( $ENV{SCRIPT_NAME} );
    print join("\n",@_,"");
    exit(1);
    }

#########################################################################
#	Put <form> information into %FORM (from STDIN or ENV).		#
#########################################################################
my %FORM;
sub CGIreceive
    {
    my ( $name, $value );
    my ( @fields, @ignorefields, @requirefields );
    my ( @parts );
    my $incoming = "";
    return if ! defined( $ENV{'REQUEST_METHOD'} );
    if ($ENV{'REQUEST_METHOD'} eq "POST")
	{
        read(STDIN, $incoming, $ENV{'CONTENT_LENGTH'});
	}
    else
	{
        $incoming = $ENV{'QUERY_STRING'};
	}
    
    if( defined($ENV{"CONTENT_TYPE"}) &&
        $ENV{"CONTENT_TYPE"} =~ m#^multipart/form-data# )
	{
	my $bnd = $ENV{"CONTENT_TYPE"};
	$bnd =~ s/.*boundary=//;
	foreach $_ ( split(/--$bnd/s,$incoming) )
	    {
	    if( /^[\r\n]*[^\r\n]* name="([^"]*)"[^\r\n]*\r*\nContent-[^\r\n]*\r*\n\r*\n(.*)[\r]\n/s )
		{
		#### Skip generally blank fields
		next if ($2 eq "");

		#### Allow for multiple values of a single name
		$FORM{$1} .= "," if ($FORM{$1} ne "");

		$FORM{$1} .= $2;

		#### Add to ordered list if not on list already
		push (@fields, $1) unless (grep(/^$1$/, @fields));
		}
	    elsif( /^[\r\n]*[^\r\n]* name="([^"]*)"[^\r\n]*\r*\n\r*\n(.*)[\r]\n/s )
		{
		#### Skip generally blank fields
		next if ($2 eq "");

		#### Allow for multiple values of a single name
		$FORM{$1} .= "," if (defined($FORM{$1}) && $FORM{$1} ne "");

		$FORM{$1} .= $2;

		#### Add to ordered list if not on list already
		push (@fields, $1) unless (grep(/^$1$/, @fields));
		}
	    }
	}
    else
	{
	foreach ( split(/&/, $incoming) )
	    {
	    ($name, $value) = split(/=/, $_);

	    $name  =~ tr/+/ /;
	    $value =~ tr/+/ /;
	    $name  =~ s/%([A-F0-9][A-F0-9])/pack("C", hex($1))/gie;
	    $value =~ s/%([A-F0-9][A-F0-9])/pack("C", hex($1))/gie;

	    #### Strip out semicolons unless for special character
	    $value =~ s/;/$$/g;
	    $value =~ s/&(\S{1,6})$$/&$1;/g;
	    $value =~ s/$$/ /g;

	    #$value =~ s/\|/ /g;
	    $value =~ s/^!/ /g; ## Allow exclamation points in sentences

	    #### Split apart any directive prefixes
	    #### NOTE: colons are reserved to delimit these prefixes
	    @parts = split(/:/, $name);
	    $name = $parts[$#parts];
	    if (grep(/^require$/, @parts))
		{
		push (@requirefields, $name);
		}
	    if (grep(/^ignore$/, @parts))
		{
		push (@ignorefields, $name);
		}
	    if (grep(/^dynamic$/, @parts))
		{
		#### For simulating a checkbox
		#### It may be dynamic, but useless if nothing entered
		next if ($value eq "");
		$name = $value;
		$value = "on";
		}

	    #### Skip generally blank fields
	    next if ($value eq "");

	    #### Allow for multiple values of a single name
	    $FORM{$name} .= "," if( defined($FORM{$name}) && $FORM{$name} ne "");
	    $FORM{$name} .= $value;

	    #### Add to ordered list if not on list already
	    push (@fields, $name) unless (grep(/^$name$/, @fields));
	    }
	}
    }

#########################################################################
#	Send e-mail to the specified destination.  Knows how to send	#
#	attachments.							#
#########################################################################
sub html_to_sendmail
    {
    my( $src, $dest, $subject, $msg ) = @_;

    my $mime_msg = MIME::Lite->new
	( 
	From    => $src,
	To      => $dest,
	Subject => $subject,
	Type    => 'multipart/mixed',
	);

    my $msg_type;
    my $cid_ctr = 0;
    my %fn_to_cid = ();

    if( $msg !~ /<\/.*>/ )
        { $msg_type = "TEXT"; }
    else
        {
	my @msg_parts = ();
	$msg_type = "text/html";
	foreach my $mpart ( split(/("cid:.*?")/, $msg ) )
	    {
	    if( $mpart !~ /"cid:(.*)"/ )
	        { push( @msg_parts, $mpart ); }
	    else
	        {
		my $fn = $1;
		if( ! defined($fn_to_cid{$fn}) )
		    {
		    $fn_to_cid{$fn} = sprintf("%x-%x",$$,++$cid_ctr);
		    $fn_to_cid{$fn} .= ".$1" if( $fn =~ /\.(\w*)$/ );
		    }
		push( @msg_parts, "\"cid:$fn_to_cid{$fn}\"" );
		}
	    }
	$msg = join("", @msg_parts );
	}
    
    $mime_msg->attach
        (
	Type	=> $msg_type,
	Data	=> $msg
	) || die("Cannot attach body of message:  $!");

    open( OUT, "| tee $LOGDIR/sendmail.log | $SENDMAIL -t -f '$src' 2>&1" ) ||
        die("Cannot run $SENDMAIL:  $!");
    print OUT $mime_msg->as_string;
    close( OUT );
    }

#########################################################################
#	Parse standard input coming from a mailer.			#
#########################################################################
# Side effect:	May update "Subject" and "To" header fields for OUTGOING mail.
sub parse_email
    {
    my $in_body = 0;
    my $stop_ind = -1;
    my %stops;
    my %display_order;

    open( LOG, ">> $LOGDIR/log" );
    if( ! $LOCAL_INPUT )
	{
	close( STDOUT );
	close( STDERR );
	open( STDOUT,   "> $LOGDIR/stdout"       );
	open( STDERR,   "> $LOGDIR/stderr"       );
	system("id -a");
	}

    while( $_ = <STDIN> )
	{
	print LOG $_;
	chomp($_);
	if( /^Subject:\s*(.*)$/ )
	    {
	    $header{subject} = $1;
	    ( $header{subject}, $header{to} ) = ( $1, $2 )
		if( $header{subject} =~ /^(.*)\s+([^\s@]+@[^\s]+)$/ );
	    $header{route_name} = $1
	    	if( $header{subject} =~ /^(.*) update/ );
	    }
	elsif( /^From:\s+(.*\@.*)/ )		{ $header{from} = $1; }
	elsif( $_ eq "" )			{ $in_body = 1; }
	elsif( $in_body )
	    {
	    if( /^-(.*)/ )
		{ $stops{$stop_ind}->{notes} .= "$1\n"; }
	    elsif( (   /^(\w[^:]+):\s+(\w+)$/
		    || /^(\w[^:]+):\s+(\w+)\s+@\s+([0-9:]+)$/ )
			&& $COLORS{$2} )
		{
		$stop_ind++;
		$display_order{$stop_ind} = $stop_ind;
		$stops{$stop_ind}->{name} = $1;
		$stops{$stop_ind}->{status} = $2;
		$stops{$stop_ind}->{when} = ($3||"");
		$stops{$stop_ind}->{odometer} = ($4||"");
		$stops{$stop_ind}->{notes} = "";
		}
	    else
		{
		print LOG "Skipping [$_]\n";
		}
	    }
	}

    return
	{
	user		=> ( $header{from} || "unknown" ),
	route_name	=> ( $header{route_name} || "unknown" ),
	stops_p		=> \%stops,
	display_order_p	=> \%display_order
	};
    }

#########################################################################
##	Parse incoming form.						#
#########################################################################
sub parse_form
    {
    &CGIheader();
    &CGIreceive();

    open( LOG, "> $LOGDIR/form" ) || &fatal("Cannot write $LOGDIR/form:  $!");
    print LOG
	"fv_user=",$FORM{fv_user}, " ",
        "fv_route_name=",$FORM{fv_route_name},"\n",
	"fv_stops=[",$FORM{fv_stops},"]\n",
	"fv_display_order=[",$FORM{fv_display_order},"]\n";
    close( LOG );

    return
	{
	user		=>	$FORM{fv_user},
	route_name	=>	$FORM{fv_route_name},
	stops_p		=>	decode_json($FORM{fv_stops}),
    	display_order_p	=>	decode_json($FORM{fv_display_order})
	};
    }

#########################################################################
#	Figure out what type of input we're getting and			#
#	call appropriate parser.					#
#########################################################################
sub parse_input
    {
    my $input_p = ( $ENV{SCRIPT_NAME} ? &parse_form() : &parse_email() );

    my @mileage;
    foreach my $stop_p ( @{ $input_p->{stops_p} } )
        {
	push( @mileage, $stop_p->{odometer} ) if( $stop_p->{odometer} );
	}
    if( scalar(@mileage) >= 2 )
        {
	@mileage = sort @mileage;
	$input_p->{mileage} = $mileage[$#mileage] - $mileage[0];
	}

    return $input_p;
    }

#########################################################################
##	Generate table							#
#########################################################################
sub generate_html
    {
    my( $input_p ) = @_;
    my $stops_p = $input_p->{stops_p};
    my $display_order_p = $input_p->{display_order_p};

    my @ret = ( <<EOF );
<html></head><head><body><center>
<table width=90% style='border: solid black' border=0 cellspacing=0>
    <tr><th width=100% align=left>Stop</th>
	<th align=left>Status</th>
	<th align=right>When</th>
	<th align=right>Odometer<br>(miles)</th></tr>
EOF

    foreach my $display_order_p_key ( sort {$a<=>$b} keys %$display_order_p )
	{
	next if( $display_order_p_key !~ /^\d+$/ );
	my $stop_p = $stops_p->{$display_order_p->{$display_order_p_key}};
	push( @ret,
	    "    <tr bgcolor=", $COLORS{$stop_p->{status}}, ">",
	    "<th style='border-top:1px solid blue' align=left>",
	        $stop_p->{name}, "</th>\n",
	    "\t<td style='border-top:1px solid blue' align=left>",
	        $stop_p->{status}, "</td>\n",
	    "\t<td style='border-top:1px solid blue' align=right>",
	        $stop_p->{when}||"", "</td>\n",
	    "\t<td style='border-top:1px solid blue' align=right>",
	        $stop_p->{odometer}||"",
		"",
		"</td>\n",
	    "</tr>\n");
	if( $stop_p->{notes} )
	    {
	    my $notes = $stop_p->{notes};
	    $notes =~ s+\n+<br>\n+gs;
	push( @ret,
	    "    <tr bgcolor=", $COLORS{$stop_p->{status}}, ">",
	    "<td colspan=4>", $notes, "</td>",
	    "</tr>\n" );
	    }
	}
    push( @ret, "    <tr><th align=left colspan=3",
	" style='border-top:3px solid blue'>Miles excluding distance to distribution:</th>",
	"<td align=right style='border-top:3px solid blue'>",
	sprintf("%.1f",$input_p->{mileage}),
	"</td></tr>\n" ) if( $input_p->{mileage} );

    push( @ret, "</table></center></body></html>\n" );
    return join("",@ret);
    }

#########################################################################
#	Just dump what we got with no HTML.				#
#########################################################################
sub dump
    {
    my( $stops_p, $display_order_p ) = @_;

    foreach my $display_order_p_key ( sort {$a<=>$b} keys %$display_order_p )
	{
	next if( $display_order_p_key !~ /^\d+$/ );
	my $stop_p = $stops_p->{$display_order_p->{$display_order_p_key}};
	#my $stop_p = $stops_p->{$stops_p_key};
	print $stop_p->{name}||"UNDEF",
	    " ",$stop_p->{when}||"UNDEF",
	    " ",$stop_p->{status}||"UNDEF",
	    ( $ENV{SCRIPT_NAME}?"<br>":"" ),
	    "\n";
	}
    }

#########################################################################
#	Update trips file						#
#########################################################################
sub update_trips
    {
    my $USER = "chris";
    my $ROUTE_NAME = "Cheston";

    my( $input_p ) = @_;
    my($sec,$min,$hour,$mday,$month,$year,$wday) = localtime(time);
    my $trip_dir = "$LOGDIR/".$input_p->{user};
    my $date_string = sprintf("%04d%02d%02d.%s", $year+1900, $month+1, $mday );
    my $trip_file = "$trip_dir/$date_string-".$input_p->{route_name};
    if( ! -d $trip_dir ) { system("mkdir -p $trip_dir"); }
    open(OUT, "> $trip_file") || &fatal("Cannot write to ${trip_file}:  $!");
    print OUT $date_string,
	"\t", $DAY_NAMES[$wday],
	"\t", $input_p->{mileage},
	"\t", $input_p->{route_name},
	"\n";
    close( OUT );
    }

#########################################################################
#	Main								#
#########################################################################

$ENV{PATH}="/sbin:/bin:/usr/sbin:/usr/bin:/usr/local/bin:/opt/aws/bin";

%header = map { $_, $DEFAULT_HEADER{$_} } keys %DEFAULT_HEADER;

my( $input_p ) = &parse_input();

#&dump( $input_p->{stops_p}, $input_p->{display_order_p} );

my $html_table = &generate_html( $input_p );

&html_to_sendmail(
    $header{from},
    $header{to}.",chris.interim\@gmail.com",
    $header{subject},
    $html_table
    ) if( ! $LOCAL_OUTPUT );

&update_trips( $input_p );

print "<h2>Update sent</h2>",
join("<br>\n",
    "To:  $header{to}",
    "From:  $header{from}",
    "Subject:  $header{subject}",
    "",
    $html_table);

if( ! $LOCAL_INPUT )
    {
    close( STDOUT );
    close( STDERR );
    }
close( LOG );

exit(0);
