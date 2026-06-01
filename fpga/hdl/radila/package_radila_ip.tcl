set script_dir [file normalize [file dirname [info script]]]
set hdl_dir [file normalize [file dirname $script_dir]]

if {![info exists radila_part]} {
    if {[info exists ::env(RADBUILD_VIVADO_PART)] && $::env(RADBUILD_VIVADO_PART) ne ""} {
        set radila_part $::env(RADBUILD_VIVADO_PART)
    } else {
        set radila_part xc7a35tcsg324-1
    }
}
if {![info exists radila_ip_repo_dir]} {
    if {[info exists ::env(RADBUILD_IP_REPO_DIR)] && $::env(RADBUILD_IP_REPO_DIR) ne ""} {
        set radila_ip_repo_dir $::env(RADBUILD_IP_REPO_DIR)
    } else {
        set radila_ip_repo_dir [file join $hdl_dir iprepo]
    }
}

set project_dir [file join $script_dir .vivado_ip_packager]
set ip_root_dir [file join $radila_ip_repo_dir radila_1.0]

proc find_bus_interface_ci {core wanted_name} {
    foreach bus_if [ipx::get_bus_interfaces -of_objects $core] {
        if {[string equal -nocase [get_property name $bus_if] $wanted_name]} {
            return $bus_if
        }
    }
    return ""
}

file mkdir $radila_ip_repo_dir
if {[llength [get_projects -quiet]] > 0} {
    close_project
}

create_project -force radila_ip_packager $project_dir -part $radila_part
set_property target_language VHDL [current_project]

set rtl_files [list \
    [file join $script_dir radila_core.vhd] \
    [file join $script_dir raddebughub_axi.vhd] \
    [file join $script_dir radila_axi_top.vhd] \
]
add_files -norecurse $rtl_files
set_property library work [get_files $rtl_files]
set_property file_type {VHDL 2008} [get_files $rtl_files]
set_property top radila_v1_0 [current_fileset]
update_compile_order -fileset sources_1

ipx::package_project \
    -force \
    -root_dir $ip_root_dir \
    -vendor user.org \
    -library user \
    -taxonomy {/UserIP} \
    -import_files

set core [ipx::current_core]
set_property name radila $core
set_property display_name {RadILA AXI-Lite Capture Core} $core
set_property description {HDL-only AXI-Lite capture buffer with event trigger and BRAM readback} $core
set_property version 1.0 $core
set_property vendor_display_name {RCT} $core
set_property supported_families {zynquplus Production zynq Production} $core

ipx::infer_bus_interface s00_axi_aclk xilinx.com:signal:clock_rtl:1.0 $core
ipx::infer_bus_interface s00_axi_aresetn xilinx.com:signal:reset_rtl:1.0 $core
set clk_bus [find_bus_interface_ci $core s00_axi_aclk]
set rst_bus [find_bus_interface_ci $core s00_axi_aresetn]
set axi_bus [find_bus_interface_ci $core S00_AXI]
if {$axi_bus eq ""} {
    set axi_bus [find_bus_interface_ci $core s00_axi]
}
if {$axi_bus eq ""} {
    ipx::infer_bus_interface s00_axi xilinx.com:interface:aximm_rtl:1.0 $core
    set axi_bus [find_bus_interface_ci $core s00_axi]
}
if {$axi_bus ne ""} {
    set axi_bus_name [get_property name $axi_bus]
    set_property interface_mode slave $axi_bus
    set_property abstraction_type_vlnv xilinx.com:interface:aximm_rtl:1.0 $axi_bus
    set_property bus_type_vlnv xilinx.com:interface:aximm:1.0 $axi_bus
    if {$clk_bus ne ""} {
        set assoc [ipx::get_bus_parameters ASSOCIATED_BUSIF -of_objects $clk_bus]
        if {$assoc ne ""} {
            set_property value $axi_bus_name $assoc
        }
    }
}
if {$rst_bus ne ""} {
    set pol [ipx::get_bus_parameters POLARITY -of_objects $rst_bus]
    if {$pol ne ""} {
        set_property value ACTIVE_LOW $pol
    }
}

set mem_maps [ipx::get_memory_maps -of_objects $core]
if {[llength $mem_maps] == 0 && $axi_bus ne ""} {
    ipx::add_memory_map S00_AXI $core
}
set mem_map [lindex [ipx::get_memory_maps -of_objects $core] 0]
if {$mem_map ne ""} {
    set_property slave_memory_map_ref [get_property name $mem_map] $axi_bus
    set blocks [ipx::get_address_blocks -of_objects $mem_map]
    if {[llength $blocks] == 0} {
        ipx::add_address_block S00_AXI_reg $mem_map
        set blocks [ipx::get_address_blocks -of_objects $mem_map]
    }
    set block [lindex $blocks 0]
    set_property name S00_AXI_reg $block
    set_property range 64 $block
    set_property width 32 $block
    set_property usage register $block
}

foreach port_name {sample_i event_i irq_o} {
    set port [ipx::get_ports $port_name -of_objects $core]
    if {$port ne ""} {
        set_property enablement_dependency {} $port
    }
}

ipx::check_integrity $core
ipx::save_core $core
set_property ip_repo_paths $radila_ip_repo_dir [current_project]
update_ip_catalog
puts "Packaged user.org:user:radila:1.0"
