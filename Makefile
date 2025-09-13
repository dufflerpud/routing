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

%:
		@echo "Invoking std_$@ rule:"
		@$(MAKE) std_$@ ORIGINAL_TARGET=$@
