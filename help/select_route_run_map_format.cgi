#!/usr/local/projects/routing/help/html_filter.pl
<h2 align=center>Select map output format for selected route runs</h2>
Show the trips actually taken by the drivers for the routes and times
selected (note this information is not always available as there are
multiple conditions where the driver's GPS position is unavailable).
<p><b>You cannot select an output format until you have selected some route runs
to process.</b>  Some output formats only support a limited number of route runs.
<p>We support multiple output options for several reasons, perhaps the
most pressing is that the company Mapquest, though very successful at one time,
is not really the market leader.
<p>
The following options are currently available:
<table>
<tr><th>Option</th><th>Use</th></tr>
<tr><th align=left>Mapquest browser map</th><td>
    Mapquest is usually the preferred, displaying the requested
    information on your browser.
</td></tr>
<tr><th align=left>Google KML</th><td>
    Google KML files can be read by several different web sites and
    applications but cannot be seen directly.  This option, will download
    a file to your computer, which you can than upload to
    https://mymaps.google.com or whatever KML reader you prefer.
</td></tr>
<tr><th align=left>GPX</th><td>
    GPX files can be read by several different web sites and
    applications, for instance, Garmin, but cannot be seen directly.
    This option, will download a file to your computer, which you can than
    upload to https://mymaps.google.com or whatever GPX reader you prefer.
    Note that the GPX file format does not really support the idea of colors,
    so all of the icons and routes will be the same color.
</td></tr>
<tr><th align=left>Perl object</th><td>
    This format is a convenient way of dumping the information so that other
    undetermined software can read it.
</td></tr>
</table>
