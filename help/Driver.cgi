#!/usr/local/projects/routing/help/html_filter.pl
<h2 align=center>%%PRODUCT%% Driver Documentation</h2>

Click or press the arrow to see or hide its corresponding section.

<details><summary>Just a piece of paper</summary>
    Your first exposure to %%PRODUCT%% will be a replacement route sheet with
    all of the information you're used to seeing on the old sheet.  Yes, it
    has more stuff on it, but you can safely ignore what you're not using and
    do everything you were doing before:
    <ul>
	<li>You drive to the addresses specified on the piece of paper just as before.</li>
	<li>You read notes about each stop, along with color coded things to be aware of.</li>
        <li>You write notes on it just as before.</li>
	<li>You turn it in to %%YOURCOORDINATOR%%, just as before.</li>
    </ul>
    <b>Most important</b>:  You can continue to do this with no access to the Internet or any %%MID%%.
    <b>If all else fails, revert to this!</b>
</details>

<details><summary>Convenient way of programming your %%MID%% mapper</summary>
    For the more adventurous, you'll notice a QR code (square of dots) at the
    top left of the route sheet.  Continue to ignore this QR code.

    <p>If you are reading this, you may already have clicked on the QR code
    on the top right of the route sheet.  It leads to this documentation.

    <p>You'll also notice QR codes to the left of each person receiving
    food on your route.  You'll can use these codes to program your %%MID%%'s
    mapping software.  In fact, you'll probably only use the code to the
    left of the <em>first</em> stop, as that will allow you to easily program
    the rest of route.

    <p>QR codes require access to the Internet, so you'll need to
        connect your %%MID%% to the Internet.
	You may as well configure "CarPlay" or "Android Auto" if
	your car supports them.
	<details href="Mobile_Internet_devices.cgi"><summary>Connecting to the Internet and your vehicle</summary>
	    This would be documentation on how to connect to your
	    Internet and vehicle.
	</details>

    <p>The QR codes next to each person contain the URL for using Google
    maps (available on common %%MID%%s such as iOS and Android).  Point
    your %%MID%%'s camera at the QR code to the left of the first stop
    and follow the link.  It will program your GPS mapper with a route
    starting at that stop in an order determined by %%YOURCOORDINATOR%%
    and optimized for time.  As you complete each stop, you'll simply
    need to tell your mapper that you are headed to the next stop.

    <p>If you need to restart (or switch out) your %%MID%%, you can
    simply point the device camera to the QR code next to the next stop
    and click to continue.  Do <em>not</em> go back to the QR codes of
    earlier stops unless you wish to repeat sections of the route.

    <details><summary>If you've never used GPS mapping before</summary>
        This is a cool thing to know how to use even if you don't use it for
	delivering.  Indeed, most drivers who have had smart phones for more
	than a week have tried it, and for more than a year, use it regularly.
	If this describes you, you can safely skip this section.

	<p>Mapping software does not read minds.  Once you have programmed
	in a route, it will doggedly try to take you to next stop, it will doggedly
	try to take you there.  If you want to skip
	a stop, you can edit the stop list using your %%MID%%
	mapping software.  Over time, you will get used to many of the cool
	features your %%MID%% mapper supports, but this document
	does not attempt to describe them, only to state that you can use the
	QR code to set them up in seconds.

	<p>Note that you'll need to be able to access the Internet at the
	time you use the QR code feature, <em>but</em> once your GPS is
	programmed, it should function the way it always does (which will
	handle going in and out of Internet range).

	<p>Which is to say, once you are on your route on Google maps, you don't
	need to access the Internet unless you leave the route.  When this
	happens, you'll tend to see a message like "Rerouting" on your %%MID%%
	(or on your car screen).  It will usually leave the
	route you were on displayed while it is trying to figure out what is
	happening, and if you slip back onto the route, it <em>should</em> resume
	without intervention.

	<p>It needs to be said, however, that using Internet based GPS tools
	can be a pretty crappy experience with prolonged inability to access
	the Internet.  If you setup your route with a QR code and then just drive
	out into the wilderness with no cell towers in range and no satellite
	access, you'll wish you had paper maps.

	<p>If your GPS becomes useless without Internet access, and you don't have
	paper maps, you may find it useful to drive back to where you remember
	having Internet access, or if you're completely lost, simply pick a direction
	and drive until you get Internet connectivity back.

	<p>If you have a great big body of water in front of you, <b>stop!</b>  Call Deidre.
    </details>

    Continue with your route as if you were not using the QR code to program
    your GPS.  With your new route sheet:
        <ul>
	    <li>You read notes about each stop, along with color coded things to be aware of.</li>
	    <li>You write notes on it just as before.</li>
	    <li>You turn it in to %%YOURCOORDINATOR%%, just as before.</li>
	</ul>
</details>

<details><summary>Tracking mileage, time, stop status and notes</summary>
    If you've gotten to the point where you are using QR codes to setup your
    navigation, it is simple to use %%PRODUCT%% to keep track of mileage, your time,
    and what happened at each stop.  You've already done the hard parts.

    <p>Towards the top on the right side of the route sheet, you should see your
    name next to "Driver name:".  If this is not you, replace your route sheet with
    %%YOURCOORDINATOR%%.  Failure to do so will cause your route to be logged under
    the wrong driver.  You don't want that, do you?

    <p>When you have the correct route sheet, point your %%MID%%'s camera at the QR code at the
    top left of your route sheet, and touch the hyperlink that appears, thereby following
    that link to the %%PRODUCT%% application, pre-configured for you, driving this route.

    <p>Follow the link to proceed to:

    <details><summary>The software wants to access your GPS</summary>
	<p>When you follow the QR code (or the "Take route live" link sent to you
	via e-mail), your %%MID%% will bring up a page similar to:
	<br><img width=50% src="images/01_access_your_location.jpg"><br>
	You do <em>not</em> have to allow this (though generally most people do).

	<p>If you allow this, the application server will be able to track your position*
	throughout your route.  If you do not allow this, the server will not
	know.  Note that this question is <em>not</em> for your %%MID%%'s
	GPS mapper software (which always knows because it has to), but only for the server's tracking.
	That information is currently unused other than for the coordinator to know how far
	along drivers are in their routes.

	<p><em>*Note:</em>  Most browsers cannot track your position if their software isn't
	currently active on the screen.  If, for instance, you are taking a call and your
	call screen is up, %%PRODUCT%% is not tracking your position even if you allowed it to.
	As soon as you hang up, tracking will resume.

	<p>Click on "Allow" or "Don't Allow" to proceed to the next step.
    </details>

    <details><summary>Stop List</summary>
        Regardless of whether or not you allow %%PRODUCT%% to track your position, when
	you select your answer, your screen will change to something like:
	<br><img width=50% src="images/02_stop_list.jpg"><br>
	The left hand column is the stop name, typically the person being delivered to.
	The middle column is their phone number to call in the event of a problem delivering.
	The right column is the address to deliver to.
	<p>If you touch a stop name, it will bring up a page that talks all about that stop.
	<p>If you touch a phone number, it will bring you to the page for that stop, and
	ask you if you want to call that number.
	<p>If you touch an address, it will bring you to the page for that stop, and also
	tell your mapper to go to that address (and all subsequent addresses).
	<p>You can get back to this list from the menu displaying information about a particular
	stop by hitting <button>&larr;</button>.
	<p>Select the first stop in the list, where you will pick-up for the deliveries, to
	proceed to the next step.
    </details>


    <details><summary>Unvisited Distributor</summary>
	When you first view a distributor, the screen will appear something like:
	    <br><img width=50% src="images/03_unvisited_distributor.jpg"><br>
	For your first stop (the distribution center), you'll need to select your route type,
	set the odometer, and set the status of the stop (probably "Normal").  You may also choose to
	program your GPS from this page.  The following buttons are available:
	<table><tr><th>Button</th><th>Explanation</th></tr>
	    <tr><th valign=top><button><img style='height:50px' src="common/route_type.jpg"></button></th><td>
	        Takes you to a new menu where you indicate what type of
		vehicle you will be driving.  This information is used for calculating expenses
		associated with the route.  This icon appears only on the first stop and you must
		fill it in before submitting the completed route.  If you forget, it will prompt
		you.
		<details><summary>Example select route type screen</summary>
		    <br><img width=50% src="images/04_select_route_type.jpg"><br>
		</details></td></tr>
	    <tr><th valign=top><button><img style='height:50px' src="common/phone.jpg"></button></th><td>
		Call the number you see to the right, in this case, the
		general number associated with the distribution center.
		<details><summary>Example phone screen</summary>
		    <br><img width=50% src="images/05_make_a_call.jpg"><br>
		</details></td></tr>
	    <tr><th valign=top><button><img style='height:50px' src="common/texting.jpg"></button></th><td>
		Bring up a text window to the number specified to the right.
		(This is probably not useful for the distribution center, but will also
		appear on screens for subsequent stops and you may have people on your route
		that prefer texts).
		<details><summary>Example text sending screen</summary>
		    <br><img width=50% src="images/06_send_a_text.jpg"><br>
		</details></td></tr>
	    <tr><th valign=top><button><img style='height:50px' src="common/map.jpg"></button></th><td>
	        Program your %%MID%%'s mapper
		for the entire route, starting at this stop (which is to say, the distribution
		center).  Since you are probably already at the distribution center when you
		invoke this page, you probably should hold off programming your GPS until you
		move on to the next stop.

		<p>If there are more stops after the one you indicate,
		%%PRODUCT%% will ask you if you want to program the
		remaining stops as well (vs. just the stop you indicated):
		<details><summary>Programming remaining stops as well</summary>
		    <br><img width=50% src="images/more_stops.jpg"><br>
		</details>
		and then you will be transferred to your mapper.
		<details><summary>Program GPS</summary>
		    <br><img width=50% src="images/07_program_GPS.jpg"><br>
		</details></td></tr>
	    <tr><th valign=top><button><img style='height:50px' src="common/odometer.jpg"></button></th><td>
	        Bring up the odometer page.  This option will only be available on the first and last
		stop, and you'll need to specify the odometer's value in both cases before submitting
		your route.
		<details><summary>Example odometer page</summary>
		    <br><img width=50% src="images/08_note_odometer.jpg"><br>
		</details></td></tr>
	    <tr><th valign=top><button><img style='height:50px' src="common/status.jpg"></button></th><td>
	        Bring up the stop status menu.  For the first stop, the distribution center, this
		will probably be "Normal".
		<details><summary>Example status page</summary>
		    <br><img width=50% src="images/09_set_stop_status.jpg"><br>
		</details></td></tr>
	</table>
	Set the route type, odometer and status of the first stop to proceed to the next step.
    </details>

    <details><summary>Distributor Complete</summary>
	At this point, you have completed picking food up and setting the
	application to proceed on your route.  Your screen should look something like:
	<br><img width=50% src="images/10_stop_complete.jpg"><br>
	Hit the <button>&darr;</button> on the lower right of the screen to proceed to the first
	non-distributor stop.
    </details>

    <details><summary>Visit Next Stop</summary>
        You got here either by selecting this stop from the top level menu or selecting the
	<button>&darr;</button> from the prevoius stop.  In the vast majority of
	cases, you'll select "Visit the stop" on this menu, though potentially, if you find out
	the status of the patron has changed between when the route sheet was generated and now,
	you might select something different.
	<br><img width=50% src="images/11_visit_next_stop.jpg"><br>
	You'll get this page for all but the first and last stop.
	<p>When you make a selection, you'll proceed to the next step, viewing the page
	for the first non-distribution center stop.
    </details>

    <details><summary>Unvisited First Real Stop</summary>
        The page should look like:
	<br><img width=50% src="images/12_unvisited_first_stop.jpg"><br>

	In place of some of the buttons you saw in the distribution screen, you'll see the
	following additional buttons:
	<table><tr><th width=10%>Button</th><th>Explanation</th></tr>
	    <tr><th valign=top><button><img style='height:50px' src="common/note.jpg"></button></th><td>
	        Bring up a page allowing you to specify things that others may want to know
		about this stop.  It is rare that you ever add anything to the notes for the
		distribution center.
		<details><summary>Example note page</summary>
		    <br><img width=50% src="images/08_take_a_note.jpg"><br>
		</details></td></tr>
	    <tr><th valign=top><button>Include parking location</button></th><td>
	        <details><summary>Include parking location</summary>
		    When you hit this button, it adds text to the not similar to:
		    <br><img width=50% src="images/13_set_parking_location.jpg"><br>
		</details></td></tr>
	    <tr><th valign=top><button><img style='height:50px' src="common/donation.jpg"></button></th><td>
		Specify any cash or check donation the patron has made.  This will not appear for
		the first or last stop, but will appear for all the patrons in between.
		<details><summary>Example donation page</summary>
		    <br><img width=50% src="images/14_set_donation.jpg"><br>
		</details></td></tr>
	    <tr><th valign=top><button><img style='height:50px' src="common/pickups.jpg"></button></th><td>
		Van driver picking up food at food collection/creation point
		uses this to check bags received against expected.  This
		will not appear at any stop other than a collection/creation
		point.
		<details><summary>Example pickups page</summary>
		    <br><img width=50% src="images/pickups.jpg"><br>
		</details></td></tr>
	</table>
    </details>

    <details><summary>Completed First non-distributor stop</summary>
	<br><img width=50% src="images/15_completed_first_stop.jpg"><br>
	If you hit the <button>&larr;</button>, you can view what your
	progress looks like in the ordered list of stops.
    </details>

    <details><summary>Route in Progress</summary>
	<br><img width=50% src="images/16_route_in_progress.jpg"><br>
	Hit the stop you wish to view next.
    </details>

    You might run across a patron with special needs or things that you
    need to be aware of.  Often these are flagged with different colors
    to stand out.
    <details><summary>Stop With Flags</summary>
	<br><img width=50% src="images/17_stop_with_flags.jpg"><br>
    </details>

    When you complete the last patron, return to the distribution center
    and fill out that page (with the odometer setting), you can hit
    the done button:
    <details><summary>Done Button</summary>
	<br><img width=50% src="images/18_done_button.jpg"><br>
    </details>

    <details><summary>Recording Complete</summary>
	<br><img width=50% src="images/19_recording_complete.jpg"><br>
    </details>

<b>Important:</b>  Just because you only used your route sheet to follow the first
QR code to get to the software, this does not mean the route sheet magically disappears.
It contains information about our patrons that we are required to keep private so you
must either return it to %%YOURCOORDINATOR%% or destroy it.

</details>
