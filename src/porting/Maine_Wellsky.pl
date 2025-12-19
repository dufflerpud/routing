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

use lib "/usr/local/lib/perl";
use cpi_vars;
use cpi_file qw( fatal cleanup read_file write_file read_lines tempfile );
use cpi_arguments qw( parse_arguments );
use cpi_reorder qw( orderer );
use cpi_config qw( read_map );
use cpi_filename qw( just_ext_of );
use cpi_drivers qw( get_driver );

my $driverp = &get_driver(__FILE__);

# Put constants here

my @PSF_ORDER = qw(
    Ind Name Distributor Route Email Phone Notify Address Coords Status
    Emergency_contact_0 Emergency_relationship_0 Emergency_phone_0
    FoodPrefs Cats Dogs Times_receiving Coordinator_note Assessor_note
    Driver_note Last_seen Last_seen_by Last_route Last_note
    Last_assessment );
my @PSF_EXCLUDES = qw( pos0 len0 pos1 len1 pos2 len2 pos3 len3 pos4 len4 );
my $TOWNS = "/usr/local/projects/routing/lib/towns.list";
my $ROADS = "/usr/local/projects/routing/lib/roads.list";

$driverp->{name} = "Maine Wellsky Server";

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
    my( $pdf_file, $distributor_name, $route_name ) = @_;
    my @lines = split(/\n/,&read_file( "pdftotext -layout $pdf_file - |" ) );
    print STDERR "Read ", scalar(@lines), " lines.\n";

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
		Distributor	=>	$distributor_name,
		Route		=>	$route_name,
		Address		=>	$6,
		Phone		=>	$8,
		Status		=>	"Active"
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
#	Imported addresses come in all kinds of formats.  Try to make	#
#	this something Mapquest or Google Maps understands.		#
#	Ideally this would be replaced by:				#
#		Geo::StreetAddress::US->normalize_address($address)	#
#	followed by something that joined it back in "normal" order.	#
#	However, this is smart enough to know that we're parsing	#
#	Maine's Wellsky database, so we can pick out town names more	#
#	easily.								#
#########################################################################
my $townsearch;
my %townmap;
my $roadsearch;
my %roadmap;
sub fix_Maine_address
    {
    my ( $address ) = @_;
    ( $townsearch, %townmap ) = &read_map( $TOWNS ) if( ! $townsearch );
    ( $roadsearch, %roadmap ) = &read_map( $ROADS ) if( ! $roadsearch );
    my @resarray;
    my $no_commas = $address;
    $no_commas =~ s/,/ /g;
    #if( $no_commas !~ /^(.*?)[^\w]*\b($roadsearch)\b[^\w]*(.*?)$/ims )
    if( $no_commas !~ /^(.*)[^\w]+\b($roadsearch)\b[^\w]*(.*?)$/ims )
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
    my $res = join(",",@resarray);
    print STDERR "fix_Maine_address($address) returns [$res]\n";
    return $res;
    }

#########################################################################
#	Imported records come in all kinds of formats.  Try to fix	#
#	format.								#
#########################################################################
sub fix_recs
    {
    my( @recs ) = @_;


    foreach my $recp ( @recs )
	{
	$recp->{Name} = "$2 $1"
	    if( $recp->{Name} && $recp->{Name}=~/(.*),\s+(.*)/ );
	$recp->{Phone} =~ s/ //g if( $recp->{Phone} );
	$recp->{Address} = &fix_Maine_address( $recp->{Address} )
	    if( $recp->{Address} );
	}
    print STDERR "Post fix_recs nrecs=", scalar(@recs), ".\n";
    return @recs;
    }

#########################################################################
#	Output records fields in character separated fields.		#
#########################################################################
sub recs_to_psv
    {
    my( @recs ) = @_;

    my %seen_field;
    foreach my $recp ( @recs )
	{ grep( $seen_field{$_}=1, keys %{$recp} ); }

    my @field_order = &orderer({first=>\@PSF_ORDER,exclude=>\@PSF_EXCLUDES},keys %seen_field);

    my @toprint = ( join("|",@field_order)."\n" );
    foreach my $recp ( @recs )
        {
	push( @toprint,
	    join("|",map {defined($recp->{$_})?$recp->{$_}:""} @field_order).
		"\n" );
	}

    return join("",@toprint);
    }

#########################################################################
#	Input a Wellsky database from its route sheets.			#
#########################################################################
$driverp->{importer} = sub
    {
    my( $contents, $distributor_name, $route_name ) = @_;
    my $tmppdf = &tempfile(".pdf");
    &write_file( $tmppdf, $contents );
    &write_file( "/var/log/routing/debug.0", $contents );
    my @recs = &read_pdf( $tmppdf, $distributor_name, $route_name );
    print STDERR "Post read_pdf nrecs=", scalar(@recs), ".\n";
    @recs = &fix_recs( @recs );
    my $ret = &recs_to_psv( @recs );
    &write_file( "/var/log/routing/debug.2", $ret );
    return $ret;
    };

#########################################################################
#	Export a Wellsky database in some format.			
#########################################################################
$driverp->{exporter} = sub
    {
    my( $contents ) = @_;
    return "Content-type:  text/html\n\n"
        . "<h1>Unable to generate a Wellsky update at this time.</h1>";
    };
1;
