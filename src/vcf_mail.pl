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

my $PROJECT = "Routing";
my $PROG = ( $_ = $0, s+.*/++, s/\.[^\.]*$//, $_ );
my $BASEDIR = "/usr/local/projects/$PROJECT";
my $VCFDIR = "$BASEDIR/vcf";
my $DOMAIN = "Brightsands.com";
my $SENDMAIL_FROM = "Meals on Wheels router <$PROJECT\@$DOMAIN>";
my $URL_DIR = "https://$PROJECT.$DOMAIN/routes";
my $LOG_BASE = "/var/log/$PROJECT/$PROG";

my %LOG_FILES =
    (
    "STDOUT"	=> $LOG_BASE . "/stdout",
    "STDERR"	=> $LOG_BASE . "/stderr",
    "LOG"	=> $LOG_BASE . "/log",
    "SMTP"	=> $LOG_BASE . "/smtp"
    );

$ENV{PATH}="/sbin:/bin:/usr/sbin:/usr/bin:/usr/local/bin:/opt/aws/bin";

close( STDOUT );
close( STDERR );
open( STDOUT,	"> $LOG_FILES{STDOUT}"	);
open( STDERR,	"> $LOG_FILES{STDERR}"	);
open( LOG,	"> $LOG_FILES{LOG}"	);
system("id -a");

my $last_file;
my $reply_to;
my $boundary;
my %new_urls;

while( $_ = <STDIN> )
    {
    chomp( $_ );
    print LOG "$_\n";
    if( m:filename="([^/]*)"$: || m:filename=([^/]*)$: )
	{
	$last_file = $1;
	$last_file =~ s/\.vcf//;
	$last_file =~ s+$PROJECT ++g;
	$last_file =~ s:[^A-Za-z0-9_\.]+:_:g;
	$last_file = $1 if( $last_file =~ /^_*(.*?)_*$/ );
#	print "if-1 last_file=[$last_file]\n";
	}
    elsif( m=^From:.*?<(.*@.*)>= || m=^From:\s*([^\s]+@[^\s]+)= )
        {
	$reply_to = $1;
#	print "if-2 reply_to=[$reply_to]\n";
	}
    elsif( m~^Content-Type: multipart/mixed; boundary=(.*)$~ )
	{
	$boundary = $1;
#	print "if-3 boundary=[$boundary]\n";
	}
    elsif( /Encoding: quoted-printable$/ && $last_file )
        {
##	print "if-4 looking for empty.\n";
#	while( $_ = <STDIN> )
#	    {
#	    chomp( $_ );
#	    print "Read [$_]\n";
#	    last if( $_ eq "" );
#	    }
	my @contents = ();
#	print "if-4 sucking in data.\n";
	while( $_ = <STDIN> )
	    {
	    print LOG $_;
	    s/[\r\n]//gs;
	    # chomp( $_ );
	    #print "Read [$_]\n";
	    last if( /^--(.*)/ && $1 eq $boundary );
	    #s/=$//gs;
	    #last if( ! /^(.*)=$/ );
	    if( $_ =~ /^(.*)=$/ )
		{ push( @contents, $1 ); }
	    else
		{ push( @contents, $_, "\n" ); }
	    #print "Pushing [$_]\n";
	    }
#	print "if-4 data sucked in, contents=",scalar(@contents),".\n";

	if( @contents )
	    {
	    #print "Have contents...\n";
	    my $outstring = join("",@contents);
	    $outstring =~ s/=([A-F0-9][A-F0-9])/pack("C", hex($1))/giems;
	    $outstring =~ s/\r//gms;
	    $_ = "$VCFDIR/$last_file.vcf";
	    open( OUT, ">$_" ) || die("Cannot write ${_}:  $!");
	    binmode OUT;
	    print OUT $outstring;
	    close( OUT );
	    
	    $new_urls{$last_file} = "$URL_DIR/$last_file.html";

	    chdir( $BASEDIR ) || die("Cannot chdir($BASEDIR):  $!");
	    system( "make vcfs_html vcfs_db" );
	    }
	}
    }

print "E-mail parsed.\n";
print "New_urls = ", %new_urls, "\n";
print "reply_to = ", ( $reply_to || "UNDEFINED" ), "\n";

my @smtp_data = ( "From:  Meals on Wheels router <mow\@$DOMAIN>" );
push( @smtp_data, "To:  $reply_to" ) if( $reply_to );
if( ! %new_urls )
    { push(@smtp_data,"Subject:  Messages from route processing"); }
else
    {
    my @routes = sort keys %new_urls;
    push( @smtp_data,
	"Subject:  Routes for ".join(", ",@routes),
	"",
	(map { sprintf("%-25s%s",$_.":",$new_urls{$_}) } @routes) );
    }

close( STDOUT );
close( STDERR );
close( LOG );

open( INF, $LOG_FILES{STDERR} ) || die("Cannot open $LOG_FILES{STDERR}:  $!");
push( @smtp_data, "", "STDERR:" );
while( $_ = <INF> )
    {
    chomp( $_ );
    push( @smtp_data, "\t" . $_ );
    }
close( INF );

open(SENDMAIL,"> $LOG_FILES{SMTP}") || die("Cannot write $LOG_FILES{SMTP}: $!");
print SENDMAIL join("\n",@smtp_data,"");
close( SENDMAIL );

system("/usr/lib/sendmail -t < $LOG_FILES{SMTP}") if( $reply_to );
exit(0);
