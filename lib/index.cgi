#!/usr/bin/perl -w
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

my $DIRNAME = ".";

#########################################################################
#	Print an error message (to STDOUT or user can't see it.		#
#########################################################################
sub fatal
    {
    print join("<br>\n","Fatal error:\n",@_,"");
    exit(1);
    }

#########################################################################
#	Turn a filename into something prettier.			#
#########################################################################
sub pretty
    {
    my( $name ) = @_;
    $name =~ s/\.html$//;	# Get rid of the extension
    $name =~ s+.*/++g;		# And any directory
    $name =~ s+_+ +g;		# Convert underlines to spaces
    return $name;
    }

#########################################################################
#	Main								#
#########################################################################
print <<EOF;
Content-type:  text/html

<html><head></head><body>
EOF

opendir( DIR, $DIRNAME ) || &fatal("Cannot opendir($DIRNAME):  $!");
my @files = grep(/^[A-Z].*\.html/,readdir(DIR));
closedir( DIR );

print join("\n",
    "<center><table>",
    "<tr><th>Select a route</th></tr>",
    (map {"<tr><th align=left><a href='$_'>".&pretty($_)."</a></th></tr>"}
        @files ),
    "</table></center></body>","");
exit(0);
