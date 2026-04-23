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
		$(MAKE) install
		#$(MAKE) launder
		(cd $(MERGE_DIR)/Distributors; find . -print | grep -v $(SAMPLE_DISTRIBUTOR) | cpio -o) | (cd Distributors; cpio -idumv)
		cp $(MERGE_DIR)/monthly_reports .

# ROUTING_WWW_DIR="/var/www/html"
ROUTING_DB="$(PROJECTDIR)/db"
ROUTING_ADMINISTRATOR="administrator"
ROUTING_ADMINISTRATOR_PASSWORD="OOPSCHANGEME!"

fratboy:
	@echo "SYSTEMWWW=$(SYSTEMWWW) WWWDIR=$(WWWDIR)"

install:
	$(GNUINSTALL) -d -m 777 -o $(SYSTEMUSER) -g $(SYSTEMGROUP)		$(LOGDIR)/. 
	$(GNUINSTALL) -d -m 755 -o $(WUSER) -g $(WGROUP)	$(LOGDIR)/assessments 
	$(GNUINSTALL) -d -m 755 -o $(WUSER) -g $(WGROUP)	$(LOGDIR)/html 
	$(RM) -f $(LOGDIR)/httpd
	$(LN) -s	 ../httpd/routing			$(LOGDIR)/httpd
	$(GNUINSTALL) -d -m 777 -o $(WUSER) -g $(WGROUP)	$(LOGDIR)/import 
	$(GNUINSTALL) -d -m 777 -o $(SYSTEMUSER) -g $(SYSTEMGROUP)		$(LOGDIR)/patrons 
	$(GNUINSTALL) -d -m 777 -o $(WUSER) -g $(WGROUP)	$(LOGDIR)/progress 
	$(RM) -f $(LOGDIR)/stderr
	$(LN) -s	 /var/log/stderr/routing		$(LOGDIR)/stderr
	$(GNUINSTALL) -d -m 777 -o $(WUSER) -g $(WGROUP)	$(LOGDIR)/trips 
	: $(GNUINSTALL) -d -m 755 -o $(SYSTEMUSER) -g $(SYSTEMGROUP)		$(ROUTING_WWW_DIR)/. 
	: $(LN) -s	 sto/default.css			$(ROUTING_WWW_DIR)/default.css
	: $(LN) -s	 /non_sys$(ROUTING_WWW_DIR)		$(ROUTING_WWW_DIR)/routing
	$(GNUINSTALL) -d -m 755 -o $(WUSER) -g $(WGROUP)	$(WWWDIR) 
	$(RM) -f $(WWWDIR)/common
	$(LN) -s	 routing_common				$(WWWDIR)/common
	: $(LN) -s	 $(CPI_USER_DIR)			$(WWWDIR)/common.projects
	$(GNUINSTALL) -d -m 755 -o $(SYSTEMUSER) -g $(SYSTEMGROUP)		$(WWWDIR)/forms 
	$(RM) -f $(WWWDIR)/help
	$(GNUINSTALL) -d -m 777 -o $(WUSER) -g $(WGROUP)	$(PROJECTDIR)/cache
	$(GNUINSTALL) -d -m 755 -o $(WUSER) -g $(WGROUP)	$(PROJECTDIR)/src/porting
	$(LN) -s	 $(PROJECTDIR)/help			$(WWWDIR)/help
	$(GNUINSTALL) -d -m 755 -o $(SYSTEMUSER) -g $(SYSTEMGROUP)		$(WWWDIR)/icons 
	$(GNUINSTALL) -d -m 755 -o $(SYSTEMUSER) -g $(SYSTEMGROUP)		$(WWWDIR)/icons/kml 
	$(RM) -f $(WWWDIR)/progress
	$(LN) -s	 $(LOGDIR)/progress			$(WWWDIR)/progress
	$(GNUINSTALL) -d -m 755 -o $(SYSTEMUSER) -g $(SYSTEMGROUP)		$(WWWDIR)/ref 
	$(GNUINSTALL) -d -m 777 -o $(SYSTEMUSER) -g $(SYSTEMGROUP)		$(WWWDIR)/routes 
	$(GNUINSTALL) -d -m 755 -o $(SYSTEMUSER) -g $(SYSTEMGROUP)		$(WWWDIR)/routing_common
	$(RM) -f $(WWWDIR)/routes/common
	$(LN) -s	 ../routing_common			$(WWWDIR)/routes/common
	$(GNUINSTALL) -o $(WUSER) -g $(WGROUP) -m 0644 lib/*.css lib/*.jpg $(WWWDIR)/routes/common
	: $(GNUINSTALL) -d -m 755 -o $(SYSTEMUSER) -g $(SYSTEMGROUP)		$(WWWDIR)/routing 
	$(GNUINSTALL) -d -m 755 -o $(WUSER) -g $(WGROUP)	$(WWWDIR)/routing_common 
	$(GNUINSTALL) -d -m 755 mail mail			$(WWWDIR)/vcf 
	$(GNUINSTALL) -d -m 777 -o $(SYSTEMUSER) -g $(SYSTEMGROUP)		$(ROUTING_DB)
	$(MAKE) ORIGINAL_TARGET=$@ std_$@

%:
		@echo "Invoking std_$@ rule:"
		@$(MAKE) ORIGINAL_TARGET=$@ std_$@
