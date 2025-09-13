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

sub convert
    {
    open( INF, "base64 -w 0 < $_[0] |" ) || die("Cannot open $_[0]:  $!");
    my $ret = join("","data:image/jpeg;base64,",<INF>);
    close( INF );
    return $ret;
    }


my @new = ();
foreach my $piece ( split( /(<img.*?>)/, join("",<STDIN>) ) )
    {
    if( $piece !~ /(<img.*src=)("|')(.*?)("|')(.*>)$/ )
        { push( @new, $piece ); }
    else
        { push( @new, $1, $2, &convert($3), $4, $5 ); }
    }

print join("",@new);
exit(0);
