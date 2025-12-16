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
PROGRAMS=last_month addr_to_latlong check_history completed_route_update defluff distuser_to_pdf embed_images htmls_to_times merge_routes read_mapquest read_trips read_vcf split_trips vcf_mail xlate_vcf

PROJECTSDIR?=$(shell echo $(CURDIR) | sed -e 's+/projects/.*+/projects+')
include $(PROJECTSDIR)/common/Makefile.std

MERGE_DIR=/usr/local/projects/$(PROJECT).dirty
SAMPLE_DISTRIBUTOR=DC_Distributor
LOGDIR=/var/log/$(PROJECT)
LOGDIRS=$(LOGDIR)/patrons $(LOGDIR)/trips $(LOGDIR)/html $(LOGDIR)/progress

launder:
		rm -rf cache
		mkdir -p cache
		chmod 777 cache

merge:
		make install
		#make launder
		(cd $(MERGE_DIR)/Distributors; find . -print | grep -v $(SAMPLE_DISTRIBUTOR) | cpio -o) | (cd Distributors; cpio -idumv)
		cp $(MERGE_DIR)/monthly_reports .

# ROUTING_WWW_DIR="/var/www/html"
ROUTING_DB="$(PROJECTDIR)/db"
ROUTING_ADMINISTRATOR="administrator"
ROUTING_ADMINISTRATOR_PASSWORD="OOPSCHANGEME!"

install:
	install -d -m 777 -o root -g root		$(LOGDIR)/. 
	install -d -m 755 -o $(WUSER) -g $(WGROUP)	$(LOGDIR)/assessments 
	install -d -m 755 -o $(WUSER) -g $(WGROUP)	$(LOGDIR)/html 
	rm -f $(LOGDIR)/httpd
	ln -s	 ../httpd/routing			$(LOGDIR)/httpd
	install -d -m 777 -o $(WUSER) -g $(WGROUP)	$(LOGDIR)/import 
	install -d -m 777 -o root -g root		$(LOGDIR)/patrons 
	install -d -m 777 -o $(WUSER) -g $(WGROUP)	$(LOGDIR)/progress 
	rm -f $(LOGDIR)/stderr
	ln -s	 /var/log/stderr/routing		$(LOGDIR)/stderr
	install -d -m 777 -o $(WUSER) -g $(WGROUP)	$(LOGDIR)/trips 
	: install -d -m 755 -o root -g root		$(ROUTING_WWW_DIR)/. 
	: ln -s	 sto/default.css			$(ROUTING_WWW_DIR)/default.css
	: ln -s	 /non_sys$(ROUTING_WWW_DIR)		$(ROUTING_WWW_DIR)/routing
	install -d -m 755 -o $(WUSER) -g $(WGROUP)	$(WWWDIR) 
	rm -f $(WWWDIR)/common
	ln -s	 routing_common				$(WWWDIR)/common
	: ln -s	 $(CPI_USER_DIR)			$(WWWDIR)/common.projects
	install -d -m 755 -o root -g root		$(WWWDIR)/forms 
	rm -f $(WWWDIR)/help
	install -d -m 777 -o $(WUSER) -g $(WGROUP)	$(PROJECTDIR)/cache
	ln -s	 $(PROJECTDIR)/help			$(WWWDIR)/help
	install -d -m 755 -o root -g root		$(WWWDIR)/icons 
	install -d -m 755 -o root -g root		$(WWWDIR)/icons/kml 
	rm -f $(WWWDIR)/progress
	ln -s	 $(LOGDIR)/progress			$(WWWDIR)/progress
	install -d -m 755 -o root -g root		$(WWWDIR)/ref 
	install -d -m 777 -o root -g root		$(WWWDIR)/routes 
	rm -f $(WWWDIR)/routes/common
	ln -s	 ../routing_common			$(WWWDIR)/routes/common
	install -d -m 755 -o root -g root		$(WWWDIR)/routing 
	rm -f $(WWWDIR)/routing/routing
	ln -s	 .					$(WWWDIR)/routing/routing
	install -d -m 755 -o $(WUSER) -g $(WGROUP)	$(WWWDIR)/routing_common 
	install -d -m 755 mail mail			$(WWWDIR)/vcf 
	install -d -m 777 -o root -g root		$(ROUTING_DB)
	$(MAKE) std_$@ ORIGINAL_TARGET=$@

%:
		@echo "Invoking std_$@ rule:"
		@$(MAKE) std_$@ ORIGINAL_TARGET=$@
