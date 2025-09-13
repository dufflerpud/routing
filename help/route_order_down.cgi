#!/usr/local/projects/routing/help/html_filter.pl
<h2 align=center>Help for the <button>&darr;</button> in route ordering</h2>
In the route order menu, this button (or key) has no effect if you do
not have a patron (stop) selected.
<p>If your selected patron is in the "Start with" group, it will be
moved one stop later in the list.  If they are the last stop in the
"Start with" group, they will be removed from that group and placed in
the unordered "Optimize" group.
<p>If your selected patron is in the "Optimize" group, they will be
removed from that group and placed at the start of the "End with"
group.  This means that after the driver has completed all of the stops
in the "Start with" group and all the stops in the "Optimize" group,
this patron will be the next stop.
<p>If your selected patron is already in the "End with" group, they will
be moved one stop later in the list, but cannot ever be moved after the
last stop, the distributor.
