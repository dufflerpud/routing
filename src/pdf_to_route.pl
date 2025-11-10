#!/usr/local/bin/perl -w
########################################################################
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
########################################################################
#	(Replace with brief explanation of what this file is or does)
#
#	2024-04-20 - c.m.caldwell@alumni.unh.edu - Created
########################################################################

use strict;

use lib "/usr/local/lib/perl";
use cpi_vars;
use cpi_file qw( fatal cleanup read_file write_file read_lines );
use cpi_arguments qw( parse_arguments );
use cpi_reorder qw( orderer );
use cpi_config qw( read_map );
use cpi_filename qw( just_ext_of );

#use Data::Dumper;	# Very useful for debugging

# Put constants here

my @EXCLUDES = qw( pos0 len0 pos1 len1 pos2 len2 pos3 len3 pos4 len4 );
my $TOWNS = "/usr/local/projects/routing/lib/towns.list";
my $ROADS = "/usr/local/projects/routing/lib/roads.list";

our %ONLY_ONE_DEFAULTS =
    (
    "ifile"		=>	"/dev/stdin",
    "itype"		=>	"",
    "ofile"		=>	"/dev/stdout",
    "otype"		=>	"",
    "distributor"	=>	"BI Distributor",
    "route"		=>	"",
    "verbosity"		=>	"0",
    );

# Put variables here.

our $exit_stat = 0;

# These variables are used by &cpi_arguments::parse_arguments()
our @problems;
our %ARGS;
our @files;

# Put interesting subroutines here

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
	"Usage:  $cpi_vars::PROG <possible arguments>","",
	"where <possible arguments> is:",
	"    -i <input file>",
	"    -o <output file>",
	"    -v 1 or 0 for verbose on or off"
	);
    }

#########################################################################
#	Look for any standard flags in the 5th column.			#
#########################################################################
sub column4
    {
    my( $recp, $data ) = @_;
    if( $data =~ /SPECIAL: SECTION 19 - 7/ )
	{ push( @{$recp->{FoodPrefs}}, "7 pack" ); }
    elsif( $data =~ /SPECIAL/ )
	{ push( @{$recp->{FoodPrefs}}, "Special meal" ); }
    push( @{$recp->{FoodPrefs}}, "CSFP box" ) if( $data =~ /USDA/ );
    push( @{$recp->{FoodPrefs}}, "SSBG"	) if( $data =~ /SSBG/ );

    if( $data =~ /(\d+)\s*CAT/ )
	{ $recp->{Cats} = $1; }
    elsif( $data =~ /CAT/ )
	{ $recp->{Cats} = 1; }

    if( $data =~ /(\d+)\s*DOG/ )
	{ $recp->{Dogs} = $1; }
    elsif( $data =~ /DOG/ )
	{ $recp->{Dogs} = 1; }
    }

#########################################################################
#	Replace this with the meat of the new software.			#
#########################################################################
sub read_pdf
    {
    $ARGS{itype} = &just_ext_of( $ARGS{ifile}, "pdf" ) if( ! $ARGS{itype} );
    my $contents =
	( $ARGS{itype} eq "pdf"
        ? &read_file( "pdftotext -layout $ARGS{ifile} - |" )
	: &read_file( $ARGS{ifile} ) );
    my @lines = split(/\n/,$contents);

    my $recp;
    my @recs;

    my $recnum = 0;
    for( my $lnm=0; $lnm<=$#lines; $lnm++ )
        {
	$_ = $lines[$lnm];
	if( /^(([1-9][0-9]*)\s*)(([\w\-\.]+,[^\d]*?)\s*)((\d.*?)\s*)([A-Z]:\s*(\(\d\d\d\)\s+[\d\-]+)\s*)(.*)$/ )
	    {
	    push( @recs, $recp ) if( $recp );
	    #print "1=[$1]\n 2=[$2]\n 3=[$3]\n 4=[$4]\n 5=[$5]\n 6=[$6]\n 7=[$7]\n 8=[$8]\n 9=[$9]\n";
	    $recp =
		{
		Ind		=>	$2,
		Name		=>	$4,
		Distributor	=>	$ARGS{distributor},
		Route		=>	$ARGS{route},
		Address		=>	$6,
		Phone		=>	$8
		};
	    $recp->{pos0}=0;				$recp->{len0}=length($1);
	    $recp->{pos1}=$recp->{pos0}+$recp->{len0};	$recp->{len1}=length($3);
	    $recp->{pos2}=$recp->{pos1}+$recp->{len1};	$recp->{len2}=length($5);
	    $recp->{pos3}=$recp->{pos2}+$recp->{len2};	$recp->{len3}=length($7);
	    $recp->{pos4}=$recp->{pos3}+$recp->{len3};	$recp->{len4}=length($9);
	    &column4( $recp, $9 ) if( $9 );
	    }
	elsif( /^\w/ )
	    {
	    push( @recs, $recp ) if( $recp );
	    $recp = undef;
	    }
	elsif( $recp )
	    {
	    if( length($_) > $recp->{pos0} )
		{
		my $col0=substr($_,$recp->{pos0},$recp->{len0});
		if( length($_) > $recp->{pos1} )
	    	    {
		    my $col1=substr($_,$recp->{pos1},$recp->{len1});
		    $col1 =~ s/\s+$//;
		    $recp->{Name} .= " $col1" if( $col1 );
		    if( length($_) > $recp->{pos2} )
			{
			my $col2=substr($_,$recp->{pos2},$recp->{len2});
			$col2 =~ s/\s+$//;
			if( $col2 )
			    {
			    if( $col2=~/Directions/ )
				{
				$col2 =~ s/Directions[:\s]*//;
				$recp->{Driver_note} = $col2;
				}
			    elsif( $recp->{Driver_note} )
				{ $recp->{Driver_note} .= " $col2"; }
			    else
				{ $recp->{Address} .= " $col2"; }
			    }
			if( length($_) > $recp->{pos3} )
			    {
			    my $col3=substr($_,$recp->{pos3},$recp->{len3});
			    $col3 =~ s/\s+$//;
			    if( length($_) > $recp->{pos4} )
				{
				my $col4=substr($_,$recp->{pos4},$recp->{len4});
				$col4 =~ s/\s+$//;
				&column4( $recp, $col4 ) if( $col4 );
				}
			    }
			}
		    }
		}
	    }
	}
    push( @recs, $recp ) if( $recp );

    foreach my $recp ( @recs )
        {
	foreach my $field ( %{$recp} )
	    {
	    $recp->{$field} = join(",",@{$recp->{$field}})
		if( $recp->{$field} && ref( $recp->{$field} ) eq "ARRAY" );
	    }
	}
    return @recs;
    }

#########################################################################
#	Imported addresses come in all kinds of formats.  Try to fix	#
#	format.								#
#########################################################################
sub fix_addresses
    {
    my( @recs ) = @_;

    my( $townsearch, %townmap ) = &read_map( $TOWNS );
    my( $roadsearch, %roadmap ) = &read_map( $ROADS );

    foreach my $recp ( @recs )
	{
	$recp->{Name} = "$2 $1"
	    if( $recp->{Name} && $recp->{Name}=~/(.*),\s+(.*)/ );
	$recp->{Phone} =~ s/ //g if( $recp->{Phone} );
	if( $recp->{Address} )
	    {
	    my @resarray;
	    #print STDERR "Looking at [$recp->{Address}]\n";
	    my $no_commas = $recp->{Address};
	    $no_commas =~ s/,/ /g;
	    if( $no_commas !~ /^(.*?)[^\w]*\b($roadsearch)\b[^\w]*(.*?)$/ims )
		{ push( @resarray, $recp->{Address} ); }
	    else
		{
		my( $streetinfo, $streettype, $rest0 ) = ( $1, $2, $3 );
		push( @resarray, $streetinfo." ".$roadmap{ lc($streettype) } );
		if( $rest0 !~ /^[^\w]*(.*?)\s*\b($townsearch)\b[^\w#]*(.*?)$/ims )
		    { push( @resarray, $rest0 ); }
		else
		    {
		    my( $apartment, $town, $post_town ) = ( $1, $2, $3 );
		    push( @resarray, $apartment ) if( $apartment =~ /\w/ );
		    push( @resarray, $townmap{ lc( $town ) } );
		    push( @resarray, $post_town =~ /\w/ ? $post_town : "ME" );
		    }
		}
	    $recp->{Address} = join(",",@resarray);
	    }
	}
    }

#########################################################################
#	Debug output							#
#########################################################################
sub recs_to_lpf
    {
    my( @recs ) = @_;
    my @order = qw( Name Distributor Route Phone Address FoodPrefs Cats Dogs Driver_note );
    my @toprint;
    foreach my $recp ( @recs )
        {
	push(@toprint,"\n") if( @toprint );
	foreach my $field (
	    &orderer({first=>\@order,exclude=>\@EXCLUDES},
	        keys %{$recp} ) )
	    {
	    next if( $field eq "Ind" );
	    push( @toprint, sprintf("%-20s%s\n",$field.":",$recp->{$field}) );
	    }
	}
    &write_file( $ARGS{ofile}, @toprint );
    }

#########################################################################
#	Output records fields in character separated fields.		#
#########################################################################
sub recs_to_psv
    {
    my @order = qw(
	Ind Name Distributor Route Email Phone Notify Address Coords Status
	Emergency_contact_0 Emergency_relationship_0 Emergency_phone_0
	FoodPrefs Cats Dogs Times_receiving Coordinator_note Assessor_note
	Driver_note Last_seen Last_seen_by Last_route Last_note
	Last_assessment );
    my( @recs ) = @_;

    my %seen_field;
    foreach my $recp ( @recs )
	{ grep( $seen_field{$_}=1, keys %{$recp} ); }

    my @field_order = &orderer({first=>\@order,exclude=>\@EXCLUDES},keys %seen_field);

    my @toprint = ( join("|",@field_order)."\n" );
    foreach my $recp ( @recs )
        {
	push( @toprint,
	    join("|",map {defined($recp->{$_})?$recp->{$_}:""} @field_order).
		"\n" );
	}

    if( $ARGS{otype} eq "psv" )
        { &write_file( $ARGS{ofile}, @toprint ); }
    else
	{
	my $cmd = "table_fun"
	    ." -idelimeter '|' -itype csv -ifile /dev/stdin"
	    ." -otype $ARGS{otype} -ofile $ARGS{ofile}";
	open( OUT, "| $cmd" ) || &autopsy( "Command [$cmd] failed:  $!");
	print OUT @toprint;
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

my @recs = &read_pdf();
&fix_addresses( @recs );

$ARGS{otype} = &just_ext_of( $ARGS{ofile}, "psv" ) if( ! $ARGS{otype} );

if( $ARGS{otype} eq "lpf" )
    { &recs_to_lpf( @recs ); }
else
    { &recs_to_psv( @recs ); }

&cleanup(0);
