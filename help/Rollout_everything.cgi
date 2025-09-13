#!/usr/local/projects/routing/help/html_filter.pl
<h2>Goals for automating more of the coordinator/driver/patron triad</h2>
    <ul>
    <li>Decrease errors in data-entry by having those closest to data
        be the ones entering it.</li>
    <li>Optimize driver resources on the road and use of volunteer resources.</li>
    <li>Increase amount of time available for coordinators to communicate with
        patrons and drivers, or alternately, make it possible for coordinators
	to handle more routes without reducing quality interaction with
	patrons and volunteers.</li>
    <li>Automate more institutional memory - keep more complete records.  Allow
        easier hand-offs between coordinators.</li>
    <li>Allow better monitoring of driver's progress throughout route delivery.</li>
    </ul>
<h2>Long term goals</h2>
    <ul>
    <li>Improve patron's privacy by reducing amount of copyable paper changing hands
        between coordinators, drivers and patrons.</li>
    <li>Improve periodic balancing of resources (such as driver time).</li>
    <li>Improve uniformity of experience of coordinators and drivers as they move
        from distributor to distributor.</li>
    <li>Improve predictive maintenance as we retain better tracking of mileage of
        vehicles we maintain.</li>
    <li>Realistically, US Federal requirements for record keeping may
        modify the modus operandi of meal delivery programs, requiring more complete
	information.  It is our feeling that putting an easy interface in place
	that can be readily extended for new recordkeeping requirements that also
	improves the efficiency of existing staff and volunteers may be the best
	bet to hedge against such onerous changes.</li>
    <li>Ultimately, as is true with most automation, the goal here is to do more
        with fewer resources - particularly do more with less labor.  The earlier
	the system can detect problems, for instance, the less time is wasted by
	coordinators and drivers fixing them.  It is our feeling that this will
	always be a pressure point, but we most definitely do not want to be
	sacrificing face-to-face time non-bookkeeping time with our patrons.
    </ul>
<h2>Specific roadblocks to avoid</h2>
    <ul>
    <li>Intent is to improve/increase quality time drivers have to work with patrons,
        by making the mundane parts of the job more efficient.
	With the exception of implementation/training time, this objective fails
	if data entry etc requires more driver time than they are spending now.</li>
    <li>Intent is to improve/increase quality time coordinators have to work with
	patrons, by making the mundane parts of the job more efficient.  With the
	exception of implementation/training time, this objective fails if data
	entry etc requires more coordinator time than they are spending now.</li>
    <li>As is true with automating <b>anything</b> in the car, these tools
        have the potential for decreasing driver safety by unnecessarily grabbing
	driver attention.  Delivery companies (e.g. UPS) have found that if you
	provide enough of the right information and avoid superfluous information, 
	it can actually improve driver safety, but this is easy to get wrong with
	dire consequences.</li>
    </ul>
<h2>Rollout for Brunswick MOW</h2>
I would envision the following steps:
    <ol class=checkoff>
    <li>Have the coordinator run through all the bells and whistles of
        software including everything a patron and driver would do.  Notably,
	this would include:
	<ol class=checkoff>
	<li>Driver sign-up:
	    <ol class=checkoff>
	    <li>Generating a driver sign-up sheet (printing it out)</li>
	    <li>Filling out printed sheet and entering the data as coordinator</li>
	    <li>Following the QR code on the top and filling the data out on
		the web form, OKing the submission as coordinator</li>
	    <li>We expect that this process will cause the coordinator
	        to request multiple modifications to the form.</li>
	    </ol></li>
	<li>Patron sign-up:
	    <ol class=checkoff>
	    <li>Generating a patron sign-up sheet (printing it out)</li>
	    <li>Filling out printed sheet and entering the data as coordinator</li>
	    <li>Following the QR code on the top and filling the data out on
		the web form, OKing the submission as coordinator</li>
	    <li>We expect that this process will cause the coordinator
	        to request multiple modifications to the form.</li>
	    </ol></li>
	</ol>
    <li>Find a group of drivers willing to use the new format route sheet
        the same way they use the standard route sheet.  Present a driver
	sign-up sheet to each of them and handle those who fill it out
	by hand and those who fill out the form by following the QR code.</li>
    <li>Find a group of drivers willing to use the new format route sheet's
        QR codes to program their %%MID%%s.</li>
    <li>Find a group of drivers willing to use the new format route sheet
        and follow the QR codes to log their entries.</li>
    <li>Sign up a new patron using the signup sheet on paper, enter that
        data into both the old and new systems.
    <li>Sign up a new patron using the signup sheet with QR code and then
        add that data to the old system from the record stored in the new
	system.
    <li>Create a procedure for importing patrons, people and routes from
	the old system</li>
    <li>Import from the old system and run in parallel where possible.  Resolve
        problems and repeat.</li>
    <li>Cutover:
        <ol class=checkoff>
	<li><b>Flag day:</b>  Import data from the old system and run on the
	    new system, with old system in "stand-by/read-only" mode.</li>
	<li>If new system fails and cannot be made to work sufficiently, bring
	    old system to ready mode and put new system in stand-by/read-only mode.
	    Import recent changes to the new system back to the old system.</li>
	<li>Repeat cutover as necessary until stable.</li>
	</ol>
    <li>Decommission old system when new system deemed totally stable.</li>
    </ol>
