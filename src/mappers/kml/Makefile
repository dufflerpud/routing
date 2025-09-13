ICONS=/var/www/routing/sto/icons
KML_ICONS=$(ICONS)/kml
WHITE_SRC=http://maps.google.com/mapfiles/kml/paddle/wht-circle.png
COLORS=$(shell awk '/^[0-9]/ {print $$2}' ../../colors)
TARGETS=$(addsuffix .png,$(addprefix $(KML_ICONS)/paddle-,$(COLORS)))
BASE=/var/log/routing/progress/MOW_Sagadahoc
FILES=									\
	$(BASE)/2025-04-30-Woolwich-Chris_Caldwell-1uA6to.po		\
	$(BASE)/2025-04-02-Brunswick_Towers-Chris_Caldwell-XXXXXX.po		

route_run:
	/var/www/routing/sto/index-test.cgi pomap $(FILES) /tmp/rr.kml

route:
	/var/www/routing/sto/index-test.cgi pomap Woolwich Brunswick /tmp/route.kml

paddles:
	mkdir -p $(KML_ICONS)
	@make $(TARGETS)

$(KML_ICONS)/paddle-%.png:
	convert $(WHITE_SRC) -fuzz 10% -fill $(subst $(KML_ICONS)/paddle-,,$(subst .png,,$@)) -opaque white $@
