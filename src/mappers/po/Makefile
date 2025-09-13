BASE=/var/log/routing/progress/MOW_Sagadahoc
FILES=									\
	$(BASE)/2025-04-30-Woolwich-Chris_Caldwell-1uA6to.po		\
	$(BASE)/2025-04-02-Brunswick_Towers-Chris_Caldwell-XXXXXX.po		

route_run:
	/var/www/routing/sto/index-test.cgi pomap $(FILES) /tmp/rr.po

route:
	/var/www/routing/sto/index-test.cgi pomap Woolwich Brunswick /tmp/route.po
