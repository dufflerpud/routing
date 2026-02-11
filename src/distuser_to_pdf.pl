#!/usr/local/bin/perl -w
#
#indx#	distuser_to_pdf.pl - Generate pdf expense report from trip entries
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
#doc#	distuser_to_pdf.pl - Generate pdf expense report from trip entries
########################################################################

use strict;

use lib "/usr/local/lib/perl";

use cpi_file qw( fatal echodo mkdirp files_in tempfile cleanup );
use cpi_send_file qw( sendmail );
use cpi_arguments qw( parse_arguments );
use cpi_perl qw( quotes );
use cpi_filename qw( text_to_filename );
use cpi_vars;

# Put constants here

my $PROJECT = "routing";
my $PROG = ( $_ = $0, s+.*/++, s/\.[^\.]*$//, $_ );
my $TRIP_DIR="/var/log/$PROJECT/trips";
my $BASEDIR = "/usr/local/projects/$PROJECT";
my $SPLIT_TRIPS = "$BASEDIR/bin/split_trips";
my $READ_TRIPS = "$BASEDIR/bin/read_trips";
my $SIGN = "/var/www/www/sto/sign/index.cgi";

my $DEFAULT_DISTRIBUTOR = "MOW_Sagadahoc";
my $DEFAULT_DRIVER = "Chris_Caldwell";

our %ONLY_ONE_DEFAULTS =
    (
    #"i"	=>	"/var/log/routing/trips/$DEFAULT_DISTRIBUTOR/$DEFAULT_DRIVER/log",
    "input_file"	=>	"",
    "tempdir"		=>	&tempfile(".dir"),
    "distributor"	=>	$DEFAULT_DISTRIBUTOR,
    "rate" 		=>	"",
    "user"		=>	$DEFAULT_DRIVER,
    "output"		=>	"/tmp/fun.pdf",
    "month"		=>	"",
    "verbosity"		=>	0
    );

# Put variables here.

our @problems;
our %ARGS;
our @files;
our $exit_stat = 0;

#########################################################################
#	Print usage message and die.					#
#########################################################################
sub usage
    {
    &fatal( @_, "",
	"Usage:  $PROG <possible arguments>","",
	"where <possible arguments> is:",
	"    -output <output file or e-mail address>",
	"    -rate x.xx",
	"    -user <driver>",
	"    -distributor <distributor>",
	"    -month yyyy-mm",
	"    -verbosity 0 or 1"
	);
    }

#########################################################################
#	Find all the trip files, sort them by yearmonth, make reports	#
#	and congretate them all into one gigantic .pdf file.		#
#########################################################################
sub do_it
    {
    my $trips_dir = "$ARGS{tempdir}/$ARGS{distributor}/$ARGS{user}";
    my %fnames =
	(
	log	=> $ARGS{input_file}||$trips_dir."/log",
	data	=> $trips_dir,
	trips	=> $trips_dir."/trips",
	htmls	=> $trips_dir."/htmls",
	pdfs	=> $trips_dir."/pdfs"
	);

    chdir( $BASEDIR ) || &fatal("Cannot chdir($BASEDIR):  $!");
    &mkdirp( 0755, $fnames{data}, $fnames{htmls}, $fnames{pdfs} );

    &echodo(
	    $SPLIT_TRIPS,
	    "-v",	$ARGS{verbosity},
	    "-i",	$fnames{log},
	    "-o",	$fnames{data}
	    );

    my @pdfs = ();
    my $l4 = $ARGS{month};
    $l4 = "$1-$2" if( $l4 && $l4 =~ /(\d\d\d\d)(\d\d)/ );
    #foreach my $trips_file ( grep( /\d\d\d\d-\d\d-\d\d/, readdir(D) ) )
    print STDERR "Looking for [$l4] in [$fnames{trips}]\n";
    foreach my $trips_file ( &files_in($fnames{trips},"\\d\\d\\d\\d-\\d\\d-\\d\\d.*") )
	{
	next if( $l4 && $trips_file !~ /^$l4/ );
	print STDERR "Processing $fnames{trips}/$trips_file.\n" if( 1 || $ARGS{verbosity} );
	&echodo(
	    $READ_TRIPS,
	    ( $ARGS{rate} ? ("-r", $ARGS{rate}) : () ),
	    "-d",	$ARGS{distributor},
	    "-u",	$ARGS{user},
	    "-i",	"$fnames{trips}/$trips_file",
	    "-h",	"$fnames{htmls}/$trips_file.html",
	    "-o",	"$fnames{pdfs}/$trips_file.pdf"
	    );
	push( @pdfs, "$fnames{pdfs}/$trips_file.pdf" );
	&echodo("ls -ld '$fnames{pdfs}/$trips_file.pdf'");
	}

    if( ! @pdfs )
        { &fatal("No expenses/trips to report for $ARGS{distributor}."); }
    elsif( $ARGS{output}=~/^sign:(.*):(.*)/ || $ARGS{output}=~/^sign:(.*)/ )
        {
	my $sign_user = $1;
	my $mailto = $2;
	&mkdirp( 0755, $ARGS{tempdir} );
	my $filepiece = "$ARGS{distributor}-$ARGS{user}";
	$filepiece .= "-$ARGS{month}" if( $ARGS{month} );
	$filepiece .= "-log.pdf";
	my $outfile = "$ARGS{tempdir}/".&text_to_filename($filepiece);
        &echodo( "pdfunite",@pdfs,$outfile );
	if( $mailto )
	    { &echodo($SIGN,"handoff",&quotes($sign_user,$outfile,$mailto)); }
	else
	    { &echodo($SIGN,"handoff",&quotes($sign_user,$outfile)); }
	}
    elsif( $ARGS{output} =~ /\@/ )
	{
	my $outfile = &tempfile(".pdf");
        &echodo( "pdfunite",@pdfs,$outfile );
	my $msg = "$ARGS{distributor} log of $ARGS{user}";
	$msg .= sprintf(" of %s",$ARGS{month}) if( $ARGS{month} );
	$msg =~ s/_+/ /g;
	&sendmail( "$PROJECT\@$cpi_vars::DOMAIN",$ARGS{output},$msg,
	    "$msg in enclosed PDF file.\n", $outfile );
	}
    else
        { &echodo( join(" ","pdfunite",@pdfs,$ARGS{output}) ); }
    }

#########################################################################
#	Main								#
#########################################################################

&parse_arguments();
$ARGS{input_file} ||= "$TRIP_DIR/$ARGS{distributor}/$ARGS{user}.log";
$cpi_vars::VERBOSITY = $ARGS{verbosity};

#print join("\n\t","Args:",map{"$_:\t$ARGS{$_}"} sort keys %ARGS), "\n";

&do_it();

&cleanup(0);
