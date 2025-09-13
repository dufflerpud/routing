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
my $DEFAULT_DISTRIBUTOR="MOW_Sagadahoc";
my $DEFAULT_USER="Chris_Caldwell";
my $BASE = "/var/log/routing/trips/$DEFAULT_DISTRIBUTOR/$DEFAULT_USER";

my %ONLY_ONE_DEFAULTS =
    (
    "i"	=>	"$BASE/log",
    "o"	=>	$BASE,
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
	{ }	# No need to print anything
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
    }

#########################################################################
#	Swallow directory of individual trip files and generate		#
#	files aggreated by route and month.				#
#########################################################################
sub process_trip_files
    {
    my %entries;
    my @fnames;

    if( ! -d $ARGS{i} )
	{ push( @fnames, $ARGS{i} ); }
    else
	{
	opendir( D, $ARGS{i} ) || &fatal("Cannot open $ARGS{i}:  $!");
	push( @fnames,
	    map { "$ARGS{i}/$_" }
		grep( /^\d\d\d\d\d\d\d\d-.*/, readdir(D) ) );
	closedir( D );
	}

    foreach my $fn ( @fnames )
	{
	print "Reading [$fn]\n" if( $ARGS{v} );
	# 20220316	Wed	0:00	26.3	Brunswick Towers
	open( INF, $fn ) || die("Cannot open ${fn}:  $!");
	while( $_ = <INF> )
	    {
	    chomp( $_ );
	    my( $when, $day, $elapsed, $mileage, $route ) = split(/\t/);

	    # By storing it this way, all but the last entry on a particular year-month-day on a
	    # particular route are ignored.  This allows the system to handle somebody writing
	    # out the their route update multiple times.
	    my $year;
	    my $month;
	    my $monthday;
	    if( $when =~ m:^(\d\d\d\d)(\d\d)(\d\d): || $when =~ m:^(\d\d\d\d)-(\d\d)-(\d\d): )
		{ $year=$1; $month=$2; $monthday=$3; }
	    elsif( $when =~ m:^(\d\d)/(\d\d)/(20\d\d): )
		{ $year=$3; $month=$1; $monthday=$2; }
	    else
		{ &fatal("Do not know how to read when=[$when]"); }
	    $entries{"$year-$month"}{$monthday}{$_} = $_;
	    }
	}

    system("mkdir -p $ARGS{o}") if( ! -d $ARGS{o} );

    foreach my $yearmo ( sort keys %entries )
	{
	my @days = sort keys %{$entries{$yearmo}};
	my $lastday = $days[$#days];
	my $fn = "$ARGS{o}/trips/$yearmo-$lastday";
	system("mkdir -p $ARGS{o}/trips") if( ! -d "$ARGS{o}/trips" );
	print "Creating [$fn]\n" if( $ARGS{v} );
	open( OUT, "> $fn" ) || die("Cannot write ${fn}:  $!");
	foreach my $day ( @days )
	    {
	    print OUT ( map { $entries{$yearmo}{$day}{$_}."\n" }
		sort keys %{$entries{$yearmo}{$day}} );
	    }
	close( OUT );
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

&process_trip_files();

exit($exit_stat);
