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
use Digest::MD5;
use JSON;

package main;
do "./common.pl";

&COMMON::setup( );

# Put constants here

my $PROG = ( $_ = $0, s+.*/++, s/\.[^\.]*$//, $_ );
my $TMP = "/tmp/$PROG.$$";
my $BASE = "/usr/local/projects/Routing";
my $CACHEDIR = "$BASE/cache";
my $TEMPLATE = "${BASE}/lib/routes.html";

my %CFG =
    (
    DELETE_MISSING_PATRONS	=> 0,
    ADD_NEW_ROUTES		=> 0,
    OVERWRITE_OLD_PATRONS	=> 0
    );

my @KNOWN_EXTENSIONS = ( "vcf" );

my %ONLY_ONE_DEFAULTS =
    (
    "d" =>	"",		# .db file
    "p"	=>	"",		# .plt file
    "c"	=>	"",		# .csv file
    "t"	=>	"",		# .txt file
    "h"	=>	"",		# .html file
    "r" =>	"mapquest",	# Ask mapquest for best order
    "l"	=>	""		# Directory for the library
    );
my $TABLE_FUN="/usr/local/bin/table_fun";
my $TF_FIELDS="Address,LatLong,Navrules,Full-Name,Phone,Organization,Note";
my $CVT = "/usr/local/bin/nene";

my %ORIGIN =
    (
    stop	=>		"MOW",
    address	=>		"1472 Federal Road,Livermore,ME,04253,US",
    coords	=>		"44.373755,-70.250453"
    );

my $MAPQUEST_KEY="dxMEhIJ2eQ1jS8098HjxwiUj8W0xjJwH";
my @HUMAN_ORDER=split(/,/,"street,town,state,zip,country");
#my @MAPQUEST_ORDER=split(m:/:,"country/state/town/street");
my @MAPQUEST_ORDER=split(m:,:,"street,town,state");
my $MAPQUEST_URL="http://www.mapquestapi.com/directions/v2/optimizedroute";
my @SKIPLIST = ( "disabled", "suspended", "skip" );

my %stop;			# Indexed by following and then a unique index:
				#  address, coords, distance_to,
				#  name_string, navrules, note, time_to,
				#  total_distance_to, total_time_to;

my %HARD_CODED_CARRIER_EMAIL =
    (
    "2074184226"	=> "2074184226\@mms.uscc.net",	# Dianne Alward
    "2075574435"	=> "2075574435\@vzwpix.com",	# Libby Matthews
    "2076204196"	=> "2076204196\@vzwpix.com",	# Rachel Gerow
    "2078417418"	=> "2078417418\@vzwpix.com"	# Chris Caldwell
    );

my $total_time = 0;
my $total_distance = 0;

my $current_route;

my @problems;
my %ARGS;
my @files;
my @jtable;
my %route;

#########################################################################
#	Avoid some typing.  Make prettier code.				#
#########################################################################
sub DBread	{ return &COMMON::dbread($COMMON::DB); }
sub DBwrite	{ return &COMMON::dbwrite($COMMON::DB); }
sub DBpop	{ return &COMMON::dbpop($COMMON::DB); }
sub DBget	{ return &COMMON::dbget($COMMON::DB,@_); }
sub DBput	{ return &COMMON::dbput($COMMON::DB,@_); }
sub DBdelkey	{ return &COMMON::dbdelkey($COMMON::DB,@_); }
sub DBadd	{ return &COMMON::dbadd($COMMON::DB,@_); }
sub DBdel	{ return &COMMON::dbdel($COMMON::DB,@_); }
sub DBnewkey	{ return &COMMON::dbnewkey($COMMON::DB,@_); }

#########################################################################
#	Print usage message and die.					#
#########################################################################
sub usage
    {
    &COMMON::fatal( @_, "",
	"Usage:  $PROG <possible arguments> <vcf files>","",
	"where <possible arguments> is:",
	"    -t <output .txt file>",
	"    -h <output .html or .pdf file>",
	"    -p <output .plt file>",
	"    -c <output .csv file>",
	"    -r(0|1) whether or not to ask mapquest for best route"
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
	elsif( -r $arg )
	    { push( @files, $arg ); }
	else
	    {
	    my $found_file;
	    foreach my $ext ( @KNOWN_EXTENSIONS )
	        {
		if( -r "$arg.$ext" )
		    {
		    push( @files, "$arg.$ext" );
		    $found_file = 1;
		    last;
		    }
		}
	    push( @problems, "[$arg] does not appear to be a file." )
	        if( ! $found_file );
	    }
	}

    push( @problems, "No files specified" ) if( ! @files );

    #print join("\n\t","Args:",map{"$_:\t$ARGS{$_}"} sort keys %ARGS), "\n";

    grep( $ARGS{$_}=(defined($ARGS{$_})?$ARGS{$_}:$ONLY_ONE_DEFAULTS{$_}),
	keys %ONLY_ONE_DEFAULTS );

    #print join("\n\t","Args:",map{"$_:\t$ARGS{$_}"} sort keys %ARGS), "\n";

    &usage( @problems ) if( @problems );

    $ARGS{o} = "/dev/stdout" if( !$ARGS{o} && !$ARGS{p} );
    }

#########################################################################
#	Print a command and then execute it.				#
#########################################################################
sub echodo
    {
    my( $cmd ) = @_;
    print "+ $cmd\n";
    return system( $cmd );
    }

#########################################################################
#	Read specified contacts files into an array of lines edited for	#
#	easy use elsewhere.  No longer know how to read vcf files	#
#	directly (use table_fun) to turn them into perl objects.	#
#	For sanity, we DO know how to read a perl object directly.	#
#########################################################################
sub read_contacts
    {
    my( @fnames ) = @_;
    my $to_open;

    if ( scalar(@fnames)!=1 || $fnames[0] !~ m:^.*?([^/]+)\.([\w]+)$: )
        { $current_route = "Current"; }
    else
        {
	$current_route = $1;
	my $ext = $2;
	$current_route =~ s/[^a-zA-Z0-9]+/_/g;
	$to_open = $fnames[0] if( $ext eq "po" );
	}

    $to_open=join(" ","cat",@fnames,"|",$TABLE_FUN,"-f",$TF_FIELDS,"-ot perl |")
	if( ! $to_open );

    my $refp;
    eval( "\$refp = " . &read_file( $to_open ) );

    my %points = ();
    foreach my $entryp ( @{ $refp } )
	{
    	my $organization = $entryp->{"Organization"};
	#next if( $organization =~ /disabled/i ); # Eliminate suspended people
	next if( grep( $organization =~ /$_/i, @SKIPLIST ) );

	my $name = $entryp->{"Full-Name"};

	#$name = join(" ",$2,$1)
	$name = $1
	    if( $name =~ /^(.*?)\s*(Routing [^\d\s]+\s*\d+)\s*(.*?)$/
	     || $name =~ /^(.*?)\s*(MOW [^\d\s]+\s*\d+)\s*(.*?)$/ );
	if( $entryp->{Phone} && $entryp->{Phone} =~ /^(.*)(\(.*\))(.*)/ )
	    { $name .= " $2$3"; }
	$name =~ s/\*\(/(/g;

	my $addr = $entryp->{Address};
	$addr =~ s/^[^\w]*//g;		# Delete *;; in some addrs
	$addr =~ s/,[^;]*//gs;		# Anything after a comma is bad
	$addr =~ s/\n[^;]*//gs;		# Delete 2nd line in street
	$addr =~ s/;/,/g;		# More useful comma separated
	$addr =~ s/,United States/,US/g;

	my $stop_name = $addr;		# Causes people at a particular
					# address to all be at the same stop.

	if( $organization =~ /(MOW|Routing).*staff/i )
	    { push( @{$points{mow}}, $stop_name ); }
	elsif( $organization =~ /(MOW|Routing).*driver/i )
	    { push( @{$points{beginend}}, $stop_name ); }
	else
	    { push( @{$points{way}}, $stop_name ); }

	push( @{$stop{$stop_name}{names}}, $name );
	$stop{$stop_name}{address} = $addr;
	$stop{$stop_name}{organization} = $organization;
	$stop{$stop_name}{coords} = ($entryp->{LatLong} || "");
	$stop{$stop_name}{coords} =~ s/:/,/g;
	$stop{$stop_name}{navrules} = ($entryp->{Navrules} || "");
	$stop{$stop_name}{note} = ( $entryp->{Note} || "");
	}
    if( ! $points{beginend} )
        {
	if( $points{mow} )
	    { $route{beginpoint} = $route{endpoint} = $points{mow}[0]; }
	else
	    {	# No endpoints?  No mowpoints?  Make something up.
	    &COMMON::fatal( "No Routing Driver or Routing Staff specified.\n" .
	    	"You probably want to add one before proceeding.\n" );
	    $route{beginpoint} = $route{endpoint} = $_ = $ORIGIN{stop};
	    $stop{$_}{address} = $ORIGIN{address};
	    $stop{$_}{coords} = $ORIGIN{coords};
	    push( @{ $stop{address}{$stop{$_}{names} } }, $_ );
	    }
	}
    elsif( scalar(@{$points{beginend}}) >= 2 )
	{ $route{beginpoint}=$points{beginend}[0]; $route{endpoint}=$points{beginend}[1]; }
    elsif( ! $points{mow} )
	{ $route{beginpoint} = $route{endpoint} = $points{beginend}[0]; }
    else
	{ $route{beginpoint}=$points{mow}[0]; $route{endpoint}=$points{beginend}[0]; }

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
	        { push( @{ $last_name_to_names{$2} }, $1 ); }
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
	$stop{$stopind}{name_string} = join(", ",@building);
	}
    }

#########################################################################
#	Generate a small unique id					#
#########################################################################
my @COMPACT_LEX = ( '0'..'9', 'A'..'Z', 'a'..'z', '_' );
sub unique_id
    {
    my @compact=();
    my $t = time();
    my $l = scalar(@COMPACT_LEX);
    do { push( @compact, $COMPACT_LEX[ $t % $l ] ); } while( $t = int($t/$l) );
    return join("",reverse(@compact));
    }

#########################################################################
#	Sort helper which sorts on basis of names of people at stop.	#
#########################################################################
sub mow_sort
    {
    my ( $a, $b ) = @_;
    my $an = $stop{$a}{name_string};
    $an = ( $an =~/Routing [^\d]+ (\d[\dA-Za-z]*)/ ? $1
	  : $an =~/MOW [^\d]+ (\d[\dA-Za-z]*)/ ? $1
	  : $an );
    my $bn = $stop{$b}{name_string};
    $bn = ( $bn =~/Routing [^\d]+ (\d[\dA-Za-z]*)/ ? $1
	  : $bn =~/MOW [^\d]+ (\d[\dA-Za-z]*)/ ? $1
	  : $bn );
    return ( $an cmp $bn );
    }

#########################################################################
#	Read an entire file and return the contents.			#
#	If open fails and a return value is not specified, fail.	#
#########################################################################
sub read_file
    {
    my( $fname, $ret ) = @_;
    if( open(INF,$fname) )
        {
	$ret = do { local $/; <INF> };
	close( INF );
	}
    elsif( scalar(@_) < 2 )
        { &COMMON::fatal("Cannot open ${fname}:  $!"); }
    return $ret;
    }

#########################################################################
#	Write an entire file.						#
#########################################################################
sub write_file
    {
    my( $fname, @contents ) = @_;
    open( OUT, "> $fname" ) || &COMMON::fatal("Cannot write ${fname}:  $!");
    print OUT @contents;
    close( OUT );
    print STDERR $fname, " written.\n";
    }

#########################################################################
#	Constructs query to mapquest.  Turn query into filename.	#
#	If file exists, it is the cached results, use those.  Else,	#
#	actually run the query and put results in the cache.		#
#########################################################################
sub query_mapquest
    {
    my( @stoplist ) = @_;

    my @mapquest_locations;
    my @debug_list;
    foreach my $stopind ( @stoplist )
	{
	my $locstr;
	if( $stop{$stopind}{coords} )
	    { $locstr = $stop{$stopind}{coords}; }
	else
	    {
	    my @toks = split(/, */,$stop{$stopind}{address});
	    my %fld = map { $_, shift(@toks) } @HUMAN_ORDER;
	    #$locstr = join( "/", ( map { $fld{$_} } @MAPQUEST_ORDER ) );
	    $locstr = join( ",", ( map { $fld{$_} } @MAPQUEST_ORDER ) );
	    }
	push( @mapquest_locations, $locstr );
	push( @debug_list, $stop{$stopind}{name_string} . ": " . $locstr );
	}

    #my $begin_address	= $mapquest_locations[0];
    #my @waypoints	= @mapquest_locations[1..$#mapquest_locations-1];
    #my $end_address	= $mapquest_locations[$#mapquest_locations];

    my $jsonpart =
	"{" . join(",",
	    #"beginpoint:'$begin_address'",
	    #"endpoint:'$end_address'",
	    #"locations:['".join("','",@waypoints)."']"
	    '"locations":["'.join('","',@mapquest_locations).'"]',
	    '"debug":["'.join('","',@debug_list).'"]'
	    ) . "}";

    my $results;
    my $cache_base = "$CACHEDIR/$current_route";
    my $query_file = "$cache_base.query.json";
    my $result_file = "$cache_base.result.json";

    if( &read_file( $query_file, "" ) eq $jsonpart )
	{ $results = &read_file( $result_file ); }
    else
	{
	my $coded_jsonpart = $jsonpart;
	$coded_jsonpart =~ s/([^A-Za-z0-9])/uc sprintf("%%%02x",ord($1))/eg;

	my $url = join("&",
	    "$MAPQUEST_URL?key=$MAPQUEST_KEY",
	    "format=json",
	    "json=$coded_jsonpart"
	    );

	my $cmd = ( -f "/usr/bin/curl" ? "curl -s '$url'" : "wget -q -O - '$url'" );
	#print "Opening [$cmd]\n";
	$results = &read_file( "$cmd |" );

	&write_file( $query_file, $jsonpart );
	&write_file( $result_file, $results );
	}

    my $refp = decode_json( $results );
    my @sequence = @{ $refp->{route}{locationSequence} };

    my $last_time = 0;
    my $last_distance = 0;

    for( my $i=0; $i<scalar(@sequence); $i++ )
        {
	my $stop_name = $stoplist[$sequence[$i]];
	$stop{$stop_name}{time_to} = $last_time;
	$stop{$stop_name}{distance_to} = $last_distance;
	$total_time += $last_time;
	$total_distance += $last_distance;
	$stop{$stop_name}{total_time_to} = $total_time;
	$stop{$stop_name}{total_distance_to} = $total_distance;
	my $lp = $refp->{route}{legs}[$i];
	$last_time = $lp->{time};
	$last_distance = int( ($lp->{distance}||0) * 10 + 0.5 ) / 10.0;
	}

    return map { $stoplist[$_] } @{$refp->{route}{locationSequence}};
    }

#########################################################################
#	Return stops ordered by name but 1st key will be start of route	#
#	and last key will be end of route.				#
#########################################################################
sub reorder
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
    if( $ARGS{r} =~ /mapquest/i )
        { return &query_mapquest(@sort1); }
    elsif( $ARGS{r} )
        { print STDERR "Do not know how to do a $ARGS{r} sort.\n"; }
    return @sort1;
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
#	Create a unique key, but leave some clues as to what type of	#
#	table it goes to.						#
#########################################################################
sub new_tagged_key
    {
    my( $tbl ) = @_;
    my $ret = substr($tbl,0,1) . "_" . &DBnewkey();
    &DBadd( $tbl, $ret );
    return $ret;
    }

#########################################################################
#	Create a new distributor.					#
#########################################################################
sub obj
    {
    my( $tbl, $Name, %args ) = @_;
    my $ind = ( &findkeys( $tbl, "Name", $Name ) || &new_tagged_key($tbl) );
    &DBput( $ind, "Name", $Name );
    foreach my $k ( keys %args )
	{ &DBput($ind,$k,$args{$k}); }
    return $ind;
    }

my $Distributor_None;
my $MOW_Sagadahoc;
my $MOW_Livermore;
my $Staff_None;
my $Staff_Chris_Caldwell;
my $Staff_Rachel_Gerow;
my $Staff_Dianne_Alward;
my $Route_None;

#########################################################################
#	Setup initial world.						#
#########################################################################
sub setup_objs
    {
    $Distributor_None
        = &obj("Distributor","No distributor" );
    $Route_None
	= &obj("Route","No route",
		Distributor=>$Distributor_None,
		Address=>"?" );
    $Staff_None
	= &obj("Staff","No staff",
		Email=>"?",
		Phone=>"?",
		Notify=>"?",
		Address=>"?",
		Distributor=>$Distributor_None );

    $MOW_Sagadahoc
	= &obj("Distributor","MOW Sagadahoc",
		Address=>"35 Union St.,Brunswick,ME,04011,US" );
    $MOW_Livermore
	= &obj("Distributor","MOW Livermore",
		Address=>"1766 Federal Rd.,Livermore,ME,,US",
		Coords=>"44.374210,-70.249784");

    $Staff_Chris_Caldwell
	= &obj("Staff","Chris Caldwell",
		Email=>"chris.interim\@gmail.com",
		Phone=>"(207)841-7418",
		Notify=>"2078417418\@vzwpix.com",
		Address=>"8 Island View Drive, Bailey Island, ME, 04003, USA",
		Distributor=>$MOW_Sagadahoc);
    $Staff_Rachel_Gerow
	= &obj("Staff","Rachel Gerow",
		Email=>"rgerow\@spectrumgenerations.org",
		Phone=>"(207)820-4196",
		Notify=>"2076204196\@vzwpix.com",
		Address=>"35 Union St.,Brunswick,ME,04011,US",
		Distributor=>$MOW_Sagadahoc);
    $Staff_Dianne_Alward
	= &obj("Staff","Dianne_Alward",
		Email=>"rgerow\@spectrumgenerations.org",
		Phone=>"(207)418-4226",
		Notify=>"2074184226\@mms.uscc.net",
		Address=>"1766 Federal Rd.,Livermore,ME,,US",
		Distributor=>$MOW_Livermore);

    &DBput( $MOW_Sagadahoc, "Contact",
	"$Staff_Rachel_Gerow,$Staff_Chris_Caldwell" );
    &DBput( $MOW_Livermore, "Contact",
	"$Staff_Dianne_Alward,$Staff_Chris_Caldwell" );
    }

#########################################################################
#	Process VCF files to db files appropriate for routing.cgi.	#
#	No point in re-ordering anything since routeing.cgi will do it	#
#	again.								#
#########################################################################
sub contacts_to_db
    {
    my( $outname ) = @_;

    # $COMMON::DB = $outname;
 
    &DBwrite();
    &setup_objs();

    my %endpoint;
    my %routes;

    foreach my $addr ( keys %stop )
	{
	#print "CMC processing [$addr], so=[$stop{$addr}{organization}]\n";
	if( $stop{$addr}{organization} =~ /(.*)staff$/i )
	    { $endpoint{staff} = $addr; }
	elsif( $stop{$addr}{organization} =~ /(.*)driver$/i )
	    { $endpoint{driver} = $addr; }
	elsif( $stop{$addr}{organization}
		=~ /^(Routing|)\s*(.*?)\s*(staff|driver|)$/i
		|| $stop{$addr}{organization}
		=~ /^(MOW|)\s*(.*?)\s*(staff|driver|)$/i )
	    { push( @{$routes{$2}}, $addr ); }
	}

    #
    my $orgaddr = $endpoint{staff} || $endpoint{driver};
    &COMMON::fatal("VCF requires staff or driver.") if( ! $orgaddr );
    my $distributorname =
	( $orgaddr =~ /1766 Federal/			? "MOW Livermore"
	: $orgaddr =~ /239 Temple/			? "MOW Livermore"
	: $orgaddr =~ /35 Union/			? "MOW Sagadahoc"
	: $orgaddr =~ /8 Island View/			? "MOW Sagadahoc"
	:						  "MOW Elsewhere" );
    my $tbl = "Distributor";
    my $distributorind = &findkeys( $tbl, "Name", $distributorname );

    my $np = $stop{$orgaddr}{names}[0];
    my( $contact, $phone ) = ( $np, "?" );
    ( $contact, $phone ) = ( $1, $2 ) if( $np =~ /^(.*?)\s*(\(.*\).*$)/ );

    foreach my $route ( keys %routes )
	{
	$tbl = "Route";
	my ( $routeind ) = &findkeys( $tbl, "Name", $route );
	if( defined( $routeind ) )
	    { }		# Nothing to do
	elsif( ! $CFG{ADD_NEW_ROUTES} )
	    {
	    print STDERR
		"Cowardly choosing not to define the new route [$route].\n";
	    $routeind = &Route_None;
	    }
	else
	    {
	    $routeind = &new_tagged_key($tbl);
	    my $drvaddr = $endpoint{driver} || $endpoint{staff};
	    my $np = $stop{$drvaddr}{names}[0];
	    my( $name, $phone ) = ( $np, "?" );
	    ( $name, $phone ) = ( $1, $2 ) if( $np =~ /^(.*?)\s*(\(.*\).*$)/ );
	    &DBput( $routeind, "Name",		$route		);
	    #my $notify = $phone;
	    #$notify =~ s/[^\d]*//g;
	    #$notify = $HARD_CODED_CARRIER_EMAIL{$notify} || $notify;
	    ##$notify = $HARD_CODED_CARRIER_EMAIL{2078417418};
	    #my $email = "chris.interim\@gmail.com";

	    my $staffind = &findkeys( "Staff", "Name", $name );
	    &DBput( $routeind, "Distributor",	$distributorind	);
	    &DBput( $routeind, "Driver",	$staffind	);
	    }

	$tbl = "Patron";
	my @old_patrons_on_route = &findkeys( $tbl, "Route", $routeind );
	foreach my $addr ( @{$routes{$route}} )
	    {
	    foreach my $np ( @{$stop{$addr}{names}} )
		{
		my( $name, $phone ) = ( $np, "?" );
		( $name, $phone ) = ( $1, $2 ) if( $np =~ /^(.*?)\s*(\(.*\).*$)/ );

		my ( $patronind ) = &findkeys($tbl,"Name",$name);
		if( ! $patronind  )
		    { $patronind = &new_tagged_key($tbl); }
		elsif( ! $CFG{OVERWRITE_OLD_PATRONS} )
		    {
		    print STDERR "Skipping overwrite of [$name].\n";
		    next;
		    }
		print STDERR "Adding Patron($patronind) name=$name phone=$phone route=$route address=$addr\n";
		&DBput($patronind, "Name",		$name );
		&DBput($patronind, "Route",		$routeind );
		&DBput($patronind, "Distributor",	$distributorind );
		&DBput($patronind, "Email",		"" );
		&DBput($patronind, "Phone",		$phone );
		&DBput($patronind, "Notify",		"" );
		&DBput($patronind, "Address",		$addr );
		&DBput($patronind, "Navrules",		$stop{navrules} );
		&DBput($patronind, "Coords",		$stop{$addr}{coords} );
		&DBput($patronind, "Note",		$stop{$addr}{note} );
		&DBput($patronind, "Status",		"Active" );
		&DBput($patronind, "Last_seen",		"" );
		&DBput($patronind, "Last_seen_by",	"" );
		&DBput($patronind, "Last_route",	"" );
		&DBput($patronind, "Last_note",		"" );
		@old_patrons_on_route =
		    grep( $_ ne $patronind, @old_patrons_on_route )
		    if( scalar(@old_patrons_on_route) > 0 );
		}
	    }
	# @old_patrons_on_route now consists of patrons that were in the
	# database but not in the .vcf file.
	if( $CFG{DELETE_MISSING_PATRONS} && @old_patrons_on_route )
	    {	# Don't delete them, but move them to a bogus route.
	    print STDERR join("\n\t",
	        "Removing the following patrons from route ${route}:",
		( map { &DBget($_,"Name") } @old_patrons_on_route ) ), "\n";
	    grep( &DBput($_,"Route",$Route_None), @old_patrons_on_route);
	    }
	}

    &DBpop();
    }

#########################################################################
#	Process VCF files to csv files appropriate for mapquest.	#
#########################################################################
sub contacts_to_csv
    {
    my( $outname ) = @_;

    &write_file( $outname, join("\n",
	(map {join(",",$stop{$_}{address},join(" and ",@{$stop{${_}{names}}}))} &reorder() ),
	""
	) );
    }

#########################################################################
#	Process VCF files to a simple route sheet.			#
#########################################################################
sub contacts_to_text
    {
    my( $outname ) = @_;

    my $spacer = "\t";
    foreach my $name ( map { $stop{$_}{names}[0] } keys %stop )
        {
	if( $name =~ /^(Routing\s*.*?\s*[\d]+\s*)/
	 || $name =~ /^(MOW\s*.*?\s*[\d]+\s*)/ )
	    {
	    $spacer = " " x length( $1 ) ;
	    last;
	    }
	}

    &write_file( $outname, join("\n",
	( map{$_}{ ($stop{name_string}, $spacer.$stop{$_}{address}) } &reorder() ),
	"") );
    }

#########################################################################
#	Process VCF files to coord file appropriate for best_route.	#
#	Unused.								#
#########################################################################
sub contacts_to_best_route
    {
    my( $outname ) = @_;

    &write_file( $outname, join("\n",
	"name=car0 begin=\"$stop{coords}}\" end=\"$stop{$route{endpoint}{coords}}\"",
	(map {"name=\"".$stop{name_string}."\" where=\"".($stop{$_}{coords}||"?,?").'"'}
	    &reorder()), "") );
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
    return $txtname . ":" .
	( !defined($txtdata) ? "''"
	: ( ($txtdata eq "0") || ($txtdata =~ /^[1-9]\d*$/) ) ? $txtdata
	: "'" . $txtdata . "'" );
    }

#########################################################################
#	One entry (including header)					#
#########################################################################
sub one_entry
    {
    my( $trind, $ind, $name, $phone, $address,
        $time_to, $distance_to, $total_time_to, $total_distance_to, $coords,
	$navrules, $note ) = @_;
    $phone ||= "";
    my $addrtxt =
	( $address =~ /(.*),US$/ ? $1 : $address );
#        ( $address =~ /^(.*?),\s*(.*),US$/
#	?  "<nobr>$1,</nobr> <nobr>$2</nobr>"
#	: $address );
    push( @jtable, join(",",
	&jdata("ind",$ind),
        &jdata("name",$name),
        &jdata("phone",$phone),
        &jdata("addrtxt",$addrtxt),
        &jdata("address",$address),
	&jdata("time_to",$time_to),
	&jdata("distance_to",$distance_to),
	&jdata("time_ref",$time_to),
	&jdata("distance_ref",$distance_to),
	&jdata("total_time_to",$total_time_to),
	&jdata("total_distance_to",$total_distance_to),
        &jdata("coords",$coords),
        &jdata("navrules",$navrules),
	&jdata("note",$note)
	) );
    return ( "",
	"<tr id=tr$trind onClick='setactive($trind,0);'>",	"\n\t",
	"<td align=right valign=top>$ind</td>",			"\n\t",
	"<th valign=top align=left style='white-space: nowrap;'>$name</th>",
		"\n\t",
	"<th valign=top align=left style='white-space: nowrap;' onClick='make_call($trind);'>",
	    &fake_link( $phone ), "</th>",			"\n\t",
	"<td valign=top onClick='goto_map($trind);'>",
	    &fake_link( $address ), "</td>",			"\n\t",
	"</tr>\n" );
    }

#########################################################################
#	Make a tag look prettier.					#
#########################################################################
sub pretty_tag
    {
    my( $tag ) = @_;
    $tag =~ s/::/ /g;
    return $tag;
    }

#########################################################################
#	Process VCF files to a html route sheet.			#
#########################################################################
sub contacts_to_html
    {
    my( $outname ) = @_;

    my @reordered_stops = &reorder();

    #my $TITLE = $current_route . " route ($total_distance miles)";
    my $TITLE = $current_route . " route";;

    my $trind = 0;

    my @bigtable = ( "<table frame=box cellspacing=0 cellpadding=2>" );
    foreach my $stopind ( @reordered_stops )
        {
	my $name = $stop{$stopind}{name_string};
	my $phone = "";
	if( $name =~ /^(.*?)\s*(\(\d*?\)\s*[\d][\s\d\-]*)(.*)$/ )
	    {
	    $phone = $2;
	    $name =~ s/\s*\(\d+\)[\s\d\-]*//g;	# Remove any phone numbers
	    }
	push( @bigtable,
	    &one_entry( $trind++, "", $name, $phone,
		$stop{$stopind}{address},
		$stop{$stopind}{time_to}, $stop{$stopind}{distance_to},
		$stop{$stopind}{total_time_to}, $stop{$stopind}{total_distance_to},
		$stop{$stopind}{coords},
		$stop{$stopind}{navrules},
		$stop{$stopind}{note} ) );
	}
    push( @bigtable, "</table>" );

    my $BIG_TABLE = join("",@bigtable);
    my $INIT = join("\n",
	"//{ INIT",
	"var ROUTE_LENGTH='$total_distance';",
        "var ROUTE_NAME='$current_route';",
	"var SECRET='" . &unique_id() . "';",
	"var stops =\n    [\t{" . join("},\n\t{",@jtable) . "} ];",
	"//} INIT" );

    my $template = &read_file( $TEMPLATE );

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
		    push( @epieces,
			"<$tag", $preincsrc, "incsrc='", $incsrc, "'",
			$postincsrc, ">\n",
			&read_file( $incsrc ),
			$tagbody, "\n",
			"</$tag>\n" );
		    }
		}
	    $template = join("",@epieces);
	    }
	}
    $template =~ s/%%INIT%%/$INIT/ms;
    $template =~ s/%%TITLE%%/$TITLE/gms;
    $template =~ s/%%ROUTE_NAME%%/$current_route/gms;
    $template =~ s/%%BIG_TABLE%%/$BIG_TABLE/ms;
    $template =~ s/%%COMPLETED_CGI%%/completed_route_update.cgi/ms;

    if( $outname =~ /\.htm$/i || $outname =~ /\.html$/i )
        { &write_file( $outname, $template ); }
    else
        {
	my $cmd = "$CVT -.html $outname";
	open( OUT, "| $cmd" ) || &COMMON::fatal("Cannot ${cmd}:  $!");
	print OUT $template;
	close( OUT );
	}
    }

#########################################################################
#	Main								#
#########################################################################

&parse_arguments();

#print join("\n\t","Args:",map{"$_:\t$ARGS{$_}"} sort keys %ARGS), "\n";

&read_contacts( @files );
&contacts_to_db			( $ARGS{d} )	if( $ARGS{d} );
&contacts_to_csv		( $ARGS{c} )	if( $ARGS{c} );
&contacts_to_text		( $ARGS{t} )	if( $ARGS{t} );
&contacts_to_best_route		( $ARGS{p} )	if( $ARGS{p} );
&contacts_to_html		( $ARGS{h} )	if( $ARGS{h} );

&COMMON::cleanup(0);
