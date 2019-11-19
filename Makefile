# The order of packages is significant as there are dependencies between
# the packages. Typically generated namespaces are used by other packages.
PACKAGES = resource-manager l3vpn-ntw ietf-l3vpn-svc

# Directory of example packages
PACKAGE_STORE=$(NCS_DIR)/packages/neds

# The create-network argument to ncs-netsim
NETWORK = \
	create-network $(PACKAGE_STORE)/cisco-ios-cli-3.0     9 ce \
	create-network $(PACKAGE_STORE)/cisco-iosxr-cli-3.0   4 pe \
	create-network $(PACKAGE_STORE)/cisco-iosxr-cli-3.0   4 p

DEMO_DIR = $(shell basename $(CURDIR))

all: packages netsim ncs
.PHONY: all

packages:
	for i in $(PACKAGES); do \
	    $(MAKE) -C packages/$${i}/src all || exit 1; \
	done
.PHONY: packages

netsim:
	ncs-netsim --dir netsim $(NETWORK)
	cp initial_data/ios.xml netsim/ce/ce0/cdb
	cp initial_data/ios.xml netsim/ce/ce1/cdb
	cp initial_data/ios.xml netsim/ce/ce2/cdb
	cp initial_data/ios.xml netsim/ce/ce3/cdb
	cp initial_data/ios.xml netsim/ce/ce4/cdb
	cp initial_data/ios.xml netsim/ce/ce5/cdb
	cp initial_data/ios.xml netsim/ce/ce6/cdb
	cp initial_data/ios.xml netsim/ce/ce7/cdb
	cp initial_data/ios.xml netsim/ce/ce8/cdb
	cp initial_data/iosxr.xml netsim/pe/pe0/cdb
	cp initial_data/iosxr.xml netsim/pe/pe1/cdb
	cp initial_data/iosxr.xml netsim/pe/pe2/cdb
	cp initial_data/iosxr.xml netsim/pe/pe3/cdb
	cp initial_data/iosxr.xml netsim/p/p0/cdb
	cp initial_data/iosxr.xml netsim/p/p1/cdb
	cp initial_data/iosxr.xml netsim/p/p2/cdb
	cp initial_data/iosxr.xml netsim/p/p3/cdb

ncs:
	ncs-setup --netsim-dir netsim --dest .
	ncs-netsim ncs-xml-init > ncs-cdb/netsim_devices_init.xml
	cp initial_data/device-groups.xml ncs-cdb
	cp initial_data/qos.xml ncs-cdb
	cp initial_data/resource-pools.xml ncs-cdb
	cp initial_data/topology.xml ncs-cdb
.PHONY: ncs

clean:
	for i in $(PACKAGES); do \
		$(MAKE) -C packages/$${i}/src clean || exit 1; \
	done
	rm -f README.ncs README.netsim
	rm -rf netsim running.DB logs state ncs-cdb *.trace
	rm -f packages/cisco-ios-cli-3.0
	rm -f packages/cisco-iosxr-cli-3.0
	rm -rf bin
.PHONY: clean

start:
	ncs-netsim start
	ncs --ignore-initial-validation
.PHONY: start

stop:
	-ncs-netsim stop
	-ncs --stop
.PHONY: stop

reset:
	ncs-setup --reset
.PHONY: reset

cli:
	ncs_cli -u admin
.PHONY: cli

dist: stop clean
	cd .. ; \
	tar -cf $(DEMO_DIR).tar \
		--exclude='.git' \
		--exclude='*.swp' \
		--exclude='.DS_Store' \
		--exclude='lux_logs' \
		--exclude='$(DEMO_DIR)\/ncs-cdb\/*' \
		--exclude='$(DEMO_DIR)\/state\/*' \
		--exclude='$(DEMO_DIR)\/logs\/*' \
		--exclude='$(DEMO_DIR)\/netsim' \
		--exclude='$(DEMO_DIR)\/doc' \
		$(DEMO_DIR) && gzip -9 $(DEMO_DIR).tar
.PHONY: dist
