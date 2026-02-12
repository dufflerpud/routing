#!/usr/bin/perl -w
#
#indx#	update_carriers.pl - Add notify e-mail addresses to database
#@HDR@	$Id$
#@HDR@
#@HDR@	Copyright (c) 2026 Christopher Caldwell (Christopher.M.Caldwell0@gmail.com)
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
#hist#	2026-02-12 - Christopher.M.Caldwell0@gmail.com - Created
########################################################################
#doc#	update_carriers.pl - Add notify e-mail addresses to database
########################################################################

use strict;

use lib "/usr/local/lib/perl";

use cpi_file qw( fatal cleanup read_lines );
use cpi_arguments qw( parse_arguments );
use cpi_db qw( DBwrite DBget DBpop DBput );
use cpi_vars;

our %ARGS;

my $REFDIR = "/usr/local/projects/routing/ref";

#########################################################################
#	Print an error message and show how to invoke us.		#
#########################################################################
sub usage
    {
    &fatal( @_, "Usage:  $cpi_vars::PROG" );
    };

#########################################################################
#	This information came from www.carrierlookup.com with		#
#	cut-and-paste.  It would be really nice if we could get this	#
#	information for free and periodically.				#
#########################################################################
sub read_carrier_lookups
    {
    my %carrier_to_address;
    #Parse:	mms.att.net	Mobile 		AT&T
    foreach my $line ( &read_lines( $ARGS{carriers_to_addresses} ) )
        {
	my ( $address, @carrier_toks ) = split(/\s+/,$line);
	my $carrier = join(" ",@carrier_toks);
	$carrier_to_address{$carrier} = $address;
	}

    my %phone_to_email;
    #Parse:	2076516627      Mobile  VERIZON
    foreach my $line ( &read_lines( $ARGS{phones_to_carriers} ) )
        {
	my( $phone, @carrier_toks ) = split(/\s+/,$line);
	my $carrier = join(" ",@carrier_toks );
	my $address = $carrier_to_address{$carrier};
	if( $address )
	    {
	    $phone_to_email{$phone} = "$phone\@$address";
	    #print "$phone $phone_to_email{$phone}\n";
	    }
	}

    $cpi_vars::DB = $ARGS{db};
    &DBwrite();
    foreach my $patron ( &DBget("Patron") )
        {
	my $phone = &DBget( $patron, "Phone" );
	$phone =~ s/[^\d]//g;
	if( $phone_to_email{$phone} )
	    {
	    my $notify_was = &DBget( $patron, "Notify" );
	    if( $notify_was )
	        {
		printf("%-5s %-30s %s (ok)\n",
		    $patron, &DBget($patron,"Name"),$notify_was );
		}
	    printf("%-5s %-30s %s\n",
		    $patron, &DBget($patron,"Name"),$phone_to_email{$phone} );
	    &DBput( $patron, "Notify", $phone_to_email{$phone} );
	    }
	}
    &DBpop();
    }

#########################################################################
#	Main								#
#########################################################################
%ARGS = &parse_arguments({
    switches=>
    	{
	"phones_to_carriers"	=> "$REFDIR/phones_to_carriers.cols",
	"carriers_to_addresses"	=> "$REFDIR/carriers_to_addresses.cols",
	"db"			=> "app.db",
	"verbosity"		=> 0
	}
    });
$cpi_vars::VERBOSITY = $ARGS{verbosity};

if( $ENV{script_filename} )
    {
    &fatal("Not a CGI utility") if( -exists &CGI_handler );
    &CGI_handler();
    }
else
    {
    #printf("    %-20s [%s]\n",$_.":",$ARGS{$_}) foreach sort keys %ARGS;
    &read_carrier_lookups();
    }

&cleanup( 0 );
