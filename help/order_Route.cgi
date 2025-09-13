#!/usr/local/projects/routing/help/html_filter.pl
<h2 align=center>Help for setting a route's order</h2>
Routing is done by dividing the active patrons into a route order in 3 phases:
<ul>
<li>Starting - the distributor followed by zero or more patrons in a particular order
<li>Optimize - followed by zero or more patrons which can be re-ordered to make the fastest route
<li>Ending - followed by zero or more patrons in a particular order, followed by the distributor
</ul>
<p>Routes always start and end with the distributor, but every patron can be selected and moved in
the order by clicking on the patron and then hitting the <button>&uarr;</button> or <button>&darr;</button>.
<em>Note</em> that the order in the "Optimize" section is ignored since it will be optimized when the
<a href="Route_sheet.cgi">route sheet</a> is generated.  Note that your new route order will not be saved until you hit
<button>Update</button>.
<p>Click <button>&larr;</button> to navigate to the previous menu.

