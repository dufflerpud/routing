#!/usr/local/projects/routing/help/html_filter.pl
<h2 align=center>Help for the "Reimbursement" field of the "Distributor" table</h2>
This field contains a comma separated list of types of driving to be tracked along with their
associated reimbursement rate.  This field is in the format:
    <div class=field_format>Type=reimbursement,Type=reimbursement,...</div>
For instance:
    <div class=field_format>Volunteer_Car_Driver=0.50,Company_van=0.00,Donate=0.00</div>
When drivers log their trip, they will select what type ("Volunteer Car Driver",
"Company Van" or just "Donate" (for everything else)).  At the end of the month, the software
will generate expense reports for each driver, specifying where they drove, in what, and the
expected re-imbursement.

