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

# Put constants here

my $PROG = ( $_ = $0, s+.*/++, s/\.[^\.]*$//, $_ );
my $TMP = "/tmp/$PROG.$$";
my $BASE = "/usr/local/projects/MOW";
my $CACHEDIR = "$BASE/cache";
my $TEMPLATE = "${BASE}/lib/routes.html";

my @KNOWN_EXTENSIONS = ( "vcf" );

my %ONLY_ONE_DEFAULTS =
    (
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

my %stop_address;		# Hash of stop name to address at stop
my %stop_coords;		# Hash of stop name to latitude/longitude at stop
my %stop_navrules;		# Hash of when to use address or latlong
my %stop_names;			# Hash of stop name to people at stop
my %stop_name_string;		# Hash of stop name to printable people at stop
my %points;			# Hash of magic stop names
my %stop_time_to;		# Hash of time to get to the stop
my %stop_distance_to;		# Hash of distance to the stop
my %stop_total_time_to;		# Hash of time to get to the stop
my %stop_total_distance_to;	# Hash of distance to the stop
my %stop_note;			# Hash of notes about the stop

my $total_time = 0;
my $total_distance = 0;

my $current_route;

my @problems;
my %ARGS;
my @files;
my @jtable;
my %route;


#########################################################################
#	Print message and die.						#
#########################################################################
sub fatal
    {
    print STDERR join("\n",@_), "\n";
    exit(1);
    }

#########################################################################
#	Print usage message and die.					#
#########################################################################
sub usage
    {
    &fatal( @_, "",
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
	$name = $1 if( $name =~ /^(.*?)\s*(MOW [^\d\s]+\s*\d+)\s*(.*?)$/ );
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

	if( $organization =~ /MOW.*staff/i )
	    { push( @{$points{mow}}, $stop_name ); }
	elsif( $organization =~ /MOW.*driver/i )
	    { push( @{$points{beginend}}, $stop_name ); }
	else
	    { push( @{$points{way}}, $stop_name ); }

	push( @{$stop_names{$stop_name}}, $name );
	$stop_address{$stop_name} = $addr;
	$stop_coords{$stop_name} = ($entryp->{LatLong} || "");
	$stop_coords{$stop_name} =~ s/:/,/g;
	$stop_navrules{$stop_name} = ($entryp->{Navrules} || "");
	$stop_note{$stop_name} = ( $entryp->{Note} || "");
	}
    if( ! $points{beginend} )
        {
	if( $points{mow} )
	    { $route{beginpoint} = $route{endpoint} = $points{mow}[0]; }
	else
	    {	# No endpoints?  No mowpoints?  Make something up.
	    &fatal( "No MOW Driver or MOW Staff specified.\n" .
	    	"You probably want to add one before proceeding.\n" );
	    $route{beginpoint} = $route{endpoint} = $_ = $ORIGIN{stop};
	    $stop_address{$_} = $ORIGIN{address};
	    $stop_coords{$_} = $ORIGIN{coords};
	    push( @{$stop_names{ $stop_address{$_} } }, $_ );
	    }
	}
    elsif( scalar(@{$points{beginend}}) >= 2 )
	{ $route{beginpoint}=$points{beginend}[0]; $route{endpoint}=$points{beginend}[1]; }
    elsif( ! $points{mow} )
	{ $route{beginpoint} = $route{endpoint} = $points{beginend}[0]; }
    else
	{ $route{beginpoint}=$points{mow}[0]; $route{endpoint}=$points{beginend}[0]; }

    foreach my $stop ( keys %stop_names )
	{
	my %last_name_to_names;
	my %last_name_to_phone;
	my @building;
	foreach my $name ( @{$stop_names{$stop}} )
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
	$stop_name_string{$stop} = join(", ",@building);
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
    #print STDERR "mow_sort($a=>$a,$b=>$b)\n";
    my $an = $stop_name_string{$a};
    $an = ( $an =~/MOW [^\d]+ (\d[\dA-Za-z]*)/ ? $1 : $an );
    my $bn = $stop_name_string{$b};
    $bn = ( $bn =~/MOW [^\d]+ (\d[\dA-Za-z]*)/ ? $1 : $bn );
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
        { &fatal("Cannot open ${fname}:  $!"); }
    return $ret;
    }

#########################################################################
#	Write an entire file.						#
#########################################################################
sub write_file
    {
    my( $fname, @contents ) = @_;
    open( OUT, "> $fname" ) || &fatal("Cannot write ${fname}:  $!");
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
    foreach my $stop ( @stoplist )
	{
	my $locstr;
	if( $stop_coords{$stop} )
	    { $locstr = $stop_coords{$stop}; }
	else
	    {
	    my @toks = split(/, */,$stop_address{$stop});
	    my %fld = map { $_, shift(@toks) } @HUMAN_ORDER;
	    #$locstr = join( "/", ( map { $fld{$_} } @MAPQUEST_ORDER ) );
	    $locstr = join( ",", ( map { $fld{$_} } @MAPQUEST_ORDER ) );
	    }
	push( @mapquest_locations, $locstr );
	push( @debug_list, $stop_name_string{$stop} . ": " . $locstr );
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
	$stop_time_to{$stop_name} = $last_time;
	$stop_distance_to{$stop_name} = $last_distance;
	$total_time += $last_time;
	$total_distance += $last_distance;
	$stop_total_time_to{$stop_name} = $total_time;
	$stop_total_distance_to{$stop_name} = $total_distance;
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
    my @sort0 = keys %stop_address;
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
#	Process VCF files to csv files appropriate for mapquest.	#
#########################################################################
sub contacts_to_csv
    {
    my( $outname ) = @_;

    &write_file( $outname, join("\n",
	(map {join(",",$stop_address{$_},join(" and ",@{$stop_names{$stop_address{$_}}}))} &reorder() ),
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
    foreach my $name ( map { $stop_names{$_}[0] } keys %stop_names )
        {
	next if( $name !~ /^(MOW\s*.*?\s*[\d]+\s*)/ );
	$spacer = " " x length( $1 ) ;
	last;
	}

    &write_file( $outname, join("\n",
	( map{ ($stop_name_string{$_}, $spacer.$stop_address{$_}) } &reorder() ),
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
	"name=car0 begin=\"$stop_coords{$route{beginpoint}}\" end=\"$stop_coords{$route{endpoint}}\"",
	(map {"name=\"".$stop_name_string{$_}."\" where=\"".($stop_coords{$_}||"?,?").'"'}
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
    foreach my $stop ( @reordered_stops )
        {
	my $name = $stop_name_string{$stop};
	my $phone = "";
	if( $name =~ /^(.*?)\s*(\(\d*?\)\s*[\d][\s\d\-]*)(.*)$/ )
	    {
	    $phone = $2;
	    $name =~ s/\s*\(\d+\)[\s\d\-]*//g;	# Remove any phone numbers
	    }
	push( @bigtable,
	    &one_entry( $trind++, "", $name, $phone,
		$stop_address{$stop},
		$stop_time_to{$stop}, $stop_distance_to{$stop},
		$stop_total_time_to{$stop}, $stop_total_distance_to{$stop},
		$stop_coords{$stop},
		$stop_navrules{$stop},
		$stop_note{$stop} ) );
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

    if( $outname =~ /\.htm$/i || $outname =~ /\.html$/i )
        { &write_file( $outname, $template ); }
    else
        {
	my $cmd = "$CVT -.html $outname";
	open( OUT, "| $cmd" ) || &fatal("Cannot ${cmd}:  $!");
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
&contacts_to_csv		( $ARGS{c} )	if( $ARGS{c} );
&contacts_to_text		( $ARGS{t} )	if( $ARGS{t} );
&contacts_to_best_route		( $ARGS{p} )	if( $ARGS{p} );
&contacts_to_html		( $ARGS{h} )	if( $ARGS{h} );

exit(0);
