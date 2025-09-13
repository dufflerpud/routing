#!/usr/bin/perl -w
use strict;

my $need_headers = ( $ARGV[0] =~ /Driver/ );
$need_headers = ( !$ENV{REQUEST_URI} || $ENV{REQUEST_URI} !~ /embedded/ );

sub fatal
    {
    print STDERR @_, "\n";
    exit(1);
    }

sub read_file
    {
    my( $url, $orelse ) = @_;
    if( ! open( INF, $url ) )
        {
	return $orelse if( defined($orelse) );
	&fatal("Cannot open [$url]:  $!");
	}

    my @lines = <INF>;
    close( INF );
    shift @lines if( $lines[0] =~ /^#!/ );
    return join("",@lines);
    }

sub read_url
    {
    return &read_file( @_ );
    }

my %includes;
my %display;
sub read_url_with_includes
    {
    my( $base_url ) = @_;
    my @todo = ( $base_url );
    while( my $url = shift(@todo) )
        {
	if( ! $includes{$url} )
	    {
	    $includes{$url} = "in progress";
	    my @new_include;
	    foreach my $piece (
		split( /(<details[^>]*href=.*?>)/,
		&read_url($url) ) )
		{
		if( $piece !~ /^(<details.*)href=["']*(.*?)["']([^>]*>)/ )
		    { push( @new_include, $piece ); }
		else
		    {
		    my( $before, $newurl, $after ) = ( $1, $2, $3 );
		    push( @new_include,
			$before,
			"ontoggle='setup_include(this,\"$newurl\");'",
			$after );
		    push( @todo, $newurl );
		    }
		}
	    $includes{$url} = join("",@new_include);
	    $display{$url} = "none";
	    }
	}
    $display{$base_url} = "block";
    }

&read_url_with_includes( $ARGV[0] );
my @includes = grep( $_ ne $ARGV[0], keys %includes );
#@includes = ();
push( @includes, $ARGV[0] );
my $content = join("",
    ( map { "<span id='$_' style='display:$display{$_}'>$includes{$_}</span>" }
        @includes ) );
$content =~ s/%%PRODUCT%%/Volunteer Delivery Routing/gms;
$content =~ s/%%MID%%/Mobile Internet Device/gms;
$content =~ s/%%YOURCOORDINATOR%%/your coordinator/gms;
print "Content-type:  text/html\n\n<html>";
if( ! $need_headers )
    { print "<body>\n"; }
else
    {
    print
	"<head><style>\n", &read_file( "help.css" ), "</style>\n",
	"<script>\n", &read_file( "html_filter.js" ), "</script>\n",
	"</head>\n<body onload='reset_sbs(\"none\");'>\n",
	"<form><iframe onerror='iframe_error(this);' id=loading_frame onload='iframe_loaded(this);' style='display:none'></iframe>\n";
    }

print $content;

if( $need_headers )
    {
    print
	"<button class='helpfoot' style='display:none;position:fixed;top:0%;left:0%' onClick='history.back(); return false;'>&larr;</button>\n",
	"<button class='helpfoot' style='position:fixed;top:1%;right:1%' onClick='(parent.done_help?parent.done_help():window.close());'>X</button>\n",
	"</form>\n";
    }
print "</body></html>\n";
