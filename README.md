# Routing and delivery software.

Makes **HEAVY** use of cpi and common software packages.

<hr>

<table src="src/*.pl src/*.cgi src/mappers/*/*.js src/mappers/*/*.pl"><tr><th align=left><a href='#dt_86zQUiHD9'>addr_to_latlong.pl</a></th><td>Convert address to lat/long using Google</td></tr>
<tr><th align=left><a href='#dt_86zQUiHDA'>check_history.pl</a></th><td>Traverse past history directories</td></tr>
<tr><th align=left><a href='#dt_86zQUiHDB'>completed_route_update.pl</a></th><td>Obsolete software called via e-mail with older routing sw</td></tr>
<tr><th align=left><a href='#dt_86zQUiHDC'>defluff.pl</a></th><td>OBSOLETE:  Read http log files to make error messages more readable</td></tr>
<tr><th align=left><a href='#dt_86zQUiHDD'>distuser_to_pdf.pl</a></th><td>Generate pdf expense report from trip entries</td></tr>
<tr><th align=left><a href='#dt_86zQUiHDE'>embed_images.pl</a></th><td>Resolve image urls into image data</td></tr>
<tr><th align=left><a href='#dt_86zQUiHDF'>htmls_to_times.pl</a></th><td>OBSOLETE:  Get timing info from log entries</td></tr>
<tr><th align=left><a href='#dt_86zQUiHDG'>merge_routes.pl</a></th><td>OBSOLETE - merge routes with KML files</td></tr>
<tr><th align=left><a href='#dt_86zQUiHDH'>pdf_to_route.pl</a></th><td>Used for parsing foreign pdf files for routing info</td></tr>
<tr><th align=left><a href='#dt_86zQUiHDI'>read_mapquest.pl</a></th><td>OBSOLETE - Dump results of a mapquest query</td></tr>
<tr><th align=left><a href='#dt_86zQUiHDJ'>read_trips.pl</a></th><td>Suck in logged trips and create a summary</td></tr>
<tr><th align=left><a href='#dt_86zQUiHDK'>read_vcf.pl</a></th><td>Obsolete - Read vcf entries into patron database</td></tr>
<tr><th align=left><a href='#dt_86zQUiHDL'>simple_routing.pl</a></th><td>OBSOLETE - one of the first delivery routers</td></tr>
<tr><th align=left><a href='#dt_86zQUiHDM'>split_trips.pl</a></th><td>Split trips up by user, route, month</td></tr>
<tr><th align=left><a href='#dt_86zQUiHDN'>update_carriers.pl</a></th><td>Add notify e-mail addresses to database</td></tr>
<tr><th align=left><a href='#dt_86zQUiHDO'>upgrade_log_format.pl</a></th><td>Obsolete - Used to transfer old style log files to new</td></tr>
<tr><th align=left><a href='#dt_86zQUiHDP'>vcf_mail.pl</a></th><td>OBSOLETE - used for parsing e-mail from old system</td></tr>
<tr><th align=left><a href='#dt_86zQUiHDQ'>xlate_vcf.pl</a></th><td>OBSOLETE - Methods for moving data in & out of vcf files</td></tr>
<tr><th align=left><a href='#dt_86zQUiHDR'>app.cgi</a></th><td>Main routing application web interface for meal delivery service</td></tr>
<tr><th align=left><a href='#dt_86zQUiHDS'>lib.js</a></th><td>Javascript portion of Apple mapping software</td></tr>
<tr><th align=left><a href='#dt_86zQUiHDT'>lib.js</a></th><td>Javascript portion of Google mapping software</td></tr>
<tr><th align=left><a href='#dt_86zQUiHDU'>lib.js</a></th><td>Javascript portion of Mapquest routing</td></tr>
<tr><th align=left><a href='#dt_86zQUiHDV'>template.js</a></th><td>Used for creating mapquest map</td></tr>
<tr><th align=left><a href='#dt_86zQUiHDW'>lib.pl</a></th><td>Routines for using Apple routing</td></tr>
<tr><th align=left><a href='#dt_86zQUiHDX'>lib.pl</a></th><td>Routines for using Bing maps</td></tr>
<tr><th align=left><a href='#dt_86zQUiHDY'>lib.pl</a></th><td>Routines for using GeoJSON maps</td></tr>
<tr><th align=left><a href='#dt_86zQUiHDZ'>lib.pl</a></th><td>Routines for using Google routing and mapping</td></tr>
<tr><th align=left><a href='#dt_86zQUiHDa'>lib.pl</a></th><td>Routines for using GPX mapping</td></tr>
<tr><th align=left><a href='#dt_86zQUiHDb'>lib.pl</a></th><td>Routines for using KML (Google) mapping</td></tr>
<tr><th align=left><a href='#dt_86zQUiHDc'>lib.pl</a></th><td>Routines for using Mapquest routing and mapping</td></tr>
<tr><th align=left><a href='#dt_86zQUiHDd'>compress.pl</a></th><td>Routines for generating static mapquest maps (problems)</td></tr>
<tr><th align=left><a href='#dt_86zQUiHDe'>lib.pl</a></th><td>Routines for storing and saving mapping perl objects</td></tr></table>

<hr>

<div id=docs>

## <a id='dt_86zQUiHD9'>addr_to_latlong.pl</a>
Convert address to lat/long using Google

## <a id='dt_86zQUiHDA'>check_history.pl</a>
Traverse past history directories

## <a id='dt_86zQUiHDB'>completed_route_update.pl</a>
Obsolete software called via e-mail with older routing sw

## <a id='dt_86zQUiHDC'>defluff.pl</a>
OBSOLETE:  Read http log files to make error messages more readable

## <a id='dt_86zQUiHDD'>distuser_to_pdf.pl</a>
Generate pdf expense report from trip entries

## <a id='dt_86zQUiHDE'>embed_images.pl</a>
Resolve image urls into image data

## <a id='dt_86zQUiHDF'>htmls_to_times.pl</a>
OBSOLETE:  Get timing info from log entries

## <a id='dt_86zQUiHDG'>merge_routes.pl</a>
OBSOLETE - merge routes in database

## <a id='dt_86zQUiHDH'>pdf_to_route.pl</a>
Used for parsing foreign pdf files for routing info

## <a id='dt_86zQUiHDI'>read_mapquest.pl</a>
OBSOLETE - Dump results of a mapquest query
(Replace with more full explanation of what this file is or does
spread across multiple lines)

## <a id='dt_86zQUiHDJ'>read_trips.pl</a>
Suck in logged trips and create a summary

## <a id='dt_86zQUiHDK'>read_vcf.pl</a>
Obsolete - Read vcf entries into patron database

## <a id='dt_86zQUiHDL'>simple_routing.pl</a>
OBSOLETE - one of the first delivery routers

## <a id='dt_86zQUiHDM'>split_trips.pl</a>
Split trips up by user, route, month

## <a id='dt_86zQUiHDN'>update_carriers.pl</a>
Add notify e-mail addresses to database

## <a id='dt_86zQUiHDO'>upgrade_log_format.pl</a>
Obsolete - Used to transfer old style log files to new

## <a id='dt_86zQUiHDP'>vcf_mail.pl</a>
OBSOLETE - used for parsing e-mail from old system

## <a id='dt_86zQUiHDQ'>xlate_vcf.pl</a>
OBSOLETE - Methods for moving data in & out of vcf files

## <a id='dt_86zQUiHDR'>app.cgi</a>
Main routing application web interface for meal delivery service
Tested with:
on-wheels for Livermore/Farmington
on-wheels for Brunswick/Sagadahoc
Harpswell Aging at Home

## <a id='dt_86zQUiHDS'>lib.js</a>
Javascript portion of Apple mapping software

## <a id='dt_86zQUiHDT'>lib.js</a>
Javascript portion of Google mapping software
Note that this will get used by Android users and potentially	//
by Apple users running with Chrome.				//

## <a id='dt_86zQUiHDU'>lib.js</a>
Javascript portion of Mapquest routing

## <a id='dt_86zQUiHDV'>template.js</a>
Used for creating mapquest map

## <a id='dt_86zQUiHDW'>lib.pl</a>
Routines for using Apple routing

## <a id='dt_86zQUiHDX'>lib.pl</a>
Routines for using Bing maps

## <a id='dt_86zQUiHDY'>lib.pl</a>
Routines for using GeoJSON maps

## <a id='dt_86zQUiHDZ'>lib.pl</a>
Routines for using Google routing and mapping

## <a id='dt_86zQUiHDa'>lib.pl</a>
Routines for using GPX mapping

## <a id='dt_86zQUiHDb'>lib.pl</a>
Routines for using KML (Google) mapping

## <a id='dt_86zQUiHDc'>lib.pl</a>
Routines for using Mapquest routing and mapping

## <a id='dt_86zQUiHDd'>compress.pl</a>
Routines for generating static mapquest maps (problems)

## <a id='dt_86zQUiHDe'>lib.pl</a>
Routines for storing and saving mapping perl objects</div>

<hr>

There are very few routines here that aren't used by multiple
different pieces of software.









