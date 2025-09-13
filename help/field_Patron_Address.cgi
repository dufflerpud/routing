#!/usr/local/projects/routing/help/html_filter.pl
<h2 align=center>Help for the "Address" field of the "Patron" table</h2>
This field contains the address to deliver to this patron in the form:
<div class=field_format>Street address, Town, ME, nnnnn</div>
"Street" can contain information like ", Apt#1" and similar.  Although the system
usually does not require the zip code, it is often useful to disambiguate
addresses.  The underlying software tries to be smart about typos and frequently
guesses wrong unless it is absolutely sure what town it is looking in.  Zip codes
are you friend.

