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

# Put constants here

my $PROG = ( $_ = $0, s+.*/++, s/\.[^\.]*$//, $_ );
my $TMP = "/tmp/$PROG.$$";
my $LOG_BASE = "/var/log/routing";
my $PROGRESS_DIR = "$LOG_BASE/progress";
my $EXPECTED_DIR = "$LOG_BASE/expected";
my %ONLY_ONE_DEFAULTS =
    (
    "d"	=>	"Test_Distributor",
    "c"	=>	"current.kml",
    "n"	=>	"new.kml"
    );

# Put variables here.

my @problems;
my %ARGS;
my @files;
my $exit_stat = 0;

# Put interesting subroutines here

#=======================================================================#
#	Verbatim from prototype.pl					#
#=======================================================================#

#########################################################################
#	Print a header if need be.					#
#########################################################################
my $hdrcount = 0;
sub CGIheader
    {
    print "Content-type:  text/html\n\n" if( $hdrcount++ == 0 );
    }

#########################################################################
#	Print out a list of error messages and then exit.		#
#########################################################################
sub fatal
    {
    if( ! $ENV{SCRIPT_NAME} )
        { print join("\n",@_,""); }
    else
        {
	&CGIheader();
	print "<h2>Fatal error:</h2>\n",
	    map { "<dd><font color=red>$_</font>\n" } @_;
	}
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
	{ read(STDIN, $incoming, $ENV{'CONTENT_LENGTH'}); }
    else
	{ $incoming = $ENV{'QUERY_STRING'}; }
    
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
#	Print a command and then execute it.				#
#########################################################################
sub echodo
    {
    my( $cmd ) = @_;
    if( $ENV{SCRIPT_NAME} )
	{ print "<pre>+ $cmd</pre>\n"; }
    else
        { print "+ $cmd\n"; }
    return system( $cmd );
    }

#########################################################################
#	Read an entire file and return the contents.			#
#	If open fails and a return value is not specified, fail.	#
#########################################################################
sub read_file
    {
    my( $fname, $ret ) = @_;
    if( open(COM_INF,$fname) )
        {
	$ret = do { local $/; <COM_INF> };
	close( COM_INF );
	}
    elsif( scalar(@_) < 2 )
        { &fatal("Cannot open ${fname}:  $!"); }
    return $ret;
    }

#########################################################################
#	Read an entire file.						#
#########################################################################
sub write_file
    {
    my( $fname, @contents ) = @_;
    open( COM_OUT, "> $fname" ) || &fatal("Cannot write ${fname}:  $!");
    print COM_OUT @contents;
    close( COM_OUT );
    }

#=======================================================================#
#	New code not from prototype.pl					#
#		Should at least include:				#
#			parse_arguments()				#
#			CGI_arguments()					#
#			usage()						#
#=======================================================================#

#########################################################################
#	Setup arguments if CGI.						#
#########################################################################
sub CGI_arguments
    {
    &CGIreceive();
    }

#########################################################################
#	Print usage message and die.					#
#########################################################################
sub usage
    {
    &fatal( @_, "",
	"Usage:  $PROG <possible arguments>","",
	"where <possible arguments> is:",
	"    -o <output file>",
	"    -t <title>",
	"    <filename>",
	"    <filename> -t <filename title>"
	);
    }

#########################################################################
#	Parse the arguments						#
#########################################################################
sub parse_arguments
    {
    my $arg;
    while( defined($arg = shift(@ARGV) ) )
	{
	# Put better argument parsing here.

	if( $arg =~ /^-(.)(.*)$/ && defined($ONLY_ONE_DEFAULTS{$1}) )
	    {
	    if( defined($ARGS{$1}) )
		{ push( @problems, "-$1 specified multiple times." ); }
	    else
		{ $ARGS{$1} = ( $2 ne "" ? $2 : shift(@ARGV) ); }
	    }
	elsif( $arg =~ /^-(t)(.*)$/ )
	    {
	    my $val = ( $2 ? $2 : shift(@ARGV) );
	    if( $#files <= 0 )
	        {
		if( defined($files[$#files]->{$1}) )
		    {
		    push( @problems,
			$files[$#files]->{name} .
			    " -$1 specified multiple times." );
		    }
		else
		    { $files[$#files]->{$1} = $val; }
		}
	    elsif( defined( $ARGS{$1} ) )
		{ push( @problems, "-$1 specified multiple times." ); }
	    else
		{ $ARGS{$1} = $val; }
	    }
	elsif( $arg =~ /^-.*/ )
	    { push( @problems, "Unknown argument [$arg]" ); }
	else
	    { push( @files, $arg ); }
	}

    #push( @problems, "No files specified" ) if( ! @files );
    &usage( @problems ) if( @problems );

    # Put interesting code here.

    grep( $ARGS{$_}=(defined($ARGS{$_})?$ARGS{$_}:$ONLY_ONE_DEFAULTS{$_}),
	keys %ONLY_ONE_DEFAULTS );
    }

#########################################################################
#	Return a triple consisting of everything pre the track folders,	#
#	the last track, and everything after the track folders.		#
#########################################################################
sub old_split_kml_file
    {
    my( $fname ) = @_;
    my $contents = &read_file( $ARGS{p} );
    &fatal( "$fname Cannot find track folder in $fname." )
	if($contents!~m:(.*<Folder>)(.*?<name>Tracks</name>.*?)(</Folder>.*)$:s);
    my( $pre_track, $track_folder, $post_track ) = ( $1, $2, $3 );
    my @placemark_pieces=split(m:(<Placemark>.*?</Placemark>):s,$track_folder);
    &fatal( "track folder has no placemarks in $fname." )
	if( scalar(@placemark_pieces) < 3 );
    my $pre_track_placemark = $pre_track . $placemark_pieces[0];
    my $post_track_placemark = pop( @placemark_pieces ) . $post_track;
    my $last_track = pop( @placemark_pieces );
    return( $pre_track_placemark, $last_track, $post_track_placemark );
    }

#########################################################################
#	This is actually much quicker and dirtier than you might think.	#
#	We're going to assume there are two <Folders> per file,		#
#	and that the first one contains the GPS tracks,			#
#	and that the last GPS track is the latest in that file.		#
#	and that the last GPS track is always the latest.		#
#########################################################################
sub merge_them_kml_routes
    {
    my($previous_head,$previous_track,$previous_tail)=&split_kml_file($ARGS{p});
    $previous_track =~ s+<styleUrl>(.*)</styleUrl>+<styleUrl>#red</styleUrl>+;
    my($new_head,$new_track,$new_tail)=&split_kml_file($ARGS{c});
    $new_track =~ s+<styleUrl>(.*)</styleUrl>+<styleUrl>#blue</styleUrl>+;
    &write_file($ARGS{n},$new_head,$previous_track."\n   ".$new_track,$new_tail);
    }

#########################################################################
#########################################################################
sub split_kml_file
    {
    my( $fname ) = @_;
    print "Processing [$fname]\n";
    my @folder_pieces = split(m:(<Folder>.*?</Folder>):s,&read_file($fname));
    my $folders_pre = shift(@folder_pieces);
    my $folders_post = pop(@folder_pieces);
    my ( $waypoint, $placemarks_pre, $placemarks_post, $last_placemark );
    foreach my $folder ( grep( $_ =~ /^<Folder>/, @folder_pieces ) )
	{
	if( $folder =~ m:<name>Waypoints</name>: )
	    { $waypoint = $folder; }
	elsif( $folder =~ m:<name>Tracks</name>: )
	    {
	    my(@placemark_pieces)
		= split( m:(<Placemark>.*</Placemark>):s, $folder );
	    $placemarks_pre = shift(@placemark_pieces);
	    $placemarks_post = pop(@placemark_pieces);
	    @placemark_pieces = grep( /^<Placemark>/, @placemark_pieces );
	    $last_placemark = pop(@placemark_pieces);
	    }
	}
    return
	(
	$folders_pre,
	$waypoint,
	$placemarks_pre,
	$last_placemark,
	$placemarks_post,
	$folders_post
	);
    }

#########################################################################
#########################################################################
my( $folders_pre, $placemarks_pre, $placemarks_post, $folders_post );
my %kmls;
my %fi;
my %expected_waypoints;
my %expected_routes;
sub analyze_distributor
    {
    my %kmls;
    opendir( D0, "$EXPECTED_DIR/$ARGS{d}" )
	|| &fatal("Cannot opendir($EXPECTED_DIR/$ARGS{d}):  $!");
    foreach my $route_file ( readdir(D0) )
	{
	if( $route_file =~ /^(\w.*)\.kml$/ )
	    {
	    my $route = $1;
	    my  (
		$folders_pre,
		$expected_waypoints{$route},
		$placemarks_pre,
		$last_placemark,
		$expected_routes{$route},
		$folders_post
		) = &split_kml_file( $route_file );
	    }
	}
    closedir( D0 );
	
    opendir( D0, "$PROGRESS_DIR/$ARGS{d}" )
	|| &fatal("Cannot opendir($PROGRESS_DIR/$ARGS{d}):  $!");
    foreach my $driver ( readdir(D0) )
	{
	if( opendir(D1,"$PROGRESS_DIR/$ARGS{d}/$driver") )
	    {
	    foreach my $fname ( readdir(D1) )
		{
	        $kmls{$2}{$1}{$driver} = "$ARGS{d}/$driver/$fname"
		    if( $fname =~ /^(\d\d\d\d\d\d\d\d)-(.*)\.kml$/ );
		}
	    close(D1);
	    }
	}
    closedir( D0 );
    }

#########################################################################
#########################################################################
sub read_kml_files
    {
    foreach my $route ( sort keys %kmls )
	{
	my @dates = sort keys %{$kmls{$route}};

	foreach my $pos ( "last", "previous" )
	    {
	    my $newdate = pop(@dates);
	    if( $newdate )
		{
		my $driver = (keys %{$kmls{$route}{$newdate}})[0];
		my $file = $kmls{$route}{$newdate}{$driver};
		$fi{$route}{$pos}{date} = $newdate;
		$fi{$route}{$pos}{driver} = $driver;
		$fi{$route}{$pos}{file} = $file;
		(   $folders_pre,
		    $fi{$route}{$pos}{waypoints},
		    $placemarks_pre,
		    $fi{$route}{$pos}{placemark},
		    $placemarks_post,
		    $folders_post
		    ) = &split_kml_file( $fi{$route}{$pos}{file} );
		}
	    }
	}
    }

#########################################################################
#########################################################################
sub write_new_kmls
    {
    my @waypoints;
    my @placemarks;
    foreach my $pos ( keys %fi )
        {
	foreach my $route ( sort keys %kmls )
	    {
	    push(@waypoints,$_) if( $_ = $fi{$route}{$pos}{waypoints} );
	    push(@placemarks,$_) if( $_ = $fi{$route}{$pos}{last_placemark} );
	    }
	{
	&write_file(
	    join( "/", $ARGS{d}, "$route.kml" ),
	    $folders_pre,
	    $waypoint,
	    $placemarks_pre,
	    $last_placemark,
	    $placemarks_post,
	    $folders_post
	    );
	}
    }

#########################################################################
#	Main								#
#########################################################################

if( $ENV{SCRIPT_NAME} )
    { &CGI_arguments(); }
else
    { &parse_arguments(); }

&analyze_distributor();

exit($exit_stat);
