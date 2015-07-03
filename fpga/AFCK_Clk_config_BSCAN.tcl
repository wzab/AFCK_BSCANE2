# Set the reference directory for source file relative paths (by default the value is script directory path)
set origin_dir "."

# Create project
create_project AFCK_i2c_controller ./AFCK_i2c_controller

# Set the directory path for the new project
set proj_dir [get_property directory [current_project]]

# Set project properties
set obj [get_projects AFCK_i2c_controller]
set_property "default_lib" "xil_defaultlib" $obj
set_property "part" "xc7k325tffg900-2" $obj
set_property "simulator_language" "Mixed" $obj
set_property "target_language" "VHDL" $obj

# Create 'sources_1' fileset (if not found)
if {[string equal [get_filesets -quiet sources_1] ""]} {
  create_fileset -srcset sources_1
}

# Set 'sources_1' fileset object
set obj [get_filesets sources_1]
set my_files [list \
 "src/i2c_master_bit_ctrl.vhd" \
 "src/i2c_master_byte_ctrl.vhd" \
 "src/i2c_master_top.vhd" \
 "src/i2c_bus_wrap.vhd" \
 "src/frq_counter.vhd" \
 "src/jtag_bus_ctl_3.vhd" \
 "src/i2c_bscan_ctrl.vhd" \
 "src/i2c_bscan_ctrl_top.vhd"\
]
set files [list ]

foreach my_file $my_files {
 lappend files "[file normalize "$origin_dir/$my_file"]"
}
add_files -norecurse -fileset $obj $files

# Set 'sources_1' fileset file properties for remote files
# None

# Set 'sources_1' fileset file properties for local files
foreach my_file $my_files {
 set file $my_file
 set file_obj [get_files -of_objects [get_filesets sources_1] [list "*$file"]]
 set_property "file_type" "VHDL" $file_obj
}

# Set 'sources_1' fileset properties
set obj [get_filesets sources_1]
set_property "top" "i2c_bscan_ctrl_top" $obj

#set my_ip_files [list \
# "ip/vio_0/vio_0.xci" \
# "ip/frqx/frqx.xci" \
#]
#foreach my_ip_file $my_ip_files {
#  # Set 'sources_1' fileset object
#  set obj [get_filesets sources_1]
#  set files [list \
#  "[file normalize "$origin_dir/$my_ip_file"]"\
#  ]
#  add_files -norecurse -fileset $obj $files
#
#  # Set 'sources_1' fileset file properties for remote files
#  # None
#
#  # Set 'sources_1' fileset file properties for local files
#  set file $my_ip_file
#  set file_obj [get_files -of_objects [get_filesets sources_1] [list "*$file"]]
#  if { ![get_property "is_locked" $file_obj] } {
#    set_property "synth_checkpoint_mode" "Singular" $file_obj
#  }
#}

# Create 'constrs_1' fileset (if not found)
if {[string equal [get_filesets -quiet constrs_1] ""]} {
  create_fileset -constrset constrs_1
}

# Set 'constrs_1' fileset object
set obj [get_filesets constrs_1]

# Add/Import constrs file and set constrs file properties
set file "[file normalize "$origin_dir/src/AFCK_i2c_constr.xdc"]"
set file_added [add_files -norecurse -fileset $obj $file]
set file "$origin_dir/src/AFCK_i2c_constr.xdc"
set file [file normalize $file]
set file_obj [get_files -of_objects [get_filesets constrs_1] [list "*$file"]]
set_property "file_type" "XDC" $file_obj

# Set 'constrs_1' fileset properties
set obj [get_filesets constrs_1]
set_property "target_constrs_file" "$origin_dir/src/AFCK_i2c_constr.xdc" $obj

# Create 'sim_1' fileset (if not found)
if {[string equal [get_filesets -quiet sim_1] ""]} {
  create_fileset -simset sim_1
}

# Set 'sim_1' fileset object
set obj [get_filesets sim_1]
# Empty (no sources present)

# Set 'sim_1' fileset properties
set obj [get_filesets sim_1]
set_property "top" "i2c_vio_ctrl_top" $obj

# Create 'synth_1' run (if not found)
if {[string equal [get_runs -quiet synth_1] ""]} {
  create_run -name synth_1 -part xc7k325tffg900-2 -flow {Vivado Synthesis 2014} -strategy "Vivado Synthesis Defaults" -constrset constrs_1
} else {
  set_property strategy "Vivado Synthesis Defaults" [get_runs synth_1]
  set_property flow "Vivado Synthesis 2014" [get_runs synth_1]
}
set obj [get_runs synth_1]
set_property "part" "xc7k325tffg900-2" $obj
set_property "steps.synth_design.args.flatten_hierarchy" "none" $obj

# set the current synth run
current_run -synthesis [get_runs synth_1]

# Create 'impl_1' run (if not found)
if {[string equal [get_runs -quiet impl_1] ""]} {
  create_run -name impl_1 -part xc7k325tffg900-2 -flow {Vivado Implementation 2014} -strategy "Vivado Implementation Defaults" -constrset constrs_1 -parent_run synth_1
} else {
  set_property strategy "Vivado Implementation Defaults" [get_runs impl_1]
  set_property flow "Vivado Implementation 2014" [get_runs impl_1]
}
set obj [get_runs impl_1]
set_property "part" "xc7k325tffg900-2" $obj

# set the current impl run
current_run -implementation [get_runs impl_1]

puts "INFO: Project created:AFCK_i2c_controller"
launch_runs synth_1
wait_on_run synth_1
launch_runs impl_1
wait_on_run impl_1
launch_runs impl_1 -to_step write_bitstream
wait_on_run impl_1

