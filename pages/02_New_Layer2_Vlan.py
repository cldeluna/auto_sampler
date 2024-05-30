#!/usr/bin/python -tt
# Project: auto_sampler
# Filename: 02_New_Layer2_Vlan
# claudiadeluna
# PyCharm

from __future__ import absolute_import, division, print_function

__author__ = "Claudia de Luna (claudia@indigowire.net)"
__version__ = ": 1.0 $"
__date__ = "5/13/24"
__copyright__ = "Copyright (c) 2023 Claudia"
__license__ = "Python"

import os

import streamlit as st
import datetime

import utilities


def main():

    # Use the full page instead of a narrow central column
    st.set_page_config(layout="wide")

    with st.sidebar:
        st.image(
            "images/EIAlogo_OnWhite-01-Transparent2.jpg",
            caption="",
            width=75,
        )

        url = "https://eianow.com/"
        st.markdown(f"**[EIA]({url})**")

    # Start of script execution
    start_time = datetime.datetime.now()

    # Date stamp for Report Output
    file_timestamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")

    st.title("Configure New Layer 2 Vlan")
    # st.write(st.session_state)

    # Load Well Known Action Dict for New layer2 Vlan
    action = "Existing_Vlan_L2"
    action_dict = utilities.load_wellknown_action(action)
    # st.write(action_dict)

    # Load Vlan Guidelines -----------------------------------------------------------------------
    st.markdown("---")
    st.markdown("### Loading Vlan Guidelines")
    vlan_type_list, vlan_guidelines_dict, vlan_guidelines_df = (
        utilities.load_vlan_guidelines()
    )
    st.write(vlan_guidelines_df)
    st.markdown("---")

    st.subheader("Select Location")

    # Trick to get a unique list of namespaces for the pull down
    namespace_list = utilities.get_namespace_list()

    # User interactive Selectbox to Select Namespace
    namespace = st.selectbox("Select Location", namespace_list)
    st.write(f"Selected Location: {namespace}")

    st.subheader("Select Vlan Type")
    add_vlan_type = st.selectbox(
        label="Select Type of Vlan to Configure", options=vlan_type_list, index=None
    )
    if add_vlan_type:
        st.write(vlan_guidelines_df[add_vlan_type])

    if add_vlan_type:
        # Set the guidelines for the selected vlan
        vlan_type_info_dict = vlan_guidelines_dict[add_vlan_type]
        # st.write(vlan_type_info_dict["Range"])

        # Now that we have VLAN type we can set min/max values
        st.subheader("Enter Vlan ID")
        add_vlan = st.number_input(
            "Enter Vlan ID",
            min_value=vlan_type_info_dict["Range"]["start"],
            max_value=vlan_type_info_dict["Range"]["end"],
            value=None,
        )
        st.write(f"Selected Vlan ID: {add_vlan}")
        vlan_shortname = vlan_type_info_dict["ShortName"]

        st.subheader(f"Enter Vlan {add_vlan} Subnet")
        vlan_subnet = st.text_input(
            f"Enter Subnet Associated with Vlan {add_vlan} in CIDR Notation:"
        )
        st.write(f"Vlan Subnet: {vlan_subnet}")

        st.subheader(f"Test in Virtual Lab")
        virtual_lab = st.checkbox("Validate Configuration Payload against Virtual Lab")
        force_lab_restart = st.checkbox("Force Virtual Lab Restart")
        st.write(
            f"Spin up Virtual lab: {virtual_lab} Force vLab Restart: {force_lab_restart}"
        )

        st.markdown("---")

    button_label = "Set Essential Configuration Parameters"
    with st.form(key="Essential_Config_Details"):
        lookup_option = st.form_submit_button(label=button_label)

        if lookup_option and (
            add_vlan_type is not None
            and add_vlan is not None
            and vlan_subnet
            and namespace
        ):

            st.subheader(f"Check Vlans in Use at Location {namespace}")
            # Is VLAN in use at the campus?
            vlans_found_bool, vlans_in_use = utilities.find_vlans_in_namespace(
                namespace
            )
            if vlans_found_bool:
                st.write(vlans_in_use)
            else:
                st.error(f"Aborting run! Cannot verify Vlans!")
                st.stop()

            # with the list of all the vlans at the site check to see if the vlan selected exists
            st.write(f"Checking to see if vlan {add_vlan} exists at site {namespace}")
            vlan_check_bool = False
            if int(add_vlan) in vlans_in_use:
                st.error(
                    f"👎 Aborting run! Vlan {add_vlan} is already configured at site {namespace}"
                )
                st.stop()
            else:
                vlan_check_bool = True
                st.success(f"👍 Vlan {add_vlan} is available at location {namespace}")

            # If vlan check bool is True it passed the check and the vlan is not in use
            if vlan_check_bool:

                # Initialize Ready to Deploy to False
                ready_to_deploy = False
                st.subheader(
                    "Select Access Switches (Uplink Device will be Automatically Determined)"
                )
                switch_list = utilities.get_switches_in_location(namespace)

                add_to_switches_list = st.multiselect(
                    label="Select Access Switches to deploy Vlan",
                    options=switch_list,
                    default=None,
                )
                st.info(
                    f":white_check_mark: Deploy New Layer 2 **{add_vlan}** Vlan to: {add_to_switches_list}"
                )

                # For each switch
                for sw in add_to_switches_list:
                    st.markdown("---")
                    st.markdown(f"# Configuration for Switch {sw}")

                    # Initializing Variables to empty so we always have the expected keys in the config dict
                    cfg_dict = dict()
                    po_num = ""
                    po_lod = dict()
                    lldp_lod = dict()
                    po_desc = ""
                    intf1_desc = ""
                    intf2_desc = ""
                    uplink_dev = ""

                    # Timestamp
                    cfg_dict.update(
                        {
                            "timestamp": datetime.datetime.now().strftime(
                                "%Y-%m-%d-%H:%M:%S"
                            ),
                        }
                    )

                    # Change Title
                    cfg_dict.update({"location": namespace})

                    # Location/Namespace
                    cfg_dict.update({"location": namespace})

                    # Switch
                    cfg_dict.update({"hostname": sw})

                    # Risk Info
                    cfg_dict.update({"risk": action_dict[action]["Impact_Rating"]})
                    cfg_dict.update(
                        {"impact": action_dict[action]["Impact_Description"]}
                    )

                    # Vlan ID
                    cfg_dict.update({"vlan_id": add_vlan})

                    # Vlan Name
                    vlan_name = f"{vlan_shortname}_{vlan_subnet}"
                    cfg_dict.update({"vlan_name": vlan_name})

                    # check for bonded interfaces
                    po_bool, po_lod = utilities.get_intf_bonded_switch(sw)
                    if po_bool:
                        # Go through each list element and make sure both interfaces have the same master
                        master_list = [line["master"] for line in po_lod]
                        slaveif_list = [line["ifname"] for line in po_lod]
                        umaster_list = list(set(master_list))
                        st.write(
                            f"Master list is {master_list} and Unique Master list is {umaster_list}"
                        )
                        if len(umaster_list) == 1:
                            st.write(f"Uplink Port Channel is {umaster_list[0]}")
                            po_num = umaster_list[0]

                            # Find the device on the other end of the interface
                            st.write(f"First Interface {slaveif_list[0]}")
                            lldp_bool, lldp_lod = utilities.get_lldp_switch(
                                sw, slaveif_list[0]
                            )
                            # st.write(lldp_lod)
                            if lldp_bool:
                                st.write(
                                    f"Found lldp neighbor on {slaveif_list[0]} {lldp_lod}"
                                )
                                po_desc = f"To {lldp_lod[0]['peerHostname']}"
                                uplink_dev = lldp_lod[0]["peerHostname"]
                                intf1_desc = f"To {lldp_lod[0]['peerHostname']}_{lldp_lod[0]['peerIfname']}"

                            st.write(f"Second Interface {slaveif_list[1]}")
                            lldp_bool, lldp_lod = utilities.get_lldp_switch(
                                sw, slaveif_list[1]
                            )
                            # st.write(lldp_lod)
                            if lldp_bool:
                                st.write(
                                    f"Found lldp neighbor on {slaveif_list[1]} {lldp_lod}"
                                )
                                intf2_desc = f"To {lldp_lod[0]['peerHostname']}_{lldp_lod[0]['peerIfname']}"

                    cfg_dict.update({"uplink_po_exists": po_bool})
                    cfg_dict.update({"uplink_po": po_num})
                    cfg_dict.update({"uplink_po_lod": po_lod})
                    cfg_dict.update({"uplink_lldp_lod": lldp_lod})
                    cfg_dict.update({"uplink_dev": uplink_dev})
                    cfg_dict.update({"uplink_po_desc": po_desc})
                    cfg_dict.update({"uplink_intf1_desc": intf1_desc})
                    cfg_dict.update({"uplink_intf2_desc": intf2_desc})

                    # Didn't find a Po so look for a trunk interface
                    trunk_bool = False
                    trunk_lod = dict()
                    lldp_lod = dict()
                    uplink_trunk = ""
                    trunk_intf_desc = ""
                    if not po_bool:
                        trunk_bool, trunk_lod = utilities.get_intf_trunk_switch(sw)
                        if trunk_bool:
                            # st.write(trunk_dict)

                            st.warning(
                                f"WARNING: No Port Channel! Found {len(trunk_lod)} uplink trunk port {trunk_lod[0]['ifname']}"
                            )

                            # Find the device on the other end of the interface
                            lldp_bool, lldp_lod = utilities.get_lldp_switch(
                                sw, trunk_lod[0]["ifname"]
                            )
                            # st.write(lldp_lod)

                            if lldp_bool:
                                # Set description
                                uplink_trunk = trunk_lod[0]["ifname"]
                                uplink_dev = lldp_lod[0]["peerHostname"]
                                trunk_intf_desc = f"To {lldp_lod[0]['peerHostname']}_{lldp_lod[0]['peerIfname']}"

                    cfg_dict.update({"uplink_trunk_exists": trunk_bool})
                    cfg_dict.update({"uplink_trunk_lod": trunk_lod})
                    cfg_dict.update({"uplink_trunk_lldp_lod": lldp_lod})
                    cfg_dict.update({"uplink_dev": uplink_dev})
                    cfg_dict.update({"uplink_trunk": uplink_trunk})
                    cfg_dict.update({"uplink_trunk_desc": trunk_intf_desc})

                    # Corner Cases
                    # SQ Enterprise to follow spanning tree
                    if not po_bool and not trunk_bool:
                        st.error(
                            f"Cannot find uplink.  Need SuzieQ Enterprise to follow spanning tree"
                        )

                    # Get Switch Configuration
                    devcfg_bool, devcfg_lod = utilities.get_devcfg_switch(sw)
                    cfg_dict.update({"devcfg_bool": devcfg_bool})
                    cfg_dict.update({"devcfg_lod": devcfg_lod})

                    # Create a suitable containerlab config
                    utilities.cfg_xfer_clab(devcfg_lod[0]["config"])

                    # Render the full configuration
                    rendered = utilities.render_j2template(
                        cfg_dict, "cisco_iosxe_l2vlan_default.j2", debug=False
                    )

                    # Create files with specific content for documentation, config, and rollback
                    # Options for file are full cfg rollback
                    # Full configuration for Documentation, Review, and Change Request
                    cwd_path = os.getcwd()
                    filename = f"{sw}_changedoc_{file_timestamp}.txt"
                    full_list = utilities.write_rendered_to_file(
                        cwd_path, rendered, filename, type="full"
                    )
                    cfg_dict.update({"full_list": full_list})

                    # Configuration Only
                    cwd_path = os.getcwd()
                    filename = f"{sw}_cfglet_{file_timestamp}.txt"
                    cfg_list = utilities.write_rendered_to_file(
                        cwd_path, rendered, filename, type="cfg"
                    )
                    cfg_dict.update({"cfg_list": cfg_list})

                    # Rollback
                    cwd_path = os.getcwd()
                    filename = f"{sw}_rollback_{file_timestamp}.txt"
                    rollback_list = utilities.write_rendered_to_file(
                        cwd_path, rendered, filename, type="rollback"
                    )
                    cfg_dict.update({"rollback_list": rollback_list})

                    # Save the cfg_dict to YAML
                    filename = f"{sw}_cfgpayload_{file_timestamp}.yml"
                    st.write(
                        f"Saving Analysis and Configuration Payload to YAML file {filename} "
                    )
                    utilities.save_yaml_file(cfg_dict, filename)

                    st.markdown("---")

                    if virtual_lab:
                        st.title("Setting Up Virtual Lab")
                        ready_to_deploy = utilities.netmiko_jump(
                            access_hn=sw,
                            uplink_hn=uplink_dev,
                            cfg_list=cfg_dict["cfg_list"],
                            force_lab_restart=force_lab_restart,
                        )
                        # utilities.netmiko_jump()
                    else:
                        st.warning(":broken_heart: No Virtual Lab!  Remember to test!")

                st.markdown("---")
                # ----------------------------------- SCRIPT EXECUTION TIME --------------------------------------------
                end_time = datetime.datetime.now()
                st.markdown(f"**Execution Time: {end_time - start_time}**")

                if ready_to_deploy:
                    st.markdown("---")
                    st.subheader(":stopwatch: Change is ready to deploy")
            else:
                # Vlan check failed
                pass


# Standard call to the main() function.
if __name__ == "__main__":

    main()
