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
"<html><head>
<title>REQUEST FOR CLIENT RELATED REIMBURSEMENT OF MILEAGE EXPENSES</title>
</head><body>
<center>
<table border=0 $TABLE_ARGS>
<tr><th width=33%><img src='lib/MOW_logo.jpg'></th>
    <td align=center width=33%>
	<b>NON-REIMBURSED TRAVEL EXPENSES FOR VOLUNTEER WORK</b><br>
	Generated $generated_date
    </td>
    <th width=33%><img src='lib/IRS_logo.jpg'></th></tr>
<tr><th>&nbsp;</th></tr>
<tr><td align=left width=33%><u><b>Chris Caldwell</b></u><br>
    P.O. Box 401<br>
    Bailey Island, ME 04003-0401<br>
    207-841-7418
    </td>
    <td align=center width=33%>Rate:  \$$ARGS{r}/mile</td>
    <td align=right width=33%>Distance from Home to MOW:  $ARGS{d} miles</td></tr>
</table><table border=1 $TABLE_ARGS>
<tr><th>Date</th>
    <th>Client related travel only</th>
    <th>Home to MOW to (Route) to Home</th>
    <th>Start Odometer</th>
    <th>End Odometer</th>
    <th>Total Miles</th>
    <th>Parking &amp; Tolls</th>
    <th>Total</th>
    <th>&#x2713;</th>
    </tr>
$chart_data_string
</table></center>
&nbsp;<br>
<b>No receipts attached</b>
<p>
This is a true and accurate statement of expenses incurred.
I certify that the expenses incurred are necessary and proper
amounts are claimed and are reasonable.
<center><table width=100%>
<tr><th colspan=2><br>&nbsp;<br><hr width=100%></th></tr>
<tr><th>Volunteer Signature</th>
    <th>Date Signed</th></tr>
</table></center>
</body></html>"
