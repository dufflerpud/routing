#!/usr/local/projects/routing/help/html_filter.pl
<h2 align=center>Problems with the Android %%MID%%</h2>
This document describes problems we've had running
the %%PRODUCT%% software under Android OS.  It is
completely likely that many of these are caused by
the developer being an inexperienced Android user, but
some reflect known bugs or limitations with
Google Maps.

<p>Problems:
<details>
    <summary>Android requires more Internet</summary>
        A route with waypoints (any routing containing
	more than one stop) will require access
	to the Internet even to remove stops along
	the way.
</details>
<details>
    <summary>Chrome restarts frequently</summary>
    	Fortunately, due to the fact that most of
	the information is kept in cookies, when
	the browser automatically reloads the page,
	it picks up the old information.  Of course,
	such a reload fail will access if you
	currently don't have connectivity to the
	Internet.
</details>
