.PHONY: all clean

SOURCES := $(shell find . -name "*.sv")
TARGETS := $(SOURCES:ProcessingPipeline.sv=post_synth_utilization.rpt)

all: $(TARGETS)

$(TARGETS): $(SOURCES)
	vivado -mode batch -source synth.tcl -tclargs $(dir $@)

clean:
	rm -rf tests/
