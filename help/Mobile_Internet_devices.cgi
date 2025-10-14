#!/usr/local/projects/routing/help/html_filter.pl
<h2 align=center>Setting up your %%MID%% for %%PRODUCT%%</h2>
This document describes a driver's configuration of his or her %%MID%%.
<details href="Driver.cgi">
    <summary>More information on the life of a driver</summary>
        Details from a different help file here
</details>
The %%PRODUCT%% software supports drivers using Apple IOS iPhone/iPads
and Android Smart phones or tablets, running either Safari, Google Chrome
or Firefox.

<p>With newer vehicles, it can take advantage of the car's bigger
display using "CarPlay" with IOS or "Android Auto" on Androids.
Older implementations of either protocol require a cable, but newer
implementations may be able to talk to your car using Bluetooth.

<p>Not all configurations of %%MID%% OS, browser and vehicle have been
tested and considering the buggy implementations of many car screen
interfaces, it is safe to say some simply will not work.  However, never
fear:  As nice as a bigger map is, the software is quite usable with the
screen and mapping that reasonably modern iOS and Android devices provide.

<p>The reference platform (where it is most tested) is with Safari and
Apple maps on an iPhone 14, running IOS 18 talking "CarPlay" through a
standard USB-A/lightning cable to a 2021 Rav-4 Prime.  This configuration
is solid and has worked with no issues other than those caused by the USB
cable not being totally seated.

<p>Running %%PRODUCT%% software on your %%MID%% in your car requires
jumping the following major hurdles:
<br>(click on arrows beside sections for more information)
<details><summary>Ability to access the Internet</summary>
    The most common driver access to the Internet will be by using a smart
    phone accessing the Internet over cellular data.  Other variations
    are possible and have been tested; in particular, using a tablet
    connected to a hot-spot.

    <p>If you can access web pages from your %%MID%% while on the road,
    you presumably have already jumped this hurdle.

    <p><em>Note:</em> If you are using cellular data, your cell provider's
    coverage will vary depending on where you are currently driving,
    your access may drop in and out and you may incur roaming charges.
    We have used %%PRODUCT%% successfully with intermittent coverage
    (though you'll definitely need connectivity at the beginning and end
    of the route) but many things will just work better with more access.
    You may want to enable cellular roaming data.
</details>

<details><summary>Ability to know where you are</summary>
    You do <em>not</em> need %%PRODUCT%%'s ability to program your
    %%MID%%'s mapping software to take notes about stops or keep mileage
    (which is really all the record keeping system requires).

    <p>However, why wouldn't you want to get directions and keep track
    of your position if you could?  Why would you type in an address or
    use a QR code if the system could already have our course laid in?

    <p>To proceed, pick your browser:

    <details><summary>Safari on iOS (iPhone/iPad/iPod running Safari)</summary>
	Apple's support article:
	    <a target=Mobile_help
		href="https://support.apple.com/en-us/102647">
		Turn Location Services and GPS on or off on your iPhone, iPad, or iPod touch.
	    </a><br>
	Buddypunch's article:
	    <a target=Mobile_help
		href="https://docs.buddypunch.com/en/articles/919258-how-to-enable-location-services-for-chrome-safari-edge-and-android-ios-devices-gps-setting#enabling-ios-location-services">
		    Enabling iOS Location Services</a>
        <details><summary>Troubleshooting</summary>
	    <ul>
		<li>In USB configurations, check the seating of the cable
		    to verify it is seated well, both at the car end and
		    at the smartphone end.</li>
	    </ul>
	</details>
    </details>

    <details><summary>Google Chrome on Android</summary>
	Google's support article:
	    <a target=Mobile_help
		href="https://support.google.com/accounts/answer/3467281">
		    Manage your Android device's location settings</a><br>
        Buddypunch's article
	    <a target=Mobile_help
		href="https://docs.buddypunch.com/en/articles/919258-how-to-enable-location-services-for-chrome-safari-edge-and-android-ios-devices-gps-setting#enabling-android-location-services">
		    Enabling Android Location Services</a><br>
	<details><summary>Troubleshooting</summary>
	    <ul>
	        <li>Note that out of the box, some Androids come with
		Chrome configured for "desktop" - which means that they
		will not invoke the Android application "Google Maps".
		This is configured by going to Chrome's
		"settings/Site-settings" and turning "Desktop site" to
		"off".</li>

		<li>In some configurations of Android and Android Auto running
		on some cars, Android auto botches the initial configuration
		of waypoints (basically, the mapping software will take you
		directly to the last point you are routing which typically
		is where you started, ignoring all the planned stops!).
		The work-around is to setup the route and <em>then</em>
		connect the cable to the car and/or start Android Auto.
		Alternately, only program one stop ahead (thereby not using
		waypoints).</li>

		<li>We've had many problems with Android Auto and
		Google maps:
		    <details href="Android_problems.cgi"><summary>Problems with Android Auto</summary
		        This documentation contains a running list of the problems
			we're having with Android Auto
		</details></li>
	    </ul>
	</details>
    </details>

    <details><summary>Safari on Mac</summary>
	Buddypunch's article
	    <a target=Mobile_help
		href="https://docs.buddypunch.com/en/articles/919258-how-to-enable-location-services-for-chrome-safari-edge-and-android-ios-devices-gps-setting#enabling-safari-location-services-mac">
		    Enabling Safari Location Services</a>.
    </details>

    <details><summary>Google Chrome on non-Android</summary>
    	Buddypunch's article
	    <a target=Mobile_help
		href="https://docs.buddypunch.com/en/articles/919258-how-to-enable-location-services-for-chrome-safari-edge-and-android-ios-devices-gps-setting#enabling-chrome-location-services">
		    Enabling Google Chrome Location Services</a>.<br>
	From <a target=Mobile_help href="https://www.napo.net/page/locationpermission">
	    NAPO's locationpermission</a>:
	<ol>
	    <li>Select Google Chrome's Main Menu button, marked by three vertically aligned dots. It's
		located in the upper right corner of the browser.</li>
	    <li>Select Settings > Advanced > Privacy and security > Site Settings > Location.</li>
	    <li>Move the Ask before accessing (recommended) slider to toggle it on or off. Turn
		it on if you want websites to request your permission before accessing your location.</li>
	    <li>Below that, you can see the Block section and the Allow section. Here, you can see
		which websites you've given geolocation permissions to and revoke them, if needed.</li>
	</ol>
    </details>

    <details><summary>Microsoft Edge on Windows</summary>
	Buddypunch's article
	    <a target=Mobile_help
		href="https://docs.buddypunch.com/en/articles/919258-how-to-enable-location-services-for-chrome-safari-edge-and-android-ios-devices-gps-setting#enabling-microsoft-edge-location-services">
		    Enabling Microsoft Edge Location Services</a>.<br>
	From <a target=Mobile_help href="https://www.napo.net/page/locationpermission">
	    NAPO's locationpermission</a>:
	<ol>
	    <li>Select the Settings and more button (depicted as three horizontal dots) in the
		 upper right corner of the screen.</li>
	    <li>Select Settings > View Advanced Settings.</li>
	    <li>Press the Manage button under Website Permissions. Here you can see and change
		a website's permissions, including location and whether or not it can access
		your microphone.</li>
	</ol>
    </details>

    <details><summary>Internet Explorer on Windows</summary>
	From <a target=Mobile_help
	    href="https://www.napo.net/page/locationpermission">
	        NAPO's locationpermission</a>:
	<ol>
	    <li>Select the Gear icon in the upper right-hand corner of the browser window.</li>
	    <li>When the drop-down menu appears, select Internet Options.</li>
	    <li>Select the Privacy tab.</li>
	    <li>Find the Location section under Privacy Options and click the checkbox next to
		Never allow websites to request your physical location. When activated, this
		option instructs the browser to deny all requests to access your physical location
		data.</li>
	    <li>The Clear Sites button is also found within the Location section. Anytime a
		website attempts to access your location data, IE11 prompts you to take action.
		In addition to allowing or denying that individual request, you have the option
		to blacklist or whitelist the respective website. These preferences are then
		stored by the browser and used on subsequent visits to those sites. To delete
		all of those saved preferences and start anew, select the Clear Sites button.</li>
	</ol>
    </details>

    <details><summary>Mozilla Firefox</summary>
	From <a target=Mobile_help href="https://www.napo.net/page/locationpermission">
	    NAPO's locationpermission</a>:
	<ol>
	    <li>Press the Menu button and choose Options.</li>
	    <li>Type "location" in the search bar.</li>
	    <li>Find Permissions in the search results and select the Settings button to the
		right of Location.</li>
	    <li>This opens the Settings - Location Permissions dialog box. From here, you can
		see which websites have requested access to your location and choose to allow
		or block them.</li>
	</ol>
    </details>
</details>

<details><summary>Ability to display popups from Brightsands.com</summary>
    When the %%PRODUCT%% application invokes your %%MID%%'s mapping
    software, it is treated like a pop-up from the routing.brightsands.com web site.
    Therefore, to take advantage of this feature, you need to allow pop-ups from
    routing.brightsands.com.

    <p>Please note, however, that browsers disable pop-ups by default for good reason:
    it blocks a ton of annoying ads during regular browsing.  Certainly you could allow
    all websites to create pop-ups, but we strongly recommend only allowing pop-ups
    from routing.brightsands.com in browsers that allow site-by-site pop-ups.
    <details><summary>Safari on iOS</summary>
	From Apple support:
	    <a target=Mobile_help
		href="https://discussions.apple.com/thread/251037745?sortBy=rank">
		    How do I enable pop ups for one website only</a><br>
	From iPhoneLife:
	    <a target=Mobile_help
		href="https://www.iphonelife.com/content/how-to-block-or-allow-pop-ups-safari-your-iphone">
		Easily Block or Allow Pop-Ups in Safari on iPhone</a>
    </details>

    <details><summary>Google Chrome on Android</summary>
	From Google support:
	    <a target=Mobile_help
		href="https://support.google.com/chrome/answer/95472?hl=en&co=GENIE.Platform%3DAndroid">
		Block or allow pop-ups in Google Chrome</a>
    </details>

    <details><summary>Safari on Mac</summary>
	From <a target=Mobile_help
	    href="https://help.ziflow.com/hc/en-us/articles/30721795965844-Enabling-Pop-ups-in-Different-Web-Browsers">
	        Enabling Pop-ups in different Web Browsers</a>:
	<ol>
	    <li>Open Safari and click on "Safari" in the top menu bar.</li>
	    <li>From the drop-down menu, select "Preferences."</li>
	    <li>In the preferences window, click on the "Websites" tab.</li>
	    <li>In the left-hand menu, click on "Pop-up Windows."</li>
	    <li>Ensure that the checkbox for "Block and Notify" is unchecked, or add
		routing.brightsands.com as an exception in the list of websites below.</li>
	</ol>
    </details>

    <details><summary>Google Chrome on non-Android</summary>
	From <a target=Mobile_help
	    href="https://help.ziflow.com/hc/en-us/articles/30721795965844-Enabling-Pop-ups-in-Different-Web-Browsers">
	    Enabling Pop-ups in different Web Browsers</a>:
	<ol>
	    <li>Open Google Chrome and click on the three-dot menu icon located in the top right
		corner of the browser window.</li>
	    <li>From the drop-down menu, select "Settings."</li>
	    <li>Scroll down and click on "Privacy and security" in the left-hand menu.</li>
	    <li>Under the "Privacy and security" section, click on "Site settings."</li>
	    <li>Scroll down and click on "Pop-ups and redirects."</li>
	    <li>Toggle the switch to allow pop-ups, and make sure it is turned on (the switch will
		appear blue).</li>
	</ol>
    </details>

    <details><summary>Mozilla Firefox</summary>
	From <a target=Mobile_help
	    href="https://help.ziflow.com/hc/en-us/articles/30721795965844-Enabling-Pop-ups-in-Different-Web-Browsers">
	        Enabling Pop-ups in different Web Browsers</a>:
	<ol>
	    <li>Open Mozilla Firefox and click on the three-line menu icon located in the top right
		corner of the browser window.</li>
	    <li>From the drop-down menu, select "Preferences."</li>
	    <li>In the left-hand menu, click on "Privacy & Security."</li>
	    <li>Scroll down to the "Permissions" section and find "Block pop-up windows."</li>
	    <li>Uncheck the box next to "Block pop-up windows" to enable pop-ups.</li>
	</ol>
    </details>

    <details><summary>Microsoft Edge on Windows</summary>
	From <a target=Mobile_help
	    href="https://help.ziflow.com/hc/en-us/articles/30721795965844-Enabling-Pop-ups-in-Different-Web-Browsers">
	        Enabling Pop-ups in different Web Browsers</a>:
	<ol>
	    <li>Open Microsoft Edge and click on the three-dot menu icon located in the top
		right corner of the browser window.</li>
	    <li>From the drop-down menu, select "Settings."</li>
	    <li>Scroll down and click on "Cookies and site permissions" in the left-hand menu.</li>
	    <li>Under the "General" section, click on "Pop-ups and redirects."</li>
	    <li>Toggle the switch to allow pop-ups, and make sure it is turned on (the switch will
		appear blue).</li>
	</ol>
    </details>

</details>

<details><summary>Connecting your car display to your %%MID%%</summary>
    Unfortunately, your experience connecting your %%MID%% to your car screen will vary
    dramatically from car type to car type.  You may well end up going to your car manufacturer's
    support pages to get it working.  You certainly want to make sure you are running the latest
    version of OS software on your %%MID%% that you can before you even begin to diagnosing
    problems.

    <p>Or, as has frequently been our experience - it just works.  That is, you connect the
    cable, both the car and the phone display a message saying that the other device is accessible
    and ask if should it be allowed.  If you allow it, when you bring up the mapping application on
    the %%MID%%, and you bring up the mapping application on the car screen, it just
    syncs and works.

    <details><summary>Connecting your iOS device via CarPlay to your car screen</summary>
	Apple support:
	    <a target=Mobile_help
		href="https://support.apple.com/guide/iphone/connect-to-carplay-iph6860e6b53/ios">
		    Connect iPhone to CarPlay</a>
    </details>

    <details><summary>Connecting your Android device via Android Auto to your car screen</summary>
        Google support:
	    <a target=Mobile_help href="https://support.google.com/androidauto/answer/6348029">
	        Set up Android Auto</a>
    </details>
</details>
