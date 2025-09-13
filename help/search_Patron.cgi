#!/usr/local/projects/routing/help/html_filter.pl
<h2 align=center>Help for the "Patron" search menu</h2>
You can reach this menu by clicking on the 'Patrons' button
at the footer of this application.  Other operations will
also put you here with search terms already specified (such
as showing a route will show you all the patrons with the
route selected).
<p>The Patron search menu allows you to search through all the
patrons you have access to, and select which one to view.
<p>
The header for the search table shows the description of each of the columns.
If you click on the column header, you can enter a value and only show
routes with the specified value in that field.
<p>
Values in the search output are clickable:
<ul>
<li>Clicking on a <a href="record_Patron.cgi">patron</a>'s name will view information about
    that patron.
<li>Clicking the <a href="record_Distributor.cgi">distributor</a> will show you information about that distributor.
<li>Clicking on a <a href="record_Route.cgi">route</a> will show you information about that route.  Note that
    patrons can be on multiple routes.
<li>Clicking the <a href="field_Patron_Phone.cgi">phone number</a> will bring up your phone application (if
    available) with that number.
<li>Clicking the <a href="field_Patron_Address.cgi">address</a> will bring up Google directions and a map for
    getting to that patron's home address.
<li>The <a href="field_Patron_Status.cgi">Status</a> column shows the current status of the patron.  Note that
    "Active" is the only status where a patron will actually be included on
    a generated route.
<li>The <a href="field_Patron_FoodPrefs.cgi">Preferences</a> column shows the various things that make this patron
    different, such as whether or not they have animals.
<li>The <a href="field-Patron-Last_seen.cgi">Last Seen</a> column shows when the patron was last visited by a driver
    using this software.
<li>The <a href="field-Patron-Last_seen_by.cgi">Last Seen By</a> column shows which staff member last visited them.
</ul>

