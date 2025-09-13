#!/usr/local/projects/routing/help/html_filter.pl
<h2 align=center>Help for the <button>&uarr;</button> in route ordering</h2>
In the route order menu, this button (or key) has no effect if you do
not have a patron (stop) selected.
<p>If your selected patron is in the "End with" group, it will be
moved one stop earlier in the list.  If they are the first stop in the
"End with" group, they will be removed from that group and placed in
the unordered "Optimize" group.
<p>If your selected patron is in the "Optimize" group, they will be
removed from that group and placed at the end of the "Start with"
group.  This means that before the driver has done all of the stops
in the "Optimize" group and all the stops in the "End with" group,
this patron will be the last stop (after all the other "Start with" stops).
<p>If your selected patron is already in the "Start with" group, they will
be moved one stop earlier in the list, but cannot ever be moved before the
first stop, the distributor.
