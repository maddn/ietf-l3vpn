all:fxs
.PHONY: all

# Include standard NCS examples build definitions and rules
include $(NCS_DIR)/src/ncs/build/include.ncs.mk

YANG_ALL_FILES = $(wildcard yang/*.yang)
YANG_FILES     = $(and $(YANG_ALL_FILES),$(notdir $(shell grep -L "belongs-to" $(YANG_ALL_FILES))))
FXS = $(YANG_FILES:%.yang=../load-dir/%.fxs)

## Uncomment and patch the line below if you have a dependency to a NED
## or to other YANG files
# YANGPATH += ../../<ned-name>/src/ncsc-out/modules/yang \
# 	../../<pkt-name>/src/yang

YANGPATH +=	yang
NCSCPATH  = $(YANGPATH:%=--yangpath %)

fxs:	$(FXS)

../load-dir/%.fxs:	yang/%.yang
	$(NCSC)  `ls $*-ann.yang  > /dev/null 2>&1 && echo "-a $*-ann.yang"` \
             $(NCSCPATH) -c -o $@ $<

clean:
	rm -rf  ../load-dir/*
