#!/usr/local/bin/perl -w
#
#indx#	read_trips.pl - Suck in logged trips and create a summary
#@HDR@	$Id$
#@HDR@
#@HDR@	Copyright (c) 2024-2026 Christopher Caldwell (Christopher.M.Caldwell0@gmail.com)
#@HDR@
#@HDR@	Permission is hereby granted, free of charge, to any person
#@HDR@	obtaining a copy of this software and associated documentation
#@HDR@	files (the "Software"), to deal in the Software without
#@HDR@	restriction, including without limitation the rights to use,
#@HDR@	copy, modify, merge, publish, distribute, sublicense, and/or
#@HDR@	sell copies of the Software, and to permit persons to whom
#@HDR@	the Software is furnished to do so, subject to the following
#@HDR@	conditions:
#@HDR@	
#@HDR@	The above copyright notice and this permission notice shall be
#@HDR@	included in all copies or substantial portions of the Software.
#@HDR@	
#@HDR@	THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY
#@HDR@	KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE
#@HDR@	WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE
#@HDR@	AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT
#@HDR@	HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY,
#@HDR@	WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
#@HDR@	FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR
#@HDR@	OTHER DEALINGS IN THE SOFTWARE.
#
#hist#	2026-02-10 - Christopher.M.Caldwell0@gmail.com - Created
########################################################################
#doc#	read_trips.pl - Suck in logged trips and create a summary
########################################################################

use lib "/usr/local/lib/perl";

use cpi_db qw( DBget DBread DBclose );
use cpi_file qw( fatal echodo cleanup read_file read_lines );
use cpi_filename qw( filename_to_text text_to_filename );
use cpi_inlist qw( inlist );
use cpi_setup qw( setup );
use cpi_arguments qw( parse_arguments );
use cpi_vars;

&setup();

use strict;

# Put constants here

my $PROJECT		= "routing";
my $CLIENT		= "Consumers";
$cpi_vars::PROG		= ( $_ = $0, s+.*/++, $_ );
$cpi_vars::BASEDIR	= "/usr/local/projects/$PROJECT";

my $EMBED_IMAGES	= "$cpi_vars::BASEDIR/bin/embed_images";
my $CONVERT		= "/usr/local/bin/nene";
my $WKHTMLTOPDFBIN	= "/usr/local/bin/wkhtmltopdf";
my $WKHTMLTOPDFCMD	= "$WKHTMLTOPDFBIN --log-level none";
my $TO_MOW		= "Unknown";

my %EXTMAP		= ( "pdf"=>"o", "trips"=>"i", "htm"=>"h", "html"=>"h" );
my $generated_date	= `date +%m/%d/%Y`; chomp($generated_date);
my $TABLE_ARGS		= <<EOF;
    style='border-collapse:collapse;border-style:solid;display:table-inline;margin:0'
    width=100% cellspacing=2 cellpadding=2
EOF

our %ONLY_ONE_DEFAULTS =
    (
    "rate"		=>	"",
    "input_file"	=>	"/dev/stdin",
    "html_file"		=>	"$cpi_vars::BASEDIR/public_html/mow.html",
    "output_file"	=>	"/dev/stdout",
    "distributor"	=>	"MOW",
    "user"		=>	"Unknown driver",	# Unused
    "add_to_distance"	=>	"0.00",
    "log_file"		=>	"",
    "verbosity"		=>	"0"
    );

# Put variables here.

our @problems;
our %ARGS;
our @files;

# Put interesting subroutines here

#########################################################################
#	Print usage message and die.					#
#########################################################################
sub usage
    {
    &fatal( join("\n", @_, "",
	"Usage:  $cpi_vars::PROG <possible arguments>","",
	"where <possible arguments> is:",
	"    -i <trip file>",
	"    -d <Distributor>",
	"    -u <Driver>",
	"    -h <HTML file to generate>",
	"    -o <PDF made from HTML file>",
	"    -t <template containing look and feel>",
	"    -r <rate_string>"
	), 0 );
    }

#########################################################################
#	Make sure comma separated list is always in same order.		#
#########################################################################
sub standardize_route
    {
    my( $ratestr ) = @_;
    return join(", ", sort split(/, */,$_[0]) );
    }

#########################################################################
#	Return the database index of something with the supplied name.	#
#	Third argument is a flag with what to return if failed.	#
#	Undefined causes fatal error.					#
#########################################################################
sub map_name_to_ind
    {
    my( $table, $name, $retval ) = @_;
    foreach my $ind ( &DBget($table) )	# Who doesn't like a nice linear search?
	{
	my $checkname = &DBget( $ind, "Name" );

	return $ind
	    if( $checkname eq $name
	     || &text_to_filename($checkname) eq $name );
	}
    return $retval if( defined($retval) );
    &fatal("Cannot map $name to an index in the $table table.");
    }


#########################################################################
#	Filter the data							#
#########################################################################
sub filter
    {
    my %total_elapsed_per_category;
    my %total_distance_per_category;
    my %total_cost_per_category;
    my $total_elapsed = 0;
    my $total_distance = 0;
    my $total_cost = 0;
    my %rates;
    my $donation_percentage = 0;
    my $donation_maximum;
    my $ncolumns =
	(
	&inlist( $ARGS{distributor},
	    "MOW_Sagadahoc",
	    "MOW_Lincoln",
	    "MOW_Cohen_Community_Center" )
	    ? 6
	    : 8
	);
    if( ! $ARGS{rate} || $ARGS{rate} !~ /\d/ )
	{
	&DBread() || &fatal("Cannot opendb($cpi_vars::DB):  $!");
	my $distributor_ind = &map_name_to_ind( "Distributor", $ARGS{distributor} );
	my $staff_ind = &map_name_to_ind( "Staff", $ARGS{user} );
	$ARGS{rate} = &DBget( $distributor_ind, "Reimbursement" );
	$donation_percentage =
	    &DBget( $staff_ind, "Donation_percentage" )
	    || 0;
	$donation_maximum =
	    &DBget( $staff_ind, "Donation_maximum" )
	    || 0;
	&DBclose();
	}

    my $PAGE_CONTENTS = &read_file(
	"$cpi_vars::BASEDIR/Distributors/$ARGS{distributor}/invoice.pl" );

    foreach $_ ( split(/,/,$ARGS{rate}) )
	{
	if( $_ !~ /(.*)=(.*)/ )
	    { print STDERR "Ignoring rate [$_].\n"; }
	else
	    {
	    $rates{$1}=$2;
	    $total_elapsed_per_category{$1}=$total_distance_per_category{$1}=$total_cost_per_category{$1}=0;
	    }
	}

    &fatal("Cannot write $ARGS{log_file}:  $!")
        if( $ARGS{log_file} && ! open(OUT,">$ARGS{log_file}") );

    my @chart_data = ();
    foreach my $line ( &read_lines($ARGS{input_file}) )
        {
	my ($dt,$da,$de,$diststring,$townlist) = split(/\t+/,$line);
	my( $distance, $stype ) =
	    ( $diststring =~ /^([0-9\.]+)@([A-Za-z].+)/
	    ? ($1,$2)
	    : ($diststring,"Unknown") );
	if( $dt =~ m:(\d+)/(\d+)/(\d+): )
            { $dt = sprintf("%04d-%02d-%02d",$3,$1,$2) }
	elsif( $dt =~ m:(20\d\d)(\d\d)(\d\d): )
            { $dt = sprintf("%04d-%02d-%02d",$1,$2,$3) }
	$distance = sprintf("%.1f",$distance+$ARGS{add_to_distance});
	$diststring = $distance.$stype;
	print OUT "$dt\t$da\t$diststring\t$townlist\n" if( $ARGS{log_file} );
	my $othercost = 0;
	print STDERR "distance=",($distance||"UNDEF"),
		" stype=",($stype||"UNDEF"),
		" rates=",($rates{$stype}||"UNDEF"), ".\n";
	my $cost = sprintf("%.2f", $distance * $rates{$stype} + $othercost );
	if( $ncolumns == 6 )
	    { push( @chart_data,
	    "<tr><td valign=top>",			$dt,
	    "</td><td valign=top align=right>",		$de,
	    "</td><td valign=top>",			"$townlist route",
	    "</td><td valign=top align=right>",		$distance,
	    "</td><td valign=top align=right>\$",	sprintf("%.2f",$rates{$stype}),
	    "</td><td valign=top align=right>\$",	sprintf("%.2f",$cost),
	    "</td></tr>\n" ); }
	else
	    { push( @chart_data,
	    "<tr><td valign=top>",			$dt,
	    "</td><td valign=top>",			$CLIENT,
	    "</td><td valign=top>",			$townlist,
	    "</td><td valign=top align=right>",		sprintf("%.1f",0),
	    "</td><td valign=top align=right>",		$distance,
	    "</td><td valign=top align=right>",		$diststring,
	    "</td><td valign=top align=right>\$",	sprintf("%.2f",$othercost),
	    "</td><td valign=top align=right>\$",	sprintf("%.2f",$cost),
	    "</td><td>",				"&nbsp",
	    "</td></tr>\n" ); }
	my( $elapsed ) = ( $de =~ /(\d+):(\d+)/ ? $1*60+$2 : $de );
	$total_distance_per_category{$stype} += $distance;	$total_distance += $distance;
	$total_cost_per_category{$stype} += $cost;		$total_cost += $cost;
	$total_elapsed_per_category{$stype} += $elapsed;	$total_elapsed += $elapsed;
	my $lll = $total_elapsed_per_category{$stype};
	#my $lll = 123;
	}
    close( OUT ) if( $ARGS{log_file} );

    foreach my $stype ( keys %total_distance_per_category )
	{
	next if( ! $total_distance_per_category{$stype} );
	$total_cost_per_category{$stype} = sprintf( "%.2f", $total_cost_per_category{$stype} );
	if( $ncolumns == 6 )
	    { push( @chart_data, "<tr><th>".&filename_to_text(${stype})." totals</th>",
		"<td align=right>",
		    sprintf("%d:%02d",$total_elapsed_per_category{$stype}/60,$total_elapsed_per_category{$stype}%60),"</td>",
		"<td></td>",
		"<td align=right><b>",
		    sprintf("%.1f",$total_distance_per_category{$stype}),
		    "</b></td>",
		"<td align=right></td>",
		"<td align=right><b>\$", $total_cost_per_category{$stype}, "</b></td>",
		"</tr>\n" ); }
	else
	    { push( @chart_data, "<tr><th>Totals</th>",
		"<td></td><td></td><td></td><td></td>",
		"<td align=right><b>",
		    sprintf("%.1f",$total_distance_per_category{$stype}), "</b></td>",
		"<td></td>",
		"<td align=right><b>\$", $total_cost_per_category{$stype}, "</b></td>",
		"<td></td></tr>\n" ); }
	}

    my $chart_data_string = join("",@chart_data);
    my $donation = $total_cost * $donation_percentage / 100;
    $donation = sprintf("%.2f",
	$donation>$donation_maximum ? $donation_maximum : $donation );
    my $net_request = sprintf("%.2f",$total_cost - $donation);
    my $page = eval( $PAGE_CONTENTS );
    #print "Error was [$@]\n";
    #print STDERR "errmessage=[$@]\n" if( $ARGS{verbosity} );

    open( OUT, "| $EMBED_IMAGES > $ARGS{html_file}" )
	|| &fatal("Cannot write $ARGS{html_file}:  $!");
    print OUT $page;
    close( OUT );

    #&echodo("$CONVERT $ARGS{html_file} $ARGS{output_file}");
    &echodo("$WKHTMLTOPDFCMD $ARGS{html_file} $ARGS{output_file}");
    }

#########################################################################
#	Main								#
#########################################################################

&parse_arguments();
$cpi_vars::VERBOSITY = $ARGS{verbosity};

#print join("\n\t","Args:",map{"$_:\t$ARGS{$_}"} sort keys %ARGS), "\n";

&filter();

&cleanup(0);
