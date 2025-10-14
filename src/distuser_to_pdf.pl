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

my $PROJECT = "routing";
my $PROG = ( $_ = $0, s+.*/++, s/\.[^\.]*$//, $_ );
my $TMP = "/tmp/$PROG.$$";
#my $TMP = "/tmp/$PROG";
my $TRIP_DIR="/var/log/$PROJECT/trips";
my $BASEDIR = "/usr/local/projects/$PROJECT";
my $SPLIT_TRIPS = "$BASEDIR/bin/split_trips";
my $READ_TRIPS = "$BASEDIR/bin/read_trips";

my $DEFAULT_DISTRIBUTOR = "MOW_Sagadahoc";
my $DEFAULT_DRIVER = "Chris_Caldwell";

my %ONLY_ONE_DEFAULTS =
    (
    #"i"	=>	"/var/log/routing/trips/$DEFAULT_DISTRIBUTOR/$DEFAULT_DRIVER/log",
    "i"	=>	"",
    "t"	=>	$TMP,
    "d"	=>	$DEFAULT_DISTRIBUTOR,
    "r" =>	"",
    "u"	=>	$DEFAULT_DRIVER,
    "o"	=>	"/tmp/fun.pdf",
    "m"	=>	"",
    "v"	=>	""
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
    if( ! $ARGS{v} )
	{ }	# No need to print commands
    elsif( $ENV{SCRIPT_NAME} )
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

    $ARGS{i} ||= "$TRIP_DIR/$ARGS{d}/$ARGS{u}.log";
    }

#########################################################################
#	Find all the trip files, sort them by yearmonth, make reports	#
#	and congretate them all into one gigantic .pdf file.		#
#########################################################################
sub do_it
    {
    my $trips_dir = "$ARGS{t}/$ARGS{d}/$ARGS{u}";
    my %fnames =
	(
	log	=> $ARGS{i}||$trips_dir."/log",
	data	=> $trips_dir,
	trips	=> $trips_dir."/trips",
	htmls	=> $trips_dir."/htmls",
	pdfs	=> $trips_dir."/pdfs"
	);

    chdir( $BASEDIR ) || &fatal("Cannot chdir($BASEDIR):  $!");
    grep( -d $fnames{$_} || &echodo("mkdir -p $fnames{$_}"), "data", "htmls", "pdfs" );

    &echodo( join(" ",
	    $SPLIT_TRIPS,
	    "-i", $fnames{log},
	    "-o", $fnames{data}
	    ) );

    my @pdfs = ();
    opendir( D, $fnames{trips} ) || &fatal("Cannot opendir($fnames{trips}):  $!");

    my $l4 = $ARGS{m};
    $l4 = "$1-$2" if( $l4 && $l4 =~ /(\d\d\d\d)(\d\d)/ );
    foreach my $trips_file ( grep( /\d\d\d\d-\d\d-\d\d/, readdir(D) ) )
	{
	#print STDERR "l4=$l4 trips_file=$trips_file.\n";
	next if( $l4 && $trips_file !~ /^$l4/ );
	#print STDERR "Processing $trips_file.\n" if( 1 || $ARGS{v} );
	&echodo( join(" ",
	    $READ_TRIPS,
	    ( $ARGS{r} ? ("-r",	$ARGS{r}) : () ),
	    "-d",	$ARGS{d},
	    "-u",	$ARGS{u},
	    "-i",	"$fnames{trips}/$trips_file",
	    "-h",	"$fnames{htmls}/$trips_file.html",
	    "-o",	"$fnames{pdfs}/$trips_file.pdf"
	    ) );
	push( @pdfs, "$fnames{pdfs}/$trips_file.pdf" );
	}
    closedir( D );

    if( ! @pdfs )
        { &fatal("No expenses/trips to report for $ARGS{d}."); }
    elsif( $ARGS{o} !~ /\@/ )
        { &echodo( join(" ","pdfunite",@pdfs,$ARGS{o}) ); }
    else
	{
	my $outfile = "$TMP.pdf";
        &echodo( join(" ","pdfunite",@pdfs,$outfile) );
	my $msg = "$ARGS{d} log of $ARGS{u}";
	$msg .= sprintf(" of %s",$ARGS{m}) if( $ARGS{m} );
	$msg =~ s/_+/ /g;
	open( OUT, "| mailx -s '$msg' -a $outfile $ARGS{o}" )
	    || &fatal("Cannot e-mail to $ARGS{o}:  $!");
	print OUT "$msg in enclosed PDF file.\n";
	close( OUT );
	unlink( $outfile );
	}
    }

#########################################################################
#	Main								#
#########################################################################

if( 0 && $ENV{SCRIPT_NAME} )
    { &CGI_arguments(); }
else
    { &parse_arguments(); }

#print join("\n\t","Args:",map{"$_:\t$ARGS{$_}"} sort keys %ARGS), "\n";

&do_it();

exec("rm -rf $TMP");
