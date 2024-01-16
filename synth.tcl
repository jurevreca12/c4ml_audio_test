# synth.tcl is a synthesis script for Vivado
# 
# run "vivado -mode batch -source synth.tcl -tclargs $dir" to get a compiled vivado design
#
proc synth_circuit {source_dir} {
	set output_dir $source_dir/synth/
	set script_path [ file dirname [ file normalize [ info script ] ] ]
	read_xdc     $script_path/constr.xdc
	
	read_verilog [ glob $source_dir/*.sv ] 

	# Run out-of-context synthesis
	set_part xc7z010clg225-1
	synth_design -top ProcessingPipeline
	opt_design
	write_checkpoint -force $output_dir/post_synth
	report_timing_summary 		 -file $output_dir/post_synth_timing_summary.rpt
	report_power			 -file $output_dir/post_synth_power.rpt
	report_clock_interaction	 -file $output_dir/post_synth_clock_interaction.rpt \
					 -delay_type min_max
	report_high_fanout_nets		 -file $output_dir/post_synth_high_fanout_nets.rpt  \
					 -fanout_greater_than 200 \
					 -max_nets 50
	report_utilization -hierarchical -file $output_dir/post_synth_utilization.rpt
	
	# write_verilog -force $output_dir/impl_netlist.v
}

if { $argc != 1 } {
	puts "Please provide the source directory as:"
	puts "vivado -mode batch -source synth.tcl -tclargs \$dir"
} else {
	set source_dir [lindex $argv 0]
	puts "Synthesizing circuit in $source_dir"
	synth_circuit $source_dir
}


